"""Pydantic schemas for `/api/v1/auth/*` per `Lusterko_API_Contracts_v1.md` §3."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.constants import Role
from app.schemas.common import UserBrief


class GoogleStartResponse(BaseModel):
    redirect_url: str


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
