"""auth_lockouts: brute-force protection state

Sprint 7 EPIC-72. Tracks consecutive failed authentication attempts and the
backoff cycle per key. The key encodes both the endpoint and the
identifying coordinate (IP+email or IP) so each surface has its own
counter and cannot DoS another.

We keep this as one mutable row per key (not an immutable attempt log) so
the table stays tiny and inserts/updates are predictable. An auth-success
deletes the row.

Revision ID: 0008_auth_lockouts
Revises: 0007_email_password_auth
Create Date: 2026-05-02

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_auth_lockouts"
down_revision: str | Sequence[str] | None = "0007_email_password_auth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auth_lockouts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column(
            "failed_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "cycle",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "last_failure_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("key", name="uq_auth_lockouts_key"),
    )
    op.create_index("ix_auth_lockouts_key", "auth_lockouts", ["key"])
    op.create_index(
        "ix_auth_lockouts_locked_until",
        "auth_lockouts",
        ["locked_until"],
    )


def downgrade() -> None:
    op.drop_index("ix_auth_lockouts_locked_until", table_name="auth_lockouts")
    op.drop_index("ix_auth_lockouts_key", table_name="auth_lockouts")
    op.drop_table("auth_lockouts")
