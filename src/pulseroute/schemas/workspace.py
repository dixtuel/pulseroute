from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(description="Workspace name e.g. Marketing Team")
    slug: str = Field(description="Unique workspace URL slug e.g. marketing-team")
    adsense_client_id: Optional[str] = None
    adsense_slot_id: Optional[str] = None
    adsense_enabled: bool = False
    interstitial_default_delay: int = 0


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    adsense_client_id: Optional[str] = None
    adsense_slot_id: Optional[str] = None
    adsense_enabled: Optional[bool] = None
    interstitial_default_delay: Optional[int] = None


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    adsense_client_id: Optional[str] = None
    adsense_slot_id: Optional[str] = None
    adsense_enabled: bool = False
    interstitial_default_delay: int = 0
    created_at: datetime
