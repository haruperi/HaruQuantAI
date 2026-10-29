"""Test identity and schema specifications for canonical market storage contracts."""

from __future__ import annotations

import app.core.data.market_storage as new_storage
import app.include.market_storage as old_storage
import pyarrow as pa
import pytest


def test_canonical_storage_module_identity() -> None:
    """Verify that importing old and new market storage returns identical objects and matches schema."""
    assert old_storage.encode_frame is new_storage.encode_frame
    assert old_storage.scan_catalog is new_storage.scan_catalog
    assert old_storage.TICK_SCHEMA is new_storage.TICK_SCHEMA
    assert old_storage.M1_SCHEMA is new_storage.M1_SCHEMA
    assert old_storage.safe_component is new_storage.safe_component
    assert old_storage.price_columns is new_storage.price_columns
    assert old_storage.catalog_paths is new_storage.catalog_paths

    # TICK_SCHEMA: DateTime: timestamp[us, UTC], Bid: int64, Ask: int64, Flags: uint16
    assert [(field.name, field.type) for field in new_storage.TICK_SCHEMA] == [
        ("DateTime", pa.timestamp("us", tz="UTC")),
        ("Bid", pa.int64()),
        ("Ask", pa.int64()),
        ("Flags", pa.uint16()),
    ]

    # M1_SCHEMA: DateTime, Open, High, Low, Close, Volume with timestamp[us, UTC], four int64 prices and uint64 volume
    assert [(field.name, field.type) for field in new_storage.M1_SCHEMA] == [
        ("DateTime", pa.timestamp("us", tz="UTC")),
        ("Open", pa.int64()),
        ("High", pa.int64()),
        ("Low", pa.int64()),
        ("Close", pa.int64()),
        ("Volume", pa.uint64()),
    ]

    # safe_component validation
    assert new_storage.safe_component("EURUSD") == "EURUSD"
    with pytest.raises(ValueError, match="Use a safe alphanumeric source or symbol"):
        new_storage.safe_component("../EURUSD")
