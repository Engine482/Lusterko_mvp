"""Brute-force protection tests (TASK-7503 + EPIC-72).

Covers: 5-fail threshold trips lock, lock TTL behaviour, success resets the
counter, exponential backoff cycle, and ACCOUNT_LOCKED on /login,
/password/forgot, /password/reset, /invite/accept.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from app.models.auth_lockout import AuthLockout
from app.modules.auth import rate_limit as rl
from tests.factories import issue_invite_for, login_as, make_user


GOOD_PASSWORD = "test-password-1234"


def _force_unlock(key: str) -> None:
    """Move locked_until into the past so the next call is unlocked,
    without sleeping in tests."""

    with SessionLocal() as db:
        row = db.execute(
            select(AuthLockout).where(AuthLockout.key == key)
        ).scalar_one()
        row.locked_until = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()


def test_login_locks_after_threshold(client: TestClient) -> None:
    user = make_user(email="lock@example.com", roles=("soldier",))
    login_as(client, user)
    client.post("/api/v1/auth/logout")

    for _ in range(rl.FAILURE_THRESHOLD):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "lock@example.com", "password": "wrong-very-wrong-1"},
        )
        assert res.json()["error"]["code"] == "UNAUTHORIZED"

    locked = client.post(
        "/api/v1/auth/login",
        json={"email": "lock@example.com", "password": "wrong-very-wrong-1"},
    )
    assert locked.status_code == 429
    assert locked.json()["error"]["code"] == "ACCOUNT_LOCKED"

    locked_correct = client.post(
        "/api/v1/auth/login",
        json={"email": "lock@example.com", "password": GOOD_PASSWORD},
    )
    assert locked_correct.json()["error"]["code"] == "ACCOUNT_LOCKED"

    with SessionLocal() as db:
        events = db.execute(select(AuditLog.event_type)).scalars().all()
    assert "account_locked" in events


def test_login_unlock_after_ttl_expires(client: TestClient) -> None:
    user = make_user(email="ttl@example.com", roles=("soldier",))
    login_as(client, user)
    client.post("/api/v1/auth/logout")

    for _ in range(rl.FAILURE_THRESHOLD):
        client.post(
            "/api/v1/auth/login",
            json={"email": "ttl@example.com", "password": "wrong-very-wrong-1"},
        )

    key = rl.login_key(ip=None, email="ttl@example.com")
    _force_unlock(key)

    ok = client.post(
        "/api/v1/auth/login",
        json={"email": "ttl@example.com", "password": GOOD_PASSWORD},
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["data"]["logged_in"] is True


def test_successful_login_resets_failure_counter(client: TestClient) -> None:
    user = make_user(email="reset@example.com", roles=("soldier",))
    login_as(client, user)
    client.post("/api/v1/auth/logout")

    for _ in range(rl.FAILURE_THRESHOLD - 1):
        client.post(
            "/api/v1/auth/login",
            json={"email": "reset@example.com", "password": "wrong"},
        )

    ok = client.post(
        "/api/v1/auth/login",
        json={"email": "reset@example.com", "password": GOOD_PASSWORD},
    )
    assert ok.status_code == 200

    key = rl.login_key(ip=None, email="reset@example.com")
    with SessionLocal() as db:
        row = db.execute(
            select(AuthLockout).where(AuthLockout.key == key)
        ).scalar_one_or_none()
    assert row is None

    client.post("/api/v1/auth/logout")
    client.post(
        "/api/v1/auth/login",
        json={"email": "reset@example.com", "password": "wrong"},
    )
    with SessionLocal() as db:
        row = db.execute(
            select(AuthLockout).where(AuthLockout.key == key)
        ).scalar_one()
    assert row.failed_count == 1
    assert row.locked_until is None


def test_lock_window_doubles_each_cycle(client: TestClient) -> None:
    user = make_user(email="cycle@example.com", roles=("soldier",))
    login_as(client, user)
    client.post("/api/v1/auth/logout")

    key = rl.login_key(ip=None, email="cycle@example.com")

    for _ in range(rl.FAILURE_THRESHOLD):
        client.post(
            "/api/v1/auth/login",
            json={"email": "cycle@example.com", "password": "x"},
        )
    with SessionLocal() as db:
        row = db.execute(
            select(AuthLockout).where(AuthLockout.key == key)
        ).scalar_one()
        assert row.locked_until is not None
        first_window = (row.locked_until - row.last_failure_at).total_seconds()
        assert row.cycle == 1
    _force_unlock(key)

    for _ in range(rl.FAILURE_THRESHOLD):
        client.post(
            "/api/v1/auth/login",
            json={"email": "cycle@example.com", "password": "x"},
        )
    with SessionLocal() as db:
        row = db.execute(
            select(AuthLockout).where(AuthLockout.key == key)
        ).scalar_one()
        assert row.locked_until is not None
        second_window = (row.locked_until - row.last_failure_at).total_seconds()
        assert row.cycle == 2

    assert second_window == first_window * 2


def test_failures_outside_window_reset_streak() -> None:
    """Direct service-level test: failures > 15 min apart don't accumulate."""

    key = "login:127.0.0.1:stale@example.com"
    with SessionLocal() as db:
        long_ago = datetime.now(timezone.utc) - rl.WINDOW - timedelta(seconds=10)
        row = AuthLockout(
            key=key,
            failed_count=4,
            cycle=0,
            last_failure_at=long_ago,
            updated_at=long_ago,
        )
        db.add(row)
        db.commit()

        rl.record_failure(db, key=key)
        db.commit()
        refreshed = db.execute(
            select(AuthLockout).where(AuthLockout.key == key)
        ).scalar_one()
        assert refreshed.failed_count == 1
        assert refreshed.locked_until is None


