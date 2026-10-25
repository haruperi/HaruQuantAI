"""Unit tests for Symbols service CRUD, cloning, and CSV import/export commands."""

from __future__ import annotations

import sqlite3
from unittest.mock import patch

import pytest
from app.host.persistence import HostPersistence
from app.workspace.data_manager.symbols import Symbols


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


def test_symbols_save_failures(temp_db, tmp_path) -> None:
    svc = Symbols()
    res_empty = svc.save([], tmp_path / "empty.csv")
    assert res_empty["success"] is False
    assert res_empty["error"]["code"] == "validation"

    res_not_found = svc.save(["NONEXISTENT"], tmp_path / "out.csv")
    assert res_not_found["success"] is False
    assert res_not_found["error"]["code"] == "not_found"


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
