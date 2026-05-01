from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, UUIDPKMixin


class CaseReviewNote(UUIDPKMixin, CreatedAtMixin, Base):
    """Free-text note attached to a case (DB Schema §6.2)."""

    __tablename__ = "case_review_notes"
    __table_args__ = (
        CheckConstraint(
            "char_length(text) between 1 and 4000", name="text_length_in_range"
        ),
    )

    case_review_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("case_reviews.id", ondelete="CASCADE"),
        nullable=False,
    )
    author_user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    text: Mapped[str] = mapped_column(String, nullable=False)
