from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pulseroute.core.database import Base

if TYPE_CHECKING:
    from pulseroute.models.click import ClickEvent
    from pulseroute.models.domain import CustomDomain
    from pulseroute.models.workspace import Workspace


class ShortLink(Base):
    __tablename__ = "short_links"
    __table_args__ = (
        Index("ix_domain_slug", "domain_id", "slug", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workspace_id: Mapped[int | None] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    domain_id: Mapped[int | None] = mapped_column(ForeignKey("custom_domains.id", ondelete="SET NULL"), nullable=True, index=True)

    slug: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    destination_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tags: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Smart Device & Geo Targeting
    ios_destination: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    android_destination: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    geo_targets: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Interstitial / Monetized Delay & AdSense
    interstitial_delay: Mapped[int] = mapped_column(Integer, default=0)
    interstitial_ad_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    interstitial_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    adsense_client_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # ca-pub-XXXX
    adsense_slot_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Expiration & Custom Fallback
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expired_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # OpenGraph & Social Previews
    og_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    og_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    og_image: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Security & Public Visibility
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    public_stats: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # UTM Parameters
    utm_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    utm_medium: Mapped[str | None] = mapped_column(String(100), nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(100), nullable=True)

    total_clicks: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    workspace: Mapped["Workspace | None"] = relationship("Workspace", back_populates="links")
    custom_domain: Mapped["CustomDomain | None"] = relationship("CustomDomain", back_populates="links")
    clicks: Mapped[list["ClickEvent"]] = relationship("ClickEvent", back_populates="link", cascade="all, delete-orphan")
