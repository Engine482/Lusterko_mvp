"""Token generation and hashing primitives.

We never store plaintext invite or session tokens — only their sha-256 hashes.
Plaintext is shown to the admin once (invite) or set as an HttpOnly cookie
(session) and then forgotten by the server.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets


TOKEN_BYTES = 32  # 256 bits


def generate_token() -> str:
    """Return a URL-safe random token (~43 chars, 256 bits of entropy)."""

    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(token: str) -> str:
    """Stable sha-256 hex digest used for DB equality lookups."""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def constant_time_eq(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)
