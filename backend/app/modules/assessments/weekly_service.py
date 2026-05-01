"""Weekly PHQ-4 / PSS-4 reassessments (Backlog TASK-3101..3102).

Single-shot submission per call. Frequency rule lives in the due-state
calculator (`completion_summary`): a fresh weekly is due once the latest row
is older than 7 days (PRD §8.7).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.weekly_phq4 import WeeklyPhq4Assessment
from app.models.weekly_pss4 import WeeklyPss4Assessment
from app.services.audit_logger import log_event


class WeeklyError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def submit_phq4(
    db: Session,
    *,
    user_id: uuid.UUID,
    answers: list[int],
    now: datetime | None = None,
) -> WeeklyPhq4Assessment:
    if len(answers) != 4:
        raise WeeklyError("VALIDATION_ERROR", "PHQ-4 expects 4 answers.")
    a1, a2, a3, a4 = answers
    total = a1 + a2 + a3 + a4
    today = (now or datetime.now(timezone.utc)).date()
    row = WeeklyPhq4Assessment(
        user_id=user_id,
        assessment_date=today,
        answer_1=a1,
        answer_2=a2,
        answer_3=a3,
        answer_4=a4,
        total_score=total,
    )
    db.add(row)
    db.flush()
    log_event(
        db,
        event_type="weekly_phq4_submitted",
        actor_user_id=user_id,
        target_user_id=user_id,
        entity_type="weekly_phq4_assessments",
        entity_id=row.id,
        metadata={"context": "weekly", "total": total},
    )
    return row


def submit_pss4(
    db: Session,
    *,
    user_id: uuid.UUID,
    answers: list[int],
    now: datetime | None = None,
) -> WeeklyPss4Assessment:
    if len(answers) != 4:
        raise WeeklyError("VALIDATION_ERROR", "PSS-4 expects 4 answers.")
    # Standard PSS-4: items 1,2 direct; items 3,4 reverse-scored (4 - x).
    a1, a2, a3, a4 = answers
    total = a1 + a2 + (4 - a3) + (4 - a4)
    today = (now or datetime.now(timezone.utc)).date()
    row = WeeklyPss4Assessment(
        user_id=user_id,
        assessment_date=today,
        answer_1=a1,
        answer_2=a2,
        answer_3=a3,
        answer_4=a4,
        total_score=total,
    )
    db.add(row)
    db.flush()
    log_event(
        db,
        event_type="weekly_pss4_submitted",
        actor_user_id=user_id,
        target_user_id=user_id,
        entity_type="weekly_pss4_assessments",
        entity_id=row.id,
        metadata={"context": "weekly", "total": total},
    )
    return row
