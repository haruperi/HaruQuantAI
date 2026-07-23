"""Executable UTC clock and timestamp examples."""

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


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def fr_utils_010_utc_now() -> None:
    """FR-UTL-010: read and display the real current instant through UTC clock."""
    _header("Example 1: UTC Now")
    print("UTC instant:", utc_now())


def fr_utils_011_parse_format_timestamp() -> None:
    """FR-UTL-011: Round-trip a canonical UTC timestamp."""
    _header("Example 2: Parse Format Timestamp")
    value = datetime(2026, 1, 1, tzinfo=UTC)
    print("Timestamp:", parse_utc_timestamp(format_utc_timestamp(value)))


def fr_utils_012_age_and_freshness() -> None:
    """FR-UTL-012: Calculate exact age and inclusive freshness."""
    _header("Example 3: Age and Freshness")
    reference = datetime(2026, 1, 1, 0, 0, 2, tzinfo=UTC)
    observed = reference - timedelta(seconds=1)
    print(
        "Freshness:",
        {
            "age": str(age_seconds(observed, reference=reference)),
            "is_fresh": is_fresh(
                observed,
                reference=reference,
                max_age_seconds=Decimal(1),
            ),
        },
    )


def main() -> None:
    """Run all UTC-time examples."""
    fr_utils_010_utc_now()
    fr_utils_011_parse_format_timestamp()
    fr_utils_012_age_and_freshness()


if __name__ == "__main__":
    main()
