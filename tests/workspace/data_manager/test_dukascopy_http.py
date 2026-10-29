"""Integration tests for Data Manager Dukascopy HTTP endpoints."""

import json
import sqlite3
from contextlib import closing

import pytest
from app.core.host.persistence import HostPersistence
from app.core.host.session import SessionManager
from app.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def gateway(tmp_path):
    path = tmp_path / "transport.db"
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript("""
            CREATE TABLE host_settings (
                scope TEXT NOT NULL, key TEXT NOT NULL, value_json TEXT NOT NULL,
                schema_version INTEGER NOT NULL DEFAULT 1, updated_at_utc TEXT NOT NULL,
                PRIMARY KEY(scope,key));
            CREATE TABLE host_session (
                session_id TEXT PRIMARY KEY, token_hash TEXT NOT NULL UNIQUE,
                username TEXT NOT NULL, peer_id TEXT NOT NULL,
                created_at_utc TEXT NOT NULL, expires_at_utc TEXT NOT NULL,
                revoked_at_utc TEXT, status TEXT NOT NULL);
            CREATE TABLE host_entities (
                entity_id TEXT NOT NULL, entity_type TEXT NOT NULL, scope TEXT NOT NULL,
                payload TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1,
                created_at_utc TEXT NOT NULL, updated_at_utc TEXT NOT NULL,
                PRIMARY KEY(entity_id,entity_type));
            CREATE TABLE datamgr_datasets (
                id TEXT PRIMARY KEY, source TEXT NOT NULL, symbol TEXT NOT NULL,
                underlying TEXT NOT NULL, timeframe TEXT NOT NULL,
                broker TEXT NOT NULL, timezone TEXT NOT NULL,
                category TEXT NOT NULL, date_from TEXT NOT NULL, date_to TEXT NOT NULL,
                bars INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL, path TEXT NOT NULL DEFAULT '',
                data_kind TEXT NOT NULL DEFAULT 'bars', quality_score REAL NOT NULL DEFAULT 1.0,
                lineage_json TEXT NOT NULL DEFAULT '{}', schema_version INTEGER NOT NULL DEFAULT 1);
        """)
    gw = HostPersistence(path)
    gw.create_records(
        "host_settings",
        [
            {
                "scope": "application",
                "key": "user_access",
                "value_json": json.dumps(
                    {
                        "username": "tester",
                        "password_hash": SessionManager.hash_password("password"),
                    }
                ),
                "updated_at_utc": "unchanged",
            }
        ],
    )
    return gw


@pytest.fixture
def client(gateway):
    with TestClient(create_app(gateway)) as cl:
        login = cl.post("/api/v1/auth/login", json={"password": "password"})
        assert login.status_code == 200
        token = login.json()["data"]["token"]
        cl.headers.update({"Authorization": f"Bearer {token}"})
        yield cl


def test_http_disclaimer(client):
    res = client.get("/api/v1/data/dukascopy/disclaimer")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"]["title"] == "Dukascopy data disclaimer"


def test_http_catalog(client):
    res = client.get("/api/v1/data/dukascopy/catalog")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert "symbols" in body["data"]


def test_http_add_and_dataset_routes(client):
    # Test direct Dukascopy add
    res = client.post(
        "/api/v1/data/dukascopy/add",
        json={"symbols": ["EURUSD"], "dataType": "M1", "postfix": "_TEST"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert len(body["data"]["records"]) == 1
    ds_id = body["data"]["records"][0]["id"]

    # Test clear dataset
    res_clear = client.post(f"/api/v1/data/datasets/{ds_id}/clear")
    assert res_clear.status_code == 200

    # Test review-chart
    res_chart = client.post(
        "/api/v1/data/datasets/review-chart", json={"dataset_id": ds_id}
    )
    assert res_chart.status_code == 200
    assert "bars" in res_chart.json()["data"]

    # Test delete dataset
    res_del = client.post(f"/api/v1/data/datasets/{ds_id}/delete")
    assert res_del.status_code == 200


def test_http_ui_datasets_create_and_provider_download(client):
    # Test UI /datasets route mapping to Dukascopy
    res = client.post(
        "/api/v1/data/datasets",
        json={
            "source": "dukascopy",
            "symbol": "GBPUSD",
            "underlying": "GBPUSD",
            "timeframe": "M1",
            "broker": "default",
            "instrument": "GBPUSD",
        },
    )
    assert res.status_code == 200
    assert res.json()["data"]["id"] == "dukascopy:GBPUSD:M1"
    assert res.json()["data"]["symbolDefinition"] == "GBPUSD"

    # Test UI /providers/download fallback
    res_down = client.post(
        "/api/v1/data/providers/download",
        json={"provider": "other", "symbol": "EURUSD"},
    )
    assert res_down.status_code == 422

    # Submission delegates to the backend job owner instead of pretending completion.
    from unittest.mock import patch

    with patch(
        "app.workspace.data_manager.sources.start_download",
        return_value={"job_id": "job-1", "status": "QUEUED"},
    ) as submit:
        response = client.post(
            "/api/v1/data/providers/download",
            json={
                "provider": "dukascopy",
                "symbol": "GBPUSD",
                "timeframe": "M1",
                "date_from": "2025-01-01",
                "date_to": "2025-01-02",
            },
        )
        assert response.status_code == 200
        assert response.json()["data"]["job_id"] == "job-1"
        submit.assert_called_once()
