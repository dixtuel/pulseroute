
import redis.asyncio as aioredis
import structlog

from pulseroute.core.config import settings

logger = structlog.get_logger()

redis_client: aioredis.Redis | None = None


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
            redis_client = aioredis.from_url(
                formatted_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=3.0,
                socket_connect_timeout=3.0,
                retry_on_timeout=True,
            )
            await redis_client.ping()
        except Exception as e:
            logger.warning("redis_connect_failed", error=repr(e))
            redis_client = None
    return redis_client


async def close_redis() -> None:
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
