"""Risk recompute orchestration (Backlog EPIC-42).

Glue between the pure `engine` and DB. One public entrypoint —
`recompute(...)` — is invoked from every soldier-side write that can move the
risk needle: daily check-in, weekly PHQ-4/PSS-4, cognitive tests, baseline
completion (Spec §13 + Backlog TASK-4201..4206).

We always insert a fresh `risk_event` (append-only history) and upsert the
single `risk_statuses` row per user. Rule hits are written under the new
event so the explanation can be reproduced.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import RiskSourceEvent
from app.models.baseline_profile import BaselineProfile
from app.models.comment_ai_analysis import CommentAiAnalysis
from app.models.daily_checkin import DailyCheckin
from app.models.go_no_go_test import GoNoGoTest
from app.models.reaction_test import ReactionTest
from app.models.risk_event import RiskEvent
from app.models.risk_rule_hit import RiskRuleHit
from app.models.risk_status import RiskStatusRow
from app.models.weekly_phq4 import WeeklyPhq4Assessment
from app.models.weekly_pss4 import WeeklyPss4Assessment
from app.modules.cases import service as cases_service
from app.modules.risk import engine
from app.services.audit_logger import log_event


def _baseline_snapshot(
    profile: BaselineProfile | None,
) -> engine.BaselineSnapshot:
    if profile is None:
        return engine.BaselineSnapshot(completed=False)
    return engine.BaselineSnapshot(
        completed=bool(profile.baseline_completed),
        sleep=profile.baseline_sleep_score,
        energy=profile.baseline_energy_score,
        mood=profile.baseline_mood_score,
        concentration=profile.baseline_concentration_score,
        phq4_total=profile.baseline_phq4_total,
        pss4_total=profile.baseline_pss4_total,
        reaction_median_ms=profile.baseline_reaction_time_median_ms,
        gonogo_commission_errors=profile.baseline_go_no_go_commission_errors,
        gonogo_omission_errors=profile.baseline_go_no_go_omission_errors,
    )


def _latest_daily(db: Session, user_id: uuid.UUID) -> DailyCheckin | None:
    return db.execute(
        select(DailyCheckin)
        .where(DailyCheckin.user_id == user_id)
        .order_by(DailyCheckin.checkin_date.desc(), DailyCheckin.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def _latest_weekly_phq4(db: Session, user_id: uuid.UUID) -> WeeklyPhq4Assessment | None:
    return db.execute(
        select(WeeklyPhq4Assessment)
        .where(WeeklyPhq4Assessment.user_id == user_id)
        .order_by(WeeklyPhq4Assessment.assessment_date.desc())
        .limit(1)
    ).scalar_one_or_none()


def _latest_weekly_pss4(db: Session, user_id: uuid.UUID) -> WeeklyPss4Assessment | None:
    return db.execute(
        select(WeeklyPss4Assessment)
        .where(WeeklyPss4Assessment.user_id == user_id)
        .order_by(WeeklyPss4Assessment.assessment_date.desc())
        .limit(1)
    ).scalar_one_or_none()


def _latest_cognitive_reaction(
    db: Session, user_id: uuid.UUID
) -> ReactionTest | None:
    return db.execute(
        select(ReactionTest)
        .where(ReactionTest.user_id == user_id, ReactionTest.context == "cognitive")
        .order_by(ReactionTest.test_date.desc(), ReactionTest.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def _latest_cognitive_gonogo(db: Session, user_id: uuid.UUID) -> GoNoGoTest | None:
    return db.execute(
        select(GoNoGoTest)
        .where(GoNoGoTest.user_id == user_id, GoNoGoTest.context == "cognitive")
        .order_by(GoNoGoTest.test_date.desc(), GoNoGoTest.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def _last_two_text_levels(
    db: Session, user_id: uuid.UUID
) -> tuple[engine.TextSnapshot | None, str | None]:
    """Return (current_text_snapshot, previous_text_risk_level).

    The current row is the most recent comment_ai_analysis for the user; the
    previous one is needed for HF4 (repeated_high_text_risk). We follow daily
    -> analysis joins so the order matches submission order even when two
    daily rows share a date.
    """

    rows = db.execute(
        select(CommentAiAnalysis)
        .join(DailyCheckin, DailyCheckin.id == CommentAiAnalysis.daily_checkin_id)
        .where(DailyCheckin.user_id == user_id)
        .order_by(DailyCheckin.checkin_date.desc(), DailyCheckin.created_at.desc())
        .limit(2)
    ).scalars().all()
    if not rows:
        return None, None
    current = rows[0]
    previous_level = rows[1].text_risk_level if len(rows) > 1 else None
    snapshot = engine.TextSnapshot(
        parse_status=current.parse_status,  # type: ignore[arg-type]
        text_risk_level=current.text_risk_level,  # type: ignore[arg-type]
        confidence_score=Decimal(current.confidence_score),
        markers=tuple(current.markers or []),
        previous_text_risk_level=previous_level,  # type: ignore[arg-type]
    )
    return snapshot, previous_level


def _empty_text() -> engine.TextSnapshot:
    return engine.TextSnapshot(
        parse_status="skipped",
        text_risk_level="unknown",
        confidence_score=Decimal("0"),
        markers=(),
        previous_text_risk_level=None,
    )


def _empty_daily() -> engine.DailySnapshot:
    """Used when recomputing before any daily exists (e.g., baseline-completion
    trigger). Mid-range values produce zero functional score."""

    return engine.DailySnapshot(
        sleep_score=7, energy_score=7, mood_score=7, concentration_score=7
    )


def recompute(
    db: Session,
    *,
    user_id: uuid.UUID,
    source_event_type: RiskSourceEvent,
    source_event_id: uuid.UUID,
    now: datetime | None = None,
) -> RiskEvent:
    """Pull the latest snapshots, run the engine, persist event/status/hits.

    Returns the new RiskEvent. The caller commits the surrounding transaction.
    """

    when = now or datetime.now(timezone.utc)

    profile = db.execute(
        select(BaselineProfile).where(BaselineProfile.user_id == user_id)
    ).scalar_one_or_none()
    baseline = _baseline_snapshot(profile)

    daily_row = _latest_daily(db, user_id)
    daily_snapshot = (
        engine.DailySnapshot(
            sleep_score=daily_row.sleep_score,
            energy_score=daily_row.energy_score,
            mood_score=daily_row.mood_score,
            concentration_score=daily_row.concentration_score,
        )
        if daily_row is not None
        else _empty_daily()
    )

    weekly_phq4 = _latest_weekly_phq4(db, user_id)
    weekly_pss4 = _latest_weekly_pss4(db, user_id)
    weekly_snapshot = engine.WeeklySnapshot(
        phq4_total=weekly_phq4.total_score if weekly_phq4 else None,
        pss4_total=weekly_pss4.total_score if weekly_pss4 else None,
    )

    reaction = _latest_cognitive_reaction(db, user_id)
    gonogo = _latest_cognitive_gonogo(db, user_id)
    cognitive_snapshot = engine.CognitiveSnapshot(
        reaction_median_ms=reaction.median_reaction_time_ms if reaction else None,
        gonogo_commission_errors=gonogo.commission_errors if gonogo else None,
        gonogo_omission_errors=gonogo.omission_errors if gonogo else None,
    )

    text_snapshot, _ = _last_two_text_levels(db, user_id)
    if text_snapshot is None:
        text_snapshot = _empty_text()

    result = engine.compute(
        daily=daily_snapshot,
        weekly=weekly_snapshot,
        cognitive=cognitive_snapshot,
        text=text_snapshot,
        baseline=baseline,
    )

    existing = db.execute(
        select(RiskStatusRow).where(RiskStatusRow.user_id == user_id)
    ).scalar_one_or_none()
    previous_status = existing.current_risk_status if existing else None

    event = RiskEvent(
        user_id=user_id,
        source_event_type=source_event_type,
        source_event_id=source_event_id,
        previous_status=previous_status,
        new_status=result.status,
        total_score=result.total_score,
        hard_flag=result.hard_flag,
        explanation_text=result.explanation_text,
    )
    db.add(event)
    db.flush()

    for hit in result.hits:
        db.add(
            RiskRuleHit(
                risk_event_id=event.id,
                rule_code=hit.rule_code,
                domain=hit.domain,
                weight=hit.weight,
                details_json=hit.details,
            )
        )

    if existing is None:
        db.add(
            RiskStatusRow(
                user_id=user_id,
                current_risk_status=result.status,
                current_risk_score=result.total_score,
                functional_score=result.functional_score,
                emotional_score=result.emotional_score,
                cognitive_score=result.cognitive_score,
                text_modifier_score=result.text_score,
                hard_flag=result.hard_flag,
                explanation_text=result.explanation_text,
                calculated_at=when,
            )
        )
    else:
        existing.current_risk_status = result.status
        existing.current_risk_score = result.total_score
        existing.functional_score = result.functional_score
        existing.emotional_score = result.emotional_score
        existing.cognitive_score = result.cognitive_score
        existing.text_modifier_score = result.text_score
        existing.hard_flag = result.hard_flag
        existing.explanation_text = result.explanation_text
        existing.calculated_at = when

    log_event(
        db,
        event_type="risk_recomputed",
        actor_user_id=user_id,
        target_user_id=user_id,
        entity_type="risk_events",
        entity_id=event.id,
        metadata={
            "source_event_type": source_event_type,
            "source_event_id": str(source_event_id),
            "previous_status": previous_status,
            "new_status": result.status,
            "total_score": str(result.total_score),
            "hard_flag": result.hard_flag,
        },
    )

    # Sprint 5: auto-open or attach to an existing open case (Spec §13).
    cases_service.maybe_open_case(db, user_id=user_id, risk_event=event)

    return event


def latest_status_for(
    db: Session, user_id: uuid.UUID
) -> RiskStatusRow | None:
    return db.execute(
        select(RiskStatusRow).where(RiskStatusRow.user_id == user_id)
    ).scalar_one_or_none()


def recent_events_for(
    db: Session, user_id: uuid.UUID, limit: int = 10
) -> list[RiskEvent]:
    return list(
        db.execute(
            select(RiskEvent)
            .where(RiskEvent.user_id == user_id)
            .order_by(RiskEvent.created_at.desc())
            .limit(limit)
        ).scalars()
    )


def latest_daily_date_for(db: Session, user_id: uuid.UUID) -> date | None:
    row = _latest_daily(db, user_id)
    return row.checkin_date if row else None
