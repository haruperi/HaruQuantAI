"""Unit tests for Symbols service CRUD, cloning, and CSV import/export commands."""

from __future__ import annotations

import sqlite3
from unittest.mock import patch

import pytest
from app.host.persistence import HostPersistence
from app.host.transport import register_transport_exception_handlers
from app.workspace.data_manager import http as symbols_http
from app.workspace.data_manager.symbols import Symbols
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def symbol_http(temp_db):
    application = FastAPI()
    application.state.persistence = temp_db
    application.include_router(symbols_http.create_router())
    application.dependency_overrides[symbols_http._access] = lambda: None
    register_transport_exception_handlers(application)
    with TestClient(application) as client:
        yield client


def test_symbol_http_workspace_and_commands(symbol_http, temp_db):
    client = symbol_http
    workspace = client.get("/api/v1/data/workspace").json()["data"]
    assert len(workspace["tabs"]) == 9
    assert (
        client.post("/api/v1/data/workspace/tabs/symbols", json={}).json()["data"][
            "active_tab"
        ]
        == "symbols"
    )
    body = {
        "symbol": "WEB",
        "datasource": "demo",
        "description": "Browser symbol",
        "commissions": "7",
        "point_value": 12,
        "contract_size": 100,
        "tick_size": 0.25,
        "pip_size": 0.1,
    }
    response = client.post("/api/v1/data/instruments", json=body)
    assert response.status_code == 200
    source = response.json()["data"]
    assert source["symbol"] == "WEB_demo"
    assert source["point_value"] == 12
    assert source["contract_size"] == 100
    assert source["tick_size"] == 0.25
    assert source["pip_size"] == 0.1
    assert client.post("/api/v1/data/instruments", json=body).status_code == 409
    cloned = client.post(
        "/api/v1/data/instruments/clone",
        json={"source_id": source["id"], "new_symbol": "COPY"},
    ).json()["data"]
    assert cloned["symbol"] == "COPY_demo"
    ids = [source["id"], cloned["id"]]
    edited = client.post(
        "/api/v1/data/instruments/mass-edit",
        json={"instrument_ids": ids, "updates": {"default_spread": 0}},
    )
    assert edited.status_code == 200
    assert edited.json()["data"]["updated_count"] == 2
    assert all(row["default_spread"] == 0 for row in edited.json()["data"]["symbols"])
    assert all(row["commissions"] == "7" for row in edited.json()["data"]["symbols"])
    saved = client.post("/api/v1/data/instruments/save", json={}).json()["data"]
    assert saved["count"] == 2
    assert "WEB_demo" in saved["content"]
    deleted = client.post(
        "/api/v1/data/instruments/delete", json={"instrument_ids": ids}
    )
    assert deleted.json()["data"]["deleted_count"] == 2
    assert client.get("/api/v1/data/instruments").json()["data"] == []
    loaded = client.post(
        "/api/v1/data/instruments/load", json={"content": saved["content"]}
    )
    assert loaded.json()["data"]["loaded_count"] == 2
    assert Symbols(temp_db).get("WEB_demo")["success"]


