from datetime import UTC, datetime, timedelta

from app.services.indicators import assert_closed_input

NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)


def test_closed_input_accepts_causal_evidence_and_fails_closed() -> None:
    valid = assert_closed_input(
        source_start=NOW.replace(hour=11),
        source_end=NOW,
        available_at=NOW,
        decision_time=NOW,
        source_timeframe="H1",
        requested_timeframe="H4",
        max_age=timedelta(hours=1),
        complete=True,
    )
    assert valid.data is True

    unknown = assert_closed_input(
        source_start=NOW.replace(hour=11),
        source_end=NOW,
        available_at=None,
        decision_time=NOW,
        source_timeframe="H1",
        requested_timeframe="H4",
        max_age=timedelta(hours=1),
        complete=True,
    )
    assert unknown.error.code == "IND_INPUT_NOT_CLOSED"
