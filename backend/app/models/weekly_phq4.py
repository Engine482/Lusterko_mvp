from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, UUIDPKMixin


class WeeklyPhq4Assessment(UUIDPKMixin, CreatedAtMixin, Base):
    """Weekly PHQ-4 (DB Schema §3.4). Item range 0..3, total 0..12."""

    __tablename__ = "weekly_phq4_assessments"
    __table_args__ = (
        CheckConstraint(
            "answer_1 between 0 and 3 and answer_2 between 0 and 3 "
            "and answer_3 between 0 and 3 and answer_4 between 0 and 3",
            name="answers_in_range",
        ),
        CheckConstraint("total_score between 0 and 12", name="total_in_range"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    assessment_date: Mapped[date] = mapped_column(Date, nullable=False)
    answer_1: Mapped[int] = mapped_column(Integer, nullable=False)
    answer_2: Mapped[int] = mapped_column(Integer, nullable=False)
    answer_3: Mapped[int] = mapped_column(Integer, nullable=False)
    answer_4: Mapped[int] = mapped_column(Integer, nullable=False)
    total_score: Mapped[int] = mapped_column(Integer, nullable=False)
