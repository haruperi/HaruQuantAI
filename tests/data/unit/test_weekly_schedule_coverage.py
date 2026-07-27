"""
Unit tests for app/services/data/time_sessions/weekly_schedule.py to reach >80% coverage.
"""

from datetime import UTC, date, datetime, time, timedelta

import pytest
from app.services.data.contracts import DataError
from app.services.data.time_sessions.contracts import (
    WeeklyHoliday,
    WeeklyScheduleDefinition,
)
from app.services.data.time_sessions.weekly_schedule import WeeklyScheduleProvider

_REQ_ID = "req-11111111-1111-4111-8111-111111111111"
_NOW = datetime.now(UTC)


def _make_definition(**kwargs) -> WeeklyScheduleDefinition:
    defaults = {
        "source_id": "mt5",
        "symbol": "EURUSD",
        "timezone": "UTC",
        "revision": "v1",
        "effective_from": date(2020, 1, 1),
        "effective_to": date(2030, 12, 31),
        "sessions": {
            0: ((time(0, 0), time(23, 59)),),  # Monday
            1: ((time(0, 0), time(23, 59)),),  # Tuesday
        },
        "holidays": (
            WeeklyHoliday(
                date=date(2026, 1, 1),
                opens_at=None,
                closes_at=None,
            ),
            WeeklyHoliday(
                date=date(2026, 7, 4),
                opens_at=time(8, 0),
                closes_at=time(12, 0),
            ),
        ),
    }
    defaults.update(kwargs)
    return WeeklyScheduleDefinition(**defaults)


def test_get_sessions_invalid_range() -> None:
    """Test get_sessions raises INVALID_INPUT when start >= end or naive."""
    provider = WeeklyScheduleProvider(_make_definition())
    with pytest.raises(DataError) as exc_info:
        provider.get_sessions(start=_NOW, end=_NOW - timedelta(hours=1))
    assert exc_info.value.code == "INVALID_INPUT"

    with pytest.raises(DataError) as exc_info:
        provider.get_sessions(start=datetime.now(UTC), end=_NOW)
    assert exc_info.value.code == "INVALID_INPUT"


def test_get_sessions_invalid_timezone() -> None:
    """Test get_sessions raises INVALID_INPUT when definition timezone is invalid."""
    defl = _make_definition(timezone="Invalid/Timezone_123")
    provider = WeeklyScheduleProvider(defl)
    with pytest.raises(DataError) as exc_info:
        provider.get_sessions(start=_NOW - timedelta(days=1), end=_NOW)
    assert exc_info.value.code == "INVALID_INPUT"


def test_get_schedule_identity_mismatch() -> None:
    """Test get_schedule raises INVALID_INPUT when requested identity differs."""
    provider = WeeklyScheduleProvider(_make_definition())
    with pytest.raises(DataError) as exc_info:
        provider.get_schedule(
            source_id="wrong_source",
            symbol="EURUSD",
            timezone="UTC",
            observed_at=_NOW,
            request_id=_REQ_ID,
        )
    assert exc_info.value.code == "INVALID_INPUT"


def test_sessions_outside_effective_dates() -> None:
    """Test sessions for dates before effective_from or after effective_to."""
    defl = _make_definition(
        effective_from=date(2026, 1, 1),
        effective_to=date(2026, 12, 31),
    )
    provider = WeeklyScheduleProvider(defl)
    sessions_early = provider.get_sessions(
        start=datetime(2025, 1, 1, tzinfo=UTC),
        end=datetime(2025, 1, 2, tzinfo=UTC),
    )
    assert len(sessions_early) == 0


def test_sessions_with_holidays() -> None:
    """Test get_sessions with full-day and partial-day holidays."""
    provider = WeeklyScheduleProvider(_make_definition())
    # Full-day holiday on 2026-01-01 (Thursday)
    sessions_holiday = provider.get_sessions(
        start=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
        end=datetime(2026, 1, 1, 23, 59, tzinfo=UTC),
    )
    assert len(sessions_holiday) == 0

    # Half-day holiday on 2026-07-04 (Saturday)
    sessions_half = provider.get_sessions(
        start=datetime(2026, 7, 4, 0, 0, tzinfo=UTC),
        end=datetime(2026, 7, 4, 23, 59, tzinfo=UTC),
    )
    assert len(sessions_half) == 1
    assert sessions_half[0].opens_at == datetime(2026, 7, 4, 8, 0, tzinfo=UTC)
