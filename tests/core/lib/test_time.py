"""Unit tests for format_duration_seconds and TimePeriod models."""

from __future__ import annotations

import logging

import pytest
from app.core.lib.time import (
    DAY_MILLIS,
    HOUR_MILLIS,
    MINUTE_MILLIS,
    SECOND_MILLIS,
    TimePeriod,
    format_duration_seconds,
)


def test_time_constants() -> None:
    """Verify canonical millisecond constants matching SQTime."""
    assert SECOND_MILLIS == 1_000
    assert MINUTE_MILLIS == 60_000
    assert HOUR_MILLIS == 3_600_000
    assert DAY_MILLIS == 86_400_000


def test_time_period_model_and_clone() -> None:
    """Verify TimePeriod defaults, attribute storage, and independent clone."""
    period = TimePeriod(from_ms=1000, to_ms=5000, value=42.5, name="p1", note="sample")
    assert period.from_ms == 1000
    assert period.to_ms == 5000
    assert period.value == 42.5
    assert period.name == "p1"
    assert period.note == "sample"

    cloned = period.clone()
    assert cloned is not period
    assert cloned.from_ms == 1000
    assert cloned.to_ms == 5000
    assert cloned.value == 42.5
    assert cloned.name == "p1"
    assert cloned.note == "sample"

    # Mutating original does not alter clone
    period.value = 99.9
    assert cloned.value == 42.5


def test_format_duration_boundaries() -> None:
    """Assert canonical duration formatting at key boundaries."""
    assert format_duration_seconds(0) == "0s"
    assert format_duration_seconds(59) == "59s"
    assert format_duration_seconds(60) == "1m 0s"
    assert format_duration_seconds(65) == "1m 5s"
    assert format_duration_seconds(3599) == "59m 59s"
    assert format_duration_seconds(3600) == "1h 0m"
    assert format_duration_seconds(3660) == "1h 1m"
    assert format_duration_seconds(86400) == "1d 0h 0m"
    assert format_duration_seconds(90060) == "1d 1h 1m"


def test_format_duration_negative_clamping(caplog: pytest.LogCaptureFixture) -> None:
    """Negative values clamp to 0s and log."""
    with caplog.at_level(logging.DEBUG):
        assert format_duration_seconds(-10) == "0s"
        assert any(
            "FR-core-lib-format-duration" in record.message for record in caplog.records
        )
