"""Verify host-owned normalized watchlist schema installation and operations.

Description:
    Tests schema creation idempotency, table definitions, relational constraints,
    and CRUD operations for watchlists and watchlist_items in isolated databases.
Purpose:
    FEAT-HOST-PERSISTENCE: Maintain host schema and transaction authority.
Key Capabilities:
    - FR-host-watchlist-schema: Install additive watchlists and watchlist items
      tables and reject incompatible existing definitions; isolated tests verify logs.
Python API Usage:
    response = HostPersistence(path).ensure_watchlists_schema()
CLI Usage:
    uv run python -m pytest tests/core/host/test_watchlist_schema.py --no-cov
"""

from __future__ import annotations

import logging
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from app.core.host.persistence import HostPersistence


@pytest.fixture
def gateway(tmp_path: Path) -> HostPersistence:
    """Provide an isolated host persistence gateway with an initialized database file."""
    path = tmp_path / "host.db"
    path.touch()
    return HostPersistence(path)


def test_watchlist_schema_is_idempotent_and_logs(
    gateway: HostPersistence, caplog: pytest.LogCaptureFixture
) -> None:
    """Ensure watchlist schema installs atomically, idempotently, and logs capability."""
    caplog.set_level(logging.INFO)

    first_install = gateway.ensure_watchlists_schema()
    assert first_install["success"]
    assert "FR-host-watchlist-schema: verified" in caplog.text

    second_install = gateway.ensure_watchlists_schema()
    assert second_install["success"]


def test_watchlist_crud_operations(gateway: HostPersistence) -> None:
    """Ensure CRUD operations work seamlessly on watchlists and watchlist_items."""
    assert gateway.ensure_watchlists_schema()["success"]

    # Create parent watchlist
    wl_result = gateway.create_records(
        "watchlists",
        {
            "name": "Crypto Breakouts",
            "description": "High volatility crypto pairs",
            "is_default": 1,
            "sort_order": 0,
            "color": "#10B981",
            "created_at_utc": "2026-11-01T12:00:00Z",
            "updated_at_utc": "2026-11-01T12:00:00Z",
        },
    )
    assert wl_result["success"]
    watchlist_id = wl_result["data"]["records"][0]["id"]

    # Create child watchlist items
    item1 = gateway.create_records(
        "watchlist_items",
        {
            "watchlist_id": watchlist_id,
            "symbol": "BTCUSD",
            "asset_class": "Crypto",
            "exchange": "BINANCE",
            "broker": "MT5",
            "default_timeframe": "H1",
            "sort_order": 0,
            "target_price_high": 105000.0,
            "target_price_low": 95000.0,
            "alert_rules_json": '{"rsi_below": 30}',
            "notes": "Key resistance retest",
            "is_active": 1,
            "created_at_utc": "2026-11-01T12:00:00Z",
            "updated_at_utc": "2026-11-01T12:00:00Z",
        },
    )
    assert item1["success"]
    item_id = item1["data"]["records"][0]["id"]

    # Read items
    items_read = gateway.read_records(
        "watchlist_items", filters={"watchlist_id": watchlist_id}
    )
    assert items_read["success"]
    assert len(items_read["data"]["records"]) == 1
    record = items_read["data"]["records"][0]
    assert record["symbol"] == "BTCUSD"
    assert record["target_price_high"] == 105000.0

    # Update item
    update_result = gateway.update_record(
        "watchlist_items",
        {"target_price_high": 110000.0, "notes": "Target raised"},
        filters={"id": item_id},
    )
    assert update_result["success"]
    assert update_result["data"]["records"][0]["target_price_high"] == 110000.0
    assert update_result["data"]["records"][0]["notes"] == "Target raised"


def test_watchlist_unique_constraints(gateway: HostPersistence) -> None:
    """Ensure duplicate watchlist names and duplicate (watchlist, symbol, broker) fail."""
    assert gateway.ensure_watchlists_schema()["success"]

    first = gateway.create_records(
        "watchlists",
        {
            "name": "Equities",
            "created_at_utc": "2026-11-01T12:00:00Z",
            "updated_at_utc": "2026-11-01T12:00:00Z",
        },
    )
    assert first["success"]
    watchlist_id = first["data"]["records"][0]["id"]

    # Duplicate name should fail
    duplicate_wl = gateway.create_records(
        "watchlists",
        {
            "name": "Equities",
            "created_at_utc": "2026-11-01T12:00:00Z",
            "updated_at_utc": "2026-11-01T12:00:00Z",
        },
    )
    assert not duplicate_wl["success"]

    # Add item
    item = gateway.create_records(
        "watchlist_items",
        {
            "watchlist_id": watchlist_id,
            "symbol": "AAPL",
            "broker": "Alpaca",
            "created_at_utc": "2026-11-01T12:00:00Z",
            "updated_at_utc": "2026-11-01T12:00:00Z",
        },
    )
    assert item["success"]

    # Duplicate (watchlist_id, symbol, broker) should fail
    duplicate_item = gateway.create_records(
        "watchlist_items",
        {
            "watchlist_id": watchlist_id,
            "symbol": "AAPL",
            "broker": "Alpaca",
            "created_at_utc": "2026-11-01T12:00:00Z",
            "updated_at_utc": "2026-11-01T12:00:00Z",
        },
    )
    assert not duplicate_item["success"]


def test_watchlist_foreign_key_guard(gateway: HostPersistence) -> None:
    """Ensure foreign key violations and reference guards are enforced."""
    assert gateway.ensure_watchlists_schema()["success"]

    # Inserting item referencing non-existent watchlist should fail
    orphan = gateway.create_records(
        "watchlist_items",
        {
            "watchlist_id": 99999,
            "symbol": "EURUSD",
            "created_at_utc": "2026-11-01T12:00:00Z",
            "updated_at_utc": "2026-11-01T12:00:00Z",
        },
    )
    assert not orphan["success"]

    # Create parent and child
    wl = gateway.create_records(
        "watchlists",
        {
            "name": "FX",
            "created_at_utc": "2026-11-01T12:00:00Z",
            "updated_at_utc": "2026-11-01T12:00:00Z",
        },
    )
    wl_id = wl["data"]["records"][0]["id"]
    item = gateway.create_records(
        "watchlist_items",
        {
            "watchlist_id": wl_id,
            "symbol": "EURUSD",
            "created_at_utc": "2026-11-01T12:00:00Z",
            "updated_at_utc": "2026-11-01T12:00:00Z",
        },
    )
    assert item["success"]
    item_id = item["data"]["records"][0]["id"]

    # Attempting to delete parent while child exists is guarded
    del_parent = gateway.delete_record("watchlists", filters={"id": wl_id})
    assert not del_parent["success"]

    # Deleting child first allows parent deletion
    del_child = gateway.delete_record("watchlist_items", filters={"id": item_id})
    assert del_child["success"]
    del_parent2 = gateway.delete_record("watchlists", filters={"id": wl_id})
    assert del_parent2["success"]


def test_incompatible_existing_watchlist_table_is_rejected(tmp_path: Path) -> None:
    """Ensure pre-existing incompatible table definition is rejected safely."""
    path = tmp_path / "host.db"
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("CREATE TABLE watchlists (id INTEGER PRIMARY KEY)")
        connection.execute("INSERT INTO watchlists VALUES (1)")
    gateway = HostPersistence(path)
    assert not gateway.ensure_watchlists_schema()["success"]
    assert gateway.read_records("watchlists")["data"]["records"] == [{"id": 1}]
