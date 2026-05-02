from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPKMixin


class AuthLockout(UUIDPKMixin, Base):
    __tablename__ = "auth_lockouts"
    __table_args__ = (
        UniqueConstraint("key", name="auth_lockouts_key_key"),
    )

    key: Mapped[str] = mapped_column(String, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cycle: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_failure_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
