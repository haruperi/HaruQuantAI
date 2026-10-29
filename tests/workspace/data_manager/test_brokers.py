"""Broker mutations and JSON round trips against isolated SQLite."""

import json
import sqlite3
from contextlib import closing

import pytest
from app.core.host.persistence import HostPersistence
from app.workspace.data_manager.brokers import Brokers


@pytest.fixture
def brokers(tmp_path):
    database = tmp_path / "brokers.db"
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("""
            CREATE TABLE datamgr_broker (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                is_system INTEGER NOT NULL DEFAULT 0,
                description TEXT DEFAULT '',
                stockpicker_use INTEGER DEFAULT 0,
                mt_use INTEGER DEFAULT 0,
                server_timezone TEXT DEFAULT 'UTC',
                postfix TEXT DEFAULT '',
                enabled INTEGER DEFAULT 1,
                created_at_utc TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL,
                clock_policy_json TEXT NOT NULL DEFAULT '{}',
                clock_policy_revision INTEGER NOT NULL DEFAULT 0
            )
        """)
        connection.commit()
    return Brokers(HostPersistence(database))


def test_crud(brokers):
    created = brokers.add("A", mt_use=True, clock_policy={"offset": 120})
    assert created["success"]
    assert created["data"]["clock_policy"] == {"offset": 120}
    assert created["data"]["created_at_utc"]
    assert brokers.add("B")["success"]
    edited = brokers.edit(["A", "B", "A"], enabled=False, postfix=".x")
    assert edited["success"]
    assert len(edited["data"]) == 2
    assert all(not row["enabled"] for row in edited["data"])
    renamed = brokers.edit("A", {"name": "Renamed"})
    assert renamed["success"]
    assert renamed["data"][0]["clock_policy"] == {"offset": 120}
    assert renamed["data"][0]["created_at_utc"] == created["data"]["created_at_utc"]
    assert brokers.delete(["Renamed", "B"])["success"]
    assert brokers.list()["data"] == []


@pytest.mark.parametrize("operation", ["edit", "delete"])
def test_bulk_missing_rolls_back(brokers, operation):
    assert brokers.add("A")["success"]
    result = (
        brokers.edit(["A", "missing"], description="changed")
        if operation == "edit"
        else brokers.delete(["A", "missing"])
    )
    assert not result["success"]
    assert result["error"]["code"] == "not_found"
    assert brokers.list()["data"][0]["description"] == ""


def test_conflicts(brokers):
    assert brokers.add("A")["success"]
    assert brokers.add("B")["success"]
    for result in (brokers.add("A"), brokers.edit("A", name="B")):
        assert not result["success"]
        assert result["error"]["code"] == "conflict"


@pytest.mark.parametrize(
    "fields",
    [
        {"name": " "},
        {"server_timezone": "Invalid/Zone"},
        {"enabled": "false"},
        {"clock_policy": []},
        {"clock_policy_revision": -1},
        {"clock_policy_revision": True},
        {"unknown": True},
        {"description": None},
        {"clock_policy": {"offset": float("nan")}},
    ],
)
def test_validation(brokers, fields):
    result = brokers.add(**{"name": "A", **fields})
    assert not result["success"]
    assert result["error"]["code"] == "validation"
    assert brokers.list()["data"] == []


def test_invalid_targets(brokers):
    for result in (
        brokers.delete([]),
        brokers.delete(" "),
        brokers.edit("A"),
        brokers.edit(["A", "B"], name="C"),
    ):
        assert not result["success"]
        assert result["error"]["code"] == "validation"


