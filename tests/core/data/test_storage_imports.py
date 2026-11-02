"""Test specifications for canonical market storage contracts and verify legacy include removal."""

from __future__ import annotations

import importlib

import app.core.data.market_storage as new_storage
import pyarrow as pa
import pytest


def test_canonical_storage_module_identity() -> None:
    """Verify that market storage matches schema and legacy bridge is removed."""
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("app.include.market_storage")

    assert new_storage.encode_frame is not None
    assert new_storage.scan_catalog is not None
    assert new_storage.TICK_SCHEMA is not None
    assert new_storage.M1_SCHEMA is not None
    assert new_storage.safe_component is not None
    assert new_storage.price_columns is not None
    assert new_storage.catalog_paths is not None

    # TICK_SCHEMA: DateTime: timestamp[us, UTC], Bid: int64, Ask: int64, Flags: uint16, Volume: uint64
    assert [(field.name, field.type) for field in new_storage.TICK_SCHEMA] == [
        ("DateTime", pa.timestamp("us", tz="UTC")),
        ("Bid", pa.int64()),
        ("Ask", pa.int64()),
        ("Flags", pa.uint16()),
        ("Volume", pa.uint64()),
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
