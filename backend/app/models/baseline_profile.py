from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class BaselineProfile(UUIDPKMixin, TimestampMixin, Base):
    """One row per user; populated incrementally by baseline_* endpoints.

    DB Schema §3.1.
    """

    __tablename__ = "baseline_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="baseline_profiles_user_id_key"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    baseline_sleep_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    baseline_energy_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    baseline_mood_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    baseline_concentration_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    baseline_phq4_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    baseline_pss4_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    baseline_reaction_time_median_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    baseline_go_no_go_commission_errors: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    baseline_go_no_go_omission_errors: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    baseline_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
