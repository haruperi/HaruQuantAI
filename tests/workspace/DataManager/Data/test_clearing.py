"""Verify clearing behavior and negative gates."""

from dataclasses import replace

import pytest
from app.workspace.DataManager.Data.clearing import clear_datasets
from app.workspace.DataManager.Data.contracts import Catalog


@pytest.mark.parametrize("count", [0, 1, 4, 5])
def test_clear_has_no_size_dependent_semantics(dataset, count):
    items = tuple(
        replace(dataset, id=str(i), symbol="FX" + str(i)) for i in range(count)
    )
    original = Catalog(items)
    result = clear_datasets(original, tuple(item.id for item in items)).unwrap()
    assert all(item.records == () for item in result.catalog.datasets)
    assert all(item.row_count == 2 for item in original.datasets)
    assert result.cleared_ids == tuple(item.id for item in items)


def test_clear_source_warning_uses_complete_catalog(dataset):
    clone = replace(dataset, id="clone", symbol="CLONE", parent_id="fx")
    catalog = Catalog((dataset, clone))
    assert clear_datasets(catalog, ("fx",)).error_code == "SOURCE_CONFIRMATION_REQUIRED"
    updated = clear_datasets(catalog, ("fx",), confirm_sources=True).unwrap().catalog
    assert updated.datasets[0].records == ()
    assert updated.datasets[1] == clone


def test_clear_batch_validation(dataset):
    catalog = Catalog(
        (dataset, replace(dataset, id="limited", symbol="LIMITED", restricted=True))
    )
    assert clear_datasets(catalog, ("fx", "limited")).error_code == "RESTRICTED_DATASET"
    assert clear_datasets(catalog, ("missing",)).error_code == "UNKNOWN_DATASET"
    assert clear_datasets(catalog, ("fx", "fx")).error_code == "DUPLICATE_SELECTION"
    assert dataset.row_count == 2
