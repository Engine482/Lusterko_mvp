"""Regression test for the production-cookie secure flag (TASK-6104).

The session cookie must be `Secure` whenever `APP_ENV=production`. The check
lives in `is_secure_cookies()`. Tests run with `APP_ENV=test` so we monkeypatch
the cached settings to assert both branches without poking process env.
"""

from __future__ import annotations

import dataclasses

from fastapi import Response

from app.core import cookies
from app.core.config import Settings, get_settings


def _settings_with_env(app_env: str) -> Settings:
    return dataclasses.replace(get_settings(), app_env=app_env)


def test_session_cookie_is_secure_in_production(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cookies, "get_settings", lambda: _settings_with_env("production"))
    response = Response()
    cookies.set_session_cookie(response, "tok")
    assert "Secure" in response.headers["set-cookie"]


def test_session_cookie_not_secure_outside_production(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    for env in ("development", "test", "staging"):
        monkeypatch.setattr(cookies, "get_settings", lambda env=env: _settings_with_env(env))
        response = Response()
        cookies.set_session_cookie(response, "tok")
        assert "Secure" not in response.headers["set-cookie"], env
