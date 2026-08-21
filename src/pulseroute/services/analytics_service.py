from datetime import UTC, datetime, timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.models.click import ClickEvent
from pulseroute.models.link import ShortLink
from pulseroute.schemas.analytics import AnalyticsSummaryResponse, BreakdownItem, TimeSeriesPoint


class AnalyticsService:
    @staticmethod
    async def get_link_analytics(
        db: AsyncSession,
        link_id: int | None = None,
        days: int = 7,
    ) -> AnalyticsSummaryResponse:
        since_time = datetime.now(UTC) - timedelta(days=days)

        base_query = select(ClickEvent).where(ClickEvent.clicked_at >= since_time)
        if link_id:
            base_query = base_query.where(ClickEvent.link_id == link_id)

        # 1. Total clicks
        total_clicks_res = await db.execute(
            select(func.count(ClickEvent.id)).where(ClickEvent.clicked_at >= since_time).filter(ClickEvent.link_id == link_id if link_id else True)
        )
        total_clicks = total_clicks_res.scalar() or 0

        # 2. Bot clicks
        bot_clicks_res = await db.execute(
            select(func.count(ClickEvent.id)).where(ClickEvent.clicked_at >= since_time, ClickEvent.is_bot.is_(True)).filter(ClickEvent.link_id == link_id if link_id else True)
        )
        bot_clicks = bot_clicks_res.scalar() or 0

        # Helper for breakdown
        async def get_breakdown(column) -> list[BreakdownItem]:
            query = (
                select(column, func.count(ClickEvent.id).label("cnt"))
                .where(ClickEvent.clicked_at >= since_time)
                .filter(ClickEvent.link_id == link_id if link_id else True)
                .group_by(column)
                .order_by(desc("cnt"))
                .limit(10)
            )
            res = await db.execute(query)
            items = []
            for name, count in res.all():
                val = name if name else "Direct / None"
                pct = round((count / total_clicks * 100), 1) if total_clicks > 0 else 0.0
                items.append(BreakdownItem(name=str(val), count=count, percentage=pct))
            return items

        countries = await get_breakdown(ClickEvent.country_code)
        devices = await get_breakdown(ClickEvent.device_type)
        browsers = await get_breakdown(ClickEvent.browser)
        os_list = await get_breakdown(ClickEvent.os)
        referrers = await get_breakdown(ClickEvent.referrer)

        # Timeseries
        timeseries = [
            TimeSeriesPoint(timestamp=(datetime.now(UTC) - timedelta(days=i)).strftime("%Y-%m-%d"), clicks=0)
            for i in range(days - 1, -1, -1)
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
