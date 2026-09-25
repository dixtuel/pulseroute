from datetime import UTC, datetime, timedelta
from typing import Literal, Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, Security
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.api.deps import require_authenticated_user, security_scheme
from pulseroute.core.config import settings
from pulseroute.core.database import get_db
from pulseroute.core.moderation_policy import ADMIN_PAGE_SIZE, ADMIN_SESSION_MINUTES
from pulseroute.core.redis import get_redis
from pulseroute.core.security import create_access_token, decode_access_token, verify_password
from pulseroute.core.security_middleware import BruteForceGuard
from pulseroute.models.abuse import AbuseReport
from pulseroute.models.appeal import ModerationAction, ModerationAppeal
from pulseroute.models.link import ShortLink
from pulseroute.models.user import User
from pulseroute.models.workspace import WorkspaceMember

router = APIRouter(prefix="/moderation", tags=["Owner Moderation"])
COOKIE_NAME = "pr_moderation"


class LoginPayload(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=256)


class DecisionPayload(BaseModel):
    decision: Literal["approve", "reject", "quarantine", "release", "ban", "unban"]
    note: str | None = Field(default=None, max_length=1000)


class AppealPayload(BaseModel):
    link_id: int = Field(gt=0)
    details: str = Field(min_length=20, max_length=3000)


def _configured() -> bool:
    return bool(settings.MODERATION_OWNER_EMAIL and settings.MODERATION_OWNER_PASSWORD_HASH)


def _origin_ok(request: Request) -> bool:
    origin = request.headers.get("origin")
    if not origin:
        return False
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme).split(",", 1)[0].strip()
    host = request.headers.get("host", request.url.netloc)
    return origin == f"{scheme}://{host}"


def _request_is_https(request: Request) -> bool:
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme).split(",", 1)[0].strip()
    return scheme == "https"


def _admin_claims(token: str | None) -> dict:
    if not _configured() or not token:
        raise HTTPException(404, "Not found")
    claims = decode_access_token(token)
    if not claims:
        raise HTTPException(401, "Authentication required")
    if claims.get("purpose") == "moderation" and claims.get("sub", "").casefold() == settings.MODERATION_OWNER_EMAIL.casefold():
        return claims
    if claims.get("email") and claims.get("email", "").casefold() == settings.MODERATION_OWNER_EMAIL.casefold():
        return {"sub": settings.MODERATION_OWNER_EMAIL, "purpose": "moderation", "email": claims["email"]}
    raise HTTPException(401, "Authentication required")