def test_password_forgot_is_rate_limited(client: TestClient) -> None:
    user = make_user(email="spam@example.com", roles=("soldier",))
    login_as(client, user)
    client.post("/api/v1/auth/logout")

    for _ in range(rl.FAILURE_THRESHOLD + 3):
        res = client.post(
            "/api/v1/auth/password/forgot",
            json={"email": "spam@example.com"},
        )
        assert res.status_code == 200
        assert res.json()["data"]["queued"] is True

    key = rl.password_forgot_key(ip=None, email="spam@example.com")
    with SessionLocal() as db:
        row = db.execute(
            select(AuthLockout).where(AuthLockout.key == key)
        ).scalar_one()
    assert row.locked_until is not None
    assert row.cycle >= 1


def test_password_reset_locks_on_repeated_invalid_token(client: TestClient) -> None:
    for _ in range(rl.FAILURE_THRESHOLD):
        res = client.post(
            "/api/v1/auth/password/reset",
            json={
                "token": "totally-bogus-token-but-long-enough",
                "password": GOOD_PASSWORD,
            },
        )
        assert res.json()["error"]["code"] == "INVALID_RESET_TOKEN"

    locked = client.post(
        "/api/v1/auth/password/reset",
        json={
            "token": "totally-bogus-token-but-long-enough",
            "password": GOOD_PASSWORD,
        },
    )
    assert locked.status_code == 429
    assert locked.json()["error"]["code"] == "ACCOUNT_LOCKED"


def test_invite_accept_locks_on_repeated_invalid_token(client: TestClient) -> None:
    for _ in range(rl.FAILURE_THRESHOLD):
        res = client.post(
            "/api/v1/auth/invite/accept",
            json={
                "token": "totally-bogus-token-but-long-enough",
                "password": GOOD_PASSWORD,
            },
        )
        assert res.json()["error"]["code"] == "INVALID_INVITE"

    locked = client.post(
        "/api/v1/auth/invite/accept",
        json={
            "token": "totally-bogus-token-but-long-enough",
            "password": GOOD_PASSWORD,
        },
    )
    assert locked.status_code == 429
    assert locked.json()["error"]["code"] == "ACCOUNT_LOCKED"


def test_weak_password_does_not_count_toward_lockout(client: TestClient) -> None:
    """A valid invite + a too-short password must not increment the
    failure counter — that would let users lock themselves out by
    fat-fingering."""

    user = make_user(email="weak@example.com", roles=("soldier",))
    token = issue_invite_for(user.id)

    for _ in range(rl.FAILURE_THRESHOLD + 2):
        res = client.post(
            "/api/v1/auth/invite/accept",
            json={"token": token, "password": "short"},
        )
        assert res.json()["error"]["code"] == "WEAK_PASSWORD"

    ok = client.post(
        "/api/v1/auth/invite/accept",
        json={"token": token, "password": GOOD_PASSWORD},
    )
    assert ok.status_code == 200, ok.text
