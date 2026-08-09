from datetime import UTC, datetime, timedelta

from app.services.indicators import assert_closed_input


def test_stale_input_is_visible_and_restricted() -> None:
    now = datetime(2026, 1, 1, 2, tzinfo=UTC)
    result = assert_closed_input(
        source_start=now - timedelta(hours=2),
        source_end=now - timedelta(hours=1),
        available_at=now - timedelta(hours=1),
        decision_time=now,
        source_timeframe="H1",
        requested_timeframe="H1",
        max_age=timedelta(minutes=30),
        complete=True,
    )
    assert result.error.code == "IND_STALE_INPUT"
