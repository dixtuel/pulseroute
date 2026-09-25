from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from pulseroute.core.database import Base


class ModerationAppeal(Base):
    __tablename__ = "moderation_appeals"
    __table_args__ = (Index("ix_moderation_appeals_status_id", "status", "id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    link_id: Mapped[int | None] = mapped_column(ForeignKey("short_links.id", ondelete="SET NULL"), nullable=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True)
    requester_email: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ModerationAction(Base):
    __tablename__ = "moderation_actions"
    __table_args__ = (
        Index("ix_moderation_actions_created_at", "created_at"),
        Index("ix_moderation_actions_report_created", "report_id", "created_at"),
        Index("ix_moderation_actions_appeal_created", "appeal_id", "created_at"),
        Index("ix_moderation_actions_link_created", "link_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    link_id: Mapped[int | None] = mapped_column(ForeignKey("short_links.id", ondelete="CASCADE"), nullable=True)
    report_id: Mapped[int | None] = mapped_column(ForeignKey("abuse_reports.id", ondelete="CASCADE"), nullable=True)
    appeal_id: Mapped[int | None] = mapped_column(ForeignKey("moderation_appeals.id", ondelete="CASCADE"), nullable=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    actor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
