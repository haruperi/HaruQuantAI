"""Unit tests verifying 100% SQX parity for DataManagerLog.

Description:
    Tests comprehensive StrategyQuant X parity for Data Manager logging,
    covering the LogEntry model, SQX line formatting, LogStore SQLite
    persistence, DataManagerLogService in-memory/DB operations, and REST
    endpoints for querying, posting, and clearing logs.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Manage data logging and progress reporting
    in the Data Manager workspace.

Key Capabilities:
    - FR-DATA-LOG-MODEL: LogEntry data model with SQX format serialization.
    - FR-DATA-LOG-PERSISTENCE: SQLite datamgr_logs table CRUD operations.
    - FR-DATA-LOG-SERVICE: DataManagerLogService dual ring-buffer and DB routing.
    - FR-DATA-LOG-REST-API: REST endpoints for log ingestion, query, and clearance.
    - FR-DATA-LOG-EVENTBUS: Real-time event publishing on log creation.

Python API Usage:
    Run via pytest:
    `pytest tests/unit/workspace/test_data_manager_log_parity.py -v --no-cov`

CLI Usage:
    `pytest tests/unit/workspace/test_data_manager_log_parity.py`
"""

from __future__ import annotations

from pathlib import Path

import pytest
from app.host.persistence import DatabaseManager
from app.host.resources import ResourceManager
from app.host.transport import EventBus
from app.workspace.data_manager.log import DataManagerLogService, LogEntry
from app.workspace.data_manager.routes import create_data_router
from fastapi import FastAPI
from fastapi.testclient import TestClient

# =====================================================================
# Unit Tests: LogEntry and SQX Formatting
# =====================================================================


def test_log_entry_defaults_and_attributes() -> None:
    """Verify LogEntry field validation and attribute properties."""
    entry = LogEntry(
        timestamp_utc="2026-10-11T08:30:00+00:00",
        action="INGEST",
        message="Import completed successfully",
    )
    assert entry.timestamp_utc == "2026-10-11T08:30:00+00:00"
    assert entry.action == "INGEST"
    assert entry.message == "Import completed successfully"
    assert entry.symbol is None
    assert entry.key is None
    assert entry.pct is None
    assert entry.log_str is None
    assert entry.details == {}


def test_log_entry_custom_sqx_fields() -> None:
    """Verify LogEntry with SQX progress fields."""
    entry = LogEntry(
        timestamp_utc="2026-10-11T08:30:00+00:00",
        action="DOWNLOAD",
        message="50% downloaded",
        symbol="EURUSD",
        key="EURUSD",
        pct=50.0,
        log_str="Downloaded 50MB",
        details={"provider": "Dukascopy"},
    )
    assert entry.key == "EURUSD"
    assert entry.pct == 50.0
    assert entry.log_str == "Downloaded 50MB"
    assert entry.details == {"provider": "Dukascopy"}


def test_format_sqx_line_with_key_and_log_str() -> None:
    """Verify format_sqx_line matches SQX YYYY.M.D HH:mm <key> <logStr>."""
    entry = LogEntry(
        timestamp_utc="2026-03-05T09:04:00+00:00",
        action="INGEST",
        message="Fallback message",
        key="EURUSD_M1",
        log_str="Imported 12450 bars",
    )
    formatted = entry.format_sqx_line()
    assert formatted == "2026.3.5 09:04 EURUSD_M1 Imported 12450 bars"


def test_format_sqx_line_with_log_str_only() -> None:
    """Verify format_sqx_line when key is empty."""
    entry = LogEntry(
        timestamp_utc="2026-12-25T14:05:00+00:00",
        action="CLEANUP",
        message="Fallback message",
        log_str="General data cleanup finished",
    )
    formatted = entry.format_sqx_line()
    assert formatted == "2026.12.25 14:05 General data cleanup finished"


