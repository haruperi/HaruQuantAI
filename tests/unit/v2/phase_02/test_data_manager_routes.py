"""Unit tests for Data Manager workspace home and SQX dataset REST routes.

Description:
    Tests the extended REST endpoints in app.workspace.data_manager.routes:
    - Home overview statistics and documentation links.
    - Dataset metadata editing (PUT /datasets/{id}).
    - Dataset on-disk Parquet data clearing while retaining definitions (POST /datasets/{id}/clear).
    - Chart review OHLCV bar extraction (POST /datasets/review-chart).
    - Dataset timezone cloning (POST /datasets/clone-timezone).
    - Provider download persistence into Parquet partitions and database catalog.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Verify connected Data Manager Home and dataset operations.

Key Capabilities:
    - FR-DATA-INTEGRATION-DATASETS: REST endpoints for SQX dataset CRUD and slice review.
    - FR-DATA-INTEGRATION-PROVIDERS: Downloaded provider data written to Parquet and catalog.
    - FR-WORKSPACE-DATAMGR-HOME: Workspace overview metrics and documentation cards.

Python API Usage:
    Run via pytest:
    `pytest tests/unit/v2/phase_02/test_data_manager_routes.py -v --no-cov`

CLI Usage:
    `uv run pytest tests/unit/v2/phase_02/test_data_manager_routes.py -v --no-cov`
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from app.host.persistence import DatabaseManager
from app.host.resources import ResourceManager
from app.workspace.data_manager.data import BarRecord, CatalogService
from app.workspace.data_manager.routes import create_data_router
from app.workspace.data_manager.storage import MarketDataStorage
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def test_setup(tmp_path: Path) -> tuple[TestClient, CatalogService, DatabaseManager]:
    """Create isolated DatabaseManager, CatalogService, and TestClient."""
    db_file = tmp_path / "test_dm_routes.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()

    res_dir = tmp_path / "resources"
    res_dir.mkdir(parents=True, exist_ok=True)
    res_mgr = ResourceManager(root_dir=res_dir)

    catalog = CatalogService(
        db, storage=MarketDataStorage(base_dir=res_dir / "datasets")
    )

    app = FastAPI()
    router = create_data_router(db_manager=db, resource_manager=res_mgr)
    app.include_router(router)

    client = TestClient(app)
    return client, catalog, db


def test_home_overview_and_doc_links(
    test_setup: tuple[TestClient, CatalogService, DatabaseManager],
) -> None:
    """Validate GET /data/home/overview and GET /data/home/doc-links."""
    client, catalog, _ = test_setup

    # Overview endpoint
    resp = client.get("/data/home/overview")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "datasets_count" in data
    assert "instruments_count" in data
    assert "total_bars" in data
    assert data["workspace_name"] == "Data Manager"

    # Documentation links endpoint
    resp_docs = client.get("/data/home/doc-links")
    assert resp_docs.status_code == 200
    links = resp_docs.json()["data"]
    assert len(links) >= 6
    titles = [link["title"] for link in links]
    assert "Import History Data MT4" in titles
    assert "Import Data to MT5" in titles
    assert "Full Documentation" in titles


def test_dataset_edit_and_clear_operations(
    test_setup: tuple[TestClient, CatalogService, DatabaseManager],
) -> None:
    """Validate PUT /data/datasets/{id} and POST /data/datasets/{id}/clear."""
    client, catalog, _ = test_setup

    bars = [
        BarRecord(
            timestamp_utc="2025-05-01T10:00:00Z",
            open=1.1000,
            high=1.1050,
            low=1.0950,
            close=1.1020,
            volume=500.0,
        ),
        BarRecord(
            timestamp_utc="2025-05-01T10:01:00Z",
            open=1.1020,
            high=1.1060,
            low=1.1010,
            close=1.1040,
            volume=600.0,
        ),
    ]
    catalog.save_bars(
        source="test_src",
        symbol="EURUSD",
        timeframe="M1",
        bars=bars,
    )
    dataset_id = "test_src:M1:EURUSD"

    # Verify initial dataset state
    ds_resp = client.get(f"/data/datasets/{dataset_id}")
    assert ds_resp.status_code == 200
    assert ds_resp.json()["data"]["symbol"] == "EURUSD"

    # Edit metadata
    edit_resp = client.put(
        f"/data/datasets/{dataset_id}",
        json={"category": "ForexMajor", "timezone": "Europe/Prague"},
    )
    assert edit_resp.status_code == 200
    assert edit_resp.json()["data"]["updated"] is True

    # Check updated dataset metadata
    updated_ds = client.get(f"/data/datasets/{dataset_id}").json()["data"]
    assert updated_ds["category"] == "ForexMajor"
    assert updated_ds["timezone"] == "Europe/Prague"

    # Clear data (clears parquet, resets bars=0, preserves row)
    clear_resp = client.post(f"/data/datasets/{dataset_id}/clear")
    assert clear_resp.status_code == 200
    assert clear_resp.json()["data"]["cleared"] is True

    cleared_ds = client.get(f"/data/datasets/{dataset_id}").json()["data"]
    assert cleared_ds["bars"] == 0
    assert cleared_ds["date_from"] == ""
    assert cleared_ds["date_to"] == ""

    # Test 404 for unknown dataset
    unknown_edit = client.put("/data/datasets/nonexistent", json={"category": "Forex"})
    assert unknown_edit.status_code == 404
    unknown_clear = client.post("/data/datasets/nonexistent/clear")
    assert unknown_clear.status_code == 404


def test_dataset_chart_review(
    test_setup: tuple[TestClient, CatalogService, DatabaseManager],
) -> None:
    """Validate POST /data/datasets/review-chart."""
    client, catalog, _ = test_setup

    bars = [
        BarRecord(
            timestamp_utc="2025-06-01T12:00:00Z",
            open=1.2000,
            high=1.2050,
            low=1.1950,
            close=1.2020,
            volume=300.0,
        ),
        BarRecord(
            timestamp_utc="2025-06-01T12:01:00Z",
            open=1.2020,
            high=1.2080,
            low=1.2010,
            close=1.2070,
            volume=400.0,
        ),
    ]
    catalog.save_bars(
        source="test_chart",
        symbol="GBPUSD",
        timeframe="M1",
        bars=bars,
    )
    dataset_id = "test_chart:M1:GBPUSD"

    # Request review bars
    review_resp = client.post(
        "/data/datasets/review-chart",
        json={"dataset_id": dataset_id, "limit": 10},
    )
    assert review_resp.status_code == 200
    res_data = review_resp.json()["data"]
    assert res_data["count"] == 2
    assert len(res_data["bars"]) == 2
    assert res_data["bars"][0]["open"] == 1.2000
    assert res_data["bars"][1]["close"] == 1.2070


def test_dataset_clone_to_timezone(
    test_setup: tuple[TestClient, CatalogService, DatabaseManager],
) -> None:
    """Validate POST /data/datasets/clone-timezone."""
    client, catalog, _ = test_setup

    bars = [
        BarRecord(
            timestamp_utc="2025-07-01T14:00:00Z",
            open=1.3000,
            high=1.3050,
            low=1.2950,
            close=1.3020,
            volume=100.0,
        ),
    ]
    catalog.save_bars(
        source="test_clone",
        symbol="USDJPY",
        timeframe="M1",
        bars=bars,
    )
    dataset_id = "test_clone:M1:USDJPY"

    clone_resp = client.post(
        "/data/datasets/clone-timezone",
        json={
            "dataset_id": dataset_id,
            "target_timezone": "America/New_York",
            "new_dataset_id": "test_clone:M1:USDJPY_NY",
        },
    )
    assert clone_resp.status_code == 201
    assert clone_resp.json()["data"]["cloned_id"] == "test_clone:M1:USDJPY_NY"


def test_provider_download_persistence(tmp_path: Path) -> None:
    """Validate that provider downloads save bars to catalog and Parquet."""
    db_file = tmp_path / "test_download.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()

    res_dir = tmp_path / "resources"
    res_dir.mkdir(parents=True, exist_ok=True)
    res_mgr = ResourceManager(root_dir=res_dir)

    # Mock provider manager to return sample bars
    mock_provider_mgr = MagicMock()
    sample_bars = [
        BarRecord(
            timestamp_utc="2025-08-01T09:00:00Z",
            open=1.1100,
            high=1.1150,
            low=1.1090,
            close=1.1130,
            volume=250.0,
        ),
        BarRecord(
            timestamp_utc="2025-08-01T09:01:00Z",
            open=1.1130,
            high=1.1180,
            low=1.1120,
            close=1.1170,
            volume=350.0,
        ),
    ]
    mock_provider_mgr.download.return_value = sample_bars
    mock_provider_mgr.list_capabilities.return_value = []

    app = FastAPI()
    router = create_data_router(
        db_manager=db,
        resource_manager=res_mgr,
        provider_manager=mock_provider_mgr,
    )
    app.include_router(router)
    client = TestClient(app)

    payload = {
        "provider": "dukascopy",
        "symbol": "EURUSD",
        "timeframe": "M1",
        "date_from": "2025-08-01",
        "date_to": "2025-08-01",
        "async_job": False,
    }
    resp = client.post("/data/providers/download", json=payload)
    assert resp.status_code == 200
    assert resp.json()["data"]["bars_count"] == 2

    # Verify catalog contains the newly saved dataset
    catalog = CatalogService(db)
    datasets = catalog.list_datasets(source="dukascopy", symbol="EURUSD")
    assert len(datasets) == 1
    assert datasets[0].symbol == "EURUSD"
    assert datasets[0].bars == 2
