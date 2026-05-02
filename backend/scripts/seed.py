"""Bootstrap seed: minimal unit + admin user + first-login invite.

Idempotent. Run after `make db-migrate`. Used in Sprint 1 (Backlog TASK-0601)
to give the demo a starting admin account, and in Sprint 6 (TASK-6501..6502)
to bootstrap the pilot admin with multiple roles.

Usage:
    DATABASE_URL=... ADMIN_EMAIL=admin@example.com python -m scripts.seed

    # Pilot bootstrap with a multi-role admin:
    DATABASE_URL=... \
    ADMIN_EMAIL=motorny.v@gmail.com \
    BOOTSTRAP_USER_ROLES=admin,soldier,commander,medic_psych \
    SEED_UNIT_NAME="Тестовий підрозділ" \
    python -m scripts.seed
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.constants import Role
from app.db.session import SessionLocal
from app.models.unit import Unit
from app.models.user import User
from app.models.user_role import UserRole
from app.modules.auth import service as auth_service


_VALID_ROLES: set[Role] = {"soldier", "commander", "medic_psych", "admin"}


def _parse_roles(raw: str) -> list[Role]:
    """Accept CSV like `admin,soldier,commander,medic_psych`. The shorthand
    `medic` maps to `medic_psych` so the env var stays human-readable."""

    parts = [p.strip() for p in raw.split(",") if p.strip()]
    aliases = {"medic": "medic_psych"}
    resolved: list[Role] = []
    for p in parts:
        canonical = aliases.get(p, p)
        if canonical not in _VALID_ROLES:
            raise SystemExit(
                f"Invalid role '{p}' in BOOTSTRAP_USER_ROLES. "
                f"Valid roles: {sorted(_VALID_ROLES)} (alias: medic→medic_psych)."
            )
        if canonical not in resolved:
            resolved.append(canonical)  # type: ignore[arg-type]
    if not resolved:
        raise SystemExit("BOOTSTRAP_USER_ROLES must contain at least one role.")
    return resolved


def main() -> int:
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@lusterko.local")
    admin_full_name = os.environ.get("ADMIN_FULL_NAME", "Lusterko Admin")
    unit_name = os.environ.get("SEED_UNIT_NAME", "Демо підрозділ")
    raw_roles = os.environ.get("BOOTSTRAP_USER_ROLES", "admin")
    desired_roles = _parse_roles(raw_roles)

    with SessionLocal() as db:
        unit = db.execute(select(Unit).where(Unit.name == unit_name)).scalar_one_or_none()
        if unit is None:
            unit = Unit(name=unit_name, is_active=True)
            db.add(unit)
            db.flush()

        admin = db.execute(select(User).where(User.email == admin_email)).scalar_one_or_none()
        if admin is None:
            admin = User(
                full_name=admin_full_name,
                email=admin_email,
                unit_id=unit.id,
                status="active",
            )
            db.add(admin)
            db.flush()

        existing_roles = set(
            db.execute(
                select(UserRole.role).where(UserRole.user_id == admin.id)
            ).scalars()
        )
        for role in desired_roles:
            if role not in existing_roles:
                db.add(UserRole(user_id=admin.id, role=role))

        # Create a fresh invite for first login (system-actor: None).
        issued = auth_service.issue_invite(db, user_id=admin.id, created_by_user_id=None)
        db.commit()

        print("Seed OK:")
        print(f"  unit_id     = {unit.id}")
        print(f"  admin_id    = {admin.id}")
        print(f"  admin_email = {admin.email}")
        print(f"  roles       = {','.join(desired_roles)}")
        print(f"  invite_token = {issued.token}")
        print(f"  invite_expires_at = {issued.invite.expires_at.isoformat()}")
    return 0


if __name__ == "__main__":
    _ = uuid.uuid4()  # ensure uuid module imported
    _ = datetime.now(timezone.utc)
    sys.exit(main())
