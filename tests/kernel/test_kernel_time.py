"""Unit tests for kernel time, clock boundaries, and timestamps."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from app.kernel.errors import ValidationError
from app.kernel.time import (
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


class MockClock:
    """Mock clock for deterministic time injection."""

    def __init__(self, current: datetime) -> None:
        self._current = current

    def now(self) -> datetime:
        return self._current


def test_utc_now_returns_aware_utc() -> None:
    """Verify utc_now returns timezone-aware UTC datetime."""
    now = utc_now()
    assert now.tzinfo is not None
    assert now.utcoffset() == timedelta(0)


def test_utc_now_injected_clock_validation() -> None:
    """Verify utc_now validates injected clock output."""
    fixed = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)
    clock = MockClock(fixed)
    assert utc_now(clock) == fixed

    # Naive clock output raises error
    naive_clock = MockClock(datetime(2026, 9, 1, 12, 0, 0))  # noqa: DTZ001
    with pytest.raises(ValidationError):
        utc_now(naive_clock)

    # Non-UTC clock output raises error
    non_utc_clock = MockClock(
        datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=2)))
    )
    with pytest.raises(ValidationError):
        utc_now(non_utc_clock)


def test_format_and_parse_utc_timestamp() -> None:
    """Verify format and parse round-trip preserves microseconds and Z suffix."""
    now = datetime(2026, 9, 1, 12, 0, 0, 123456, tzinfo=UTC)
    formatted = format_utc_timestamp(now)
    assert formatted == "2026-09-01T12:00:00.123456Z"
    parsed = parse_utc_timestamp(formatted)
    assert parsed == now


def test_parse_invalid_timestamp() -> None:
    """Verify invalid or naive timestamps fail closed."""
    with pytest.raises(ValidationError, match="TIMESTAMP_INVALID"):
        parse_utc_timestamp("2026-09-01T12:00:00")
    with pytest.raises(ValidationError, match="TIMESTAMP_INVALID"):
        parse_utc_timestamp("invalid")
    with pytest.raises(ValidationError, match="TIMESTAMP_INVALID"):
        parse_utc_timestamp("")


def test_age_seconds_and_freshness() -> None:
    """Verify age calculation and freshness evaluation."""
    past = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)
    reference = datetime(2026, 9, 1, 12, 0, 10, tzinfo=UTC)
    age = age_seconds(past, reference=reference)
    assert age == Decimal(10)
    assert is_fresh(past, reference=reference, max_age_seconds=Decimal(15)) is True
    assert is_fresh(past, reference=reference, max_age_seconds=Decimal(5)) is False

    # Future timestamps raise error
    with pytest.raises(ValidationError):
        age_seconds(reference, reference=past)

    # Invalid freshness limits
    with pytest.raises(ValidationError):
        is_fresh(past, reference=reference, max_age_seconds=Decimal(-1))


def test_build_and_parse_time_stamp() -> None:
    """Verify build_time_stamp and parse_time_stamp validation."""
    now = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)
    stamp = build_time_stamp(domain="MARKET_EVENT", instant=now)
    assert stamp["domain"] == "MARKET_EVENT"
    assert stamp["instant"] == "2026-09-01T12:00:00Z"

    parsed = parse_time_stamp(stamp)
    assert parsed == stamp

    # Invalid domain
    with pytest.raises(ValidationError):
        build_time_stamp(domain="INVALID_DOMAIN", instant=now)

    # Invalid mapping
    with pytest.raises(ValidationError):
        parse_time_stamp({"invalid": "mapping"})


def test_compare_time_stamps() -> None:
    """Verify compare_time_stamps ordering and domain mismatch protection."""
    t1 = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)
    t2 = datetime(2026, 9, 1, 12, 0, 5, tzinfo=UTC)
    s1 = build_time_stamp(domain="FILL", instant=t1)
    s2 = build_time_stamp(domain="FILL", instant=t2)

    assert compare_time_stamps(s1, s2) == -1
    assert compare_time_stamps(s2, s1) == 1
    assert compare_time_stamps(s1, s1) == 0

    s3 = build_time_stamp(domain="REPORT", instant=t1)
    with pytest.raises(ValidationError):
        compare_time_stamps(s1, s3)


def test_to_and_from_venue_local() -> None:
    """Verify venue-local timezone conversions."""
    utc_dt = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)
    venue = to_venue_local(utc_dt, "America/New_York")
    assert venue["zone_key"] == "America/New_York"
    assert "local" in venue
    assert "utc" in venue

    # Invalid timezone
    with pytest.raises(ValidationError):
        to_venue_local(utc_dt, "Invalid/Zone")

    # from_venue_local takes naive ISO string
    naive_local_str = "2026-09-01T08:00:00"
    converted_back = from_venue_local(naive_local_str, "America/New_York")
    assert converted_back == utc_dt


def test_next_sequence() -> None:
    """Verify monotonic sequence allocation across scopes."""
    counter: dict[str, int] = {}
    assert next_sequence("orders", counter) == 0
    assert next_sequence("orders", counter) == 1
    assert next_sequence("trades", counter) == 0

    # Callable counter
    seq = 10

    def alloc(scope: str) -> int:
        nonlocal seq
        seq += 1
        return seq

    assert next_sequence("custom", alloc) == 11

    # Invalid scope or counter
    with pytest.raises(ValidationError):
        next_sequence("", counter)
    with pytest.raises(ValidationError):
        next_sequence("invalid_val", {"invalid_val": -5})
