from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WebhookCreate(BaseModel):
    workspace_id: int
    url: str = Field(description="HTTPS endpoint that receives POSTed event payloads")
    events: str = Field(
        default="link.clicked,link.created",
        description="Comma-separated event types to subscribe to",
    )


class WebhookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    events: str
    is_active: bool
    created_at: datetime


class WebhookCreateResponse(WebhookResponse):
    secret_key: str = Field(
        description="Shown once at creation time only — used to verify the X-PulseRoute-Signature header"
    )
