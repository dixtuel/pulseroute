from datetime import UTC, datetime, timedelta
from typing import Dict, List, Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.api.deps import get_current_user, require_authenticated_user, verify_workspace_access
from pulseroute.common.rate_limiter import SlidingWindowRateLimiter
from pulseroute.core.config import settings
from pulseroute.core.database import get_db
from pulseroute.core.redis import get_redis
from pulseroute.models.domain import CustomDomain
from pulseroute.models.link import ShortLink
from pulseroute.models.user import User
from pulseroute.schemas.link import LinkCreate, LinkResponse, LinkUpdate
from pulseroute.services.link_service import LinkService

router = APIRouter(prefix="/links", tags=["Links"])


def build_short_url(request: Optional[Request], slug: str, custom_domain: Optional[str] = None) -> str:
    if custom_domain:
        return f"https://{custom_domain}/{slug}"
    if not request:
        return f"/{slug}"
    host = request.headers.get("host") or settings.PRIMARY_DOMAIN
    proto = request.headers.get("x-forwarded-proto") or ("http" if (host.startswith("localhost") or host.startswith("127.0.0.1")) else "https")
    return f"{proto}://{host}/{slug}"


def _serialize_link(link: ShortLink, request: Optional[Request], domain_name: Optional[str] = None) -> dict:
    return {
        "id": link.id,
        "slug": link.slug,
        "destination_url": link.destination_url,
        "title": link.title,
        "tags": link.tags,
        "interstitial_delay": link.interstitial_delay,
        "short_url": build_short_url(request, link.slug, custom_domain=domain_name),
        "total_clicks": link.total_clicks,
        "public_stats": link.public_stats,
        "is_active": link.is_active,
        "created_at": link.created_at,
        "expires_at": link.expires_at,
    }


async def _domain_name(db: AsyncSession, domain_id: Optional[int]) -> Optional[str]:
    if not domain_id:
        return None
    result = await db.execute(select(CustomDomain.domain).where(CustomDomain.id == domain_id))
    return result.scalar_one_or_none()


async def _domain_names(db: AsyncSession, domain_ids: set[int]) -> Dict[int, str]:
    if not domain_ids:
        return {}
    result = await db.execute(select(CustomDomain.id, CustomDomain.domain).where(CustomDomain.id.in_(domain_ids)))
    return dict(result.all())


@router.get("/stats/anonymous-count")
async def anonymous_links_count(db: AsyncSession = Depends(get_db)):
    """Public, aggregate-only stat: how many anonymous links were created in the last 24h."""
    since = datetime.now(UTC) - timedelta(hours=24)
    result = await db.execute(
        select(func.count(ShortLink.id)).where(
            ShortLink.workspace_id.is_(None),
            ShortLink.created_at >= since,
        )
    )
    return {"count": result.scalar() or 0}


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

    workspace_id = None
    if current_user and link_data.workspace_id:
        workspace = await verify_workspace_access(link_data.workspace_id, current_user, db)
        workspace_id = workspace.id

    try:
        link = await LinkService.create_link(db, redis_cli, link_data, workspace_id=workspace_id)
        domain_name = await _domain_name(db, link.domain_id)
        return _serialize_link(link, request, domain_name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{link_id}", response_model=LinkResponse)
async def update_short_link(
    link_id: int,
    link_data: LinkUpdate,
    request: Request,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
    redis_cli: Optional[aioredis.Redis] = Depends(get_redis),
):
    link = await LinkService.get_link_by_id(db, link_id)
    if not link or link.workspace_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    await verify_workspace_access(link.workspace_id, current_user, db)

    try:
        link = await LinkService.update_link(db, redis_cli, link_id, link_data)
        domain_name = await _domain_name(db, link.domain_id)
        return _serialize_link(link, request, domain_name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[LinkResponse])
async def list_links(
    workspace_id: int = Query(..., description="Workspace to list links for"),
    search: Optional[str] = Query(None, description="Search by slug, title or destination"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    is_active: Optional[bool] = Query(None, description="Filter active status"),
    limit: int = 50,
    offset: int = 0,
    request: Request = None,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_workspace_access(workspace_id, current_user, db)

    links = await LinkService.list_links(
        db, workspace_id=workspace_id, search=search, tag=tag, is_active=is_active, limit=limit, offset=offset
    )
    domain_names = await _domain_names(db, {lnk.domain_id for lnk in links if lnk.domain_id})
    return [_serialize_link(lnk, request, domain_names.get(lnk.domain_id)) for lnk in links]


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_short_link(
    link_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
    redis_cli: Optional[aioredis.Redis] = Depends(get_redis),
):
    link = await LinkService.get_link_by_id(db, link_id)
    if not link or link.workspace_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    await verify_workspace_access(link.workspace_id, current_user, db)

    success = await LinkService.delete_link(db, redis_cli, link_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
