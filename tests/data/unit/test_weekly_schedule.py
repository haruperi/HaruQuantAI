"""Tests for explicit revisioned weekly schedule expansion."""

from datetime import UTC, date, datetime, time

from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.time_sessions.contracts import (
    WeeklyHoliday,
    WeeklyScheduleDefinition,
)
from app.services.data.time_sessions.weekly_schedule import WeeklyScheduleProvider


def _unwrap(response):
    return unwrap_data_response(
        response,
        operation="data.time_sessions.test",
        request_id="req-00000000-0000-4000-8000-000000000000",
    )


def test_weekly_schedule_applies_holiday_closure_and_revision() -> None:
    provider = WeeklyScheduleProvider(
        WeeklyScheduleDefinition(
            source_id="broker-a",
            symbol="EURUSD",
            timezone="Europe/London",
            sessions={0: ((time(8), time(17)),)},
            effective_from=date(2026, 1, 1),
            holidays=(WeeklyHoliday(date=date(2026, 7, 20)),),
            revision="operator-v1",
        )
    )

    sessions = _unwrap(
        provider.get_sessions(
            start=datetime(2026, 7, 20, tzinfo=UTC),
            end=datetime(2026, 7, 21, tzinfo=UTC),
        )
    )

    assert sessions == ()


def test_weekly_schedule_normalizes_dst_regional_time_to_utc() -> None:
    provider = WeeklyScheduleProvider(
        WeeklyScheduleDefinition(
            source_id="broker-a",
            symbol="EURUSD",
            timezone="Europe/London",
            sessions={0: ((time(8), time(17)),)},
            effective_from=date(2026, 1, 1),
            revision="operator-v1",
        )
    )

    sessions = _unwrap(
        provider.get_sessions(
            start=datetime(2026, 7, 20, tzinfo=UTC),
            end=datetime(2026, 7, 21, tzinfo=UTC),
        )
    )

    assert len(sessions) == 1
    assert sessions[0].opens_at == datetime(2026, 7, 20, 7, tzinfo=UTC)
    assert sessions[0].closes_at == datetime(2026, 7, 20, 16, tzinfo=UTC)
    assert sessions[0].source.endswith("operator-v1")