async def require_moderation_admin(
    request: Request,
    pr_moderation: str | None = Cookie(default=None),
    pr_token: str | None = Cookie(default=None),
    auth: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not _configured():
        raise HTTPException(404, "Not found")

    # 1. Öncelik: Dedicated moderasyon çerezi
    if pr_moderation:
        claims = decode_access_token(pr_moderation)
        if claims and claims.get("purpose") == "moderation":
            sub = claims.get("sub", "")
            if sub.casefold() == settings.MODERATION_OWNER_EMAIL.casefold():
                return claims

    # 2. Öncelik: Normal web auth token (Bearer auth veya pr_token çerezi)
    token = None
    if auth and auth.credentials:
        token = auth.credentials
    elif pr_token:
        token = pr_token
    else:
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()

    if token:
        claims = decode_access_token(token)
        if claims:
            # Token doğrudan moderasyon tokenı ise
            if claims.get("purpose") == "moderation":
                sub = claims.get("sub", "")
                if sub.casefold() == settings.MODERATION_OWNER_EMAIL.casefold():
                    return claims

            # Normal web JWT'si: sub=user_id, email=user.email
            token_email = claims.get("email")
            if token_email and token_email.casefold() == settings.MODERATION_OWNER_EMAIL.casefold():
                return {
                    "sub": settings.MODERATION_OWNER_EMAIL,
                    "purpose": "moderation",
                    "user_id": claims.get("sub"),
                    "email": token_email,
                }

            # DB üzerinden kullanıcı yetkisini doğrula
            sub = claims.get("sub")
            if sub and str(sub).isdigit():
                user = await db.get(User, int(sub))
                if user and user.is_active:
                    if user.email.casefold() == settings.MODERATION_OWNER_EMAIL.casefold() or user.is_superuser:
                        return {
                            "sub": settings.MODERATION_OWNER_EMAIL,
                            "purpose": "moderation",
                            "user_id": user.id,
                            "email": user.email,
                        }

    raise HTTPException(401, "Authentication required")




async def _invalidate_link(db: AsyncSession, redis_cli, link: ShortLink) -> None:
    from pulseroute.services.link_service import LinkService

    await LinkService.invalidate_link_cache(db, redis_cli, link)


@router.post("/session")
async def create_session(payload: LoginPayload, request: Request, response: Response, redis_cli: aioredis.Redis | None = Depends(get_redis)):
    if not _configured():
        raise HTTPException(404, "Not found")
    if not _origin_ok(request):
        raise HTTPException(403, "Invalid origin")
    ip = request.client.host if request.client else "unknown"
    if await BruteForceGuard.is_ip_jailed(redis_cli, ip):
        raise HTTPException(429, "Too many attempts")
    password_valid = (
        len(payload.password.encode("utf-8")) <= 72
        and verify_password(payload.password, settings.MODERATION_OWNER_PASSWORD_HASH)
    )
    valid = payload.email.casefold() == settings.MODERATION_OWNER_EMAIL.casefold() and password_valid
    if not valid:
        await BruteForceGuard.record_failure(redis_cli, ip)
        raise HTTPException(401, "Invalid email or password")
    await BruteForceGuard.record_success(redis_cli, ip)
    token = create_access_token(
        {"sub": settings.MODERATION_OWNER_EMAIL, "purpose": "moderation"},
        expires_delta=timedelta(minutes=ADMIN_SESSION_MINUTES),
    )
    response.set_cookie(COOKIE_NAME, token, max_age=ADMIN_SESSION_MINUTES * 60, httponly=True, secure=_request_is_https(request), samesite="strict", path="/api/v1/moderation")
    return {"authenticated": True, "email": settings.MODERATION_OWNER_EMAIL}


@router.delete("/session")
async def delete_session(request: Request, response: Response, claims: dict = Depends(require_moderation_admin)):
    if not _origin_ok(request):
        raise HTTPException(403, "Invalid origin")
    response.delete_cookie(COOKIE_NAME, path="/api/v1/moderation", secure=_request_is_https(request), httponly=True, samesite="strict")
    return {"authenticated": False}


@router.get("/session")
async def session_status(request: Request, response: Response, claims: dict = Depends(require_moderation_admin)):
    token = create_access_token(
        {"sub": settings.MODERATION_OWNER_EMAIL, "purpose": "moderation"},
        expires_delta=timedelta(minutes=ADMIN_SESSION_MINUTES),
    )
    response.set_cookie(COOKIE_NAME, token, max_age=ADMIN_SESSION_MINUTES * 60, httponly=True, secure=_request_is_https(request), samesite="strict", path="/api/v1/moderation")
    return {"authenticated": True, "email": claims.get("email") or claims["sub"]}


@router.get("/reports")
async def list_reports(status: str = "new", before: int | None = None, claims: dict = Depends(require_moderation_admin), db: AsyncSession = Depends(get_db)):
    query = select(AbuseReport.id, AbuseReport.slug, AbuseReport.reason, AbuseReport.reporter_email, AbuseReport.status, AbuseReport.review_status, AbuseReport.created_at).where(AbuseReport.review_status == status).order_by(AbuseReport.id.desc()).limit(ADMIN_PAGE_SIZE + 1)
    if before:
        query = query.where(AbuseReport.id < before)
    rows = (await db.execute(query)).mappings().all()
    return {"items": [dict(r) for r in rows[:ADMIN_PAGE_SIZE]], "next": rows[ADMIN_PAGE_SIZE - 1]["id"] if len(rows) > ADMIN_PAGE_SIZE else None}


async def _action_history(db: AsyncSession, *, report_id: int | None = None, appeal_id: int | None = None, link_id: int | None = None):
    query = select(ModerationAction).order_by(ModerationAction.created_at.desc()).limit(10)
    if report_id is not None:
        query = query.where(ModerationAction.report_id == report_id)
    elif appeal_id is not None:
        query = query.where(ModerationAction.appeal_id == appeal_id)
    elif link_id is not None:
        query = query.where(ModerationAction.link_id == link_id)
    else:
        return []
    rows = (await db.execute(query)).scalars().all()
    return [{"action": row.action, "actor": row.actor_email, "note": row.note, "created_at": row.created_at} for row in rows]


@router.get("/reports/{report_id}")
async def report_detail(report_id: int, claims: dict = Depends(require_moderation_admin), db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(AbuseReport, ShortLink).outerjoin(ShortLink, AbuseReport.link_id == ShortLink.id).where(AbuseReport.id == report_id))).first()
    if not row:
        raise HTTPException(404, "Report not found")
    report, link = row
    history = await _action_history(db, report_id=report.id)
    return {"id": report.id, "slug": report.slug, "reason": report.reason, "details": report.details, "reporter_email": report.reporter_email, "masked_ip": report.reporter_ip, "automated_status": report.status, "review_status": report.review_status, "created_at": report.created_at, "link_status": link.moderation_status if link else "missing", "destination_url": link.destination_url if link else None, "history": history}


