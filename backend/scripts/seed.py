"""Bootstrap seed: minimal unit + admin user + first-login invite.

Idempotent. Run after `make db-migrate`. Used in Sprint 1 (Backlog TASK-0601)
to give the demo a starting admin account.

Usage:
    DATABASE_URL=... ADMIN_EMAIL=admin@example.com python -m scripts.seed
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.unit import Unit
from app.models.user import User
from app.models.user_role import UserRole
from app.modules.auth import service as auth_service


def main() -> int:
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@lusterko.local")
    admin_full_name = os.environ.get("ADMIN_FULL_NAME", "Lusterko Admin")
    unit_name = os.environ.get("SEED_UNIT_NAME", "Демо підрозділ")

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

        if (
            db.execute(
                select(UserRole).where(UserRole.user_id == admin.id, UserRole.role == "admin")
            ).scalar_one_or_none()
            is None
        ):
            db.add(UserRole(user_id=admin.id, role="admin"))

        # Create a fresh invite for first login (system-actor: None).
        issued = auth_service.issue_invite(db, user_id=admin.id, created_by_user_id=None)
        db.commit()

        print("Seed OK:")
        print(f"  unit_id     = {unit.id}")
        print(f"  admin_id    = {admin.id}")
        print(f"  admin_email = {admin.email}")
        print(f"  invite_token = {issued.token}")
        print(f"  invite_expires_at = {issued.invite.expires_at.isoformat()}")
    return 0


if __name__ == "__main__":
    _ = uuid.uuid4()  # ensure uuid module imported
    _ = datetime.now(timezone.utc)
    sys.exit(main())
