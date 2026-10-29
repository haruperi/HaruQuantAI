"""Integration tests for Data Manager Help HTTP endpoints."""

import json
import sqlite3
from contextlib import closing

import pytest
from app.core.host.session import SessionManager
from app.host.persistence import HostPersistence
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
        cl.headers.update({"Authorization": f"Bearer {token}"})
        yield cl


def test_get_help_endpoint(client):
    # Test overview default
    res = client.get("/api/v1/data/help")
    assert res.status_code == 200
    payload = res.json()["data"]
    assert payload["topic"] == "overview"
    assert payload["title"] == "Data Manager Overview"
    assert len(payload["tutorials"]) >= 3
    assert len(payload["links"]) == 3

    # Test specific topic (export)
    res_export = client.get("/api/v1/data/help?topic=export")
    assert res_export.status_code == 200
    export_payload = res_export.json()["data"]
    assert export_payload["topic"] == "export"
    assert export_payload["tab"] == "Export"
    assert export_payload["title"] == "Multi-Format Data Export"


def test_help_topics_tutorials_and_articles(client):
    res_topics = client.get("/api/v1/data/help/topics")
    assert res_topics.status_code == 200
    assert len(res_topics.json()["data"]["topics"]) == 11

    res_tuts = client.get("/api/v1/data/help/tutorials?topic=symbols")
    assert res_tuts.status_code == 200
    assert len(res_tuts.json()["data"]["tutorials"]) == 1

    res_articles = client.get("/api/v1/data/help/articles")
    assert res_articles.status_code == 200
    assert len(res_articles.json()["data"]["articles"]) == 3


def test_help_search_endpoint(client):
    res = client.get("/api/v1/data/help/search?query=metatrader")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total_matches"] > 0
    assert len(data["articles"]) > 0