def test_symbol_http_partial_import_and_errors(symbol_http):
    response = symbol_http.post(
        "/api/v1/data/instruments/load",
        json={"content": "name,datasource,commission\nONE,demo,7\nBAD,demo,invalid\n"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["loaded_count"] == 1
    assert response.json()["data"]["errors"][0]["row"] == 2
    assert (
        symbol_http.post(
            "/api/v1/data/instruments/load", json={"content": ""}
        ).status_code
        == 422
    )
    assert (
        symbol_http.post(
            "/api/v1/data/instruments/delete", json={"instrument_ids": ["999"]}
        ).status_code
        == 404
    )


def test_symbol_http_validates_fields_and_preserves_settings(symbol_http, temp_db):
    import json

    settings = {"version": 1, "settings": {"model": "Per trade", "value": 7}}
    swap = {
        "use": True,
        "type": "points",
        "long": -2,
        "short": 1,
        "tripleSwapOn": "FRIDAY",
        "rolloutHour": "22:00",
    }
    body = {
        "symbol": "SETTINGS",
        "datasource": "demo",
        "commissions": json.dumps(settings),
        "swap_settings": swap,
        "default_slippage": 2,
        "margin_rate": 0.05,
    }
    created = symbol_http.post("/api/v1/data/instruments", json=body).json()["data"]
    assert json.loads(created["commissions"]) == settings
    assert created["swap_settings"] == swap
    assert created["default_slippage"] == 2
    assert created["margin_rate"] == 0.05
    invalid = symbol_http.post(
        "/api/v1/data/instruments/mass-edit",
        json={"instrument_ids": [created["id"]], "updates": {"default_spread": "bad"}},
    )
    assert invalid.status_code == 422
    assert (
        symbol_http.post(
            "/api/v1/data/instruments", json={"symbol": "BAD", "commissions": "bad"}
        ).status_code
        == 422
    )
    exported = symbol_http.post("/api/v1/data/instruments/save", json={}).json()[
        "data"
    ]["content"]
    symbol_http.post(
        "/api/v1/data/instruments/delete", json={"instrument_ids": [created["id"]]}
    )
    symbol_http.post("/api/v1/data/instruments/load", json={"content": exported})
    restored = symbol_http.get("/api/v1/data/instruments").json()["data"][0]
    assert restored["swap_settings"] == swap
    assert json.loads(restored["commissions"]) == settings
    assert Symbols(temp_db).edit(
        "SETTINGS_demo", commission=3, swap_long=-4, point_value=500, pip_size=0.01
    )["success"]
    edited = symbol_http.get("/api/v1/data/instruments").json()["data"][0]
    assert edited["commissions"] == "3.0"
    assert edited["swap_settings"] is None
    assert edited["swap_long"] == -4
    assert edited["point_value"] == 500
    assert edited["pip_size"] == 0.01


def test_symbol_http_requires_ui_session(temp_db):
    from unittest.mock import Mock

    application = FastAPI()
    application.state.persistence = temp_db
    application.state.sessions = Mock()
    application.state.sessions.validate_session.return_value = None
    register_transport_exception_handlers(application)
    application.include_router(symbols_http.create_router())
    with TestClient(application) as client:
        assert client.get("/api/v1/data/instruments").status_code == 401
        assert (
            client.post(
                "/api/v1/data/instruments/load", json={"content": ""}
            ).status_code
            == 401
        )
        application.state.sessions.validate_session.return_value = object()
        application.state.sessions.authorize.return_value = False
        assert (
            client.post("/api/v1/data/instruments/delete", json={}).status_code == 403
        )


@pytest.fixture
def temp_db(tmp_path):
    """Provide an isolated test database with refactored datamgr_symbols schema."""
    db_path = tmp_path / "test_haruquantai.db"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE "datamgr_symbols" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            exchange TEXT DEFAULT '',
            data_type TEXT DEFAULT 'Forex',
            spread TEXT NOT NULL DEFAULT '{}',
            margin TEXT NOT NULL DEFAULT '{}',
            volume TEXT NOT NULL DEFAULT '{}',
            trade TEXT NOT NULL DEFAULT '{}',
            price TEXT NOT NULL DEFAULT '{}',
            swap TEXT NOT NULL DEFAULT '{}',
            commission REAL DEFAULT 0.0,
            session TEXT NOT NULL DEFAULT '[]',
            state TEXT NOT NULL DEFAULT '{}',
            broker_id INTEGER DEFAULT 0,
            created_at_utc TEXT NOT NULL,
            updated_at_utc TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

    test_persistence = HostPersistence(db_path)
    with patch("app.workspace.data_manager.symbols.persistence", test_persistence):
        yield test_persistence


def test_symbols_add_success(temp_db) -> None:
    svc = Symbols()
    res = svc.add(name="EURUSD", datasource="dukascopy")

    assert res["success"] is True
    assert res["metadata"]["operation"] == "symbols.add"
    assert res["data"]["name"] == "EURUSD_dukascopy"
    assert res["data"]["data_type"] == "Forex"
    assert res["data"]["price"]["tick_size"] == 0.0001
    assert res["data"]["price"]["contract_size"] == 100000.0
    assert res["data"]["spread"]["default"] == 1.0
    assert res["data"]["swap"]["mode"] == "Points"
    assert res["data"]["swap"]["rollover3days"] == "Wednesday"


def test_cli_add_persists_symbol_and_reports_duplicate(temp_db, capsys, monkeypatch):
    from app import cli

    monkeypatch.setattr(cli, "shutdown_logging", lambda: None)
    command = [
        "data-manager",
        "symbol",
        "add",
        "--name",
        "EURUSD",
        "--datasource",
        "demo",
        "--description",
        "Euro vs Dollar",
        "--pip-size",
        "0.0001",
        "--point-value",
        "100000",
        "--default-spread",
        "1.5",
        "--commission",
        "7",
        "--swap-long",
        "-2.5",
        "--order-size-step",
        "0.01",
    ]
    assert cli.main(command) == 0
    output = capsys.readouterr().out
    assert "Added symbol 'EURUSD_demo'" in output
    assert "=== Symbols Catalog (1 items) ===" in output
    row = temp_db.read_records("datamgr_symbols")["data"]["records"][0]
    assert row["name"] == "EURUSD_demo"
    assert row["commission"] == 7
    symbol = Symbols().get("EURUSD_demo")["data"]
    assert symbol["spread"]["default"] == 1.5
    assert symbol["swap"]["long"] == -2.5
    assert cli.main(command) == 1
    assert '"code": "conflict"' in capsys.readouterr().out


@pytest.mark.parametrize(
    "arguments",
    [
        [],
        ["--name", "EURUSD"],
        ["--name", "EURUSD", "--datasource", "demo", "--commission", "invalid"],
    ],
)
def test_cli_add_rejects_invalid_arguments(temp_db, monkeypatch, arguments):
    from app import cli

    monkeypatch.setattr(cli, "shutdown_logging", lambda: None)
    with pytest.raises(SystemExit) as error:
        cli.main(["data-manager", "symbol", "add", *arguments])
    assert error.value.code == 2
    assert temp_db.read_records("datamgr_symbols")["data"]["records"] == []


def test_cli_edit_updates_only_supplied_fields(temp_db, capsys, monkeypatch):
    from app import cli

    monkeypatch.setattr(cli, "shutdown_logging", lambda: None)
    service = Symbols()
    assert service.add(
        name="EURUSD", datasource="demo", description="Original", commission=7
    )["success"]
    assert (
        cli.main(
            [
                "data-manager",
                "symbol",
                "edit",
                "EURUSD_demo",
                "--default-spread",
                "0",
                "--swap-long",
                "-3.5",
                "--description",
                "Updated",
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "Successfully edited 1 symbol(s)" in output
    assert "EURUSD_demo" in output
    symbol = service.get("EURUSD_demo")["data"]
    assert symbol["spread"]["default"] == 0
    assert symbol["swap"]["long"] == -3.5
    assert symbol["description"] == "Updated"
    assert symbol["commission"] == 7
    assert symbol["price"]["contract_size"] == 100000
    assert (
        cli.main(
            ["data-manager", "symbol", "edit", "EURUSD_demo", "--name", "RENAMED_demo"]
        )
        == 0
    )
    capsys.readouterr()
    assert service.get("RENAMED_demo")["success"]
    assert not service.get("EURUSD_demo")["success"]


def test_cli_edit_missing_symbol(temp_db, capsys, monkeypatch):
    from app import cli

    monkeypatch.setattr(cli, "shutdown_logging", lambda: None)
    assert (
        cli.main(["data-manager", "symbol", "edit", "MISSING", "--commission", "0"])
        == 1
    )
    assert '"code": "not_found"' in capsys.readouterr().out
    assert temp_db.read_records("datamgr_symbols")["data"]["records"] == []


@pytest.mark.parametrize(
    "arguments", [[], ["EURUSD_demo"], ["EURUSD_demo", "--commission", "invalid"]]
)
def test_cli_edit_invalid_arguments(temp_db, monkeypatch, arguments):
    from app import cli

    monkeypatch.setattr(cli, "shutdown_logging", lambda: None)
    assert Symbols().add(name="EURUSD", datasource="demo", commission=7)["success"]
    with pytest.raises(SystemExit) as error:
        cli.main(["data-manager", "symbol", "edit", *arguments])
    assert error.value.code == 2
    assert Symbols().get("EURUSD_demo")["data"]["commission"] == 7


def test_cli_delete_removes_only_named_symbol(temp_db, capsys, monkeypatch):
    from app import cli

    monkeypatch.setattr(cli, "shutdown_logging", lambda: None)
    service = Symbols()
    assert service.add(name="EURUSD", datasource="demo")["success"]
    assert service.add(name="GBPUSD", datasource="demo")["success"]
    command = ["data-manager", "symbol", "delete", "EURUSD_demo"]
    assert cli.main(command) == 0
    output = capsys.readouterr().out
    assert "Deleted 1 symbol(s)" in output
    assert "EURUSD_demo" in output
    assert not service.get("EURUSD_demo")["success"]
    assert service.get("GBPUSD_demo")["success"]
    assert cli.main(command) == 1
    assert '"code": "not_found"' in capsys.readouterr().out


@pytest.mark.parametrize(
    "arguments",
    [[], ["EURUSD_demo", "--name", "OTHER"]],
)
def test_cli_delete_invalid_arguments(temp_db, monkeypatch, arguments):
    from app import cli

    monkeypatch.setattr(cli, "shutdown_logging", lambda: None)
    assert Symbols().add(name="EURUSD", datasource="demo")["success"]
    with pytest.raises(SystemExit) as error:
        cli.main(["data-manager", "symbol", "delete", *arguments])
    assert error.value.code == 2
    assert Symbols().get("EURUSD_demo")["success"]


def test_cli_bulk_edit_and_delete(temp_db, capsys, monkeypatch):
    from app import cli

    monkeypatch.setattr(cli, "shutdown_logging", lambda: None)
    service = Symbols()
    for name in ("EURUSD", "GBPUSD", "USDJPY"):
        assert service.add(name=name, datasource="demo", commission=7)["success"]
    names = ["EURUSD_demo", "GBPUSD_demo"]
    assert (
        cli.main(
            [
                "data-manager",
                "symbol",
                "edit",
                *names,
                "--commission",
                "0",
                "--swap-long",
                "-2",
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "Successfully edited 2 symbol(s)" in output
    for name in names:
        symbol = service.get(name)["data"]
        assert symbol["commission"] == 0
        assert symbol["swap"]["long"] == -2
        assert name in output
    assert service.get("USDJPY_demo")["data"]["commission"] == 7
    with pytest.raises(SystemExit) as error:
        cli.main(["data-manager", "symbol", "edit", *names, "--name", "SAME"])
    assert error.value.code == 2
    capsys.readouterr()
    assert cli.main(["data-manager", "symbol", "delete", *names]) == 0
    output = capsys.readouterr().out
    assert "Deleted 2 symbol(s)" in output
    for name in names:
        assert name in output
        assert not service.get(name)["success"]
    assert service.get("USDJPY_demo")["success"]


def test_symbols_add_validation_failures(temp_db) -> None:
    svc = Symbols()
    res_no_name = svc.add(name="", datasource="dukascopy")
    assert res_no_name["success"] is False
    assert res_no_name["error"]["code"] == "validation"

    res_no_ds = svc.add(name="EURUSD", datasource="")
    assert res_no_ds["success"] is False
    assert res_no_ds["error"]["code"] == "validation"


def test_symbols_add_conflict(temp_db) -> None:
    svc = Symbols()
    res1 = svc.add(name="EURUSD", datasource="dukascopy")
    assert res1["success"] is True

    res2 = svc.add(name="EURUSD", datasource="dukascopy")
    assert res2["success"] is False
    assert res2["error"]["code"] == "conflict"
    assert "already exists" in res2["message"]


def test_symbols_add_custom_screenshot_fields(temp_db) -> None:
    svc = Symbols()
    res = svc.add(
        name="GBPUSD",
        datasource="custom_broker",
        description="British Pound vs US Dollar",
        pip_size=0.0001,
        point_value=100000.0,
        pip_step=0.00001,
        default_spread=2.0,
        min_distance=5.0,
        order_size_multiplier=2.0,
        order_size_step=0.1,
        commission_value=0.05,
        swap_long=-1.5,
        swap_short=0.8,
        triple_swap_on="Wednesday",
    )

    assert res["success"] is True
    data = res["data"]
    assert data["name"] == "GBPUSD_custom_broker"
    assert data["description"] == "British Pound vs US Dollar"
    assert data["spread"]["default"] == 2.0
    assert data["trade"]["min_distance"] == 5.0
    assert data["volume"]["min"] == 2.0
    assert data["volume"]["step"] == 0.1
    assert data["commission"] == 0.05
    assert data["swap"]["long"] == -1.5
    assert data["swap"]["short"] == 0.8
    assert data["swap"]["rollover3days"] == "Wednesday"


def test_symbols_edit_single(temp_db) -> None:
    svc = Symbols()
    svc.add(name="USDJPY", datasource="dukascopy")

    edit_res = svc.edit(
        "USDJPY_dukascopy",
        description="US Dollar vs Japanese Yen",
        default_spread=1.8,
        pip_size=0.01,
    )

    assert edit_res["success"] is True
    assert edit_res["metadata"]["operation"] == "symbols.edit"
    records = edit_res["data"]
    assert len(records) == 1
    assert records[0]["description"] == "US Dollar vs Japanese Yen"
    assert records[0]["spread"]["default"] == 1.8
    assert records[0]["price"]["tick_size"] == 0.01


def test_symbols_edit_mass(temp_db) -> None:
    svc = Symbols()
    svc.add(name="AUDUSD", datasource="brokerA")
    svc.add(name="NZDUSD", datasource="brokerA")

    mass_res = svc.edit(
        ["AUDUSD_brokerA", "NZDUSD_brokerA"],
        default_spread=3.0,
        commission_value=2.5,
    )

    assert mass_res["success"] is True
    records = mass_res["data"]
    assert len(records) == 2
    for r in records:
        assert r["spread"]["default"] == 3.0
        assert r["commission"] == 2.5


def test_symbols_edit_validation_and_not_found(temp_db) -> None:
    svc = Symbols()
    res_empty_syms = svc.edit([], default_spread=1.0)
    assert res_empty_syms["success"] is False
    assert res_empty_syms["error"]["code"] == "validation"

    res_empty_fields = svc.edit("NONEXISTENT", {})
    assert res_empty_fields["success"] is False
    assert res_empty_fields["error"]["code"] == "validation"

    res_not_found = svc.edit("NONEXISTENT", default_spread=1.0)
    assert res_not_found["success"] is False
    assert res_not_found["error"]["code"] == "not_found"


def test_symbols_delete_single_and_multiple(temp_db) -> None:
    svc = Symbols()
    svc.add(name="EURGBP", datasource="ds1")
    svc.add(name="EURCAD", datasource="ds1")
    svc.add(name="EURAUD", datasource="ds1")

    # Delete single
    del1 = svc.delete("EURGBP_ds1")
    assert del1["success"] is True
    assert del1["metadata"]["operation"] == "symbols.delete"
    assert del1["data"] == ["EURGBP_ds1"]

    # Delete multiple
    del_multi = svc.delete(["EURCAD_ds1", "EURAUD_ds1"])
    assert del_multi["success"] is True
    assert sorted(del_multi["data"]) == ["EURAUD_ds1", "EURCAD_ds1"]

    # Verify deleted
    assert svc.get("EURGBP_ds1")["success"] is False
    assert svc.get("EURCAD_ds1")["success"] is False


def test_symbols_delete_validation_and_not_found(temp_db) -> None:
    svc = Symbols()
    del_empty = svc.delete([])
    assert del_empty["success"] is False
    assert del_empty["error"]["code"] == "validation"

    del_nf = svc.delete("NONEXISTENT")
    assert del_nf["success"] is False
    assert del_nf["error"]["code"] == "not_found"


def test_cli_clone_persists_copy(temp_db, capsys, monkeypatch):
    from app import cli

    monkeypatch.setattr(cli, "shutdown_logging", lambda: None)
    service = Symbols()
    assert service.add(
        name="EURUSD",
        datasource="demo",
        description="Original",
        commission=7,
        default_spread=2,
    )["success"]
    command = ["data-manager", "symbol", "clone", "EURUSD_demo", "EURUSD_COPY"]
    assert cli.main(command) == 0
    output = capsys.readouterr().out
    assert "EURUSD_COPY_demo" in output
    assert "=== Symbols Catalog (1 items) ===" in output
    original = service.get("EURUSD_demo")["data"]
    copy = service.get("EURUSD_COPY_demo")["data"]
    assert copy == {**original, "name": "EURUSD_COPY_demo"}
    assert cli.main(command) == 1
    assert '"code": "conflict"' in capsys.readouterr().out
    assert cli.main([*command[:-1], "EURUSD", "--new-datasource", "other"]) == 0
    capsys.readouterr()
    assert service.get("EURUSD_other")["success"]
    assert service.get("EURUSD_demo")["data"] == original


def test_cli_clone_missing_source(temp_db, capsys, monkeypatch):
    from app import cli

    monkeypatch.setattr(cli, "shutdown_logging", lambda: None)
    assert cli.main(["data-manager", "symbol", "clone", "MISSING", "COPY"]) == 1
    assert '"code": "not_found"' in capsys.readouterr().out
    assert temp_db.read_records("datamgr_symbols")["data"]["records"] == []


@pytest.mark.parametrize(
    "arguments", [[], ["EURUSD_demo"], ["EURUSD_demo", "COPY", "EXTRA"]]
)
def test_cli_clone_invalid_arguments(temp_db, monkeypatch, arguments):
    from app import cli

    monkeypatch.setattr(cli, "shutdown_logging", lambda: None)
    with pytest.raises(SystemExit) as error:
        cli.main(["data-manager", "symbol", "clone", *arguments])
    assert error.value.code == 2
    assert temp_db.read_records("datamgr_symbols")["data"]["records"] == []


def test_symbols_clone(temp_db) -> None:
    svc = Symbols()
    svc.add(
        name="EURUSD",
        datasource="dukascopy",
        description="Euro vs US Dollar",
        default_spread=1.2,
        swap_long=-5.0,
    )

    clone_res = svc.clone("EURUSD_dukascopy", "EURUSD_COPY")
    assert clone_res["success"] is True
    assert clone_res["metadata"]["operation"] == "symbols.clone"
    cloned_data = clone_res["data"]
    assert cloned_data["name"] == "EURUSD_COPY_dukascopy"
    assert cloned_data["description"] == "Euro vs US Dollar"
    assert cloned_data["spread"]["default"] == 1.2
    assert cloned_data["swap"]["long"] == -5.0

    # Test cloning with datasource override
    clone_diff_ds = svc.clone(
        "EURUSD_dukascopy", "EURUSD", new_datasource="pepperstone"
    )
    assert clone_diff_ds["success"] is True
    assert clone_diff_ds["data"]["name"] == "EURUSD_pepperstone"


def test_symbols_clone_failures(temp_db) -> None:
    svc = Symbols()
    res_nf = svc.clone("NONEXISTENT", "NEW_SYM")
    assert res_nf["success"] is False
    assert res_nf["error"]["code"] == "not_found"

    res_empty = svc.clone("", "")
    assert res_empty["success"] is False
    assert res_empty["error"]["code"] == "validation"


def test_symbols_save_and_load(temp_db, tmp_path) -> None:
    svc = Symbols()
    svc.add(
        name="USDCHF",
        datasource="brokerX",
        description="Dollar vs Franc",
        default_spread=1.4,
        swap_long=2.1,
    )
    svc.add(
        name="USDCAD",
        datasource="brokerX",
        description="Dollar vs Loonie",
        default_spread=1.6,
        swap_long=-1.2,
    )

    csv_path = tmp_path / "saved_symbols.csv"

    # Save
    save_res = svc.save(["USDCHF_brokerX", "USDCAD_brokerX"], csv_path)
    assert save_res["success"] is True
    assert save_res["metadata"]["operation"] == "symbols.save"
    assert save_res["data"]["count"] == 2
    assert csv_path.is_file()

    # Delete existing symbols so load can re-add them
    svc.delete(["USDCHF_brokerX", "USDCAD_brokerX"])
    assert svc.get("USDCHF_brokerX")["success"] is False

    # Load
    load_res = svc.load(csv_path)
    assert load_res["success"] is True
    assert load_res["metadata"]["operation"] == "symbols.load"
    assert len(load_res["data"]["loaded"]) == 2

    # Verify loaded symbols in database
    get_chf = svc.get("USDCHF_brokerX")
    assert get_chf["success"] is True
    assert get_chf["data"]["description"] == "Dollar vs Franc"
    assert get_chf["data"]["spread"]["default"] == 1.4


def test_cli_save_full_catalog_over_1000_rows(temp_db, tmp_path, capsys, monkeypatch):
    import csv

    from app import cli

    monkeypatch.setattr(cli, "shutdown_logging", lambda: None)
    service = Symbols()
    assert service.add(name="BASE", datasource="demo", commission=7)["success"]
    template = temp_db.read_records("datamgr_symbols")["data"]["records"][0]
    template.pop("id")
    rows = [{**template, "name": f"TEST{i:04d}_demo"} for i in range(1000)]
    assert temp_db.create_records("datamgr_symbols", rows)["success"]
    path = tmp_path / "new folder" / "all symbols.csv"
    assert cli.main(["data-manager", "symbol", "save", str(path)]) == 0
    output = capsys.readouterr().out
    assert "Saved 1001 symbol(s)" in output
    assert str(path) in output
    with path.open(encoding="utf-8-sig", newline="") as stream:
        exported = list(csv.DictReader(stream))
    assert len(exported) == 1001
    assert {row["name"] for row in exported} == {
        "BASE_demo",
        *(row["name"] for row in rows),
    }
    assert all(float(row["commission"]) == 7 for row in exported)


def test_cli_save_errors(temp_db, tmp_path, capsys, monkeypatch):
    from app import cli

    monkeypatch.setattr(cli, "shutdown_logging", lambda: None)
    path = tmp_path / "empty.csv"
    assert cli.main(["data-manager", "symbol", "save", str(path)]) == 1
    assert '"success": false' in capsys.readouterr().out
    assert not path.exists()
    assert Symbols().add(name="EURUSD", datasource="demo")["success"]
    assert cli.main(["data-manager", "symbol", "save", str(tmp_path)]) == 1
    assert '"success": false' in capsys.readouterr().out
    with pytest.raises(SystemExit) as error:
        cli.main(["data-manager", "symbol", "save"])
    assert error.value.code == 2


def test_symbols_save_failures(temp_db, tmp_path) -> None:
    svc = Symbols()
    res_empty = svc.save([], tmp_path / "empty.csv")
    assert res_empty["success"] is False
    assert res_empty["error"]["code"] == "validation"

    res_not_found = svc.save(["NONEXISTENT"], tmp_path / "out.csv")
    assert res_not_found["success"] is False
    assert res_not_found["error"]["code"] == "not_found"


def test_cli_load_csv_with_skipped_rows(temp_db, tmp_path, capsys, monkeypatch):
    from app import cli

    monkeypatch.setattr(cli, "shutdown_logging", lambda: None)
    path = tmp_path / "symbol imports.csv"
    path.write_text(
        "name,datasource,description,commission\n"
        "EURUSD,demo,Euro vs Dollar,7\n"
        "GBPUSD,demo,Pound vs Dollar,5\n"
        "EURUSD,demo,Duplicate,0\n"
        "USDJPY,demo,Invalid,not-a-number\n",
        encoding="utf-8-sig",
    )
    assert cli.main(["data-manager", "symbol", "load", str(path)]) == 0
    output = capsys.readouterr().out
    assert "Loaded 2 symbol(s)" in output
    assert "(2 skipped)" in output
    assert "EURUSD_demo" in output
    assert "GBPUSD_demo" in output
    assert "Skipped row 3:" in output
    assert "Skipped row 4:" in output
    assert Symbols().get("EURUSD_demo")["data"]["commission"] == 7
    assert Symbols().get("GBPUSD_demo")["data"]["commission"] == 5
    assert not Symbols().get("USDJPY_demo")["success"]
    assert cli.main(["data-manager", "symbol", "load", str(path)]) == 1
    assert '"success": false' in capsys.readouterr().out


@pytest.mark.parametrize(
    "contents",
    [None, "name,datasource\n", "name,datasource,commission\nEURUSD,demo,invalid\n"],
)
def test_cli_load_failures(temp_db, tmp_path, capsys, monkeypatch, contents):
    from app import cli

    monkeypatch.setattr(cli, "shutdown_logging", lambda: None)
    path = tmp_path / "symbols.csv"
    if contents is not None:
        path.write_text(contents, encoding="utf-8")
    assert cli.main(["data-manager", "symbol", "load", str(path)]) == 1
    assert '"success": false' in capsys.readouterr().out
    assert temp_db.read_records("datamgr_symbols")["data"]["records"] == []


def test_cli_load_requires_path(temp_db, monkeypatch):
    from app import cli

    monkeypatch.setattr(cli, "shutdown_logging", lambda: None)
    with pytest.raises(SystemExit) as error:
        cli.main(["data-manager", "symbol", "load"])
    assert error.value.code == 2


def test_symbols_load_failures(temp_db, tmp_path) -> None:
    svc = Symbols()
    res_no_file = svc.load(tmp_path / "does_not_exist.csv")
    assert res_no_file["success"] is False
    assert res_no_file["error"]["code"] == "not_found"

    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("", encoding="utf-8")
    res_empty_file = svc.load(empty_csv)
    assert res_empty_file["success"] is False
    assert res_empty_file["error"]["code"] == "validation"