@router.post("/reports/{report_id}/decision")
async def decide_report(report_id: int, payload: DecisionPayload, request: Request, claims: dict = Depends(require_moderation_admin), db: AsyncSession = Depends(get_db), redis_cli: aioredis.Redis | None = Depends(get_redis)):
    if not _origin_ok(request):
        raise HTTPException(403, "Invalid origin")
    report = await db.get(AbuseReport, report_id, with_for_update=True)
    if not report:
        raise HTTPException(404, "Report not found")
    if report.review_status != "new":
        raise HTTPException(409, "Report has already been reviewed")
    if payload.decision not in ("approve", "reject", "quarantine", "ban"):
        raise HTTPException(422, "Reports support approve, reject, quarantine or ban decisions")
    link = await db.scalar(select(ShortLink).where(ShortLink.id == report.link_id).with_for_update()) if report.link_id else None
    now = datetime.now(UTC)
    db.add(ModerationAction(link_id=link.id if link else None, report_id=report.id, slug=report.slug, action=payload.decision, actor_email=claims["sub"], note=payload.note, created_at=now))
    if payload.decision in ("approve", "quarantine", "ban"):
        report.review_status = "approved"
        if link:
            if link.moderation_was_active is None:
                link.moderation_was_active = link.is_active
            link.is_active = False
            link.is_quarantined = payload.decision == "quarantine"
            link.moderation_status = "banned" if payload.decision == "ban" else "removed" if payload.decision == "approve" else "quarantined"
            link.quarantine_reason = payload.note or f"Owner moderation: {payload.decision}"
            link.moderation_updated_at = now
    elif payload.decision == "reject":
        report.review_status = "rejected"
    elif payload.decision in ("release", "unban"):
        if not link:
            raise HTTPException(404, "Link not found")
        link.moderation_status = "active"
        link.is_quarantined = False
        link.is_active = link.moderation_was_active if link.moderation_was_active is not None else True
        link.quarantine_reason = None
        link.moderation_was_active = None
        link.moderation_updated_at = now
    if payload.decision in ("approve", "reject", "quarantine", "ban"):
        report.resolved_at = now
    await db.commit()
    if link:
        await _invalidate_link(db, redis_cli, link)
    return {"ok": True, "decision": payload.decision, "actor": claims["sub"]}


