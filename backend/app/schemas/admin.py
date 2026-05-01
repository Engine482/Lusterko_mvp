"""Pydantic schemas for `/api/v1/admin/*` per `Lusterko_API_Contracts_v1.md` §4."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.constants import AuditEventType, InviteStatus, Role, UserStatus
from app.schemas.common import UnitBrief, UserDetail


class CreateUserRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    unit_id: uuid.UUID | None = None
    roles: list[Role] = Field(..., min_length=1)


class UpdateUserRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    unit_id: uuid.UUID | None = None


class SetRolesRequest(BaseModel):
    roles: list[Role] = Field(..., min_length=1)


class UserResponse(BaseModel):
    user: UserDetail


class UsersListResponse(BaseModel):
    items: list[UserDetail]
    total: int
    page: int
    page_size: int


class CreateUnitRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str | None = Field(default=None, max_length=50)


class UnitsListResponse(BaseModel):
    items: list[UnitBrief]


class InviteResponse(BaseModel):
    """Returned to the admin once when an invite is created.

    `token` is the plaintext used to assemble the invite URL on the admin UI;
    only `token_hash` is persisted (DB Schema §2.5).
    """

    invite_id: uuid.UUID
    token: str
    expires_at: datetime
    status: InviteStatus


class AuditLogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    event_type: AuditEventType
    actor_user_id: uuid.UUID | None = None
    target_user_id: uuid.UUID | None = None
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class AuditLogsListResponse(BaseModel):
    items: list[AuditLogItem]
    total: int
    page: int
    page_size: int


class StatusOnlyResponse(BaseModel):
    user_id: uuid.UUID
    status: UserStatus
