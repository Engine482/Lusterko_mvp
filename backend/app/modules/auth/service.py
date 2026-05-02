"""Auth orchestration: invite lifecycle, session lifecycle, login,
password reset.

Implements API Contracts §3 and Sprint 7 (Auth Pivot) per
`docs/06_decisions/2026-05-02-auth-email-password.md`. Audit hooks for
login_success/failed, logout, role_selected/switched, invite_used,
password_reset_requested/completed live here so callers in routes stay thin.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import Role
from app.core.cookies import INVITE_TTL, PASSWORD_RESET_TTL, SESSION_TTL
from app.core.security import (
    PasswordPolicyError,
    generate_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.auth_invite import AuthInvite
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.models.user_role import UserRole
from app.models.user_session import UserSession
from app.services.audit_logger import log_event


# --- Invite lifecycle --------------------------------------------------------


@dataclass(frozen=True)
class IssuedInvite:
    invite: AuthInvite
    token: str  # plaintext; show to admin once and forget


class AuthError(Exception):
    """Auth-domain error raised by the service. Routes translate `code` to a
    response envelope. Distinct from FastAPI's HTTPException so the service
    stays framework-agnostic."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def issue_invite(
    db: Session,
    *,
    user_id: uuid.UUID,
    created_by_user_id: uuid.UUID | None,
    now: datetime | None = None,
) -> IssuedInvite:
    now = now or datetime.now(timezone.utc)

    # Revoke any open invite for the same user — only one active invite at a time.
    open_invites = db.execute(
        select(AuthInvite).where(
            AuthInvite.user_id == user_id,
            AuthInvite.status == "pending",
        )
    ).scalars().all()
    for old in open_invites:
        old.status = "revoked"
        old.revoked_at = now

    token = generate_token()
    invite = AuthInvite(
        user_id=user_id,
        token_hash=hash_token(token),
        status="pending",
        expires_at=now + INVITE_TTL,
        created_by_user_id=created_by_user_id,
    )
    db.add(invite)
    db.flush()
    log_event(
        db,
        event_type="invite_created",
        actor_user_id=created_by_user_id,
        target_user_id=user_id,
        entity_type="auth_invites",
        entity_id=invite.id,
    )
    return IssuedInvite(invite=invite, token=token)


def validate_invite_token(
    db: Session,
    *,
    token: str,
    now: datetime | None = None,
) -> AuthInvite:
    now = now or datetime.now(timezone.utc)
    invite = db.execute(
        select(AuthInvite).where(AuthInvite.token_hash == hash_token(token))
    ).scalar_one_or_none()
    if invite is None:
        raise AuthError("INVALID_INVITE", "Invite not found.")
    if invite.status == "used":
        raise AuthError("INVALID_INVITE", "Invite already used.")
    if invite.status in {"revoked"}:
        raise AuthError("INVALID_INVITE", "Invite revoked.")
    if invite.expires_at <= now or invite.status == "expired":
        raise AuthError("INVITE_EXPIRED", "Invite expired.")
    return invite


def consume_invite(db: Session, invite: AuthInvite, *, now: datetime | None = None) -> None:
    now = now or datetime.now(timezone.utc)
    invite.status = "used"
    invite.used_at = now
    log_event(
        db,
        event_type="invite_used",
        target_user_id=invite.user_id,
        entity_type="auth_invites",
        entity_id=invite.id,
    )


# --- Login + invite acceptance ----------------------------------------------


def authenticate(
    db: Session,
    *,
    email: str,
    password: str,
) -> User:
    """Verify credentials. Raises `AuthError("UNAUTHORIZED")` for any failure
    mode (no user, wrong password, inactive user, no password set yet) so the
    response is identical and we don't leak user existence.

    The caller is responsible for auditing the failure with whatever metadata
    it has (IP, attempted email)."""

    user = db.execute(
        select(User).where(User.email == email.lower().strip())
    ).scalar_one_or_none()
    if user is None or user.status != "active":
        # Still hash a dummy password so the timing of "no user" matches
        # "wrong password" and we don't leak account existence via timing.
        verify_password(password, None)
        raise AuthError("UNAUTHORIZED", "Invalid email or password.")
    if not verify_password(password, user.password_hash):
        raise AuthError("UNAUTHORIZED", "Invalid email or password.")
    return user


def accept_invite(
    db: Session,
    *,
    token: str,
    full_name: str | None,
    password: str,
    now: datetime | None = None,
) -> User:
    """Validate invite, set the user's password (and optionally full_name),
    consume the invite. Returns the User row. Caller issues the session."""

    now = now or datetime.now(timezone.utc)
    invite = validate_invite_token(db, token=token, now=now)
    user = db.get(User, invite.user_id)
    if user is None or user.status != "active":
        raise AuthError("UNAUTHORIZED", "User is not active.")

    try:
        password_hash_value = hash_password(password)
    except PasswordPolicyError as err:
        raise AuthError("WEAK_PASSWORD", str(err)) from err

    user.password_hash = password_hash_value
    if full_name is not None and full_name.strip():
        user.full_name = full_name.strip()
    consume_invite(db, invite, now=now)
    return user


# --- Session lifecycle -------------------------------------------------------


@dataclass(frozen=True)
class IssuedSession:
    session: UserSession
    token: str  # plaintext for the cookie


def _user_roles(db: Session, user_id: uuid.UUID) -> list[Role]:
    rows = db.execute(select(UserRole.role).where(UserRole.user_id == user_id)).scalars().all()
    valid: set[Role] = {"soldier", "commander", "medic_psych", "admin"}
    return [r for r in rows if r in valid]


