"""Public session operations against isolated relational persistence."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest
from app.host.persistence import HostPersistence
from app.workspace.data_manager.routes import create_data_manager_router
from app.workspace.data_manager.sessions import Sessions
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(HostPersistence, "DEFAULT_DB_PATH", tmp_path / "sessions.db")


def window(
    start: str = "09:30:15",
    end: str = "12:00:45",
    day: str = "Mon",
    end_day: str | None = None,
) -> dict[str, Any]:
    return {
        "day_from": day,
        "day_to": end_day or day,
        "start_time": start,
        "end_time": end,
        "eod": True,
        "session_type": "Regular",
    }


def profile(name: str = "Saved schedule") -> dict[str, Any]:
    return {
        "name": name,
        "description": "Local hours and lunch pause",
        "timezone": "America/New_York",
        "broker_id": 0,
        "is_default": True,
        "windows": [window(), window("13:00:00", "16:00:00")],
        "holidays": [{"date_str": "2028-02-29", "description": "Configured closure"}],
    }


def client(*, require_auth: bool = False) -> TestClient:
    app = FastAPI()
    app.include_router(create_data_manager_router(require_auth=require_auth))
    return TestClient(app)


def test_template_and_holiday_fields_survive_reopen_and_partial_edit() -> None:
    row = Sessions().session_template(profile())
    assert isinstance(row["id"], str)
    assert Sessions().sessions() == [row]
    saved = Sessions().session_template({"id": row["id"], "description": "Changed"})
    assert saved == {**row, "description": "Changed"}
    raw = HostPersistence.read_records("datamgr_sessions")[0]
    assert json.loads(raw["windows_json"]) == row["windows"]
    assert json.loads(raw["holidays_json"]) == row["holidays"]
    assert saved["broker_id"] == 0


def test_list_all_rows_filters_and_empty() -> None:
    service = Sessions()
    assert service.sessions() == []
    HostPersistence.apply_batch(
        [
            {
                "op": "create",
                "table": "datamgr_sessions",
                "values": {"name": f"Session {index:03}", "timezone": "UTC"},
            }
            for index in range(103)
        ]
    )
    assert len(service.sessions()) == 103
    assert len(service.sessions({"search": "session 102"})) == 1
    assert len(service.sessions({"timezone": "UTC", "broker_id": "-1"})) == 103
    assert service.sessions({"timezone": "Asia/Kolkata"}) == []
    with pytest.raises(ValueError):
        service.sessions({"unexpected": 1})


@pytest.mark.parametrize(
    ("minutes", "start_day", "start_time", "end_day", "end_time"),
    [
        (30, "Mon", "00:20:15", "Mon", "00:40:45"),
        (-30, "Sun", "23:20:15", "Sun", "23:40:45"),
        (1440, "Mon", "23:50:15", "Tue", "00:10:45"),
    ],
)
def test_clone_week_wrap_preserves_duration_seconds_and_calendars(
    minutes: int, start_day: str, start_time: str, end_day: str, end_time: str
) -> None:
    service = Sessions()
    source = service.session_template(
        {**profile(), "windows": [window("23:50:15", "00:10:45", "Sun", "Mon")]}
    )
    clone = service.clone_session(source["id"], "Shifted", timezone_offset=minutes)
    assert clone["id"] != source["id"]
    assert clone["is_default"] is False
    assert clone["windows"] == [
        {
            **source["windows"][0],
            "day_from": start_day,
            "day_to": end_day,
            "start_time": start_time,
            "end_time": end_time,
        }
    ]
    assert clone["timezone"] == source["timezone"]
    assert clone["holidays"] == source["holidays"]
    assert service.sessions({"search": source["name"]}) == [source]


def test_element_add_update_remove_and_adjacency() -> None:
    service = Sessions()
    row = service.clone_session("", "Unconfigured")
    assert row["windows"] == [] and row["holidays"] == []
    added = service.session_element(
        row["id"], {"action": "add", "window": window("09:00", "12:00")}
    )
    assert len(added["windows"]) == 1
    adjacent = service.session_element(
        row["id"], {"action": "add", "window": window("12:00", "16:00")}
    )
    assert len(adjacent["windows"]) == 2
    paused = service.session_element(
        row["id"], {"action": "update", "index": 1, "window": window("13:00", "16:00")}
    )
    assert paused["windows"][1]["start_time"] == "13:00"
    removed = service.session_element(row["id"], {"action": "remove", "index": 0})
    assert removed["windows"] == paused["windows"][1:]
    service.session_element(row["id"], {"action": "remove", "index": 0})
    assert service.sessions()[0]["windows"] == []


@pytest.mark.parametrize(
    "patch",
    [
        {"timezone": "Unknown/Zone"},
        {"broker_id": True},
        {"broker_id": 999},
        {"is_default": 1},
        {"holidays": [{"date_str": "2027-02-29"}]},
        {"holidays": [{"date_str": "2028-02-29"}, {"date_str": "2028-02-29"}]},
        {"windows": [window("09:00", "09:00")]},
        {"windows": [window("12:00", "09:00")]},
        {"windows": [window("09:00", "13:00"), window("12:00", "15:00")]},
        {"windows": [window("23:00", "01:00", "Sun", "Mon"), window("00:30", "02:00")]},
        {"windows": [window("24:00", "25:00")]},
        {"windows": [window(day="Bad")]},
        {"name": ""},
        {"unknown": "field"},
        {"windows": [] * 101 + [window()] * 101},
    ],
)
def test_invalid_templates_leave_persistence_unchanged(patch: dict[str, Any]) -> None:
    service = Sessions()
    source = service.session_template(profile())
    with pytest.raises(ValueError):
        service.session_template({"id": source["id"], **patch})
    assert service.sessions() == [source]


def test_duplicate_missing_ids_and_invalid_element_commands() -> None:
    service = Sessions()
    source = service.session_template(profile())
    with pytest.raises(FileExistsError):
        service.clone_session(source["id"], source["name"].lower())
    with pytest.raises(LookupError):
        service.session_template({"id": "999", "name": "Must not insert"})
    for command in (
        {"action": "remove", "index": -1},
        {"action": "update", "index": True, "window": window()},
        {"action": "remove", "index": 99},
        {"action": "add", "window": window()},
        {"action": "remove"},
    ):
        with pytest.raises(ValueError):
            service.session_element(source["id"], command)
    invalid_offsets: tuple[Any, ...] = (True, 1441, 0.5)
    for offset in invalid_offsets:
        with pytest.raises(ValueError):
            service.clone_session(source["id"], "Invalid shift", timezone_offset=offset)
    assert service.sessions() == [source]


def test_delete_only_requested_profile_and_explicit_missing_failure() -> None:
    service = Sessions()
    source = service.session_template(profile())
    other = service.clone_session(source["id"], "Other")
    result = service.clone_session(other["id"], "", delete=True)
    assert result == {"id": other["id"], "name": "Other", "deleted": True}
    assert service.sessions() == [source]
    with pytest.raises(LookupError):
        service.clone_session(other["id"], "", delete=True)


def test_real_write_failure_rolls_back_and_corrupt_calendar_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = Sessions()
    row = service.session_template(profile())
    original = HostPersistence.apply_batch

    def fail(operations: Any) -> Any:
        guard = {
            "op": "create",
            "table": "datamgr_sessions",
            "values": {"name": "ROLLBACK_GUARD"},
        }
        return original([*operations, guard, guard])

    with monkeypatch.context() as temporary:
        temporary.setattr(HostPersistence, "apply_batch", fail)
        with pytest.raises(RuntimeError):
            service.session_template({"id": row["id"], "description": "Must roll back"})
        with pytest.raises(RuntimeError):
            service.clone_session(row["id"], "", delete=True)
    assert service.sessions() == [row]
    HostPersistence.update_record(
        "datamgr_sessions", {"id": int(row["id"])}, {"windows_json": "{"}
    )
    with client() as http:
        result = http.get("/data/sessions")
        assert result.status_code == 503
        assert "windows_json" not in result.text


def test_http_contracts_auth_and_structured_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO), client() as http:
        row = http.post("/data/sessions", json=profile())
        assert row.status_code == 201
        identifier = row.json()["data"]["id"]
        assert http.get("/data/sessions").json()["data"] == [row.json()["data"]]
        assert http.post("/data/sessions", json=profile()).status_code == 409
        assert (
            http.post(
                "/data/sessions", json={"id": identifier, "description": "Changed"}
            ).status_code
            == 200
        )
        assert (
            http.post(
                f"/data/sessions/{identifier}/elements",
                json={"action": "remove", "index": 0},
            ).status_code
            == 200
        )
        assert (
            http.post(
                "/data/sessions/clone",
                json={
                    "session_id": identifier,
                    "new_name": "Copy",
                    "timezone_offset": -30,
                },
            ).status_code
            == 201
        )
        assert (
            http.delete(f"/data/sessions/{identifier}").json()["data"]["deleted"]
            is True
        )
        assert http.delete(f"/data/sessions/{identifier}").status_code == 404
        assert (
            http.post(
                "/data/sessions/clone", json={"session_id": identifier}
            ).status_code
            == 422
        )
        assert http.get("/data/sessions?unknown=yes").status_code == 422
    ids = {getattr(record, "fr_id", None) for record in caplog.records}
    assert {
        "FR-DATAMGR-SESS-LIST",
        "FR-DATAMGR-SESS-CLONE",
        "FR-DATAMGR-SESS-ELEMENT",
        "FR-DATAMGR-SESS-TEMPLATE",
    } <= ids
    with client(require_auth=True) as http:
        assert http.get("/data/sessions").status_code == 401
        assert http.post("/data/sessions", json=profile()).status_code == 401
        assert http.delete("/data/sessions/1").status_code == 401


@pytest.mark.parametrize("aliases", [True, False])
def test_legacy_catalog_reads_all_profiles_without_writes(aliases: bool) -> None:
    service = Sessions()
    canonical = service.session_template(profile("Canonical"))
    for dow in range(7):
        times = (
            {"open_time": "09:30:15", "close_time": "16:00:45"}
            if aliases
            else {"start_time": "09:30:15", "end_time": "16:00:45"}
        )
        HostPersistence.apply_batch(
            [
                {
                    "op": "create",
                    "table": "datamgr_sessions",
                    "values": {
                        "name": f"Legacy {dow}",
                        "timezone": "America/New_York",
                        "windows_json": json.dumps([{"day_of_week": dow, **times}]),
                        "holidays_json": json.dumps(canonical["holidays"]),
                    },
                }
            ]
        )
    before = HostPersistence.read_records("datamgr_sessions", limit=0)
    listed = service.sessions()
    assert {row["id"] for row in listed} == {str(row["id"]) for row in before}
    assert HostPersistence.read_records("datamgr_sessions", limit=0) == before
    assert next(row for row in listed if row["name"] == "Canonical") == canonical
    for dow, day in enumerate(("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
        row = next(row for row in listed if row["name"] == f"Legacy {dow}")
        assert row["timezone"] == "America/New_York"
        assert row["holidays"] == canonical["holidays"]
        assert row["windows"] == [
            {
                "day_of_week": dow,
                "day_from": day,
                "day_to": day,
                "start_time": "09:30:15",
                "end_time": "16:00:45",
                "eod": False,
                "session_type": "Regular",
            }
        ]
        assert any(
            "EOD was not stored" in note for note in row["normalization_warnings"]
        )
        assert len(row["normalization_warnings"]) == (3 if aliases else 2)


@pytest.mark.parametrize(
    "bad_window",
    [
        {"day_of_week": -1, "start_time": "09:00", "end_time": "16:00"},
        {"day_of_week": 7, "start_time": "09:00", "end_time": "16:00"},
        {"day_of_week": True, "start_time": "09:00", "end_time": "16:00"},
        {"day_of_week": "1", "start_time": "09:00", "end_time": "16:00"},
        {
            "day_of_week": 1,
            "open_time": "09:00",
            "start_time": "10:00",
            "close_time": "16:00",
        },
        {"day_of_week": 1, "start_time": "16:00", "end_time": "09:00"},
        {
            "day_from": "Mon",
            "day_of_week": 0,
            "start_time": "09:00",
            "end_time": "16:00",
        },
        {"day_of_week": 1, "start_time": "09:00", "end_time": "16:00", "extra": 1},
    ],
)
def test_invalid_legacy_calendar_fails_without_repair(
    bad_window: dict[str, Any],
) -> None:
    HostPersistence.apply_batch(
        [
            {
                "op": "create",
                "table": "datamgr_sessions",
                "values": {
                    "name": "Invalid",
                    "timezone": "UTC",
                    "windows_json": json.dumps([bad_window]),
                },
            }
        ]
    )
    before = HostPersistence.read_records("datamgr_sessions", limit=0)
    with pytest.raises(RuntimeError, match="Stored session calendar is invalid"):
        Sessions().sessions()
    assert HostPersistence.read_records("datamgr_sessions", limit=0) == before


def test_read_defaults_do_not_relax_canonical_write_validation() -> None:
    legacy = {"day_of_week": 0, "open_time": "09:00", "close_time": "16:00"}
    with pytest.raises(ValueError):
        Sessions().session_template({**profile(), "windows": [legacy]})
    missing_eod = window()
    del missing_eod["eod"]
    with pytest.raises(ValueError):
        Sessions().session_template({**profile(), "windows": [missing_eod]})
    row = Sessions().session_template(profile())
    with pytest.raises(ValueError):
        Sessions().session_element(row["id"], {"action": "add", "window": legacy})
    with pytest.raises(ValueError):
        Sessions().session_template({"id": row["id"], "normalization_warnings": []})


def test_legacy_alias_agreement_and_explicit_eod_are_preserved() -> None:
    value = {**window(), "open_time": "09:30:15", "close_time": "12:00:45"}
    HostPersistence.apply_batch(
        [
            {
                "op": "create",
                "table": "datamgr_sessions",
                "values": {
                    "name": "Compatible",
                    "timezone": "UTC",
                    "windows_json": json.dumps([value]),
                },
            }
        ]
    )
    row = Sessions().sessions()[0]
    assert row["windows"] == [window()]
    assert row["normalization_warnings"] == [
        "Legacy open/close time fields were read as start/end times."
    ]
    saved = Sessions().session_template(
        {"id": row["id"], "description": "Explicit save"}
    )
    assert "normalization_warnings" not in saved
    assert json.loads(
        HostPersistence.read_records("datamgr_sessions")[0]["windows_json"]
    ) == [window()]
