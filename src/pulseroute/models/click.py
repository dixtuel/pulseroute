from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pulseroute.core.database import Base

if TYPE_CHECKING:
    from pulseroute.models.link import ShortLink


class ClickEvent(Base):
    __tablename__ = "click_events"
    __table_args__ = (
        Index("ix_click_link_time", "link_id", "clicked_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    link_id: Mapped[int] = mapped_column(ForeignKey("short_links.id", ondelete="CASCADE"), index=True)

    # Geo Data
    country_code: Mapped[str] = mapped_column(String(5), default="XX")
    city: Mapped[str] = mapped_column(String(100), default="Unknown")

    # Client Data
    device_type: Mapped[str] = mapped_column(String(20), default="desktop")
    browser: Mapped[str] = mapped_column(String(50), default="Unknown")
    os: Mapped[str] = mapped_column(String(50), default="Unknown")
    referrer: Mapped[str | None] = mapped_column(String(500), nullable=True)

    is_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)

    link: Mapped["ShortLink"] = relationship("ShortLink", back_populates="clicks")
