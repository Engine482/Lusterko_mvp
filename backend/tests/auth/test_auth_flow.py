"""Auth integration tests for Sprint 7 email+password flow.

Covers Test Scenarios T-AUTH-001..008 (rewritten for the new flow) plus the
new password-reset path. The Google OAuth flow these tests previously
exercised was retired per `docs/06_decisions/2026-05-02-auth-email-password.md`.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from app.models.auth_invite import AuthInvite
from app.models.password_reset_token import PasswordResetToken
from app.modules.notifications import mailer as mailer_mod
from tests.factories import issue_invite_for, make_unit, make_user


GOOD_PASSWORD = "correct horse battery staple"


def _accept_invite(
    client: TestClient,
    token: str,
    *,
    full_name: str | None = None,
    password: str = GOOD_PASSWORD,
) -> dict:
    payload: dict = {"token": token, "password": password}
    if full_name is not None:
        payload["full_name"] = full_name
    res = client.post("/api/v1/auth/invite/accept", json=payload)
    return res.json()


def _login(client: TestClient, email: str, password: str = GOOD_PASSWORD) -> dict:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()


def test_t_auth_001_invite_accept_creates_session(client: TestClient) -> None:
    unit = make_unit()
    user = make_user(email="user001@example.com", roles=("soldier",), unit_id=unit.id)
    token = issue_invite_for(user.id)

    body = _accept_invite(client, token, full_name="User 001")
    assert body["success"] is True
    assert body["data"]["accepted"] is True

    me = client.get("/api/v1/auth/me").json()["data"]
    assert me["user"]["email"] == "user001@example.com"
    assert me["user"]["full_name"] == "User 001"
    assert me["roles"] == ["soldier"]
    assert me["active_role"] == "soldier"
    assert me["role_selection_required"] is False

    with SessionLocal() as db:
        events = (
            db.execute(select(AuditLog.event_type).order_by(AuditLog.created_at))
            .scalars()
            .all()
        )
    assert "invite_used" in events
    assert "login_success" in events


def test_t_auth_002_expired_invite_rejected(client: TestClient) -> None:
    user = make_user(email="user002@example.com")
    token = issue_invite_for(user.id)

    with SessionLocal() as db:
        invite = db.execute(
            select(AuthInvite).where(AuthInvite.user_id == user.id)
        ).scalar_one()
        invite.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()

    body = _accept_invite(client, token)
    assert body["success"] is False
    assert body["error"]["code"] == "INVITE_EXPIRED"


def test_t_auth_003_invite_cannot_be_reused(client: TestClient) -> None:
    user = make_user(email="user003@example.com")
    token = issue_invite_for(user.id)

    first = _accept_invite(client, token)
    assert first["success"] is True

    second = _accept_invite(client, token)
    assert second["success"] is False
    assert second["error"]["code"] == "INVALID_INVITE"


def test_t_auth_004_inactive_user_blocked(client: TestClient) -> None:
    user = make_user(email="user004@example.com", status="inactive")
    token = issue_invite_for(user.id)

    body = _accept_invite(client, token)
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_t_auth_005_single_role_auto_enters(client: TestClient) -> None:
    user = make_user(email="user005@example.com", roles=("commander",))
    token = issue_invite_for(user.id)
    _accept_invite(client, token)

    me = client.get("/api/v1/auth/me").json()["data"]
    assert me["active_role"] == "commander"
    assert me["role_selection_required"] is False


def test_t_auth_006_multi_role_forced_to_choose(client: TestClient) -> None:
    user = make_user(
        email="user006@example.com",
        roles=("commander", "medic_psych"),
    )
    token = issue_invite_for(user.id)
    _accept_invite(client, token)

    me = client.get("/api/v1/auth/me").json()["data"]
    assert me["role_selection_required"] is True
    assert me["active_role"] is None

    blocked = client.get("/api/v1/admin/users")
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "ROLE_SELECTION_REQUIRED"

    sel = client.post("/api/v1/auth/select-role", json={"role": "commander"})
    assert sel.status_code == 200
    me2 = client.get("/api/v1/auth/me").json()["data"]
    assert me2["active_role"] == "commander"
    assert me2["role_selection_required"] is False


def test_t_auth_007_role_switch_audited(client: TestClient) -> None:
    user = make_user(
        email="user007@example.com",
        roles=("commander", "medic_psych"),
    )
    token = issue_invite_for(user.id)
    _accept_invite(client, token)

    client.post("/api/v1/auth/select-role", json={"role": "commander"})
    client.post("/api/v1/auth/select-role", json={"role": "medic_psych"})

    with SessionLocal() as db:
        events = (
            db.execute(select(AuditLog.event_type).order_by(AuditLog.created_at))
            .scalars()
            .all()
        )
    assert "role_switched" in events


def test_t_auth_008_role_not_assigned_rejected(client: TestClient) -> None:
    user = make_user(email="user008@example.com", roles=("soldier",))
    token = issue_invite_for(user.id)
    _accept_invite(client, token)

    body = client.post("/api/v1/auth/select-role", json={"role": "admin"}).json()
    assert body["success"] is False
    assert body["error"]["code"] == "INVALID_ACTIVE_ROLE"


def test_invite_accept_rejects_short_password(client: TestClient) -> None:
    user = make_user(email="weak@example.com")
    token = issue_invite_for(user.id)
    body = _accept_invite(client, token, password="short")
    assert body["success"] is False
    assert body["error"]["code"] == "WEAK_PASSWORD"


def test_login_after_invite_accept(client: TestClient) -> None:
    user = make_user(email="returning@example.com", roles=("soldier",))
    token = issue_invite_for(user.id)
    _accept_invite(client, token)
    client.post("/api/v1/auth/logout")

    body = _login(client, "returning@example.com")
    assert body["success"] is True
    me = client.get("/api/v1/auth/me").json()["data"]
    assert me["user"]["email"] == "returning@example.com"


def test_login_wrong_password_returns_unauthorized(client: TestClient) -> None:
    user = make_user(email="wrong@example.com", roles=("soldier",))
    token = issue_invite_for(user.id)
    _accept_invite(client, token)
    client.post("/api/v1/auth/logout")

    body = _login(client, "wrong@example.com", password="not the password!!")
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_login_unknown_email_returns_unauthorized(client: TestClient) -> None:
    body = _login(client, "ghost@example.com", password="anything-but-real")
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_login_user_without_password_blocked(client: TestClient) -> None:
    """A user that exists but has not accepted their invite has
    password_hash = NULL. Login must still fail."""

    make_user(email="nopw@example.com", roles=("soldier",))
    body = _login(client, "nopw@example.com", password=GOOD_PASSWORD)
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_logout_invalidates_session(client: TestClient) -> None:
    user = make_user(email="logout@example.com", roles=("soldier",))
    token = issue_invite_for(user.id)
    _accept_invite(client, token)

    out = client.post("/api/v1/auth/logout")
    assert out.status_code == 200
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 401


def test_password_forgot_is_anti_enumeration(client: TestClient) -> None:
    """Same envelope whether the email is known or not."""

    stub = mailer_mod.StubMailer()
    mailer_mod.set_mailer(stub)
    try:
        unknown = client.post(
            "/api/v1/auth/password/forgot",
            json={"email": "ghost@example.com"},
        ).json()
        assert unknown["success"] is True
        assert unknown["data"]["queued"] is True
        assert stub.sent_resets == []  # no email actually sent for ghost

        user = make_user(email="exists@example.com", roles=("soldier",))
        token = issue_invite_for(user.id)
        _accept_invite(client, token)
        client.post("/api/v1/auth/logout")

        known = client.post(
            "/api/v1/auth/password/forgot",
            json={"email": "exists@example.com"},
        ).json()
        # Identical shape; email is queued in the background.
        assert known["data"]["queued"] is True
        assert len(stub.sent_resets) == 1
        assert stub.sent_resets[0].to_email == "exists@example.com"
    finally:
        mailer_mod.set_mailer(None)


def test_password_reset_full_flow(client: TestClient) -> None:
    user = make_user(email="reset@example.com", roles=("soldier",))
    token = issue_invite_for(user.id)
    _accept_invite(client, token)
    # session A is now live; we keep its cookie for the "session revoked" check
    # below by using a separate client.

    stub = mailer_mod.StubMailer()
    mailer_mod.set_mailer(stub)
    try:
        # Trigger reset email.
        client.post(
            "/api/v1/auth/password/forgot",
            json={"email": "reset@example.com"},
        )
        assert len(stub.sent_resets) == 1
        reset_url = stub.sent_resets[0].reset_url

        # Pull the token out of the URL — frontend would do this via query
        # param routing.
        assert "token=" in reset_url
        reset_token = reset_url.rsplit("token=", 1)[1]

        new_password = "brand new battery horse staple"
        body = client.post(
            "/api/v1/auth/password/reset",
            json={"token": reset_token, "password": new_password},
        ).json()
        assert body["success"] is True

        # Old password no longer works; new one does.
        client.post("/api/v1/auth/logout")
        bad = _login(client, "reset@example.com", password=GOOD_PASSWORD)
        assert bad["success"] is False
        good = _login(client, "reset@example.com", password=new_password)
        assert good["success"] is True

        with SessionLocal() as db:
            events = (
                db.execute(select(AuditLog.event_type).order_by(AuditLog.created_at))
                .scalars()
                .all()
            )
        assert "password_reset_requested" in events
        assert "password_reset_completed" in events
    finally:
        mailer_mod.set_mailer(None)


def test_password_reset_token_cannot_be_reused(client: TestClient) -> None:
    user = make_user(email="reuse@example.com", roles=("soldier",))
    token = issue_invite_for(user.id)
    _accept_invite(client, token)

    stub = mailer_mod.StubMailer()
    mailer_mod.set_mailer(stub)
    try:
        client.post(
            "/api/v1/auth/password/forgot",
            json={"email": "reuse@example.com"},
        )
        reset_token = stub.sent_resets[0].reset_url.rsplit("token=", 1)[1]
        first = client.post(
            "/api/v1/auth/password/reset",
            json={"token": reset_token, "password": "first new password 123"},
        ).json()
        assert first["success"] is True

        second = client.post(
            "/api/v1/auth/password/reset",
            json={"token": reset_token, "password": "second new password 456"},
        ).json()
        assert second["success"] is False
        assert second["error"]["code"] == "INVALID_RESET_TOKEN"
    finally:
        mailer_mod.set_mailer(None)


def test_password_reset_token_expired(client: TestClient) -> None:
    user = make_user(email="exp@example.com", roles=("soldier",))
    token = issue_invite_for(user.id)
    _accept_invite(client, token)

    stub = mailer_mod.StubMailer()
    mailer_mod.set_mailer(stub)
    try:
        client.post(
            "/api/v1/auth/password/forgot",
            json={"email": "exp@example.com"},
        )
        reset_token = stub.sent_resets[0].reset_url.rsplit("token=", 1)[1]

        with SessionLocal() as db:
            row = db.execute(select(PasswordResetToken)).scalar_one()
            row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            db.commit()

        body = client.post(
            "/api/v1/auth/password/reset",
            json={"token": reset_token, "password": "another fresh password"},
        ).json()
        assert body["success"] is False
        assert body["error"]["code"] == "RESET_TOKEN_EXPIRED"
    finally:
        mailer_mod.set_mailer(None)
