"""Session calendar mutations and JSON round trips against isolated SQLite."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from app.host.persistence import HostPersistence
from app.workspace.data_manager.sessions import (
    Sessions,
    SessionWindow,
    TradingHoliday,
)


@pytest.fixture
def sessions(tmp_path):
    database = tmp_path / "sessions.db"
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("""
            CREATE TABLE datamgr_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT DEFAULT '',
                timezone TEXT NOT NULL DEFAULT 'UTC',
                windows_json TEXT NOT NULL DEFAULT '[]',
                holidays_json TEXT NOT NULL DEFAULT '[]',
                is_default INTEGER NOT NULL DEFAULT 0,
                broker_id INTEGER NOT NULL DEFAULT -1
            )
        """)
        connection.commit()
    return Sessions(HostPersistence(database))


def test_crud_and_clone_preserve_schedule(sessions):
    created = sessions.add(
        "London",
        description="London hours",
        timezone="Europe/London",
        windows=[
            SessionWindow(
                day_from="Mon", day_to="Fri", start_time="08:00", end_time="17:00"
            )
        ],
        holidays=[TradingHoliday("2026-12-25", "Christmas")],
        broker_id=9,
    )
    assert created["success"]
    first = created["data"]
    assert first["windows"][0]["start_time"] == "08:00"
    assert first["holidays"][0]["date_str"] == "2026-12-25"
    cloned = sessions.clone("London", "London copy")
    assert cloned["success"]
    assert cloned["data"]["id"] != first["id"]
    assert cloned["data"]["windows"] == first["windows"]
    assert cloned["data"]["broker_id"] == 9
    edited = sessions.edit("London copy", {"name": "Renamed"}, description="New")
    assert edited["success"]
    assert edited["data"][0]["windows"] == first["windows"]
    assert edited["data"][0]["description"] == "New"
    assert sessions.delete(["London", "Renamed"])["success"]
    assert sessions.list()["data"] == []


def test_bulk_edit_and_clear_calendars(sessions):
    for name in ("A", "B"):
        assert sessions.add(name, windows=[{}], holidays=[{"date_str": "2026-01-01"}])[
            "success"
        ]
    edited = sessions.edit(
        ["A", "B", "A"], timezone="Europe/London", windows=[], holidays=[]
    )
    assert edited["success"]
    assert len(edited["data"]) == 2
    assert all(s["windows"] == [] and s["holidays"] == [] for s in edited["data"])


@pytest.mark.parametrize("operation", ["edit", "delete"])
def test_bulk_missing_rolls_back(sessions, operation):
    assert sessions.add("A")["success"]
    result = (
        sessions.edit(["A", "missing"], description="changed")
        if operation == "edit"
        else sessions.delete(["A", "missing"])
    )
    assert not result["success"]
    assert result["error"]["code"] == "not_found"
    assert sessions.list()["data"][0]["description"] == ""


def test_conflicts(sessions):
    assert sessions.add("A")["success"]
    assert sessions.add("B")["success"]
    for result in (
        sessions.add("A"),
        sessions.clone("A", "B"),
        sessions.edit("A", name="B"),
    ):
        assert not result["success"]
        assert result["error"]["code"] == "conflict"
    assert len(sessions.list()["data"]) == 2


@pytest.mark.parametrize(
    "fields",
    [
        {"name": " "},
        {"timezone": "No/SuchTimezone"},
        {"unknown": True},
        {"windows": "[]"},
        {"windows": [None]},
        {"windows": [{"start_time": "24:00"}]},
        {"windows": [{"day_from": "Bad"}]},
        {"windows": [{"day_of_week": 8}]},
        {"windows": [{"eod": "false"}]},
        {"holidays": [{"date_str": "2026-02-30"}]},
        {"holidays": [{"date_str": "20260101"}]},
        {"broker_id": True},
        {"is_default": "false"},
    ],
)
def test_validation(sessions, fields):
    result = sessions.add(**{"name": "A", **fields})
    assert not result["success"]
    assert result["error"]["code"] == "validation"
    assert sessions.list()["data"] == []


def test_invalid_targets_and_empty_edit(sessions):
    for result in (
        sessions.delete([]),
        sessions.delete(" "),
        sessions.edit("A"),
        sessions.edit(["A", "B"], name="C"),
    ):
        assert not result["success"]
        assert result["error"]["code"] == "validation"
    assert sessions.clone("missing", "new")["error"]["code"] == "not_found"


def test_json_round_trip(sessions, tmp_path):
    assert sessions.add(
        "Tokyo 日本", windows=[{}], holidays=[{"date_str": "2026-01-01"}]
    )["success"]
    path = tmp_path / "sessions.json"
    saved = sessions.save(path)
    assert saved["success"] and saved["data"]["count"] == 1
    original = json.loads(path.read_text(encoding="utf-8"))
    assert "id" not in original[0]
    assert original[0]["windows"][0]["day_from"] == "Mon"
    assert sessions.delete("Tokyo 日本")["success"]
    assert sessions.load(path)["success"]
    assert sessions.save(path)["success"]
    assert json.loads(path.read_text(encoding="utf-8")) == original


@pytest.mark.parametrize(
    "content",
    [
        "{bad",
        "{}",
        "[null]",
        '[{"name":"ok"},{"name":"bad","windows":[{"start_time":"99:00"}]}]',
    ],
)
def test_invalid_import_does_not_change_catalog(sessions, tmp_path, content):
    path = tmp_path / "bad.json"
    path.write_text(content, encoding="utf-8")
    result = sessions.load(path)
    assert not result["success"]
    assert result["error"]["code"] == "validation"
    assert sessions.list()["data"] == []


def test_import_conflict_rolls_back_prior_batch(sessions, tmp_path):
    data = [{"name": f"Session {i}"} for i in range(1001)]
    data.append({"name": "Session 0"})
    path = tmp_path / "many.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert sessions.load(path)["error"]["code"] == "conflict"
    assert sessions.list()["data"] == []
    path.write_text(json.dumps(data[:-1]), encoding="utf-8")
    assert sessions.load(path)["success"]
    assert len(sessions.list()["data"]) == 1001
    assert sessions.save(path)["data"]["count"] == 1001
    assert len(json.loads(path.read_text(encoding="utf-8"))) == 1001


def test_save_failure_preserves_existing_file(sessions, tmp_path):
    path = tmp_path / "sessions.json"
    path.write_text("original", encoding="utf-8")
    with patch.object(Path, "replace", side_effect=OSError("Disk failure")):
        assert not sessions.save(path)["success"]
    assert path.read_text(encoding="utf-8") == "original"
    assert not list(tmp_path.glob("*.tmp"))


@pytest.fixture
def session_http(sessions):
    from app.host.transport import register_transport_exception_handlers
    from app.workspace.data_manager import http
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    application = FastAPI()
    application.state.persistence = sessions.gateway
    application.include_router(http.create_router())
    application.dependency_overrides[http._access] = lambda: None
    register_transport_exception_handlers(application)
    with TestClient(application) as client:
        yield client


def test_http_session_lifecycle(session_http):
    client = session_http
    payload = {
        "name": "API",
        "timezone": "UTC",
        "windows": [
            {
                "day_from": "Sun",
                "day_to": "Mon",
                "start_time": "23:50:15",
                "end_time": "00:10:45",
                "eod": False,
                "session_type": "Extended",
                "day_of_week": 6,
            }
        ],
        "holidays": [{"date_str": "2028-02-29", "description": "Holiday"}],
    }
    response = client.post("/api/v1/data/sessions", json=payload)
    assert response.status_code == 200
    record = response.json()["data"]
    identifier = record["id"]
    assert isinstance(identifier, str)
    assert client.get("/api/v1/data/sessions").json()["data"][0] == record
    edited = client.post(
        "/api/v1/data/sessions",
        json={
            **payload,
            "id": identifier,
            "description": "Changed",
            "name": "Renamed",
        },
    )
    assert edited.status_code == 200
    assert edited.json()["data"]["id"] == identifier
    clone = client.post(
        "/api/v1/data/sessions/clone",
        json={
            "session_id": identifier,
            "new_name": "Copy",
            "timezone_offset": 30,
        },
    )
    assert clone.status_code == 200
    copied = clone.json()["data"]
    assert copied["windows"][0]["start_time"] == "00:20:15"
    assert copied["windows"][0]["day_from"] == "Mon"
    assert copied["windows"][0]["day_of_week"] == 0
    assert copied["holidays"] == payload["holidays"]
    result = client.post(
        f"/api/v1/data/sessions/{identifier}/elements",
        json={
            "action": "update",
            "index": 0,
            "window": {
                **payload["windows"][0],
                "start_time": "23:45:15",
            },
        },
    )
    assert result.status_code == 200
    assert result.json()["data"]["windows"][0]["start_time"] == "23:45:15"
    export = client.post("/api/v1/data/sessions/save", json={})
    assert export.status_code == 200
    content = export.json()["data"]["content"]
    assert len(json.loads(content)) == 2
    assert (
        client.post(
            "/api/v1/data/sessions/delete",
            json={
                "session_ids": [identifier, copied["id"]],
            },
        ).status_code
        == 200
    )
    assert (
        client.post("/api/v1/data/sessions/load", json={"content": content}).json()[
            "data"
        ]["loaded_count"]
        == 2
    )
    new_id = client.get("/api/v1/data/sessions").json()["data"][0]["id"]
    assert client.delete(f"/api/v1/data/sessions/{new_id}").json()["data"]["deleted"]


def test_http_validation_and_atomic_delete(session_http):
    client = session_http
    record = client.post("/api/v1/data/sessions", json={"name": "Saved"}).json()["data"]
    assert (
        client.post("/api/v1/data/sessions", json={"name": "Saved"}).status_code == 409
    )
    assert (
        client.post(
            "/api/v1/data/sessions", json={"name": "Bad", "timezone": "No/Such"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/data/sessions/delete", json={"session_ids": [record["id"], "999"]}
        ).status_code
        == 404
    )
    assert len(client.get("/api/v1/data/sessions").json()["data"]) == 1
    assert (
        client.post(
            "/api/v1/data/sessions/load", json={"content": "not JSON"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/data/sessions/load", json={"content": '[{"name":"Saved"}]'}
        ).status_code
        == 409
    )
    assert (
        client.post(
            f"/api/v1/data/sessions/{record['id']}/elements",
            json={"action": "remove", "index": 99},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/data/sessions/clone",
            json={
                "session_id": record["id"],
                "new_name": "Bad",
                "timezone_offset": 0.5,
            },
        ).status_code
        == 422
    )


def test_http_sessions_require_authentication(sessions):
    from app.host.transport import register_transport_exception_handlers
    from app.workspace.data_manager.http import create_router
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    application = FastAPI()
    application.state.persistence = sessions.gateway
    application.state.sessions = Mock(validate_session=Mock(return_value=None))
    application.include_router(create_router())
    register_transport_exception_handlers(application)
    with TestClient(application) as client:
        assert client.get("/api/v1/data/sessions").status_code in {401, 403}
        assert client.post(
            "/api/v1/data/sessions", json={"name": "Forbidden"}
        ).status_code in {401, 403}
    assert sessions.list()["data"] == []


def test_session_cli_lifecycle(sessions, monkeypatch, capsys, tmp_path):
    import argparse

    from app.workspace.data_manager import cli
    from app.workspace.data_manager import sessions as module

    monkeypatch.setattr(module, "persistence", sessions.gateway)
    parser = argparse.ArgumentParser()
    cli.register_commands(parser.add_subparsers(dest="command", required=True))

    def run(*args):
        arguments = parser.parse_args(["data-manager", "session", *args])
        return arguments.handler(arguments)

    assert (
        run(
            "add",
            "--name",
            "CLI",
            "--windows",
            '[{"start_time":"08:00","end_time":"17:00"}]',
        )
        == 0
    )
    assert run("clone", "CLI", "Copy") == 0
    assert run("edit", "CLI", "Copy", "--description", "Changed", "--is-default") == 0
    assert run("list", "--page-size", "1", "--page", "2") == 0
    assert "Page 2 of 2" in capsys.readouterr().out
    path = str(tmp_path / "cli.json")
    assert run("save", path) == 0
    assert run("delete", "CLI", "Copy") == 0
    assert run("load", path) == 0
    assert len(sessions.list()["data"]) == 2
    assert run("delete", "missing") == 1
    assert '"not_found"' in capsys.readouterr().out
    with pytest.raises(SystemExit):
        run("add", "--name", "Bad", "--windows", "{}")
    with pytest.raises(SystemExit):
        run("list", "--page", "3", "--page-size", "1")


def test_legacy_numeric_weekdays_are_read_without_mutation(sessions):
    raw = json.dumps(
        [{"day_of_week": 2, "open_time": "09:30:15", "close_time": "16:00:45"}]
    )
    assert sessions.gateway.create_records(
        "datamgr_sessions",
        {
            "name": "Legacy",
            "windows_json": raw,
        },
    )["success"]
    window = sessions.list()["data"][0]["windows"][0]
    assert window["day_from"] == window["day_to"] == "Wed"
    assert window["start_time"] == "09:30:15"
    assert window["end_time"] == "16:00:45"
    assert (
        sessions.gateway.read_records("datamgr_sessions")["data"]["records"][0][
            "windows_json"
        ]
        == raw
    )
