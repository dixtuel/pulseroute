from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LinkCreate(BaseModel):
    destination_url: str = Field(description="Target destination URL")
    slug: str | None = Field(None, max_length=100, description="Custom slug or empty for auto-generated")
    title: str | None = None
    tags: str | None = None
    domain_id: int | None = None

    # Targeting (Dub.co feature-set)
    ios_destination: str | None = None
    android_destination: str | None = None
    geo_targets: dict[str, str] | None = None  # e.g. {"TR": "https://...", "US": "https://..."}

    # Fallbacks & Social
    expires_at: datetime | None = None
    expired_url: str | None = None
    og_title: str | None = None
    og_description: str | None = None
    og_image: str | None = None

    password: str | None = None
    public_stats: bool = False
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None


class LinkUpdate(BaseModel):
    destination_url: str | None = None
    title: str | None = None
    tags: str | None = None
    is_active: bool | None = None
    ios_destination: str | None = None
    android_destination: str | None = None
    geo_targets: dict[str, str] | None = None
    expires_at: datetime | None = None
    expired_url: str | None = None
    public_stats: bool | None = None


class LinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    destination_url: str
    title: str | None = None
    tags: str | None = None
    short_url: str
    total_clicks: int
    public_stats: bool
    is_active: bool
    created_at: datetime
    expires_at: datetime | None = None


class LinkDetailResponse(LinkResponse):
    ios_destination: str | None = None
    android_destination: str | None = None
    geo_targets: dict[str, str] | None = None
    expired_url: str | None = None
    og_title: str | None = None
    og_description: str | None = None
    og_image: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    has_password: bool = False
