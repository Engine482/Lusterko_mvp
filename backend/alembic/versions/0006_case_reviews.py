"""case_reviews + case_review_notes

DB Schema §6. Sprint 5 — Backlog TASK-5001..5003.

Partial unique index enforces "one open case per user" per Risk Engine §13.2:
the index covers rows where status != 'closed', so multiple closed cases for
the same user are allowed but only one open case can exist at a time.

Revision ID: 0006_case_reviews
Revises: 0005_risk_engine
Create Date: 2026-05-01

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_case_reviews"
down_revision: str | Sequence[str] | None = "0005_risk_engine"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_CASE_STATUSES = ("new", "in_review", "monitoring", "closed")


def _in(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{v}'" for v in values)


def upgrade() -> None:
    op.create_table(
        "case_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "users.id", ondelete="CASCADE", name="fk_case_reviews_user_id_users"
            ),
            nullable=False,
        ),
        sa.Column(
            "status", sa.Text(), nullable=False, server_default=sa.text("'new'")
        ),
        sa.Column(
            "opened_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "last_risk_event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "risk_events.id",
                ondelete="SET NULL",
                name="fk_case_reviews_last_risk_event_id_risk_events",
            ),
            nullable=True,
        ),
        sa.Column(
            "assigned_to_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "users.id",
                ondelete="SET NULL",
                name="fk_case_reviews_assigned_to_user_id_users",
            ),
            nullable=True,
        ),
        sa.Column(
            "created_at",
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
        sa.CheckConstraint(
            f"status in ({_in(_CASE_STATUSES)})", name="status_allowed"
        ),
    )
    op.create_index("ix_case_reviews_user_id", "case_reviews", ["user_id"])
    op.create_index("ix_case_reviews_status", "case_reviews", ["status"])
    op.create_index(
        "ix_case_reviews_assigned_to_user_id",
        "case_reviews",
        ["assigned_to_user_id"],
    )
    # Partial unique: at most one open (= not closed) case per user.
    op.create_index(
        "uq_case_reviews_user_id_open",
        "case_reviews",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status <> 'closed'"),
    )

    op.create_table(
        "case_review_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "case_review_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "case_reviews.id",
                ondelete="CASCADE",
                name="fk_case_review_notes_case_review_id_case_reviews",
            ),
            nullable=False,
        ),
        sa.Column(
            "author_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "users.id",
                ondelete="RESTRICT",
                name="fk_case_review_notes_author_user_id_users",
            ),
            nullable=False,
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "char_length(text) between 1 and 4000", name="text_length_in_range"
        ),
    )
    op.create_index(
        "ix_case_review_notes_case_review_id",
        "case_review_notes",
        ["case_review_id"],
    )


def downgrade() -> None:
    op.drop_table("case_review_notes")
    op.drop_table("case_reviews")
