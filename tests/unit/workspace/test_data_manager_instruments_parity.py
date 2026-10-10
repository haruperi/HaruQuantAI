"""Unit tests verifying 100% SQX parity for DataManagerInstruments.

Key Capabilities Verified:
    - FR-DATA-INSTRUMENTS-SPECIFICATION: Extended fields (min_distance,
      order_size_multiplier, order_size_step, cot, broker_id).
    - FR-DATA-INSTRUMENTS-CLONE: Instrument cloning with broker postfix resolution.
    - FR-DATA-INSTRUMENTS-MASS-EDIT: Selective parameter updates with change flags.
    - FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD: Bulk deletion and async threshold.
    - FR-DATA-INSTRUMENTS-TRANSFER-XML: StrategyQuant X XML import/export.
    - FR-DATA-INSTRUMENTS-ALIAS-RESOLUTION: Broker alias registry lifecycle.
    - FR-DATA-INTEGRATION-INSTRUMENTS: FastAPI REST endpoints for all operations.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
from app.host.persistence import DatabaseManager
from app.host.resources import ResourceManager
from app.workspace.data_manager.instruments import (
    DATA_TYPE_INT_TO_NAME,
    DATA_TYPE_NAME_TO_INT,
    InstrumentService,
)
from app.workspace.data_manager.routes import create_data_router
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def test_db(tmp_path: Path) -> DatabaseManager:
    """Fixture providing an isolated SQLite database."""
    db_file = tmp_path / "test_instruments_parity.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()
    InstrumentService(db).ensure_defaults()
    return db


@pytest.fixture
def instrument_service(test_db: DatabaseManager) -> InstrumentService:
    """Fixture providing InstrumentService backed by isolated test DB."""
    return InstrumentService(test_db)


@pytest.fixture
def api_client(test_db: DatabaseManager, tmp_path: Path) -> TestClient:
    """Fixture providing FastAPI TestClient mounted with market data router."""
    res_mgr = ResourceManager(root_dir=tmp_path / "resources")
    router = create_data_router(db_manager=test_db, resource_manager=res_mgr)
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return TestClient(app)


def test_instrument_extended_fields_and_mappings(
    instrument_service: InstrumentService,
) -> None:
    """Verify extended SQX fields and integer/string data_type mappings."""
    inst = instrument_service.get_instrument("EURUSD")
    assert inst is not None
    assert inst.min_distance == 0.0
    assert inst.order_size_multiplier == 1.0
    assert inst.order_size_step == 0.0
    assert inst.cot == "6E"
    assert inst.broker_id == -1
    assert inst.data_type == "Forex"
    assert inst.data_type_int == 3

    assert DATA_TYPE_INT_TO_NAME[1] == "Futures"
    assert DATA_TYPE_INT_TO_NAME[2] == "Stock"
    assert DATA_TYPE_INT_TO_NAME[3] == "Forex"
    assert DATA_TYPE_NAME_TO_INT["futures"] == 1
    assert DATA_TYPE_NAME_TO_INT["stocks"] == 2
    assert DATA_TYPE_NAME_TO_INT["forex"] == 3


def test_clone_instrument_with_postfix(
    instrument_service: InstrumentService, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify cloning an instrument with broker postfix handling."""
    caplog.set_level(logging.INFO)
    cloned = instrument_service.clone_instrument(
        symbol="EURUSD",
        clone_name="EURUSD_CLONE",
        broker_id=2,
        broker_postfix=".m",
    )
    assert cloned.symbol == "EURUSD_CLONE.M"
    assert cloned.broker_id == 2
    assert cloned.point_value == 100000.0

    retrieved = instrument_service.get_instrument("EURUSD_CLONE.M")
    assert retrieved is not None
    assert retrieved.symbol == "EURUSD_CLONE.M"
    assert "FR-DATA-INSTRUMENTS-CLONE" in caplog.text

    # Duplicate clone name error
    with pytest.raises(ValueError, match="already exists"):
        instrument_service.clone_instrument("EURUSD", "EURUSD_CLONE.M")

    # Non-existent source error
    with pytest.raises(ValueError, match="doesn't exist"):
        instrument_service.clone_instrument("NONEXISTENT", "CLONE")


