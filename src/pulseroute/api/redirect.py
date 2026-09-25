import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Body, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError

from pulseroute.common.bot_detector import parse_user_agent
from pulseroute.common.redirect_ticket import issue_ticket, read_ticket
from pulseroute.core.config import settings
from pulseroute.core.database import async_session_maker
from pulseroute.core.redis import get_analytics_redis, get_redis
from pulseroute.services.analytics_service import AnalyticsService
from pulseroute.services.link_service import LinkService
from pulseroute.services.redirect_service import RedirectService

router = APIRouter(tags=["Redirector"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "web" / "templates"))
WAIT_SECONDS = 5

RESERVED_SLUGS = {
    "favicon.ico", "robots.txt", "sitemap.xml", "BingSiteAuth.xml", "ads.txt",
    "docs", "redoc", "openapi.json", "dashboard", "api", "privacy", "terms",
    "accessibility", "abuse", "report", "healthz", "healtalive",
}


async def _resolve(request: Request, slug: str, password: Optional[str]):
    async with async_session_maker() as db:
        redis_cli = await get_redis()
        analytics_redis_cli = (
            await get_analytics_redis() if settings.ANALYTICS_REDIS_URL else redis_cli
        )
        return await RedirectService.resolve_and_track(
            db=db,
            redis_cli=redis_cli,
            host=request.headers.get("host") or "localhost",
            slug=slug,
            user_agent=request.headers.get("user-agent") or "",
            client_ip=request.client.host if request.client else "127.0.0.1",
            referrer=request.headers.get("referer"),
            password=password,
            analytics_redis_cli=analytics_redis_cli,
        )


def _raise_resolution_error(status_code: int, message: str) -> None:
    raise HTTPException(status_code=status_code if status_code in (401, 410, 451) else 404, detail=message)


@router.get("/api/v1/redirect/resolve/{slug}")
async def resolve_browser_link(
    slug: str,
    request: Request,
    ticket: str,
    password: Optional[str] = Query(None),
):
    start = read_ticket(ticket)
    host = request.headers.get("host") or "localhost"
    if (
        not start or start.get("kind") != "start" or start.get("slug") != slug
        or start.get("host") != host or not isinstance(start.get("started_at"), (int, float))
    ):
        raise HTTPException(status_code=400, detail="Invalid redirect ticket")

    try:
        target_url, status_code, err_msg, interstitial = await _resolve(request, slug, password)
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Link verification is temporarily unavailable") from None

    if err_msg:
        _raise_resolution_error(status_code, err_msg)

    ready_at = float(start["started_at"]) + WAIT_SECONDS
    completion_ticket = issue_ticket(
        {"kind": "complete", "host": host, "slug": slug, "target_url": target_url, "ready_at": ready_at}
    )
    return JSONResponse(
        content={
            "ticket": completion_ticket,
            "wait_ms": max(0, round((ready_at - time.time()) * 1000)),
            "title": interstitial.get("title") if interstitial else None,
        },
        headers={"Cache-Control": "no-store"},
    )


@router.post("/api/v1/redirect/complete")
async def complete_browser_link(request: Request, payload: dict = Body(...)):
    ticket = read_ticket(payload.get("ticket", ""))
    host = request.headers.get("host") or "localhost"
    if (
        not ticket or ticket.get("kind") != "complete" or ticket.get("host") != host
        or not isinstance(ticket.get("ready_at"), (int, float))
        or not isinstance(ticket.get("target_url"), str)
    ):
        raise HTTPException(status_code=400, detail="Invalid redirect ticket")
    if time.time() < float(ticket["ready_at"]):
        raise HTTPException(status_code=425, detail="Please wait before continuing")
    return JSONResponse(
        content={"target_url": ticket["target_url"]}, headers={"Cache-Control": "no-store"}
    )


@router.get("/{slug}")
async def redirect_short_url(slug: str, request: Request, password: Optional[str] = Query(None)):
    if slug in RESERVED_SLUGS or slug.startswith("google") or slug.startswith("yandex_"):
        raise HTTPException(status_code=404, detail="Not Found")

    if slug.endswith("+"):
        async with async_session_maker() as db:
            link = await LinkService.get_link_by_slug(db, slug[:-1])
            if not link:
                raise HTTPException(status_code=404, detail="Link not found")
            if not link.public_stats:
                raise HTTPException(status_code=403, detail="Public stats are disabled for this link")
            analytics = await AnalyticsService.get_link_analytics(db, link_id=link.id, days=30)
            return JSONResponse(content=analytics.model_dump())

    user_agent = request.headers.get("user-agent") or ""
    is_bot = parse_user_agent(user_agent)[0]
    if "text/html" in request.headers.get("accept", "") and not is_bot:
        start_ticket = issue_ticket(
            {"kind": "start", "host": request.headers.get("host") or "localhost", "slug": slug,
             "started_at": time.time()}
        )
        return templates.TemplateResponse(
            request=request,
            name="interstitial.html",
            context={
                "start_ticket": start_ticket,
                "slug": slug,
                "adsense_client_id": settings.GLOBAL_ADSENSE_CLIENT_ID,
                "adsense_slot_id": settings.GLOBAL_ADSENSE_REDIRECT_SLOT_ID or settings.GLOBAL_ADSENSE_SLOT_ID,
            },
            headers={"Cache-Control": "private, no-store", "X-Robots-Tag": "noindex, nofollow"},
        )

    try:
        target_url, status_code, err_msg, _ = await _resolve(request, slug, password)
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Link verification is temporarily unavailable") from None
    if err_msg:
        _raise_resolution_error(status_code, err_msg)

    response = RedirectResponse(url=target_url, status_code=status_code)
    response.headers["Cache-Control"] = "private, no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response
