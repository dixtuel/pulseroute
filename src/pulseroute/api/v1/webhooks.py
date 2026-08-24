import secrets
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.api.deps import require_authenticated_user, verify_workspace_access
from pulseroute.common.encryption import encrypt_secret
from pulseroute.core.database import get_db
from pulseroute.models.user import User
from pulseroute.models.webhook import WebhookSubscription
from pulseroute.schemas.webhook import WebhookCreate, WebhookCreateResponse, WebhookResponse

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


async def _get_webhook_or_404(db: AsyncSession, webhook_id: int) -> WebhookSubscription:
    webhook = await db.get(WebhookSubscription, webhook_id)
    if not webhook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")
    return webhook


@router.post("", response_model=WebhookCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    webhook_in: WebhookCreate,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_workspace_access(webhook_in.workspace_id, current_user, db, required_roles=("owner", "admin"))

    plain_secret = secrets.token_hex(32)
    webhook = WebhookSubscription(
        workspace_id=webhook_in.workspace_id,
        url=webhook_in.url,
        secret_key=encrypt_secret(plain_secret),
        events=webhook_in.events,
    )
    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)

    return WebhookCreateResponse(
        id=webhook.id,
        url=webhook.url,
        events=webhook.events,
        is_active=webhook.is_active,
        created_at=webhook.created_at,
        secret_key=plain_secret,
    )


@router.get("", response_model=List[WebhookResponse])
async def list_webhooks(
    workspace_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_workspace_access(workspace_id, current_user, db)
    result = await db.execute(
        select(WebhookSubscription)
        .where(WebhookSubscription.workspace_id == workspace_id)
        .order_by(WebhookSubscription.created_at.desc())
    )
    return list(result.scalars().all())


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    webhook = await _get_webhook_or_404(db, webhook_id)
    await verify_workspace_access(webhook.workspace_id, current_user, db, required_roles=("owner", "admin"))
    await db.delete(webhook)
    await db.commit()
