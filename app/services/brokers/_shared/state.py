"""Shared redaction and validation for broker operational checkpoints."""

from __future__ import annotations

import hashlib
from decimal import Decimal, InvalidOperation

_MAX_TEXT_LENGTH = 256


def _text(value: str, field_name: str) -> str:
    """Return one bounded non-empty text value.

    Args:
        value: Candidate text.
        field_name: Stable field label.

    Returns:
        Stripped bounded text.

    Raises:
        ValueError: If the value is empty or exceeds the bound.
    """
    normalized = value.strip()
    if not normalized or len(normalized) > _MAX_TEXT_LENGTH:
        message = f"{field_name} must contain 1..256 characters"
        raise ValueError(message)
    return normalized


def _account_digest(account_reference: str) -> str:
    """Return a non-reversible digest for one account reference.

    Args:
        account_reference: Provider account reference.

    Returns:
        Lowercase SHA-256 digest.

    Raises:
        ValueError: If the reference is empty or unbounded.
    """
    normalized = _text(account_reference, "account_reference")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _optional_decimal(value: Decimal | str | None, field_name: str) -> str | None:
    """Normalize one optional finite non-negative decimal.

    Args:
        value: Candidate decimal value.
        field_name: Stable field label.

    Returns:
        Canonical decimal string or ``None``.

    Raises:
        ValueError: If the value is invalid, negative, or non-finite.
    """
    if value is None:
        return None
    try:
        normalized = Decimal(str(value))
    except InvalidOperation as error:
        message = f"{field_name} must be decimal-compatible"
        raise ValueError(message) from error
    if not normalized.is_finite() or normalized < 0:
        message = f"{field_name} must be finite and non-negative"
        raise ValueError(message)
    return str(normalized)
