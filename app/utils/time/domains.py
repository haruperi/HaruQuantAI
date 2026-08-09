"""Typed time-domain stamps and lossless venue-local conversion."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.utils.errors.exceptions import ValidationError

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
        local = instant.astimezone(ZoneInfo(zone_key))
    except ZoneInfoNotFoundError as error:
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
        zone = ZoneInfo(zone_key)
        naive = datetime.fromisoformat(local_value)
    except (ValueError, ZoneInfoNotFoundError) as error:
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
