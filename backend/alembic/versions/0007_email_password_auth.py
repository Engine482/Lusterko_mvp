"""email+password auth: users.password_hash, password_reset_tokens; drop user_identities

Sprint 7 (Auth Pivot). See `docs/06_decisions/2026-05-02-auth-email-password.md`
for rationale and `docs/03_planning/Lusterko_Development_Backlog_v1.md` Sprint 7
for task scope.

`users.password_hash` is nullable: a user row exists from the moment an admin
issues an invite, but the hash is only set when the invitee accepts the invite
or completes a password reset. Login rejects users whose hash is NULL.

`password_reset_tokens.token_hash` is sha-256 hex of a random URL-safe token,
mirroring the `auth_invites` discipline (plaintext token leaves the server in
the email, never in the DB).

Revision ID: 0007_email_password_auth
Revises: 0006_case_reviews
Create Date: 2026-05-02

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_email_password_auth"
down_revision: str | Sequence[str] | None = "0006_case_reviews"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("password_hash", sa.Text(), nullable=True),
    )

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "users.id",
                ondelete="CASCADE",
                name="fk_password_reset_tokens_user_id_users",
            ),
            nullable=False,
        ),
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
            name="uq_password_reset_tokens_token_hash",
        ),
    )
    op.create_index(
        "ix_password_reset_tokens_user_id",
        "password_reset_tokens",
        ["user_id"],
    )

    op.drop_table("user_identities")


def downgrade() -> None:
    op.create_table(
        "user_identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "users.id",
                ondelete="CASCADE",
                name="fk_user_identities_user_id_users",
            ),
            nullable=False,
        ),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("provider_subject", sa.Text(), nullable=False),
        sa.Column("email_at_provider", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "provider",
            "provider_subject",
            name="uq_user_identities_provider_provider_subject",
        ),
        sa.CheckConstraint(
            "provider in ('google')",
            name="provider_allowed",
        ),
    )

    op.drop_index(
        "ix_password_reset_tokens_user_id",
        table_name="password_reset_tokens",
    )
    op.drop_table("password_reset_tokens")

    op.drop_column("users", "password_hash")
