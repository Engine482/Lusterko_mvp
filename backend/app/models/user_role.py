from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import ROLES
from app.db.base import Base, CreatedAtMixin, UUIDPKMixin

_ROLES_CHECK = ", ".join(f"'{r}'" for r in ROLES)


class UserRole(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role", name="user_roles_user_id_role_key"),
        CheckConstraint(f"role in ({_ROLES_CHECK})", name="role_allowed"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String, nullable=False)
