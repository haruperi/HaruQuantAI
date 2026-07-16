"""Caller-keyed Fernet authenticated symmetric encryption helpers."""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.utils.errors.exceptions import SecurityError


def generate_fernet_key() -> bytes:
    """Generate a URL-safe Fernet key using operating-system entropy.

    Returns:
        A URL-safe Fernet key as bytes.
    """
    return Fernet.generate_key()


def _fernet(key: bytes) -> Fernet:
    """Initialize a Fernet instance with a validation check.

    Args:
        key: Fernet key to validate and load.

    Returns:
        The validated Fernet instance.

    Raises:
        SecurityError: If the key is invalid.
    """
    if not isinstance(key, bytes):
        raise SecurityError("ENCRYPTION_KEY_INVALID")
    try:
        return Fernet(key)
    except (ValueError, TypeError):
        raise SecurityError("ENCRYPTION_KEY_INVALID") from None


def encrypt_text(value: str, key: bytes) -> str:
    """Encrypt non-empty UTF-8 text with a caller-supplied Fernet key.

    Args:
        value: Plaintext to encrypt.
        key: Valid Fernet key owned by the caller.

    Returns:
        URL-safe authenticated token as text.

    Raises:
        SecurityError: If the value or key is invalid.
    """
    if not isinstance(value, str) or not value:
        raise SecurityError("ENCRYPTION_VALUE_INVALID")
    return _fernet(key).encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_text(token: str, key: bytes) -> str:
    """Decrypt and authenticate a Fernet token with a caller-supplied key.

    Args:
        token: Fernet token returned by :func:`encrypt_text`.
        key: Matching Fernet key owned by the caller.

    Returns:
        Decrypted UTF-8 text.

    Raises:
        SecurityError: If the key or authenticated token is invalid.
    """
    if not isinstance(token, str) or not token:
        raise SecurityError("ENCRYPTION_TOKEN_INVALID")
    try:
        return _fernet(key).decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeDecodeError, UnicodeEncodeError):
        raise SecurityError("ENCRYPTION_TOKEN_INVALID") from None
