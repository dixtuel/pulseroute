import structlog
from fastapi import APIRouter, status
from pydantic import BaseModel

logger = structlog.get_logger()
router = APIRouter(prefix="/abuse", tags=["Abuse & Security Reporting"])


class AbuseReportRequest(BaseModel):
    short_url_or_slug: str
    reason: str
    reporter_email: str


@router.post("/report", status_code=status.HTTP_202_ACCEPTED)
async def report_abuse(payload: AbuseReportRequest):
    logger.warning("abuse_report_received", slug=payload.short_url_or_slug, reason=payload.reason, reporter=payload.reporter_email)
    return {"status": "received", "message": "Report has been queued for review."}
