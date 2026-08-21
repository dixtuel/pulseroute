import hashlib
import hmac
import json
from typing import Any

import httpx
import structlog

logger = structlog.get_logger()


class WebhookService:
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
