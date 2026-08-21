import json

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.common.abuse_filter import is_url_safe
from pulseroute.common.id_generator import generate_unique_slug
from pulseroute.core.config import settings
from pulseroute.core.security import hash_password
from pulseroute.models.domain import CustomDomain
from pulseroute.models.link import ShortLink
from pulseroute.schemas.link import LinkCreate


class LinkService:
    @staticmethod
    def _build_cache_key(domain: str | None, slug: str) -> str:
        domain_part = (domain or "default").lower()
        return f"link:{domain_part}:{slug}"

    @staticmethod
    async def create_link(
        db: AsyncSession,
        redis_cli: aioredis.Redis | None,
        data: LinkCreate,
        workspace_id: int | None = None,
        base_domain: str | None = None,
    ) -> ShortLink:
        # 1. Validate destination URL safety
        if settings.ENFORCE_SAFE_BROWSING:
            safe, reason = is_url_safe(data.destination_url)
            if not safe:
                raise ValueError(f"URL Safety Violation: {reason}")

        # 2. Resolve or generate slug
        slug = data.slug.strip() if data.slug else None
        if slug:
            # Check for existing slug on the same domain
            query = select(ShortLink).where(ShortLink.slug == slug)
            if data.domain_id:
                query = query.where(ShortLink.domain_id == data.domain_id)
            else:
                query = query.where(ShortLink.domain_id.is_(None))
            result = await db.execute(query)
            if result.scalar_one_or_none():
                raise ValueError(f"Slug '{slug}' is already taken.")
        else:
            slug = await generate_unique_slug(redis_cli, length=6)

        # 3. Handle password protection
        pwd_hash = hash_password(data.password) if data.password else None

        # 4. Create DB record
        link = ShortLink(
            workspace_id=workspace_id,
            domain_id=data.domain_id,
            slug=slug,
            destination_url=data.destination_url,
            title=data.title,
            ios_destination=data.ios_destination,
            android_destination=data.android_destination,
            password_hash=pwd_hash,
            utm_source=data.utm_source,
            utm_medium=data.utm_medium,
            utm_campaign=data.utm_campaign,
            expires_at=data.expires_at,
        )
        db.add(link)
        await db.commit()
        await db.refresh(link)

        # 5. Populate Redis Cache
        if redis_cli:
            try:
                domain_str = None
                if data.domain_id:
                    dom_res = await db.execute(select(CustomDomain.domain).where(CustomDomain.id == data.domain_id))
                    domain_str = dom_res.scalar_one_or_none()
                cache_key = LinkService._build_cache_key(domain_str, slug)
                cache_payload = {
                    "id": link.id,
                    "destination_url": link.destination_url,
                    "ios_destination": link.ios_destination or "",
                    "android_destination": link.android_destination or "",
                    "has_password": bool(link.password_hash),
                    "is_active": link.is_active,
                    "expires_at": link.expires_at.isoformat() if link.expires_at else "",
                }
                await redis_cli.set(cache_key, json.dumps(cache_payload), ex=settings.CACHE_DEFAULT_TTL)
            except Exception:
                pass

        return link

    @staticmethod
    async def get_link_by_id(db: AsyncSession, link_id: int) -> ShortLink | None:
        result = await db.execute(select(ShortLink).where(ShortLink.id == link_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_links(
        db: AsyncSession,
        workspace_id: int | None = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[ShortLink]:
        query = select(ShortLink).order_by(ShortLink.created_at.desc()).limit(limit).offset(offset)
        if workspace_id:
            query = query.where(ShortLink.workspace_id == workspace_id)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def delete_link(
        db: AsyncSession,
        redis_cli: aioredis.Redis | None,
        link_id: int
    ) -> bool:
        link = await LinkService.get_link_by_id(db, link_id)
        if not link:
            return False

        # Invalidate Cache
        if redis_cli:
            try:
                cache_key = LinkService._build_cache_key(None, link.slug)
                await redis_cli.delete(cache_key)
            except Exception:
                pass

        await db.delete(link)
        await db.commit()
        return True
