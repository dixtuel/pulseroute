
from pydantic import BaseModel


class BreakdownItem(BaseModel):
    name: str
    count: int
    percentage: float


class TimeSeriesPoint(BaseModel):
    timestamp: str
    clicks: int


class AnalyticsSummaryResponse(BaseModel):
    link_id: int | None = None
    slug: str | None = None
    total_clicks: int
    unique_visitors: int
    bot_clicks: int
    timeseries: list[TimeSeriesPoint]
    countries: list[BreakdownItem]
    devices: list[BreakdownItem]
    browsers: list[BreakdownItem]
    os: list[BreakdownItem]
    referrers: list[BreakdownItem]
