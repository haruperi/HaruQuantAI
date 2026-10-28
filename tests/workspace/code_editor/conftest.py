"""Isolate editor tests from the user's database; seed real Parquet history."""

import json
import sqlite3
from datetime import UTC, datetime, timedelta

import polars as pl
import pytest
from app.host.persistence import HostPersistence
from app.workspace.code_editor import _storage, http
from app.workspace.code_editor.import_export import ImportExport
from app.workspace.code_editor.indicator_tester import IndicatorTester
from app.workspace.code_editor.registry import registry
from app.workspace.code_editor.routes import CodeEditor


@pytest.fixture(autouse=True)
def isolated_editor(tmp_path, monkeypatch):
    database = tmp_path / "editor.db"
    sqlite3.connect(database).close()
    gateway = HostPersistence(database)
    assert gateway.ensure_datasets_schema()["success"]
    history = tmp_path / "history.parquet"
    count = 300
    closes = [1.1 + index * 0.00001 for index in range(count)]
    pl.DataFrame(
        {
            "DateTime": [
                datetime(2025, 1, 1, tzinfo=UTC) + timedelta(hours=i)
                for i in range(count)
            ],
            "Open": closes,
            "High": [v + 0.001 for v in closes],
            "Low": [v - 0.001 for v in closes],
            "Close": closes,
            "Volume": [1000] * count,
        }
    ).write_parquet(history)
    assert gateway.create_records(
        "datamgr_datasets",
        {
            "id": "test:EURUSD:H1",
            "source": "test",
            "symbol": "EURUSD",
            "underlying": "EURUSD",
            "timeframe": "H1",
            "broker": "test",
            "timezone": "UTC",
            "category": "Forex",
            "date_from": "2025-01-01",
            "date_to": "2025-01-13",
            "bars": count,
            "created_at": "2025-01-01",
            "updated_at": "2025-01-01",
            "path": str(history),
            "lineage_json": json.dumps({"tick_size": 0.00001}),
        },
    )["success"]
    monkeypatch.setattr(_storage, "HostPersistence", lambda: gateway)
    monkeypatch.setattr(http, "_code_editor", CodeEditor())
    monkeypatch.setattr(http, "_indicator_tester", IndicatorTester())
    monkeypatch.setattr(http, "_import_export", ImportExport())
    registry.blocks.clear()
    registry.tools.clear()
    registry._tools_by_path.clear()
    yield gateway
    registry.blocks.clear()
    registry.tools.clear()
    registry._tools_by_path.clear()
