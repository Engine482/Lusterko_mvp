"""risk engine: risk_statuses, risk_events, risk_rule_hits

DB Schema §5. Sprint 4 — Backlog TASK-4001..4004.

Revision ID: 0005_risk_engine
Revises: 0004_weekly_cognitive_ai
Create Date: 2026-05-01

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_risk_engine"
down_revision: str | Sequence[str] | None = "0004_weekly_cognitive_ai"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_RISK_STATUSES = ("green", "yellow", "red", "insufficient_data")
_HARD_FLAGS = (
    "severe_functional_cluster",
    "severe_cognitive_drop",
    "acute_distress",
    "repeated_high_text_risk",
)
_RISK_DOMAINS = ("functional", "emotional", "cognitive", "text")
_SOURCE_EVENTS = (
    "daily_checkin",
    "weekly_phq4",
    "weekly_pss4",
    "reaction_test",
    "go_no_go",
    "baseline_completion",
)


def _in(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{v}'" for v in values)


def upgrade() -> None:
    op.create_table(
        "risk_statuses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "users.id", ondelete="CASCADE", name="fk_risk_statuses_user_id_users"
            ),
            nullable=False,
        ),
        sa.Column("current_risk_status", sa.Text(), nullable=False),
        sa.Column(
            "current_risk_score",
            sa.Numeric(4, 1),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "functional_score",
            sa.Numeric(4, 1),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "emotional_score",
            sa.Numeric(4, 1),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "cognitive_score",
            sa.Numeric(4, 1),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "text_modifier_score",
            sa.Numeric(4, 1),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("hard_flag", sa.Text(), nullable=True),
        sa.Column("explanation_text", sa.Text(), nullable=True),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.UniqueConstraint("user_id", name="uq_risk_statuses_user_id"),
        sa.CheckConstraint(
            f"current_risk_status in ({_in(_RISK_STATUSES)})",
            name="status_allowed",
        ),
        sa.CheckConstraint(
            f"hard_flag is null or hard_flag in ({_in(_HARD_FLAGS)})",
            name="hard_flag_allowed",
        ),
    )
    op.create_index(
        "ix_risk_statuses_current_risk_status",
        "risk_statuses",
        ["current_risk_status"],
    )

    op.create_table(
        "risk_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "users.id", ondelete="CASCADE", name="fk_risk_events_user_id_users"
            ),
            nullable=False,
        ),
        sa.Column("source_event_type", sa.Text(), nullable=False),
        sa.Column("source_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("previous_status", sa.Text(), nullable=True),
        sa.Column("new_status", sa.Text(), nullable=False),
        sa.Column("total_score", sa.Numeric(4, 1), nullable=False),
        sa.Column("hard_flag", sa.Text(), nullable=True),
        sa.Column("explanation_text", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            f"source_event_type in ({_in(_SOURCE_EVENTS)})",
            name="source_event_type_allowed",
        ),
        sa.CheckConstraint(
            f"new_status in ({_in(_RISK_STATUSES)})", name="new_status_allowed"
        ),
        sa.CheckConstraint(
            f"previous_status is null or previous_status in ({_in(_RISK_STATUSES)})",
            name="previous_status_allowed",
        ),
        sa.CheckConstraint(
            f"hard_flag is null or hard_flag in ({_in(_HARD_FLAGS)})",
            name="hard_flag_allowed",
        ),
    )
    op.create_index(
        "ix_risk_events_user_id_created_at_desc",
        "risk_events",
        ["user_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "ix_risk_events_new_status_created_at_desc",
        "risk_events",
        ["new_status", sa.text("created_at DESC")],
    )

    op.create_table(
        "risk_rule_hits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "risk_event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "risk_events.id",
                ondelete="CASCADE",
                name="fk_risk_rule_hits_risk_event_id_risk_events",
            ),
            nullable=False,
        ),
        sa.Column("rule_code", sa.Text(), nullable=False),
        sa.Column("domain", sa.Text(), nullable=False),
        sa.Column("weight", sa.Numeric(4, 1), nullable=False),
        sa.Column(
            "details_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            f"domain in ({_in(_RISK_DOMAINS)})", name="domain_allowed"
        ),
    )
    op.create_index(
        "ix_risk_rule_hits_risk_event_id",
        "risk_rule_hits",
        ["risk_event_id"],
    )


def downgrade() -> None:
    op.drop_table("risk_rule_hits")
    op.drop_table("risk_events")
    op.drop_table("risk_statuses")
