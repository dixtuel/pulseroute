from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pulseroute.core.database import Base

if TYPE_CHECKING:
    from pulseroute.models.link import ShortLink
    from pulseroute.models.workspace import Workspace


class CustomDomain(Base):
    __tablename__ = "custom_domains"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workspace_id: Mapped[int | None] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    domain: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    verification_code: Mapped[str] = mapped_column(String(64), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    custom_not_found_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    workspace: Mapped["Workspace | None"] = relationship("Workspace", back_populates="domains")
    links: Mapped[list["ShortLink"]] = relationship("ShortLink", back_populates="custom_domain")
