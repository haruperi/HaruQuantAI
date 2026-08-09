"""Executable UTC clock and timestamp examples."""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils import (
    age_seconds,
    build_time_stamp,
    compare_time_stamps,
    format_utc_timestamp,
    from_venue_local,
    is_fresh,
    next_sequence,
    parse_time_stamp,
    parse_utc_timestamp,
    to_venue_local,
    utc_now,
)


def _feature_header(title: str) -> None:
    """Print feature title and module flow banner."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'-' * 88}\n{title}\n{'-' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def fr_utils_010_utc_now() -> None:
    """FR-UTL-010: Stage 1 — Read and display the real current instant through UTC clock."""
    _header("Stage 1: Clock Read - Real Current UTC Instant (FR-UTL-010)")
    now = utc_now()
    print(_format_result(now))
    print(f"Data -> utc_instant='{now.isoformat()}'")


def fr_utils_011_parse_format_timestamp() -> None:
    """FR-UTL-011: Stage 2 — Round-trip a canonical UTC timestamp."""
    _header("Stage 2: UTC Validation - Round-Trip Canonical Formatting (FR-UTL-011)")
    value = datetime(2026, 1, 1, tzinfo=UTC)
    formatted = format_utc_timestamp(value)
    parsed = parse_utc_timestamp(formatted)
    print(_format_result(parsed))
    print(f"Data -> formatted='{formatted}', parsed='{parsed.isoformat()}'")


def fr_utils_012_age_and_freshness() -> None:
    """FR-UTL-012: Stage 3 — Calculate exact age and inclusive freshness verdict."""
    _header(
        "Stage 3: Aware Instant / Freshness Verdict - Age and Freshness (FR-UTL-012)"
    )
    reference = datetime(2026, 1, 1, 0, 0, 2, tzinfo=UTC)
    observed = reference - timedelta(seconds=1)
    age = age_seconds(observed, reference=reference)
    fresh = is_fresh(observed, reference=reference, max_age_seconds=Decimal(1))
    print(_format_result(fresh))
    print(f"Data -> age_seconds={age}, is_fresh={fresh}")


def main() -> None:
    """Run all UTC-time examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-UTIL-03 — time/ — Aware UTC Time and Timestamp Utilities\n\n"
        "Purpose: Provide aware UTC clocks, canonical string serialization, and freshness calculations across all domains.\n\n"
        "Module flow:\n"
        "-> clock read / timestamp input\n"
        "-> UTC validation and calculation\n"
        "-> aware instant or freshness verdict"
    )

    # Stage 1: Clock read / timestamp input
    fr_utils_010_utc_now()

    # Stage 2: UTC validation and calculation
    fr_utils_011_parse_format_timestamp()

    # Stage 3: Aware instant or freshness verdict output
    fr_utils_012_age_and_freshness()
    instant = datetime(2026, 1, 1, tzinfo=UTC)
    stamp = build_time_stamp(domain="MARKET_EVENT", instant=instant)
    parsed = parse_time_stamp(stamp)
    assert compare_time_stamps(stamp, parsed) == 0
    local = to_venue_local(instant, "UTC")
    assert local["zone_key"] == "UTC"
    assert from_venue_local("2026-01-01T00:00:00", "UTC") == instant
    assert next_sequence("usage", {}) == 0


if __name__ == "__main__":
    main()
