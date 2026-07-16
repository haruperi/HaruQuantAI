"""Parse, format, and compare canonical aware UTC timestamps."""

from datetime import datetime, timedelta
from decimal import Decimal

from app.utils.errors.exceptions import ValidationError


def _validate_utc(value: datetime) -> datetime:
    """Validate an aware UTC datetime.

    Args:
        value: Candidate datetime.

    Returns:
        The unchanged validated datetime.

    Raises:
        ValidationError: The datetime is naive or not UTC.
    """
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValidationError("TIMESTAMP_NOT_UTC")
    return value


def parse_utc_timestamp(value: str) -> datetime:
    """Parse a canonical UTC timestamp with a ``Z`` suffix.

    Args:
        value: Trimmed ISO 8601 text ending in ``Z``.

    Returns:
        The represented aware UTC datetime.

    Raises:
        ValidationError: The input is empty, untrimmed, lacks ``Z``, or is not
            a valid timestamp.
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
        value: Aware UTC datetime to serialize.

    Returns:
        Canonical ISO 8601 text with microseconds and a ``Z`` suffix.

    Raises:
        ValidationError: The datetime is naive or not UTC.
    """
    return (
        _validate_utc(value)
        .isoformat(timespec="microseconds")
        .replace(
            "+00:00",
            "Z",
        )
    )


def age_seconds(value: datetime, *, reference: datetime) -> Decimal:
    """Calculate exact non-negative age against an explicit instant.

    Args:
        value: Observed aware UTC timestamp.
        reference: Aware UTC instant against which age is measured.

    Returns:
        Exact elapsed seconds as a finite ``Decimal``.

    Raises:
        ValidationError: Either datetime is not UTC or ``value`` is later than
            ``reference``.
    """
    delta = _validate_utc(reference) - _validate_utc(value)
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
        value: Observed aware UTC timestamp.
        reference: Aware UTC instant against which age is measured.
        max_age_seconds: Finite, non-negative inclusive freshness limit.

    Returns:
        ``True`` when age is less than or equal to the supplied limit.

    Raises:
        ValidationError: The limit is negative or non-finite, either datetime
            is not UTC, or ``value`` is in the future.
    """
    if not max_age_seconds.is_finite() or max_age_seconds < 0:
        raise ValidationError("FRESHNESS_LIMIT_INVALID")
    return age_seconds(value, reference=reference) <= max_age_seconds
