"""Verify contracts behavior and rejection boundaries."""

from collections.abc import Callable
from dataclasses import FrozenInstanceError
from math import inf, nan
from typing import Any, cast

import pytest
from app.workspace.DataManager.Data.contracts import (
    BarRecord,
    Catalog,
    Dataset,
    TickRecord,
)


def test_immutable_records_and_coverage(dataset):
    assert dataset.row_count == 2
    assert (dataset.date_from_ms, dataset.date_to_ms) == (0, 60_000)
    with pytest.raises(FrozenInstanceError):
        dataset.symbol = "new"
    empty = Dataset("empty", "EMPTY", "EMPTY")
    assert (empty.date_from_ms, empty.date_to_ms) == (None, None)


@pytest.mark.parametrize("value", [inf, -inf, nan])
def test_non_finite_records_rejected(value):
    with pytest.raises(ValueError):
        TickRecord(0, value, 1)
    with pytest.raises(ValueError):
        BarRecord(0, 1, value, 0, 1)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"symbol": ""},
        {"symbol": "space name"},
        {"timeframe": "M2"},
        {"timezone": "EETUS"},
        {"instrument": ""},
        {"id": ""},
        {"parent_id": "fx"},
        {"visible": 1},
        {"restricted": 1},
        {"records": (TickRecord(0, 1, 2),)},
        {"records": (BarRecord(1, 1, 2, 0, 1), BarRecord(0, 1, 2, 0, 1))},
    ],
)
def test_invalid_dataset(kwargs):
    values: dict[str, Any] = {"id": "fx", "symbol": "EURUSD", "instrument": "EURUSD"}
    values.update(kwargs)
    with pytest.raises((ValueError, TypeError)):
        Dataset(**values)


def test_catalog_identity_and_parent_validation(dataset):
    for items in [
        (dataset, dataset),
        (dataset, Dataset("other", "EURUSD", "OTHER")),
        (Dataset("clone", "CLONE", "EURUSD", parent_id="missing"),),
    ]:
        with pytest.raises(ValueError):
            Catalog(items)
    clone = Dataset("clone", "CLONE", "EURUSD", parent_id="fx")
    assert Catalog((dataset, clone)).datasets[1] == clone
    with pytest.raises(ValueError):
        Catalog(
            (dataset, clone, Dataset("grand", "GRAND", "EURUSD", parent_id="clone"))
        )


def test_record_constraints():
    constructors: list[Callable[[], object]] = [
        lambda: TickRecord(True, 1, 2),
        lambda: BarRecord(True, 1, 2, 0, 1),
        lambda: TickRecord(0, 1, 2, -1),
        lambda: BarRecord(0, 1, 2, 0, 1, -1),
    ]
    for ctor in constructors:
        with pytest.raises(ValueError):
            ctor()
    with pytest.raises(TypeError):
        Catalog(cast("Any", []))
    with pytest.raises(TypeError):
        Dataset("x", "X", "X", groups=cast("Any", []))
    with pytest.raises(TypeError):
        Dataset("x", "X", "X", bar_convention=cast("Any", "start"))
