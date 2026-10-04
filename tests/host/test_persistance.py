"""Unit tests for host SQLite persistence and scoped settings store."""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path

import pytest
from app.host.persistance import (
    DEFAULT_DATABASE_PATH,
    MAX_BATCH_SIZE,
    MAX_IDENTIFIER_LENGTH,
    MAX_JSON_DEPTH,
    MAX_VALUE_BYTES,
    CorruptDataError,
    IncompatibleSchemaError,
    SettingsStore,
    StorageBusyError,
    ValidationError,
)


def test_default_database_path() -> None:
    """Verify default database path points to expected repo location."""
    store = SettingsStore()
    assert store.db_path == DEFAULT_DATABASE_PATH
    assert store.db_path.name == "haruquantai.db"


def test_initialize_creates_table(tmp_path: Path) -> None:
    """Verify initialize creates host_settings table on fresh database."""
    db_file = tmp_path / "test.db"
    store = SettingsStore(db_file)
    store.initialize()

    conn = sqlite3.connect(db_file)
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name = 'host_settings'"
        ).fetchone()
        assert row is not None
        assert row[0] == "host_settings"
    finally:
        conn.close()


def test_initialize_compatible_existing_schema(tmp_path: Path) -> None:
    """Verify initialize succeeds if table already exists with valid schema."""
    db_file = tmp_path / "test.db"
    store = SettingsStore(db_file)
    store.initialize()
    # Calling again should succeed without error
    store.initialize()


def test_initialize_incompatible_schema(tmp_path: Path) -> None:
    """Verify initialize raises IncompatibleSchemaError for corrupt schema."""
    db_file = tmp_path / "incompatible.db"
    conn = sqlite3.connect(db_file)
    try:
        conn.execute("CREATE TABLE host_settings (wrong_column INTEGER PRIMARY KEY)")
        conn.commit()
    finally:
        conn.close()

    store = SettingsStore(db_file)
    with pytest.raises(IncompatibleSchemaError, match="Missing required column"):
        store.initialize()


