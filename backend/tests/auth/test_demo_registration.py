"""Tests for the open-demo registration flow (Task A).

Covers:
- /auth/config feature flag visibility
- start-confirm round trip with the StubMailer capturing the token
- new user gets soldier+commander+medic_psych roles
- anti-enumeration: existing email yields the same envelope, no token issued
- flag-off behavior: start returns generic queued envelope, confirm rejects
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.demo_registration import DemoRegistration
from app.models.user import User
from app.models.user_role import UserRole
from app.modules.notifications import mailer as mailer_mod
from tests.factories import make_user


GOOD_PASSWORD = "correct horse battery staple"


def _enable_open_registration(monkeypatch) -> None:
    monkeypatch.setenv("DEMO_OPEN_REGISTRATION", "true")
    get_settings.cache_clear()


def _disable_open_registration(monkeypatch) -> None:
    monkeypatch.setenv("DEMO_OPEN_REGISTRATION", "false")
    get_settings.cache_clear()


def _stub_mailer() -> mailer_mod.StubMailer:
    stub = mailer_mod.StubMailer()
    mailer_mod.set_mailer(stub)
    return stub


def _last_demo_token(stub: mailer_mod.StubMailer) -> str:
    assert stub.sent_demo_registrations, "expected one demo registration email"
    msg = stub.sent_demo_registrations[-1]
    # confirm_url is .../register/confirm?token=<token>
    return msg.confirm_url.split("token=", 1)[1]


def test_config_reflects_demo_open_registration_flag(
    client: TestClient, monkeypatch
) -> None:
    _disable_open_registration(monkeypatch)
    body = client.get("/api/v1/auth/config").json()
    assert body["data"]["open_registration_enabled"] is False

    _enable_open_registration(monkeypatch)
    body = client.get("/api/v1/auth/config").json()
    assert body["data"]["open_registration_enabled"] is True


def test_demo_register_full_round_trip(client: TestClient, monkeypatch) -> None:
    _enable_open_registration(monkeypatch)
    stub = _stub_mailer()

    start = client.post(
        "/api/v1/auth/demo/register/start",
        json={"email": "tester@tester.lusterko.io"},
    )
    assert start.status_code == 200
    assert start.json()["data"]["queued"] is True

    token = _last_demo_token(stub)
    confirm = client.post(
        "/api/v1/auth/demo/register/confirm",
        json={
            "token": token,
            "full_name": "Demo Tester",
            "password": GOOD_PASSWORD,
        },
    )
    assert confirm.status_code == 200, confirm.text
    assert confirm.json()["data"]["registered"] is True
    # Session cookie issued on confirm so the tester is logged in immediately.
    assert "lusterko_session" in confirm.cookies

    me = client.get("/api/v1/auth/me").json()["data"]
    assert me["user"]["email"] == "tester@tester.lusterko.io"
    assert me["user"]["full_name"] == "Demo Tester"
    assert sorted(me["roles"]) == ["commander", "medic_psych", "soldier"]
    # Three roles → role selection is required on first login.
    assert me["role_selection_required"] is True

    with SessionLocal() as db:
        user = db.execute(
            select(User).where(User.email == "tester@tester.lusterko.io")
        ).scalar_one()
        roles = db.execute(
            select(UserRole.role).where(UserRole.user_id == user.id)
        ).scalars().all()
        assert sorted(roles) == ["commander", "medic_psych", "soldier"]


def test_demo_register_existing_email_anti_enumeration(
    client: TestClient, monkeypatch
) -> None:
    _enable_open_registration(monkeypatch)
    stub = _stub_mailer()
    make_user(email="taken@tester.lusterko.io", roles=("soldier",))

    res = client.post(
        "/api/v1/auth/demo/register/start",
        json={"email": "taken@tester.lusterko.io"},
    )
    # Same envelope as the success case — caller cannot distinguish.
    assert res.status_code == 200
    assert res.json()["data"]["queued"] is True
    # But no email was sent and no DemoRegistration row was created.
    assert stub.sent_demo_registrations == []
    with SessionLocal() as db:
        rows = db.execute(select(DemoRegistration)).scalars().all()
        assert rows == []


def test_demo_register_flag_off_does_nothing(
    client: TestClient, monkeypatch
) -> None:
    _disable_open_registration(monkeypatch)
    stub = _stub_mailer()

    res = client.post(
        "/api/v1/auth/demo/register/start",
        json={"email": "noflag@tester.lusterko.io"},
    )
    # Generic envelope so a turned-off demo doesn't surface as a 4xx.
    assert res.status_code == 200
    assert res.json()["data"]["queued"] is True
    assert stub.sent_demo_registrations == []

    confirm = client.post(
        "/api/v1/auth/demo/register/confirm",
        json={
            "token": "x" * 32,
            "full_name": "Should Not Work",
            "password": GOOD_PASSWORD,
        },
    )
    assert confirm.status_code == 403
    assert confirm.json()["error"]["code"] == "DEMO_REGISTRATION_DISABLED"


def test_demo_register_confirm_rejects_invalid_token(
    client: TestClient, monkeypatch
) -> None:
    _enable_open_registration(monkeypatch)
    _stub_mailer()
    res = client.post(
        "/api/v1/auth/demo/register/confirm",
        json={
            "token": "x" * 32,
            "full_name": "Demo Tester",
            "password": GOOD_PASSWORD,
        },
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_DEMO_TOKEN"


def test_demo_register_confirm_rejects_weak_password(
    client: TestClient, monkeypatch
) -> None:
    _enable_open_registration(monkeypatch)
    stub = _stub_mailer()
    client.post(
        "/api/v1/auth/demo/register/start",
        json={"email": "weak@tester.lusterko.io"},
    )
    token = _last_demo_token(stub)

    res = client.post(
        "/api/v1/auth/demo/register/confirm",
        json={
            "token": token,
            "full_name": "Demo Tester",
            "password": "short",
        },
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "WEAK_PASSWORD"


def test_demo_register_token_single_use(
    client: TestClient, monkeypatch
) -> None:
    _enable_open_registration(monkeypatch)
    stub = _stub_mailer()
    client.post(
        "/api/v1/auth/demo/register/start",
        json={"email": "once@tester.lusterko.io"},
    )
    token = _last_demo_token(stub)

    first = client.post(
        "/api/v1/auth/demo/register/confirm",
        json={
            "token": token,
            "full_name": "Demo Tester",
            "password": GOOD_PASSWORD,
        },
    )
    assert first.status_code == 200

    # Replay the same token from a fresh client (no session cookie carried).
    second = client.post(
        "/api/v1/auth/demo/register/confirm",
        json={
            "token": token,
            "full_name": "Other",
            "password": GOOD_PASSWORD,
        },
    )
    assert second.status_code == 400
    assert second.json()["error"]["code"] == "INVALID_DEMO_TOKEN"


def test_demo_register_start_reports_email_dispatch_sent(
    client: TestClient, monkeypatch
) -> None:
    """Successful path advertises `email_dispatch=sent` so the frontend can
    redirect to the «Перевірте пошту» screen with confidence."""

    _enable_open_registration(monkeypatch)
    _stub_mailer()

    res = client.post(
        "/api/v1/auth/demo/register/start",
        json={"email": "ok@tester.lusterko.io"},
    )
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["queued"] is True
    assert body["email_dispatch"] == "sent"


def test_demo_register_start_reports_email_dispatch_failed_on_smtp_error(
    client: TestClient, monkeypatch
) -> None:
    """When the mailer surfaces an SMTP error we must NOT pretend success.
    The frontend reads `email_dispatch=failed` and shows an honest message
    instead of "Перевірте пошту". P0.3 fix for prod silent-success bug."""

    _enable_open_registration(monkeypatch)

    class FailingMailer:
        name = "failing"

        def send_invite(self, msg: mailer_mod.InviteEmail) -> mailer_mod.SendResult:
            return mailer_mod.SendResult(ok=False, error="connection refused")

        def send_password_reset(
            self, msg: mailer_mod.PasswordResetEmail
        ) -> mailer_mod.SendResult:
            return mailer_mod.SendResult(ok=False, error="connection refused")

        def send_demo_registration(
            self, msg: mailer_mod.DemoRegistrationEmail
        ) -> mailer_mod.SendResult:
            return mailer_mod.SendResult(ok=False, error="connection refused")

    mailer_mod.set_mailer(FailingMailer())
    try:
        res = client.post(
            "/api/v1/auth/demo/register/start",
            json={"email": "smtp-broken@tester.lusterko.io"},
        )
        assert res.status_code == 200
        body = res.json()["data"]
        # Anti-enumeration: outer envelope still says queued.
        assert body["queued"] is True
        # But the dispatch field is honest — the frontend must NOT redirect
        # to /register/sent on this response.
        assert body["email_dispatch"] == "failed"
    finally:
        mailer_mod.set_mailer(None)


def test_demo_register_start_existing_user_reports_sent_for_anti_enumeration(
    client: TestClient, monkeypatch
) -> None:
    """An attacker probing with a known email must see the same envelope as
    a real success — including `email_dispatch=sent`. Otherwise the field
    leaks user existence."""

    _enable_open_registration(monkeypatch)
    _stub_mailer()
    make_user(email="existing@tester.lusterko.io", roles=("soldier",))

    res = client.post(
        "/api/v1/auth/demo/register/start",
        json={"email": "existing@tester.lusterko.io"},
    )
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["queued"] is True
    assert body["email_dispatch"] == "sent"


def test_demo_register_confirm_links_user_to_demo_unit(
    client: TestClient, monkeypatch
) -> None:
    """P0.5: a tester who self-registers must be attached to the seeded
    `Демо-взвод` so the commander dashboard and medic queue render data
    on first login. Without the link the dashboards are silently empty
    because both endpoints scope reads by `users.unit_id`."""

    from app.models.unit import Unit

    _enable_open_registration(monkeypatch)
    stub = _stub_mailer()

    # Stand up the demo unit the way the seed script does.
    with SessionLocal() as db:
        demo_unit = Unit(name="Демо-взвод", is_active=True)
        db.add(demo_unit)
        db.commit()
        demo_unit_id = demo_unit.id

    client.post(
        "/api/v1/auth/demo/register/start",
        json={"email": "linked@tester.lusterko.io"},
    )
    token = _last_demo_token(stub)
    res = client.post(
        "/api/v1/auth/demo/register/confirm",
        json={
            "token": token,
            "full_name": "Linked Tester",
            "password": GOOD_PASSWORD,
        },
    )
    assert res.status_code == 200, res.text

    with SessionLocal() as db:
        user = db.execute(
            select(User).where(User.email == "linked@tester.lusterko.io")
        ).scalar_one()
        assert user.unit_id == demo_unit_id


def test_demo_register_confirm_without_demo_unit_leaves_unit_null(
    client: TestClient, monkeypatch
) -> None:
    """If the seed has not run on this environment, the user is still
    created — just without a unit. The dashboards stay empty rather than
    crash; operators can wire the user up later."""

    _enable_open_registration(monkeypatch)
    stub = _stub_mailer()

    client.post(
        "/api/v1/auth/demo/register/start",
        json={"email": "no-unit@tester.lusterko.io"},
    )
    token = _last_demo_token(stub)
    res = client.post(
        "/api/v1/auth/demo/register/confirm",
        json={
            "token": token,
            "full_name": "No Unit Tester",
            "password": GOOD_PASSWORD,
        },
    )
    assert res.status_code == 200, res.text

    with SessionLocal() as db:
        user = db.execute(
            select(User).where(User.email == "no-unit@tester.lusterko.io")
        ).scalar_one()
        assert user.unit_id is None
