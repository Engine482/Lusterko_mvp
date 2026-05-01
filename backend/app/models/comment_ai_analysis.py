from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import LANGUAGES_DETECTED, PARSE_STATUSES, TEXT_RISK_LEVELS
from app.db.base import Base, CreatedAtMixin, UUIDPKMixin

_LANG_CHECK = ", ".join(f"'{x}'" for x in LANGUAGES_DETECTED)
_TEXT_RISK_CHECK = ", ".join(f"'{x}'" for x in TEXT_RISK_LEVELS)
_PARSE_CHECK = ", ".join(f"'{x}'" for x in PARSE_STATUSES)


class CommentAiAnalysis(UUIDPKMixin, CreatedAtMixin, Base):
    """Result of AI text parsing for a daily check-in (DB Schema §4.1)."""

    __tablename__ = "comment_ai_analyses"
    __table_args__ = (
        UniqueConstraint(
            "daily_checkin_id", name="comment_ai_analyses_daily_checkin_id_key"
        ),
        CheckConstraint(f"language_detected in ({_LANG_CHECK})", name="lang_allowed"),
        CheckConstraint(f"text_risk_level in ({_TEXT_RISK_CHECK})", name="text_risk_allowed"),
        CheckConstraint(f"parse_status in ({_PARSE_CHECK})", name="parse_status_allowed"),
        CheckConstraint(
            "confidence_score >= 0 and confidence_score <= 1",
            name="confidence_in_range",
        ),
    )

    daily_checkin_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("daily_checkins.id", ondelete="CASCADE"),
        nullable=False,
    )
    language_detected: Mapped[str] = mapped_column(String, nullable=False)
    has_signal: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    markers: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default="'[]'::jsonb"
    )
    text_risk_level: Mapped[str] = mapped_column(String, nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 3), nullable=False, server_default="0"
    )
    summary_for_system: Mapped[str | None] = mapped_column(String, nullable=True)
    parse_status: Mapped[str] = mapped_column(String, nullable=False)
    raw_model_name: Mapped[str | None] = mapped_column(String, nullable=True)
