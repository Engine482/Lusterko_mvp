"""demo_registrations: pending self-registration tokens for open demo flow

Sprint UX-4 (Task A — demo registration). Mirrors `password_reset_tokens`:
plaintext token leaves the server in the confirmation email, only sha-256
hash is stored. The row is consumed when the tester clicks the link and
sets their password — at that point a `users` row + three `user_roles`
rows (soldier + commander + medic_psych) are created in the same txn.

Revision ID: 0009_demo_registration
Revises: 0008_auth_lockouts
Create Date: 2026-05-10

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_demo_registration"
down_revision: str | Sequence[str] | None = "0008_auth_lockouts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "demo_registrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "token_hash",
            name="uq_demo_registrations_token_hash",
        ),
    )
    op.create_index(
        "ix_demo_registrations_email",
        "demo_registrations",
        ["email"],
    )


def downgrade() -> None:
    op.drop_index("ix_demo_registrations_email", table_name="demo_registrations")
    op.drop_table("demo_registrations")
