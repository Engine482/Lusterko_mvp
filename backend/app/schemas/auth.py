"""Pydantic schemas for `/api/v1/auth/*` per `Lusterko_API_Contracts_v1.md` §3
(Sprint 7 email+password auth)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.core.constants import Role
from app.schemas.common import UserBrief


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    logged_in: bool


class InviteAcceptRequest(BaseModel):
    token: str = Field(..., min_length=10)
    full_name: str | None = Field(default=None, max_length=200)
    password: str = Field(..., min_length=1)


class InviteAcceptResponse(BaseModel):
    accepted: bool


class PasswordForgotRequest(BaseModel):
    email: EmailStr


class PasswordForgotResponse(BaseModel):
    # Always identical regardless of whether the email matched a real user —
    # the frontend renders a single generic "if your email is registered…"
    # message based on this flag.
    queued: bool = True


class PasswordResetRequest(BaseModel):
    token: str = Field(..., min_length=10)
    password: str = Field(..., min_length=1)


class PasswordResetResponse(BaseModel):
    reset: bool


class AuthMeResponse(BaseModel):
    user: UserBrief
    roles: list[Role]
    active_role: Role | None = None
    role_selection_required: bool


class SelectRoleRequest(BaseModel):
    role: Role = Field(...)


class SelectRoleResponse(BaseModel):
    active_role: Role


class RefreshResponse(BaseModel):
    refreshed: bool


class LogoutResponse(BaseModel):
    logged_out: bool


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=1)


class PasswordChangeResponse(BaseModel):
    changed: bool


class ProfileUpdateRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)


class ProfileUpdateResponse(BaseModel):
    user: UserBrief


class AuthConfigResponse(BaseModel):
    open_registration_enabled: bool


class DemoRegisterStartRequest(BaseModel):
    email: EmailStr


class DemoRegisterStartResponse(BaseModel):
    # Anti-enumeration: `queued` and `email_dispatch` stay identical
    # regardless of whether the email matched an existing active user, was
    # rate-limited, or hit a turned-off flag — those paths all report
    # `sent` so callers cannot distinguish them from a real success.
    # `failed` is reserved for genuine SMTP misfires on a freshly-issued
    # registration so the frontend can show an honest error instead of
    # "Перевірте пошту" when the mailer is misconfigured (P0.3).
    queued: bool = True
    email_dispatch: Literal["sent", "failed"] = "sent"


class DemoRegisterConfirmRequest(BaseModel):
    token: str = Field(..., min_length=10)
    full_name: str = Field(..., min_length=1, max_length=200)
    password: str = Field(..., min_length=1)


class DemoRegisterConfirmResponse(BaseModel):
    registered: bool