def test_initialize_incompatible_column_type(tmp_path: Path) -> None:
    """Verify initialize raises IncompatibleSchemaError for invalid column types."""
    db_file = tmp_path / "incompatible_type.db"
    conn = sqlite3.connect(db_file)
    try:
        conn.execute(
            """
            CREATE TABLE host_settings (
                scope BLOB NOT NULL,
                key TEXT NOT NULL,
                value_json TEXT NOT NULL,
                schema_version INTEGER NOT NULL DEFAULT 1,
                updated_at_utc TEXT NOT NULL,
                PRIMARY KEY (scope, key)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

    store = SettingsStore(db_file)
    with pytest.raises(IncompatibleSchemaError, match="Incompatible column definition"):
        store.initialize()


def test_read_nonexistent_database(tmp_path: Path) -> None:
    """Verify reading from nonexistent database returns empty page."""
    store = SettingsStore(tmp_path / "nonexistent.db")
    page = store.read_settings("global", limit=10)
    assert page.items == []
    assert page.next_key is None


def test_read_and_update_roundtrip(tmp_path: Path) -> None:
    """Verify batch updates and single key / paginated reads."""
    db_file = tmp_path / "store.db"
    store = SettingsStore(db_file)
    store.initialize()

    values = {
        "theme": "dark",
        "retry_count": 3,
        "ratio": 1.25,
        "is_active": True,
        "tags": ["alpha", "beta"],
        "metadata": {"nested": {"level": 2}},
        "empty_val": None,
    }

    changed = store.update_settings("ui", values)
    assert len(changed) == 7

    # Read single key
    theme_page = store.read_settings("ui", key="theme")
    assert len(theme_page.items) == 1
    assert theme_page.items[0].key == "theme"
    assert theme_page.items[0].value == "dark"
    assert theme_page.items[0].scope == "ui"
    assert theme_page.items[0].schema_version == 1
    assert theme_page.next_key is None

    # Read nonexistent key
    missing_page = store.read_settings("ui", key="nonexistent")
    assert missing_page.items == []
    assert missing_page.next_key is None

    # Read all keys in scope
    all_page = store.read_settings("ui", limit=100)
    assert len(all_page.items) == 7
    assert all_page.next_key is None

    keys = [r.key for r in all_page.items]
    assert keys == sorted(values.keys())


def test_keyset_pagination(tmp_path: Path) -> None:
    """Verify keyset pagination with after_key cursor."""
    db_file = tmp_path / "page.db"
    store = SettingsStore(db_file)
    store.initialize()

    store.update_settings("items", {f"k{i:02d}": i for i in range(10)})

    # Page 1
    page1 = store.read_settings("items", limit=4)
    assert len(page1.items) == 4
    assert [r.key for r in page1.items] == ["k00", "k01", "k02", "k03"]
    assert page1.next_key == "k03"

    # Page 2
    page2 = store.read_settings("items", after_key=page1.next_key, limit=4)
    assert len(page2.items) == 4
    assert [r.key for r in page2.items] == ["k04", "k05", "k06", "k07"]
    assert page2.next_key == "k07"

    # Page 3 (final partial page)
    page3 = store.read_settings("items", after_key=page2.next_key, limit=4)
    assert len(page3.items) == 2
    assert [r.key for r in page3.items] == ["k08", "k09"]
    assert page3.next_key is None


def test_update_idempotency_preserves_timestamp(tmp_path: Path) -> None:
    """Verify unchanged canonical JSON retains original updated_at_utc timestamp."""
    db_file = tmp_path / "idempotent.db"
    store = SettingsStore(db_file)
    store.initialize()

    first_change = store.update_settings("config", {"rate": 10})
    assert len(first_change) == 1
    original_ts = first_change[0].updated_at_utc

    # Update with identical value
    second_change = store.update_settings("config", {"rate": 10})
    assert second_change == []

    # Verify timestamp in database remains unchanged
    page = store.read_settings("config", key="rate")
    assert page.items[0].updated_at_utc == original_ts

    # Update with modified value
    third_change = store.update_settings("config", {"rate": 20})
    assert len(third_change) == 1
    assert third_change[0].value == 20
    assert third_change[0].updated_at_utc >= original_ts


def test_empty_batch_update(tmp_path: Path) -> None:
    """Verify empty dictionary batch returns empty list immediately."""
    store = SettingsStore(tmp_path / "empty.db")
    result = store.update_settings("global", {})
    assert result == []


def test_identifier_validation() -> None:
    """Verify scope and key identifier validation rules."""
    store = SettingsStore()

    with pytest.raises(ValidationError, match="scope must not be empty"):
        store.read_settings("")

    with pytest.raises(ValidationError, match="contains invalid characters"):
        store.read_settings("bad scope!")

    with pytest.raises(ValidationError, match="exceeds maximum"):
        store.read_settings("a" * (MAX_IDENTIFIER_LENGTH + 1))

    with pytest.raises(ValidationError, match="key must not be empty"):
        store.read_settings("valid", key="")

    with pytest.raises(ValidationError, match="limit must be between 1 and"):
        store.read_settings("valid", limit=0)

    with pytest.raises(ValidationError, match="limit must be between 1 and"):
        store.read_settings("valid", limit=1001)


def test_batch_limits(tmp_path: Path) -> None:
    """Verify batch size and payload size limits."""
    store = SettingsStore(tmp_path / "limits.db")
    store.initialize()

    # Exceed max batch size
    large_batch = {f"k{i}": i for i in range(MAX_BATCH_SIZE + 1)}
    with pytest.raises(ValidationError, match="Batch size of 101 exceeds maximum"):
        store.update_settings("test", large_batch)

    # Exceed single value size limit
    oversized_value = "x" * (MAX_VALUE_BYTES + 10)
    with pytest.raises(ValidationError, match="exceeds maximum limit"):
        store.update_settings("test", {"key": oversized_value})

    # Exceed nesting depth
    nested: dict[str, object] = {"val": 1}
    for _ in range(MAX_JSON_DEPTH + 1):
        nested = {"sub": nested}
    with pytest.raises(ValidationError, match="exceeds maximum nesting depth"):
        store.update_settings("test", {"nested": nested})


def test_payload_bytes_limit(tmp_path: Path) -> None:
    """Verify total batch payload size limit."""
    store = SettingsStore(tmp_path / "payload.db")
    store.initialize()

    # Batch with 50 items of 30 KiB each = ~1.5 MiB (exceeds 1 MiB)
    chunk = "y" * (30 * 1024)
    batch = {f"k{i}": chunk for i in range(50)}
    with pytest.raises(ValidationError, match="Total batch payload size"):
        store.update_settings("test", batch)


def test_corrupt_json_in_database(tmp_path: Path) -> None:
    """Verify CorruptDataError when database contains malformed JSON."""
    db_file = tmp_path / "corrupt.db"
    store = SettingsStore(db_file)
    store.initialize()

    conn = sqlite3.connect(db_file)
    try:
        conn.execute(
            """
            INSERT INTO host_settings (scope, key, value_json, schema_version, updated_at_utc)
            VALUES ('s', 'corrupt_key', '{bad_json', 1, '2026-10-04T12:00:00Z')
            """
        )
        conn.commit()
    finally:
        conn.close()

    with pytest.raises(CorruptDataError, match="Corrupt JSON payload"):
        store.read_settings("s", key="corrupt_key")


def test_unsupported_schema_version_in_database(tmp_path: Path) -> None:
    """Verify CorruptDataError on read and IncompatibleSchemaError on update."""
    db_file = tmp_path / "version.db"
    store = SettingsStore(db_file)
    store.initialize()

    conn = sqlite3.connect(db_file)
    try:
        conn.execute(
            """
            INSERT INTO host_settings (scope, key, value_json, schema_version, updated_at_utc)
            VALUES ('s', 'v2_key', '123', 99, '2026-10-04T12:00:00Z')
            """
        )
        conn.commit()
    finally:
        conn.close()

    with pytest.raises(CorruptDataError, match="Unsupported schema version"):
        store.read_settings("s", key="v2_key")

    with pytest.raises(IncompatibleSchemaError, match="Unsupported schema version"):
        store.update_settings("s", {"v2_key": 456})


def test_missing_table_during_update(tmp_path: Path) -> None:
    """Verify IncompatibleSchemaError when updating a database without host_settings."""
    db_file = tmp_path / "no_table.db"
    store = SettingsStore(db_file)
    # Note: store.initialize() is NOT called, but file is created
    conn = sqlite3.connect(db_file)
    conn.close()

    with pytest.raises(
        IncompatibleSchemaError, match="Table 'host_settings' does not exist"
    ):
        store.update_settings("s", {"k": 1})


def test_non_serializable_value(tmp_path: Path) -> None:
    """Verify ValidationError when value cannot be serialized to JSON."""
    store = SettingsStore(tmp_path / "test.db")
    store.initialize()

    with pytest.raises(ValidationError, match="not serializable"):
        store.update_settings("s", {"key": object()})

    with pytest.raises(ValidationError, match="not serializable"):
        store.update_settings("s", {"key": float("nan")})


def test_concurrent_lock_contention(tmp_path: Path) -> None:
    """Verify StorageBusyError is raised under exclusive lock contention."""
    db_file = tmp_path / "lock.db"
    store = SettingsStore(db_file)
    store.initialize()

    # Hold an exclusive lock in another connection
    conn = sqlite3.connect(db_file, autocommit=True)
    try:
        conn.execute("BEGIN EXCLUSIVE")
        fast_store = SettingsStore(db_file, busy_timeout=0.05)
        with pytest.raises(StorageBusyError):
            fast_store.update_settings("s", {"k": 1})
    finally:
        conn.execute("ROLLBACK")
        conn.close()


def test_logging_requirements(tmp_path: Path) -> None:
    """Verify FR-HOST-SETTINGS-READ and FR-HOST-SETTINGS-UPDATE emit structured logs."""
    from app.host.logging import configure_host_logging, flush, reset_logging

    log_dir = tmp_path / "telemetry_logs"
    configure_host_logging(log_dir=log_dir, level=logging.DEBUG, include_console=False)
    try:
        db_file = tmp_path / "logs.db"
        store = SettingsStore(db_file)
        store.initialize()

        store.update_settings("telemetry_scope", {"setting_a": "secret_value"})
        store.read_settings("telemetry_scope", key="setting_a")
        store.read_settings("telemetry_scope", limit=10)
        flush()

        app_log = log_dir / "app.log"
        assert app_log.exists()
        lines = [
            json.loads(line)
            for line in app_log.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        # Check for update requirement log
        update_events = [
            e
            for e in lines
            if e.get("context", {}).get("requirement") == "FR-HOST-SETTINGS-UPDATE"
        ]
        assert len(update_events) == 1
        assert update_events[0]["context"]["changed_count"] == 1
        assert update_events[0]["context"]["scope"] == "telemetry_scope"

        # Check that setting value was NOT leaked in the log file
        assert "secret_value" not in app_log.read_text(encoding="utf-8")

        # Check for read requirement log
        read_events = [
            e
            for e in lines
            if e.get("context", {}).get("requirement") == "FR-HOST-SETTINGS-READ"
        ]
        assert len(read_events) >= 2
    finally:
        reset_logging()
