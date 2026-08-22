from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.api.deps import require_authenticated_user, verify_workspace_access
from pulseroute.core.database import get_db
from pulseroute.models.user import User
from pulseroute.schemas.analytics import AnalyticsSummaryResponse
from pulseroute.services.analytics_service import AnalyticsService
from pulseroute.services.link_service import LinkService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("", response_model=AnalyticsSummaryResponse)
async def get_overview_analytics(
    workspace_id: int,
    link_id: Optional[int] = None,
    days: int = 7,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_workspace_access(workspace_id, current_user, db)

    if link_id:
        link = await LinkService.get_link_by_id(db, link_id)
        if not link or link.workspace_id != workspace_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    return await AnalyticsService.get_link_analytics(db, workspace_id=workspace_id, link_id=link_id, days=days)
