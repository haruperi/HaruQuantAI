"""Exercise grouped catalog operations against isolated host persistence."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from app.host.persistence import HostPersistence
from app.services.include.contracts import SymbolInfo
from app.workspace.data_manager.instruments import Instruments, InstrumentsCLI


@pytest.fixture(autouse=True)
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(HostPersistence, "DEFAULT_DB_PATH", tmp_path / "instruments.db")


def specification(symbol: str = "TEST") -> dict[str, Any]:
    return {
        "symbol": symbol,
        "contract_size": 250,
        "pip_size": 0.01,
        "point_value": 12,
        "margin_rate": 0,
        "connection": "recorded",
    }


def test_add_list_filter_and_duplicate() -> None:
    service = Instruments()
    row = service.add_instrument(specification())
    assert isinstance(row["id"], str)
    assert row["contract_size"] == 250
    assert row["margin_rate"] == 0
    assert service.instruments({"symbol": "TEST"}) == [row]
    assert service.instruments({"data_type": "Missing"}) == []
    with pytest.raises(RuntimeError):
        service.add_instrument(specification())
    assert service.instruments() == [row]


def test_mass_edit_merges_siblings_and_is_atomic() -> None:
    service = Instruments()
    first = service.add_instrument(specification("ONE"))
    second = service.add_instrument(
        {**specification("TWO"), "contract_size": 80, "point_value": 9}
    )
    result = service.mass_edit_instruments(
        [first["id"], second["id"]], {"contract_size": 75}
    )
    assert result["updated_count"] == 2
    one, two = result["instruments"]
    assert one["contract_size"] == two["contract_size"] == 75
    assert one["point_value"] == 12
    assert two["point_value"] == 9
    before = service.instruments()
    with pytest.raises(LookupError):
        service.mass_edit_instruments([first["id"], "999"], {"contract_size": 5})
    assert service.instruments() == before
    with pytest.raises(ValueError):
        service.mass_edit_instruments([first["id"]], {"unknown_field": 2})
    assert service.instruments() == before


def test_clone_and_delete_preserve_grouped_values() -> None:
    service = Instruments()
    source = service.add_instrument(specification())
    clone = service.clone_instrument(source["id"], "COPY")
    assert clone["id"] != source["id"]
    assert clone["contract_size"] == source["contract_size"]
    with pytest.raises(LookupError):
        service.delete_instruments([source["id"], "999"])
    assert len(service.instruments()) == 2
    assert service.delete_instruments([source["id"]]) == {"deleted_count": 1}
    assert service.instruments() == [clone]


def test_requirement_boundary_logging(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        service = Instruments()
        row = service.add_instrument(specification())
        service.instruments()
        service.mass_edit_instruments([row["id"]], {"margin_rate": 0.1})
        service.clone_instrument(row["id"], "COPY")
        service.delete_instruments([row["id"]])
    ids = {getattr(record, "fr_id", None) for record in caplog.records}
    assert {
        "FR-DATAMGR-INSTR-LIST",
        "FR-DATAMGR-INSTR-ADD",
        "FR-DATAMGR-INSTR-MASS-EDIT",
        "FR-DATAMGR-INSTR-CLONE",
        "FR-DATAMGR-INSTR-DELETE",
    } <= ids


def test_cli_grouped_add_edit_list_delete() -> None:
    service = Instruments()
    cli = InstrumentsCLI
    row = cli.dispatch(
        ["action=add", "instrument=EURUSD", "swapLong=-2.5", "broker=-1"], service
    )["instrument"]
    assert row["swap_long"] == -2.5
    edited = cli.dispatch(["action=edit", "instrument=EURUSD", "pointvalue=7"], service)
    assert edited["instruments"][0]["point_value"] == 7
    assert "EURUSD" in cli.dispatch(["list"], service)["rendered"]
    assert cli.dispatch(["delete", "instruments=EURUSD"], service)["deleted_count"] == 1
    with pytest.raises(ValueError, match="Unsupported"):
        cli.dispatch(["action=bogus"], service)


def _simulated_trading(*infos: Any) -> Any:
    from app.services.brokers.simulator import SimulatorClient
    from app.services.include.trading import Trading

    backend = SimulatorClient()
    for info in infos:
        backend.add_symbol(info)
    return Trading(backend)


def test_refresh_subset_retains_existing_flat_contract(
    caplog: pytest.LogCaptureFixture,
) -> None:
    service = Instruments()
    keep = service.add_instrument(specification("KEEP"))
    service.add_instrument(specification("EURJPY"))
    trading = _simulated_trading(
        SymbolInfo(
            name="EURJPY",
            path="Markets\\Forex\\Majors\\EURJPY",
            digits=3,
            point=0.001,
            spread=17,
            swap_long=-0.2,
            currency_profit="JPY",
            trade_stops_level=4,
            filling_mode=3,
        )
    )

    async def run() -> dict[str, Any]:
        async with trading:
            return await service.refresh_instruments(trading, ["EURJPY"])

    with caplog.at_level(logging.INFO):
        assert asyncio.run(run()) == {"deleted_count": 1, "inserted_count": 1}
    assert any(
        getattr(r, "fr_id", None) == "FR-DATAMGR-INSTR-REFRESH" for r in caplog.records
    )
    rows = {r["symbol"]: r for r in service.instruments()}
    current = rows["EURJPY"]
    assert rows["KEEP"] == keep
    assert current["swap_long"] == -0.2
    assert current["default_spread"] == pytest.approx(0.017)
    assert current["filling_mode"] == 3
    assert current["currency_profit"] == "JPY"
    assert current["data_type"] == "Forex\\Majors"
    assert current["swap_settings"] is None
    assert json.loads(current["commissions"])["status"] == "not_retrieved"
    assert "specification_meta" not in current


def test_refresh_failure_never_partially_writes() -> None:
    service = Instruments()
    row = service.add_instrument(specification())
    trading = _simulated_trading(SymbolInfo(name="VALID"))

    async def run(names: list[str]) -> None:
        async with trading:
            await service.refresh_instruments(trading, names)

    with pytest.raises(LookupError):
        asyncio.run(run(["VALID", "MISSING"]))
    assert service.instruments() == [row]
    with pytest.raises(ValueError, match="at least one"):
        asyncio.run(run([]))


def test_refresh_all_keeps_existing_replacement_behavior() -> None:
    service = Instruments()
    service.add_instrument(specification("MANUAL"))
    trading = _simulated_trading(SymbolInfo(name="EURUSD"))

    async def run() -> dict[str, Any]:
        async with trading:
            return await service.refresh_instruments(trading)

    assert asyncio.run(run())["inserted_count"] == 1
    assert {r["symbol"] for r in service.instruments()} == {"EURUSD"}


def _client(trading_factory: Any) -> Any:
    from app.workspace.data_manager.routes import (
        AppDataManager,
        create_data_manager_router,
    )
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()
    workspace = AppDataManager(trading_factory=trading_factory)
    app.include_router(create_data_manager_router(workspace))
    return TestClient(app)


@pytest.mark.parametrize("configured_token", [None, "", "   "])
def test_bridge_factory_requires_configured_token(
    monkeypatch: pytest.MonkeyPatch, configured_token: str | None
) -> None:
    from app.services.brokers import metatrader
    from app.workspace.data_manager.routes import _metatrader_trading

    if configured_token is None:
        monkeypatch.delenv("MT5_BRIDGE_TOKEN", raising=False)
    else:
        monkeypatch.setenv("MT5_BRIDGE_TOKEN", configured_token)
    client_factory = MagicMock()
    monkeypatch.setattr(metatrader, "MetaTraderClient", client_factory)

    with pytest.raises(ValueError, match="MT5_BRIDGE_TOKEN is not set"):
        _metatrader_trading()
    client_factory.assert_not_called()


def test_bridge_factory_uses_environment_token(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services.brokers import metatrader
    from app.services.include import trading
    from app.workspace.data_manager.routes import _metatrader_trading

    monkeypatch.setenv("MT5_BRIDGE_TOKEN", "  test-only-configured-token  ")
    client_factory = MagicMock()
    facade_factory = MagicMock()
    monkeypatch.setattr(metatrader, "MetaTraderClient", client_factory)
    monkeypatch.setattr(trading, "Trading", facade_factory)

    assert _metatrader_trading() is facade_factory.return_value
    client_factory.assert_called_once_with(auth_token="test-only-configured-token")
    facade_factory.assert_called_once_with(client_factory.return_value)


def test_delete_and_refresh_routes() -> None:
    from app.services.include.contracts import SymbolInfo

    service = Instruments()
    one = service.add_instrument(specification("ONE"))
    client = _client(
        lambda: _simulated_trading(
            SymbolInfo(name="EURJPY", path="Forex\\EURJPY", digits=3, point=0.001)
        )
    )
    assert client.post("/data/instruments/delete", json={}).status_code == 422
    assert (
        client.post(
            "/data/instruments/delete", json={"instrument_ids": ["99"]}
        ).status_code
        == 404
    )
    deleted = client.post(
        "/data/instruments/delete", json={"instrument_ids": [one["id"]]}
    )
    assert deleted.status_code == 200
    assert service.instruments() == []
    assert (
        client.post("/data/instruments/refresh", json={"symbols": "x"}).status_code
        == 422
    )
    assert (
        client.post("/data/instruments/refresh", json={"symbols": []}).status_code
        == 422
    )
    assert (
        client.post("/data/instruments/refresh", json={"symbols": ["NOPE"]}).status_code
        == 422
    )
    done = client.post("/data/instruments/refresh", json={"symbols": ["EURJPY"]})
    assert done.status_code == 200
    assert [r["symbol"] for r in service.instruments()] == ["EURJPY"]


def test_normalize_data_type() -> None:
    from app.workspace.data_manager.instruments import _normalize_data_type

    assert _normalize_data_type("Markets\\Forex\\Majors\\USDCAD") == "Forex\\Majors"
    assert _normalize_data_type("Markets/Forex/Majors/USDCAD") == "Forex\\Majors"
    assert (
        _normalize_data_type("Markets\\Stocks\\Hong Kong\\0001.HK")
        == "Stocks\\Hong Kong"
    )
    assert _normalize_data_type("Markets\\Forex\\EURUSD") == "Forex"
    assert _normalize_data_type("Forex\\EURUSD") == "Forex"
    assert _normalize_data_type("Forex") == "Forex"
    assert _normalize_data_type("") == ""


def test_flat_filters_still_match_values_stored_in_json() -> None:
    service = Instruments()
    row = service.add_instrument(
        {**specification(), "swap_long": -2.5, "filling_mode": 3}
    )
    assert service.instruments({"swap_long": -2.5, "filling_mode": "3"}) == [row]
    assert service.instruments({"id": int(row["id"])}) == [row]
    assert service.instruments({"id": float(row["id"])}) == [row]
    assert service.instruments({"swap_long": "bad"}) == []
    assert service.instruments({"cot": None}) == [row]
    with pytest.raises(ValueError, match="Unsupported instrument filter"):
        service.instruments({"unknown": 2})


def test_broker_commissions_refresh_storage_and_manual_edit_are_lossless() -> None:
    service = Instruments()
    configured = {"model": "Per trade", "value": 7}
    service.add_instrument(
        {
            "symbol": "EURUSD",
            "commissions": json.dumps({"version": 1, "settings": configured}),
        }
    )
    keep = service.add_instrument(specification("KEEP"))
    rule = {
        "currency": "USD",
        "range": "range volume",
        "charge": "charge instant",
        "entry": "entry inout",
        "direction": "direction both",
        "profit": "profit all",
        "tiers": [
            {
                "mode": "money specified",
                "volume_type": "volume type volume",
                "value": 3.5,
                "min": 0.01,
                "max": 0,
                "from": 0,
                "to": 1e9,
                "currency": "USD",
                "effective_currency": "USD",
            }
        ],
    }
    document = {"version": 2, "source": "mt5", "status": "available", "rules": [rule]}
    trading = _simulated_trading(
        SymbolInfo(name="EURUSD", commissions=json.dumps(document))
    )

    async def refresh() -> None:
        async with trading:
            await service.refresh_instruments(trading, ["EURUSD"])

    asyncio.run(refresh())
    current = service.instruments({"symbol": "EURUSD"})[0]
    parsed = json.loads(current["commissions"])
    assert parsed["rules"] == [rule]
    assert parsed["settings"] == configured
    raw = HostPersistence.read_records("datamgr_instruments", {"symbol": "EURUSD"})[0]
    assert json.loads(raw["commissions"])["rules"] == [rule]
    assert isinstance(current["commissions"], str)
    assert service.instruments({"symbol": "KEEP"}) == [keep]
    patch = json.dumps({"version": 1, "settings": {**configured, "value": 9}})
    edited = service.mass_edit_instruments([current["id"]], {"commissions": patch})[
        "instruments"
    ][0]
    changed = json.loads(edited["commissions"])
    assert changed["settings"]["value"] == 9
    assert changed["rules"] == [rule]
    unrelated = service.mass_edit_instruments([edited["id"]], {"default_spread": 0.2})[
        "instruments"
    ][0]
    assert json.loads(unrelated["commissions"]) == changed


def test_old_ea_default_keeps_manual_settings_without_inventing_broker_zero() -> None:
    service = Instruments()
    configured = {"model": "Per trade", "value": 5}
    service.add_instrument(
        {
            "symbol": "EURUSD",
            "commissions": json.dumps({"version": 1, "settings": configured}),
        }
    )
    trading = _simulated_trading(SymbolInfo(name="EURUSD"))

    async def refresh() -> None:
        async with trading:
            await service.refresh_instruments(trading, ["EURUSD"])

    asyncio.run(refresh())
    current = json.loads(service.instruments()[0]["commissions"])
    assert current["status"] == "not_retrieved"
    assert current["rules"] is None
    assert current["settings"] == configured
