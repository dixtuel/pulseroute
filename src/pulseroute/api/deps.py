from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.core.database import get_db
from pulseroute.core.security import decode_access_token
from pulseroute.models.user import User
from pulseroute.models.workspace import Workspace, WorkspaceMember

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    if not auth:
        return None

    token = auth.credentials

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = int(payload["sub"])
    res = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user


async def require_authenticated_user(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token or API key."
        )
    return current_user


async def verify_workspace_access(
    workspace_id: int,
    user: User,
    db: AsyncSession,
    required_roles: tuple[str, ...] = ("owner", "admin", "member"),
) -> Workspace:
    """Strictly enforces tenant data isolation between users and organizations."""
    query = (
        select(Workspace)
        .join(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
        .where(
            Workspace.id == workspace_id,
            WorkspaceMember.user_id == user.id,
            WorkspaceMember.role.in_(required_roles)
        )
    )
    result = await db.execute(query)
    workspace = result.scalar_one_or_none()

    if not workspace and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: You do not have permission to access or modify this workspace."
        )

    return workspace
