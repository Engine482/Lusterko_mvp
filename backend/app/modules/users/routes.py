"""Admin API per `Lusterko_API_Contracts_v1.md` §4.

All endpoints under `/api/v1/admin` require `active_role == 'admin'`
(`Lusterko_RBAC_Matrix_v1.md` §5.5). Audit logging is wired into the service
layer so route handlers stay thin.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.api_response import error_response, success_response
from app.core.config import get_settings
from app.modules.auth import service as auth_service
from app.modules.auth.dependencies import (
    SessionContext,
    get_db,
    require_role,
)
from app.modules.notifications import mailer as mailer_mod
from app.modules.users import service as users_service
from app.services.audit_logger import log_event
from app.schemas.admin import (
    AuditLogItem,
    AuditLogsListResponse,
    CreateUnitRequest,
    CreateUserRequest,
    InviteResponse,
    SetRolesRequest,
    StatusOnlyResponse,
    UnitsListResponse,
    UpdateUserRequest,
    UserResponse,
    UsersListResponse,
)
from app.schemas.common import UnitBrief, UserDetail

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_role("admin"))],
)


def _user_detail(db: Session, user_id: uuid.UUID) -> UserDetail:
    from app.models.user import User  # local to avoid circular import

    user = db.get(User, user_id)
    assert user is not None  # caller ensures existence
    return UserDetail(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        status=user.status,  # type: ignore[arg-type]
        unit_id=user.unit_id,
        roles=users_service.get_user_roles(db, user.id),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


# --- Users CRUD --------------------------------------------------------------


@router.post("/users")
def create_user(
    payload: CreateUserRequest,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("admin")),
) -> Response:
    try:
        user = users_service.create_user(
            db,
            actor_user_id=ctx.user.id,
            full_name=payload.full_name,
            email=str(payload.email),
            unit_id=payload.unit_id,
            roles=payload.roles,
        )
    except users_service.UserManagementError as err:
        db.rollback()
        return error_response(err.code, err.message)  # type: ignore[arg-type]
    db.commit()
    return success_response(
        UserResponse(user=_user_detail(db, user.id)).model_dump(mode="json"),
        http_status=201,
    )


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    unit_id: uuid.UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    role: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    _: SessionContext = Depends(require_role("admin")),
) -> Response:
    items, total = users_service.list_users(
        db,
        unit_id=unit_id,
        status=status,
        role=role,
        page=page,
        page_size=page_size,
    )
    payload = UsersListResponse(
        items=[_user_detail(db, u.id) for u in items],
        total=total,
        page=page,
        page_size=page_size,
    )
    return success_response(payload.model_dump(mode="json"))


@router.get("/users/{user_id}")
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: SessionContext = Depends(require_role("admin")),
) -> Response:
    from app.models.user import User

    user = db.get(User, user_id)
    if user is None:
        return error_response("NOT_FOUND", "User not found.")
    return success_response(
        UserResponse(user=_user_detail(db, user.id)).model_dump(mode="json")
    )


@router.patch("/users/{user_id}")
def update_user(
    user_id: uuid.UUID,
    payload: UpdateUserRequest,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("admin")),
) -> Response:
    try:
        users_service.update_user(
            db,
            actor_user_id=ctx.user.id,
            user_id=user_id,
            full_name=payload.full_name,
            unit_id=payload.unit_id,
        )
    except users_service.UserManagementError as err:
        db.rollback()
        return error_response(err.code, err.message)  # type: ignore[arg-type]
    db.commit()
    return success_response(
        UserResponse(user=_user_detail(db, user_id)).model_dump(mode="json")
    )


@router.put("/users/{user_id}/roles")
def set_roles(
    user_id: uuid.UUID,
    payload: SetRolesRequest,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("admin")),
) -> Response:
    try:
        users_service.set_user_roles(
            db,
            actor_user_id=ctx.user.id,
            user_id=user_id,
            roles=payload.roles,
        )
    except users_service.UserManagementError as err:
        db.rollback()
        return error_response(err.code, err.message)  # type: ignore[arg-type]
    db.commit()
    return success_response(
        UserResponse(user=_user_detail(db, user_id)).model_dump(mode="json")
    )


@router.post("/users/{user_id}/invite")
def issue_invite(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("admin")),
) -> Response:
    from app.models.user import User

    user = db.get(User, user_id)
    if user is None:
        return error_response("NOT_FOUND", "User not found.")
    if user.status != "active":
        return error_response("CONFLICT", "User is not active.")
    issued = auth_service.issue_invite(
        db, user_id=user.id, created_by_user_id=ctx.user.id
    )

    # TASK-6403 — best-effort delivery. The token in the response is the
    # source of truth; mail is just convenience. Failures are audited but do
    # not roll back the invite.
    invite_url = mailer_mod.build_invite_url(
        get_settings().app_public_base_url, issued.token
    )
    result = mailer_mod.get_mailer().send_invite(
        mailer_mod.InviteEmail(
            to_email=user.email,
            to_full_name=user.full_name,
            invite_url=invite_url,
            expires_at_iso=issued.invite.expires_at.isoformat(),
        )
    )
    log_event(
        db,
        event_type="invite_email_sent" if result.ok else "invite_email_failed",
        actor_user_id=ctx.user.id,
        target_user_id=user.id,
        entity_type="auth_invites",
        entity_id=issued.invite.id,
        metadata={"error": result.error} if result.error else None,
    )
    db.commit()
    return success_response(
        InviteResponse(
            invite_id=issued.invite.id,
            token=issued.token,
            expires_at=issued.invite.expires_at,
            status=issued.invite.status,  # type: ignore[arg-type]
        ).model_dump(mode="json")
    )


@router.post("/users/{user_id}/deactivate")
def deactivate(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("admin")),
) -> Response:
    try:
        user = users_service.deactivate_user(
            db, actor_user_id=ctx.user.id, user_id=user_id
        )
    except users_service.UserManagementError as err:
        db.rollback()
        return error_response(err.code, err.message)  # type: ignore[arg-type]
    db.commit()
    return success_response(
        StatusOnlyResponse(user_id=user.id, status=user.status).model_dump(mode="json")  # type: ignore[arg-type]
    )


@router.post("/users/{user_id}/reactivate")
def reactivate(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("admin")),
) -> Response:
    try:
        user = users_service.reactivate_user(
            db, actor_user_id=ctx.user.id, user_id=user_id
        )
    except users_service.UserManagementError as err:
        db.rollback()
        return error_response(err.code, err.message)  # type: ignore[arg-type]
    db.commit()
    return success_response(
        StatusOnlyResponse(user_id=user.id, status=user.status).model_dump(mode="json")  # type: ignore[arg-type]
    )


# --- Units -------------------------------------------------------------------


@router.get("/units")
def list_units(
    db: Session = Depends(get_db),
    _: SessionContext = Depends(require_role("admin")),
) -> Response:
    units = users_service.list_units(db)
    return success_response(
        UnitsListResponse(items=[UnitBrief.model_validate(u) for u in units]).model_dump(
            mode="json"
        )
    )


@router.post("/units")
def create_unit(
    payload: CreateUnitRequest,
    db: Session = Depends(get_db),
    _: SessionContext = Depends(require_role("admin")),
) -> Response:
    try:
        unit = users_service.create_unit(db, name=payload.name, code=payload.code)
    except users_service.UserManagementError as err:
        db.rollback()
        return error_response(err.code, err.message)  # type: ignore[arg-type]
    db.commit()
    return success_response(
        UnitBrief.model_validate(unit).model_dump(mode="json"),
        http_status=201,
    )


# --- Audit -------------------------------------------------------------------


@router.get("/audit-logs")
def get_audit_logs(
    db: Session = Depends(get_db),
    event_type: str | None = Query(default=None),
    actor_user_id: uuid.UUID | None = Query(default=None),
    target_user_id: uuid.UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    _: SessionContext = Depends(require_role("admin")),
) -> Response:
    items, total = users_service.list_audit_logs(
        db,
        event_type=event_type,
        actor_user_id=actor_user_id,
        target_user_id=target_user_id,
        page=page,
        page_size=page_size,
    )
    payload = AuditLogsListResponse(
        items=[AuditLogItem.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )
    return success_response(payload.model_dump(mode="json"))
