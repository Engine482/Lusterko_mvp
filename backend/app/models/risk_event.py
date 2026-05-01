from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import HARD_FLAGS, RISK_SOURCE_EVENTS, RISK_STATUSES
from app.db.base import Base, CreatedAtMixin, UUIDPKMixin

_STATUS_CHECK = ", ".join(f"'{s}'" for s in RISK_STATUSES)
_HARD_FLAG_CHECK = ", ".join(f"'{f}'" for f in HARD_FLAGS)
_SOURCE_CHECK = ", ".join(f"'{s}'" for s in RISK_SOURCE_EVENTS)


class RiskEvent(UUIDPKMixin, CreatedAtMixin, Base):
    """One row per recompute (DB Schema §5.2). Append-only history."""

    __tablename__ = "risk_events"
    __table_args__ = (
        CheckConstraint(
            f"source_event_type in ({_SOURCE_CHECK})", name="source_event_type_allowed"
        ),
        CheckConstraint(f"new_status in ({_STATUS_CHECK})", name="new_status_allowed"),
        CheckConstraint(
            f"previous_status is null or previous_status in ({_STATUS_CHECK})",
            name="previous_status_allowed",
        ),
        CheckConstraint(
            f"hard_flag is null or hard_flag in ({_HARD_FLAG_CHECK})",
            name="hard_flag_allowed",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_event_type: Mapped[str] = mapped_column(String, nullable=False)
    source_event_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )
    previous_status: Mapped[str | None] = mapped_column(String, nullable=True)
    new_status: Mapped[str] = mapped_column(String, nullable=False)
    total_score: Mapped[Decimal] = mapped_column(Numeric(4, 1), nullable=False)
    hard_flag: Mapped[str | None] = mapped_column(String, nullable=True)
    explanation_text: Mapped[str | None] = mapped_column(String, nullable=True)
