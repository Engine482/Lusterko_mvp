from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import BASELINE_STEPS
from app.db.base import Base, CreatedAtMixin, UUIDPKMixin

_STEPS_CHECK = ", ".join(f"'{s}'" for s in BASELINE_STEPS)


class BaselineEvent(UUIDPKMixin, CreatedAtMixin, Base):
    """Append-only audit-friendly trail of every baseline submission (§3.2)."""

    __tablename__ = "baseline_events"
    __table_args__ = (
        CheckConstraint(f"step_code in ({_STEPS_CHECK})", name="step_code_allowed"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_code: Mapped[str] = mapped_column(String, nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
