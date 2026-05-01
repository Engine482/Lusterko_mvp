"""weekly + cognitive + comment_ai_analyses

DB Schema §3.4-§3.7, §4.1. Sprint 3 — Backlog TASK-3001..3005.

Revision ID: 0004_weekly_cognitive_ai
Revises: 0003_baseline_and_daily
Create Date: 2026-05-01

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_weekly_cognitive_ai"
down_revision: str | Sequence[str] | None = "0003_baseline_and_daily"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_TEST_CONTEXTS = ("baseline", "cognitive")
_LANGUAGES = ("uk", "ru", "mixed", "unknown")
_TEXT_RISK_LEVELS = ("none", "low", "medium", "high", "unknown")
_PARSE_STATUSES = ("success", "failed", "partial", "skipped")


def _in_list(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{v}'" for v in values)


def _weekly_table(name: str, *, item_max: int, total_max: int) -> None:
    op.create_table(
        name,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "users.id", ondelete="CASCADE", name=f"fk_{name}_user_id_users"
            ),
            nullable=False,
        ),
        sa.Column("assessment_date", sa.Date(), nullable=False),
        sa.Column("answer_1", sa.Integer(), nullable=False),
        sa.Column("answer_2", sa.Integer(), nullable=False),
        sa.Column("answer_3", sa.Integer(), nullable=False),
        sa.Column("answer_4", sa.Integer(), nullable=False),
        sa.Column("total_score", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            f"answer_1 between 0 and {item_max} and answer_2 between 0 and {item_max} "
            f"and answer_3 between 0 and {item_max} and answer_4 between 0 and {item_max}",
            name="answers_in_range",
        ),
        sa.CheckConstraint(
            f"total_score between 0 and {total_max}", name="total_in_range"
        ),
    )
    op.create_index(
        f"ix_{name}_user_id_assessment_date_desc",
        name,
        ["user_id", sa.text("assessment_date DESC")],
    )


def upgrade() -> None:
    _weekly_table("weekly_phq4_assessments", item_max=3, total_max=12)
    _weekly_table("weekly_pss4_assessments", item_max=4, total_max=16)

    op.create_table(
        "reaction_tests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "users.id", ondelete="CASCADE", name="fk_reaction_tests_user_id_users"
            ),
            nullable=False,
        ),
        sa.Column("test_date", sa.Date(), nullable=False),
        sa.Column("context", sa.Text(), nullable=False),
        sa.Column("median_reaction_time_ms", sa.Integer(), nullable=False),
        sa.Column("valid_trials", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            f"context in ({_in_list(_TEST_CONTEXTS)})", name="context_allowed"
        ),
        sa.CheckConstraint(
            "median_reaction_time_ms between 50 and 10000", name="median_in_range"
        ),
        sa.CheckConstraint("valid_trials >= 5", name="trials_min"),
    )
    op.create_index(
        "ix_reaction_tests_user_id_test_date_desc",
        "reaction_tests",
        ["user_id", sa.text("test_date DESC")],
    )

    op.create_table(
        "go_no_go_tests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "users.id", ondelete="CASCADE", name="fk_go_no_go_tests_user_id_users"
            ),
            nullable=False,
        ),
        sa.Column("test_date", sa.Date(), nullable=False),
        sa.Column("context", sa.Text(), nullable=False),
        sa.Column("commission_errors", sa.Integer(), nullable=False),
        sa.Column("omission_errors", sa.Integer(), nullable=False),
        sa.Column("valid_trials", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            f"context in ({_in_list(_TEST_CONTEXTS)})", name="context_allowed"
        ),
        sa.CheckConstraint("commission_errors >= 0", name="commission_nonneg"),
        sa.CheckConstraint("omission_errors >= 0", name="omission_nonneg"),
        sa.CheckConstraint("valid_trials >= 10", name="trials_min"),
    )
    op.create_index(
        "ix_go_no_go_tests_user_id_test_date_desc",
        "go_no_go_tests",
        ["user_id", sa.text("test_date DESC")],
    )

    op.create_table(
        "comment_ai_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "daily_checkin_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "daily_checkins.id",
                ondelete="CASCADE",
                name="fk_comment_ai_analyses_daily_checkin_id_daily_checkins",
            ),
            nullable=False,
        ),
        sa.Column("language_detected", sa.Text(), nullable=False),
        sa.Column(
            "has_signal", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "markers",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("text_risk_level", sa.Text(), nullable=False),
        sa.Column(
            "confidence_score",
            sa.Numeric(4, 3),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("summary_for_system", sa.Text(), nullable=True),
        sa.Column("parse_status", sa.Text(), nullable=False),
        sa.Column("raw_model_name", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "daily_checkin_id", name="uq_comment_ai_analyses_daily_checkin_id"
        ),
        sa.CheckConstraint(
            f"language_detected in ({_in_list(_LANGUAGES)})", name="lang_allowed"
        ),
        sa.CheckConstraint(
            f"text_risk_level in ({_in_list(_TEXT_RISK_LEVELS)})",
            name="text_risk_allowed",
        ),
        sa.CheckConstraint(
            f"parse_status in ({_in_list(_PARSE_STATUSES)})",
            name="parse_status_allowed",
        ),
        sa.CheckConstraint(
            "confidence_score >= 0 and confidence_score <= 1",
            name="confidence_in_range",
        ),
    )
    op.create_index(
        "ix_comment_ai_analyses_text_risk_level",
        "comment_ai_analyses",
        ["text_risk_level"],
    )


def downgrade() -> None:
    op.drop_table("comment_ai_analyses")
    op.drop_table("go_no_go_tests")
    op.drop_table("reaction_tests")
    op.drop_table("weekly_pss4_assessments")
    op.drop_table("weekly_phq4_assessments")
