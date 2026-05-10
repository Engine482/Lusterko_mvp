from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, UUIDPKMixin


class DemoRegistration(UUIDPKMixin, CreatedAtMixin, Base):
    """Pending self-registration for the open demo flow.

    Created when a tester submits their email to `/auth/demo/register/start`.
    Consumed when they click the email link and set a password — at that
    point a real `users` row is created with the three tester roles
    (soldier + commander + medic_psych). The token leaves the server only
    in the email; we store the sha-256 hash, mirroring `auth_invites` and
    `password_reset_tokens`.
    """

    __tablename__ = "demo_registrations"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_demo_registrations_token_hash"),
    )

    email: Mapped[str] = mapped_column(String, nullable=False)
    token_hash: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
