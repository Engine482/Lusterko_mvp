"""Auth integration tests covering Test Scenarios T-AUTH-001..008."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from app.models.auth_invite import AuthInvite
from tests.factories import issue_invite_for, make_unit, make_user


def _login_via_dev_stub(client: TestClient, invite_token: str) -> None:
    start = client.get(f"/api/v1/auth/google/start?invite_token={invite_token}")
    assert start.status_code == 200, start.text
    body = start.json()
    assert body["success"] is True
    redirect = body["data"]["redirect_url"]
    assert "dev_stub=1" in redirect
    callback = client.get(
        "/api/v1/auth/google/callback",
        params={"state": invite_token, "dev_stub": 1},
    )
    assert callback.status_code == 200, callback.text


def test_t_auth_001_valid_invite_login(client: TestClient) -> None:
    unit = make_unit()
    user = make_user(email="user001@example.com", roles=("soldier",), unit_id=unit.id)
    invite_token = issue_invite_for(user.id)

    _login_via_dev_stub(client, invite_token)

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    payload = me.json()["data"]
    assert payload["user"]["email"] == "user001@example.com"
    assert payload["roles"] == ["soldier"]
    assert payload["active_role"] == "soldier"
    assert payload["role_selection_required"] is False

    with SessionLocal() as db:
        events = db.execute(select(AuditLog.event_type).order_by(AuditLog.created_at)).scalars().all()
    assert "invite_used" in events
    assert "login_success" in events


def test_t_auth_002_expired_invite_rejected(client: TestClient) -> None:
    unit = make_unit("Unit B")
    user = make_user(email="user002@example.com", unit_id=unit.id)
    invite_token = issue_invite_for(user.id)

    # Force-expire the invite.
    with SessionLocal() as db:
        invite = db.execute(select(AuthInvite).where(AuthInvite.user_id == user.id)).scalar_one()
        invite.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()

    res = client.get(f"/api/v1/auth/google/start?invite_token={invite_token}")
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "INVITE_EXPIRED"


def test_t_auth_003_invite_cannot_be_reused(client: TestClient) -> None:
    user = make_user(email="user003@example.com")
    invite_token = issue_invite_for(user.id)

    _login_via_dev_stub(client, invite_token)

    second = client.get(
        "/api/v1/auth/google/callback",
        params={"state": invite_token, "dev_stub": 1},
    )
    body = second.json()
    assert body["success"] is False
    assert body["error"]["code"] == "INVALID_INVITE"


def test_t_auth_004_inactive_user_blocked(client: TestClient) -> None:
    user = make_user(email="user004@example.com", status="inactive")
    invite_token = issue_invite_for(user.id)

    res = client.get(
        "/api/v1/auth/google/callback",
        params={"state": invite_token, "dev_stub": 1},
    )
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_t_auth_005_single_role_auto_enters(client: TestClient) -> None:
    user = make_user(email="user005@example.com", roles=("commander",))
    token = issue_invite_for(user.id)
    _login_via_dev_stub(client, token)
    me = client.get("/api/v1/auth/me").json()["data"]
    assert me["active_role"] == "commander"
    assert me["role_selection_required"] is False


def test_t_auth_006_multi_role_forced_to_choose(client: TestClient) -> None:
    user = make_user(email="user006@example.com", roles=("commander", "medic_psych"))
    token = issue_invite_for(user.id)
    _login_via_dev_stub(client, token)
    me = client.get("/api/v1/auth/me").json()["data"]
    assert me["role_selection_required"] is True
    assert me["active_role"] is None

    # Until the role is selected, role-scoped admin endpoint must refuse.
    blocked = client.get("/api/v1/admin/users")
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "ROLE_SELECTION_REQUIRED"

    sel = client.post("/api/v1/auth/select-role", json={"role": "commander"})
    assert sel.status_code == 200
    me2 = client.get("/api/v1/auth/me").json()["data"]
    assert me2["active_role"] == "commander"
    assert me2["role_selection_required"] is False


def test_t_auth_007_role_switch_audited(client: TestClient) -> None:
    user = make_user(email="user007@example.com", roles=("commander", "medic_psych"))
    token = issue_invite_for(user.id)
    _login_via_dev_stub(client, token)

    client.post("/api/v1/auth/select-role", json={"role": "commander"})
    client.post("/api/v1/auth/select-role", json={"role": "medic_psych"})
    me = client.get("/api/v1/auth/me").json()["data"]
    assert me["active_role"] == "medic_psych"

    with SessionLocal() as db:
        events = (
            db.execute(select(AuditLog.event_type).order_by(AuditLog.created_at)).scalars().all()
        )
    assert "role_switched" in events


def test_t_auth_008_role_not_assigned_rejected(client: TestClient) -> None:
    user = make_user(email="user008@example.com", roles=("soldier",))
    token = issue_invite_for(user.id)
    _login_via_dev_stub(client, token)

    res = client.post("/api/v1/auth/select-role", json={"role": "admin"})
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "INVALID_ACTIVE_ROLE"


def test_logout_invalidates_session(client: TestClient) -> None:
    user = make_user(email="logout@example.com", roles=("soldier",))
    token = issue_invite_for(user.id)
    _login_via_dev_stub(client, token)

    out = client.post("/api/v1/auth/logout")
    assert out.status_code == 200
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 401
    assert me.json()["error"]["code"] == "UNAUTHORIZED"
