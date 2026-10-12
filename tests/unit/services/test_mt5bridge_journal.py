"""Verify shared-store MT5 journal custody, validation and redacted logging.

Description:
    Exercise command/event persistence and reopen temporary databases only.
    Check schema rejection without resetting data or touching live stores.

Purpose:
    FEAT-HOST-PERSISTENCE-MT5-JOURNAL: Verify relocated storage behavior.

Key Capabilities:
    - FR-HOST-PERSISTENCE-MT5-JOURNAL: Verify CRUD, durable values and cleanup.
      Associated: `Journal`
      Logging: Assert every operation emits metadata without payloads or paths.
    - FR-HOST-PERSISTENCE-MT5-JOURNAL-SCHEMA: Reject incompatible journal shapes.
      Associated: `ensure_mt5bridge_journal_schema()`
      Logging: Assert compatibility attempts and successful initialization events.

Python API Usage:
    Run via pytest using isolated tmp_path journals.

CLI Usage:
    uv run pytest tests/unit/services/test_mt5bridge_journal.py --no-cov
"""

import json
import sqlite3
from contextlib import closing
from inspect import signature
from pathlib import Path
from unittest.mock import Mock

import pytest
from app.host.persistence import IncompatibleSchemaError, mt5bridge_journal, schema
from app.host.persistence.engine import DEFAULT_DATABASE_PATH
from app.host.persistence.mt5bridge_journal import Journal


def test_command_event_storage_and_reopen(tmp_path: Path) -> None:
    """Preserve statuses, serialized results and full unsigned identifiers."""
    path = tmp_path / "journal.sqlite3"
    journal = Journal(path)
    try:
        assert journal.get_command("missing") is None
        journal.create_command(
            command_id="command",
            session_id="session",
            object_id="trade",
            class_name="Trade",
            method_name="Buy",
            args=[0.1, "EURUSD"],
            requires_arm=True,
        )
        created = journal.get_command("command")
        assert created is not None
        assert created["status"] == "created"
        assert created["sent_at"] is None
        journal.mark_sent("command")
        sent = journal.get_command("command")
        assert sent is not None
        assert sent["status"] == "sent"
        assert sent["sent_at"] >= created["created_at"]
        journal.resolve_command(
            "command",
            status="resolved",
            value={"ticket": 2**64 - 1},
            meta={"retcode": 10009},
            native_request_id=2**64 - 1,
        )
        result = journal.get_command("command")
        assert result is not None
        assert result["native_request_id"] == 2**64 - 1
        assert result["value"] == {"ticket": 2**64 - 1}
        assert result["meta"] == {"retcode": 10009}
        assert result["error"] is None
        journal.resolve_command("command", status="rejected", error={"code": "test"})
        rejected = journal.get_command("command")
        assert rejected is not None
        assert rejected["acknowledged_at"] == result["acknowledged_at"]
        assert rejected["error"] == {"code": "test"}
        assert rejected["value"] is None
        assert rejected["meta"] == {}
        assert rejected["native_request_id"] is None
        journal.add_event(
            session_id="session",
            event_type="transaction",
            command_id="command",
            native_request_id=2**64 - 1,
            payload={"symbol": "EURUSD"},
        )
        journal.add_event(session_id=None, event_type="other", payload=None)
    finally:
        journal.close()
    reopened = Journal(path)
    try:
        assert reopened.get_command("command") == rejected
    finally:
        reopened.close()
    with closing(sqlite3.connect(path)) as conn, conn:
        assert json.loads(
            conn.execute("SELECT args_json FROM mt5_commands").fetchone()[0]
        ) == [0.1, "EURUSD"]
        events = conn.execute(
            "SELECT native_request_id, payload_json FROM mt5_events ORDER BY event_id"
        ).fetchall()
        assert events == [(str(2**64 - 1), '{"symbol":"EURUSD"}'), (None, "null")]
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert tables == {"mt5_commands", "mt5_events", "sqlite_sequence"}
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        indexes = {row[1] for row in conn.execute("PRAGMA index_list(mt5_events)")}
        assert indexes == {"idx_mt5_events_request", "idx_mt5_events_command"}


@pytest.mark.parametrize("mismatch", ["table", "index"])
def test_incompatible_schema_preserves_rows(tmp_path: Path, mismatch: str) -> None:
    """Reject incompatible existing storage before DDL can alter the database."""
    path = tmp_path / "incompatible.sqlite3"
    with closing(sqlite3.connect(path)) as conn, conn:
        if mismatch == "table":
            conn.execute("CREATE TABLE mt5_commands(command_id TEXT PRIMARY KEY)")
            conn.execute("INSERT INTO mt5_commands VALUES('preserved')")
        else:
            conn.executescript(schema.MT5BRIDGE_JOURNAL_DDL)
            conn.execute("DROP INDEX idx_mt5_events_command")
            conn.execute(
                "CREATE INDEX idx_mt5_events_command ON mt5_events(event_type)"
            )
            conn.execute(
                "INSERT INTO mt5_events(event_type,payload_json,received_at) VALUES('preserved','{}',0)"
            )
    with pytest.raises(IncompatibleSchemaError, match="shape differs"):
        Journal(path)
    with closing(sqlite3.connect(path)) as conn, conn:
        if mismatch == "table":
            assert conn.execute("SELECT command_id FROM mt5_commands").fetchall() == [
                ("preserved",)
            ]
            assert (
                conn.execute(
                    "SELECT name FROM sqlite_master WHERE name='mt5_events'"
                ).fetchone()
                is None
            )
        else:
            assert conn.execute("SELECT event_type FROM mt5_events").fetchall() == [
                ("preserved",)
            ]
            assert (
                conn.execute("PRAGMA index_info(idx_mt5_events_command)").fetchone()[2]
                == "event_type"
            )


