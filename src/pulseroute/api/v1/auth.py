from datetime import timedelta
from typing import Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.api.deps import require_authenticated_user
from pulseroute.common.email_validator import email_domain_accepts_mail
from pulseroute.core.config import settings
from pulseroute.core.database import get_db
from pulseroute.core.moderation_policy import ADMIN_SESSION_MINUTES
from pulseroute.core.redis import get_redis
from pulseroute.core.security import create_access_token, hash_password, verify_password
from pulseroute.core.security_middleware import BruteForceGuard
from pulseroute.models.user import User
from pulseroute.models.workspace import Workspace, WorkspaceMember
from pulseroute.schemas.auth import (
    AccountDeleteRequest,
    AccountDeleteResponse,
    LoginRequest,
    Token,
    UserCreate,
    UserResponse,
)
from pulseroute.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == user_in.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered.")

    if settings.ENFORCE_EMAIL_DOMAIN_CHECK and not await email_domain_accepts_mail(user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email's domain does not appear to accept mail. Please use a real email address.",
        )

    # 1. Create User
    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        is_superuser=False,
    )
    db.add(user)
    await db.flush()

    # 2. Automatically provision personal Workspace (Dub-like pattern)
    clean_name = user_in.full_name or user_in.email.split("@")[0]
    workspace = Workspace(
        name=f"{clean_name}'s Workspace",
        slug=f"{user_in.email.split('@')[0].lower()}-{user.id}",
    )
    db.add(workspace)
    await db.flush()

    # 3. Add as Owner
    member = WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="owner")
    db.add(member)
    await db.commit()
    await db.refresh(user)

    return user


def _request_is_https(request: Request) -> bool:
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme).split(",", 1)[0].strip()
    return scheme == "https"


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis_cli: Optional[aioredis.Redis] = Depends(get_redis),
):
    client_ip = request.client.host if request.client else "127.0.0.1"

    if await BruteForceGuard.is_ip_jailed(redis_cli, client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. IP address temporarily blocked for 10 minutes.",
        )

    try:
        result = await db.execute(select(User).where(User.email == login_data.email))
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sign-in is temporarily unavailable while account storage is offline. Please try again later.",
        ) from None
    user = result.scalar_one_or_none()
    owner_password_valid = (
        bool(settings.MODERATION_OWNER_EMAIL and settings.MODERATION_OWNER_PASSWORD_HASH)
        and login_data.email.casefold() == settings.MODERATION_OWNER_EMAIL.casefold()
        and len(login_data.password.encode("utf-8")) <= 72
        and verify_password(login_data.password, settings.MODERATION_OWNER_PASSWORD_HASH)
    )
    account_password_valid = bool(user and verify_password(login_data.password, user.hashed_password))
    if not user or not user.is_active or not (account_password_valid or owner_password_valid):
        await BruteForceGuard.record_failure(redis_cli, client_ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    await BruteForceGuard.record_success(redis_cli, client_ip)
    token = create_access_token(data={"sub": str(user.id), "email": user.email}, expires_delta=timedelta(days=7))

    # Standard web session cookie
    response.set_cookie(
        "pr_token",
        token,
        max_age=7 * 86400,
        httponly=False,
        secure=_request_is_https(request),
        samesite="lax",
        path="/",
    )

    # If this is the owner account, also issue moderation cookie immediately
    if (
        bool(settings.MODERATION_OWNER_EMAIL and settings.MODERATION_OWNER_PASSWORD_HASH)
        and user.email.casefold() == settings.MODERATION_OWNER_EMAIL.casefold()
    ):
        mod_token = create_access_token(
            {"sub": settings.MODERATION_OWNER_EMAIL, "purpose": "moderation"},
            expires_delta=timedelta(minutes=ADMIN_SESSION_MINUTES),
        )
        response.set_cookie(
            "pr_moderation",
            mod_token,
            max_age=ADMIN_SESSION_MINUTES * 60,
            httponly=True,
            secure=_request_is_https(request),
            samesite="strict",
            path="/api/v1/moderation",
        )

    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve currently authenticated user profile."""
    is_owner = bool(
        settings.MODERATION_OWNER_EMAIL
        and user.email.casefold() == settings.MODERATION_OWNER_EMAIL.casefold()
    )
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        is_owner=is_owner,
    )


@router.delete("/me", response_model=AccountDeleteResponse)
async def delete_my_account(
    data: AccountDeleteRequest,
    user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
    redis_cli: Optional[aioredis.Redis] = Depends(get_redis),
):
    """Permanently deletes the authenticated user's account and all personal data

    in compliance with KVKK (Article 7) and GDPR (Article 17 - Right to Erasure).
    Cascades all owned workspaces, short links, clicks, and associated secrets.
    """
    if data.confirmation.strip().upper() != "DELETE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation text must be 'DELETE' to confirm irreversible account deletion.",
        )

    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password. Account deletion aborted.",
        )

    # 1. Find and purge all workspaces where this user is the 'owner'
    owned_ws_query = (
        select(Workspace)
        .join(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
        .where(WorkspaceMember.user_id == user.id, WorkspaceMember.role == "owner")
    )
    owned_workspaces = list((await db.execute(owned_ws_query)).scalars().all())

    for ws in owned_workspaces:
        await WorkspaceService.delete_workspace(db, redis_cli, ws)

    # 2. Delete user entity (cascade will delete remaining WorkspaceMember entries)
    await db.delete(user)
    await db.commit()

    return AccountDeleteResponse(
        status="success",
        detail="Account and all associated personal data permanently deleted in accordance with KVKK / GDPR.",
    )
