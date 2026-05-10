"""Seed the public demo platoon ("Демо-взвод").

Builds one unit with 30 soldiers spread across the three demo risk states
(10 Норма / 10 Потребує уваги / 10 Високий ризик) plus a commander and a
psychologist accountable for the unit. Soldiers carry roughly four weeks of
back-dated daily check-ins and weekly/cognitive assessments so the
commander dashboard and medic queue render with realistic trends.

Idempotent: if the unit already exists the script bails (re-run with
`--reset-demo-data` to recreate). Bootstrap admin and other seeded demo
data (Альфа/Браво from `seed_demo.py`) are never touched.

Usage (Local / Railway):
    DATABASE_URL=... uv run python -m scripts.seed_demo_unit
    DATABASE_URL=... uv run python -m scripts.seed_demo_unit --reset-demo-data

Production safety:
- Refuses to run with `APP_ENV=production` unless `FORCE=1` is also set —
  the public demo is intentionally a one-off seeding step on Railway.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.constants import Role
from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from app.models.case_review import CaseReview
from app.models.case_review_note import CaseReviewNote
from app.models.comment_ai_analysis import CommentAiAnalysis
from app.models.unit import Unit
from app.models.user import User
from app.models.user_role import UserRole
from app.modules.ai import parser as ai_parser
from app.modules.assessments import (
    baseline_service,
    cognitive_service,
    daily_service,
    weekly_service,
)
from app.modules.cases import service as cases_service
from app.modules.risk import service as risk_service
from app.modules.auth import service as auth_service


UNIT_NAME = "Демо-взвод"
DEMO_DOMAIN = "demo-platoon.lusterko.local"
SOLDIER_COUNT = 30
HISTORY_DAYS = 28  # ~4 weeks of trend
DAILY_GAP_DAYS = 1  # one daily per calendar day per soldier
WEEKLY_OFFSETS_DAYS = (21, 14, 7, 0)  # 4 weekly snapshots
COGNITIVE_OFFSETS_DAYS = (24, 18, 12, 6, 0)  # ~every 6 days
RISK_BUCKETS = ("green", "yellow", "red")
SOLDIERS_PER_BUCKET = 10


@dataclass
class DailyValues:
    sleep: int
    energy: int
    mood: int
    concentration: int
    comment: str | None = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Trend templates per risk bucket
# ---------------------------------------------------------------------------


def _green_daily(day_offset: int) -> DailyValues:
    # Stable, healthy. day_offset counts days ago (28 → oldest, 0 → today).
    rng = random.Random(f"green:{day_offset}")
    return DailyValues(
        sleep=rng.randint(7, 9),
        energy=rng.randint(7, 9),
        mood=rng.randint(7, 9),
        concentration=rng.randint(7, 9),
    )


def _yellow_daily(day_offset: int) -> DailyValues:
    # Healthy first three weeks, dip in the last 7 days. Comment is added
    # only when the dip is deepest so the AI text marker shows up but
    # doesn't dominate the whole month.
    rng = random.Random(f"yellow:{day_offset}")
    if day_offset > 7:
        return DailyValues(
            sleep=rng.randint(7, 8),
            energy=rng.randint(6, 8),
            mood=rng.randint(7, 8),
            concentration=rng.randint(7, 8),
        )
    return DailyValues(
        sleep=rng.randint(4, 6),
        energy=rng.randint(4, 6),
        mood=rng.randint(5, 7),
        concentration=rng.randint(5, 7),
        comment=(
            "Складно повноцінно виспатися останні дні."
            if day_offset == 1
            else None
        ),
    )


def _red_daily(day_offset: int) -> DailyValues:
    # Sharp drop in last 14 days; recurring concerning comments keep the
    # text-risk signal high so the Risk Engine maintains red.
    rng = random.Random(f"red:{day_offset}")
    if day_offset > 14:
        return DailyValues(
            sleep=rng.randint(6, 8),
            energy=rng.randint(6, 8),
            mood=rng.randint(6, 8),
            concentration=rng.randint(6, 8),
        )
    comments = [
        "Виснажений, нічого не виходить",
        "Не справляюся, не хочу більше",
        "Жодних сил, постійна тривога",
    ]
    return DailyValues(
        sleep=rng.randint(2, 4),
        energy=rng.randint(2, 4),
        mood=rng.randint(2, 4),
        concentration=rng.randint(2, 4),
        comment=rng.choice(comments) if day_offset % 3 == 0 else None,
    )


_DAILY_PROFILE = {
    "green": _green_daily,
    "yellow": _yellow_daily,
    "red": _red_daily,
}


def _weekly_phq4(bucket: str, week_offset_days: int) -> list[int]:
    # PHQ-4 items each in 0..3. Higher in red, drift up over time for
    # yellow, stable low for green.
    rng = random.Random(f"phq4:{bucket}:{week_offset_days}")
    if bucket == "green":
        return [rng.randint(0, 1) for _ in range(4)]
    if bucket == "yellow":
        if week_offset_days <= 7:
            return [rng.randint(2, 3) for _ in range(4)]
        return [rng.randint(0, 2) for _ in range(4)]
    # red
    return [rng.randint(2, 3) for _ in range(4)]


def _weekly_pss4(bucket: str, week_offset_days: int) -> list[int]:
    rng = random.Random(f"pss4:{bucket}:{week_offset_days}")
    if bucket == "green":
        return [rng.randint(0, 1) for _ in range(4)]
    if bucket == "yellow":
        if week_offset_days <= 7:
            return [rng.randint(2, 4) for _ in range(4)]
        return [rng.randint(1, 3) for _ in range(4)]
    return [rng.randint(2, 4) for _ in range(4)]


def _cognitive(bucket: str, day_offset: int) -> tuple[int, int, int]:
    """Returns (reaction_ms, commission_errors, omission_errors)."""

    rng = random.Random(f"cog:{bucket}:{day_offset}")
    if bucket == "green":
        return rng.randint(330, 410), rng.randint(0, 2), rng.randint(0, 2)
    if bucket == "yellow":
        if day_offset <= 6:
            return rng.randint(440, 520), rng.randint(2, 4), rng.randint(2, 4)
        return rng.randint(360, 430), rng.randint(1, 3), rng.randint(0, 2)
    return rng.randint(550, 680), rng.randint(5, 9), rng.randint(3, 6)


# ---------------------------------------------------------------------------
# Submission helpers (back-dated)
# ---------------------------------------------------------------------------


def _submit_daily(db: Session, *, user_id, when: datetime, values: DailyValues):
    row = daily_service.submit_daily(
        db,
        user_id=user_id,
        sleep_score=values.sleep,
        energy_score=values.energy,
        mood_score=values.mood,
        concentration_score=values.concentration,
        comment_text=values.comment,
        day=when.date(),
    )
    analysis = ai_parser.analyze_comment(values.comment)
    db.add(
        CommentAiAnalysis(
            daily_checkin_id=row.id,
            language_detected=analysis.language_detected,
            has_signal=analysis.has_signal,
            markers=list(analysis.markers),
            text_risk_level=analysis.text_risk_level,
            confidence_score=Decimal(str(round(analysis.confidence_score, 3))),
            summary_for_system=analysis.summary_for_system,
            parse_status=analysis.parse_status,
            raw_model_name=analysis.raw_model_name,
        )
    )
    db.flush()
    return row


def _seed_soldier_history(db: Session, *, user_id, bucket: str) -> None:
    # Baseline first — required for daily checkins to be accepted. The
    # baseline_service helpers don't accept a back-dated `now`, but baseline
    # only needs to exist before we submit daily checkins; its created_at
    # being "today" is fine for demo trends (we display daily/weekly/cognitive
    # history, not baseline history).
    baseline_service.submit_phq4(db, user_id=user_id, answers=[1, 1, 0, 1])
    baseline_service.submit_pss4(db, user_id=user_id, answers=[2, 1, 3, 2])
    baseline_service.submit_sleep(db, user_id=user_id, sleep_score=7)
    baseline_service.submit_reaction_test(
        db, user_id=user_id, median_reaction_time_ms=400, valid_trials=24
    )
    baseline_service.submit_go_no_go(
        db, user_id=user_id, commission_errors=2, omission_errors=1, valid_trials=30
    )
    baseline_service.complete_baseline(db, user_id=user_id)

    # Daily back-fill: HISTORY_DAYS down to today. Track the most recent
    # daily so the single risk-recompute below has a real source_event_id.
    profile = _DAILY_PROFILE[bucket]
    last_daily_id = None
    for offset in range(HISTORY_DAYS, -1, -DAILY_GAP_DAYS):
        when = _now() - timedelta(days=offset)
        row = _submit_daily(db, user_id=user_id, when=when, values=profile(offset))
        last_daily_id = row.id

    # Weekly snapshots (PHQ-4 + PSS-4) at fixed offsets.
    for offset in WEEKLY_OFFSETS_DAYS:
        when = _now() - timedelta(days=offset)
        weekly_service.submit_phq4(
            db, user_id=user_id, answers=_weekly_phq4(bucket, offset), now=when
        )
        weekly_service.submit_pss4(
            db, user_id=user_id, answers=_weekly_pss4(bucket, offset), now=when
        )

    # Cognitive snapshots: reaction + go/no-go together every six days.
    for offset in COGNITIVE_OFFSETS_DAYS:
        when = _now() - timedelta(days=offset)
        rt_ms, commission, omission = _cognitive(bucket, offset)
        cognitive_service.submit_reaction(
            db,
            user_id=user_id,
            median_reaction_time_ms=rt_ms,
            valid_trials=20,
            now=when,
        )
        cognitive_service.submit_go_no_go(
            db,
            user_id=user_id,
            commission_errors=commission,
            omission_errors=omission,
            valid_trials=30,
            now=when,
        )

    # Risk Engine: one final recompute against today's state. Cheaper than
    # recomputing per-event and the dashboard only displays the latest row.
    if last_daily_id is not None:
        risk_service.recompute(
            db,
            user_id=user_id,
            source_event_type="daily_checkin",
            source_event_id=last_daily_id,
        )


# ---------------------------------------------------------------------------
# Reset / detection
# ---------------------------------------------------------------------------


def _is_demo_email(email: str) -> bool:
    return email.endswith(f"@{DEMO_DOMAIN}")


def _demo_unit_exists(db: Session) -> bool:
    return (
        db.execute(select(Unit.id).where(Unit.name == UNIT_NAME).limit(1)).first()
        is not None
    )


def _reset(db: Session) -> None:
    demo_user_ids = list(
        db.execute(
            select(User.id).where(User.email.like(f"%@{DEMO_DOMAIN}"))
        ).scalars()
    )
    if demo_user_ids:
        db.execute(
            delete(AuditLog).where(
                AuditLog.actor_user_id.in_(demo_user_ids)
                | AuditLog.target_user_id.in_(demo_user_ids)
            )
        )
        db.execute(
            delete(CaseReviewNote).where(
                CaseReviewNote.author_user_id.in_(demo_user_ids)
            )
        )
        db.execute(delete(User).where(User.id.in_(demo_user_ids)))
    db.execute(delete(Unit).where(Unit.name == UNIT_NAME))
    db.commit()


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------


def _make_user(
    db: Session,
    *,
    full_name: str,
    email: str,
    unit_id,
    roles: tuple[Role, ...],
) -> User:
    user = User(full_name=full_name, email=email, unit_id=unit_id, status="active")
    db.add(user)
    db.flush()
    for role in roles:
        db.add(UserRole(user_id=user.id, role=role))
    db.flush()
    return user


def _seed_unit(db: Session) -> dict[str, object]:
    unit = Unit(name=UNIT_NAME, is_active=True)
    db.add(unit)
    db.flush()

    commander = _make_user(
        db,
        full_name="Командир Демо-взводу",
        email=f"commander@{DEMO_DOMAIN}",
        unit_id=unit.id,
        roles=("commander",),
    )
    medic = _make_user(
        db,
        full_name="Психолог Демо-взводу",
        email=f"medic@{DEMO_DOMAIN}",
        unit_id=unit.id,
        roles=("medic_psych",),
    )
    invites: dict[str, str] = {
        commander.email: auth_service.issue_invite(
            db, user_id=commander.id, created_by_user_id=None
        ).token,
        medic.email: auth_service.issue_invite(
            db, user_id=medic.id, created_by_user_id=None
        ).token,
    }

    # 30 soldiers, 10 per bucket, deterministic ordering.
    soldier_index = 0
    summary_per_bucket: dict[str, list[dict[str, str]]] = {b: [] for b in RISK_BUCKETS}
    for bucket in RISK_BUCKETS:
        for _ in range(SOLDIERS_PER_BUCKET):
            soldier_index += 1
            email_local = f"boets{soldier_index:02d}"
            soldier = _make_user(
                db,
                full_name=f"Боєць {soldier_index:02d}",
                email=f"{email_local}@{DEMO_DOMAIN}",
                unit_id=unit.id,
                roles=("soldier",),
            )
            _seed_soldier_history(db, user_id=soldier.id, bucket=bucket)
            summary_per_bucket[bucket].append(
                {"full_name": soldier.full_name, "email": soldier.email}
            )

    # Move two priority cases into "В роботі" so the medic queue shows
    # something on the second tab on first load.
    open_red_cases = db.execute(
        select(CaseReview)
        .join(User, User.id == CaseReview.user_id)
        .where(User.unit_id == unit.id, CaseReview.status == "new")
        .order_by(CaseReview.opened_at.desc())
        .limit(2)
    ).scalars().all()
    for c in open_red_cases:
        cases_service.add_note(
            db,
            case_id=c.id,
            author_user_id=medic.id,
            text="Перший огляд психолога. Призначено індивідуальну розмову.",
        )
        cases_service.update_status(
            db,
            case_id=c.id,
            actor_user_id=medic.id,
            new_status="in_review",
        )

    return {
        "unit_id": str(unit.id),
        "unit_name": UNIT_NAME,
        "commander_email": commander.email,
        "medic_email": medic.email,
        "invites": invites,
        "soldiers_per_bucket": summary_per_bucket,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lusterko Демо-взвод seed.")
    parser.add_argument(
        "--reset-demo-data",
        action="store_true",
        help="Delete the Демо-взвод unit + its users before seeding.",
    )
    args = parser.parse_args(argv)

    if os.environ.get("APP_ENV") == "production" and os.environ.get("FORCE") != "1":
        print(
            "Refusing to run Демо-взвод seed with APP_ENV=production. "
            "Set FORCE=1 to override (intentional one-off step on Railway).",
            file=sys.stderr,
        )
        return 2

    with SessionLocal() as db:
        if args.reset_demo_data:
            _reset(db)
        if _demo_unit_exists(db):
            print(
                f"'{UNIT_NAME}' already exists. Re-run with --reset-demo-data "
                "to recreate.",
                file=sys.stderr,
            )
            return 1

        result = _seed_unit(db)
        db.commit()

    print(f"Демо-взвод seeded at {_now().isoformat()}")
    print(f"Unit: {result['unit_name']} ({result['unit_id']})")
    print(f"Commander email: {result['commander_email']}")
    print(f"Psychologist email: {result['medic_email']}")
    print("Invites (email — token):")
    for email, token in result["invites"].items():  # type: ignore[union-attr]
        print(f"  {email} — {token}")
    for bucket, soldiers in result["soldiers_per_bucket"].items():  # type: ignore[union-attr]
        print(f"\nRisk bucket {bucket} ({len(soldiers)} soldiers):")
        for s in soldiers:
            print(f"  {s['full_name']} — {s['email']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