def test_json_round_trip_and_atomic_import(brokers, tmp_path):
    assert brokers.add("A", mt_use=True, clock_policy={"mode": "fixed"})["success"]
    target = tmp_path / "brokers.json"
    assert brokers.save(target)["data"]["count"] == 1
    exported = json.loads(target.read_text(encoding="utf-8"))
    assert "id" not in exported[0]
    assert "customized_stocks" not in exported[0]
    assert brokers.delete("A")["success"]
    assert brokers.load(target)["success"]
    row = brokers.list()["data"][0]
    assert row["mt_use"] is True
    assert row["clock_policy"] == {"mode": "fixed"}
    target.write_text(json.dumps([{"name": "B"}, {"name": "A"}]), encoding="utf-8")
    assert not brokers.load(target)["success"]
    assert [r["name"] for r in brokers.list()["data"]] == ["A"]


@pytest.mark.parametrize(
    "content", ["{}", "[null]", '[{"name": "A"}, {"name": "A"}]', "{"]
)
def test_invalid_import(brokers, tmp_path, content):
    target = tmp_path / "invalid.json"
    target.write_text(content, encoding="utf-8")
    assert not brokers.load(target)["success"]
    assert brokers.list()["data"] == []


@pytest.fixture
def broker_http(brokers, temp_db):
    from app.core.host.transport import register_transport_exception_handlers
    from app.workspace.data_manager import _access, create_router
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    with closing(sqlite3.connect(temp_db.database_path)) as source:
        symbols_sql = source.execute(
            "SELECT sql FROM sqlite_master WHERE name='datamgr_symbols'"
        ).fetchone()[0]
    with closing(sqlite3.connect(brokers.gateway.database_path)) as connection:
        connection.execute(symbols_sql)
        connection.executescript("""
            CREATE TABLE datamgr_sessions (
                id INTEGER PRIMARY KEY, name TEXT UNIQUE, description TEXT DEFAULT '',
                timezone TEXT DEFAULT 'UTC', windows_json TEXT DEFAULT '[]',
                holidays_json TEXT DEFAULT '[]', is_default INTEGER DEFAULT 0,
                broker_id INTEGER DEFAULT -1);
            CREATE TABLE datamgr_broker_stock (
                ID INTEGER PRIMARY KEY, TICKER TEXT NOT NULL, BROKER_ID INTEGER NOT NULL,
                FOREIGN KEY(BROKER_ID) REFERENCES datamgr_broker(id));
            CREATE TABLE datamgr_datasets (id TEXT PRIMARY KEY, broker TEXT);
        """)
        connection.commit()
    application = FastAPI()
    application.state.persistence = brokers.gateway
    application.include_router(create_router())
    application.dependency_overrides[_access] = lambda: None
    register_transport_exception_handlers(application)
    with TestClient(application) as client:
        yield client


def test_http_crud_and_transfer(broker_http):
    base = "/api/v1/data/brokers"
    created = broker_http.post(
        base, json={"name": "A", "timezone": "EETUS", "stockpicker_use": True}
    )
    assert created.status_code == 200, created.text
    row = created.json()["data"]
    assert row["timezone"] == "EETUS"
    assert row["stocks"] == []
    identifier = row["id"]
    edited = broker_http.post(base, json={"id": identifier, "description": "changed"})
    assert edited.status_code == 200, edited.text
    stocks = broker_http.put(
        f"{base}/{identifier}/stocks", json={"stocks": [" AAPL ", "AAPL"]}
    )
    assert stocks.status_code == 200, stocks.text
    assert stocks.json()["data"]["stocks"] == ["AAPL"]
    assert broker_http.get(base).json()["data"][0]["customized_stocks"] == 1
    exported = broker_http.post(base + "/save", json={}).json()["data"]
    assert json.loads(exported["content"])[0]["name"] == "A"
    assert (
        broker_http.post(base + "/delete", json={"ids": [identifier]}).status_code
        == 200
    )
    assert broker_http.get(base).json()["data"] == []
    assert (
        broker_http.post(
            base + "/load", json={"content": exported["content"]}
        ).status_code
        == 200
    )
    assert (
        broker_http.post(
            base + "/load", json={"content": exported["content"]}
        ).status_code
        == 409
    )


