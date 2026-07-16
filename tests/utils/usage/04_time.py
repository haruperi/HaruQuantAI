"""Executable UTC time examples."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.utils import (
    age_seconds,
    format_utc_timestamp,
    is_fresh,
    parse_utc_timestamp,
    utc_now,
)


def example_utc_now() -> datetime:
    """Read the system UTC clock."""
    return utc_now()


def example_parse_format_timestamp() -> str:
    """Round-trip a canonical UTC timestamp."""
    value = datetime(2026, 1, 1, tzinfo=UTC)
    text = format_utc_timestamp(value)
    assert parse_utc_timestamp(text) == value
    return text


def example_age_and_freshness() -> Decimal:
    """Evaluate age against an explicit reference."""
    reference = datetime(2026, 1, 1, tzinfo=UTC)
    observed = reference - timedelta(seconds=2)
    age = age_seconds(observed, reference=reference)
    assert is_fresh(observed, reference=reference, max_age_seconds=Decimal(2))
    return age


def main() -> None:
    """Run all UTC time examples."""
    current = example_utc_now()
    canonical_timestamp = example_parse_format_timestamp()
    age = example_age_and_freshness()
    assert current.tzinfo is not None
    assert canonical_timestamp.endswith("Z")
    assert age == Decimal(2)
    print("Current UTC time:", format_utc_timestamp(current))
    print("Canonical timestamp:", canonical_timestamp)
    print("Age and freshness:", {"age_seconds": str(age), "is_fresh": True})


if __name__ == "__main__":
    main()
