import pytest

from pulseroute.common.rate_limiter import SlidingWindowRateLimiter


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
