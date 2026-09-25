import redis.asyncio as aioredis
import structlog

from pulseroute.core.config import settings

logger = structlog.get_logger()

redis_client: aioredis.Redis | None = None
analytics_redis_client: aioredis.Redis | None = None


def normalize_redis_url(url: str) -> str:
    """Ensures SSL/TLS scheme for cloud Redis providers like Upstash."""
    clean = url.strip()
    if "upstash.io" in clean and clean.startswith("redis://"):
        clean = clean.replace("redis://", "rediss://", 1)
    return clean


async def get_redis() -> aioredis.Redis | None:
    global redis_client
    if redis_client is None and settings.REDIS_URL:
        try:
            formatted_url = normalize_redis_url(settings.REDIS_URL)
            redis_client = _create_client(formatted_url)
            await redis_client.ping()
        except Exception as e:
            logger.warning("redis_connect_failed", error=repr(e))
            if redis_client:
                await redis_client.aclose()
            redis_client = None
    return redis_client


def _create_client(url: str) -> aioredis.Redis:
    return aioredis.from_url(
        url,
        encoding="utf-8",
        decode_responses=True,
        socket_timeout=3.0,
        socket_connect_timeout=3.0,
        retry_on_timeout=True,
        health_check_interval=30,
        max_connections=20,  # Bound each process's connection pool without relying on a plan limit.
    )


async def get_analytics_redis() -> aioredis.Redis | None:
    """Return the configured analytics stream backend, or share the general Redis backend."""
    global analytics_redis_client
    analytics_url = settings.ANALYTICS_REDIS_URL
    if not analytics_url:
        return await get_redis()

    normalized_url = normalize_redis_url(analytics_url)
    primary_url = normalize_redis_url(settings.REDIS_URL) if settings.REDIS_URL else None
    if normalized_url == primary_url:
        return await get_redis()

    if analytics_redis_client is None:
        try:
            analytics_redis_client = _create_client(normalized_url)
            await analytics_redis_client.ping()
        except Exception as e:
            logger.warning("analytics_redis_connect_failed", error=repr(e))
            if analytics_redis_client:
                await analytics_redis_client.aclose()
            analytics_redis_client = None
    return analytics_redis_client


async def close_redis() -> None:
    global redis_client, analytics_redis_client
    if analytics_redis_client:
        await analytics_redis_client.aclose()
        analytics_redis_client = None
    if redis_client:
        await redis_client.aclose()
        redis_client = None
