"""Canonical UTC timestamp parsing, formatting, and freshness."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from app.utils.errors.exceptions import ValidationError


def _validate_utc(value: datetime) -> datetime:
    """Validate that the datetime instance is timezone-aware and set to UTC.

    Args:
        value: Datetime object to validate.

    Returns:
        The validated aware UTC datetime.

    Raises:
        ValidationError: If the datetime is naive or not in UTC.
    """
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValidationError("TIMESTAMP_NOT_UTC")
    return value


def parse_utc_timestamp(value: str) -> datetime:
    """Parse a canonical UTC timestamp with a ``Z`` suffix.

    Args:
        value: Timestamp text.

    Returns:
        An aware UTC datetime.

    Raises:
        ValidationError: If the timestamp is malformed or non-UTC.
    """
    if not value or value != value.strip() or not value.endswith("Z"):
        raise ValidationError("TIMESTAMP_INVALID")
    try:
        parsed = datetime.fromisoformat(f"{value[:-1]}+00:00")
    except ValueError as error:
        raise ValidationError("TIMESTAMP_INVALID") from error
    return _validate_utc(parsed)


def format_utc_timestamp(value: datetime) -> str:
    """Format an aware UTC datetime with six fractional digits and ``Z``.

    Args:
        value: Aware UTC datetime.

    Returns:
        Canonical UTC timestamp text.

    Raises:
        ValidationError: If the datetime is naive or non-UTC.
    """
    validated = _validate_utc(value)
    return validated.isoformat(timespec="microseconds").replace("+00:00", "Z")


def age_seconds(value: datetime, *, reference: datetime) -> Decimal:
    """Calculate exact non-negative age against an explicit instant.

    Args:
        value: Observed UTC instant.
        reference: Explicit UTC reference instant.

    Returns:
        Exact non-negative age in seconds.

    Raises:
        ValidationError: If either instant is invalid or the value is future-dated.
    """
    observed = _validate_utc(value)
    current = _validate_utc(reference)
    delta = current - observed
    if delta < timedelta(0):
        raise ValidationError("TIMESTAMP_IN_FUTURE")
    whole_seconds = delta.days * 86_400 + delta.seconds
    return Decimal(whole_seconds) + Decimal(delta.microseconds) / Decimal(1_000_000)


def is_fresh(
    value: datetime,
    *,
    reference: datetime,
    max_age_seconds: Decimal,
) -> bool:
    """Evaluate freshness inclusively against an explicit age limit.

    Args:
        value: Observed UTC instant.
        reference: Explicit UTC reference instant.
        max_age_seconds: Inclusive maximum age.

    Returns:
        Whether the value is within the age limit.

    Raises:
        ValidationError: If the limit or either instant is invalid.
    """
    if not max_age_seconds.is_finite() or max_age_seconds < 0:
        raise ValidationError("FRESHNESS_LIMIT_INVALID")
    return age_seconds(value, reference=reference) <= max_age_seconds
