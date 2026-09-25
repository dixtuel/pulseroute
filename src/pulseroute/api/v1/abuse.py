from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Optional
from urllib.parse import urlparse

import redis.asyncio as aioredis
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.common.privacy import anonymize_ip, extract_client_ip, generate_reporter_fingerprint
from pulseroute.common.rate_limiter import SlidingWindowRateLimiter
from pulseroute.core.config import settings
from pulseroute.core.database import get_db
from pulseroute.core.redis import get_redis
from pulseroute.models.abuse import AbuseReport
from pulseroute.models.link import ShortLink
from pulseroute.services.link_service import LinkService

logger = structlog.get_logger()
router = APIRouter(prefix="/abuse", tags=["Abuse & Security Reporting"])


class AbuseReason(str, Enum):
    PHISHING = "phishing"
    MALWARE = "malware"
    ILLEGAL_CONTENT = "illegal_content"
    COPYRIGHT = "copyright"
    SPAM = "spam"
    OTHER = "other"


class AbuseReportRequest(BaseModel):
    short_url_or_slug: str = Field(..., min_length=1, max_length=2048, description="Slug or full short URL")
    reason: AbuseReason = Field(..., description="Nature of the violation")
    reporter_email: EmailStr = Field(..., description="Contact email of the reporter for verification")
    details: Optional[str] = Field(None, max_length=2000, description="Additional context or evidence")


def extract_slug(input_str: str) -> str:
    """Extracts clean slug from either raw slug or full URL."""
    clean = input_str.strip()
    if clean.startswith(("http://", "https://")):
        parsed = urlparse(clean)
        path = parsed.path.strip("/")
        # If there are subpaths, take the last segment or first
        clean = path.split("/")[-1] if path else ""
    return clean.rstrip("+").strip()


@router.post("/report", status_code=status.HTTP_202_ACCEPTED)
async def report_abuse(
    payload: AbuseReportRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis_cli: Optional[aioredis.Redis] = Depends(get_redis),
):
    client_ip = extract_client_ip(request)

    # Rate limiting: Max 15 reports per hour per IP to prevent griefing/abuse of reporting channel
    allowed, rem = await SlidingWindowRateLimiter.is_allowed(
        redis_cli, key=f"abuse_report:{client_ip}", limit=15, window_seconds=3600
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many abuse reports submitted from this IP. Please try again later.",
        )

    slug = extract_slug(payload.short_url_or_slug)
    if not slug:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract a valid short link identifier or slug from the input.",
        )

    # 1. Locate the link in the database
    query = select(ShortLink).where(ShortLink.slug == slug).with_for_update()
    res = await db.execute(query)
    link = res.scalars().first()

    if not link:
        logger.info("abuse_report_link_not_found", slug=slug, reporter=payload.reporter_email)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Short link not found for slug '{slug}'.",
        )

    # Keep only a keyed digest of transient request signals; raw UA/language/IP are not stored.
    fingerprint = generate_reporter_fingerprint(
        client_ip=client_ip,
        user_agent=request.headers.get("user-agent", ""),
        accept_language=request.headers.get("accept-language", ""),
        secret_key=settings.SECRET_KEY,
    )
    dedupe_cutoff = datetime.now(UTC) - timedelta(seconds=settings.ABUSE_REPORT_DEDUP_WINDOW_SECONDS)
    duplicate = await db.execute(
        select(AbuseReport.id)
        .where(
            AbuseReport.slug == link.slug,
            AbuseReport.reporter_fingerprint == fingerprint,
            AbuseReport.created_at >= dedupe_cutoff,
        )
        .limit(1)
    )
    if duplicate.scalar_one_or_none() is not None:
        return {
            "status": "duplicate",
            "slug": link.slug,
            "action_taken": "A recent report from this browser and network was already recorded.",
            "message": "Bu bağlantı için yakın zamanda aynı cihaz ve ağdan bildirim alındı.",
        }

    # Record the formal Abuse Report for 5651 Sayılı Kanun and Safe Harbor auditability.
    masked_ip = anonymize_ip(client_ip)
    report = AbuseReport(
        link_id=link.id,
        slug=link.slug,
        reason=payload.reason.value,
        details=payload.details,
        reporter_email=str(payload.reporter_email),
        reporter_ip=masked_ip,
        reporter_fingerprint=fingerprint,
        status="quarantined" if payload.reason in (AbuseReason.PHISHING, AbuseReason.MALWARE) else "pending",
        created_at=datetime.now(UTC),
    )
    db.add(report)

    # High-Priority Automated Quarantine & Deletion Policy:
    # If cumulative report count reaches deletion threshold, permanently remove link.
    # If reported for Phishing/Malware or cumulative report count reaches quarantine threshold, immediately quarantine.
    current_reports = (link.abuse_reports_count or 0) + 1
    link.abuse_reports_count = current_reports
    await db.flush()

    if current_reports >= settings.ABUSE_AUTO_DELETE_REPORT_THRESHOLD:
        report.status = "deleted"
        await db.commit()
        await LinkService.delete_link(db, redis_cli, link.id)
        logger.critical(
            "abuse_link_automatically_deleted",
            slug=slug,
            reports_count=current_reports,
            reason=payload.reason.value,
        )
        return {
            "status": "deleted",
            "slug": slug,
            "action_taken": "Link has been permanently removed due to exceeding the maximum abuse report threshold.",
            "message": "Bağlantı çok sayıda şikayet alması nedeniyle sistemden kalıcı olarak silinmiştir.",
        }

    is_quarantined = False
    action_status = "received"
    if (
        payload.reason in (AbuseReason.PHISHING, AbuseReason.MALWARE)
        or current_reports >= settings.ABUSE_QUARANTINE_REPORT_THRESHOLD
    ):
        is_quarantined = True
        action_status = "quarantined"
        report.status = "quarantined"
        quarantine_reason = f"Notice-and-takedown quarantine: reported as {payload.reason.value} ({current_reports} reports)"
        await LinkService.quarantine_link(db, redis_cli, slug=link.slug, reason=quarantine_reason)
        logger.error(
            "abuse_link_automatically_quarantined",
            slug=link.slug,
            link_id=link.id,
            reason=payload.reason.value,
            reports_count=current_reports,
        )
    else:
        await db.commit()
        logger.warning(
            "abuse_report_queued_for_review",
            slug=link.slug,
            link_id=link.id,
            reason=payload.reason.value,
            reports_count=current_reports,
        )

    return {
        "status": action_status,
        "slug": link.slug,
        "action_taken": (
            "Link has been quarantined immediately and redirection halted pending formal review."
            if is_quarantined
            else "Report has been safely logged and prioritized for compliance review within 24 hours."
        ),
        "message": (
            "Bağlantı 5651 Sayılı Kanun ve Güvenlik İlkelerimiz kapsamında derhal karantinaya alınmış ve erişimi durdurulmuştur."
            if is_quarantined
            else "Bildiriminiz alınmıştır. İnceleme en geç 24 saat içinde tamamlanacaktır."
        ),
    }
