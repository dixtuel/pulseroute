from datetime import UTC, datetime, timedelta
from typing import List, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.models.click import ClickEvent
from pulseroute.models.link import ShortLink
from pulseroute.schemas.analytics import AnalyticsSummaryResponse, BreakdownItem, TimeSeriesPoint


def clean_referrer_name(referrer: Optional[str]) -> str:
    """Cleans raw referrers into human-readable brand names."""
    if not referrer:
        return "Direct / None"
    ref_lower = referrer.lower()
    if "t.co" in ref_lower or "twitter.com" in ref_lower or "x.com" in ref_lower:
        return "Twitter / X"
    elif "instagram.com" in ref_lower:
        return "Instagram"
    elif "facebook.com" in ref_lower or "fb.me" in ref_lower:
        return "Facebook"
    elif "linkedin.com" in ref_lower or "lnkd.in" in ref_lower:
        return "LinkedIn"
    elif "youtube.com" in ref_lower or "youtu.be" in ref_lower:
        return "YouTube"
    elif "google." in ref_lower:
        return "Google Search"
    elif "github.com" in ref_lower:
        return "GitHub"
    elif "reddit.com" in ref_lower:
        return "Reddit"

    # Strip protocol and path
    try:
        from urllib.parse import urlparse
        parsed = urlparse(referrer)
        return parsed.hostname or referrer[:30]
    except Exception:
        return referrer[:30]


class AnalyticsService:
    @staticmethod
    async def get_link_analytics(
        db: AsyncSession,
        link_id: Optional[int] = None,
        days: int = 7,
    ) -> AnalyticsSummaryResponse:
        since_time = datetime.now(UTC) - timedelta(days=days)

        # 1. Total clicks
        total_clicks_query = select(func.count(ClickEvent.id)).where(ClickEvent.clicked_at >= since_time)
        if link_id:
            total_clicks_query = total_clicks_query.where(ClickEvent.link_id == link_id)
        total_clicks_res = await db.execute(total_clicks_query)
        total_clicks = total_clicks_res.scalar() or 0

        # 2. Bot clicks
        bot_query = select(func.count(ClickEvent.id)).where(ClickEvent.clicked_at >= since_time, ClickEvent.is_bot.is_(True))
        if link_id:
            bot_query = bot_query.where(ClickEvent.link_id == link_id)
        bot_clicks_res = await db.execute(bot_query)
        bot_clicks = bot_clicks_res.scalar() or 0

        # Helper for breakdown
        async def get_breakdown(column, is_referrer: bool = False) -> List[BreakdownItem]:
            query = select(column, func.count(ClickEvent.id).label("cnt")).where(ClickEvent.clicked_at >= since_time)
            if link_id:
                query = query.where(ClickEvent.link_id == link_id)
            query = query.group_by(column).order_by(desc("cnt")).limit(10)

            res = await db.execute(query)
            items = []
            for name, count in res.all():
                if is_referrer:
                    val = clean_referrer_name(name)
                else:
                    val = name if name else "Unknown"
                pct = round((count / total_clicks * 100), 1) if total_clicks > 0 else 0.0
                items.append(BreakdownItem(name=str(val), count=count, percentage=pct))
            return items

        countries = await get_breakdown(ClickEvent.country_code)
        devices = await get_breakdown(ClickEvent.device_type)
        browsers = await get_breakdown(ClickEvent.browser)
        os_list = await get_breakdown(ClickEvent.os)
        referrers = await get_breakdown(ClickEvent.referrer, is_referrer=True)

        # 3. Real Timeseries Aggregation by Day
        timeseries_map: dict[str, int] = {
            (datetime.now(UTC) - timedelta(days=i)).strftime("%Y-%m-%d"): 0
            for i in range(days - 1, -1, -1)
        }

        # Fetch actual clicks per day
        ts_query = select(
            func.date(ClickEvent.clicked_at).label("day"),
            func.count(ClickEvent.id).label("cnt")
        ).where(ClickEvent.clicked_at >= since_time)
        if link_id:
            ts_query = ts_query.where(ClickEvent.link_id == link_id)
        ts_query = ts_query.group_by(func.date(ClickEvent.clicked_at))

        ts_res = await db.execute(ts_query)
        for day_str, count in ts_res.all():
            if str(day_str) in timeseries_map:
                timeseries_map[str(day_str)] = count

        timeseries = [
            TimeSeriesPoint(timestamp=dt, clicks=cnt)
            for dt, cnt in sorted(timeseries_map.items())
        ]

        slug_val = None
        if link_id:
            link_res = await db.execute(select(ShortLink.slug).where(ShortLink.id == link_id))
            slug_val = link_res.scalar_one_or_none()

        return AnalyticsSummaryResponse(
            link_id=link_id,
            slug=slug_val,
            total_clicks=total_clicks,
            unique_visitors=max(0, total_clicks - bot_clicks),
            bot_clicks=bot_clicks,
            timeseries=timeseries,
            countries=countries,
            devices=devices,
            browsers=browsers,
            os=os_list,
            referrers=referrers,
        )
