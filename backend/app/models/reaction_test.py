from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import TEST_CONTEXTS
from app.db.base import Base, CreatedAtMixin, UUIDPKMixin

_CTX_CHECK = ", ".join(f"'{c}'" for c in TEST_CONTEXTS)


class ReactionTest(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "reaction_tests"
    __table_args__ = (
        CheckConstraint(f"context in ({_CTX_CHECK})", name="context_allowed"),
        CheckConstraint(
            "median_reaction_time_ms between 50 and 10000", name="median_in_range"
        ),
        CheckConstraint("valid_trials >= 5", name="trials_min"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    test_date: Mapped[date] = mapped_column(Date, nullable=False)
    context: Mapped[str] = mapped_column(String, nullable=False)
    median_reaction_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    valid_trials: Mapped[int] = mapped_column(Integer, nullable=False)
