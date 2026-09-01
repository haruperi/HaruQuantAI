"""Unit tests for kernel time, clock boundaries, and timestamps."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.kernel.errors import ValidationError
from app.kernel.time import (
    age_seconds,
    format_utc_timestamp,
    is_fresh,
    parse_utc_timestamp,
    utc_now,
)


def test_utc_now_returns_aware_utc() -> None:
    """Verify utc_now returns timezone-aware UTC datetime."""
    now = utc_now()
    assert now.tzinfo is not None
    assert now.utcoffset() == timedelta(0)


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


def test_age_seconds_and_freshness() -> None:
    """Verify age calculation and freshness evaluation."""
    past = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)
    reference = datetime(2026, 9, 1, 12, 0, 10, tzinfo=UTC)
    age = age_seconds(past, reference=reference)
    assert age == Decimal(10)
    assert is_fresh(past, reference=reference, max_age_seconds=Decimal(15)) is True
    assert is_fresh(past, reference=reference, max_age_seconds=Decimal(5)) is False
