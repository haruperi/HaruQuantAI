"""Unit tests for resolve internal persistence layer."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from app.services.brokers.resolve._persistence import (
    get_active_broker_record,
    init_broker_table,
    list_broker_records,
    register_broker_record,
    set_active_broker_record,
)


@pytest.fixture
def db_file(tmp_path: Path) -> Path:
    """Create a temporary database for persistence tests."""
    path = tmp_path / "brokers_persistence.db"
    init_broker_table(path)
    return path


def test_init_broker_table_creates_schema_and_seeds(db_file: Path) -> None:
    """Verify table creation, column structure, and initial seeds."""
    assert db_file.is_file()

    conn = sqlite3.connect(str(db_file))
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(broker);")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        assert "id" in columns
        assert "name" in columns
        assert "platform" in columns
        assert "desc" in columns
        assert "active" in columns
        assert "timezone" in columns

        cursor.execute("SELECT COUNT(*) FROM broker;")
        count = cursor.fetchone()[0]
        assert count == 5
    finally:
        conn.close()


def test_init_broker_table_idempotent(db_file: Path) -> None:
    """Verify calling init_broker_table multiple times does not duplicate records."""
    init_broker_table(db_file)
    init_broker_table(db_file)

    conn = sqlite3.connect(str(db_file))
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM broker;")
        count = cursor.fetchone()[0]
        assert count == 5
    finally:
        conn.close()


def test_get_active_broker_record_defaults(db_file: Path) -> None:
    """Verify get_active_broker_record returns MetaTrader 5 by default."""
    record = get_active_broker_record(db_file)
    assert record["name"] == "MetaTrader 5"
    assert record["platform"] == "mt5"
    assert record["active"] is True
    assert record["timezone"] == "UTC+3"


def test_get_active_broker_record_with_settings_override(db_file: Path) -> None:
    """Verify resolution respects runtime settings if configured."""
    conn = sqlite3.connect(str(db_file))
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        conn.execute(
            "INSERT INTO settings (key, value) VALUES ('broker.runtime_broker', 'ctrader');"
        )
        conn.commit()
    finally:
        conn.close()

    record = get_active_broker_record(db_file)
    assert record["name"] == "cTrader"
    assert record["platform"] == "ctrader"


def test_list_broker_records(db_file: Path) -> None:
    """Verify list_broker_records returns all registered records."""
    records = list_broker_records(db_file)
    assert len(records) == 5
    platforms = [r["platform"] for r in records]
    assert "mt5" in platforms
    assert "binance" in platforms
    assert "ctrader" in platforms


def test_set_active_broker_record_success(db_file: Path) -> None:
    """Verify activating a different broker updates active flags."""
    updated = set_active_broker_record("binance", db_path=db_file)
    assert updated["platform"] == "binance"
    assert updated["active"] is True

    current = get_active_broker_record(db_file)
    assert current["platform"] == "binance"
    assert current["name"] == "Binance"


def test_set_active_broker_record_not_found(db_file: Path) -> None:
    """Verify setting non-existent broker raises ValueError."""
    with pytest.raises(ValueError, match="not found in database"):
        set_active_broker_record("nonexistent", db_path=db_file)


def test_register_broker_record(db_file: Path) -> None:
    """Verify registering a new broker record."""
    new_brk = register_broker_record(
        name="Custom Broker",
        platform="custom",
        desc="Custom Test Gateway",
        active=True,
        timezone="UTC",
        db_path=db_file,
    )
    assert new_brk["name"] == "Custom Broker"
    assert new_brk["platform"] == "custom"
    assert new_brk["active"] is True

    active = get_active_broker_record(db_file)
    assert active["platform"] == "custom"
