"""Auth API per `Lusterko_API_Contracts_v1.md` §3 (Sprint 7 email+password).

Implementation notes:
- `db` and `current_session_context` both depend on `get_db`; FastAPI caches
  sub-dependencies per request, so they share the same SQLAlchemy `Session`.
  That means `ctx.session` is already attached to the request's transaction
  and we can mutate it directly.
- All endpoints commit at the end. Errors short-circuit with a commit too so
  audit log entries always make it to disk.
- `/password/forgot` is anti-enumeration: it always returns the same
  envelope, regardless of whether the email matched a user. The mailer is
  invoked only when there is a real active user.
"""

from __future__ import annotations

import ipaddress

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.api_response import error_response, success_response
from app.core.config import get_settings
from app.core.cookies import clear_session_cookie, set_session_cookie
from app.modules.auth import rate_limit as rl
from app.modules.auth import service as auth_service
from app.modules.auth.dependencies import (
    SessionContext,
    current_session_context,
    get_db,
    require_authenticated_session,
)
from app.modules.notifications import mailer as mailer_mod
from app.models.user import User
from app.schemas.auth import (
    AuthConfigResponse,
    AuthMeResponse,
    DemoRegisterConfirmRequest,
    DemoRegisterConfirmResponse,
    DemoRegisterStartRequest,
    DemoRegisterStartResponse,
    InviteAcceptRequest,
    InviteAcceptResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    PasswordChangeRequest,
    PasswordChangeResponse,
    PasswordForgotRequest,
    PasswordForgotResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    ProfileUpdateRequest,
    ProfileUpdateResponse,
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


# --- Login / invite-accept --------------------------------------------------


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> Response:
    ip = _client_ip(request)
    key = rl.login_key(ip=ip, email=payload.email)
    try:
        rl.check_lockout(db, key=key)
        user = auth_service.authenticate(
            db,
            email=payload.email,
            password=payload.password,
        )
    except auth_service.AuthError as err:
        if err.code != "ACCOUNT_LOCKED":
            rl.record_failure(db, key=key, ip_address=ip)
        log_event(
            db,
            event_type="login_failed",
            metadata={"email": payload.email, "reason": err.code},
            ip_address=ip,
        )
        db.commit()
        return error_response(err.code, err.message)  # type: ignore[arg-type]

    rl.record_success(db, key=key)
    try:
        issued = auth_service.create_session(
            db,
            user=user,
            ip_address=ip,
            user_agent=request.headers.get("user-agent"),
        )
    except auth_service.AuthError as err:
        db.commit()
        return error_response(err.code, err.message)  # type: ignore[arg-type]

    db.commit()
    response = success_response(LoginResponse(logged_in=True).model_dump())
    set_session_cookie(response, issued.token)
    return response


@router.post("/invite/accept")
def invite_accept(
    payload: InviteAcceptRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> Response:
    ip = _client_ip(request)
    key = rl.invite_accept_key(ip=ip)
    try:
        rl.check_lockout(db, key=key)
        user = auth_service.accept_invite(
            db,
            token=payload.token,
            full_name=payload.full_name,
            password=payload.password,
        )
    except auth_service.AuthError as err:
        # WEAK_PASSWORD is a UX hint, not a brute-force signal — don't count it.
        if err.code not in ("ACCOUNT_LOCKED", "WEAK_PASSWORD"):
            rl.record_failure(db, key=key, ip_address=ip)
        log_event(
            db,
            event_type="login_failed",
            metadata={"reason": err.code},
            ip_address=ip,
        )
        db.commit()
        return error_response(err.code, err.message)  # type: ignore[arg-type]

    rl.record_success(db, key=key)
    try:
        issued = auth_service.create_session(
            db,
            user=user,
            ip_address=ip,
            user_agent=request.headers.get("user-agent"),
        )
    except auth_service.AuthError as err:
        db.commit()
        return error_response(err.code, err.message)  # type: ignore[arg-type]

    db.commit()
    response = success_response(InviteAcceptResponse(accepted=True).model_dump())
    set_session_cookie(response, issued.token)
    return response


# --- Password reset ---------------------------------------------------------


@router.post("/password/forgot")
def password_forgot(
    payload: PasswordForgotRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> Response:
    """Anti-enumeration: same response shape whether the email matched or
    not. We do all real work inside the conditional so a missing email
    costs ~zero and timing differences stay below the noise floor.

    Rate-limited per (IP, email) to prevent reset-spam: 5/15min then a
    backoff lock. The lockout response intentionally still returns the
    generic envelope shape so it does not leak account existence."""

    ip = _client_ip(request)
    key = rl.password_forgot_key(ip=ip, email=payload.email)
    try:
        rl.check_lockout(db, key=key)
    except auth_service.AuthError:
        # Swallow lockout into the generic success envelope — anti-
        # enumeration trumps "tell user to slow down" here.
        db.commit()
        return success_response(PasswordForgotResponse(queued=True).model_dump())

    # Every call counts toward the rate-limit (success or not), so this
    # endpoint can't be used as a free-fire reset spammer.
    rl.record_failure(db, key=key, ip_address=ip)

    user = db.execute(
        select(User).where(User.email == payload.email.lower().strip())
    ).scalar_one_or_none()
    if user is not None and user.status == "active":
        issued = auth_service.issue_password_reset(db, user=user)
        reset_url = mailer_mod.build_password_reset_url(
            get_settings().app_public_base_url, issued.token
        )
        result = mailer_mod.get_mailer().send_password_reset(
            mailer_mod.PasswordResetEmail(
                to_email=user.email,
                to_full_name=user.full_name,
                reset_url=reset_url,
                expires_at_iso=issued.reset.expires_at.isoformat(),
            )
        )
        log_event(
            db,
            event_type=(
                "password_reset_email_sent" if result.ok
                else "password_reset_email_failed"
            ),
            target_user_id=user.id,
            entity_type="password_reset_tokens",
            entity_id=issued.reset.id,
            metadata={"error": result.error} if result.error else None,
        )

    db.commit()
    return success_response(PasswordForgotResponse(queued=True).model_dump())


@router.post("/password/reset")
def password_reset(
    payload: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> Response:
    ip = _client_ip(request)
    key = rl.password_reset_key(ip=ip)
    try:
        rl.check_lockout(db, key=key)
        reset_row = auth_service.validate_password_reset_token(db, token=payload.token)
        user = auth_service.consume_password_reset(
            db,
            reset_row=reset_row,
            new_password=payload.password,
        )
    except auth_service.AuthError as err:
        if err.code not in ("ACCOUNT_LOCKED", "WEAK_PASSWORD"):
            rl.record_failure(db, key=key, ip_address=ip)
        db.commit()
        return error_response(err.code, err.message)  # type: ignore[arg-type]

    rl.record_success(db, key=key)
    try:
        issued = auth_service.create_session(
            db,
            user=user,
            ip_address=ip,
            user_agent=request.headers.get("user-agent"),
        )
    except auth_service.AuthError as err:
        db.commit()
        return error_response(err.code, err.message)  # type: ignore[arg-type]

    db.commit()
    response = success_response(PasswordResetResponse(reset=True).model_dump())
    set_session_cookie(response, issued.token)
    return response


# --- Session management (unchanged shape, kept under same router) -----------


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
    except auth_service.AuthError as err:
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


# --- In-session profile / password change -----------------------------------


@router.post("/password/change")
def password_change(
    payload: PasswordChangeRequest,
    request: Request,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_authenticated_session),
) -> Response:
    """Change the password while logged in. Requires the current password to
    prevent session-takeover from updating credentials. Other devices get
    logged out; the current browser keeps its session."""

    ip = _client_ip(request)
    try:
        auth_service.change_password(
            db,
            user=ctx.user,
            current_session=ctx.session,
            current_password=payload.current_password,
            new_password=payload.new_password,
            ip_address=ip,
        )
    except auth_service.AuthError as err:
        db.commit()
        return error_response(err.code, err.message)  # type: ignore[arg-type]
    db.commit()
    return success_response(PasswordChangeResponse(changed=True).model_dump())


# --- Public config / demo open registration ---------------------------------


@router.get("/config")
def auth_config() -> Response:
    """Public flag for the frontend to render the registration entry-point.
    Lives under /auth so the existing API client already handles it."""

    settings = get_settings()
    return success_response(
        AuthConfigResponse(
            open_registration_enabled=settings.demo_open_registration,
        ).model_dump()
    )


@router.post("/demo/register/start")
def demo_register_start(
    payload: DemoRegisterStartRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> Response:
    """Begin open-demo registration. Anti-enumeration response shape (mirrors
    `/password/forgot`): the envelope is always the same, regardless of
    whether the email already belongs to an active user.

    Gated by `DEMO_OPEN_REGISTRATION` — when the flag is off this endpoint
    behaves as if registration is disabled and returns a generic envelope so
    a turned-off demo doesn't surface as a 4xx in CI/UI."""

    settings = get_settings()
    if not settings.demo_open_registration:
        return success_response(
            DemoRegisterStartResponse(queued=True).model_dump()
        )

    ip = _client_ip(request)
    key = rl.demo_register_start_key(ip=ip, email=payload.email)
    try:
        rl.check_lockout(db, key=key)
    except auth_service.AuthError:
        # Swallow lockouts into the generic envelope — same anti-enumeration
        # rationale as /password/forgot.
        db.commit()
        return success_response(
            DemoRegisterStartResponse(queued=True).model_dump()
        )

    rl.record_failure(db, key=key, ip_address=ip)

    if not auth_service.email_belongs_to_active_user(db, email=payload.email):
        issued = auth_service.start_demo_registration(db, email=payload.email)
        confirm_url = mailer_mod.build_demo_registration_url(
            settings.app_public_base_url, issued.token
        )
        result = mailer_mod.get_mailer().send_demo_registration(
            mailer_mod.DemoRegistrationEmail(
                to_email=issued.registration.email,
                confirm_url=confirm_url,
                expires_at_iso=issued.registration.expires_at.isoformat(),
            )
        )
        log_event(
            db,
            event_type=(
                "demo_registration_email_sent" if result.ok
                else "demo_registration_email_failed"
            ),
            entity_type="demo_registrations",
            entity_id=issued.registration.id,
            metadata={"error": result.error} if result.error else None,
        )

    db.commit()
    return success_response(DemoRegisterStartResponse(queued=True).model_dump())


@router.post("/demo/register/confirm")
def demo_register_confirm(
    payload: DemoRegisterConfirmRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> Response:
    """Finalize open-demo registration. Creates the user with three tester
    roles (soldier + commander + medic_psych) and issues a session so the
    tester lands logged in on the role-selection screen."""

    settings = get_settings()
    if not settings.demo_open_registration:
        return error_response(
            "DEMO_REGISTRATION_DISABLED",
            "Demo open registration is disabled.",
        )

    ip = _client_ip(request)
    key = rl.demo_register_confirm_key(ip=ip)
    try:
        rl.check_lockout(db, key=key)
        registration = auth_service.validate_demo_registration_token(
            db, token=payload.token
        )
        user = auth_service.complete_demo_registration(
            db,
            registration=registration,
            password=payload.password,
            full_name=payload.full_name,
        )
    except auth_service.AuthError as err:
        if err.code not in ("ACCOUNT_LOCKED", "WEAK_PASSWORD"):
            rl.record_failure(db, key=key, ip_address=ip)
        db.commit()
        return error_response(err.code, err.message)  # type: ignore[arg-type]

    rl.record_success(db, key=key)
    try:
        issued = auth_service.create_session(
            db,
            user=user,
            ip_address=ip,
            user_agent=request.headers.get("user-agent"),
        )
    except auth_service.AuthError as err:
        db.commit()
        return error_response(err.code, err.message)  # type: ignore[arg-type]

    db.commit()
    response = success_response(
        DemoRegisterConfirmResponse(registered=True).model_dump()
    )
    set_session_cookie(response, issued.token)
    return response


@router.patch("/me")
def update_me(
    payload: ProfileUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_authenticated_session),
) -> Response:
    """Update the user's own display name. Limited to fields the user can
    change about themselves; role/email changes stay in the admin module."""

    ip = _client_ip(request)
    try:
        auth_service.update_profile(
            db,
            user=ctx.user,
            full_name=payload.full_name,
            ip_address=ip,
        )
    except auth_service.AuthError as err:
        db.commit()
        return error_response(err.code, err.message)  # type: ignore[arg-type]
    db.commit()
    return success_response(
        ProfileUpdateResponse(user=UserBrief.model_validate(ctx.user)).model_dump(mode="json")
    )
