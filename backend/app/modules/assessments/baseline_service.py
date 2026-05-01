"""Baseline orchestration (Backlog TASK-2101..2107).

Each per-step submission appends a row to `baseline_events` (audit trail)
and patches the user's `baseline_profiles`. `complete()` flips
`baseline_completed=true` only when all five fields are filled.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import BaselineStep
from app.models.baseline_event import BaselineEvent
from app.models.baseline_profile import BaselineProfile
from app.services.audit_logger import log_event


class BaselineError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


_REQUIRED_FIELDS = (
    "baseline_phq4_total",
    "baseline_pss4_total",
    "baseline_sleep_score",
    "baseline_reaction_time_median_ms",
    "baseline_go_no_go_commission_errors",
)
_STEP_TO_FIELD: dict[BaselineStep, tuple[str, ...]] = {
    "phq4": ("baseline_phq4_total",),
    "pss4": ("baseline_pss4_total",),
    "sleep": ("baseline_sleep_score",),
    "reaction_test": ("baseline_reaction_time_median_ms",),
    "go_no_go": (
        "baseline_go_no_go_commission_errors",
        "baseline_go_no_go_omission_errors",
    ),
}


def _get_or_create_profile(db: Session, user_id: uuid.UUID) -> BaselineProfile:
    profile = db.execute(
        select(BaselineProfile).where(BaselineProfile.user_id == user_id)
    ).scalar_one_or_none()
    if profile is None:
        profile = BaselineProfile(user_id=user_id)
        db.add(profile)
        db.flush()
    return profile


def _record_event(
    db: Session,
    *,
    user_id: uuid.UUID,
    step: BaselineStep,
    payload: dict[str, Any],
) -> None:
    db.add(BaselineEvent(user_id=user_id, step_code=step, payload_json=payload))


def submit_phq4(
    db: Session, *, user_id: uuid.UUID, answers: list[int]
) -> BaselineProfile:
    if len(answers) != 4:
        raise BaselineError("VALIDATION_ERROR", "PHQ-4 expects 4 answers.")
    total = sum(answers)
    profile = _get_or_create_profile(db, user_id)
    if profile.baseline_completed:
        raise BaselineError("CONFLICT", "Baseline already completed.")
    profile.baseline_phq4_total = total
    _record_event(db, user_id=user_id, step="phq4", payload={"answers": answers, "total": total})
    log_event(
        db,
        event_type="weekly_phq4_submitted",  # baseline reuses the PHQ-4 event type
        actor_user_id=user_id,
        target_user_id=user_id,
        entity_type="baseline_profiles",
        entity_id=profile.id,
        metadata={"context": "baseline", "total": total},
    )
    return profile


def submit_pss4(
    db: Session, *, user_id: uuid.UUID, answers: list[int]
) -> BaselineProfile:
    if len(answers) != 4:
        raise BaselineError("VALIDATION_ERROR", "PSS-4 expects 4 answers.")
    # Standard PSS-4 scoring: items 1,2 direct; items 3,4 reverse-scored (4 - x).
    a1, a2, a3, a4 = answers
    total = a1 + a2 + (4 - a3) + (4 - a4)
    profile = _get_or_create_profile(db, user_id)
    if profile.baseline_completed:
        raise BaselineError("CONFLICT", "Baseline already completed.")
    profile.baseline_pss4_total = total
    _record_event(db, user_id=user_id, step="pss4", payload={"answers": answers, "total": total})
    log_event(
        db,
        event_type="weekly_pss4_submitted",
        actor_user_id=user_id,
        target_user_id=user_id,
        entity_type="baseline_profiles",
        entity_id=profile.id,
        metadata={"context": "baseline", "total": total},
    )
    return profile


def submit_sleep(
    db: Session, *, user_id: uuid.UUID, sleep_score: int
) -> BaselineProfile:
    profile = _get_or_create_profile(db, user_id)
    if profile.baseline_completed:
        raise BaselineError("CONFLICT", "Baseline already completed.")
    profile.baseline_sleep_score = sleep_score
    _record_event(db, user_id=user_id, step="sleep", payload={"sleep_score": sleep_score})
    return profile


def submit_reaction_test(
    db: Session,
    *,
    user_id: uuid.UUID,
    median_reaction_time_ms: int,
    valid_trials: int,
) -> BaselineProfile:
    profile = _get_or_create_profile(db, user_id)
    if profile.baseline_completed:
        raise BaselineError("CONFLICT", "Baseline already completed.")
    profile.baseline_reaction_time_median_ms = median_reaction_time_ms
    _record_event(
        db,
        user_id=user_id,
        step="reaction_test",
        payload={
            "median_reaction_time_ms": median_reaction_time_ms,
            "valid_trials": valid_trials,
        },
    )
    log_event(
        db,
        event_type="reaction_test_submitted",
        actor_user_id=user_id,
        target_user_id=user_id,
        entity_type="baseline_profiles",
        entity_id=profile.id,
        metadata={"context": "baseline", "median_ms": median_reaction_time_ms},
    )
    return profile


def submit_go_no_go(
    db: Session,
    *,
    user_id: uuid.UUID,
    commission_errors: int,
    omission_errors: int,
    valid_trials: int,
) -> BaselineProfile:
    profile = _get_or_create_profile(db, user_id)
    if profile.baseline_completed:
        raise BaselineError("CONFLICT", "Baseline already completed.")
    profile.baseline_go_no_go_commission_errors = commission_errors
    profile.baseline_go_no_go_omission_errors = omission_errors
    _record_event(
        db,
        user_id=user_id,
        step="go_no_go",
        payload={
            "commission_errors": commission_errors,
            "omission_errors": omission_errors,
            "valid_trials": valid_trials,
        },
    )
    log_event(
        db,
        event_type="go_no_go_submitted",
        actor_user_id=user_id,
        target_user_id=user_id,
        entity_type="baseline_profiles",
        entity_id=profile.id,
        metadata={"context": "baseline"},
    )
    return profile


def complete_baseline(
    db: Session, *, user_id: uuid.UUID
) -> BaselineProfile:
    profile = _get_or_create_profile(db, user_id)
    if profile.baseline_completed:
        return profile
    missing: list[str] = [f for f in _REQUIRED_FIELDS if getattr(profile, f) is None]
    if missing:
        raise BaselineError(
            "VALIDATION_ERROR",
            "Baseline steps missing.",
        )
    profile.baseline_completed = True
    profile.completed_at = datetime.now(timezone.utc)
    return profile


def step_status(profile: BaselineProfile | None) -> dict[BaselineStep, bool]:
    if profile is None:
        return {step: False for step in _STEP_TO_FIELD}
    return {
        step: all(getattr(profile, f) is not None for f in fields)
        for step, fields in _STEP_TO_FIELD.items()
    }


def next_required_step(profile: BaselineProfile | None) -> BaselineStep | None:
    statuses = step_status(profile)
    ordered: tuple[BaselineStep, ...] = ("phq4", "pss4", "sleep", "reaction_test", "go_no_go")
    for step in ordered:
        if not statuses[step]:
            return step
    return None