def test_storage_logs_are_redacted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every CRUD/lifecycle operation logs metadata without sensitive values."""
    logger = Mock()
    schema_logger = Mock()
    monkeypatch.setattr(mt5bridge_journal, "logger", logger)
    monkeypatch.setattr(schema, "logger", schema_logger)
    path = tmp_path / "private-path.sqlite3"
    journal = Journal(path)
    try:
        journal.create_command(
            command_id="private-id",
            session_id=None,
            object_id="trade",
            class_name="Trade",
            method_name="Buy",
            args=["private-value"],
            requires_arm=False,
        )
        journal.mark_sent("private-id")
        journal.resolve_command("private-id", status="resolved", value="private-value")
        journal.get_command("private-id")
        journal.add_event(
            session_id=None, event_type="transaction", payload="private-value"
        )
    finally:
        journal.close()
    assert [
        call.kwargs["extra"]["operation"] for call in logger.debug.call_args_list
    ] == [
        "open",
        "create_command",
        "mark_sent",
        "resolve_command",
        "get_command",
        "add_event",
        "close",
    ]
    schema_logger.debug.assert_called_once()
    schema_logger.info.assert_called_once()
    for sensitive in (str(path), "private-value", "private-id"):
        assert sensitive not in repr(logger.mock_calls)
        assert sensitive not in repr(schema_logger.mock_calls)


def test_shared_store_preserves_unrelated_data(tmp_path: Path) -> None:
    """Add only MT5 storage while preserving unrelated tables and indexes."""
    path = tmp_path / "shared.db"
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute("CREATE TABLE application_records(id INTEGER, value TEXT)")
        conn.execute("INSERT INTO application_records VALUES(1, 'preserved')")
        conn.execute("CREATE INDEX idx_events_command ON application_records(id)")
    journal = Journal(path)
    try:
        journal.create_command(
            command_id="isolated-command",
            session_id=None,
            object_id="account",
            class_name="AccountInfo",
            method_name="Balance",
            args=[],
            requires_arm=False,
        )
        journal.mark_sent("isolated-command")
        journal.resolve_command("isolated-command", status="resolved", value=1000)
        journal.add_event(session_id=None, event_type="test", payload={})
        result = journal.get_command("isolated-command")
        assert result is not None
        assert result["value"] == 1000
    finally:
        journal.close()
    with closing(sqlite3.connect(path)) as conn:
        assert conn.execute("SELECT * FROM application_records").fetchall() == [
            (1, "preserved")
        ]
        assert (
            conn.execute("PRAGMA index_info(idx_events_command)").fetchone()[2] == "id"
        )
        assert conn.execute("SELECT COUNT(*) FROM mt5_events").fetchone()[0] == 1
        assert (
            conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('commands', 'events')"
            ).fetchall()
            == []
        )


def test_default_path_is_absolute_from_another_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Open the canonical default through a double without touching active storage."""
    monkeypatch.chdir(tmp_path)
    assert DEFAULT_DATABASE_PATH.is_absolute()
    assert DEFAULT_DATABASE_PATH.parts[-3:] == ("data", "database", "haruquantai.db")
    assert signature(Journal).parameters["path"].default == DEFAULT_DATABASE_PATH
    connection = Mock()
    connect = Mock(return_value=connection)
    ensure_schema = Mock()
    path_factory = Mock()
    monkeypatch.setattr(mt5bridge_journal.sqlite3, "connect", connect)
    monkeypatch.setattr(
        mt5bridge_journal, "ensure_mt5bridge_journal_schema", ensure_schema
    )
    monkeypatch.setattr(mt5bridge_journal, "Path", path_factory)
    journal = Journal()
    try:
        connect.assert_called_once_with(
            str(DEFAULT_DATABASE_PATH), check_same_thread=False
        )
        ensure_schema.assert_called_once_with(connection)
    finally:
        journal.close()
    connection.close.assert_called_once()
    assert list(tmp_path.iterdir()) == []


def test_nested_store_and_memory_paths(tmp_path: Path) -> None:
    """Create parent directories only for file-backed temporary stores."""
    path = tmp_path / "nested" / "journal.db"
    journal = Journal(path)
    journal.close()
    assert path.exists()
    memory = Journal(":memory:")
    try:
        assert memory.get_command("missing") is None
    finally:
        memory.close()
