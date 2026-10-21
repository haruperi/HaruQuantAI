"""Unit and integration tests for Data Manager routes and workspace facade."""

from __future__ import annotations

import runpy
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.host.bootstrap import AppHost
from app.host.persistence import HostPersistence
from app.workspace.data_manager import (
    DataManagerWorkspace,
    create_data_manager_router,
)
from app.workspace.data_manager.home import Home
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def test_db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fixture providing initialized isolated SQLite database file path."""
    db_file = tmp_path / "test_datamgr_routes.db"
    monkeypatch.setattr(HostPersistence, "DEFAULT_DB_PATH", db_file)
    return db_file


def test_workspace_initialization() -> None:
    """Test DataManagerWorkspace default instantiation and lifecycle methods."""
    ws = DataManagerWorkspace()
    assert isinstance(ws.home, Home)
    assert ws.data_dir == Path("data")
    assert ws.event_bus is None
    assert ws.plugin_mgr is None
    assert ws.broker_registry is None
    assert ws.job_manager is None

    counts = ws.initialize_defaults()
    assert isinstance(counts, dict)
    assert counts.get("brokers") == 0


def test_routes_direct_endpoints() -> None:
    """Test /data/home/overview and /data/home/datasets via direct FastAPI test app."""
    now_iso = datetime.now(UTC).isoformat()
    HostPersistence.create_record(
        "datamgr_datasets",
        {
            "id": "ds:route_test",
            "source": "dukascopy",
            "symbol": "EURUSD",
            "underlying": "EUR/USD Spot",
            "instrument": "EURUSD",
            "timeframe": "M1",
            "broker": "dukascopy",
            "broker_name": "Dukascopy Broker",
            "timezone": "UTC",
            "category": "Forex",
            "date_from": "2026-01-01",
            "date_to": "2026-01-05",
            "bars": 100,
            "path": "data/history/dukascopy/EURUSD/M1.parquet",
            "created_at": now_iso,
            "updated_at": now_iso,
        },
    )

    workspace = DataManagerWorkspace()
    router = create_data_manager_router(workspace)

    app = FastAPI()
    app.include_router(router)

    with TestClient(app) as client:
        # Overview endpoint
        res = client.get("/data/home/overview")
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "success"
        assert body["data"]["datasets_count"] == 1
        assert body["data"]["total_bars"] == 100

        # Datasets endpoint
        res = client.get("/data/home/datasets")
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "success"
        assert len(body["data"]) == 1
        assert body["data"][0]["symbol"] == "EURUSD"
        assert body["data"][0]["total_days"] == 4
        assert body["data"] == [
            item.to_dict() for item in workspace.home.get_saved_datasets()
        ]
        assert body["data"][0]["total_records"] == 100
        assert body["data"][0]["broker_name"] == "Dukascopy Broker"
        assert body["data"][0]["underlying"] == "EUR/USD Spot"
        assert body["data"][0]["path"] == "data/history/dukascopy/EURUSD/M1.parquet"
        assert body["data"][0]["bar_type"] == "start"


def test_empty_catalog_response() -> None:
    """An empty database produces a successful empty catalog, not fallback rows."""
    app = FastAPI()
    app.include_router(create_data_manager_router(DataManagerWorkspace()))
    with TestClient(app) as client:
        response = client.get("/data/home/datasets")
    assert response.status_code == 200
    assert response.json()["data"] == []


def test_routes_auth_enforcement() -> None:
    """Test auth dependency rejects requests without token when require_auth=True."""
    workspace = DataManagerWorkspace()
    router = create_data_manager_router(workspace, require_auth=True)

    app = FastAPI()
    app.include_router(router)

    with TestClient(app) as client:
        res = client.get("/data/home/overview")
        assert res.status_code == 401
        assert "Active session required" in res.json()["detail"]

        res = client.get(
            "/data/home/overview",
            headers={"Authorization": "Bearer invalid_token_123"},
        )
        assert res.status_code == 401
        assert "Invalid or expired session token" in res.json()["detail"]


def test_routes_bootstrap_app_integration(tmp_path: Path) -> None:
    """Test full bootstrap app integration mounting Data Manager routes under /api/v1."""
    data_dir = tmp_path / "data"
    host = AppHost(
        data_dir=data_dir,
        headless=False,
    )
    app = host.startup()
    host.initialize_db()
    host.register_modules(app)
    host.broadcast_event("system", "host.ready")

    with TestClient(app) as client:
        res = client.get("/api/v1/data/home/overview")
        assert res.status_code == 200
        assert res.json()["status"] == "success"

        res_raw = client.get("/data/home/overview")
        assert res_raw.status_code == 200

        res_datasets = client.get("/api/v1/data/home/datasets")
        assert res_datasets.status_code == 200
        assert isinstance(res_datasets.json()["data"], list)

    host.shutdown()


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_routes_main_execution(capsys: pytest.CaptureFixture[str]) -> None:
    """Test running routes.py standalone under __main__."""
    runpy.run_module("app.workspace.data_manager.routes", run_name="__main__")
    captured = capsys.readouterr()
    assert "Initialized defaults" in captured.out
    assert "Created Data Manager router" in captured.out
    assert "Workspace overview" in captured.out


def test_package_exports() -> None:
    """Test DataManagerWorkspace and create_data_manager_router re-exported from package."""
    import app.workspace.data_manager as dm

    assert hasattr(dm, "DataManagerWorkspace")
    assert hasattr(dm, "create_data_manager_router")
    assert dm.DataManagerWorkspace is DataManagerWorkspace
    assert dm.create_data_manager_router is create_data_manager_router
