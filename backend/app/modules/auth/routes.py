"""Auth API per `Lusterko_API_Contracts_v1.md` §3.

Implementation notes:
- `db` and `current_session_context` both depend on `get_db`; FastAPI caches
  sub-dependencies per request, so they share the same SQLAlchemy `Session`.
  That means `ctx.session` is already attached to the request's transaction
  and we can mutate it directly.
- All endpoints commit at the end. Errors short-circuit with a commit too so
  audit log entries always make it to disk.
"""

from __future__ import annotations

import ipaddress

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.core.api_response import error_response, success_response
from app.core.cookies import clear_session_cookie, set_session_cookie
from app.modules.auth import service as auth_service
from app.modules.auth.dependencies import (
    SessionContext,
    current_session_context,
    get_db,
    require_authenticated_session,
)
from app.modules.auth.google import (
    build_authorize_url,
    exchange_code_for_profile,
    is_stub_mode,
    stub_profile_for,
)
from app.models.user import User
from app.schemas.auth import (
    AuthMeResponse,
    GoogleStartResponse,
    LogoutResponse,
    RefreshResponse,
    SelectRoleRequest,
    SelectRoleResponse,
)
from app.schemas.common import UserBrief
from app.services.audit_logger import log_event

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str | None:
    if request.client is None:
        return None
    raw = request.client.host
    try:
        ipaddress.ip_address(raw)
    except ValueError:
        return None
    return raw


def _redirect_uri(request: Request) -> str:
    base = str(request.base_url).rstrip("/")
    return f"{base}/api/v1/auth/google/callback"


@router.get("/google/start")
def google_start(
    request: Request,
    invite_token: str = Query(..., min_length=10),
    db: Session = Depends(get_db),
) -> Response:
    try:
        auth_service.validate_invite_token(db, token=invite_token)
    except auth_service.InviteError as err:
        log_event(
            db,
            event_type="login_failed",
            metadata={"reason": err.code},
            ip_address=_client_ip(request),
        )
        db.commit()
        return error_response(err.code, err.message)  # type: ignore[arg-type]

    url = build_authorize_url(state=invite_token, redirect_uri=_redirect_uri(request))
    return success_response(GoogleStartResponse(redirect_url=url).model_dump())


@router.get("/google/callback")
def google_callback(
    request: Request,
    state: str = Query(...),
    code: str | None = Query(default=None),
    dev_stub: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> Response:
    try:
        invite = auth_service.validate_invite_token(db, token=state)
    except auth_service.InviteError as err:
        log_event(
            db,
            event_type="login_failed",
            metadata={"reason": err.code},
            ip_address=_client_ip(request),
        )
        db.commit()
        return error_response(err.code, err.message)  # type: ignore[arg-type]

    invited_user = db.get(User, invite.user_id)
    if invited_user is None or invited_user.status != "active":
        log_event(
            db,
            event_type="login_failed",
            target_user_id=invite.user_id,
            metadata={"reason": "user_inactive"},
            ip_address=_client_ip(request),
        )
        db.commit()
        return error_response("UNAUTHORIZED", "User is not active.")

    if dev_stub == 1 or is_stub_mode():
        profile = stub_profile_for(invited_user.email)
    else:
        if not code:
            return error_response("VALIDATION_ERROR", "Missing OAuth code.")
        try:
            profile = exchange_code_for_profile(
                code=code, redirect_uri=_redirect_uri(request)
            )
        except Exception as exc:  # pragma: no cover — exercised in prod
            log_event(
                db,
                event_type="login_failed",
                target_user_id=invited_user.id,
                metadata={"reason": "google_exchange_failed", "error": str(exc)[:200]},
                ip_address=_client_ip(request),
            )
            db.commit()
            return error_response("UNAUTHORIZED", "Google sign-in failed.")

    if profile.email.lower() != invited_user.email.lower():
        log_event(
            db,
            event_type="login_failed",
            target_user_id=invited_user.id,
            metadata={"reason": "email_mismatch"},
            ip_address=_client_ip(request),
        )
        db.commit()
        return error_response("UNAUTHORIZED", "Email does not match invite.")

    auth_service.get_or_create_google_identity(
        db,
        user=invited_user,
        provider_subject=profile.subject,
        email_at_provider=profile.email,
    )
    auth_service.consume_invite(db, invite)

    try:
        issued = auth_service.create_session(
            db,
            user=invited_user,
            ip_address=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    except auth_service.InviteError as err:
        db.commit()
        return error_response(err.code, err.message)  # type: ignore[arg-type]

    db.commit()
    response = success_response({"login": "ok"})
    set_session_cookie(response, issued.token)
    return response


@router.get("/me")
def get_me(
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(current_session_context),
) -> Response:
    db.commit()  # persist last_seen_at touch
    return success_response(
        AuthMeResponse(
            user=UserBrief.model_validate(ctx.user),
            roles=sorted(ctx.role_set),
            active_role=(ctx.role if ctx.session.role_selected else None),
            role_selection_required=not ctx.session.role_selected,
        ).model_dump(mode="json")
    )


@router.post("/select-role")
def select_role(
    payload: SelectRoleRequest,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(current_session_context),
) -> Response:
    try:
        auth_service.select_role(
            db,
            session=ctx.session,
            user_id=ctx.user.id,
            desired_role=payload.role,
        )
    except auth_service.InviteError as err:
        db.commit()
        return error_response(err.code, err.message)  # type: ignore[arg-type]
    db.commit()
    return success_response(SelectRoleResponse(active_role=payload.role).model_dump())


@router.post("/refresh")
def refresh(
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(current_session_context),
) -> Response:
    auth_service.refresh_session(db, session=ctx.session)
    db.commit()
    return success_response(RefreshResponse(refreshed=True).model_dump())


@router.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_authenticated_session),
) -> Response:
    auth_service.revoke_session(
        db,
        session=ctx.session,
        actor_user_id=ctx.user.id,
        ip_address=_client_ip(request),
    )
    db.commit()
    response = success_response(LogoutResponse(logged_out=True).model_dump())
    clear_session_cookie(response)
    return response
