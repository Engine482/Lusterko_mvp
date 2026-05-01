"""baseline_profiles + baseline_events + daily_checkins

DB Schema §3.1-§3.3. Sprint 2 — Backlog TASK-2001..2003.

Revision ID: 0003_baseline_and_daily
Revises: 0002_session_role_selected
Create Date: 2026-05-01

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_baseline_and_daily"
down_revision: str | Sequence[str] | None = "0002_session_role_selected"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_BASELINE_STEPS = ("phq4", "pss4", "sleep", "reaction_test", "go_no_go")


def _in_list(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{v}'" for v in values)


def upgrade() -> None:
    op.create_table(
        "baseline_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "users.id",
                ondelete="CASCADE",
                name="fk_baseline_profiles_user_id_users",
            ),
            nullable=False,
        ),
        sa.Column("baseline_sleep_score", sa.Integer(), nullable=True),
        sa.Column("baseline_energy_score", sa.Integer(), nullable=True),
        sa.Column("baseline_mood_score", sa.Integer(), nullable=True),
        sa.Column("baseline_concentration_score", sa.Integer(), nullable=True),
        sa.Column("baseline_phq4_total", sa.Integer(), nullable=True),
        sa.Column("baseline_pss4_total", sa.Integer(), nullable=True),
        sa.Column("baseline_reaction_time_median_ms", sa.Integer(), nullable=True),
        sa.Column("baseline_go_no_go_commission_errors", sa.Integer(), nullable=True),
        sa.Column("baseline_go_no_go_omission_errors", sa.Integer(), nullable=True),
        sa.Column(
            "baseline_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint("user_id", name="uq_baseline_profiles_user_id"),
    )

    op.create_table(
        "baseline_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "users.id",
                ondelete="CASCADE",
                name="fk_baseline_events_user_id_users",
            ),
            nullable=False,
        ),
        sa.Column("step_code", sa.Text(), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            f"step_code in ({_in_list(_BASELINE_STEPS)})",
            name="step_code_allowed",
        ),
    )
    op.create_index("ix_baseline_events_user_id", "baseline_events", ["user_id"])
    op.create_index(
        "ix_baseline_events_recorded_at_desc",
        "baseline_events",
        [sa.text("recorded_at DESC")],
    )

    op.create_table(
        "daily_checkins",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "users.id",
                ondelete="CASCADE",
                name="fk_daily_checkins_user_id_users",
            ),
            nullable=False,
        ),
        sa.Column("checkin_date", sa.Date(), nullable=False),
        sa.Column("sleep_score", sa.Integer(), nullable=False),
        sa.Column("energy_score", sa.Integer(), nullable=False),
        sa.Column("mood_score", sa.Integer(), nullable=False),
        sa.Column("concentration_score", sa.Integer(), nullable=False),
        sa.Column("comment_text", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "user_id", "checkin_date", name="uq_daily_checkins_user_id_checkin_date"
        ),
        sa.CheckConstraint(
            "sleep_score between 0 and 10 and energy_score between 0 and 10 "
            "and mood_score between 0 and 10 and concentration_score between 0 and 10",
            name="scores_in_range",
        ),
        sa.CheckConstraint(
            "comment_text is null or char_length(comment_text) <= 300",
            name="comment_max_300",
        ),
    )
    op.create_index(
        "ix_daily_checkins_user_id_checkin_date_desc",
        "daily_checkins",
        ["user_id", sa.text("checkin_date DESC")],
    )


def downgrade() -> None:
    op.drop_table("daily_checkins")
    op.drop_table("baseline_events")
    op.drop_table("baseline_profiles")
