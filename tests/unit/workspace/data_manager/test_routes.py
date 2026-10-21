"""Unit and integration tests for Data Manager routes and workspace facade."""

from __future__ import annotations

import runpy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from app.host.bootstrap import AppHost
from app.host.persistence import HostPersistence
from app.workspace.data_manager import (
    AppDataManager,
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
    """Test AppDataManager default instantiation and lifecycle methods."""
    ws = AppDataManager()
    assert isinstance(ws.home, Home)
    assert ws.data_dir == Path("data")
    assert ws.event_bus is None
    assert ws.plugin_mgr is None
    assert ws.broker_registry is None
    assert ws.job_manager is None

    layout = ws.init_workspace()
    assert layout["active_tab"] == "data"
    assert [tab["id"] for tab in layout["tabs"] if tab["core"]] == [
        "data",
        "instruments",
        "sessions",
        "brokers",
        "custom-data",
    ]


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

    workspace = AppDataManager()
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
    app.include_router(create_data_manager_router(AppDataManager()))
    with TestClient(app) as client:
        response = client.get("/data/home/datasets")
    assert response.status_code == 200
    assert response.json()["data"] == []


def test_routes_auth_enforcement() -> None:
    """Test auth dependency rejects requests without token when require_auth=True."""
    workspace = AppDataManager()
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
def test_routes_main_execution(caplog: pytest.LogCaptureFixture) -> None:
    """Test running routes.py standalone under __main__."""
    caplog.set_level("INFO")
    runpy.run_module("app.workspace.data_manager.routes", run_name="__main__")
    assert "FR-DATAMGR-SHELL-INIT" in caplog.text
    assert "Created Data Manager router" in caplog.text


def test_package_exports() -> None:
    """Test AppDataManager and create_data_manager_router re-exported from package."""
    import app.workspace.data_manager as dm

    assert hasattr(dm, "AppDataManager")
    assert hasattr(dm, "create_data_manager_router")
    assert dm.AppDataManager is AppDataManager
    assert dm.create_data_manager_router is create_data_manager_router


def _saved_dataset(dataset_id: str, path: str = "", timeframe: str = "M1") -> None:
    now = datetime.now(UTC).isoformat()
    HostPersistence.create_record(
        "datamgr_datasets",
        {
            "id": dataset_id,
            "source": "recorded",
            "symbol": "EURUSD",
            "underlying": "EURUSD",
            "instrument": "EURUSD",
            "timeframe": timeframe,
            "broker": "b1",
            "broker_name": "Research broker",
            "timezone": "UTC",
            "category": "Forex",
            "date_from": "2026-01-01",
            "date_to": "2026-01-02",
            "bars": 600,
            "created_at": now,
            "updated_at": now,
            "path": path,
        },
    )


def _history(path: Path, count: int = 3) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    times = [
        (datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=i)).isoformat()
        for i in range(count)
    ]
    pq.write_table(
        pa.table(
            {
                "timestamp": times,
                "open": [1.1] * count,
                "high": [1.3] * count,
                "low": [1.0] * count,
                "close": [1.2] * count,
                "volume": [12] * count,
            }
        ),
        path,
    )


