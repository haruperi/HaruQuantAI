"""Verify record correction behavior and negative gates."""

from dataclasses import replace
from typing import Any

from app.workspace.DataManager.Data.contracts import BarRecord, TickRecord
from app.workspace.DataManager.Data.record_correction import correct_records


def test_same_time_ticks_remain_individually_addressable(dataset):
    original = replace(
        dataset,
        timeframe="TICK",
        records=(TickRecord(10, 1, 2), TickRecord(10, 2, 3), TickRecord(20, 3, 4)),
    )
    updated = correct_records(
        original, replacements={1: TickRecord(10, 5, 6)}, deleted=(0,)
    ).unwrap()
    assert updated.records == (TickRecord(10, 5, 6), TickRecord(20, 3, 4))
    assert (updated.row_count, updated.date_from_ms, updated.date_to_ms) == (2, 10, 20)
    assert original.row_count == 3


def test_invalid_changes_never_modify_input(dataset):
    cases: list[tuple[dict[str, Any], str]] = [
        ({}, "NO_CHANGES"),
        ({"deleted": (-1,)}, "INVALID_INDEX"),
        ({"deleted": (2,)}, "INVALID_INDEX"),
        ({"deleted": (True,)}, "INVALID_INDEX"),
        ({"deleted": (0, 0)}, "CONFLICTING_CHANGES"),
        (
            {"replacements": {0: dataset.records[0]}, "deleted": (0,)},
            "CONFLICTING_CHANGES",
        ),
        ({"replacements": {0: TickRecord(0, 1, 2)}}, "RECORD_KIND_MISMATCH"),
        ({"replacements": {0: BarRecord(0, 10, 9, 11, 10)}}, "INVALID_OHLC"),
        ({"replacements": {0: BarRecord(120_000, 10, 11, 9, 10)}}, "UNORDERED_RECORDS"),
    ]
    for kwargs, code in cases:
        assert correct_records(dataset, **kwargs).error_code == code
    assert dataset.row_count == 2
    assert (
        correct_records(replace(dataset, restricted=True), deleted=(0,)).error_code
        == "RESTRICTED_DATASET"
    )


def test_delete_all_recalculates_empty_coverage(dataset):
    updated = correct_records(dataset, deleted=(0, 1)).unwrap()
    assert updated.records == () and updated.date_from_ms is None
