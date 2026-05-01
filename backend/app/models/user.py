from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import USER_STATUSES
from app.db.base import Base, TimestampMixin, UUIDPKMixin

_USER_STATUS_CHECK = ", ".join(f"'{s}'" for s in USER_STATUSES)


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="users_email_key"),
        CheckConstraint(f"status in ({_USER_STATUS_CHECK})", name="status_allowed"),
    )

    full_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    unit_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("units.id"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="active")