def test_format_sqx_line_fallback_to_message() -> None:
    """Verify format_sqx_line falls back to message when log_str is empty."""
    entry = LogEntry(
        timestamp_utc="2026-01-01T00:00:00+00:00",
        action="BOOT",
        message="System initial boot log",
    )
    formatted = entry.format_sqx_line()
    assert formatted == "2026.1.1 00:00 System initial boot log"


# =====================================================================
# Unit Tests: LogStore (Persistence)
# =====================================================================


def test_log_store_crud(tmp_path: Path) -> None:
    """Verify SQLite LogStore create, list, count, and clear operations."""
    db_file = tmp_path / "test_log_store.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()

    # Initial state
    assert db.logs.count() == 0
    assert db.logs.list_logs() == []

    # Create entries
    id1 = db.logs.create(
        {
            "timestamp_utc": "2026-10-11T08:00:00+00:00",
            "action": "INGEST",
            "message": "Starting import job",
            "symbol": "GBPUSD",
            "details": {"key": "GBPUSD", "pct": 0, "log_str": "Starting import job"},
        }
    )
    id2 = db.logs.create(
        {
            "timestamp_utc": "2026-10-11T08:15:00+00:00",
            "action": "INGEST",
            "message": "Completed 100%",
            "symbol": "GBPUSD",
            "details": {"key": "GBPUSD", "pct": 100, "log_str": "Completed 100%"},
        }
    )

    assert id1 > 0
    assert id2 > id1
    assert db.logs.count() == 2

    # Query logs (reverse chronological order by ID)
    logs = db.logs.list_logs()
    assert len(logs) == 2
    assert logs[0]["id"] == id2
    assert logs[0]["details"]["pct"] == 100
    assert logs[1]["id"] == id1
    assert logs[1]["details"]["pct"] == 0

    # Limit and offset
    page1 = db.logs.list_logs(limit=1, offset=0)
    assert len(page1) == 1
    assert page1[0]["id"] == id2

    page2 = db.logs.list_logs(limit=1, offset=1)
    assert len(page2) == 1
    assert page2[0]["id"] == id1

    # Filter by symbol
    gbp_logs = db.logs.list_logs(symbol="GBPUSD")
    assert len(gbp_logs) == 2
    eur_logs = db.logs.list_logs(symbol="EURUSD")
    assert len(eur_logs) == 0

    # Clear logs
    deleted = db.logs.clear()
    assert deleted == 2
    assert db.logs.count() == 0
    assert db.logs.list_logs() == []


# =====================================================================
# Unit Tests: DataManagerLogService
# =====================================================================


def test_log_service_in_memory_only() -> None:
    """Verify DataManagerLogService operations without a database."""
    service = DataManagerLogService(db=None)

    assert service.count_logs() == 0
    assert service.list_logs() == []

    entry1 = service.log_activity(
        action="DOWNLOAD",
        message="10% done",
        symbol="EURUSD",
        key="EURUSD",
        pct=10.0,
        log_str="10% done",
    )
    assert entry1.key == "EURUSD"
    assert entry1.pct == 10.0
    assert service.count_logs() == 1
    assert len(service.list_logs()) == 1

    service.log_activity(action="CLEANUP", message="Cleanup done")
    assert service.count_logs() == 2

    # Clear
    cleared = service.clear_logs()
    assert cleared == 2
    assert service.count_logs() == 0
    assert service.list_logs() == []


def test_log_service_with_database(tmp_path: Path) -> None:
    """Verify DataManagerLogService operations backed by DatabaseManager."""
    db_file = tmp_path / "test_log_service.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()

    service = DataManagerLogService(db=db)

    service.log_activity(
        action="TRANSFORM",
        message="Resampling completed",
        symbol="USDJPY",
        key="USDJPY",
        pct=100.0,
        log_str="Resampled 5000 bars",
    )

    # Both DB and service reflect the log
    assert service.count_logs() == 1
    assert db.logs.count() == 1

    logs = service.list_logs()
    assert len(logs) == 1
    assert logs[0].key == "USDJPY"
    assert logs[0].pct == 100.0
    assert logs[0].action == "TRANSFORM"

    # Clear logs affects both
    count_cleared = service.clear_logs()
    assert count_cleared == 1
    assert service.count_logs() == 0
    assert db.logs.count() == 0


