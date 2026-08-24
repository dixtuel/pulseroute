import json
from typing import List, Optional

import redis.asyncio as aioredis
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.common.abuse_filter import is_url_safe
from pulseroute.common.id_generator import generate_unique_slug
from pulseroute.core.config import settings
from pulseroute.core.security import hash_password
from pulseroute.models.domain import CustomDomain
from pulseroute.models.link import ShortLink
from pulseroute.schemas.link import LinkCreate, LinkUpdate
from pulseroute.services.webhook_service import WebhookService


class LinkService:
    @staticmethod
    def _build_cache_key(domain: Optional[str], slug: str) -> str:
        domain_part = (domain or "default").lower()
        return f"link:{domain_part}:{slug}"

    @staticmethod
    async def create_link(
        db: AsyncSession,
        redis_cli: Optional[aioredis.Redis],
        data: LinkCreate,
        workspace_id: Optional[int] = None,
        base_domain: Optional[str] = None,
    ) -> ShortLink:
        if settings.ENFORCE_SAFE_BROWSING:
            safe, reason = is_url_safe(data.destination_url)
            if not safe:
                raise ValueError(f"URL Safety Violation: {reason}")

        domain = None
        if data.domain_id:
            domain = await db.get(CustomDomain, data.domain_id)
            if not domain or not domain.is_verified or domain.workspace_id != workspace_id:
                raise ValueError("Invalid or unverified custom domain for this workspace.")

        if settings.REQUIRE_CUSTOM_DOMAIN and domain is None:
            raise ValueError(
                "This server requires every link to use a verified custom domain. "
                "Add and verify your workspace's own domain before creating links."
            )

        slug = data.slug.strip() if data.slug else None
        if slug:
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

        pwd_hash = hash_password(data.password) if data.password else None

        link = ShortLink(
            workspace_id=workspace_id,
            domain_id=data.domain_id,
            slug=slug,
            destination_url=data.destination_url,
            title=data.title,
            tags=data.tags,
            ios_destination=data.ios_destination,
            android_destination=data.android_destination,
            geo_targets=data.geo_targets,
            interstitial_delay=data.interstitial_delay,
            interstitial_title=data.interstitial_title,
            expires_at=data.expires_at,
            expired_url=data.expired_url,
            og_title=data.og_title,
            og_description=data.og_description,
            og_image=data.og_image,
            password_hash=pwd_hash,
            public_stats=data.public_stats,
            utm_source=data.utm_source,
            utm_medium=data.utm_medium,
            utm_campaign=data.utm_campaign,
        )
        db.add(link)
        await db.commit()
        await db.refresh(link)

        # Cache in Redis
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
                    "geo_targets": link.geo_targets or {},
                    "interstitial_delay": link.interstitial_delay,
                    "interstitial_ad_html": link.interstitial_ad_html or "",
                    "interstitial_title": link.interstitial_title or "",
                    "adsense_client_id": link.adsense_client_id or "",
                    "adsense_slot_id": link.adsense_slot_id or "",
                    "expired_url": link.expired_url or "",
                    "has_password": bool(link.password_hash),
                    "public_stats": link.public_stats,
                    "is_active": link.is_active,
                    "expires_at": link.expires_at.isoformat() if link.expires_at else "",
                }
                await redis_cli.set(cache_key, json.dumps(cache_payload), ex=settings.CACHE_DEFAULT_TTL)
            except Exception:
                pass

        if workspace_id:
            await WebhookService.notify_workspace(db, workspace_id, "link.created", {
                "link_id": link.id,
                "slug": link.slug,
                "destination_url": link.destination_url,
            })

        return link

    @staticmethod
    async def update_link(
        db: AsyncSession,
        redis_cli: Optional[aioredis.Redis],
        link_id: int,
        data: LinkUpdate,
    ) -> Optional[ShortLink]:
        link = await LinkService.get_link_by_id(db, link_id)
        if not link:
            return None

        update_fields = data.model_dump(exclude_unset=True)
        if "destination_url" in update_fields and settings.ENFORCE_SAFE_BROWSING:
            safe, reason = is_url_safe(update_fields["destination_url"])
            if not safe:
                raise ValueError(f"URL Safety Violation: {reason}")

        for field, value in update_fields.items():
            setattr(link, field, value)

        await db.commit()
        await db.refresh(link)

        # Invalidate / Refresh Cache
        if redis_cli:
            try:
                cache_key = LinkService._build_cache_key(None, link.slug)
                cache_payload = {
                    "id": link.id,
                    "destination_url": link.destination_url,
                    "ios_destination": link.ios_destination or "",
                    "android_destination": link.android_destination or "",
                    "geo_targets": link.geo_targets or {},
                    "interstitial_delay": link.interstitial_delay,
                    "interstitial_ad_html": link.interstitial_ad_html or "",
                    "interstitial_title": link.interstitial_title or "",
                    "adsense_client_id": link.adsense_client_id or "",
                    "adsense_slot_id": link.adsense_slot_id or "",
                    "expired_url": link.expired_url or "",
                    "has_password": bool(link.password_hash),
                    "public_stats": link.public_stats,
                    "is_active": link.is_active,
                    "expires_at": link.expires_at.isoformat() if link.expires_at else "",
                }
                await redis_cli.set(cache_key, json.dumps(cache_payload), ex=settings.CACHE_DEFAULT_TTL)
            except Exception:
                pass

        return link

    @staticmethod
    async def get_link_by_id(db: AsyncSession, link_id: int) -> Optional[ShortLink]:
        result = await db.execute(select(ShortLink).where(ShortLink.id == link_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_link_by_slug(db: AsyncSession, slug: str) -> Optional[ShortLink]:
        result = await db.execute(select(ShortLink).where(ShortLink.slug == slug))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_links(
        db: AsyncSession,
        workspace_id: Optional[int] = None,
        search: Optional[str] = None,
        tag: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ShortLink]:
        query = select(ShortLink).order_by(ShortLink.created_at.desc())

        if workspace_id:
            query = query.where(ShortLink.workspace_id == workspace_id)
        if tag:
            query = query.where(ShortLink.tags.ilike(f"%{tag}%"))
        if is_active is not None:
            query = query.where(ShortLink.is_active.is_(is_active))
        if search:
            query = query.where(
                or_(
                    ShortLink.slug.ilike(f"%{search}%"),
                    ShortLink.title.ilike(f"%{search}%"),
                    ShortLink.destination_url.ilike(f"%{search}%")
                )
            )

        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def delete_link(
        db: AsyncSession,
        redis_cli: Optional[aioredis.Redis],
        link_id: int
    ) -> bool:
        link = await LinkService.get_link_by_id(db, link_id)
        if not link:
            return False

        if redis_cli:
            try:
                cache_key = LinkService._build_cache_key(None, link.slug)
                await redis_cli.delete(cache_key)
            except Exception:
                pass

        await db.delete(link)
        await db.commit()
        return True
