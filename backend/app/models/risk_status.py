from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import HARD_FLAGS, RISK_STATUSES
from app.db.base import Base, TimestampMixin, UUIDPKMixin

_STATUS_CHECK = ", ".join(f"'{s}'" for s in RISK_STATUSES)
_HARD_FLAG_CHECK = ", ".join(f"'{f}'" for f in HARD_FLAGS)


class RiskStatusRow(UUIDPKMixin, TimestampMixin, Base):
    """Current risk snapshot per user (DB Schema §5.1, one row per user)."""

    __tablename__ = "risk_statuses"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_risk_statuses_user_id"),
        CheckConstraint(
            f"current_risk_status in ({_STATUS_CHECK})", name="status_allowed"
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
    current_risk_status: Mapped[str] = mapped_column(String, nullable=False)
    current_risk_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 1), nullable=False, server_default="0"
    )
    functional_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 1), nullable=False, server_default="0"
    )
    emotional_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 1), nullable=False, server_default="0"
    )
    cognitive_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 1), nullable=False, server_default="0"
    )
    text_modifier_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 1), nullable=False, server_default="0"
    )
    hard_flag: Mapped[str | None] = mapped_column(String, nullable=True)
    explanation_text: Mapped[str | None] = mapped_column(String, nullable=True)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
