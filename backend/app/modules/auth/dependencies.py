"""RBAC building blocks (Backlog TASK-1101..1104).

Every guard runs server-side, against the live DB row, on every request — frontend
guards are UX only (`Lusterko_RBAC_Matrix_v1.md` §7.2).
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import Role
from app.core.cookies import SESSION_COOKIE_NAME
from app.core.security import hash_token
from app.db.session import SessionLocal
from app.models.user import User
from app.models.user_role import UserRole
from app.models.user_session import UserSession


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@dataclass(frozen=True)
class SessionContext:
    user: User
    session: UserSession
    role: Role
    role_set: frozenset[Role]


class AuthError(HTTPException):
    """Raised by guards. Translated to envelope errors by the global handler."""

    def __init__(self, code: str, message: str, http_status: int) -> None:
        super().__init__(status_code=http_status, detail={"code": code, "message": message})
        self.code = code
        self.message = message


def _require_session_row(db: Session, token: str) -> UserSession:
    token_hash = hash_token(token)
    stmt = select(UserSession).where(UserSession.refresh_token_hash == token_hash)
    session_row = db.execute(stmt).scalar_one_or_none()
    if session_row is None:
        raise AuthError("UNAUTHORIZED", "Invalid session.", status.HTTP_401_UNAUTHORIZED)
    if session_row.status != "active":
        raise AuthError("UNAUTHORIZED", "Session not active.", status.HTTP_401_UNAUTHORIZED)
    if session_row.expires_at <= datetime.now(timezone.utc):
        raise AuthError("UNAUTHORIZED", "Session expired.", status.HTTP_401_UNAUTHORIZED)
    return session_row


def _require_active_user(db: Session, user_id: uuid.UUID) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise AuthError("UNAUTHORIZED", "User missing.", status.HTTP_401_UNAUTHORIZED)
    if user.status != "active":
        raise AuthError("UNAUTHORIZED", "User deactivated.", status.HTTP_401_UNAUTHORIZED)
    return user


def _load_role_set(db: Session, user_id: uuid.UUID) -> frozenset[Role]:
    rows = db.execute(select(UserRole.role).where(UserRole.user_id == user_id)).scalars().all()
    valid: set[Role] = {"soldier", "commander", "medic_psych", "admin"}
    return frozenset(r for r in rows if r in valid)


def current_session_context(
    db: Session = Depends(get_db),
    lusterko_session: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> SessionContext:
    """Validates cookie → session → user. Used as the base of every guard."""

    if not lusterko_session:
        raise AuthError("UNAUTHORIZED", "Missing session cookie.", status.HTTP_401_UNAUTHORIZED)

    session_row = _require_session_row(db, lusterko_session)
    user = _require_active_user(db, session_row.user_id)
    roles = _load_role_set(db, user.id)

    # Defensive: active_role must still be in the user's role set.
    active = session_row.active_role
    if active not in roles:
        raise AuthError(
            "INVALID_ACTIVE_ROLE",
            "Active role no longer assigned.",
            status.HTTP_403_FORBIDDEN,
        )

    session_row.last_seen_at = datetime.now(timezone.utc)
    role_typed: Role = active  # validated via membership in `roles`
    return SessionContext(user=user, session=session_row, role=role_typed, role_set=roles)


def require_authenticated_session(
    ctx: SessionContext = Depends(current_session_context),
) -> SessionContext:
    """Authenticated, role already chosen. Default for protected endpoints."""

    if not ctx.session.role_selected:
        raise AuthError(
            "ROLE_SELECTION_REQUIRED",
            "Pick an active role first.",
            status.HTTP_409_CONFLICT,
        )
    return ctx


def require_role(role: Role) -> Callable[[SessionContext], SessionContext]:
    def _guard(
        ctx: SessionContext = Depends(require_authenticated_session),
    ) -> SessionContext:
        if ctx.role != role:
            raise AuthError(
                "INVALID_ACTIVE_ROLE",
                f"Active role is '{ctx.role}', this endpoint requires '{role}'.",
                status.HTTP_403_FORBIDDEN,
            )
        return ctx

    return _guard
