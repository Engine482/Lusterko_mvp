"""Session cookie policy.

API Contracts §1.1 defines an HTTP-only session cookie. P0 attributes:
- name        : `lusterko_session`
- httponly    : True
- secure      : True in production, False otherwise (so dev over http works)
- samesite    : 'lax'
- path        : '/'
- max_age     : matches `user_sessions.expires_at` lifetime

Refresh tokens are not used yet; `/auth/refresh` extends the same cookie's
TTL (Sprint Plan §5).
"""

from __future__ import annotations

from datetime import timedelta

from fastapi import Response

from app.core.config import get_settings

SESSION_COOKIE_NAME = "lusterko_session"
SESSION_TTL = timedelta(days=30)
INVITE_TTL = timedelta(days=7)
PASSWORD_RESET_TTL = timedelta(hours=1)


def is_secure_cookies() -> bool:
    return get_settings().app_env == "production"


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=int(SESSION_TTL.total_seconds()),
        httponly=True,
        secure=is_secure_cookies(),
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=is_secure_cookies(),
        samesite="lax",
    )
