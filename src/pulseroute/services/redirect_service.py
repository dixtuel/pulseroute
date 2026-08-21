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


def is_system_domain(host: str) -> bool:
    clean_host = host.split(":")[0].lower()
    primary_host = settings.PRIMARY_DOMAIN.split(":")[0].lower()
    if clean_host in (primary_host, "localhost", "127.0.0.1", "0.0.0.0", "testserver", "testclient"):
        return True
    if clean_host.endswith(".onrender.com") or clean_host.endswith(".railway.app") or clean_host.endswith(".zeabur.app") or clean_host.endswith(".fly.dev"):
        return True
    return False


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
    ) -> Tuple[Optional[str], int, Optional[str], Optional[dict]]:
        """
        Returns (destination_url: Optional[str], status_code: int, error_or_auth_message: Optional[str], interstitial_data: Optional[dict])
        """
        # 1. Parse host vs primary domain
        if is_system_domain(host):
            domain_name = None
        else:
            domain_name = host.split(":")[0].lower()

        cache_key = f"link:{domain_name or 'default'}:{slug}"
        link_data = None

        # 2. Check Redis Cache (Ultra-Fast Path)
        if redis_cli:
            try:
                cached_json = await redis_cli.get(cache_key)
                if cached_json == "NULL":
                    return None, 404, "Link not found", None
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
                    # Fallback to default domain link if custom domain is not registered
                    query = query.where(ShortLink.domain_id.is_(None))
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
                if custom_domain_obj and custom_domain_obj.custom_not_found_url:
                    return custom_domain_obj.custom_not_found_url, 302, None, None
                return None, 404, "Link not found", None

            link_data = {
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

            if redis_cli:
                try:
                    await redis_cli.set(cache_key, json.dumps(link_data), ex=settings.CACHE_DEFAULT_TTL)
                except Exception:
                    pass

        # 4. Check Link Active
        if not link_data.get("is_active", True):
            return None, 410, "This link has been deactivated.", None

        # 5. Check Expiration & Expired Fallback (Dub.co standard)
        if link_data.get("expires_at"):
            try:
                exp_dt = datetime.fromisoformat(link_data["expires_at"])
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=UTC)
                if datetime.now(UTC) > exp_dt:
                    if link_data.get("expired_url"):
                        return link_data["expired_url"], 307, None, None
                    return None, 410, "This link has expired.", None
            except Exception:
                pass

        # 6. Password Protection
        if link_data.get("has_password") and not password:
            return None, 401, "Password required for this short link.", None

        # 7. Device, Geo & Bot Detection
        is_bot, device_type, browser, os_name = parse_user_agent(user_agent)
        anon_ip = anonymize_ip(client_ip)
        country_code, _country_name, city = lookup_ip_location(anon_ip)

        # 8. Dynamic Target Resolution (Geo-Targeting > Device-Targeting > Default)
        target_url = link_data["destination_url"]
        geo_map = link_data.get("geo_targets") or {}

        if country_code in geo_map:
            target_url = geo_map[country_code]
        elif os_name == "iOS" and link_data.get("ios_destination"):
            target_url = link_data["ios_destination"]
        elif os_name == "Android" and link_data.get("android_destination"):
            target_url = link_data["android_destination"]

        # 9. Asynchronous Click Event Dispatch (Redis Stream or Direct DB Fallback)
        if redis_cli:
            try:
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
        else:
            # Standalone / Zero-Redis Fallback (Render Free Tier, Local Testing, Demo Instances)
            try:
                from pulseroute.models.click import ClickEvent
                click_rec = ClickEvent(
                    link_id=link_data["id"],
                    country_code=country_code,
                    city=city,
                    device_type=device_type,
                    browser=browser,
                    os=os_name,
                    referrer=referrer,
                    is_bot=is_bot,
                )
                db.add(click_rec)
                from sqlalchemy import func, update
                await db.execute(
                    update(ShortLink)
                    .where(ShortLink.id == link_data["id"])
                    .values(total_clicks=func.coalesce(ShortLink.total_clicks, 0) + 1)
                )
                await db.commit()
            except Exception:
                pass

        # 10. Interstitial / Ad delay check
        interstitial_data = None
        if link_data.get("interstitial_delay", 0) > 0 and not is_bot:
            # Fallback to server global AdSense client ID if configured
            adsense_client = link_data.get("adsense_client_id") or settings.GLOBAL_ADSENSE_CLIENT_ID
            interstitial_data = {
                "delay": link_data["interstitial_delay"],
                "target_url": target_url,
                "ad_html": link_data.get("interstitial_ad_html"),
                "title": link_data.get("interstitial_title"),
                "adsense_client_id": adsense_client,
                "adsense_slot_id": link_data.get("adsense_slot_id"),
            }

        return target_url, settings.DEFAULT_REDIRECT_STATUS, None, interstitial_data
