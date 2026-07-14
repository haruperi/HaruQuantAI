"""Versioned password hashing and constant-time verification."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import secrets

from app.utils.errors.exceptions import SecurityError

_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 600_000
_SALT_BYTES = 16
_MIN_PASSWORD_LENGTH = 12
_MAX_PASSWORD_LENGTH = 1_024


def _validate_password(password: str) -> bytes:
    if not isinstance(password, str):
        raise SecurityError("PASSWORD_INVALID")
    if not _MIN_PASSWORD_LENGTH <= len(password) <= _MAX_PASSWORD_LENGTH:
        raise SecurityError("PASSWORD_INVALID")
    return password.encode("utf-8")


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 and a fresh random salt.

    Args:
        password: Password containing 12 through 1,024 Unicode characters.

    Returns:
        Versioned encoded hash suitable for caller-owned persistence.

    Raises:
        SecurityError: If the password does not meet the input boundary.
    """
    password_bytes = _validate_password(password)
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password_bytes,
        salt,
        _ITERATIONS,
    )
    encoded_salt = base64.b64encode(salt).decode("ascii")
    encoded_digest = base64.b64encode(digest).decode("ascii")
    return f"{_ALGORITHM}${_ITERATIONS}${encoded_salt}${encoded_digest}"


def verify_password(password: str, encoded_hash: str) -> bool:
    """Verify a password against a versioned encoded hash.

    Args:
        password: Candidate password containing 12 through 1,024 characters.
        encoded_hash: Previously returned versioned hash.

    Returns:
        ``True`` only when the candidate matches. Malformed hashes return ``False``.

    Raises:
        SecurityError: If the password does not meet the input boundary.
    """
    password_bytes = _validate_password(password)
    if not isinstance(encoded_hash, str):
        return False
    try:
        algorithm, iterations_text, salt_text, digest_text = encoded_hash.split("$")
        if algorithm != _ALGORITHM or int(iterations_text) != _ITERATIONS:
            return False
        salt = base64.b64decode(salt_text, validate=True)
        expected = base64.b64decode(digest_text, validate=True)
    except (binascii.Error, ValueError, TypeError):
        return False
    if len(salt) != _SALT_BYTES or len(expected) != hashlib.sha256().digest_size:
        return False
    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password_bytes,
        salt,
        _ITERATIONS,
    )
    return hmac.compare_digest(actual, expected)
