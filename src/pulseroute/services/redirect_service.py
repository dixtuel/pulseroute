import asyncio
import time
from datetime import UTC, datetime
from typing import Optional, Tuple

import orjson
import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.common.bot_detector import parse_user_agent
from pulseroute.common.geoip import lookup_ip_location
from pulseroute.common.privacy import anonymize_ip
from pulseroute.core.config import settings
from pulseroute.models.domain import CustomDomain
from pulseroute.models.link import ShortLink


def is_primary_domain(host: str) -> bool:
    """Checks if the request host matches the configured PRIMARY_DOMAIN or local test loopbacks."""
    clean_host = host.split(":")[0].lower()
    primary_host = settings.PRIMARY_DOMAIN.split(":")[0].lower()
    return clean_host in (primary_host, "localhost", "127.0.0.1", "0.0.0.0", "testserver", "testclient")


# L1 in-process micro-cache to eliminate Upstash command burnout during traffic spikes
_l1_cache: dict[str, tuple[float, Optional[dict]]] = {}
_L1_TTL = 5.0
_L1_MAX_SIZE = 2000

# Singleflight in-process coordination locks to avoid thundering herd on cache misses
_inflight_locks: dict[str, asyncio.Lock] = {}
_inflight_master_lock = asyncio.Lock()


def get_l1_cached_link(key: str) -> tuple[bool, Optional[dict]]:
    """Returns (is_cached: bool, link_data: Optional[dict])."""
    item = _l1_cache.get(key)
    if item:
        exp, data = item
        if time.time() < exp:
            return True, data
        _l1_cache.pop(key, None)
    return False, None