# =====================================================================
# REST API & EventBus Integration Tests
# =====================================================================


@pytest.fixture
def test_client(tmp_path: Path) -> tuple[TestClient, EventBus, DatabaseManager]:
    """Fixture providing FastAPI test client, EventBus, and DatabaseManager."""
    db_file = tmp_path / "test_data_log_api.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()

    res_dir = tmp_path / "resources"
    res_dir.mkdir()
    res_mgr = ResourceManager(root_dir=res_dir)

    event_bus = EventBus()

    router = create_data_router(
        db_manager=db,
        resource_manager=res_mgr,
        event_bus=event_bus,
    )
    app = FastAPI()
    app.include_router(router)
    return TestClient(app), event_bus, db


def test_api_log_crud_and_endpoints(
    test_client: tuple[TestClient, EventBus, DatabaseManager],
) -> None:
    """Verify GET, POST, and DELETE/clear endpoints for /data/logs."""
    client, event_bus, db = test_client

    # 1. Initial list should be empty
    res = client.get("/data/logs")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    assert body["data"] == []

    # 2. Add log entry via POST /data/logs
    payload = {
        "action": "INGEST",
        "message": "Starting bar parsing",
        "symbol": "BTCUSDT",
        "key": "BTCUSDT",
        "pct": 25.0,
        "log_str": "Processed 25000 bars",
    }
    post_res = client.post("/data/logs", json=payload)
    assert post_res.status_code == 201
    post_body = post_res.json()
    assert post_body["status"] == "success"
    created = post_body["data"]
    assert created["key"] == "BTCUSDT"
    assert created["pct"] == 25.0
    assert created["log_str"] == "Processed 25000 bars"

    # 3. Query logs via GET /data/logs
    get_res = client.get("/data/logs")
    assert get_res.status_code == 200
    logs = get_res.json()["data"]
    assert len(logs) == 1
    assert logs[0]["key"] == "BTCUSDT"

    # 4. Add second log
    client.post(
        "/data/logs",
        json={"action": "DOWNLOAD", "message": "Operation finished"},
    )
    get_res2 = client.get("/data/logs")
    assert len(get_res2.json()["data"]) == 2

    # 5. Clear via POST /data/logs/clear
    clear_res = client.post("/data/logs/clear")
    assert clear_res.status_code == 200
    assert clear_res.json()["data"]["cleared_count"] == 2

    # Verify empty
    get_res3 = client.get("/data/logs")
    assert len(get_res3.json()["data"]) == 0

    # 6. Add log and clear via DELETE /data/logs
    client.post("/data/logs", json={"action": "TEMP", "message": "Temp log"})
    assert len(client.get("/data/logs").json()["data"]) == 1

    del_res = client.delete("/data/logs")
    assert del_res.status_code == 200
    assert del_res.json()["data"]["cleared_count"] == 1
    assert len(client.get("/data/logs").json()["data"]) == 0


def test_api_log_event_bus_publishing(
    test_client: tuple[TestClient, EventBus, DatabaseManager],
) -> None:
    """Verify that POST /data/logs emits a data_manager.log event on EventBus."""
    client, event_bus, _db = test_client

    # Trigger log emission
    payload = {
        "action": "DOWNLOAD",
        "message": "Download in progress",
        "symbol": "SPY",
        "key": "SPY",
        "pct": 75.0,
        "log_str": "Downloaded 75%",
    }
    res = client.post("/data/logs", json=payload)
    assert res.status_code == 201

    snapshot = event_bus.get_snapshot("data_manager.log")
    assert len(snapshot.events) == 1

    ev = snapshot.events[0]
    assert ev.channel == "data_manager.log"
    assert ev.event_type == "log.created"
    assert ev.payload["key"] == "SPY"
    assert ev.payload["pct"] == 75.0
    assert ev.payload["log_str"] == "Downloaded 75%"
