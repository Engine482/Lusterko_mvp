"""Lightweight DB factories for tests.

Keep them deterministic — no Faker — so failures are easy to read.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from app.core.constants import Role
from app.db.session import SessionLocal
from app.models.unit import Unit
from app.models.user import User
from app.models.user_role import UserRole
from app.modules.auth import service as auth_service


def make_unit(name: str = "Unit Alpha") -> Unit:
    with SessionLocal() as db:
        unit = Unit(name=name, is_active=True)
        db.add(unit)
        db.commit()
        db.refresh(unit)
    return unit


def make_user(
    *,
    email: str,
    full_name: str = "Test User",
    roles: Sequence[Role] = ("soldier",),
    unit_id: uuid.UUID | None = None,
    status: str = "active",
) -> User:
    with SessionLocal() as db:
        user = User(full_name=full_name, email=email, unit_id=unit_id, status=status)
        db.add(user)
        db.flush()
        for role in roles:
            db.add(UserRole(user_id=user.id, role=role))
        db.commit()
        db.refresh(user)
    return user


def issue_invite_for(user_id: uuid.UUID) -> str:
    """Return the plaintext invite token (only available at creation time)."""

    with SessionLocal() as db:
        issued = auth_service.issue_invite(db, user_id=user_id, created_by_user_id=None)
        db.commit()
        return issued.token
