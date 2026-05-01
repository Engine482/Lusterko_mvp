from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import IDENTITY_PROVIDERS
from app.db.base import Base, CreatedAtMixin, UUIDPKMixin

_PROVIDERS_CHECK = ", ".join(f"'{p}'" for p in IDENTITY_PROVIDERS)


class UserIdentity(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "user_identities"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_subject",
            name="user_identities_provider_subject_key",
        ),
        CheckConstraint(f"provider in ({_PROVIDERS_CHECK})", name="provider_allowed"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String, nullable=False)
    provider_subject: Mapped[str] = mapped_column(String, nullable=False)
    email_at_provider: Mapped[str | None] = mapped_column(String, nullable=True)
