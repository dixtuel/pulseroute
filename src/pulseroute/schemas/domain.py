from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DomainCreate(BaseModel):
    domain: str = Field(description="Custom domain name e.g. links.mybrand.com")
    workspace_id: Optional[int] = None
    custom_not_found_url: str | None = None


class DomainResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    domain: str
    verification_code: str
    is_verified: bool
    created_at: datetime
    custom_not_found_url: str | None = None
    dns_instructions: Optional[dict] = None


class DomainVerifyResponse(BaseModel):
    domain: str
    is_verified: bool
    status: str  # active, pending_dns
    message: str
    dns_instructions: dict