def set_l1_cached_link(key: str, data: Optional[dict], ttl: float = _L1_TTL) -> None:
    if len(_l1_cache) > _L1_MAX_SIZE:
        now = time.time()
        expired = [k for k, (exp, _) in _l1_cache.items() if exp <= now]
        for k in expired:
            _l1_cache.pop(k, None)
        if len(_l1_cache) > _L1_MAX_SIZE:
            to_remove = list(_l1_cache.keys())[: _L1_MAX_SIZE // 5]
            for k in to_remove:
                _l1_cache.pop(k, None)
    _l1_cache[key] = (time.time() + ttl, data)


def invalidate_l1_cache(domain_name: Optional[str], slug: str) -> None:
    key = f"link:{domain_name or 'default'}:{slug}"
    _l1_cache.pop(key, None)


class RedirectService:
    @staticmethod
    def invalidate_l1(domain_name: Optional[str], slug: str) -> None:
        invalidate_l1_cache(domain_name, slug)

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
        analytics_redis_cli: Optional[aioredis.Redis] = None,
    ) -> Tuple[Optional[str], int, Optional[str], Optional[dict]]:
        """
        Returns (destination_url: Optional[str], status_code: int, error_or_auth_message: Optional[str], interstitial_data: Optional[dict])
        """
        # 1. Parse host vs primary domain
        if is_primary_domain(host):
            domain_name = None
        else:
            domain_name = host.split(":")[0].lower()

        cache_key = f"link:{domain_name or 'default'}:{slug}"
        link_data = None

        # 2. Check L1 In-Process Micro-Cache First (0ms, 0 Upstash commands)
        is_hit, l1_data = get_l1_cached_link(cache_key)
        if is_hit:
            if l1_data is None:
                return None, 404, "Link not found", None
            link_data = l1_data

        # 3. Check Redis Cache (Ultra-Fast Path)
        if not link_data and redis_cli:
            try:
                cached_json = await redis_cli.get(cache_key)
                if cached_json == "NULL":
                    set_l1_cached_link(cache_key, None, ttl=min(_L1_TTL, float(settings.NEGATIVE_CACHE_TTL)))
                    return None, 404, "Link not found", None
                if cached_json:
                    link_data = orjson.loads(cached_json)
                    set_l1_cached_link(cache_key, link_data, ttl=_L1_TTL)
            except Exception:
                pass

        # 4. Cache Miss: Fallback to Database with Singleflight Protection
        if not link_data:
            async with _inflight_master_lock:
                if cache_key not in _inflight_locks:
                    _inflight_locks[cache_key] = asyncio.Lock()
                flight_lock = _inflight_locks[cache_key]

            async with flight_lock:
                # Double-check L1 and Redis in case a concurrent flight resolved it
                is_hit, l1_data = get_l1_cached_link(cache_key)
                if is_hit:
                    if l1_data is None:
                        return None, 404, "Link not found", None
                    link_data = l1_data
                elif redis_cli:
                    try:
                        cached_json = await redis_cli.get(cache_key)
                        if cached_json == "NULL":
                            set_l1_cached_link(cache_key, None, ttl=min(_L1_TTL, float(settings.NEGATIVE_CACHE_TTL)))
                            return None, 404, "Link not found", None
                        if cached_json:
                            link_data = orjson.loads(cached_json)
                            set_l1_cached_link(cache_key, link_data, ttl=_L1_TTL)
                    except Exception:
                        pass

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
                        set_l1_cached_link(cache_key, None, ttl=min(_L1_TTL, float(settings.NEGATIVE_CACHE_TTL)))
                        if redis_cli:
                            try:
                                await redis_cli.set(cache_key, "NULL", ex=settings.NEGATIVE_CACHE_TTL)
                            except Exception:
                                pass
                        if custom_domain_obj and custom_domain_obj.custom_not_found_url:
                            return custom_domain_obj.custom_not_found_url, 302, None, None
                        return None, 404, "Link not found", None

                    from pulseroute.services.link_service import LinkService

                    link_data = LinkService.serialize_cache_payload(link)
                    set_l1_cached_link(cache_key, link_data, ttl=_L1_TTL)
                    if redis_cli:
                        try:
                            await redis_cli.set(
                                cache_key, orjson.dumps(link_data).decode(), ex=settings.CACHE_DEFAULT_TTL
                            )
                        except Exception:
                            pass

            async with _inflight_master_lock:
                if not flight_lock.locked() and cache_key in _inflight_locks:
                    _inflight_locks.pop(cache_key, None)

        # 4. Check Quarantine & Link Active
        if link_data.get("is_quarantined"):
            reason = link_data.get("quarantine_reason") or "Abuse or phishing violation"
            return None, 451, f"Security Warning: This link has been quarantined ({reason}).", None

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
        event_redis = analytics_redis_cli or redis_cli
        if event_redis:
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
                await event_redis.xadd(
                    "pulseroute:events:clicks",
                    event_payload,
                    maxlen=settings.ANALYTICS_STREAM_MAXLEN,
                    approximate=True,
                )
                try:
                    from pulseroute.workers.analytics_worker import notify_click_event_published

                    notify_click_event_published()
                except Exception:
                    pass
            except Exception:
                pass
        else:
            # Standalone / Zero-Redis Fallback (no Redis configured: local testing, demo instances)
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

        # 10. Browser interstitial metadata (timing is enforced by the redirect router)
        interstitial_data = None
        adsense_client = link_data.get("adsense_client_id") or settings.GLOBAL_ADSENSE_CLIENT_ID
        adsense_slot = (
            link_data.get("adsense_slot_id")
            or settings.GLOBAL_ADSENSE_REDIRECT_SLOT_ID
            or settings.GLOBAL_ADSENSE_SLOT_ID
        )

        if not is_bot:
            interstitial_data = {
                "target_url": target_url,
                "ad_html": link_data.get("interstitial_ad_html"),
                "title": link_data.get("interstitial_title") or link_data.get("title"),
                "adsense_client_id": adsense_client,
                "adsense_slot_id": adsense_slot,
            }

        return target_url, settings.DEFAULT_REDIRECT_STATUS, None, interstitial_data
