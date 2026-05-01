from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import INET, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import ROLES, SESSION_STATUSES
from app.db.base import Base, CreatedAtMixin, UUIDPKMixin

_ACTIVE_ROLE_CHECK = ", ".join(f"'{r}'" for r in ROLES)
_SESSION_STATUS_CHECK = ", ".join(f"'{s}'" for s in SESSION_STATUSES)


class UserSession(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "user_sessions"
    __table_args__ = (
        CheckConstraint(f"active_role in ({_ACTIVE_ROLE_CHECK})", name="active_role_allowed"),
        CheckConstraint(f"status in ({_SESSION_STATUS_CHECK})", name="status_allowed"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    active_role: Mapped[str] = mapped_column(String, nullable=False)
    role_selected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="active")
    refresh_token_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
