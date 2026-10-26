"""Unit and integration tests for Custom Data indicators HTTP endpoints."""

import json
import sqlite3
from contextlib import closing
from unittest.mock import patch

import pytest
from app.host.persistence import HostPersistence
from app.host.session import SessionManager
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
        cl.headers["Authorization"] = f"Bearer {token}"
        yield cl


def test_custom_data_crud_and_review(client):
    res = client.get("/api/v1/data/custom-data")
    assert res.status_code == 200
    assert res.json()["data"] == []

    add_res = client.post(
        "/api/v1/data/custom-data",
        json={
            "name": "Sentiment",
            "values": [{"name": "Score"}],
            "data_type": "custom",
            "timeframe": "D1",
        },
    )
    assert add_res.status_code == 200
    assert add_res.json()["data"]["name"] == "Sentiment"

    dup_res = client.post(
        "/api/v1/data/custom-data",
        json={
            "name": "Sentiment",
            "values": [{"name": "Score"}],
        },
    )
    assert dup_res.status_code == 409

    edit_res = client.post(
        "/api/v1/data/custom-data/edit",
        json={
            "indicator_name": "Sentiment",
            "updates": {"timeframe": "W1"},
        },
    )
    assert edit_res.status_code == 200
    assert edit_res.json()["data"]["timeframe"] == "W1"

    rev_res = client.get("/api/v1/data/custom-data/review?name=Sentiment")
    assert rev_res.status_code == 200
    assert rev_res.json()["data"]["records"] == []

    path_rev_res = client.get("/api/v1/data/custom-data/Sentiment/records")
    assert path_rev_res.status_code == 200
    assert path_rev_res.json()["data"]["name"] == "Sentiment"


def test_custom_data_formats_and_info(client):
    info_res = client.get("/api/v1/data/custom-data/import-info")
    assert info_res.status_code == 200
    assert "," in info_res.json()["data"]["separators"]

    add_fmt = client.post(
        "/api/v1/data/custom-data/formats",
        json={
            "name": "MyCSV",
            "config": {
                "separator": ";",
                "date_format": "%Y-%m-%d",
                "skip_rows": 1,
                "skip_columns": 0,
                "columns": ["date", "Score"],
            },
        },
    )
    assert add_fmt.status_code == 200
    assert add_fmt.json()["data"]["name"] == "MyCSV"

    edit_fmt = client.post(
        "/api/v1/data/custom-data/formats/edit",
        json={
            "name": "MyCSV",
            "config": {
                "separator": "\t",
                "date_format": "%Y-%m-%d",
                "skip_rows": 0,
                "skip_columns": 0,
                "columns": ["date", "Score"],
            },
        },
    )
    assert edit_fmt.status_code == 200
    assert edit_fmt.json()["data"]["separator"] == "\t"

    del_fmt = client.delete("/api/v1/data/custom-data/formats/MyCSV")
    assert del_fmt.status_code == 200


def test_custom_data_recognize_and_preview(client):
    content = json.dumps(
        {
            "name": "AutoRecognized",
            "values": [{"name": "Score"}],
            "data_type": "custom",
            "timeframe": "D1",
        }
    )
    rec_res = client.post(
        "/api/v1/data/custom-data/recognize",
        json={"filename": "indicator.json", "content": content},
    )
    assert rec_res.status_code == 200
    assert rec_res.json()["data"]["name"] == "AutoRecognized"

    csv_text = "2026-01-01,10.5\n2026-01-02,12.0\n"
    prev_res = client.post(
        "/api/v1/data/custom-data/import-preview",
        json={
            "name": "AutoRecognized",
            "content": csv_text,
            "columns": ["date", "Score"],
        },
    )
    assert prev_res.status_code == 200
    assert prev_res.json()["data"]["total_records"] == 2


def test_custom_data_import_export_clear_delete(client):
    client.post(
        "/api/v1/data/custom-data",
        json={
            "name": "Metrics",
            "values": [{"name": "Val"}],
            "data_type": "custom",
            "timeframe": "D1",
        },
    )

    csv_text = "2026-01-01,10.5\n2026-01-02,12.0\n"
    imp_res = client.post(
        "/api/v1/data/custom-data/import",
        json={
            "name": "Metrics",
            "content": csv_text,
            "columns": ["date", "Val"],
        },
    )
    assert imp_res.status_code == 200
    assert imp_res.json()["data"]["imported_count"] == 2

    exp_res = client.post(
        "/api/v1/data/custom-data/export",
        json={"name": "Metrics"},
    )
    assert exp_res.status_code == 200
    assert "date,Val" in exp_res.json()["data"]["content"]
    assert exp_res.json()["data"]["count"] == 2

    save_res = client.post(
        "/api/v1/data/custom-data/save",
        json={"names": ["Metrics"]},
    )
    assert save_res.status_code == 200
    assert "Metrics" in save_res.json()["data"]["content"]

    clr_res = client.post(
        "/api/v1/data/custom-data/clear",
        json={"names": ["Metrics"]},
    )
    assert clr_res.status_code == 200
    assert clr_res.json()["data"]["cleared_records"] == 2

    rev_res = client.get("/api/v1/data/custom-data/Metrics/records")
    assert rev_res.json()["data"]["records"] == []

    del_res = client.post(
        "/api/v1/data/custom-data/delete",
        json={"names": ["Metrics"]},
    )
    assert del_res.status_code == 200
    assert "Metrics" in del_res.json()["data"]["names"]


def test_custom_data_load_and_jobs(client):
    definitions_json = json.dumps(
        {
            "version": 1,
            "indicators": [
                {
                    "name": "ImportedDef",
                    "values": [{"name": "V1"}],
                    "data_type": "custom",
                    "timeframe": "D1",
                }
            ],
        }
    )
    load_res = client.post(
        "/api/v1/data/custom-data/load",
        json={"content": definitions_json},
    )
    assert load_res.status_code == 200
    assert load_res.json()["data"]["loaded_count"] == 1

    missing_job = client.get("/api/v1/data/custom-data-jobs/nonexistent")
    assert missing_job.status_code == 404

    with patch("app.workspace.data_manager.custom.parse_cot_reports") as mock_cot:
        mock_cot.return_value = {
            "001": {
                "2026-01-01": {
                    "timestamp": "2026-01-01",
                    "values_json": json.dumps({"Commercial Long": 100}),
                }
            }
        }
        cot_res = client.post(
            "/api/v1/data/custom-data/update-cot",
            json={"years": [2026]},
        )
        assert cot_res.status_code == 200
        assert cot_res.json()["data"]["updated_count"] == 1
