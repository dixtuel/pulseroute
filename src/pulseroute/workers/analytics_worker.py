import asyncio
import time
from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import delete, func, select, update

from pulseroute.core.config import settings
from pulseroute.core.database import async_session_maker
from pulseroute.core.redis import get_redis
from pulseroute.models.click import ClickEvent
from pulseroute.models.link import ShortLink
from pulseroute.services.webhook_service import WebhookService

logger = structlog.get_logger()

# Event triggered when a click event is published to Redis stream
_new_click_event = asyncio.Event()


def notify_click_event_published():
    """Signals the analytics worker that a new click event was pushed to Redis."""
    _new_click_event.set()


async def purge_expired_click_events(retention_days: int) -> int:
    """
    Purges granular ClickEvent records older than 'retention_days' to comply with
    KVKK/GDPR storage limitation principles and protect database storage quotas.
    Aggregate counters (ShortLink.total_clicks) remain permanent and intact.
    """
    if retention_days <= 0:
        return 0

    cutoff_date = datetime.now(UTC) - timedelta(days=retention_days)
    try:
        async with async_session_maker() as db:
            result = await db.execute(delete(ClickEvent).where(ClickEvent.clicked_at < cutoff_date))
            await db.commit()
            deleted = result.rowcount or 0
            if deleted > 0:
                logger.info("expired_click_events_purged", count=deleted, retention_days=retention_days)
            return deleted
    except Exception as e:
        logger.error("analytics_retention_purge_failed", error=str(e))
        return 0


async def run_analytics_batch_worker(
    batch_size: int = 100,
    interval_seconds: float = 2.0,
    max_idle_seconds: float = 60.0,
):
    """
    Consumes click events in batches from Redis Stream and persists them to Database.
    Optimized for serverless Redis (Upstash request limits):
    - Uses adaptive backoff up to 60s when idle to avoid burning API requests/quotas.
    - Wakes up immediately when notify_click_event_published() is called on incoming clicks.
    - Runs a lightweight daily retention pass to purge expired granular click telemetry.
    """
    redis_cli = await get_redis()
    if not redis_cli:
        logger.warning("analytics_worker_no_redis_skipping")
        return

    stream_name = "pulseroute:events:clicks"
    group_name = "pulseroute_analytics_group"
    consumer_name = "worker_1"

    try:
        await redis_cli.xgroup_create(stream_name, group_name, id="0", mkstream=True)
    except Exception:
        pass  # Group already exists

    logger.info("analytics_batch_worker_started", stream=stream_name)

    current_idle = interval_seconds
    last_retention_purge_ts = 0.0

    while True:
        try:
            # Daily retention cleanup (KVKK / GDPR storage minimization)
            now_ts = time.time()
            if now_ts - last_retention_purge_ts >= 86400:
                last_retention_purge_ts = now_ts
                await purge_expired_click_events(settings.ANALYTICS_RETENTION_DAYS)

            _new_click_event.clear()
            entries = await redis_cli.xreadgroup(
                groupname=group_name,
                consumername=consumer_name,
                streams={stream_name: ">"},
                count=batch_size,
                block=int(interval_seconds * 1000),
            )

            if not entries:
                current_idle = min(current_idle * 2, max_idle_seconds)
                try:
                    await asyncio.wait_for(_new_click_event.wait(), timeout=current_idle)
                except asyncio.TimeoutError:
                    pass
                continue

            # Reset idle timeout when active traffic is detected
            current_idle = interval_seconds

            events_to_insert = []
            link_click_counts = {}
            msg_ids_to_ack = []

            for stream, messages in entries:
                for msg_id, data in messages:
                    msg_ids_to_ack.append(msg_id)
                    try:
                        link_id = int(data["link_id"])
                        is_bot = data.get("is_bot") == "1"
                        clicked_at = datetime.fromtimestamp(int(data.get("timestamp", 0)), tz=UTC)

                        events_to_insert.append(
                            ClickEvent(
                                link_id=link_id,
                                country_code=data.get("country_code", "XX"),
                                city=data.get("city", "Unknown"),
                                device_type=data.get("device_type", "desktop"),
                                browser=data.get("browser", "Unknown"),
                                os=data.get("os", "Unknown"),
                                referrer=data.get("referrer") or None,
                                is_bot=is_bot,
                                clicked_at=clicked_at,
                            )
                        )
                        link_click_counts[link_id] = link_click_counts.get(link_id, 0) + 1
                    except Exception as parse_err:
                        logger.error("click_event_parse_error", error=str(parse_err))

            if events_to_insert:
                async with async_session_maker() as db:
                    db.add_all(events_to_insert)
                    # Update aggregate click counters
                    for l_id, count in link_click_counts.items():
                        await db.execute(
                            update(ShortLink)
                            .where(ShortLink.id == l_id)
                            .values(total_clicks=func.coalesce(ShortLink.total_clicks, 0) + count)
                        )
                    await db.commit()

                    # Notify workspace-owned links' webhook subscribers (fire-and-forget)
                    owners = await db.execute(
                        select(ShortLink.id, ShortLink.workspace_id, ShortLink.slug).where(
                            ShortLink.id.in_(link_click_counts.keys())
                        )
                    )
                    for link_id, workspace_id, slug in owners.all():
                        if workspace_id:
                            await WebhookService.notify_workspace(
                                db,
                                workspace_id,
                                "link.clicked",
                                {
                                    "link_id": link_id,
                                    "slug": slug,
                                    "clicks": link_click_counts[link_id],
                                },
                            )

            # Acknowledge messages
            if msg_ids_to_ack:
                await redis_cli.xack(stream_name, group_name, *msg_ids_to_ack)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("analytics_worker_exception", error=str(e))
            await asyncio.sleep(2.0)
