from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.api.deps import require_authenticated_user, verify_workspace_access
from pulseroute.core.database import get_db
from pulseroute.core.security import generate_api_key, hash_api_key
from pulseroute.models.user import ApiKey, User
from pulseroute.models.workspace import Workspace, WorkspaceMember
from pulseroute.schemas.workspace import WorkspaceCreate, WorkspaceResponse

router = APIRouter(prefix="/workspaces", tags=["Workspaces & Tenant Isolation"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    data: WorkspaceCreate,
    user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Workspace).where(Workspace.slug == data.slug.strip().lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workspace slug already taken.")

    workspace = Workspace(name=data.name, slug=data.slug.strip().lower())
    db.add(workspace)
    await db.flush()

    member = WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="owner")
    db.add(member)
    await db.commit()
    await db.refresh(workspace)
    return workspace


@router.get("", response_model=List[WorkspaceResponse])
async def list_user_workspaces(
    user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Workspace)
        .join(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
        .where(WorkspaceMember.user_id == user.id)
    )
    res = await db.execute(query)
    return list(res.scalars().all())


@router.post("/{workspace_id}/api-keys")
async def generate_workspace_api_key(
    workspace_id: int,
    key_name: str = "Live Production Key",
    user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_workspace_access(workspace_id, user, db, required_roles=("owner", "admin"))

    raw_key = generate_api_key(prefix="pr_live_")
    key_hash = hash_api_key(raw_key)

    api_key_obj = ApiKey(
        user_id=user.id,
        key_hash=key_hash,
        name=key_name,
        scopes="links:read,links:write,analytics:read",
    )
    db.add(api_key_obj)
    await db.commit()

    return {
        "api_key": raw_key,
        "name": key_name,
        "warning": "Please copy this API key now. You will not be able to see it again.",
    }
