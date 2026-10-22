"""Verify public broker workflows against isolated host persistence."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from app.host.persistence import HostPersistence
from app.workspace.data_manager.broker import Broker
from app.workspace.data_manager.instruments import Instruments
from app.workspace.data_manager.routes import AppDataManager, create_data_manager_router
from app.workspace.data_manager.sessions import Sessions
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(HostPersistence, "DEFAULT_DB_PATH", tmp_path / "broker.db")


def profile(**updates: Any) -> dict[str, Any]:
    return {"name": "Demo", "postfix": "_d", **updates}


def instrument(name: str = "TEST") -> dict[str, Any]:
    return {
        "symbol": name,
        "description": "Recorded",
        "default_spread": 0.2,
        "tick_size": 0.01,
        "point_value": 100,
        "commissions": "3.5",
    }


def schedule(name: str = "Week") -> dict[str, Any]:
    return {
        "name": name,
        "timezone": "UTC",
        "windows": [
            {
                "day_from": "Mon",
                "day_to": "Tue",
                "start_time": "00:00",
                "end_time": "00:00",
                "eod": True,
                "session_type": "Regular",
            }
        ],
        "holidays": [{"date_str": "2026-12-25", "description": "Holiday"}],
    }


def document(kind: str, records: list[dict[str, Any]], **options: Any) -> str:
    return json.dumps({"version": 1, "kind": kind, kind: records, "options": options})


def commission() -> dict[str, Any]:
    return {
        "model": "Per trade",
        "value": 3.5,
        "unit": "share",
        "min": 0,
        "minUnit": "money",
        "max": 0,
        "maxUnit": "money",
    }


def test_profiles_costs_rename_and_clocks_are_preserved() -> None:
    service = Broker()
    assert service.brokers() == []
    first = service.add_broker(
        profile(
            spread_model={"model": "fixed", "value": 0}, commission_model=commission()
        )
    )
    identifier = first["id"]
    HostPersistence.update_record(
        "datamgr_broker",
        {"id": int(identifier)},
        {"clock_policy_json": '{"keep":1}', "clock_policy_revision": 7},
    )
    service.add_broker({"id": identifier, "name": "Renamed"})
    saved = Broker().brokers()[0]
    assert saved["id"] == identifier
    assert saved["spread_model"] == {"model": "fixed", "value": 0}
    assert saved["commission_model"] == commission()
    rows = HostPersistence.read_records("datamgr_broker")
    assert rows[0]["clock_policy_revision"] == 7
    assert rows[0]["clock_policy_json"] == '{"keep":1}'
    extensions = HostPersistence.read_records("host_entities")
    assert [r["entity_id"] for r in extensions] == ["renamed"]
    assert extensions[0]["revision"] == 2
    with pytest.raises(FileExistsError):
        service.add_broker(profile(name="renamed"))


@pytest.mark.parametrize(
    "changes",
    [
        {"name": ""},
        {"name": "x" * 51},
        {"description": "x" * 251},
        {"timezone": "Bad/Zone"},
        {"mt_use": 1},
        {"stockpicker_use": "yes"},
        {"is_system": True},
        {"postfix": "\x00"},
        {"id": "0"},
        {"spread_model": {"model": "fixed", "value": -1}},
        {"spread_model": {"model": "fixed", "value": float("nan")}},
        {"commission_model": {"model": "unknown", "value": 0}},
        {"commission_model": {**commission(), "model": "None"}},
        {"commission_model": {**commission(), "unit": "invalid"}},
        {"commission_model": {**commission(), "min": 5, "max": 3}},
    ],
)
def test_reject_invalid_profile(changes: dict[str, Any]) -> None:
    with pytest.raises((ValueError, TypeError)):
        Broker().add_broker(profile(**changes))
    assert Broker().brokers() == []


def test_stock_replacement_empty_and_usage_guards() -> None:
    service = Broker()
    row = service.add_broker(profile())
    result = service.edit_stocks(row["id"], [" AAPL ", "aapl", "BRK.B"])
    assert result["stocks"] == ["AAPL", "BRK.B"]
    assert Broker().brokers()[0]["customized_stocks"] == 2
    with pytest.raises(ValueError):
        service.add_broker({"id": row["id"], "stockpicker_use": False})
    for symbols in (["BAD SYMBOL"], [""], ["x"] * 10001):
        with pytest.raises(ValueError):
            service.edit_stocks(row["id"], symbols)
    assert service.edit_stocks(row["id"], [])["count"] == 0
    service.add_broker({"id": row["id"], "stockpicker_use": False})
    with pytest.raises(ValueError):
        service.edit_stocks(row["id"], ["AAPL"])


def test_profile_and_stocks_batch_roll_back() -> None:
    service = Broker()
    real_batch = HostPersistence.apply_batch

    def fail(operations: Any) -> Any:
        return real_batch(
            [*operations, {"op": "create", "table": "not_approved", "values": {"x": 1}}]
        )

    with patch.object(HostPersistence, "apply_batch", side_effect=fail):
        with pytest.raises(RuntimeError):
            service.add_broker(profile())
    assert service.brokers() == []
    assert HostPersistence.read_records("host_entities") == []
    row = service.add_broker(profile())
    service.edit_stocks(row["id"], ["OLD"])
    with patch.object(HostPersistence, "apply_batch", side_effect=fail):
        with pytest.raises(RuntimeError):
            service.edit_stocks(row["id"], ["NEW"])
    assert service.brokers()[0]["stocks"] == ["OLD"]


def test_selected_instrument_import_and_explicit_defaults() -> None:
    service = Broker()
    row = service.add_broker(
        profile(
            spread_model={"model": "fixed", "value": 0}, commission_model=commission()
        )
    )
    result = service.import_instruments(
        row["id"],
        document(
            "instruments",
            [instrument("ONE"), instrument("TWO")],
            selected_names=["ONE"],
            use_profile_costs=True,
        ),
    )
    assert result["created_count"] == 1
    saved = Instruments().instruments()[0]
    assert saved["symbol"] == "ONE_d"
    assert saved["default_spread"] == 0
    assert json.loads(saved["commissions"])["settings"] == commission()
    assert saved["point_value"] == 100
    assert service.brokers()[0]["total_instruments"] == 1
    with pytest.raises(ValueError):
        service.add_broker({"id": row["id"], "mt_use": False})
    service.add_broker(
        {"id": row["id"], "spread_model": {"model": "fixed", "value": 8}}
    )
    assert Instruments().instruments()[0]["default_spread"] == 0


def test_conflict_overwrite_retains_identity_and_cross_broker_guard() -> None:
    service = Broker()
    row = service.add_broker(profile())
    first = service.import_instruments(row["id"], [instrument()])["records"][0]
    before = HostPersistence.read_records("datamgr_instruments")[0]
    with pytest.raises(FileExistsError):
        service.import_instruments(row["id"], [instrument()])
    changed = service.import_instruments(
        row["id"],
        document(
            "instruments",
            [{"symbol": "TEST", "default_spread": 5}],
            conflict_policy="overwrite",
        ),
    )
    assert changed["updated_count"] == 1
    assert changed["records"][0]["id"] == first["id"]
    assert changed["records"][0]["point_value"] == 100
    assert (
        HostPersistence.read_records("datamgr_instruments")[0]["created_at_utc"]
        == before["created_at_utc"]
    )
    other = service.add_broker(profile(name="Other", postfix="_d"))
    with pytest.raises(FileExistsError):
        service.import_instruments(
            other["id"],
            document("instruments", [instrument()], conflict_policy="overwrite"),
        )


def test_session_import_calendar_metadata_and_overwrite() -> None:
    service = Broker()
    row = service.add_broker(profile(timezone="Europe/London"))
    first = service.import_sessions(row["id"], [schedule()])["records"][0]
    assert first["name"] == "Week_d"
    assert first["holidays"] == schedule()["holidays"]
    assert first["windows"][0]["session_type"] == "Regular"
    updated = service.import_sessions(
        row["id"], document("sessions", [schedule()], conflict_policy="overwrite")
    )
    assert updated["updated_count"] == 1
    assert updated["records"][0]["id"] == first["id"]
    assert service.brokers()[0]["total_sessions"] == 1


def test_file_record_mapping_default_broker_and_postfix_once() -> None:
    service = Broker()
    session = {
        "name": "Week",
        "broker": "999",
        "brokerName": "Foreign",
        "elements": [
            {
                "dayFrom": "Mon",
                "dayTo": "Mon",
                "timeFrom": "09:00",
                "timeTo": "16:00",
                "eod": True,
                "sessionType": "Extended",
                "dayOfWeek": 0,
            }
        ],
    }
    result = service.import_sessions("0", document("sessions", [session], postfix="_x"))
    assert result["records"][0]["windows"][0]["day_of_week"] == 0
    assert result["records"][0]["broker_id"] == -1
    raw = {
        "symbol": "FILE",
        "name": "File",
        "tickSize": 0.01,
        "pointValue": 1,
        "commission": commission(),
        "swap": {"long": -1, "short": 2},
    }
    assert (
        service.import_instruments("-1", document("instruments", [raw]))["records"][0][
            "description"
        ]
        == "File"
    )


@pytest.mark.parametrize(
    "payload",
    [
        "not json",
        "{",
        '{"version":2,"kind":"instruments","instruments":[]}',
        '{"version":1,"kind":"instruments","instruments":[null]}',
        '{"version":1,"kind":"instruments","instruments":[{"symbol":"X"}],"options":{"selected_names":[]}}',
        '{"version":1,"kind":"instruments","instruments":[{"symbol":"X"}],"options":{"selected_names":["Y"]}}',
        '{"version":1,"kind":"instruments","instruments":[{"symbol":"X"}],"options":{"conflict_policy":"skip"}}',
        '{"version":1,"kind":"instruments","instruments":[{"symbol":"X"}],"options":{"use_profile_costs":1}}',
        '[{"symbol":"X"},{"symbol":"x"}]',
        "[]",
        pytest.param('"' + "x" * 2000001 + '"', id="oversize"),
    ],
)
def test_malformed_imports_write_nothing(payload: str) -> None:
    with pytest.raises(ValueError):
        Broker().import_instruments("-1", payload)
    assert Instruments().instruments() == []


@pytest.mark.parametrize(
    "invalid",
    [None, True, "10", float("nan"), pytest.param(10**400, id="overflow")],
)
def test_invalid_instrument_quantities_do_not_corrupt_catalog(invalid: Any) -> None:
    result = Broker().import_instruments(
        "-1", [{**instrument(), "point_value": invalid}]
    )
    assert result["imported_count"] == 0
    assert len(result["failed"]) == 1
    assert Instruments().instruments() == []


def test_partial_results_and_storage_failure_stop() -> None:
    service = Broker()
    partial = service.import_sessions(
        "-1", [schedule("GOOD"), {"name": "BAD", "timezone": "bad"}]
    )
    assert partial["imported_count"] == 1
    assert partial["failed"] == [{"name": "BAD", "reason": "Record validation failed."}]
    assert len(Sessions().sessions()) == 1
    real_add = Instruments.add_instrument

    def add(instance: Instruments, values: Any) -> Any:
        if values["symbol"] == "STOP":
            raise RuntimeError("private storage detail")
        return real_add(instance, values)

    with patch.object(Instruments, "add_instrument", autospec=True, side_effect=add):
        result = service.import_instruments(
            "-1", [instrument("GOOD"), instrument("STOP"), instrument("LATER")]
        )
    assert result["imported_count"] == 1
    assert result["unattempted"] == ["LATER"]
    assert "private" not in json.dumps(result)


def test_system_invalid_settings_and_missing_profiles() -> None:
    service = Broker()
    row = service.add_broker(profile())
    HostPersistence.update_record(
        "datamgr_broker", {"id": int(row["id"])}, {"is_system": 1}
    )
    for action in (
        lambda: service.add_broker({"id": row["id"]}),
        lambda: service.edit_stocks(row["id"], []),
        lambda: service.import_sessions(row["id"], [schedule()]),
    ):
        with pytest.raises(ValueError):
            action()
    with pytest.raises(LookupError):
        service.edit_stocks("999", [])
    HostPersistence.update_entity("datamgr_broker_settings", "demo", {"payload": "{}"})
    with pytest.raises(RuntimeError):
        service.brokers()


def test_routes_and_public_boundary_logging(caplog: pytest.LogCaptureFixture) -> None:
    app = FastAPI()
    app.include_router(create_data_manager_router(AppDataManager()))
    with TestClient(app) as client, caplog.at_level(logging.INFO):
        assert client.get("/data/brokers").json()["data"] == []
        assert (
            client.post("/data/brokers", json=profile(spread_model=None)).status_code
            == 422
        )
        row = client.post("/data/brokers", json=profile()).json()["data"]
        assert (
            client.get("/data/brokers/" + row["id"]).json()["data"]["id"] == row["id"]
        )
        assert client.get("/data/brokers/999").status_code == 404
        assert client.get("/data/brokers/bad").status_code == 422
        assert (
            client.put(
                "/data/brokers/" + row["id"] + "/stocks", json={"wrong": []}
            ).status_code
            == 422
        )
        assert (
            client.put(
                "/data/brokers/" + row["id"] + "/stocks", json={"stocks": ["AAPL"]}
            ).json()["data"]["count"]
            == 1
        )
        assert client.get("/data/brokers/" + row["id"] + "/stocks").json()["data"][
            "stocks"
        ] == ["AAPL"]
        for kind, records in [
            ("instruments", [instrument()]),
            ("sessions", [schedule()]),
        ]:
            reply = client.post(
                "/data/brokers/" + row["id"] + "/import-" + kind,
                json={"version": 1, "kind": kind, kind: records},
            )
            assert reply.status_code == 200
            assert reply.json()["data"]["imported_count"] == 1
        assert client.post("/data/brokers", json=profile()).status_code == 409
    ids = {getattr(record, "fr_id", "") for record in caplog.records}
    assert all(
        "FR-DATAMGR-BROKER-" + name in ids
        for name in ["LIST", "ADD", "STOCKS", "IMPORT-INSTR", "IMPORT-SESS"]
    )
    protected = FastAPI()
    protected.include_router(
        create_data_manager_router(AppDataManager(), require_auth=True)
    )
    assert TestClient(protected).get("/data/brokers").status_code == 401


def test_existing_system_clock_label_lists_without_rewriting_records() -> None:
    identifier = HostPersistence.create_record(
        "datamgr_broker",
        {
            "name": "[[Existing]]",
            "is_system": 1,
            "stockpicker_use": 1,
            "mt_use": 1,
            "server_timezone": "EETUS",
            "created_at_utc": "2026-01-01",
            "updated_at_utc": "2026-01-01",
            "clock_policy_json": '{"preserve":true}',
        },
    )["key"]
    HostPersistence.create_record(
        "datamgr_broker_stock", {"BROKER_ID": identifier, "TICKER": "AAPL"}
    )
    Instruments().add_instrument({**instrument(), "broker_id": identifier})
    Sessions().session_template({**schedule(), "broker_id": identifier})
    tables = [
        "datamgr_broker",
        "datamgr_broker_stock",
        "datamgr_instruments",
        "datamgr_sessions",
        "host_entities",
    ]
    before = {table: HostPersistence.read_records(table, limit=0) for table in tables}
    row = Broker().brokers()[0]
    assert row["timezone"] == "EETUS"
    assert row["is_system"] is True
    assert row["stocks"] == ["AAPL"]
    assert row["total_instruments"] == row["total_sessions"] == 1
    app = FastAPI()
    app.include_router(create_data_manager_router(AppDataManager()))
    response = TestClient(app).get("/data/brokers")
    assert response.status_code == 200
    assert response.json()["data"][0]["timezone"] == "EETUS"
    assert {
        table: HostPersistence.read_records(table, limit=0) for table in tables
    } == before


def test_custom_clock_label_round_trips_without_becoming_a_session_timezone() -> None:
    service = Broker()
    row = service.add_broker(profile(timezone="EETUS"))
    saved = service.add_broker({"id": row["id"], "description": "Keep the clock label"})
    assert saved["timezone"] == "EETUS"
    assert (
        HostPersistence.read_records("datamgr_broker")[0]["server_timezone"] == "EETUS"
    )
    missing_zone = schedule()
    missing_zone.pop("timezone")
    result = service.import_sessions(row["id"], [missing_zone])
    assert result["imported_count"] == 0
    assert len(result["failed"]) == 1
    assert Sessions().sessions() == []
    with pytest.raises(ValueError):
        service.add_broker(profile(name="Invalid", timezone="Unknown/BrokerClock"))


def test_single_profile_reads_only_owned_relations() -> None:
    service = Broker()
    target = service.add_broker(profile())
    other = service.add_broker(profile(name="Other"))
    service.edit_stocks(other["id"], ["OTHER"])
    with (
        patch.object(
            HostPersistence, "read_records", wraps=HostPersistence.read_records
        ) as reads,
        patch.object(
            Instruments,
            "instruments",
            side_effect=AssertionError("Full catalog decoded"),
        ),
        patch.object(
            Sessions, "sessions", side_effect=AssertionError("Full catalog decoded")
        ),
    ):
        updated = service.add_broker({"id": target["id"], "description": "Updated"})
    assert updated["id"] == target["id"]
    assert updated["stocks"] == []
    assert updated["description"] == "Updated"
    for call in reads.call_args_list:
        table = call.args[0]
        filters = call.args[1] if len(call.args) > 1 else call.kwargs.get("filters")
        if table in ("datamgr_instruments", "datamgr_sessions"):
            assert filters == {"broker_id": int(target["id"])}
        elif table == "datamgr_broker_stock":
            assert filters == {"BROKER_ID": int(target["id"])}
        elif table == "host_entities":
            assert filters == {
                "entity_type": "datamgr_broker_settings",
                "entity_id": "demo",
            }
    broker_filters = [
        call.args[1]
        for call in reads.call_args_list
        if call.args[0] == "datamgr_broker" and len(call.args) > 1
    ]
    assert {"id": int(target["id"])} in broker_filters
    assert {"name": "Demo"} in broker_filters


def test_listing_counts_raw_associations_without_domain_decoding() -> None:
    service = Broker()
    target = service.add_broker(profile())
    other = service.add_broker(profile(name="Other"))
    service.import_instruments(target["id"], [instrument()])
    service.import_sessions(other["id"], [schedule()])
    service.edit_stocks(target["id"], ["ABC", "DEF"])
    with (
        patch.object(
            HostPersistence, "read_records", wraps=HostPersistence.read_records
        ) as reads,
        patch.object(
            Instruments, "instruments", side_effect=ValueError("Invalid economics")
        ),
        patch.object(Sessions, "sessions", side_effect=ValueError("Invalid calendar")),
    ):
        rows = service.brokers()
    assert [(row["total_instruments"], row["total_sessions"]) for row in rows] == [
        (1, 0),
        (0, 1),
    ]
    assert rows[0]["stocks"] == ["ABC", "DEF"]
    tables = [call.args[0] for call in reads.call_args_list]
    assert tables.count("host_entities") == 1
    assert tables.count("datamgr_instruments") == 1
    assert tables.count("datamgr_sessions") == 1


def test_delete_brokers_removes_owned_configuration_only(
    caplog: pytest.LogCaptureFixture,
) -> None:
    service = Broker()
    first = service.add_broker(profile())
    second = service.add_broker(profile(name="Second"))
    retained = service.add_broker(profile(name="Retained"))
    service.edit_stocks(first["id"], ["ABC"])
    service.edit_stocks(retained["id"], ["KEEP"])
    with caplog.at_level(logging.INFO):
        result = service.delete_broker([first["id"], second["id"], first["id"]])
    assert result == {"deleted_ids": [first["id"], second["id"]], "deleted_count": 2}
    assert service.brokers() == [
        {**retained, "stocks": ["KEEP"], "customized_stocks": 1}
    ]
    assert [r["entity_id"] for r in HostPersistence.read_records("host_entities")] == [
        "retained"
    ]
    assert any(
        getattr(r, "fr_id", "") == "FR-DATAMGR-BROKER-DELETE" for r in caplog.records
    )


@pytest.mark.parametrize(
    "ids",
    [[], "1", [1], ["0"], ["-1"], ["01"], ["bad"], ["1"] * 10001],
    ids=[
        "empty",
        "string",
        "number",
        "zero",
        "default",
        "leading-zero",
        "bad",
        "oversize",
    ],
)
def test_delete_rejects_invalid_ids(ids: Any) -> None:
    with pytest.raises(ValueError):
        Broker().delete_broker(ids)


@pytest.mark.parametrize(
    "blocked",
    ["missing", "system", "instrument", "session", "dataset-id", "dataset-name"],
)
def test_delete_preflight_preserves_entire_selection(blocked: str) -> None:
    service = Broker()
    first = service.add_broker(profile())
    other = service.add_broker(profile(name="Other"))
    service.edit_stocks(first["id"], ["KEEP"])
    identifier = other["id"]
    if blocked == "missing":
        identifier = "999"
    elif blocked == "system":
        HostPersistence.update_record(
            "datamgr_broker", {"id": int(identifier)}, {"is_system": 1}
        )
    elif blocked == "instrument":
        service.import_instruments(identifier, [instrument()])
    elif blocked == "session":
        service.import_sessions(identifier, [schedule()])
    else:
        fields = "id source symbol underlying instrument timeframe broker broker_name timezone category date_from date_to created_at updated_at".split()
        dataset = dict.fromkeys(fields, "fixture")
        dataset["broker"] = identifier if blocked == "dataset-id" else other["name"]
        HostPersistence.create_record("datamgr_datasets", dataset)
    before = {
        table: HostPersistence.read_records(table, limit=0)
        for table in [
            "datamgr_broker",
            "datamgr_broker_stock",
            "host_entities",
            "datamgr_instruments",
            "datamgr_sessions",
            "datamgr_datasets",
        ]
    }
    with pytest.raises((ValueError, LookupError)):
        service.delete_broker([first["id"], identifier])
    assert before == {
        table: HostPersistence.read_records(table, limit=0) for table in before
    }


def test_delete_transaction_rolls_back() -> None:
    service = Broker()
    row = service.add_broker(profile())
    service.edit_stocks(row["id"], ["KEEP"])
    before = service.brokers()
    settings = HostPersistence.read_records("host_entities")
    real_batch = HostPersistence.apply_batch
    with patch.object(
        HostPersistence,
        "apply_batch",
        side_effect=lambda ops: real_batch(
            [*ops, {"op": "create", "table": "not_approved", "values": {}}]
        ),
    ):
        with pytest.raises(RuntimeError):
            service.delete_broker([row["id"]])
    assert service.brokers() == before
    assert HostPersistence.read_records("host_entities") == settings


def test_delete_route_validation_authority_and_storage_errors() -> None:
    app = FastAPI()
    app.include_router(create_data_manager_router(AppDataManager()))
    with TestClient(app) as client:
        row = client.post("/data/brokers", json=profile()).json()["data"]
        for body in ({}, {"ids": []}, {"ids": [row["id"]], "extra": True}):
            assert client.post("/data/brokers/delete", json=body).status_code == 422
        assert (
            client.post("/data/brokers/delete", json={"ids": ["999"]}).status_code
            == 404
        )
        with patch.object(
            HostPersistence,
            "apply_batch",
            side_effect=RuntimeError("private storage detail"),
        ):
            failed = client.post("/data/brokers/delete", json={"ids": [row["id"]]})
        assert failed.status_code == 503
        assert "private storage detail" not in failed.text
        assert client.post("/data/brokers/delete", json={"ids": [row["id"]]}).json()[
            "data"
        ] == {"deleted_ids": [row["id"]], "deleted_count": 1}
    protected = FastAPI()
    protected.include_router(
        create_data_manager_router(AppDataManager(), require_auth=True)
    )
    assert (
        TestClient(protected)
        .post("/data/brokers/delete", json={"ids": ["1"]})
        .status_code
        == 401
    )
