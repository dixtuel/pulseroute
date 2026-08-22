from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(description="Workspace name e.g. Marketing Team")
    slug: str = Field(description="Unique workspace URL slug e.g. marketing-team")
    interstitial_default_delay: int = 0


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    interstitial_default_delay: int = 0
    created_at: datetime
