"""Run real UTC clock and timestamp examples."""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils import (
    age_seconds,
    format_utc_timestamp,
    is_fresh,
    parse_utc_timestamp,
    utc_now,
)


def example_utc_now() -> datetime:
    """Read an aware UTC system-clock instant."""
    current = utc_now()
    assert current.tzinfo is UTC
    print("UTC now:", format_utc_timestamp(current))
    return current


def example_parse_format_timestamp() -> None:
    """Parse and format the canonical UTC representation."""
    parsed = parse_utc_timestamp("2026-07-14T10:30:00.000000Z")
    rendered = format_utc_timestamp(parsed)
    assert rendered == "2026-07-14T10:30:00.000000Z"
    print("Canonical timestamp:", rendered)


def example_age_and_freshness(reference: datetime) -> None:
    """Calculate real age and freshness against an explicit reference."""
    observed = reference - timedelta(seconds=5)
    assert age_seconds(observed, reference=reference) == Decimal(5)
    assert is_fresh(observed, reference=reference, max_age_seconds=Decimal(5))
    print("Age seconds: 5; fresh: True")


if __name__ == "__main__":
    now = example_utc_now()
    example_parse_format_timestamp()
    example_age_and_freshness(now)
