"""Demo seed: realistic units, users, and assessments for stakeholder demos.

Creates two demo units (Альфа, Браво) populated with a commander, a medic,
and a spread of soldiers at every interesting risk state — green, yellow,
red via cumulative drop, red via acute-distress hard flag — so the
commander dashboard, medic queue, and audit trail render with real data
straight after a fresh `make db-migrate`.

Usage:
    DATABASE_URL=... uv run python -m scripts.seed_demo
    DATABASE_URL=... uv run python -m scripts.seed_demo --reset

Default behavior bails if demo data already exists. `--reset` deletes the
demo users/units and recreates them. Bootstrap admin from `scripts.seed`
is never touched.

Backlog TASK-5805. NOT for production: emails are deterministic and any
real OAuth login is bypassed by directly seeding the User rows.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.constants import Role
from app.db.session import SessionLocal
from app.models.unit import Unit
from app.models.user import User
from app.models.user_role import UserRole
from app.modules.assessments import (
    baseline_service,
    cognitive_service,
    daily_service,
    weekly_service,
)
from app.modules.ai import parser as ai_parser
from app.modules.cases import service as cases_service
from app.modules.risk import service as risk_service
from app.modules.auth import service as auth_service
from app.models.comment_ai_analysis import CommentAiAnalysis
from decimal import Decimal


_DEMO_EMAIL_DOMAIN = "demo.lusterko.local"
_DEMO_UNIT_NAMES = ("Альфа (демо)", "Браво (демо)")


def _is_demo_email(email: str) -> bool:
    return email.endswith(f"@{_DEMO_EMAIL_DOMAIN}")


# --- Reset ------------------------------------------------------------------


def _reset(db: Session) -> None:
    """Delete demo users (cascades to their assessments + risk + cases) and
    demo units. Bootstrap admin and any production data are untouched.

    audit_logs.actor/target_user_id and case_review_notes.author_user_id are
    declared NO ACTION/RESTRICT in the schema (we want audit history to
    survive a real user delete in production), so the seed clears those
    referencing rows for demo users explicitly before dropping the users.
    """

    from app.models.audit_log import AuditLog
    from app.models.case_review_note import CaseReviewNote

    demo_user_ids = list(
        db.execute(
            select(User.id).where(User.email.like(f"%@{_DEMO_EMAIL_DOMAIN}"))
        ).scalars()
    )
    if demo_user_ids:
        db.execute(
            delete(AuditLog).where(
                (AuditLog.actor_user_id.in_(demo_user_ids))
                | (AuditLog.target_user_id.in_(demo_user_ids))
            )
        )
        db.execute(
            delete(CaseReviewNote).where(
                CaseReviewNote.author_user_id.in_(demo_user_ids)
            )
        )
        db.execute(delete(User).where(User.id.in_(demo_user_ids)))
    db.execute(delete(Unit).where(Unit.name.in_(_DEMO_UNIT_NAMES)))
    db.commit()


def _demo_data_exists(db: Session) -> bool:
    if db.execute(
        select(Unit.id).where(Unit.name.in_(_DEMO_UNIT_NAMES)).limit(1)
    ).first() is not None:
        return True
    if db.execute(
        select(User.id).where(User.email.like(f"%@{_DEMO_EMAIL_DOMAIN}")).limit(1)
    ).first() is not None:
        return True
    return False


# --- Building blocks --------------------------------------------------------


def _make_user(
    db: Session,
    *,
    full_name: str,
    email: str,
    unit_id,  # type: ignore[no-untyped-def]
    roles: Sequence[Role],
) -> User:
    user = User(full_name=full_name, email=email, unit_id=unit_id, status="active")
    db.add(user)
    db.flush()
    for role in roles:
        db.add(UserRole(user_id=user.id, role=role))
    db.flush()
    return user


def _complete_baseline(db: Session, user_id) -> None:  # type: ignore[no-untyped-def]
    baseline_service.submit_phq4(db, user_id=user_id, answers=[1, 1, 0, 1])
    baseline_service.submit_pss4(db, user_id=user_id, answers=[2, 1, 3, 2])
    baseline_service.submit_sleep(db, user_id=user_id, sleep_score=7)
    baseline_service.submit_reaction_test(
        db, user_id=user_id, median_reaction_time_ms=400, valid_trials=24
    )
    baseline_service.submit_go_no_go(
        db,
        user_id=user_id,
        commission_errors=2,
        omission_errors=1,
        valid_trials=30,
    )
    profile = baseline_service.complete_baseline(db, user_id=user_id)
    risk_service.recompute(
        db,
        user_id=user_id,
        source_event_type="baseline_completion",
        source_event_id=profile.id,
    )


def _submit_daily(
    db: Session,
    *,
    user_id,  # type: ignore[no-untyped-def]
    sleep: int,
    energy: int,
    mood: int,
    concentration: int,
    comment: str | None = None,
) -> None:
    row = daily_service.submit_daily(
        db,
        user_id=user_id,
        sleep_score=sleep,
        energy_score=energy,
        mood_score=mood,
        concentration_score=concentration,
        comment_text=comment,
        day=daily_service.today(),
    )
    analysis = ai_parser.analyze_comment(comment)
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
    risk_service.recompute(
        db,
        user_id=user_id,
        source_event_type="daily_checkin",
        source_event_id=row.id,
    )


def _submit_weekly(
    db: Session,
    *,
    user_id,  # type: ignore[no-untyped-def]
    phq4: list[int],
    pss4: list[int],
) -> None:
    phq = weekly_service.submit_phq4(db, user_id=user_id, answers=phq4)
    risk_service.recompute(
        db,
        user_id=user_id,
        source_event_type="weekly_phq4",
        source_event_id=phq.id,
    )
    pss = weekly_service.submit_pss4(db, user_id=user_id, answers=pss4)
    risk_service.recompute(
        db,
        user_id=user_id,
        source_event_type="weekly_pss4",
        source_event_id=pss.id,
    )


def _submit_cognitive(
    db: Session,
    *,
    user_id,  # type: ignore[no-untyped-def]
    reaction_ms: int,
    commission: int,
    omission: int,
) -> None:
    rt = cognitive_service.submit_reaction(
        db,
        user_id=user_id,
        median_reaction_time_ms=reaction_ms,
        valid_trials=20,
    )
    risk_service.recompute(
        db,
        user_id=user_id,
        source_event_type="reaction_test",
        source_event_id=rt.id,
    )
    gn = cognitive_service.submit_go_no_go(
        db,
        user_id=user_id,
        commission_errors=commission,
        omission_errors=omission,
        valid_trials=30,
    )
    risk_service.recompute(
        db,
        user_id=user_id,
        source_event_type="go_no_go",
        source_event_id=gn.id,
    )


# --- Soldier scenarios ------------------------------------------------------


@dataclass
class SoldierProfile:
    full_name: str
    email_local: str
    scenario: str
    invite_token: str | None = None


def _scenario_just_invited(db: Session, user: User) -> None:
    # No baseline; only the invite (created in main()).
    return


def _scenario_baseline_only(db: Session, user: User) -> None:
    _complete_baseline(db, user.id)


def _scenario_healthy_daily(db: Session, user: User) -> None:
    _complete_baseline(db, user.id)
    _submit_daily(db, user_id=user.id, sleep=8, energy=7, mood=8, concentration=7)


def _scenario_yellow_weekly(db: Session, user: User) -> None:
    _complete_baseline(db, user.id)
    # Emotional alone caps at 2; pair with a moderate daily drop so the
    # cumulative score lands in 3..5 (yellow band, Spec §10.2).
    _submit_weekly(
        db, user_id=user.id, phq4=[3, 3, 2, 1], pss4=[3, 3, 0, 1]
    )
    _submit_daily(
        db,
        user_id=user.id,
        sleep=4,  # severe drop vs baseline 7 → F1 +1
        energy=5,  # moderate drop → F2 +0.5
        mood=7,
        concentration=7,
    )


def _scenario_red_functional(db: Session, user: User) -> None:
    _complete_baseline(db, user.id)
    _submit_daily(
        db,
        user_id=user.id,
        sleep=2,
        energy=2,
        mood=2,
        concentration=2,
        comment="Виснажений, нічого не виходить",
    )


def _scenario_red_acute_distress(db: Session, user: User) -> None:
    _complete_baseline(db, user.id)
    _submit_daily(
        db,
        user_id=user.id,
        sleep=3,
        energy=3,
        mood=3,
        concentration=3,
        comment="Не справляюся, не хочу більше",
    )


def _scenario_red_cognitive(db: Session, user: User) -> None:
    _complete_baseline(db, user.id)
    _submit_cognitive(
        db, user_id=user.id, reaction_ms=620, commission=8, omission=4
    )


_SCENARIOS = {
    "just_invited": _scenario_just_invited,
    "baseline_only": _scenario_baseline_only,
    "healthy_daily": _scenario_healthy_daily,
    "yellow_weekly": _scenario_yellow_weekly,
    "red_functional": _scenario_red_functional,
    "red_acute_distress": _scenario_red_acute_distress,
    "red_cognitive": _scenario_red_cognitive,
}


def _seed_unit(
    db: Session,
    *,
    unit_name: str,
    short: str,
    short_slug: str,
    soldiers: list[SoldierProfile],
) -> dict[str, object]:
    unit = Unit(name=unit_name, is_active=True)
    db.add(unit)
    db.flush()

    commander = _make_user(
        db,
        full_name=f"Командир {short}",
        email=f"commander.{short_slug}@{_DEMO_EMAIL_DOMAIN}",
        unit_id=unit.id,
        roles=("commander",),
    )
    medic = _make_user(
        db,
        full_name=f"Медик {short}",
        email=f"medic.{short_slug}@{_DEMO_EMAIL_DOMAIN}",
        unit_id=unit.id,
        roles=("medic_psych",),
    )

    invites: dict[str, str] = {}
    invites[commander.email] = auth_service.issue_invite(
        db, user_id=commander.id, created_by_user_id=None
    ).token
    invites[medic.email] = auth_service.issue_invite(
        db, user_id=medic.id, created_by_user_id=None
    ).token

    for profile in soldiers:
        user = _make_user(
            db,
            full_name=profile.full_name,
            email=f"{profile.email_local}@{_DEMO_EMAIL_DOMAIN}",
            unit_id=unit.id,
            roles=("soldier",),
        )
        invites[user.email] = auth_service.issue_invite(
            db, user_id=user.id, created_by_user_id=None
        ).token
        _SCENARIOS[profile.scenario](db, user)
        profile.invite_token = invites[user.email]

    # Medic walkthrough: pick the first open case in this unit and add a
    # note + move to in_review so the medic queue isn't all-new on first
    # load.
    from app.models.case_review import CaseReview

    open_case = db.execute(
        select(CaseReview)
        .join(User, User.id == CaseReview.user_id)
        .where(User.unit_id == unit.id, CaseReview.status == "new")
        .order_by(CaseReview.opened_at.asc())
        .limit(1)
    ).scalar_one_or_none()
    if open_case is not None:
        cases_service.add_note(
            db,
            case_id=open_case.id,
            author_user_id=medic.id,
            text="Перший огляд медика. Призначено моніторинг рівня сну.",
        )
        cases_service.update_status(
            db,
            case_id=open_case.id,
            actor_user_id=medic.id,
            new_status="in_review",
        )

    return {
        "unit_id": str(unit.id),
        "unit_name": unit_name,
        "commander_id": str(commander.id),
        "medic_id": str(medic.id),
        "soldiers": [
            {
                "user_id": None,
                "full_name": s.full_name,
                "email": f"{s.email_local}@{_DEMO_EMAIL_DOMAIN}",
                "scenario": s.scenario,
                "invite_token": s.invite_token,
            }
            for s in soldiers
        ],
        "invites": invites,
    }


# --- Entry point ------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lusterko demo seed.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing demo users + units before seeding.",
    )
    args = parser.parse_args(argv)

    # TASK-6304 — never let demo seed accidentally run against the prod DB.
    # Explicit opt-out (FORCE=1) exists only so a developer pointing local
    # tooling at a misconfigured env can override after reading this guard.
    if os.environ.get("APP_ENV") == "production" and os.environ.get("FORCE") != "1":
        print(
            "Refusing to run demo seed with APP_ENV=production. "
            "Set FORCE=1 to override (don't, unless you really mean it).",
            file=sys.stderr,
        )
        return 2

    with SessionLocal() as db:
        if args.reset:
            _reset(db)
        if _demo_data_exists(db):
            print(
                "Demo data already present. Re-run with --reset to recreate "
                "(this deletes demo users/units only; bootstrap admin is safe).",
                file=sys.stderr,
            )
            return 1

        alpha_soldiers = [
            SoldierProfile("Боєць 1 Альфа", "soldier1.alpha", "just_invited"),
            SoldierProfile("Боєць 2 Альфа", "soldier2.alpha", "baseline_only"),
            SoldierProfile("Боєць 3 Альфа", "soldier3.alpha", "healthy_daily"),
            SoldierProfile("Боєць 4 Альфа", "soldier4.alpha", "yellow_weekly"),
            SoldierProfile("Боєць 5 Альфа", "soldier5.alpha", "red_functional"),
            SoldierProfile("Боєць 6 Альфа", "soldier6.alpha", "red_acute_distress"),
        ]
        bravo_soldiers = [
            SoldierProfile("Боєць 1 Браво", "soldier1.bravo", "healthy_daily"),
            SoldierProfile("Боєць 2 Браво", "soldier2.bravo", "yellow_weekly"),
            SoldierProfile("Боєць 3 Браво", "soldier3.bravo", "red_cognitive"),
        ]

        alpha = _seed_unit(
            db,
            unit_name="Альфа (демо)",
            short="Альфа",
            short_slug="alpha",
            soldiers=alpha_soldiers,
        )
        bravo = _seed_unit(
            db,
            unit_name="Браво (демо)",
            short="Браво",
            short_slug="bravo",
            soldiers=bravo_soldiers,
        )
        db.commit()

    print("Demo seed OK")
    print(f"Generated at: {datetime.now(timezone.utc).isoformat()}")
    print()
    for u in (alpha, bravo):
        print(f"Unit: {u['unit_name']} ({u['unit_id']})")
        print("  Invites (email — token):")
        for email, token in u["invites"].items():  # type: ignore[union-attr]
            print(f"    {email} — {token}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