def test_shell_snapshot_and_recorded_preview(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """The same recorded array drives table/chart without modifying catalog/history."""
    caplog.set_level("INFO")
    root = tmp_path / "data"
    history = root / "history" / "bars.parquet"
    _history(history, 600)
    _saved_dataset("one", "data/history/bars.parquet")
    _saved_dataset("two", "", "D1")
    before = HostPersistence.read_records("datamgr_datasets")
    raw = history.read_bytes()
    ws = AppDataManager(data_dir=root)
    assert ws.init_workspace() == ws.init_workspace()
    result = ws.open_tab("data", {"dataset_id": "one"})
    assert result["selection"]["id"] == "one"
    assert result["preview"]["state"] == "ready"
    bars = result["preview"]["rows"]
    assert len(bars) == 500
    assert bars[-1]["time"] - bars[0]["time"] == 499 * 60
    assert bars[0]["close"] == 1.2
    assert bars[0]["volume"] == 12
    assert ws.open_tab("chart", {"dataset_id": "two"})["selection"]["timeframe"] == "D1"
    assert ws.open_tab("sessions")["selection"] is None
    assert result["selection"]["id"] == "one"
    assert HostPersistence.read_records("datamgr_datasets") == before
    assert history.read_bytes() == raw
    assert "FR-DATAMGR-SHELL-INIT" in caplog.text
    assert "FR-DATAMGR-SHELL-TAB" in caplog.text


@pytest.mark.parametrize(
    "context", [{"symbol": "EURUSD"}, {"dataset_id": 1}, {"dataset_id": ""}, []]
)
def test_shell_rejects_ambiguous_context(
    context: Any, caplog: pytest.LogCaptureFixture
) -> None:
    """Only explicit catalog IDs can establish a dataset selection."""
    with pytest.raises(ValueError):
        AppDataManager().open_tab("data", context)
    assert "FR-DATAMGR-SHELL-TAB" in caplog.text


@pytest.mark.parametrize(
    "path", ["../outside.parquet", "history/missing.parquet", "history/bad.csv"]
)
def test_shell_missing_and_unsafe_paths(tmp_path: Path, path: str) -> None:
    """Missing or unsafe stored files never produce generated bars."""
    _saved_dataset("one", path)
    result = AppDataManager(data_dir=tmp_path).open_tab("chart", {"dataset_id": "one"})
    assert result["preview"]["state"] in {"error", "unavailable"}
    assert result["preview"]["rows"] == []


def test_shell_unsupported_corrupt_and_oversized_history(tmp_path: Path) -> None:
    """Preview refuses ticks, corrupt Parquet, and files above its read bound."""
    bad = tmp_path / "bad.parquet"
    bad.write_bytes(b"invalid parquet")
    large = tmp_path / "large.parquet"
    with large.open("wb") as stream:
        stream.truncate(32 * 1024 * 1024 + 1)
    _saved_dataset("tick", "bad.parquet", "TICK")
    _saved_dataset("bad", "bad.parquet")
    _saved_dataset("large", "large.parquet")
    ws = AppDataManager(data_dir=tmp_path)
    assert (
        ws.open_tab("chart", {"dataset_id": "tick"})["preview"]["state"]
        == "unavailable"
    )
    assert ws.open_tab("chart", {"dataset_id": "bad"})["preview"]["state"] == "error"
    assert (
        "32 MiB" in ws.open_tab("chart", {"dataset_id": "large"})["preview"]["reason"]
    )


def test_shell_http_errors_and_session_isolation(tmp_path: Path) -> None:
    """Independent request snapshots never inherit another request's selection."""
    _saved_dataset("one")
    app = FastAPI()
    app.include_router(create_data_manager_router(AppDataManager(data_dir=tmp_path)))
    with TestClient(app) as first, TestClient(app) as second:
        assert first.get("/data/workspace").json()["data"]["active_tab"] == "data"
        selected = first.post(
            "/data/workspace/tabs/chart", json={"context": {"dataset_id": "one"}}
        )
        assert selected.json()["data"]["selection"]["id"] == "one"
        assert (
            second.post("/data/workspace/tabs/data", json={}).json()["data"][
                "selection"
            ]
            is None
        )
        missing = first.post(
            "/data/workspace/tabs/data", json={"context": {"dataset_id": "missing"}}
        )
        assert missing.status_code == 404
        assert missing.json()["status"] == "error"
        assert first.post("/data/workspace/tabs/unknown", json={}).status_code == 422
        assert (
            first.post("/data/workspace/tabs/data", json={"path": "bad"}).status_code
            == 422
        )
        assert (
            first.post("/data/workspace/tabs/data", json={"context": []}).status_code
            == 422
        )
    locked = FastAPI()
    locked.include_router(create_data_manager_router(require_auth=True))
    with TestClient(locked) as client:
        assert client.get("/data/workspace").status_code == 401
        assert client.post("/data/workspace/tabs/data", json={}).status_code == 401


def test_shell_symlink_escape(tmp_path: Path) -> None:
    """A catalog path through a symlink cannot escape the configured root."""
    root = tmp_path / "data"
    root.mkdir()
    outside = tmp_path / "outside.parquet"
    _history(outside)
    link = root / "link.parquet"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("Symlink creation is unavailable on this host.")
    _saved_dataset("link", "link.parquet")
    assert (
        AppDataManager(data_dir=root).open_tab("chart", {"dataset_id": "link"})[
            "preview"
        ]["state"]
        == "error"
    )


def test_shell_rejects_invalid_recorded_prices(tmp_path: Path) -> None:
    """Corrupt numerical rows do not reach either the chart or table."""
    path = tmp_path / "bad-prices.parquet"
    _history(path)
    table = pq.read_table(path)
    table = table.set_column(
        table.column_names.index("high"), "high", pa.array([0.1] * 3)
    )
    pq.write_table(table, path)
    _saved_dataset("bad-prices", "bad-prices.parquet")
    preview = AppDataManager(data_dir=tmp_path).open_tab(
        "chart", {"dataset_id": "bad-prices"}
    )["preview"]
    assert preview["state"] == "error"
    assert preview["rows"] == []
