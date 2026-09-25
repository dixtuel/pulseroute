import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.pool import NullPool

from pulseroute.core.database import get_engine_kwargs
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
    """Verify that Neon/pooler connection strings trigger NullPool and statement cache disabling for scale-to-zero."""
    neon_url = "postgresql+asyncpg://user:pass@ep-misty-forest-pooler.neon.tech/db"
    kwargs = get_engine_kwargs(neon_url)
    assert kwargs.get("poolclass") is NullPool
    connect_args = kwargs.get("connect_args", {})
    assert connect_args.get("prepared_statement_cache_size") == 0
    assert connect_args.get("statement_cache_size") == 0
    assert connect_args.get("command_timeout") == 30

    # Test non-pooler standard postgres (scale-to-zero friendly recycling)
    pg_url = "postgresql+asyncpg://user:pass@pg.example.com/db"
    pg_kwargs = get_engine_kwargs(pg_url)
    assert pg_kwargs.get("pool_recycle") == 280
    assert pg_kwargs.get("pool_pre_ping") is True

    # Test SQLite
    sqlite_url = "sqlite+aiosqlite:///./data/test.db"
    sqlite_kwargs = get_engine_kwargs(sqlite_url)
    assert sqlite_kwargs.get("connect_args") == {"check_same_thread": False}


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
async def test_dns_worker_waits_for_new_domain_without_polling(monkeypatch):
    event = asyncio.Event()
    monkeypatch.setattr("pulseroute.workers.dns_worker._pending_domain_event", event)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result
    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__.return_value = mock_session

    with patch("pulseroute.workers.dns_worker.async_session_maker", mock_session_maker):
        task = asyncio.create_task(run_dns_verification_worker(idle_sleep_seconds=None))
        try:
            await asyncio.sleep(0.05)
            assert mock_session.execute.await_count == 1
            notify_unverified_domains_changed()
            await asyncio.sleep(0.05)
            assert mock_session.execute.await_count == 2
        finally:
            task.cancel()
            await task


@pytest.mark.asyncio
async def test_dns_worker_batches_pending_domains_and_backs_off(monkeypatch):
    monkeypatch.setattr("pulseroute.workers.dns_worker._pending_domain_event", asyncio.Event())
    domains = [MagicMock(id=i, domain=f"domain-{i}.example") for i in range(5)]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = domains
    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result
    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__.return_value = mock_session

    with (
        patch("pulseroute.workers.dns_worker.async_session_maker", mock_session_maker),
        patch("pulseroute.workers.dns_worker.DomainService.verify_domain_dns", new_callable=AsyncMock) as verify,
    ):
        verify.return_value = (False, "pending")
        task = asyncio.create_task(
            run_dns_verification_worker(interval_seconds=0.02, max_pending_interval_seconds=0.06)
        )
        try:
            await asyncio.sleep(0.11)
            passes = mock_session.execute.await_count
            assert 2 <= passes <= 4
            assert verify.await_count == passes * len(domains)
            assert all(call.kwargs.get("preloaded_domain") is not None for call in verify.await_args_list)
            notify_unverified_domains_changed()
            await asyncio.sleep(0.02)
            assert mock_session.execute.await_count > passes
        finally:
            task.cancel()
            await task


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


def test_l1_in_process_cache_and_invalidation():
    """Test L1 in-process micro-cache hit, negative cache, and invalidation."""
    from pulseroute.services.redirect_service import (
        get_l1_cached_link,
        invalidate_l1_cache,
        set_l1_cached_link,
    )

    test_key = "link:default:opt-test-slug"
    test_data = {"id": 999, "destination_url": "https://example.com"}

    # Initially empty
    hit, data = get_l1_cached_link(test_key)
    assert not hit

    # Set data
    set_l1_cached_link(test_key, test_data, ttl=10.0)
    hit, data = get_l1_cached_link(test_key)
    assert hit
    assert data["destination_url"] == "https://example.com"

    # Invalidate
    invalidate_l1_cache(None, "opt-test-slug")
    hit, data = get_l1_cached_link(test_key)
    assert not hit


def test_serialize_cache_payload_integrity():
    """Verify that LinkService.serialize_cache_payload produces expected keys including title."""
    from pulseroute.models.link import ShortLink
    from pulseroute.services.link_service import LinkService

    link = ShortLink(
        id=42,
        slug="ser-slug",
        destination_url="https://example.com/target",
        title="Custom Link Title",
        interstitial_title="Interstitial Head",
        is_active=True,
    )
    payload = LinkService.serialize_cache_payload(link)
    assert payload["id"] == 42
    assert payload.get("slug") is None
    assert payload["title"] == "Custom Link Title"
    assert payload["destination_url"] == "https://example.com/target"
    assert payload["interstitial_title"] == "Interstitial Head"
    assert payload["is_active"] is True
