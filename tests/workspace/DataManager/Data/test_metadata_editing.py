"""Verify metadata editing behavior and rejection boundaries."""

from dataclasses import replace

from app.workspace.DataManager.Data.contracts import Catalog
from app.workspace.DataManager.Data.metadata_editing import (
    InstrumentFacts,
    edit_metadata,
)

FACTS = InstrumentFacts("EURUSD", "broker", "UTC")


def test_rename_preserves_identity_and_records(catalog, dataset):
    updated = edit_metadata(catalog, "fx", symbol="EURUSD_new", facts=FACTS).unwrap()
    assert updated.id == dataset.id and updated.records == dataset.records
    assert updated.symbol == "EURUSD_new" and dataset.symbol == "EURUSD"


def test_invalid_edits_are_explicit(catalog, dataset):
    assert (
        edit_metadata(catalog, "missing", symbol="X", facts=FACTS).error_code
        == "UNKNOWN_DATASET"
    )
    assert (
        edit_metadata(catalog, "fx", symbol="AAPL", facts=FACTS).error_code
        == "SYMBOL_CONFLICT"
    )
    assert (
        edit_metadata(catalog, "fx", symbol="bad name", facts=FACTS).error_code
        == "INVALID_METADATA"
    )
    assert (
        edit_metadata(
            catalog,
            "fx",
            symbol="X",
            facts=InstrumentFacts("EURUSD", "b", "Europe/London"),
        ).error_code
        == "BROKER_TIMEZONE_CONFLICT"
    )
    assert (
        edit_metadata(
            Catalog((replace(dataset, restricted=True),)), "fx", symbol="X", facts=FACTS
        ).error_code
        == "RESTRICTED_DATASET"
    )


def test_empty_dataset_can_change_broker_timezone(catalog):
    result = edit_metadata(
        catalog,
        "stock",
        symbol="APPLE",
        facts=InstrumentFacts("Apple", "ny", "America/New_York"),
    ).unwrap()
    assert result.timezone == "America/New_York"
    assert edit_metadata(
        catalog, "stock", symbol="APPLE", facts=InstrumentFacts("", "ny", "UTC")
    ).is_error
