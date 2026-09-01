"""Memory-hard password hashing and verification for UI/API identities."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from typing import Final

from app.composition.logging import get_logger

logger = get_logger(__name__)

_ALGORITHM: Final = "scrypt"
_N: Final = 2**15
_R: Final = 8
_P: Final = 1
_SALT_BYTES: Final = 16
_KEY_BYTES: Final = 32
_MAX_MEMORY_BYTES: Final = 64 * 1024 * 1024
_MAX_PASSWORD_BYTES: Final = 1024


def _password_bytes(password: str) -> bytes:
    """Validate and encode one password without logging its contents.

    Args:
        password: Plaintext password held only for this operation.

    Returns:
        UTF-8 encoded password.

    Raises:
        ValueError: If the password is empty or unreasonably large.
    """
    if not password:
        raise ValueError("password must not be empty")
    encoded = password.encode("utf-8")
    if len(encoded) > _MAX_PASSWORD_BYTES:
        raise ValueError("password exceeds maximum encoded length")
    return encoded


def hash_password(password: str) -> str:
    """Hash one password with randomized standard-library scrypt.

    Args:
        password: Plaintext password held only during hashing.

    Returns:
        Versioned encoded scrypt record containing parameters, salt, and digest.

    Raises:
        ValueError: If the password is invalid or scrypt is unavailable.
    """
    logger.info("Hashing a new UI/API identity password")
    encoded = _password_bytes(password)
    salt = secrets.token_bytes(_SALT_BYTES)
    try:
        digest = hashlib.scrypt(
            encoded,
            salt=salt,
            n=_N,
            r=_R,
            p=_P,
            maxmem=_MAX_MEMORY_BYTES,
            dklen=_KEY_BYTES,
        )
    except ValueError as error:
        raise ValueError("approved password hashing is unavailable") from error
    salt_text = base64.urlsafe_b64encode(salt).decode("ascii")
    digest_text = base64.urlsafe_b64encode(digest).decode("ascii")
    return f"{_ALGORITHM}${_N}${_R}${_P}${salt_text}${digest_text}"


def _parse_encoded_hash(encoded_hash: str) -> tuple[int, int, int, bytes, bytes]:
    """Parse and validate an encoded scrypt record.

    Returns:
        Scrypt parameters, salt, and expected digest.

    Raises:
        ValueError: If the record uses unsupported syntax or parameters.
    """
    algorithm, n_text, r_text, p_text, salt_text, digest_text = encoded_hash.split(
        "$", maxsplit=5
    )
    if algorithm != _ALGORITHM:
        raise ValueError("unsupported password hashing algorithm")
    n = int(n_text)
    r = int(r_text)
    p = int(p_text)
    if (n, r, p) != (_N, _R, _P):
        raise ValueError("unsupported password hashing parameters")
    salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
    expected = base64.urlsafe_b64decode(digest_text.encode("ascii"))
    return n, r, p, salt, expected


def verify_password(password: str, encoded_hash: str) -> bool:
    """Verify one password against an encoded scrypt record.

    Args:
        password: Candidate plaintext password.
        encoded_hash: Stored versioned scrypt record.

    Returns:
        Whether the candidate matches the stored record.

    Raises:
        ValueError: If either input or the stored record is malformed.
    """
    logger.info("Verifying a UI/API identity password")
    encoded = _password_bytes(password)
    try:
        n, r, p, salt, expected = _parse_encoded_hash(encoded_hash)
    except (UnicodeError, ValueError) as error:
        raise ValueError("stored password hash is malformed") from error
    actual = hashlib.scrypt(
        encoded,
        salt=salt,
        n=n,
        r=r,
        p=p,
        maxmem=_MAX_MEMORY_BYTES,
        dklen=len(expected),
    )
    return hmac.compare_digest(actual, expected)


__all__ = ("hash_password", "verify_password")