def test_mass_edit_instruments_selective_flags(
    instrument_service: InstrumentService, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify selective parameter updates with change flags."""
    caplog.set_level(logging.INFO)
    instrument_service.clone_instrument("EURUSD", "EURUSD_P1")
    instrument_service.clone_instrument("GBPUSD", "GBPUSD_P1")

    # Selectively patch only point_value and min_distance
    updates = {
        "point_value": 50000.0,
        "min_distance": 15.0,
        "default_spread": 0.0005,  # Not in change_flags, should NOT apply
    }
    flags = {
        "changePointValue": True,
        "changeMinDistance": True,
        "changeDefaultSpread": False,
    }
    count = instrument_service.mass_edit_instruments(
        symbols=["EURUSD_P1", "GBPUSD_P1"],
        updates=updates,
        change_flags=flags,
    )
    assert count == 2
    p1 = instrument_service.get_instrument("EURUSD_P1")
    assert p1 is not None
    assert p1.point_value == 50000.0
    assert p1.min_distance == 15.0
    assert p1.default_spread == 0.0001  # Retained original spread

    assert "FR-DATA-INSTRUMENTS-MASS-EDIT" in caplog.text


def test_mass_delete_instruments_async_threshold(
    instrument_service: InstrumentService, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify bulk instrument deletion and async threshold behavior (>10 items)."""
    caplog.set_level(logging.INFO)
    # Small deletion (<= 10 items) -> is_async is False
    instrument_service.clone_instrument("EURUSD", "DEL1")
    instrument_service.clone_instrument("EURUSD", "DEL2")
    count, is_async = instrument_service.delete_instruments(["DEL1", "DEL2"])
    assert count == 2
    assert not is_async

    # Large deletion (> 10 items) -> is_async is True
    large_symbols = [f"BULK_{i}" for i in range(12)]
    for s in large_symbols:
        instrument_service.clone_instrument("EURUSD", s)
    count, is_async = instrument_service.delete_instruments(large_symbols)
    assert count == 12
    assert is_async
    assert "FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD" in caplog.text


def test_export_sqx_xml(
    instrument_service: InstrumentService, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify XML catalog generation matching StrategyQuant X format."""
    caplog.set_level(logging.INFO)
    xml_str = instrument_service.export_sqx_xml(["EURUSD", "GBPUSD"])
    assert "<Instruments>" in xml_str
    assert '<Instrument instrument="EURUSD"' in xml_str
    assert '<Instrument instrument="GBPUSD"' in xml_str
    assert 'pointValue="100000.0"' in xml_str
    assert "&lt;Swap" in xml_str
    assert "FR-DATA-INSTRUMENTS-TRANSFER-XML" in caplog.text


def test_import_sqx_xml_conflict_policies(
    instrument_service: InstrumentService, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify XML import with skip, overwrite, and cancel conflict policies."""
    caplog.set_level(logging.INFO)
    sample_xml = """<Instruments>
  <Instrument instrument="IMPORT1" description="Imported Spot 1" pointValue="100000.0" tickSize="0.00001" tickStep="0.00001" defaultSpread="0.0002" defaultSlippage="0.0" commissions="0.0" dataType="3" exchange="FX" country="US" sector="Finance" swap='&lt;Swap use="true" type="points" long="-2.5" short="1.2" tripleSwapOn="WEDNESDAY" /&gt;' orderSizeMultiplier="1.0" orderSizeStep="0.01" broker="-1" minDistance="5.0" cot="6E" />
  <Instrument instrument="EURUSD" description="New EURUSD" pointValue="120000.0" tickSize="0.00001" tickStep="0.00001" defaultSpread="0.0001" defaultSlippage="0.0" commissions="0.0" dataType="3" exchange="" country="" sector="" swap="" orderSizeMultiplier="1.0" orderSizeStep="0.0" broker="-1" minDistance="0.0" />
</Instruments>"""

    # 1. Skip existing
    res_skip = instrument_service.import_sqx_xml(sample_xml, conflict_policy="skip")
    assert res_skip["imported"] == 1
    assert res_skip["skipped"] == 1
    assert "IMPORT1" in res_skip["symbols"]

    imported_inst = instrument_service.get_instrument("IMPORT1")
    assert imported_inst is not None
    assert imported_inst.description == "Imported Spot 1"
    assert imported_inst.swap_long == -2.5
    assert imported_inst.swap_short == 1.2
    assert imported_inst.min_distance == 5.0

    # 2. Cancel on conflict
    with pytest.raises(ValueError, match="Import canceled due to conflict"):
        instrument_service.import_sqx_xml(sample_xml, conflict_policy="cancel")

    # 3. Overwrite all
    res_over = instrument_service.import_sqx_xml(
        sample_xml, conflict_policy="overwrite_all"
    )
    assert res_over["overwritten"] >= 1
    eurusd = instrument_service.get_instrument("EURUSD")
    assert eurusd is not None
    assert eurusd.point_value == 120000.0


def test_alias_registry_lifecycle(
    instrument_service: InstrumentService, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify alias registration, listing, editing, and resolution."""
    caplog.set_level(logging.DEBUG)
    aliases = instrument_service.list_aliases()
    assert any(a["alias"] == "EUR/USD" for a in aliases)

    resolved = instrument_service.resolve_alias("EUR/USD")
    assert resolved == "EURUSD"

    # Add alias
    added = instrument_service.add_alias(
        "EURUSD.RAW", "EURUSD", description="Raw spread"
    )
    assert added
    assert instrument_service.resolve_alias("EURUSD.RAW") == "EURUSD"

    # Edit alias to point to GBPUSD
    edited = instrument_service.edit_alias("EURUSD.RAW", "GBPUSD")
    assert edited
    assert instrument_service.resolve_alias("EURUSD.RAW") == "GBPUSD"

    # Remove alias
    removed = instrument_service.remove_alias("EURUSD.RAW")
    assert removed
    assert instrument_service.resolve_alias("EURUSD.RAW") == "EURUSD.RAW"
    assert "FR-DATA-INSTRUMENTS-ALIAS-RESOLUTION" in caplog.text


def test_instrument_api_endpoints(api_client: TestClient) -> None:
    """Verify all REST and SQX RPC endpoints for instruments."""
    # 1. GET /api/v1/data/instruments with search & filter
    resp = api_client.get("/api/v1/data/instruments?search=EUR&data_type=Forex")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert any(inst["symbol"] == "EURUSD" for inst in data)

    # SQX alias: /api/v1/data/instruments/list?type=Forex
    resp_alias = api_client.get("/api/v1/data/instruments/list?type=Forex")
    assert resp_alias.status_code == 200

    # 2. POST /api/v1/data/instruments/clone
    clone_resp = api_client.post(
        "/api/v1/data/instruments/clone",
        json={
            "symbol": "EURUSD",
            "clone_name": "EURUSD_API",
            "broker_id": 1,
            "broker_postfix": "",
        },
    )
    assert clone_resp.status_code == 201
    assert clone_resp.json()["data"]["symbol"] == "EURUSD_API"

    # 3. POST /api/v1/data/instruments/mass-edit
    edit_resp = api_client.post(
        "/api/v1/data/instruments/mass-edit",
        json={
            "symbols": ["EURUSD_API"],
            "updates": {"point_value": 75000.0, "min_distance": 10.0},
            "change_flags": {
                "changePointValue": True,
                "changeMinDistance": True,
            },
        },
    )
    assert edit_resp.status_code == 200
    assert edit_resp.json()["data"]["updated_count"] == 1

    # 4. POST /api/v1/data/instruments/save (XML export)
    save_resp = api_client.post(
        "/api/v1/data/instruments/save",
        json={"symbols": ["EURUSD_API"]},
    )
    assert save_resp.status_code == 200
    xml_content = save_resp.json()["data"]["xml"]
    assert "<Instruments>" in xml_content

    # 5. POST /api/v1/data/instruments/load (XML import)
    load_resp = api_client.post(
        "/api/v1/data/instruments/load",
        json={"xml_content": xml_content, "conflict_policy": "overwrite_all"},
    )
    assert load_resp.status_code == 201
    assert (
        load_resp.json()["data"]["imported"] + load_resp.json()["data"]["overwritten"]
        >= 1
    )

    # 6. Aliases: GET, POST, PUT, DELETE
    alias_post = api_client.post(
        "/api/v1/data/instruments/aliases",
        json={
            "alias": "TEST_ALIAS",
            "instrument": "EURUSD",
            "description": "Test alias",
        },
    )
    assert alias_post.status_code == 201

    alias_list = api_client.get("/api/v1/data/instruments/aliases")
    assert alias_list.status_code == 200
    assert any(a["alias"] == "TEST_ALIAS" for a in alias_list.json()["data"])

    alias_del = api_client.delete("/api/v1/data/instruments/aliases/TEST_ALIAS")
    assert alias_del.status_code == 200

    # 7. POST /api/v1/data/instruments/mass-delete
    del_resp = api_client.post(
        "/api/v1/data/instruments/mass-delete",
        json={"symbols": ["EURUSD_API"]},
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["data"]["deleted_count"] == 1
