
import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.core.database import get_db
from pulseroute.core.redis import get_redis
from pulseroute.services.redirect_service import RedirectService

router = APIRouter(tags=["Redirector"])


@router.get("/{slug}")
async def redirect_short_url(
    slug: str,
    request: Request,
    password: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    redis_cli: aioredis.Redis | None = Depends(get_redis),
):
    # Ignore favicon and robots.txt
    if slug in ("favicon.ico", "robots.txt", "docs", "redoc", "openapi.json", "dashboard", "api"):
        raise HTTPException(status_code=404, detail="Not Found")

    host = request.headers.get("host") or "localhost"
    user_agent = request.headers.get("user-agent") or ""
    client_ip = request.client.host if request.client else "127.0.0.1"
    referrer = request.headers.get("referer")

    target_url, status_code, err_msg = await RedirectService.resolve_and_track(
        db=db,
        redis_cli=redis_cli,
        host=host,
        slug=slug,
        user_agent=user_agent,
        client_ip=client_ip,
        referrer=referrer,
        password=password,
    )

    if err_msg:
        if status_code == 401:
            raise HTTPException(status_code=401, detail=err_msg)
        elif status_code == 410:
            raise HTTPException(status_code=410, detail=err_msg)
        else:
            raise HTTPException(status_code=404, detail=err_msg)

    response = RedirectResponse(url=target_url, status_code=status_code)
    # Crucial headers to prevent client-side hard caching of analytics
    response.headers["Cache-Control"] = "private, no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response
