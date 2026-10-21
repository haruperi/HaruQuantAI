"""Unit tests for Data Manager DataLog service, WebSocket EventBus streaming, and CLI."""

from __future__ import annotations

import logging
import runpy
import sys
from pathlib import Path

import pytest
from app.host.events import EventBus
from app.host.persistence import HostPersistence
from app.workspace.data_manager.log import (
    CLEAR_FR,
    STREAM_FR,
    DataLog,
    DataLogCLI,
    main,
)


@pytest.fixture(autouse=True)
def test_db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fixture providing an isolated temporary SQLite database path."""
    db_file = tmp_path / "test_datamgr_log.db"
    monkeypatch.setattr(HostPersistence, "DEFAULT_DB_PATH", db_file)
    return db_file


def test_data_log_record_stream_and_clear(caplog: pytest.LogCaptureFixture) -> None:
    """Test DataLog._record_entry, data_log streaming, and clear_log reset."""
    bus = EventBus()
    service = DataLog(event_bus=bus)

    with caplog.at_level(logging.INFO):
        entry_dl = service.data_log(
            entry={
                "action": "DOWNLOAD",
                "symbol": "EURUSD",
                "status": "running",
                "progress": 45,
                "message": "Downloading 2025 M1 bars",
            }
        )[0]
        entry_err = service.data_log(
            entry={
                "action": "IMPORT_ERR",
                "symbol": "BTCUSDT",
                "status": "error",
                "progress": -1,
                "message": "Corrupt CSV line 42",
                "details": "Invalid timestamp",
            }
        )[0]
        entry_info = service.data_log(
            entry={
                "action": "EXPORT",
                "message": "Exported 1000 bars to CSV",
            }
        )[0]

    assert entry_dl["symbol"] == "EURUSD"
    assert entry_dl["progress"] == 45
    assert entry_dl["cancellable"] is True
    assert entry_dl["is_error"] is False

    assert entry_err["is_error"] is True
    assert entry_err["progress"] == -1
    assert entry_err["cancellable"] is False
    assert entry_info["status"] == "info"

    with caplog.at_level(logging.INFO):
        records = service.data_log(limit=10)

    assert len(records) == 3
    assert [r["action"] for r in records] == ["DOWNLOAD", "IMPORT_ERR", "EXPORT"]
    assert STREAM_FR in caplog.text

    op_rows = HostPersistence.read_records("datamgr_operation_log")
    assert len(op_rows) == 2

    with caplog.at_level(logging.INFO):
        cleared = service.clear_log()

    assert cleared == {"cleared": 5, "status": "idle", "progress": 0}
    assert CLEAR_FR in caplog.text
    assert service.data_log(limit=10) == []
    assert HostPersistence.read_records("datamgr_operation_log") == []

    snapshot = bus.get_snapshot(channel="logs")
    event_types = [ev.event_type for ev in snapshot.events]
    assert "datamgr.log.entry" in event_types
    assert "datamgr.log.stream" in event_types
    assert "datamgr.log.cleared" in event_types


def test_data_log_validation_errors(caplog: pytest.LogCaptureFixture) -> None:
    """Test DataLog limit and entry validation failure branches."""
    service = DataLog()

    with caplog.at_level(logging.WARNING), pytest.raises(ValueError, match="limit"):
        service.data_log(limit=0)

    with pytest.raises(ValueError, match="limit"):
        service.data_log(limit=501)

    with pytest.raises(ValueError, match="limit"):
        service.data_log(limit=True)

    with caplog.at_level(logging.WARNING), pytest.raises(ValueError, match="non-empty"):
        service.data_log(entry={"action": "", "message": "missing action"})

    with pytest.raises(ValueError, match="non-empty"):
        service.data_log(entry={"action": "DOWNLOAD", "message": "   "})

    assert STREAM_FR in caplog.text


def test_data_log_cli_and_main() -> None:
    """Test DataLogCLI formatting and standalone main entry point."""
    empty_out = DataLogCLI.format_log_entries([])
    assert "=== Data Manager Log (0 entries) ===" in empty_out

    formatted = DataLogCLI.format_log_entries(
        [
            {
                "timestamp_utc": "2026-10-21T20:00:00Z",
                "action": "DOWNLOAD",
                "symbol": "EURUSD",
                "message": "Completed",
            },
            {
                "timestamp_utc": "2026-10-21T20:01:00Z",
                "action": "EXPORT",
                "symbol": "",
                "message": "Done",
            },
        ]
    )
    assert "[EURUSD]: Completed" in formatted
    assert "EXPORT: Done" in formatted

    main()
    sys.modules.pop("app.workspace.data_manager.log", None)
    runpy.run_module("app.workspace.data_manager.log", run_name="__main__")
