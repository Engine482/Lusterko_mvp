"""Google OAuth integration with a dev-stub fallback.

Real flow when both `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set,
otherwise a deterministic stub is used so dev/test runs without external IO
(`Lusterko_API_Contracts_v1.md` §3.1-3.2 + Sprint 1 acceptance from
`Lusterko_Test_Scenarios_P0_v1.md` §6).
"""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass

import httpx

from app.core.config import get_settings


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
GOOGLE_SCOPES = ["openid", "email", "profile"]


@dataclass(frozen=True)
class GoogleProfile:
    subject: str
    email: str


def is_stub_mode() -> bool:
    settings = get_settings()
    return not (settings.google_client_id and settings.google_client_secret)


def build_authorize_url(*, state: str, redirect_uri: str) -> str:
    if is_stub_mode():
        # Skip Google entirely; the start endpoint already redirected to the
        # callback with the same `state`. The callback knows how to resolve
        # the user from the invite carried in `state`.
        return f"{redirect_uri}?state={urllib.parse.quote(state)}&dev_stub=1"

    settings = get_settings()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "state": state,
        "access_type": "online",
        "include_granted_scopes": "true",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"


def exchange_code_for_profile(*, code: str, redirect_uri: str) -> GoogleProfile:
    """Real OAuth code → ID/userinfo exchange. Raises on failure."""

    settings = get_settings()
    with httpx.Client(timeout=10.0) as client:
        token_resp = client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]

        userinfo_resp = client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        userinfo_resp.raise_for_status()
        info = userinfo_resp.json()

    return GoogleProfile(subject=str(info["sub"]), email=str(info["email"]))


def stub_profile_for(email: str) -> GoogleProfile:
    """Used by `/auth/google/callback?dev_stub=1`. Subject = email so a user
    keeps the same `user_identities` row across logins."""

    return GoogleProfile(subject=f"dev-stub:{email}", email=email)