@router.get("/restricted")
async def list_restricted(before: int | None = None, claims: dict = Depends(require_moderation_admin), db: AsyncSession = Depends(get_db)):
    query = select(ShortLink.id, ShortLink.slug, ShortLink.title, ShortLink.moderation_status, ShortLink.quarantine_reason, ShortLink.moderation_updated_at).where(ShortLink.moderation_status.in_(("quarantined", "banned", "removed"))).order_by(ShortLink.id.desc()).limit(ADMIN_PAGE_SIZE + 1)
    if before:
        query = query.where(ShortLink.id < before)
    rows = (await db.execute(query)).mappings().all()
    return {"items": [dict(r) for r in rows[:ADMIN_PAGE_SIZE]], "next": rows[ADMIN_PAGE_SIZE - 1]["id"] if len(rows) > ADMIN_PAGE_SIZE else None}


@router.get("/links/{link_id}")
async def restricted_detail(link_id: int, claims: dict = Depends(require_moderation_admin), db: AsyncSession = Depends(get_db)):
    link = await db.get(ShortLink, link_id)
    if not link:
        raise HTTPException(404, "Link not found")
    return {
        "id": link.id,
        "slug": link.slug,
        "title": link.title,
        "destination_url": link.destination_url,
        "moderation_status": link.moderation_status,
        "quarantine_reason": link.quarantine_reason,
        "created_at": link.moderation_updated_at or link.created_at,
        "history": await _action_history(db, link_id=link.id),
    }


@router.get("/appeals")
async def list_appeals(status: str = "pending", before: int | None = None, claims: dict = Depends(require_moderation_admin), db: AsyncSession = Depends(get_db)):
    query = select(ModerationAppeal.id, ModerationAppeal.slug, ModerationAppeal.requester_email, ModerationAppeal.status, ModerationAppeal.created_at).where(ModerationAppeal.status == status).order_by(ModerationAppeal.id.desc()).limit(ADMIN_PAGE_SIZE + 1)
    if before:
        query = query.where(ModerationAppeal.id < before)
    rows = (await db.execute(query)).mappings().all()
    return {"items": [dict(r) for r in rows[:ADMIN_PAGE_SIZE]], "next": rows[ADMIN_PAGE_SIZE - 1]["id"] if len(rows) > ADMIN_PAGE_SIZE else None}


@router.get("/appeals/{appeal_id}")
async def appeal_detail(appeal_id: int, claims: dict = Depends(require_moderation_admin), db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(ModerationAppeal, ShortLink).outerjoin(ShortLink, ModerationAppeal.link_id == ShortLink.id).where(ModerationAppeal.id == appeal_id))).first()
    if not row:
        raise HTTPException(404, "Appeal not found")
    appeal, link = row
    history = await _action_history(db, appeal_id=appeal.id)
    return {"id": appeal.id, "slug": appeal.slug, "requester_email": appeal.requester_email, "details": appeal.details, "status": appeal.status, "created_at": appeal.created_at, "link_status": link.moderation_status if link else "missing", "destination_url": link.destination_url if link else None, "history": history}


