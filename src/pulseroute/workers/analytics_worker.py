import asyncio
from datetime import UTC, datetime

import structlog
from sqlalchemy import func, update

from pulseroute.core.database import async_session_maker
from pulseroute.core.redis import get_redis
from pulseroute.models.click import ClickEvent
from pulseroute.models.link import ShortLink

logger = structlog.get_logger()


async def run_analytics_batch_worker(batch_size: int = 100, interval_seconds: float = 2.0):
    """
    Consumes click events in batches from Redis Stream and persists them to Database.
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

    while True:
        try:
            entries = await redis_cli.xreadgroup(
                groupname=group_name,
                consumername=consumer_name,
                streams={stream_name: ">"},
                count=batch_size,
                block=int(interval_seconds * 1000),
            )

            if not entries:
                await asyncio.sleep(interval_seconds)
                continue

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
                            update(ShortLink).where(ShortLink.id == l_id).values(total_clicks=func.coalesce(ShortLink.total_clicks, 0) + count)
                        )
                    await db.commit()

            # Acknowledge messages
            if msg_ids_to_ack:
                await redis_cli.xack(stream_name, group_name, *msg_ids_to_ack)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("analytics_worker_exception", error=str(e))
            await asyncio.sleep(2.0)
