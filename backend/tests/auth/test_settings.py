"""Settings — in-session password change and profile (full_name) update.

Covers EPIC-84 (TASK-8401, TASK-8402) per the UX appendix backlog.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from app.models.user_session import UserSession
from tests.factories import issue_invite_for, make_user


GOOD_PASSWORD = "correct horse battery staple"
NEW_PASSWORD = "another strong passphrase 9001"


def _accept(client: TestClient, token: str, password: str = GOOD_PASSWORD) -> None:
    client.post(
        "/api/v1/auth/invite/accept",
        json={"token": token, "password": password},
    )


# --- Password change --------------------------------------------------------


def test_password_change_with_correct_current_succeeds(client: TestClient) -> None:
    user = make_user(email="pwc1@example.com", roles=("soldier",))
    _accept(client, issue_invite_for(user.id))

    res = client.post(
        "/api/v1/auth/password/change",
        json={"current_password": GOOD_PASSWORD, "new_password": NEW_PASSWORD},
    )
    body = res.json()
    assert res.status_code == 200, body
    assert body["data"]["changed"] is True

    # Current session is preserved.
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200

    # Old password no longer works on a fresh client; new one does.
    second = TestClient(client.app)
    bad = second.post(
        "/api/v1/auth/login",
        json={"email": "pwc1@example.com", "password": GOOD_PASSWORD},
    )
    assert bad.json()["error"]["code"] == "UNAUTHORIZED"
    good = second.post(
        "/api/v1/auth/login",
        json={"email": "pwc1@example.com", "password": NEW_PASSWORD},
    )
    assert good.status_code == 200
    assert good.json()["data"]["logged_in"] is True


def test_password_change_with_wrong_current_returns_unauthorized(client: TestClient) -> None:
    user = make_user(email="pwc2@example.com", roles=("soldier",))
    _accept(client, issue_invite_for(user.id))

    res = client.post(
        "/api/v1/auth/password/change",
        json={"current_password": "this is not it", "new_password": NEW_PASSWORD},
    )
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_password_change_rejects_weak_new_password(client: TestClient) -> None:
    user = make_user(email="pwc3@example.com", roles=("soldier",))
    _accept(client, issue_invite_for(user.id))

    res = client.post(
        "/api/v1/auth/password/change",
        json={"current_password": GOOD_PASSWORD, "new_password": "short"},
    )
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "WEAK_PASSWORD"


def test_password_change_requires_authentication(client: TestClient) -> None:
    res = client.post(
        "/api/v1/auth/password/change",
        json={"current_password": GOOD_PASSWORD, "new_password": NEW_PASSWORD},
    )
    assert res.status_code == 401


def test_password_change_revokes_other_sessions_keeps_current(client: TestClient) -> None:
    user = make_user(email="pwc4@example.com", roles=("soldier",))
    _accept(client, issue_invite_for(user.id))

    # Create a second active session via a separate client (login on different
    # device).
    other = TestClient(client.app)
    other.post(
        "/api/v1/auth/login",
        json={"email": "pwc4@example.com", "password": GOOD_PASSWORD},
    )
    assert other.get("/api/v1/auth/me").status_code == 200

    res = client.post(
        "/api/v1/auth/password/change",
        json={"current_password": GOOD_PASSWORD, "new_password": NEW_PASSWORD},
    )
    assert res.status_code == 200

    # Current session: still alive.
    assert client.get("/api/v1/auth/me").status_code == 200
    # Other device: revoked.
    assert other.get("/api/v1/auth/me").status_code == 401

    with SessionLocal() as db:
        active = db.execute(
            select(UserSession).where(
                UserSession.user_id == user.id,
                UserSession.status == "active",
            )
        ).scalars().all()
        assert len(active) == 1


def test_password_change_writes_audit_event(client: TestClient) -> None:
    user = make_user(email="pwc5@example.com", roles=("soldier",))
    _accept(client, issue_invite_for(user.id))

    client.post(
        "/api/v1/auth/password/change",
        json={"current_password": GOOD_PASSWORD, "new_password": NEW_PASSWORD},
    )

    with SessionLocal() as db:
        rows = db.execute(
            select(AuditLog).where(AuditLog.event_type == "password_changed")
        ).scalars().all()
        assert len(rows) == 1
        assert rows[0].target_user_id == user.id


# --- Profile update ---------------------------------------------------------


def test_profile_update_changes_full_name(client: TestClient) -> None:
    user = make_user(email="pf1@example.com", full_name="Old Name", roles=("soldier",))
    _accept(client, issue_invite_for(user.id))

    res = client.patch("/api/v1/auth/me", json={"full_name": "New Name"})
    body = res.json()
    assert res.status_code == 200, body
    assert body["data"]["user"]["full_name"] == "New Name"

    me = client.get("/api/v1/auth/me").json()
    assert me["data"]["user"]["full_name"] == "New Name"


def test_profile_update_trims_whitespace(client: TestClient) -> None:
    user = make_user(email="pf2@example.com", full_name="Old", roles=("soldier",))
    _accept(client, issue_invite_for(user.id))

    res = client.patch("/api/v1/auth/me", json={"full_name": "   Trimmed Name   "})
    body = res.json()
    assert res.status_code == 200, body
    assert body["data"]["user"]["full_name"] == "Trimmed Name"


def test_profile_update_rejects_blank_after_trim(client: TestClient) -> None:
    user = make_user(email="pf3@example.com", roles=("soldier",))
    _accept(client, issue_invite_for(user.id))

    # Pydantic min_length=1 already rejects empty string at the schema layer.
    res = client.patch("/api/v1/auth/me", json={"full_name": ""})
    assert res.status_code == 422


def test_profile_update_rejects_whitespace_only(client: TestClient) -> None:
    user = make_user(email="pf4@example.com", roles=("soldier",))
    _accept(client, issue_invite_for(user.id))

    # All-whitespace passes Pydantic min_length=1 but the service layer must
    # reject it with INVALID_PROFILE.
    res = client.patch("/api/v1/auth/me", json={"full_name": "    "})
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "INVALID_PROFILE"


def test_profile_update_requires_authentication(client: TestClient) -> None:
    res = client.patch("/api/v1/auth/me", json={"full_name": "Anonymous"})
    assert res.status_code == 401


def test_profile_update_writes_audit_event(client: TestClient) -> None:
    user = make_user(email="pf5@example.com", roles=("soldier",))
    _accept(client, issue_invite_for(user.id))

    client.patch("/api/v1/auth/me", json={"full_name": "Renamed"})

    with SessionLocal() as db:
        rows = db.execute(
            select(AuditLog).where(AuditLog.event_type == "profile_updated")
        ).scalars().all()
        assert len(rows) == 1
        assert rows[0].target_user_id == user.id


def test_profile_update_idempotent_when_unchanged(client: TestClient) -> None:
    user = make_user(email="pf6@example.com", full_name="Same", roles=("soldier",))
    _accept(client, issue_invite_for(user.id))

    client.patch("/api/v1/auth/me", json={"full_name": "Same"})

    with SessionLocal() as db:
        rows = db.execute(
            select(AuditLog).where(AuditLog.event_type == "profile_updated")
        ).scalars().all()
        # No change → no audit event written.
        assert len(rows) == 0
