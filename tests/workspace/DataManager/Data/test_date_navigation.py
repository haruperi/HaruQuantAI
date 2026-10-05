"""Verify date navigation behavior and negative gates."""

from dataclasses import replace

from app.workspace.DataManager.Data.contracts import TickRecord
from app.workspace.DataManager.Data.date_navigation import find_date_index


def test_sparse_duplicates_and_boundaries(dataset):
    records = (TickRecord(10, 1, 2), TickRecord(10, 2, 3), TickRecord(1_000_000, 3, 4))
    ticks = replace(dataset, timeframe="TICK", records=records)
    for time, index in [(-1, 0), (10, 0), (11, 2), (1_000_000, 2), (1_000_001, 3)]:
        assert find_date_index(ticks, time).unwrap() == index
    assert find_date_index(replace(dataset, records=()), 0).unwrap() == 0


def test_invalid_timestamp(dataset):
    assert find_date_index(dataset, True).error_code == "INVALID_TIMESTAMP"
