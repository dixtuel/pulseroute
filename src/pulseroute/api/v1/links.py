from typing import List, Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.common.rate_limiter import SlidingWindowRateLimiter
from pulseroute.core.config import AppMode, settings
from pulseroute.core.database import get_db
from pulseroute.core.redis import get_redis
from pulseroute.schemas.link import LinkCreate, LinkResponse
from pulseroute.services.link_service import LinkService

router = APIRouter(prefix="/links", tags=["Links"])


@router.post("", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def create_short_link(
    link_data: LinkCreate,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis_cli: Optional[aioredis.Redis] = Depends(get_redis),
):
    client_ip = request.client.host if request.client else "127.0.0.1"

    # Rate limiting for public creation
    if settings.APP_MODE == AppMode.PUBLIC:
        allowed, remaining = await SlidingWindowRateLimiter.is_allowed(
            redis_cli,
            key=f"create:{client_ip}",
            limit=settings.RATE_LIMIT_PUBLIC_CREATE,
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
        host = request.headers.get("host") or settings.PRIMARY_DOMAIN
        short_url = f"http://{host}/{link.slug}"
        return {
            "id": link.id,
            "slug": link.slug,
            "destination_url": link.destination_url,
            "title": link.title,
            "short_url": short_url,
            "total_clicks": link.total_clicks,
            "is_active": link.is_active,
            "created_at": link.created_at,
            "expires_at": link.expires_at,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[LinkResponse])
async def list_links(
    limit: int = 50,
    offset: int = 0,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    links = await LinkService.list_links(db, limit=limit, offset=offset)
    host = request.headers.get("host") if request else settings.PRIMARY_DOMAIN
    return [
        {
            "id": lnk.id,
            "slug": lnk.slug,
            "destination_url": lnk.destination_url,
            "title": lnk.title,
            "short_url": f"http://{host}/{lnk.slug}",
            "total_clicks": lnk.total_clicks,
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
