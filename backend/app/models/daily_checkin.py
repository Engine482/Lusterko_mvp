from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, UUIDPKMixin


class DailyCheckin(UUIDPKMixin, CreatedAtMixin, Base):
    """Single daily check-in row (DB Schema §3.3)."""

    __tablename__ = "daily_checkins"
    __table_args__ = (
        UniqueConstraint("user_id", "checkin_date", name="daily_checkins_user_id_date_key"),
        CheckConstraint(
            "sleep_score between 0 and 10 and energy_score between 0 and 10 "
            "and mood_score between 0 and 10 and concentration_score between 0 and 10",
            name="scores_in_range",
        ),
        CheckConstraint(
            "comment_text is null or char_length(comment_text) <= 300",
            name="comment_max_300",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    checkin_date: Mapped[date] = mapped_column(Date, nullable=False)
    sleep_score: Mapped[int] = mapped_column(Integer, nullable=False)
    energy_score: Mapped[int] = mapped_column(Integer, nullable=False)
    mood_score: Mapped[int] = mapped_column(Integer, nullable=False)
    concentration_score: Mapped[int] = mapped_column(Integer, nullable=False)
    comment_text: Mapped[str | None] = mapped_column(String, nullable=True)
