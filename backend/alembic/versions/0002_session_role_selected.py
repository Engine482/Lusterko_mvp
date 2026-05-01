"""user_sessions.role_selected

Adds the boolean flag that backs `role_selection_required` per
`Lusterko_API_Contracts_v1.md` §3.3. False until the user picks a role
through `/auth/select-role`.

Revision ID: 0002_session_role_selected
Revises: 0001_initial_org_and_audit
Create Date: 2026-05-01

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_session_role_selected"
down_revision: str | Sequence[str] | None = "0001_initial_org_and_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user_sessions",
        sa.Column(
            "role_selected",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("user_sessions", "role_selected")
