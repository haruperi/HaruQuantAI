"""Verify record review behavior and negative gates."""

from dataclasses import replace
from typing import Any

from app.workspace.DataManager.Data.record_review import review_records


def test_pages_and_end_of_data(dataset):
    result = review_records(dataset, offset=1, count=10).unwrap()
    assert result.rows == (dataset.records[1],) and result.total_count == 2
    assert result.offset == 1
    assert review_records(dataset, offset=50).unwrap().rows == ()
    assert review_records(replace(dataset, records=())).unwrap().total_count == 0
    assert review_records(dataset, count=0).unwrap().rows == ()


def test_bounds_and_resampling_rejected(dataset):
    cases: list[dict[str, Any]] = [
        {"offset": -1},
        {"count": -1},
        {"count": 10_001},
        {"offset": True},
        {"count": 1.5},
    ]
    for kwargs in cases:
        assert review_records(dataset, **kwargs).error_code == "INVALID_BOUNDS"
    assert review_records(dataset, timeframe="H1").error_code == "UNSUPPORTED_TIMEFRAME"
    assert review_records(dataset, timeframe="M1").is_success
