from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DomainCreate(BaseModel):
    domain: str = Field(description="Custom domain name e.g. links.mybrand.com")
    custom_not_found_url: str | None = None


class DomainResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    domain: str
    verification_code: str
    is_verified: bool
    created_at: datetime
    custom_not_found_url: str | None = None


class DomainVerifyResponse(BaseModel):
    domain: str
    is_verified: bool
    message: str
    dns_txt_record: str
    cname_target: str
