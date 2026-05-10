from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import Role, UserStatus


class UnitBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str | None = None


class UserBrief(BaseModel):
    """Short user shape used in /auth/me, admin listings, commander views.

    Field set is the safe intersection per `Lusterko_RBAC_Matrix_v1.md` §6.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    # Output schema: loose `str` rather than `EmailStr`. The seed demo unit
    # uses `@demo-platoon.lusterko.local` addresses; pydantic's EmailStr
    # rejects the `.local` TLD (RFC 6762 mDNS reserved), so every admin
    # /users response that included a seeded soldier 500'd. Input schemas
    # (CreateUserRequest, LoginRequest, etc.) still use EmailStr for strict
    # validation of new data.
    email: str = Field(min_length=3, max_length=320)
    full_name: str = Field(min_length=1, max_length=200)
    status: UserStatus
    unit_id: uuid.UUID | None = None


class UserDetail(UserBrief):
    roles: list[Role]
    created_at: datetime
    updated_at: datetime
