from typing import List, Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.api.deps import require_authenticated_user, verify_workspace_access
from pulseroute.core.database import get_db
from pulseroute.core.redis import get_redis
from pulseroute.models.user import User
from pulseroute.models.workspace import Workspace, WorkspaceMember
from pulseroute.schemas.workspace import WorkspaceCreate, WorkspaceResponse
from pulseroute.services.workspace_service import WorkspaceService

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


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: int,
    user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
    redis_cli: Optional[aioredis.Redis] = Depends(get_redis),
):
    """Permanently deletes a specific workspace, its links, domains, and webhooks.

    Strictly restricted to the Workspace Owner (or Superuser).
    """
    workspace = await verify_workspace_access(
        workspace_id=workspace_id,
        user=user,
        db=db,
        required_roles=("owner",),
    )

    await WorkspaceService.delete_workspace(db, redis_cli, workspace)
    return None

