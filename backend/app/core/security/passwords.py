"""argon2id password hashing for Sprint 7 email+password auth.

Decision: `docs/06_decisions/2026-05-02-auth-email-password.md`. Length-only
policy (≥12 chars) per NIST SP 800-63B; argon2id parameters follow OWASP
Password Storage Cheat Sheet defaults from `argon2-cffi`.

We never accept or return a plaintext password outside the request-handler
boundary. The hash is the only thing that ever lives in the database.
"""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHash,
    VerificationError,
    VerifyMismatchError,
)


MIN_PASSWORD_LENGTH = 12


class PasswordPolicyError(ValueError):
    """Raised when a candidate password violates the length policy.

    Endpoints translate this into a 400 with a stable error code so the
    frontend can render a localized message; we deliberately do not expose
    the raw message to the API consumer."""


# A single shared hasher instance — the parameters (memory, parallelism,
# iterations) are fixed at module import; rotating them would require a
# migration helper that re-hashes on next successful login.
_hasher = PasswordHasher()


def hash_password(plaintext: str) -> str:
    """Validate the policy and return an argon2id PHC-encoded hash."""

    if len(plaintext) < MIN_PASSWORD_LENGTH:
        raise PasswordPolicyError(
            f"password must be at least {MIN_PASSWORD_LENGTH} characters"
        )
    return _hasher.hash(plaintext)


def verify_password(plaintext: str, stored_hash: str | None) -> bool:
    """Constant-time argon2id verification.

    `stored_hash=None` is supported and always returns False — that maps to
    the "user has not set a password yet" case (created via invite, not
    accepted) without leaking the difference between "no such user" and
    "user with no password". Verification errors (mismatch, malformed hash)
    also return False rather than raising.
    """

    if not stored_hash:
        return False
    try:
        return _hasher.verify(stored_hash, plaintext)
    except (VerifyMismatchError, VerificationError, InvalidHash):
        return False
