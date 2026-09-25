from unittest.mock import AsyncMock

import pytest

from pulseroute.common.rate_limiter import (
    _MAX_LIMITER_STORE_SIZE,
    SlidingWindowRateLimiter,
    _memory_limiter_store,
)
from pulseroute.core.security_middleware import (
    _MAX_MEMORY_JAIL_SIZE,
    BruteForceGuard,
    _memory_jail,
)


@pytest.mark.asyncio
async def test_memory_fallback_rate_limiter():
    key = "test_ip_1"
    limit = 3
    # First 3 should pass
    for i in range(3):
        allowed, remaining = await SlidingWindowRateLimiter.is_allowed(None, key, limit=limit, window_seconds=60)
        assert allowed is True
        assert remaining == limit - i - 1

    # 4th should be blocked
    allowed, remaining = await SlidingWindowRateLimiter.is_allowed(None, key, limit=limit, window_seconds=60)
    assert allowed is False
    assert remaining == 0


@pytest.mark.asyncio
async def test_rate_limiter_unique_member():
    """Test that rate limiter passes unique member to Lua script to avoid collisions."""
    mock_redis = AsyncMock()
    mock_redis.eval.return_value = [1, 9]

    allowed, remaining = await SlidingWindowRateLimiter.is_allowed(
        mock_redis,
        key="test_ip",
        limit=10,
        window_seconds=60,
    )

    assert allowed is True
    assert remaining == 9
    assert mock_redis.eval.called
    call_args = mock_redis.eval.call_args[0]
    assert len(call_args) >= 7  # script, numkeys, key, now, window, limit, unique_member


@pytest.mark.asyncio
async def test_rate_limiter_in_memory_eviction():
    """Verify that SlidingWindowRateLimiter evicts expired timestamps when capacity is exceeded."""
    _memory_limiter_store.clear()
    old_time = 1000.0
    for i in range(_MAX_LIMITER_STORE_SIZE + 50):
        _memory_limiter_store[f"key_{i}"] = [old_time]

    assert len(_memory_limiter_store) > _MAX_LIMITER_STORE_SIZE
    allowed, _ = await SlidingWindowRateLimiter.is_allowed(None, "new_key", limit=10, window_seconds=60)
    assert allowed is True
    assert len(_memory_limiter_store) <= _MAX_LIMITER_STORE_SIZE
    _memory_limiter_store.clear()


@pytest.mark.asyncio
async def test_memory_jail_eviction():
    """Verify that BruteForceGuard evicts stale IP records when capacity is exceeded."""
    _memory_jail.clear()
    old_time = 1000.0
    for i in range(_MAX_MEMORY_JAIL_SIZE + 50):
        _memory_jail[f"192.168.1.{i}"] = [old_time]

    assert len(_memory_jail) > _MAX_MEMORY_JAIL_SIZE
    await BruteForceGuard.is_ip_jailed(None, "10.0.0.1")
    assert len(_memory_jail) <= _MAX_MEMORY_JAIL_SIZE
    _memory_jail.clear()
