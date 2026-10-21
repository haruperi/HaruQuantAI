"""Public instrument contracts against isolated SQLite persistence."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest
from app.host.persistence import HostPersistence
from app.workspace.data_manager.instruments import Instruments
from app.workspace.data_manager.routes import create_data_manager_router
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(HostPersistence, "DEFAULT_DB_PATH", tmp_path / "instruments.db")


def specification(symbol: str = "TEST") -> dict[str, Any]:
    return {
        "symbol": symbol,
        "contract_size": 250,
        "pip_size": 0.01,
        "margin_rate": 0.0,
        "decimals": 2,
        "point_value": 12,
        "tick_size": 0.25,
        "tick_step": 0.05,
        "connection": "recorded",
        "commissions": "4.75",
        "swap_long": -2.5,
        "swap_short": 1.5,
    }


def client(*, require_auth: bool = False) -> TestClient:
    app = FastAPI()
    app.include_router(create_data_manager_router(require_auth=require_auth))
    return TestClient(app)


def test_add_reopen_and_independent_economics() -> None:
    row = Instruments().add_instrument(specification())
    assert isinstance(row["id"], str)
    assert row["margin_rate"] == 0
    assert row["point_value"] == 12
    assert row["contract_size"] == 250
    assert row["pip_size"] == row["point_size"] == 0.01
    assert row["tick_size"] == 0.25
    assert Instruments().instruments() == [row]
    assert len(HostPersistence.read_entity("datamgr_instrument_specs")) == 1


def test_all_records_and_filters() -> None:
    service = Instruments()
    for i in range(103):
        service.add_instrument(specification(f"TEST_{i:03}"))
    assert len(service.instruments()) == 103
    assert [r["symbol"] for r in service.instruments({"search": "test_102"})] == [
        "TEST_102"
    ]
    assert (
        len(service.instruments({"broker_id": "-1", "connection": "recorded"})) == 103
    )
    assert service.instruments({"data_type": "Futures"}) == []
    with pytest.raises(ValueError, match="filters"):
        service.instruments({"path": "unexpected"})


def test_legacy_metadata_remains_missing_and_clone_preserves_costs() -> None:
    values = specification()
    values.pop("contract_size")
    values.pop("pip_size")
    HostPersistence.create_record(
        "datamgr_instruments",
        {**values, "created_at_utc": "2020-01-01", "updated_at_utc": "2020-01-01"},
    )
    service = Instruments()
    source = service.instruments()[0]
    assert (
        source["contract_size"] is source["pip_size"] is source["swap_settings"] is None
    )
    clone = service.clone_instrument(source["id"], "CLONED")
    assert clone["id"] != source["id"]
    for key in (
        "contract_size",
        "pip_size",
        "commissions",
        "margin_rate",
        "swap_long",
        "tick_size",
        "broker_id",
    ):
        assert clone[key] == source[key]
    assert clone["created_at_utc"] != source["created_at_utc"]
    assert service.instruments({"search": "TEST"}) == [source]


def test_mass_edit_changes_only_selected_fields_and_clones_complete_extension() -> None:
    service = Instruments()
    first = service.add_instrument(specification("ONE"))
    second = service.add_instrument(
        {**specification("TWO"), "point_value": 80, "margin_rate": 0.2}
    )
    swap = {
        "use": True,
        "type": "money",
        "long": -5,
        "short": 2,
        "tripleSwapOn": "MONDAY",
        "rolloutHour": "22:30",
    }
    result = service.mass_edit_instruments(
        [first["id"], second["id"], first["id"]],
        {"contract_size": 75, "swap_settings": swap},
    )
    assert result["updated_count"] == 2
    one, two = result["instruments"]
    assert one["point_value"] == 12
    assert two["point_value"] == 80
    assert two["margin_rate"] == 0.2
    assert one["commissions"] == "4.75"
    assert one["swap_long"] == -5
    assert one["swap_3day_day"] == 0
    clone = service.clone_instrument(first["id"], "COPY")
    assert clone["swap_settings"] == swap
    assert clone["contract_size"] == 75


@pytest.mark.parametrize(
    "updates",
    [
        {},
        {"id": "10"},
        {"symbol": "RENAMED"},
        {"margin_rate": -1},
        {"tick_size": 0},
        {"tick_step": float("nan")},
        {"decimals": True},
        {"max_volume": 0},
        {"broker_id": 999},
        {"point_value": "5"},
        {"contract_size": -1},
        {"pip_size": float("inf")},
        {"commissions": '{"version":1,"settings":{}}'},
        {"swap_settings": {"use": True}},
    ],
)
def test_invalid_patch_never_changes_persisted_rows(updates: dict[str, Any]) -> None:
    service = Instruments()
    before = service.add_instrument(specification())
    with pytest.raises(ValueError):
        service.mass_edit_instruments([before["id"]], updates)
    assert service.instruments() == [before]


def test_missing_ids_and_duplicate_destinations_never_mutate() -> None:
    service = Instruments()
    row = service.add_instrument(specification())
    with pytest.raises(LookupError):
        service.mass_edit_instruments([row["id"], "999"], {"margin_rate": 0.1})
    with pytest.raises(FileExistsError):
        service.clone_instrument(row["id"], "test")
    with pytest.raises(FileExistsError):
        service.add_instrument(specification())
    with pytest.raises(ValueError):
        service.mass_edit_instruments("1", {"margin_rate": 0.1})
    with pytest.raises(ValueError):
        service.clone_instrument(row["id"], "bad symbol")
    assert service.instruments() == [row]


def test_actual_batch_failure_rolls_back_relational_and_extension_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = Instruments()
    first = service.add_instrument(specification("ONE"))
    second = service.add_instrument(specification("TWO"))
    original = HostPersistence.apply_batch

    def fail_batch(operations: Any) -> Any:
        # The first row/extension writes run before a genuine SQLite UNIQUE failure.
        return original(
            [
                *operations,
                {
                    "op": "create",
                    "table": "datamgr_instruments",
                    "values": {
                        "symbol": "ONE",
                        "created_at_utc": "now",
                        "updated_at_utc": "now",
                    },
                },
            ]
        )

    monkeypatch.setattr(HostPersistence, "apply_batch", fail_batch)
    with pytest.raises(RuntimeError, match="could not be saved"):
        service.mass_edit_instruments(
            [first["id"], second["id"]], {"contract_size": 19, "margin_rate": 0.9}
        )
    assert service.instruments() == [first, second]
    with pytest.raises(RuntimeError):
        service.add_instrument(specification("NEW"))
    assert service.instruments() == [first, second]


def test_http_envelopes_validation_and_auth() -> None:
    with client() as http:
        assert http.get("/data/instruments").json()["data"] == []
        response = http.post("/data/instruments", json=specification())
        assert response.status_code == 201
        row = response.json()["data"]
        assert http.post("/data/instruments", json=specification()).status_code == 409
        assert http.get("/data/instruments?unknown=true").status_code == 422
        result = http.post(
            "/data/instruments/mass-edit",
            json={"instrument_ids": [row["id"]], "updates": {"margin_rate": 0.2}},
        )
        assert result.json()["data"]["instruments"][0]["margin_rate"] == 0.2
        assert (
            http.post(
                "/data/instruments/clone",
                json={"source_id": row["id"], "new_symbol": "COPY"},
            ).status_code
            == 201
        )
        assert (
            http.post(
                "/data/instruments/clone",
                json={"source_id": "999", "new_symbol": "MISS"},
            ).status_code
            == 404
        )
        assert (
            http.post(
                "/data/instruments/mass-edit",
                json={"instrument_ids": "1", "updates": {}},
            ).status_code
            == 422
        )
    with client(require_auth=True) as http:
        assert http.get("/data/instruments").status_code == 401
        assert http.post("/data/instruments", json=specification()).status_code == 401


def test_corrupt_extension_fails_explicitly_without_exposing_storage_error() -> None:
    row = Instruments().add_instrument(specification())
    HostPersistence.update_entity(
        "datamgr_instrument_specs", row["symbol"], {"payload": "{"}
    )
    with client() as http:
        response = http.get("/data/instruments")
        assert response.status_code == 503
        assert "payload" not in response.text


def test_requirement_boundary_logging(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        service = Instruments()
        row = service.add_instrument(specification())
        service.instruments()
        service.mass_edit_instruments([row["id"]], {"margin_rate": 0.1})
        service.clone_instrument(row["id"], "COPY")
    ids = {getattr(record, "fr_id", None) for record in caplog.records}
    assert {
        "FR-DATAMGR-INSTR-LIST",
        "FR-DATAMGR-INSTR-ADD",
        "FR-DATAMGR-INSTR-MASS-EDIT",
        "FR-DATAMGR-INSTR-CLONE",
    } <= ids


def test_scalar_swap_patch_keeps_full_settings_consistent() -> None:
    service = Instruments()
    swap = {
        "use": True,
        "type": "money",
        "long": -2,
        "short": 1,
        "tripleSwapOn": "MONDAY",
        "rolloutHour": "21:30",
    }
    row = service.add_instrument(
        {"symbol": "SWAP", "contract_size": 1, "pip_size": 0.01, "swap_settings": swap}
    )
    extension = HostPersistence.read_entity("datamgr_instrument_specs", "SWAP")[0]
    result = service.mass_edit_instruments([row["id"]], {"swap_short": 8})[
        "instruments"
    ][0]
    assert result["swap_settings"] == {**swap, "short": 8}
    updated = HostPersistence.read_entity("datamgr_instrument_specs", "SWAP")[0]
    assert updated["created_at_utc"] == extension["created_at_utc"]
    assert updated["revision"] == 2
    with pytest.raises(ValueError, match="not both"):
        service.mass_edit_instruments(
            [row["id"]], {"swap_settings": swap, "swap_short": 8}
        )
