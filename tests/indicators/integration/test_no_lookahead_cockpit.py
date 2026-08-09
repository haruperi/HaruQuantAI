from datetime import UTC, datetime, timedelta

from app.services.indicators import assert_closed_input, project_structural_levels


def test_future_cockpit_evidence_fails_closed() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    interval = assert_closed_input(
        source_start=now,
        source_end=now + timedelta(hours=1),
        available_at=now + timedelta(hours=1),
        decision_time=now,
        source_timeframe="H1",
        requested_timeframe="H1",
        max_age=timedelta(hours=1),
        complete=True,
    )
    levels = project_structural_levels(
        [
            {
                "kind": "resistance",
                "price": 2.0,
                "observed_at": now + timedelta(seconds=1),
                "invalidation_price": 3.0,
            }
        ],
        decision_time=now,
    )
    assert interval.status == "error"
    assert levels.error.code == "IND_LOOKAHEAD_RISK"
