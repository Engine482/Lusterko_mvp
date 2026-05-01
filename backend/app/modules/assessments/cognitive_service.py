"""Periodic cognitive tests (Backlog TASK-3201..3202).

Reaction time and Go/No-Go are submitted twice a week per PRD §8.7. Cadence
is enforced softly via due-state, not blocked at submission time.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.go_no_go_test import GoNoGoTest
from app.models.reaction_test import ReactionTest
from app.services.audit_logger import log_event


class CognitiveError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def submit_reaction(
    db: Session,
    *,
    user_id: uuid.UUID,
    median_reaction_time_ms: int,
    valid_trials: int,
    now: datetime | None = None,
) -> ReactionTest:
    today = (now or datetime.now(timezone.utc)).date()
    row = ReactionTest(
        user_id=user_id,
        test_date=today,
        context="cognitive",
        median_reaction_time_ms=median_reaction_time_ms,
        valid_trials=valid_trials,
    )
    db.add(row)
    db.flush()
    log_event(
        db,
        event_type="reaction_test_submitted",
        actor_user_id=user_id,
        target_user_id=user_id,
        entity_type="reaction_tests",
        entity_id=row.id,
        metadata={"context": "cognitive", "median_ms": median_reaction_time_ms},
    )
    return row


def submit_go_no_go(
    db: Session,
    *,
    user_id: uuid.UUID,
    commission_errors: int,
    omission_errors: int,
    valid_trials: int,
    now: datetime | None = None,
) -> GoNoGoTest:
    today = (now or datetime.now(timezone.utc)).date()
    row = GoNoGoTest(
        user_id=user_id,
        test_date=today,
        context="cognitive",
        commission_errors=commission_errors,
        omission_errors=omission_errors,
        valid_trials=valid_trials,
    )
    db.add(row)
    db.flush()
    log_event(
        db,
        event_type="go_no_go_submitted",
        actor_user_id=user_id,
        target_user_id=user_id,
        entity_type="go_no_go_tests",
        entity_id=row.id,
        metadata={"context": "cognitive"},
    )
    return row
