"""Verify removal behavior and negative gates."""

from dataclasses import replace

import pytest
from app.workspace.DataManager.Data.contracts import Catalog
from app.workspace.DataManager.Data.removal import remove_datasets


@pytest.mark.parametrize("count", [0, 1, 4, 5])
def test_remove_explicit_selection_only(dataset, count):
    items = tuple(
        replace(dataset, id=str(i), symbol="FX" + str(i)) for i in range(count)
    )
    original = Catalog(items)
    result = remove_datasets(original, tuple(item.id for item in items)).unwrap()
    assert result.catalog.datasets == ()
    assert original.datasets == items


def test_remove_requires_explicit_dependents_and_confirmation(dataset):
    clone = replace(dataset, id="clone", symbol="CLONE", parent_id="fx")
    catalog = Catalog((dataset, clone))
    assert (
        remove_datasets(catalog, ("fx",)).error_code == "SOURCE_CONFIRMATION_REQUIRED"
    )
    assert (
        remove_datasets(catalog, ("fx",), confirm_sources=True).error_code
        == "DEPENDENTS_REMAIN"
    )
    assert (
        remove_datasets(catalog, ("fx", "clone"), confirm_sources=True)
        .unwrap()
        .catalog.datasets
        == ()
    )
    assert remove_datasets(catalog, ("clone",)).unwrap().catalog.datasets == (dataset,)


def test_remove_batch_is_atomic(dataset):
    catalog = Catalog(
        (dataset, replace(dataset, id="limited", symbol="LIMITED", restricted=True))
    )
    for ids, code in [
        (("fx", "limited"), "RESTRICTED_DATASET"),
        (("missing",), "UNKNOWN_DATASET"),
        (("fx", "fx"), "DUPLICATE_SELECTION"),
    ]:
        assert remove_datasets(catalog, ids).error_code == code
    assert len(catalog.datasets) == 2
