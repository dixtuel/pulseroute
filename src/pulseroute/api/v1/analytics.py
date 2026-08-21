
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.core.database import get_db
from pulseroute.schemas.analytics import AnalyticsSummaryResponse
from pulseroute.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("", response_model=AnalyticsSummaryResponse)
async def get_overview_analytics(
    link_id: int | None = None,
    days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    return await AnalyticsService.get_link_analytics(db, link_id=link_id, days=days)
