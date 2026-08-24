import asyncio
import hashlib
import hmac
import json
from typing import Any

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.common.encryption import decrypt_secret
from pulseroute.models.webhook import WebhookSubscription

logger = structlog.get_logger()


class WebhookService:
    @staticmethod
    async def notify_workspace(db: AsyncSession, workspace_id: int, event_type: str, payload: dict[str, Any]) -> None:
        """Fire-and-forget dispatch to every active subscription in the workspace that opted into this event type."""
        result = await db.execute(
            select(WebhookSubscription).where(
                WebhookSubscription.workspace_id == workspace_id,
                WebhookSubscription.is_active.is_(True),
            )
        )
        for sub in result.scalars().all():
            if event_type not in (sub.events or "").split(","):
                continue
            secret = decrypt_secret(sub.secret_key)
            asyncio.create_task(WebhookService.dispatch_event(sub.url, secret, event_type, payload))

    @staticmethod
    async def dispatch_event(url: str, secret_key: str, event_type: str, payload: dict[str, Any]) -> bool:
        body = json.dumps({"event": event_type, "data": payload}, separators=(",", ":"))
        signature = hmac.new(secret_key.encode(), body.encode(), hashlib.sha256).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-PulseRoute-Signature": signature,
            "User-Agent": "PulseRoute-Webhook-Worker/1.0",
        }

        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                resp = await client.post(url, content=body, headers=headers)
                return resp.is_success
            except Exception as e:
                logger.error("webhook_dispatch_failed", url=url, error=str(e))
                return False
