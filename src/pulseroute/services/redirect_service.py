import json
import time
from datetime import UTC, datetime
from typing import Optional, Tuple

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.common.bot_detector import parse_user_agent
from pulseroute.common.geoip import lookup_ip_location
from pulseroute.common.privacy import anonymize_ip
from pulseroute.core.config import settings
from pulseroute.models.domain import CustomDomain
from pulseroute.models.link import ShortLink


class RedirectService:
    @staticmethod
    async def resolve_and_track(
        db: AsyncSession,
        redis_cli: Optional[aioredis.Redis],
        host: str,
        slug: str,
        user_agent: str,
        client_ip: str,
        referrer: Optional[str],
        password: Optional[str] = None,
    ) -> Tuple[Optional[str], int, Optional[str]]:
        """
        Returns (destination_url: Optional[str], status_code: int, error_or_auth_message: Optional[str])
        """
        # 1. Parse host vs primary domain
        custom_domain = host.split(":")[0].lower()
        primary_host = settings.PRIMARY_DOMAIN.split(":")[0].lower()
        if custom_domain in (primary_host, "localhost", "127.0.0.1", "testserver", "testclient"):
            domain_name = None
        else:
            domain_name = custom_domain

        cache_key = f"link:{domain_name or 'default'}:{slug}"
        link_data = None

        # 2. Check Redis Cache (Ultra-Fast Path)
        if redis_cli:
            try:
                cached_json = await redis_cli.get(cache_key)
                if cached_json == "NULL":
                    return None, 404, "Link not found"
                if cached_json:
                    link_data = json.loads(cached_json)
            except Exception:
                pass

        # 3. Cache Miss: Fallback to Database
        if not link_data:
            query = select(ShortLink).where(ShortLink.slug == slug)
            custom_domain_obj = None
            if domain_name:
                dom_query = select(CustomDomain).where(CustomDomain.domain == domain_name)
                dom_res = await db.execute(dom_query)
                custom_domain_obj = dom_res.scalar_one_or_none()
                if custom_domain_obj:
                    query = query.where(ShortLink.domain_id == custom_domain_obj.id)
                else:
                    return None, 404, "Custom domain not registered"
            else:
                query = query.where(ShortLink.domain_id.is_(None))

            result = await db.execute(query)
            link = result.scalar_one_or_none()

            if not link:
                if redis_cli:
                    try:
                        await redis_cli.set(cache_key, "NULL", ex=settings.NEGATIVE_CACHE_TTL)
                    except Exception:
                        pass
                # Check for custom 404 URL fallback on custom domain
                if custom_domain_obj and custom_domain_obj.custom_not_found_url:
                    return custom_domain_obj.custom_not_found_url, 302, None
                return None, 404, "Link not found"

            link_data = {
                "id": link.id,
                "destination_url": link.destination_url,
                "ios_destination": link.ios_destination or "",
                "android_destination": link.android_destination or "",
                "has_password": bool(link.password_hash),
                "is_active": link.is_active,
                "expires_at": link.expires_at.isoformat() if link.expires_at else "",
            }

            # Populate cache
            if redis_cli:
                try:
                    await redis_cli.set(cache_key, json.dumps(link_data), ex=settings.CACHE_DEFAULT_TTL)
                except Exception:
                    pass

        # 4. Check Link Active & Expiration
        if not link_data.get("is_active", True):
            return None, 410, "This link has been deactivated."

        if link_data.get("expires_at"):
            try:
                exp_dt = datetime.fromisoformat(link_data["expires_at"])
                if datetime.now(UTC) > exp_dt:
                    return None, 410, "This link has expired."
            except Exception:
                pass

        # 5. Check Password Protection
        if link_data.get("has_password") and not password:
            return None, 401, "Password required for this short link."

        # 6. Parse Client, Device & Bot Filtering
        is_bot, device_type, browser, os_name = parse_user_agent(user_agent)

        # 7. Device-Specific Smart Targeting
        target_url = link_data["destination_url"]
        if os_name == "iOS" and link_data.get("ios_destination"):
            target_url = link_data["ios_destination"]
        elif os_name == "Android" and link_data.get("android_destination"):
            target_url = link_data["android_destination"]

        # 8. Async Event Ingestion into Redis Stream (GDPR/KVKK Anonymized IP)
        if redis_cli:
            try:
                anon_ip = anonymize_ip(client_ip)
                country_code, _country_name, city = lookup_ip_location(anon_ip)
                event_payload = {
                    "link_id": str(link_data["id"]),
                    "country_code": country_code,
                    "city": city,
                    "device_type": device_type,
                    "browser": browser,
                    "os": os_name,
                    "referrer": referrer or "",
                    "is_bot": "1" if is_bot else "0",
                    "timestamp": str(int(time.time())),
                }
                await redis_cli.xadd("pulseroute:events:clicks", event_payload, maxlen=100000)
            except Exception:
                pass

        return target_url, settings.DEFAULT_REDIRECT_STATUS, None
