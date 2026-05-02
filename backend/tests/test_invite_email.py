"""Invite + password-reset email delivery tests."""

from __future__ import annotations

import smtplib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from app.modules.notifications import mailer as mailer_mod
from tests.factories import issue_invite_for, make_user


GOOD_PASSWORD = "correct horse battery staple"


def _login_admin(client: TestClient, email: str) -> None:
    user = make_user(email=email, roles=("admin",))
    token = issue_invite_for(user.id)
    client.post(
        "/api/v1/auth/invite/accept",
        json={"token": token, "password": GOOD_PASSWORD},
    )


@pytest.fixture
def stub_mailer() -> mailer_mod.StubMailer:
    stub = mailer_mod.StubMailer()
    mailer_mod.set_mailer(stub)
    yield stub
    mailer_mod.set_mailer(None)


def test_stub_mailer_records_invite_url(
    client: TestClient, stub_mailer: mailer_mod.StubMailer
) -> None:
    _login_admin(client, "admin-mail-1@example.com")
    target = make_user(email="invitee-mail-1@example.com")

    res = client.post(f"/api/v1/admin/users/{target.id}/invite")
    assert res.status_code == 200, res.text
    token = res.json()["data"]["token"]

    assert len(stub_mailer.sent_invites) == 1
    msg = stub_mailer.sent_invites[0]
    assert msg.to_email == "invitee-mail-1@example.com"
    assert token in msg.invite_url
    assert msg.invite_url.endswith(f"/invite?token={token}")

    with SessionLocal() as db:
        events = db.execute(select(AuditLog.event_type)).scalars().all()
    assert "invite_email_sent" in events
    assert "invite_email_failed" not in events


def test_smtp_failure_does_not_break_invite_creation(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FailingMailer:
        name = "failing"

        def send_invite(
            self, msg: mailer_mod.InviteEmail
        ) -> mailer_mod.SendResult:
            return mailer_mod.SendResult(ok=False, error="connection refused")

        def send_password_reset(
            self, msg: mailer_mod.PasswordResetEmail
        ) -> mailer_mod.SendResult:
            return mailer_mod.SendResult(ok=False, error="connection refused")

    mailer_mod.set_mailer(FailingMailer())
    try:
        _login_admin(client, "admin-mail-2@example.com")
        target = make_user(email="invitee-mail-2@example.com")

        res = client.post(f"/api/v1/admin/users/{target.id}/invite")
        assert res.status_code == 200, res.text
        body = res.json()["data"]
        assert body["status"] == "pending"
        assert len(body["token"]) > 30
    finally:
        mailer_mod.set_mailer(None)

    with SessionLocal() as db:
        events = db.execute(select(AuditLog.event_type)).scalars().all()
    assert "invite_email_failed" in events
    assert "invite_email_sent" not in events


def test_smtp_mailer_swallows_exception_for_invite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(*args: object, **kwargs: object) -> object:
        raise smtplib.SMTPException("nope")

    monkeypatch.setattr(smtplib, "SMTP", boom)

    smtp = mailer_mod.SmtpMailer(
        host="example.invalid", port=587, from_email="from@example.com"
    )
    result = smtp.send_invite(
        mailer_mod.InviteEmail(
            to_email="to@example.com",
            to_full_name="Test",
            invite_url="https://lusterko.example/invite?token=abc",
            expires_at_iso="2026-01-01T00:00:00+00:00",
        )
    )
    assert result.ok is False
    assert result.error and "nope" in result.error


def test_smtp_mailer_swallows_exception_for_password_reset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(*args: object, **kwargs: object) -> object:
        raise smtplib.SMTPException("smtp down")

    monkeypatch.setattr(smtplib, "SMTP", boom)

    smtp = mailer_mod.SmtpMailer(
        host="example.invalid", port=587, from_email="from@example.com"
    )
    result = smtp.send_password_reset(
        mailer_mod.PasswordResetEmail(
            to_email="to@example.com",
            to_full_name="Test",
            reset_url="https://lusterko.example/reset-password?token=abc",
            expires_at_iso="2026-01-01T00:00:00+00:00",
        )
    )
    assert result.ok is False
    assert result.error and "smtp down" in result.error
