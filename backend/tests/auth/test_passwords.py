"""Unit tests for `app.core.security.passwords` (argon2id).

TASK-7501. The module is small but security-critical, so we cover policy
enforcement, verify success/mismatch, the corruption path, and the
None-hash fast-path used by the login endpoint."""

from __future__ import annotations

import pytest

from app.core.security.passwords import (
    MIN_PASSWORD_LENGTH,
    PasswordPolicyError,
    hash_password,
    verify_password,
)


def test_hash_then_verify_roundtrip() -> None:
    h = hash_password("correct horse battery staple")
    assert h.startswith("$argon2id$")
    assert verify_password("correct horse battery staple", h) is True


def test_verify_rejects_wrong_password() -> None:
    h = hash_password("correct horse battery staple")
    assert verify_password("wrong horse battery staple", h) is False


def test_hash_rejects_short_password() -> None:
    with pytest.raises(PasswordPolicyError):
        hash_password("short")


def test_min_length_is_enforced_at_boundary() -> None:
    assert MIN_PASSWORD_LENGTH == 12
    with pytest.raises(PasswordPolicyError):
        hash_password("x" * (MIN_PASSWORD_LENGTH - 1))
    # exactly at boundary is allowed
    h = hash_password("x" * MIN_PASSWORD_LENGTH)
    assert verify_password("x" * MIN_PASSWORD_LENGTH, h) is True


def test_verify_handles_none_stored_hash() -> None:
    # Used by /login when the user row exists (invite created) but the
    # invitee has not set a password yet — must return False, not raise.
    assert verify_password("any password at all", None) is False
    assert verify_password("any password at all", "") is False


def test_verify_handles_corrupt_hash() -> None:
    assert verify_password("any password at all", "not-a-real-hash") is False


def test_two_hashes_of_same_password_differ() -> None:
    # argon2id uses a per-hash random salt; observing this protects against
    # a regression that pinned the salt.
    h1 = hash_password("correct horse battery staple")
    h2 = hash_password("correct horse battery staple")
    assert h1 != h2
    assert verify_password("correct horse battery staple", h1) is True
    assert verify_password("correct horse battery staple", h2) is True
