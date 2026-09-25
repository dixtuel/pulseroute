from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pulseroute.core.database import Base

if TYPE_CHECKING:
    from pulseroute.models.link import ShortLink


class AbuseReport(Base):
    __tablename__ = "abuse_reports"
    __table_args__ = (
        Index("ix_abuse_reports_slug", "slug"),
        Index("ix_abuse_reports_created_at", "created_at"),
        Index("ix_abuse_reports_slug_fp", "slug", "reporter_fingerprint"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    link_id: Mapped[int | None] = mapped_column(
        ForeignKey("short_links.id", ondelete="SET NULL"), nullable=True, index=True
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str] = mapped_column(String(50), nullable=False)  # phishing, malware, illegal_content, copyright, spam, other
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    reporter_email: Mapped[str] = mapped_column(String(255), nullable=False)
    reporter_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)  # Anonymized / masked client IP
    reporter_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)  # Salted HMAC-SHA256 fingerprint
    status: Mapped[str] = mapped_column(String(50), default="quarantined")  # quarantined, pending, resolved, dismissed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    link: Mapped[Optional["ShortLink"]] = relationship("ShortLink", back_populates="abuse_reports")
