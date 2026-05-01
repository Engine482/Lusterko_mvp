"""Auth orchestration: invite lifecycle + session lifecycle + login.

Implements API Contracts §3 and Backlog TASK-1001..1008. Audit hooks for
login_success/failed, logout, role_selected/switched, invite_used live here so
callers in routes stay thin.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import Role
from app.core.cookies import INVITE_TTL, SESSION_TTL
from app.core.security import generate_token, hash_token
from app.models.auth_invite import AuthInvite
from app.models.user import User
from app.models.user_identity import UserIdentity
from app.models.user_role import UserRole
from app.models.user_session import UserSession
from app.services.audit_logger import log_event


# --- Invite lifecycle --------------------------------------------------------


@dataclass(frozen=True)
class IssuedInvite:
    invite: AuthInvite
    token: str  # plaintext; show to admin once and forget


class InviteError(Exception):
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
        raise InviteError("INVALID_INVITE", "Invite not found.")
    if invite.status == "used":
        raise InviteError("INVALID_INVITE", "Invite already used.")
    if invite.status in {"revoked"}:
        raise InviteError("INVALID_INVITE", "Invite revoked.")
    if invite.expires_at <= now or invite.status == "expired":
        raise InviteError("INVITE_EXPIRED", "Invite expired.")
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
        raise InviteError("FORBIDDEN", "User has no roles assigned.")

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
        raise InviteError("INVALID_ACTIVE_ROLE", "Role is not assigned to user.")
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


# --- Identity bridge ---------------------------------------------------------


def get_or_create_google_identity(
    db: Session,
    *,
    user: User,
    provider_subject: str,
    email_at_provider: str,
) -> UserIdentity:
    identity = db.execute(
        select(UserIdentity).where(
            UserIdentity.provider == "google",
            UserIdentity.provider_subject == provider_subject,
        )
    ).scalar_one_or_none()
    if identity is None:
        identity = UserIdentity(
            user_id=user.id,
            provider="google",
            provider_subject=provider_subject,
            email_at_provider=email_at_provider,
        )
        db.add(identity)
        db.flush()
    return identity
