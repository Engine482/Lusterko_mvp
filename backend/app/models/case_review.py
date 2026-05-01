from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import CASE_STATUSES
from app.db.base import Base, TimestampMixin, UUIDPKMixin

_STATUS_CHECK = ", ".join(f"'{s}'" for s in CASE_STATUSES)


class CaseReview(UUIDPKMixin, TimestampMixin, Base):
    """Open/closed case for a soldier (DB Schema §6.1).

    The partial unique index `uq_case_reviews_user_id_open` defined in
    migration 0006 enforces "one open case per user" per Risk Engine §13.2.
    """

    __tablename__ = "case_reviews"
    __table_args__ = (
        CheckConstraint(f"status in ({_STATUS_CHECK})", name="status_allowed"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="new")
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_risk_event_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("risk_events.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
