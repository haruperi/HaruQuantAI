"""Isolated persistence and HTTP fixtures for Data Manager services."""

import sqlite3
from unittest.mock import patch

import pytest
from app.core.host.persistence import HostPersistence
from app.core.host.transport import register_transport_exception_handlers
from app.workspace.data_manager import _access, create_router
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def symbol_http(temp_db):
    application = FastAPI()
    application.state.persistence = temp_db
    application.include_router(create_router())
    application.dependency_overrides[_access] = lambda: None
    register_transport_exception_handlers(application)
    with TestClient(application) as client:
        yield client


@pytest.fixture
def temp_db(tmp_path):
    """Provide an isolated test database with refactored datamgr_symbols schema."""
    db_path = tmp_path / "test_haruquantai.db"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE "datamgr_symbols" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            exchange TEXT DEFAULT '',
            data_type TEXT DEFAULT 'Forex',
            spread TEXT NOT NULL DEFAULT '{}',
            margin TEXT NOT NULL DEFAULT '{}',
            volume TEXT NOT NULL DEFAULT '{}',
            trade TEXT NOT NULL DEFAULT '{}',
            price TEXT NOT NULL DEFAULT '{}',
            swap TEXT NOT NULL DEFAULT '{}',
            commission REAL DEFAULT 0.0,
            session TEXT NOT NULL DEFAULT '[]',
            state TEXT NOT NULL DEFAULT '{}',
            broker_id INTEGER DEFAULT 0,
            created_at_utc TEXT NOT NULL,
            updated_at_utc TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

    test_persistence = HostPersistence(db_path)
    with patch("app.workspace.data_manager.symbols.persistence", test_persistence):
        yield test_persistence


@pytest.fixture
def recorded_history(temp_db, tmp_path):
    """Import known uploaded prices through the real publication pipeline."""
    from app.host.jobs import JobContext
    from app.workspace.data_manager.logs import Logs
    from app.workspace.data_manager.sources.files import import_files

    folder = tmp_path / "uploads"
    folder.mkdir()
    content = "DateTime,Open,High,Low,Close,Volume\n" + "".join(
        f"2025-01-06 09:{minute:02d}:00,1.10,1.13,1.09,1.12,{minute + 10}\n"
        for minute in (0, 1, 2, 4, 5, 6)
    )
    (folder / "0.input").write_text(content)
    item = {
        "staged": "0.input",
        "name": "EURUSD.csv",
        "symbol": "EURUSD",
        "source": "files",
        "timeframe": "M1",
        "tick_size": 0.0001,
        "market_root": str(tmp_path / "market"),
    }
    context = JobContext("fixture-import", tmp_path / "scratch")
    result = import_files(context, temp_db, str(folder), [item], Logs())
    assert result["completed"] == 1
    return temp_db, result["datasets"][0], tmp_path
