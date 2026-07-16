from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.utils import (
    ValidationError,
    age_seconds,
    format_utc_timestamp,
    is_fresh,
    parse_utc_timestamp,
)


def test_format_uses_canonical_z_suffix() -> None:
    value = datetime(2026, 1, 2, 3, 4, 5, 6, tzinfo=UTC)
    text = format_utc_timestamp(value)
    assert text == "2026-01-02T03:04:05.000006Z"
    assert parse_utc_timestamp(text) == value


def test_age_seconds_is_non_negative() -> None:
    current = datetime(2026, 1, 1, 0, 0, 2, tzinfo=UTC)
    observed = current - timedelta(seconds=1, microseconds=500_000)
    assert age_seconds(observed, reference=current) == Decimal("1.5")
    assert is_fresh(observed, reference=current, max_age_seconds=Decimal("1.5"))


def test_future_and_non_utc_timestamps_fail_closed() -> None:
    current = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(ValidationError):
        age_seconds(current + timedelta(seconds=1), reference=current)
    with pytest.raises(ValidationError):
        parse_utc_timestamp("2026-01-01T00:00:00+00:00")
    with pytest.raises(ValidationError):
        is_fresh(current, reference=current, max_age_seconds=Decimal(-1))
