"""Bootstrap seed: minimal unit + admin user + (optional) password or invite.

Idempotent. Run after `make db-migrate`.

Two modes, picked by env:

- **BOOTSTRAP_ADMIN_PASSWORD set** — admin gets the password set directly
  (argon2id-hashed). No invite is issued. Use for prod bootstrap when you
  control the password and want to log in immediately. The variable must
  satisfy the length policy (>=12 chars) — the seed will refuse otherwise.
- **BOOTSTRAP_ADMIN_PASSWORD unset** — admin row is created with password_hash
  NULL and a fresh first-login invite is issued. The token is printed; admin
  follows the invite flow to set their password via the UI.

Usage:
    DATABASE_URL=... ADMIN_EMAIL=admin@example.com python -m scripts.seed

    # Pilot bootstrap with a multi-role admin and a known password:
    DATABASE_URL=... \
    ADMIN_EMAIL=motorny.v@gmail.com \
    BOOTSTRAP_USER_ROLES=admin,soldier,commander,medic_psych \
    BOOTSTRAP_ADMIN_PASSWORD='paste-strong-password-here' \
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
from app.core.security import PasswordPolicyError, hash_password
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
    bootstrap_password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD")

    # Validate password early (before any DB writes) so the user gets a
    # clean error message and the script stays idempotent.
    password_hash_value: str | None = None
    if bootstrap_password:
        try:
            password_hash_value = hash_password(bootstrap_password)
        except PasswordPolicyError as err:
            raise SystemExit(f"BOOTSTRAP_ADMIN_PASSWORD invalid: {err}") from err

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

        issued_token: str | None = None
        invite_expires_iso: str | None = None
        if password_hash_value is not None:
            # Password mode: set hash, no invite. Re-runs overwrite the
            # hash so an operator can rotate by re-running with a new
            # BOOTSTRAP_ADMIN_PASSWORD.
            admin.password_hash = password_hash_value
        else:
            # Invite mode: create a fresh first-login invite. Existing
            # pending invites for the same user are revoked by the service.
            issued = auth_service.issue_invite(
                db, user_id=admin.id, created_by_user_id=None
            )
            issued_token = issued.token
            invite_expires_iso = issued.invite.expires_at.isoformat()

        db.commit()

        print("Seed OK:")
        print(f"  unit_id     = {unit.id}")
        print(f"  admin_id    = {admin.id}")
        print(f"  admin_email = {admin.email}")
        print(f"  roles       = {','.join(desired_roles)}")
        if password_hash_value is not None:
            print("  bootstrap_mode = password (hash set; no invite issued)")
        else:
            print(f"  invite_token = {issued_token}")
            print(f"  invite_expires_at = {invite_expires_iso}")
    return 0


if __name__ == "__main__":
    _ = uuid.uuid4()  # ensure uuid module imported
    _ = datetime.now(timezone.utc)
    sys.exit(main())
