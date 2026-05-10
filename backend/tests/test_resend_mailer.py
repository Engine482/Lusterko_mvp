"""Unit tests for `ResendApiMailer`.

Drives the mailer with a fake `httpx.post` so we exercise the success
(204 / 200), HTTP-error (422), and transport-exception (timeout) branches
without touching the network.
"""

from __future__ import annotations

import pytest

from app.modules.notifications import mailer as mailer_mod


class _FakeResponse:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


def _patch_httpx(monkeypatch: pytest.MonkeyPatch, fake):
    monkeypatch.setattr(mailer_mod.httpx, "post", fake)


def _demo_msg() -> mailer_mod.DemoRegistrationEmail:
    return mailer_mod.DemoRegistrationEmail(
        to_email="tester@example.com",
        confirm_url="https://lusterko.example/register/confirm?token=t",
        expires_at_iso="2026-01-01T00:00:00+00:00",
    )


def test_resend_mailer_send_demo_registration_ok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: ANN001
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return _FakeResponse(200, '{"id":"em_123"}')

    _patch_httpx(monkeypatch, fake_post)
    mailer = mailer_mod.ResendApiMailer(
        api_key="re_test", from_email="noreply@lusterko.example"
    )

    result = mailer.send_demo_registration(_demo_msg())

    assert result.ok is True
    assert result.error is None
    assert captured["url"] == "https://api.resend.com/emails"
    assert captured["headers"] == {"Authorization": "Bearer re_test"}
    assert captured["json"]["from"] == "noreply@lusterko.example"
    assert captured["json"]["to"] == ["tester@example.com"]
    assert "lusterko.example/register/confirm" in captured["json"]["html"]
    assert "lusterko.example/register/confirm" in captured["json"]["text"]


def test_resend_mailer_send_demo_registration_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(url, **_):  # noqa: ANN001
        return _FakeResponse(422, '{"message":"unverified domain"}')

    _patch_httpx(monkeypatch, fake_post)
    mailer = mailer_mod.ResendApiMailer(
        api_key="re_test", from_email="noreply@lusterko.example"
    )

    result = mailer.send_demo_registration(_demo_msg())

    assert result.ok is False
    assert result.error is not None
    assert "resend_http_422" in result.error


def test_resend_mailer_send_demo_registration_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(url, **_):  # noqa: ANN001
        raise mailer_mod.httpx.ReadTimeout("timed out")

    _patch_httpx(monkeypatch, fake_post)
    mailer = mailer_mod.ResendApiMailer(
        api_key="re_test", from_email="noreply@lusterko.example"
    )

    result = mailer.send_demo_registration(_demo_msg())

    assert result.ok is False
    assert result.error == "timed out"


def test_build_from_env_prefers_resend_over_smtp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LUSTERKO_MAILER", "auto")
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("INVITE_FROM_EMAIL", "noreply@lusterko.example")
    mailer_mod.set_mailer(None)
    try:
        m = mailer_mod.get_mailer()
        assert m.name == "resend"
        assert isinstance(m, mailer_mod.ResendApiMailer)
        assert m.api_key == "re_test"
        assert m.from_email == "noreply@lusterko.example"
    finally:
        mailer_mod.set_mailer(None)


def test_build_from_env_falls_back_to_smtp_without_resend_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LUSTERKO_MAILER", "auto")
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("INVITE_FROM_EMAIL", "noreply@lusterko.example")
    mailer_mod.set_mailer(None)
    try:
        m = mailer_mod.get_mailer()
        assert m.name == "smtp"
        assert isinstance(m, mailer_mod.SmtpMailer)
    finally:
        mailer_mod.set_mailer(None)


def test_build_from_env_explicit_resend_requires_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LUSTERKO_MAILER", "resend")
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    mailer_mod.set_mailer(None)
    try:
        m = mailer_mod.get_mailer()
        # Missing key falls back to stub but logs a loud warning — see
        # `mailer_init_missing_resend_key` in service logs.
        assert m.name == "stub"
    finally:
        mailer_mod.set_mailer(None)
