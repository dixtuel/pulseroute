
import redis.asyncio as aioredis

from pulseroute.core.config import settings

redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis | None:
    global redis_client
    if redis_client is None and settings.REDIS_URL:
        try:
            redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=2.0,
            )
            await redis_client.ping()
        except Exception:
            redis_client = None
    return redis_client


async def close_redis() -> None:
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
