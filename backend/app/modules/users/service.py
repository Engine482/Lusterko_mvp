"""Admin user/unit management orchestration (Backlog TASK-1201..1208)."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import Role
from app.models.audit_log import AuditLog
from app.models.auth_invite import AuthInvite
from app.models.unit import Unit
from app.models.user import User
from app.models.user_role import UserRole
from app.models.user_session import UserSession
from app.services.audit_logger import log_event


class UserManagementError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _get_user_or_raise(db: Session, user_id: uuid.UUID) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise UserManagementError("NOT_FOUND", "User not found.")
    return user


def _set_roles(
    db: Session, *, user_id: uuid.UUID, roles: Iterable[Role]
) -> None:
    desired: set[Role] = set(roles)
    if not desired:
        raise UserManagementError("VALIDATION_ERROR", "User must have at least one role.")
    existing_rows = (
        db.execute(select(UserRole.role).where(UserRole.user_id == user_id)).scalars().all()
    )
    valid: set[Role] = {"soldier", "commander", "medic_psych", "admin"}
    existing: set[Role] = {r for r in existing_rows if r in valid}
    for role_to_add in desired - existing:
        db.add(UserRole(user_id=user_id, role=role_to_add))
    for role_to_remove in existing - desired:
        db.execute(
            UserRole.__table__.delete().where(  # type: ignore[attr-defined]
                UserRole.user_id == user_id, UserRole.role == role_to_remove
            )
        )


def _validate_unit(db: Session, unit_id: uuid.UUID | None) -> None:
    if unit_id is None:
        return
    unit = db.get(Unit, unit_id)
    if unit is None or not unit.is_active:
        raise UserManagementError("VALIDATION_ERROR", "Unit not found or inactive.")


def create_user(
    db: Session,
    *,
    actor_user_id: uuid.UUID,
    full_name: str,
    email: str,
    unit_id: uuid.UUID | None,
    roles: list[Role],
) -> User:
    _validate_unit(db, unit_id)
    if db.execute(select(User).where(User.email == email)).scalar_one_or_none() is not None:
        raise UserManagementError("CONFLICT", "Email already in use.")
    user = User(full_name=full_name, email=email, unit_id=unit_id, status="active")
    db.add(user)
    db.flush()
    _set_roles(db, user_id=user.id, roles=roles)
    log_event(
        db,
        event_type="user_created",
        actor_user_id=actor_user_id,
        target_user_id=user.id,
        entity_type="users",
        entity_id=user.id,
        metadata={"roles": list(roles), "unit_id": str(unit_id) if unit_id else None},
    )
    return user


def update_user(
    db: Session,
    *,
    actor_user_id: uuid.UUID,
    user_id: uuid.UUID,
    full_name: str | None,
    unit_id: uuid.UUID | None,
) -> User:
    user = _get_user_or_raise(db, user_id)
    if unit_id is not None:
        _validate_unit(db, unit_id)
        user.unit_id = unit_id
    if full_name is not None:
        user.full_name = full_name
    log_event(
        db,
        event_type="user_updated",
        actor_user_id=actor_user_id,
        target_user_id=user.id,
        entity_type="users",
        entity_id=user.id,
        metadata={"full_name": full_name, "unit_id": str(unit_id) if unit_id else None},
    )
    return user


def set_user_roles(
    db: Session,
    *,
    actor_user_id: uuid.UUID,
    user_id: uuid.UUID,
    roles: list[Role],
) -> User:
    user = _get_user_or_raise(db, user_id)
    _set_roles(db, user_id=user.id, roles=roles)
    log_event(
        db,
        event_type="user_updated",
        actor_user_id=actor_user_id,
        target_user_id=user.id,
        entity_type="user_roles",
        entity_id=user.id,
        metadata={"roles": roles},
    )
    return user


def deactivate_user(
    db: Session,
    *,
    actor_user_id: uuid.UUID,
    user_id: uuid.UUID,
) -> User:
    user = _get_user_or_raise(db, user_id)
    if user.status == "inactive":
        return user
    user.status = "inactive"
    # Per RBAC §5.2 — kill all live sessions and pending invites.
    db.execute(
        UserSession.__table__.update()  # type: ignore[attr-defined]
        .where(UserSession.user_id == user.id, UserSession.status == "active")
        .values(status="revoked")
    )
    now = datetime.now(timezone.utc)
    db.execute(
        AuthInvite.__table__.update()  # type: ignore[attr-defined]
        .where(AuthInvite.user_id == user.id, AuthInvite.status == "pending")
        .values(status="revoked", revoked_at=now)
    )
    log_event(
        db,
        event_type="user_deactivated",
        actor_user_id=actor_user_id,
        target_user_id=user.id,
        entity_type="users",
        entity_id=user.id,
    )
    return user


def reactivate_user(
    db: Session,
    *,
    actor_user_id: uuid.UUID,
    user_id: uuid.UUID,
) -> User:
    user = _get_user_or_raise(db, user_id)
    if user.status == "active":
        return user
    user.status = "active"
    log_event(
        db,
        event_type="user_reactivated",
        actor_user_id=actor_user_id,
        target_user_id=user.id,
        entity_type="users",
        entity_id=user.id,
    )
    return user


def list_users(
    db: Session,
    *,
    unit_id: uuid.UUID | None,
    status: str | None,
    role: str | None,
    page: int,
    page_size: int,
) -> tuple[list[User], int]:
    stmt = select(User)
    count_stmt = select(func.count()).select_from(User)
    if unit_id is not None:
        stmt = stmt.where(User.unit_id == unit_id)
        count_stmt = count_stmt.where(User.unit_id == unit_id)
    if status is not None:
        stmt = stmt.where(User.status == status)
        count_stmt = count_stmt.where(User.status == status)
    if role is not None:
        stmt = stmt.join(UserRole, UserRole.user_id == User.id).where(UserRole.role == role)
        count_stmt = count_stmt.select_from(User).join(
            UserRole, UserRole.user_id == User.id
        ).where(UserRole.role == role)
    stmt = stmt.order_by(User.created_at.desc()).limit(page_size).offset((page - 1) * page_size)
    items = list(db.execute(stmt).scalars().all())
    total = int(db.execute(count_stmt).scalar_one())
    return items, total


def get_user_roles(db: Session, user_id: uuid.UUID) -> list[Role]:
    rows = db.execute(select(UserRole.role).where(UserRole.user_id == user_id)).scalars().all()
    return list(rows)  # type: ignore[arg-type]


# --- Units -------------------------------------------------------------------


def list_units(db: Session) -> list[Unit]:
    return list(db.execute(select(Unit).order_by(Unit.name)).scalars().all())


def create_unit(
    db: Session, *, name: str, code: str | None
) -> Unit:
    if db.execute(select(Unit).where(Unit.name == name)).scalar_one_or_none() is not None:
        raise UserManagementError("CONFLICT", "Unit with this name exists.")
    unit = Unit(name=name, code=code, is_active=True)
    db.add(unit)
    db.flush()
    return unit


# --- Audit logs view ---------------------------------------------------------


def list_audit_logs(
    db: Session,
    *,
    event_type: str | None,
    actor_user_id: uuid.UUID | None,
    target_user_id: uuid.UUID | None,
    page: int,
    page_size: int,
) -> tuple[list[AuditLog], int]:
    stmt = select(AuditLog)
    count_stmt = select(func.count()).select_from(AuditLog)
    if event_type:
        stmt = stmt.where(AuditLog.event_type == event_type)
        count_stmt = count_stmt.where(AuditLog.event_type == event_type)
    if actor_user_id:
        stmt = stmt.where(AuditLog.actor_user_id == actor_user_id)
        count_stmt = count_stmt.where(AuditLog.actor_user_id == actor_user_id)
    if target_user_id:
        stmt = stmt.where(AuditLog.target_user_id == target_user_id)
        count_stmt = count_stmt.where(AuditLog.target_user_id == target_user_id)
    stmt = (
        stmt.order_by(AuditLog.created_at.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    items = list(db.execute(stmt).scalars().all())
    total = int(db.execute(count_stmt).scalar_one())
    return items, total