def test_http_bulk_and_protections(broker_http, brokers):
    base = "/api/v1/data/brokers"
    a = broker_http.post(base, json={"name": "A"}).json()["data"]["id"]
    b = broker_http.post(base, json={"name": "B"}).json()["data"]["id"]
    assert (
        broker_http.post(
            base + "/edit", json={"ids": [a, b], "updates": {"enabled": False}}
        ).status_code
        == 200
    )
    assert all(not row["enabled"] for row in broker_http.get(base).json()["data"])
    assert (
        broker_http.post(
            base + "/edit", json={"ids": [a, "999"], "updates": {"description": "oops"}}
        ).status_code
        == 404
    )
    assert broker_http.post(base, json={"id": a, "name": "B"}).status_code == 409
    system = brokers.add("System", is_system=True)["data"]
    edited = broker_http.post(
        base, json={"id": str(system["id"]), "description": "Edited system profile"}
    )
    assert edited.status_code == 200, edited.text
    assert edited.json()["data"]["is_system"] is True
    assert (
        broker_http.post(
            base + "/edit",
            json={"ids": [str(system["id"])], "updates": {"is_system": False}},
        ).status_code
        == 200
    )
    assert (
        broker_http.post(
            base + "/delete", json={"ids": [str(system["id"])]}
        ).status_code
        == 200
    )
    assert brokers.gateway.create_records(
        "datamgr_datasets", {"id": "dataset", "broker": b}
    )["success"]
    assert broker_http.post(base + "/delete", json={"ids": [a, b]}).status_code == 409
    assert len(broker_http.get(base).json()["data"]) == 2


def test_all_broker_cli_commands(brokers, monkeypatch, capsys, tmp_path):
    import argparse

    from app.workspace.data_manager import register_commands

    monkeypatch.setattr("app.workspace.data_manager.brokers.Brokers", lambda: brokers)
    parser = argparse.ArgumentParser()
    register_commands(parser.add_subparsers(dest="command", required=True))
    path = str(tmp_path / "brokers.json")
    commands = [
        ["add", "--name", "A", "--mt-use"],
        ["add", "--name", "B"],
        ["list", "--page-size", "1"],
        ["edit", "A", "B", "--no-enabled"],
        ["save", path],
        ["delete", "A", "B"],
        ["load", path],
    ]
    for command in commands:
        args = parser.parse_args(["data-manager", "broker", *command])
        assert args.handler(args) == 0
    assert len(brokers.list()["data"]) == 2
    assert all(not row["enabled"] for row in brokers.list()["data"])
    assert "Page 1 of 2" in capsys.readouterr().out


def test_http_large_stock_replacement_and_edit_guards(broker_http):
    base = "/api/v1/data/brokers"
    identifier = broker_http.post(
        base, json={"name": "Large", "stockpicker_use": True}
    ).json()["data"]["id"]
    assert (
        broker_http.put(
            f"{base}/{identifier}/stocks",
            json={"stocks": [f"T{i}" for i in range(1001)]},
        ).status_code
        == 200
    )
    response = broker_http.post(
        base + "/edit",
        json={"ids": [identifier], "updates": {"stockpicker_use": False}},
    )
    assert response.status_code == 409
    assert (
        broker_http.put(f"{base}/{identifier}/stocks", json={"stocks": []}).status_code
        == 200
    )
    assert broker_http.get(base).json()["data"][0]["stocks"] == []
    assert (
        broker_http.post(base + "/delete", json={"ids": [identifier]}).status_code
        == 200
    )


def test_http_brokers_require_session(broker_http):
    from unittest.mock import Mock

    broker_http.app.state.sessions = Mock(validate_session=Mock(return_value=None))
    broker_http.app.dependency_overrides.clear()
    assert broker_http.get("/api/v1/data/brokers").status_code == 401
    assert (
        broker_http.post(
            "/api/v1/data/brokers", json={"name": "Unauthorized"}
        ).status_code
        == 401
    )
