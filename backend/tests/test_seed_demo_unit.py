"""Smoke test for the Демо-взвод seed.

Boots the seed against the truncated test DB and asserts the headline
shape: one Демо-взвод unit, 30 soldiers, 10/10/10 risk distribution, plus
a commander + psychologist account scoped to the unit.
"""

from __future__ import annotations

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.case_review import CaseReview
from app.models.risk_status import RiskStatusRow
from app.models.unit import Unit
from app.models.user import User
from app.models.user_role import UserRole
from scripts import seed_demo_unit


def test_seed_demo_unit_creates_30_soldiers_with_10_10_10_distribution() -> None:
    rc = seed_demo_unit.main([])
    assert rc == 0

    with SessionLocal() as db:
        unit = db.execute(
            select(Unit).where(Unit.name == seed_demo_unit.UNIT_NAME)
        ).scalar_one()
        users = db.execute(
            select(User).where(User.unit_id == unit.id)
        ).scalars().all()
        soldier_ids = [
            u.id for u in users
            if "soldier" in {
                r for r in db.execute(
                    select(UserRole.role).where(UserRole.user_id == u.id)
                ).scalars()
            }
        ]
        assert len(soldier_ids) == seed_demo_unit.SOLDIER_COUNT

        risk_rows = db.execute(
            select(RiskStatusRow.current_risk_status, RiskStatusRow.user_id)
            .where(RiskStatusRow.user_id.in_(soldier_ids))
        ).all()
        counts: dict[str, int] = {}
        for status, _ in risk_rows:
            counts[status] = counts.get(status, 0) + 1
        assert counts.get("green") == seed_demo_unit.SOLDIERS_PER_BUCKET
        assert counts.get("yellow") == seed_demo_unit.SOLDIERS_PER_BUCKET
        assert counts.get("red") == seed_demo_unit.SOLDIERS_PER_BUCKET

        # Commander + psychologist exist and are tied to the unit.
        commander_email = f"commander@{seed_demo_unit.DEMO_DOMAIN}"
        medic_email = f"medic@{seed_demo_unit.DEMO_DOMAIN}"
        commander = db.execute(
            select(User).where(User.email == commander_email)
        ).scalar_one()
        medic = db.execute(
            select(User).where(User.email == medic_email)
        ).scalar_one()
        assert commander.unit_id == unit.id
        assert medic.unit_id == unit.id

        # Risk Engine should have opened cases for the red soldiers.
        case_count = db.execute(
            select(CaseReview)
            .join(User, User.id == CaseReview.user_id)
            .where(User.unit_id == unit.id)
        ).scalars().all()
        assert len(case_count) >= seed_demo_unit.SOLDIERS_PER_BUCKET


def test_seed_demo_unit_is_idempotent() -> None:
    assert seed_demo_unit.main([]) == 0
    # Second run without --reset-demo-data must bail without crashing.
    assert seed_demo_unit.main([]) == 1
