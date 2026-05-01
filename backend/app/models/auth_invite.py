from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import INVITE_STATUSES
from app.db.base import Base, CreatedAtMixin, UUIDPKMixin

_INVITE_STATUS_CHECK = ", ".join(f"'{s}'" for s in INVITE_STATUSES)


class AuthInvite(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "auth_invites"
    __table_args__ = (
        UniqueConstraint("token_hash", name="auth_invites_token_hash_key"),
        CheckConstraint(f"status in ({_INVITE_STATUS_CHECK})", name="status_allowed"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="pending")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
