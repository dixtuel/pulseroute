import time

import redis.asyncio as aioredis

LUA_SLIDING_WINDOW_RATE_LIMITER = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4] or ARGV[1]

-- Remove timestamps older than window
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)

-- Count requests in current window
local current_requests = redis.call('ZCARD', key)

if current_requests < limit then
    redis.call('ZADD', key, now, member)
    redis.call('EXPIRE', key, window)
    return {1, limit - current_requests - 1}
else
    return {0, 0}
end
"""

# In-memory fallback dictionary if Redis is down: {key: [(timestamp)]}
_memory_limiter_store: dict[str, list[float]] = {}
_MAX_LIMITER_STORE_SIZE = 2000


def _cleanup_limiter_store(now: float, window_seconds: int) -> None:
    if len(_memory_limiter_store) > _MAX_LIMITER_STORE_SIZE:
        cutoff = now - window_seconds
        stale_keys = [k for k, ts_list in _memory_limiter_store.items() if not ts_list or ts_list[-1] <= cutoff]
        for k in stale_keys:
            _memory_limiter_store.pop(k, None)
        if len(_memory_limiter_store) > _MAX_LIMITER_STORE_SIZE:
            for k in list(_memory_limiter_store.keys())[: _MAX_LIMITER_STORE_SIZE // 5]:
                _memory_limiter_store.pop(k, None)


class SlidingWindowRateLimiter:
    @staticmethod
    async def is_allowed(
        redis_cli: aioredis.Redis | None,
        key: str,
        limit: int,
        window_seconds: int = 60,
    ) -> tuple[bool, int]:
        """
        Returns (is_allowed: bool, remaining_requests: int)
        """
        now = time.time()
        if redis_cli:
            try:
                unique_member = f"{now}:{time.time_ns() % 1000000}"
                result = await redis_cli.eval(
                    LUA_SLIDING_WINDOW_RATE_LIMITER,
                    1,
                    f"ratelimit:{key}",
                    str(now),
                    str(window_seconds),
                    str(limit),
                    unique_member,
                )
                allowed = bool(result[0] == 1)
                remaining = int(result[1])
                return allowed, remaining
            except Exception:
                pass

        # In-memory fallback
        _cleanup_limiter_store(now, window_seconds)
        timestamps = _memory_limiter_store.get(key, [])
        cutoff = now - window_seconds
        timestamps = [ts for ts in timestamps if ts > cutoff]

        if len(timestamps) < limit:
            timestamps.append(now)
            _memory_limiter_store[key] = timestamps
            return True, limit - len(timestamps)
        else:
            _memory_limiter_store[key] = timestamps
            return False, 0
