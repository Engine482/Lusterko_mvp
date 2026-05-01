"""Daily check-in submissions (Backlog TASK-2108).

P0 contract:
- baseline must be completed (BASELINE_NOT_COMPLETE).
- exactly one row per (user_id, checkin_date) (DAILY_ALREADY_SUBMITTED).
- AI parsing + Risk Engine wiring lands in Sprints 3-4; for now we return
  insufficient_data + skipped per API Contracts §2 valid values.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.baseline_profile import BaselineProfile
from app.models.daily_checkin import DailyCheckin
from app.services.audit_logger import log_event


class DailyError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def today(now: datetime | None = None) -> date:
    return (now or datetime.now(timezone.utc)).date()


def _existing_today(db: Session, *, user_id: uuid.UUID, day: date) -> DailyCheckin | None:
    return db.execute(
        select(DailyCheckin).where(
            DailyCheckin.user_id == user_id, DailyCheckin.checkin_date == day
        )
    ).scalar_one_or_none()


def get_today_state(
    db: Session, *, user_id: uuid.UUID, day: date
) -> tuple[bool, Literal["green", "yellow", "red", "insufficient_data"] | None]:
    row = _existing_today(db, user_id=user_id, day=day)
    return (row is not None, None)  # last_risk_status wired in Sprint 4


def submit_daily(
    db: Session,
    *,
    user_id: uuid.UUID,
    sleep_score: int,
    energy_score: int,
    mood_score: int,
    concentration_score: int,
    comment_text: str | None,
    day: date,
) -> DailyCheckin:
    profile = db.execute(
        select(BaselineProfile).where(BaselineProfile.user_id == user_id)
    ).scalar_one_or_none()
    if profile is None or not profile.baseline_completed:
        raise DailyError("BASELINE_NOT_COMPLETE", "Complete baseline before daily check-in.")

    if _existing_today(db, user_id=user_id, day=day) is not None:
        raise DailyError(
            "DAILY_ALREADY_SUBMITTED", "Daily check-in already submitted today."
        )

    row = DailyCheckin(
        user_id=user_id,
        checkin_date=day,
        sleep_score=sleep_score,
        energy_score=energy_score,
        mood_score=mood_score,
        concentration_score=concentration_score,
        comment_text=comment_text,
    )
    db.add(row)
    db.flush()
    log_event(
        db,
        event_type="daily_checkin_submitted",
        actor_user_id=user_id,
        target_user_id=user_id,
        entity_type="daily_checkins",
        entity_id=row.id,
        metadata={"has_comment": comment_text is not None},
    )
    return row


def completion_summary(
    db: Session, *, user_id: uuid.UUID, day: date
) -> dict[str, object]:
    profile = db.execute(
        select(BaselineProfile).where(BaselineProfile.user_id == user_id)
    ).scalar_one_or_none()
    baseline_done = profile is not None and profile.baseline_completed
    daily_done = (
        _existing_today(db, user_id=user_id, day=day) is not None if baseline_done else False
    )
    return {
        "daily_due": baseline_done and not daily_done,
        # Weekly + cognitive due-state lands in Sprint 3; report False for now.
        "weekly_due": False,
        "cognitive_due": False,
        "last_risk_status": None,  # Risk Engine — Sprint 4
    }
