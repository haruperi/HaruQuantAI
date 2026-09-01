"""Injectable UTC clock boundary and timestamp utilities."""

from __future__ import annotations

from collections.abc import Callable, Mapping, MutableMapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Protocol

from app.kernel.errors import ValidationError


class Clock(Protocol):
    """Protocol for an injected clock."""

    def now(self) -> datetime:
        """Return the current aware UTC instant.

        Returns:
            An aware UTC datetime instant.
        """
        ...


class SystemClock:
    """System implementation of the UTC clock boundary."""

    def now(self) -> datetime:
        """Return the current aware UTC instant.

        Returns:
            An aware UTC datetime instant.
        """
        return datetime.now(UTC)


def utc_now(clock: Clock | None = None) -> datetime:
    """Return an aware UTC instant from an injected or system clock.

    Args:
        clock: Optional injected clock.

    Returns:
        An aware UTC datetime.

    Raises:
        ValidationError: If the clock returns a naive or non-UTC datetime.
    """
    current = (clock or SystemClock()).now()
    offset = current.utcoffset()
    if current.tzinfo is None or offset is None:
        raise ValidationError("CLOCK_VALUE_INVALID")
    if offset.total_seconds() != 0:
        raise ValidationError("CLOCK_VALUE_INVALID")
    return current


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
        True when age does not exceed max_age_seconds.

    Raises:
        ValidationError: If inputs are invalid or the age limit is negative.
    """
    if not max_age_seconds.is_finite() or max_age_seconds < Decimal(0):
        raise ValidationError("FRESHNESS_LIMIT_INVALID")
    return age_seconds(value, reference=reference) <= max_age_seconds


_DOMAINS = {
    "MARKET_EVENT",
    "BROKER_RECEIVE",
    "CLIENT_RECEIVE",
    "DISPLAY",
    "PLAYER_ACTION",
    "VENUE_ACCEPT",
    "FILL",
    "REPORT",
    "PROCESS",
}


def build_time_stamp(*, domain: str, instant: datetime) -> dict[str, str]:
    """Build an aware UTC TimeStamp v1 mapping.

    Args:
        domain: Closed time domain.
        instant: Aware UTC instant.

    Returns:
        TimeStamp v1 mapping.

    Raises:
        ValidationError: If evidence is invalid.
    """
    if (
        domain not in _DOMAINS
        or instant.tzinfo is None
        or instant.utcoffset() != UTC.utcoffset(instant)
    ):
        raise ValidationError("TIME_STAMP_INVALID")
    return {
        "contract_version": "v1",
        "schema_id": "utils.time_stamp.v1",
        "domain": domain,
        "instant": instant.isoformat().replace("+00:00", "Z"),
    }


def parse_time_stamp(value: Mapping[str, object]) -> dict[str, str]:
    """Strictly parse a TimeStamp v1 mapping.

    Args:
        value: Candidate mapping.

    Returns:
        Validated stamp.

    Raises:
        ValidationError: If validation fails.
    """
    if (
        set(value) != {"contract_version", "schema_id", "domain", "instant"}
        or value.get("contract_version") != "v1"
        or value.get("schema_id") != "utils.time_stamp.v1"
        or not isinstance(value.get("domain"), str)
        or not isinstance(value.get("instant"), str)
    ):
        raise ValidationError("TIME_STAMP_INVALID")
    instant = datetime.fromisoformat(str(value["instant"]))
    return build_time_stamp(domain=str(value["domain"]), instant=instant)


def compare_time_stamps(left: Mapping[str, object], right: Mapping[str, object]) -> int:
    """Compare stamps only within the same time domain.

    Args:
        left: Left stamp.
        right: Right stamp.

    Returns:
        Ordering value.

    Raises:
        ValidationError: If domains differ.
    """
    left_value, right_value = parse_time_stamp(left), parse_time_stamp(right)
    if left_value["domain"] != right_value["domain"]:
        raise ValidationError("TIME_DOMAIN_MISMATCH")
    return (left_value["instant"] > right_value["instant"]) - (
        left_value["instant"] < right_value["instant"]
    )


def to_venue_local(instant: datetime, zone_key: str) -> dict[str, str | int]:
    """Convert aware UTC time to caller-selected venue-local rendering.

    Args:
        instant: Aware UTC instant.
        zone_key: IANA zone key.

    Returns:
        Local and originating UTC evidence.

    Raises:
        ValidationError: If instant or zone is invalid.
    """
    if instant.tzinfo is None or instant.utcoffset() != UTC.utcoffset(instant):
        raise ValidationError("VENUE_TIME_INVALID")
    try:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        local = instant.astimezone(ZoneInfo(zone_key))
    except (ZoneInfoNotFoundError, Exception) as error:
        raise ValidationError("VENUE_ZONE_INVALID") from error
    return {
        "zone_key": zone_key,
        "local": local.isoformat(),
        "utc": instant.isoformat().replace("+00:00", "Z"),
        "fold": local.fold,
    }


def from_venue_local(
    local_value: str, zone_key: str, *, fold: int | None = None
) -> datetime:
    """Convert local wall time to UTC, requiring fold for ambiguity.

    Args:
        local_value: Naive local ISO timestamp.
        zone_key: IANA zone key.
        fold: Explicit ambiguity selection.

    Returns:
        Aware UTC instant.

    Raises:
        ValidationError: If conversion is ambiguous or invalid.
    """
    try:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        zone = ZoneInfo(zone_key)
        naive = datetime.fromisoformat(local_value)
    except (ValueError, ZoneInfoNotFoundError, Exception) as error:
        raise ValidationError("VENUE_TIME_INVALID") from error
    if naive.tzinfo is not None or fold not in {None, 0, 1}:
        raise ValidationError("VENUE_TIME_INVALID")
    first, second = (
        naive.replace(tzinfo=zone, fold=0),
        naive.replace(tzinfo=zone, fold=1),
    )
    if first.utcoffset() != second.utcoffset() and fold is None:
        raise ValidationError("VENUE_TIME_AMBIGUOUS")
    return naive.replace(tzinfo=zone, fold=fold or 0).astimezone(UTC)


def next_sequence(
    scope: str, counter: MutableMapping[str, int] | Callable[[str], int]
) -> int:
    """Allocate a strictly increasing sequence in a caller-owned scope.

    Args:
        scope: Non-empty caller scope.
        counter: Caller-owned mapping or allocator.

    Returns:
        Next monotonic sequence.

    Raises:
        ValidationError: If scope or counter output is invalid.
    """
    if not scope or scope != scope.strip():
        raise ValidationError("SEQUENCE_SCOPE_INVALID")
    if callable(counter):
        value = counter(scope)
        if isinstance(value, bool) or value < 0:
            raise ValidationError("SEQUENCE_VALUE_INVALID")
        return value
    previous = counter.get(scope, -1)
    if isinstance(previous, bool) or not isinstance(previous, int) or previous < -1:
        raise ValidationError("SEQUENCE_VALUE_INVALID")
    value = previous + 1
    counter[scope] = value
    return value