@router.post("/links/{link_id}/decision")
async def decide_link(link_id: int, payload: DecisionPayload, request: Request, claims: dict = Depends(require_moderation_admin), db: AsyncSession = Depends(get_db), redis_cli: aioredis.Redis | None = Depends(get_redis)):
    if not _origin_ok(request):
        raise HTTPException(403, "Invalid origin")
    link = await db.scalar(select(ShortLink).where(ShortLink.id == link_id).with_for_update())
    if not link:
        raise HTTPException(404, "Link not found")
    now = datetime.now(UTC)
    if payload.decision in ("quarantine", "ban", "approve"):
        if link.moderation_was_active is None:
            link.moderation_was_active = link.is_active
        link.is_active = False
        link.is_quarantined = payload.decision == "quarantine"
        link.moderation_status = "quarantined" if payload.decision == "quarantine" else "banned" if payload.decision == "ban" else "removed"
        link.quarantine_reason = payload.note or f"Owner moderation: {payload.decision}"
    elif payload.decision in ("release", "unban"):
        link.is_active = link.moderation_was_active if link.moderation_was_active is not None else True
        link.is_quarantined = False
        link.moderation_status = "active"
        link.moderation_was_active = None
        link.quarantine_reason = None
    else:
        raise HTTPException(422, "Unsupported decision for link")
    link.moderation_updated_at = now
    db.add(ModerationAction(link_id=link.id, slug=link.slug, action=payload.decision, actor_email=claims["sub"], note=payload.note, created_at=now))
    await db.commit()
    await _invalidate_link(db, redis_cli, link)
    return {"ok": True, "status": link.moderation_status}


@router.post("/appeals/{appeal_id}/decision")
async def decide_appeal(appeal_id: int, payload: DecisionPayload, request: Request, claims: dict = Depends(require_moderation_admin), db: AsyncSession = Depends(get_db), redis_cli: aioredis.Redis | None = Depends(get_redis)):
    if not _origin_ok(request):
        raise HTTPException(403, "Invalid origin")
    appeal = await db.get(ModerationAppeal, appeal_id, with_for_update=True)
    if not appeal or appeal.status != "pending":
        raise HTTPException(404, "Pending appeal not found")
    if payload.decision not in ("approve", "reject"):
        raise HTTPException(422, "Appeals support approve or reject decisions only")
    link = await db.scalar(select(ShortLink).where(ShortLink.id == appeal.link_id).with_for_update()) if appeal.link_id else None
    appeal.status = "approved" if payload.decision == "approve" else "rejected"
    appeal.resolved_at = datetime.now(UTC)
    now = appeal.resolved_at
    db.add(ModerationAction(link_id=link.id if link else None, appeal_id=appeal.id, slug=appeal.slug, action=payload.decision, actor_email=claims["sub"], note=payload.note, created_at=now))
    if link and appeal.status == "approved":
        link.moderation_status = "active"
        link.is_quarantined = False
        link.is_active = link.moderation_was_active if link.moderation_was_active is not None else True
        link.quarantine_reason = None
        link.moderation_was_active = None
        link.moderation_updated_at = datetime.now(UTC)
    await db.commit()
    if link and appeal.status == "approved":
        await _invalidate_link(db, redis_cli, link)
    return {"ok": True, "status": appeal.status, "actor": claims["sub"]}


@router.post("/appeals", status_code=201)
async def submit_appeal(payload: AppealPayload, user: User = Depends(require_authenticated_user), db: AsyncSession = Depends(get_db)):
    link = await db.scalar(select(ShortLink).where(ShortLink.id == payload.link_id))
    if not link or link.workspace_id is None:
        raise HTTPException(404, "Restricted link not found")
    owner_membership = await db.scalar(
        select(WorkspaceMember.id).where(
            WorkspaceMember.workspace_id == link.workspace_id,
            WorkspaceMember.user_id == user.id,
            WorkspaceMember.role == "owner",
        )
    )
    if not owner_membership:
        raise HTTPException(403, "Only the link workspace owner may appeal")
    if link.moderation_status not in ("quarantined", "banned", "removed"):
        raise HTTPException(409, "This link is not under moderation")
    pending = await db.scalar(select(ModerationAppeal.id).where(ModerationAppeal.link_id == link.id, ModerationAppeal.status == "pending").limit(1))
    if pending:
        raise HTTPException(409, "An appeal is already pending")
    appeal = ModerationAppeal(link_id=link.id, slug=link.slug, workspace_id=link.workspace_id, requester_email=user.email, details=payload.details.strip())
    db.add(appeal)
    await db.commit()
    return {"id": appeal.id, "status": appeal.status}
