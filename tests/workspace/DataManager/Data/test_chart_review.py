"""Verify chart review behavior and negative gates."""

from dataclasses import replace
from typing import Any

from app.workspace.DataManager.Data.chart_review import review_chart
from app.workspace.DataManager.Data.contracts import TickRecord


def test_bar_and_tick_projection(dataset):
    bars = review_chart(dataset, offset=1, count=1).unwrap()
    assert bars.columns == ("open", "high", "low", "close")
    assert bars.points[0].values == (10, 11, 9, 10) and bars.points[0].time_ms == 60_000
    assert bars.total_count == 2
    ticks = replace(dataset, timeframe="TICK", records=(TickRecord(0, 1, 2),))
    assert review_chart(ticks).unwrap().points[0].values == (1, 2)
    assert review_chart(ticks).unwrap().columns == ("bid", "ask")
    assert review_chart(dataset, count=0).unwrap().points == ()
    assert review_chart(dataset, offset=5).unwrap().points == ()


def test_invalid_chart_requests(dataset):
    cases: list[dict[str, Any]] = [
        {"offset": -1},
        {"count": -1},
        {"count": 10_001},
        {"offset": True},
        {"count": False},
    ]
    for kwargs in cases:
        assert review_chart(dataset, **kwargs).error_code == "INVALID_BOUNDS"
    assert review_chart(dataset, timeframe="H1").error_code == "UNSUPPORTED_TIMEFRAME"
