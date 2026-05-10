"""Brute-force protection for auth endpoints.

Sprint 7 EPIC-72. The rule (`docs/06_decisions/2026-05-02-auth-email-password.md`):

- 5 consecutive failures within a 15-minute window → lock the key for
  5 minutes; each subsequent lock cycle doubles the lock window
  (5, 10, 20, 40, ...). Cycle resets after a successful authentication.
- The "key" encodes endpoint + identifying coordinate (IP+email or just
  IP) so each surface has its own counter and cannot DoS another.
- A failed attempt outside the 15-minute sliding window resets the
  consecutive counter — honest fat-fingered users do not get locked out
  by stale failures from days ago.
- A successful auth deletes the row entirely (clean slate).

We keep one mutable row per key (not an immutable attempt log) so the
table stays tiny and inserts/updates are predictable.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.auth_lockout import AuthLockout
from app.modules.auth.service import AuthError
from app.services.audit_logger import log_event


# Tuned for the pilot — small constants live next to the only file that
# uses them.
FAILURE_THRESHOLD = 5
WINDOW = timedelta(minutes=15)
BASE_LOCK = timedelta(minutes=5)


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(timezone.utc)


def check_lockout(
    db: Session, *, key: str, now: datetime | None = None,
) -> None:
    """Raise `AuthError("ACCOUNT_LOCKED")` if the key is currently locked.

    Cheap read; no row creation. Called at the very top of every protected
    endpoint, before any password hashing or DB writes."""

    cur = _now(now)
    row = db.execute(
        select(AuthLockout).where(AuthLockout.key == key)
    ).scalar_one_or_none()
    if row is None or row.locked_until is None:
        return
    if row.locked_until > cur:
        retry_after = int((row.locked_until - cur).total_seconds())
        raise AuthError(
            "ACCOUNT_LOCKED",
            f"Too many failed attempts. Try again in {retry_after} seconds.",
        )


def record_failure(
    db: Session,
    *,
    key: str,
    target_user_id: object | None = None,
    ip_address: str | None = None,
    now: datetime | None = None,
) -> None:
    """Increment failure counter; lock the key when the threshold is hit."""

    cur = _now(now)
    row = db.execute(
        select(AuthLockout).where(AuthLockout.key == key)
    ).scalar_one_or_none()

    if row is None:
        row = AuthLockout(
            key=key,
            failed_count=1,
            cycle=0,
            locked_until=None,
            last_failure_at=cur,
            updated_at=cur,
        )
        db.add(row)
        db.flush()
        return

    # Stale streak: reset to 1 if the previous failure is outside the window.
    if cur - row.last_failure_at > WINDOW:
        row.failed_count = 1
    else:
        row.failed_count += 1
    row.last_failure_at = cur
    row.updated_at = cur

    if row.failed_count >= FAILURE_THRESHOLD:
        # Exponential backoff: 5, 10, 20, 40, ... minutes. Cap at 24h so a
        # forgotten attacker doesn't lock a real user out of recovery
        # forever.
        lock_seconds = int(BASE_LOCK.total_seconds()) * (2 ** row.cycle)
        lock_seconds = min(lock_seconds, 24 * 60 * 60)
        row.locked_until = cur + timedelta(seconds=lock_seconds)
        row.cycle += 1
        row.failed_count = 0
        log_event(
            db,
            event_type="account_locked",
            target_user_id=target_user_id,  # type: ignore[arg-type]
            entity_type="auth_lockouts",
            entity_id=row.id,
            ip_address=ip_address,
            metadata={"key": key, "lock_seconds": lock_seconds},
        )


def record_success(db: Session, *, key: str) -> None:
    """A successful auth wipes the failure state for this key."""

    row = db.execute(
        select(AuthLockout).where(AuthLockout.key == key)
    ).scalar_one_or_none()
    if row is not None:
        db.delete(row)


# --- Key constructors --------------------------------------------------------
#
# Stable, narrow keys per endpoint. We deliberately bound by (IP, email) on
# /login and /password/forgot so an attacker on one IP cannot lock out the
# legitimate user on another IP.


def login_key(*, ip: str | None, email: str) -> str:
    return f"login:{ip or 'unknown'}:{email.lower()}"


def invite_accept_key(*, ip: str | None) -> str:
    return f"invite:{ip or 'unknown'}"


def password_forgot_key(*, ip: str | None, email: str) -> str:
    return f"forgot:{ip or 'unknown'}:{email.lower()}"


def password_reset_key(*, ip: str | None) -> str:
    return f"reset:{ip or 'unknown'}"


def demo_register_start_key(*, ip: str | None, email: str) -> str:
    return f"demoreg-start:{ip or 'unknown'}:{email.lower()}"


def demo_register_confirm_key(*, ip: str | None) -> str:
    return f"demoreg-confirm:{ip or 'unknown'}"
