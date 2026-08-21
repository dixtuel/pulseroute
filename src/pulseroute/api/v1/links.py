from datetime import UTC, datetime, timedelta
from typing import List, Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.api.deps import get_current_user
from pulseroute.common.rate_limiter import SlidingWindowRateLimiter
from pulseroute.core.config import settings
from pulseroute.core.database import get_db
from pulseroute.core.redis import get_redis
from pulseroute.models.user import User
from pulseroute.schemas.link import LinkCreate, LinkResponse, LinkUpdate
from pulseroute.services.link_service import LinkService

router = APIRouter(prefix="/links", tags=["Links"])


def build_short_url(request: Optional[Request], slug: str) -> str:
    if not request:
        return f"/{slug}"
    host = request.headers.get("host") or settings.PRIMARY_DOMAIN
    proto = request.headers.get("x-forwarded-proto") or ("https" if "onrender.com" in host or (not host.startswith("localhost") and not host.startswith("127.0.0.1")) else "http")
    return f"{proto}://{host}/{slug}"


@router.post("", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def create_short_link(
    link_data: LinkCreate,
    request: Request,
    response: Response,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_cli: Optional[aioredis.Redis] = Depends(get_redis),
):
    # Enforce 24-hour expiration for anonymous / unauthenticated users
    if not current_user and not link_data.expires_at:
        link_data.expires_at = datetime.now(UTC) + timedelta(hours=24)
    client_ip = request.client.host if request.client else "127.0.0.1"

    allowed, remaining = await SlidingWindowRateLimiter.is_allowed(
        redis_cli,
        key=f"create:{client_ip}",
        limit=30,
        window_seconds=60,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait before creating more links."
        )
    response.headers["X-RateLimit-Remaining"] = str(remaining)

    try:
        link = await LinkService.create_link(db, redis_cli, link_data)
        short_url = build_short_url(request, link.slug)
        return {
            "id": link.id,
            "slug": link.slug,
            "destination_url": link.destination_url,
            "title": link.title,
            "tags": link.tags,
            "interstitial_delay": link.interstitial_delay,
            "adsense_client_id": link.adsense_client_id,
            "short_url": short_url,
            "total_clicks": link.total_clicks,
            "public_stats": link.public_stats,
            "is_active": link.is_active,
            "created_at": link.created_at,
            "expires_at": link.expires_at,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{link_id}", response_model=LinkResponse)
async def update_short_link(
    link_id: int,
    link_data: LinkUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis_cli: Optional[aioredis.Redis] = Depends(get_redis),
):
    try:
        link = await LinkService.update_link(db, redis_cli, link_id, link_data)
        if not link:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

        short_url = build_short_url(request, link.slug)
        return {
            "id": link.id,
            "slug": link.slug,
            "destination_url": link.destination_url,
            "title": link.title,
            "tags": link.tags,
            "interstitial_delay": link.interstitial_delay,
            "adsense_client_id": link.adsense_client_id,
            "short_url": short_url,
            "total_clicks": link.total_clicks,
            "public_stats": link.public_stats,
            "is_active": link.is_active,
            "created_at": link.created_at,
            "expires_at": link.expires_at,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[LinkResponse])
async def list_links(
    search: Optional[str] = Query(None, description="Search by slug, title or destination"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    is_active: Optional[bool] = Query(None, description="Filter active status"),
    limit: int = 50,
    offset: int = 0,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    links = await LinkService.list_links(
        db, search=search, tag=tag, is_active=is_active, limit=limit, offset=offset
    )
    return [
        {
            "id": lnk.id,
            "slug": lnk.slug,
            "destination_url": lnk.destination_url,
            "title": lnk.title,
            "tags": lnk.tags,
            "interstitial_delay": lnk.interstitial_delay,
            "adsense_client_id": lnk.adsense_client_id,
            "short_url": build_short_url(request, lnk.slug),
            "total_clicks": lnk.total_clicks,
            "public_stats": lnk.public_stats,
            "is_active": lnk.is_active,
            "created_at": lnk.created_at,
            "expires_at": lnk.expires_at,
        }
        for lnk in links
    ]


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_short_link(
    link_id: int,
    db: AsyncSession = Depends(get_db),
    redis_cli: Optional[aioredis.Redis] = Depends(get_redis),
):
    success = await LinkService.delete_link(db, redis_cli, link_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
