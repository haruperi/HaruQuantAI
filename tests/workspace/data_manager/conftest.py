"""Isolated persistence and HTTP fixtures for Data Manager services."""

import sqlite3
from unittest.mock import patch

import pytest
from app.host.persistence import HostPersistence
from app.host.transport import register_transport_exception_handlers
from app.workspace.data_manager import http as symbols_http
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def symbol_http(temp_db):
    application = FastAPI()
    application.state.persistence = temp_db
    application.include_router(symbols_http.create_router())
    application.dependency_overrides[symbols_http._access] = lambda: None
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
