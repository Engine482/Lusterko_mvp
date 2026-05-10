"""Daily check-in submissions + due-state calculator (Backlog TASK-2108).

P0 contract:
- baseline must be completed (BASELINE_NOT_COMPLETE).
- exactly one row per (user_id, checkin_date) (DAILY_ALREADY_SUBMITTED).
- Risk Engine (Sprint 4) provides the real last_risk_status read from
  `risk_statuses`; before any recompute the user is in `insufficient_data`.

Due-state v1 (Sprint 3):
- weekly_due: latest weekly PHQ-4 OR PSS-4 is older than 7 days.
- cognitive_due: latest reaction_tests/go_no_go_tests context='cognitive' is
  older than 3 days (≈ twice/week per PRD §8.7).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.baseline_profile import BaselineProfile
from app.models.daily_checkin import DailyCheckin
from app.models.go_no_go_test import GoNoGoTest
from app.models.reaction_test import ReactionTest
from app.models.risk_status import RiskStatusRow
from app.models.weekly_phq4 import WeeklyPhq4Assessment
from app.models.weekly_pss4 import WeeklyPss4Assessment
from app.services.audit_logger import log_event

WEEKLY_INTERVAL = timedelta(days=7)
COGNITIVE_INTERVAL = timedelta(days=3)


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


def _current_status(
    db: Session, user_id: uuid.UUID
) -> Literal["green", "yellow", "red", "insufficient_data"] | None:
    status = db.execute(
        select(RiskStatusRow.current_risk_status).where(
            RiskStatusRow.user_id == user_id
        )
    ).scalar_one_or_none()
    return status  # type: ignore[return-value]


def get_today_state(
    db: Session, *, user_id: uuid.UUID, day: date
) -> tuple[bool, Literal["green", "yellow", "red", "insufficient_data"] | None]:
    row = _existing_today(db, user_id=user_id, day=day)
    return (row is not None, _current_status(db, user_id))


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


def _last_assessment_date(
    db: Session,
    model: type[WeeklyPhq4Assessment] | type[WeeklyPss4Assessment],
    user_id: uuid.UUID,
) -> date | None:
    stmt = (
        select(model.assessment_date)
        .where(model.user_id == user_id)
        .order_by(model.assessment_date.desc())
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


def _last_cognitive_date(
    db: Session,
    model: type[ReactionTest] | type[GoNoGoTest],
    user_id: uuid.UUID,
) -> date | None:
    stmt = (
        select(model.test_date)
        .where(model.user_id == user_id, model.context == "cognitive")
        .order_by(model.test_date.desc())
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


def _is_due(last_seen: date | None, interval: timedelta, *, today: date) -> bool:
    if last_seen is None:
        return True
    return today - last_seen >= interval


def _next_due(last_seen: date | None, interval: timedelta, *, today: date) -> date:
    """Date when the cadenced item next becomes due. Either now (already
    past due) or last_seen + interval — whichever is later but never before
    today."""

    if last_seen is None:
        return today
    candidate = last_seen + interval
    return candidate if candidate >= today else today


def completion_summary(
    db: Session, *, user_id: uuid.UUID, day: date
) -> dict[str, object]:
    profile = db.execute(
        select(BaselineProfile).where(BaselineProfile.user_id == user_id)
    ).scalar_one_or_none()
    baseline_done = profile is not None and profile.baseline_completed
    if not baseline_done:
        return {
            "daily_due": False,
            "weekly_due": False,
            "cognitive_due": False,
            "reaction_test_due": False,
            "go_no_go_due": False,
            "daily_next_due_at": None,
            "weekly_next_due_at": None,
            "cognitive_next_due_at": None,
            "last_risk_status": None,
        }

    daily_done = _existing_today(db, user_id=user_id, day=day) is not None

    last_phq4 = _last_assessment_date(db, WeeklyPhq4Assessment, user_id)
    last_pss4 = _last_assessment_date(db, WeeklyPss4Assessment, user_id)
    weekly_due = _is_due(last_phq4, WEEKLY_INTERVAL, today=day) or _is_due(
        last_pss4, WEEKLY_INTERVAL, today=day
    )

    last_reaction = _last_cognitive_date(db, ReactionTest, user_id)
    last_go_no_go = _last_cognitive_date(db, GoNoGoTest, user_id)
    reaction_due = _is_due(last_reaction, COGNITIVE_INTERVAL, today=day)
    go_no_go_due = _is_due(last_go_no_go, COGNITIVE_INTERVAL, today=day)
    cognitive_due = reaction_due or go_no_go_due

    # "Next due" is the soonest moment the item can be re-taken. Daily is
    # tomorrow when already done today; weekly/cognitive use the latest of
    # their two sub-trackers so the panel matches the OR-style due flag.
    daily_next = day + timedelta(days=1) if daily_done else day
    weekly_next = max(
        _next_due(last_phq4, WEEKLY_INTERVAL, today=day),
        _next_due(last_pss4, WEEKLY_INTERVAL, today=day),
    )
    cognitive_next = max(
        _next_due(last_reaction, COGNITIVE_INTERVAL, today=day),
        _next_due(last_go_no_go, COGNITIVE_INTERVAL, today=day),
    )

    return {
        "daily_due": not daily_done,
        "weekly_due": weekly_due,
        "cognitive_due": cognitive_due,
        "reaction_test_due": reaction_due,
        "go_no_go_due": go_no_go_due,
        "daily_next_due_at": daily_next,
        "weekly_next_due_at": weekly_next,
        "cognitive_next_due_at": cognitive_next,
        "last_risk_status": _current_status(db, user_id),
    }