def create_session(
    db: Session,
    *,
    user: User,
    ip_address: str | None,
    user_agent: str | None,
    now: datetime | None = None,
) -> IssuedSession:
    now = now or datetime.now(timezone.utc)
    roles = _user_roles(db, user.id)
    if not roles:
        raise AuthError("FORBIDDEN", "User has no roles assigned.")

    role_selected = len(roles) == 1
    active_role: Role = roles[0]

    token = generate_token()
    session = UserSession(
        user_id=user.id,
        active_role=active_role,
        role_selected=role_selected,
        status="active",
        refresh_token_hash=hash_token(token),
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=now + SESSION_TTL,
        last_seen_at=now,
    )
    db.add(session)
    db.flush()
    log_event(
        db,
        event_type="login_success",
        actor_user_id=user.id,
        target_user_id=user.id,
        entity_type="user_sessions",
        entity_id=session.id,
        ip_address=ip_address,
        metadata={"active_role": active_role, "role_selected": role_selected},
    )
    return IssuedSession(session=session, token=token)


def select_role(
    db: Session,
    *,
    session: UserSession,
    user_id: uuid.UUID,
    desired_role: Role,
) -> None:
    roles = _user_roles(db, user_id)
    if desired_role not in roles:
        raise AuthError("INVALID_ACTIVE_ROLE", "Role is not assigned to user.")
    previous = session.active_role
    session.active_role = desired_role
    if not session.role_selected:
        session.role_selected = True
        log_event(
            db,
            event_type="role_selected",
            actor_user_id=user_id,
            target_user_id=user_id,
            entity_type="user_sessions",
            entity_id=session.id,
            metadata={"role": desired_role},
        )
    elif previous != desired_role:
        log_event(
            db,
            event_type="role_switched",
            actor_user_id=user_id,
            target_user_id=user_id,
            entity_type="user_sessions",
            entity_id=session.id,
            metadata={"from": previous, "to": desired_role},
        )


def refresh_session(
    db: Session,
    *,
    session: UserSession,
    now: datetime | None = None,
) -> None:
    now = now or datetime.now(timezone.utc)
    session.expires_at = now + SESSION_TTL
    session.last_seen_at = now


def revoke_session(
    db: Session,
    *,
    session: UserSession,
    actor_user_id: uuid.UUID,
    ip_address: str | None,
) -> None:
    session.status = "revoked"
    log_event(
        db,
        event_type="logout",
        actor_user_id=actor_user_id,
        target_user_id=actor_user_id,
        entity_type="user_sessions",
        entity_id=session.id,
        ip_address=ip_address,
    )


def revoke_all_sessions(db: Session, *, user_id: uuid.UUID) -> int:
    """Revoke every active session for a user. Used on password reset so
    stolen-credential reuse drops to zero across all devices."""

    sessions = db.execute(
        select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.status == "active",
        )
    ).scalars().all()
    for s in sessions:
        s.status = "revoked"
    return len(sessions)


# --- Password reset ----------------------------------------------------------


@dataclass(frozen=True)
class IssuedPasswordReset:
    reset: PasswordResetToken
    token: str  # plaintext for the email


def issue_password_reset(
    db: Session,
    *,
    user: User,
    now: datetime | None = None,
) -> IssuedPasswordReset:
    """Always create a fresh token; existing unconsumed ones for the same
    user are not revoked here — they will simply expire naturally. The login
    surface is the same regardless, and not revoking avoids a self-DoS if
    the user spam-clicks "forgot password"."""

    now = now or datetime.now(timezone.utc)
    token = generate_token()
    row = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_token(token),
        expires_at=now + PASSWORD_RESET_TTL,
    )
    db.add(row)
    db.flush()
    log_event(
        db,
        event_type="password_reset_requested",
        target_user_id=user.id,
        entity_type="password_reset_tokens",
        entity_id=row.id,
    )
    return IssuedPasswordReset(reset=row, token=token)


def validate_password_reset_token(
    db: Session,
    *,
    token: str,
    now: datetime | None = None,
) -> PasswordResetToken:
    now = now or datetime.now(timezone.utc)
    row = db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == hash_token(token)
        )
    ).scalar_one_or_none()
    if row is None:
        raise AuthError("INVALID_RESET_TOKEN", "Reset token not found.")
    if row.consumed_at is not None:
        raise AuthError("INVALID_RESET_TOKEN", "Reset token already used.")
    if row.expires_at <= now:
        raise AuthError("RESET_TOKEN_EXPIRED", "Reset token expired.")
    return row


def consume_password_reset(
    db: Session,
    *,
    reset_row: PasswordResetToken,
    new_password: str,
    now: datetime | None = None,
) -> User:
    """Set the new password, consume the token, revoke other sessions, audit.
    Returns the User. Caller issues a fresh session."""

    now = now or datetime.now(timezone.utc)
    user = db.get(User, reset_row.user_id)
    if user is None or user.status != "active":
        raise AuthError("UNAUTHORIZED", "User is not active.")

    try:
        user.password_hash = hash_password(new_password)
    except PasswordPolicyError as err:
        raise AuthError("WEAK_PASSWORD", str(err)) from err

    reset_row.consumed_at = now
    revoke_all_sessions(db, user_id=user.id)
    log_event(
        db,
        event_type="password_reset_completed",
        target_user_id=user.id,
        entity_type="password_reset_tokens",
        entity_id=reset_row.id,
    )
    return user
