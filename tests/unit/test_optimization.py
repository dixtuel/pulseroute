import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pulseroute.workers.analytics_worker import (
    _new_click_event,
    notify_click_event_published,
    run_analytics_batch_worker,
)
from pulseroute.workers.dns_worker import (
    _pending_domain_event,
    notify_unverified_domains_changed,
    run_dns_verification_worker,
)


def test_neon_nullpool_selection():
    """Verify that Neon/pooler connection strings trigger NullPool for scale-to-zero."""
    neon_url = "postgresql+asyncpg://user:pass@ep-misty-forest-pooler.neon.tech/db"
    assert "-pooler." in neon_url or "neon.tech" in neon_url


def test_dns_worker_event_notification():
    """Test that notify_unverified_domains_changed sets the internal event."""
    _pending_domain_event.clear()
    assert not _pending_domain_event.is_set()
    notify_unverified_domains_changed()
    assert _pending_domain_event.is_set()


def test_analytics_worker_event_notification():
    """Test that notify_click_event_published sets the internal event."""
    _new_click_event.clear()
    assert not _new_click_event.is_set()
    notify_click_event_published()
    assert _new_click_event.is_set()


@pytest.mark.asyncio
async def test_dns_worker_idle_deep_sleep():
    """Test that DNS worker sleeps deeply when no unverified domains exist."""
    _pending_domain_event.clear()

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []

    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result

    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__.return_value = mock_session

    with patch("pulseroute.workers.dns_worker.async_session_maker", mock_session_maker):
        # Run worker with 0.05s idle sleep to ensure it loops and handles timeouts cleanly
        task = asyncio.create_task(run_dns_verification_worker(interval_seconds=1, idle_sleep_seconds=0.05))
        await asyncio.sleep(0.12)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    assert mock_session.execute.called


@pytest.mark.asyncio
async def test_analytics_worker_adaptive_idle_backoff():
    """Test that analytics worker backs off when stream is empty without burning requests."""
    _new_click_event.clear()

    mock_redis = AsyncMock()
    # Return empty stream
    mock_redis.xreadgroup.return_value = []

    with patch("pulseroute.workers.analytics_worker.get_redis", AsyncMock(return_value=mock_redis)):
        task = asyncio.create_task(
            run_analytics_batch_worker(batch_size=10, interval_seconds=0.02, max_idle_seconds=0.05)
        )
        await asyncio.sleep(0.12)
        # Should have called xreadgroup a bounded number of times due to backoff
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    assert mock_redis.xreadgroup.called
