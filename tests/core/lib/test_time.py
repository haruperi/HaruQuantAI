"""Unit tests for format_duration_seconds.

Description:
    Validates canonical duration formatting boundaries: seconds-only, minute-second,
    hour-minute, and day-hour-minute formats.

Purpose:
    FEAT-CORE-LIB: Validate core time utilities.

Key Capabilities:
    - FR-core-lib-format-duration: Test boundary durations.
"""

from __future__ import annotations

import logging

import pytest
from app.core.lib.time import format_duration_seconds


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
