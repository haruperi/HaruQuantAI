"""Unit tests verifying 100% SQX parity for DataManagerBroker.

Key Capabilities Verified:
    - FR-DATA-BROKER-PROFILES: CRUD operations, SQX schema compliance, system profiles.
    - FR-DATA-BROKER-DEPENDENCIES: Preventing deletion when instruments reference broker.
    - FR-DATA-BROKER-STOCKS: Stock ticker configuration, list, edit, CSV import/export.
    - FR-DATA-BROKER-XML-INTERCHANGE: StrategyQuant X <Brokers><Broker>... XML import/export.
    - FR-DATA-BROKER-METATRADER-XML: MT5/MT4 symbols/sessions XML inspection and records import.
    - FR-DATA-BROKER-DATA-UPDATE: Historical data update dispatching.
    - FR-DATA-BROKER-INTEGRATION: FastAPI REST endpoints for all broker operations.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
from app.host.persistence import DatabaseManager
from app.host.resources import ResourceManager
from app.workspace.data_manager.broker import (
    BrokerSavePayload,
    BrokerService,
)
from app.workspace.data_manager.instruments import (
    InstrumentDefinition,
    InstrumentService,
)
from app.workspace.data_manager.routes import create_data_router
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def test_db(tmp_path: Path) -> DatabaseManager:
    """Fixture providing an isolated SQLite database."""
    db_file = tmp_path / "test_broker_parity.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()
    InstrumentService(db).ensure_defaults()
    return db


@pytest.fixture
def broker_service(test_db: DatabaseManager) -> BrokerService:
    """Fixture providing BrokerService backed by isolated test DB."""
    service = BrokerService(test_db)
    service.ensure_defaults()
    return service


def test_system_brokers_seeded_and_immutable(
    broker_service: BrokerService, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify default 11 SQX broker profiles are seeded and protected from deletion."""
    caplog.set_level(logging.INFO)
    profiles = broker_service.list_brokers()
    assert len(profiles) >= 11

    names = {p.name for p in profiles}
    expected_defaults = {
        "[[XTB]]",
        "[[RoboForex]]",
        "[[Dukascopy]]",
        "[[Darwinex]]",
        "[[ICMarkets]]",
        "[[Pepperstone]]",
        "[[OANDA]]",
        "[[FTMO]]",
        "[[The5ers]]",
        "[[Monevis]]",
        "[[Darwinex Zero]]",
    }
    for expected in expected_defaults:
        assert expected in names

    duk = next(p for p in profiles if p.name == "[[Dukascopy]]")
    assert duk.is_system is True
    assert duk.server_timezone == "EETUS"
    assert duk.postfix == "_dukascopy"
    assert duk.mt_use is True

    # System broker cannot be deleted
    with pytest.raises(ValueError, match="Cannot delete system broker profile"):
        broker_service.delete_brokers([duk.id])

    assert any(
        "FR-DATA-CATALOG-BROKER-PROFILES" in rec.message for rec in caplog.records
    )


def test_broker_crud_lifecycle(
    broker_service: BrokerService, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify broker profile creation, retrieval, update, and deletion."""
    caplog.set_level(logging.INFO)

    payload = BrokerSavePayload(
        name="Custom Alpha Broker",
        desc="Proprietary execution feed",
        postfix="_alpha",
        mt_timezone="UTC+3",
        mt_use=True,
        stockpicker_use=True,
    )

    created = broker_service.create_broker(payload)
    assert created.id > 0
    assert created.name == "Custom Alpha Broker"
    assert created.description == "Proprietary execution feed"
    assert created.postfix == "_alpha"
    assert created.server_timezone == "UTC+3"
    assert created.stockpicker_use is True
    assert created.mt_use is True

    # Retrieve by ID
    retrieved = broker_service.get_broker(created.id)
    assert retrieved is not None
    assert retrieved.name == "Custom Alpha Broker"
    assert retrieved.description == "Proprietary execution feed"

    # Duplicate name should raise ValueError
    with pytest.raises(ValueError, match="already exists"):
        broker_service.create_broker(payload)

    # Update profile
    update_payload = BrokerSavePayload(
        id=created.id,
        name="Custom Alpha Broker Updated",
        desc="Updated execution feed",
        postfix="_alpha_upd",
        mt_timezone="America/New_York",
        mt_use=False,
        stockpicker_use=False,
    )
    updated = broker_service.update_broker(created.id, update_payload)
    assert updated.name == "Custom Alpha Broker Updated"
    assert updated.description == "Updated execution feed"
    assert updated.postfix == "_alpha_upd"
    assert updated.server_timezone == "America/New_York"
    assert updated.stockpicker_use is False

    # Delete custom profile
    deleted_count = broker_service.delete_brokers([created.id])
    assert deleted_count == 1

    assert broker_service.get_broker(created.id) is None


def test_broker_deletion_blocked_by_instrument_dependency(
    test_db: DatabaseManager, broker_service: BrokerService
) -> None:
    """Verify that deleting a broker referenced by an instrument is safely blocked."""
    payload = BrokerSavePayload(
        name="Dependent Prime",
        desc="Broker with instrument dependency",
    )
    created = broker_service.create_broker(payload)

    # Create an instrument linked to this broker
    instrument_service = InstrumentService(test_db)
    inst_record = InstrumentDefinition(
        symbol="EURUSD_DEP",
        description="Euro vs US Dollar dependent",
        connection=created.name,
        broker_id=created.id,
    )
    instrument_service.create_instrument(inst_record)

    # Attempt to delete broker should fail due to reference
    with pytest.raises(
        ValueError,
        match="Cannot delete broker profile 'Dependent Prime' because 1 instruments reference it",
    ):
        broker_service.delete_brokers([created.id])

    # Delete referencing instrument
    instrument_service.delete_instrument("EURUSD_DEP")

    # Now deletion must succeed
    count = broker_service.delete_brokers([created.id])
    assert count == 1


def test_broker_stocks_management_and_csv_interchange(
    broker_service: BrokerService, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify managing configured stock symbols, duplicate deduplication, and CSV export/import."""
    caplog.set_level(logging.INFO)

    payload = BrokerSavePayload(name="Equities Broker", stockpicker_use=True)
    created = broker_service.create_broker(payload)
    broker_id = created.id

    # Initially empty stocks
    assert broker_service.list_stocks(broker_id) == []

    # Edit stocks directly with mixed case and duplicates
    broker_service.edit_stocks(broker_id, ["aapl", "MSFT", "tsla", "AAPL", " "])
    stocks = broker_service.list_stocks(broker_id)
    assert stocks == ["AAPL", "MSFT", "TSLA"]

    # Verify counts in profile record
    profile = broker_service.get_broker(broker_id)
    assert profile is not None
    assert profile.customized_stocks == 3

    # Export stocks to CSV
    csv_out = broker_service.export_stocks_csv(broker_id)
    assert csv_out == "AAPL\nMSFT\nTSLA\n"

    # Import stocks from CSV text
    new_csv = "NVDA\nGOOGL\nAMZN\n# comment\nAAPL\n"
    imported_count = broker_service.import_stocks_csv(broker_id, new_csv)
    assert imported_count == 4

    updated_stocks = broker_service.list_stocks(broker_id)
    assert updated_stocks == ["AAPL", "AMZN", "GOOGL", "NVDA"]


def test_broker_xml_export_and_import(
    broker_service: BrokerService, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify exporting and importing SQX canonical <Brokers><Broker>... XML."""
    caplog.set_level(logging.INFO)

    # Create profile with stocks
    b1 = broker_service.create_broker(
        BrokerSavePayload(
            name="XML Broker A",
            desc="XML Export Test Broker",
            mt_timezone="UTC+1",
            postfix="_a",
            stockpicker_use=True,
        )
    )
    broker_service.edit_stocks(b1.id, ["AAPL", "MSFT"])

    # Export XML
    xml_data = broker_service.export_brokers_xml([b1.id])
    assert "<Brokers>" in xml_data
    assert '<Broker name="XML Broker A"' in xml_data
    assert '<Stock ticker="AAPL"' in xml_data
    assert '<Stock ticker="MSFT"' in xml_data

    # Test importing a clean SQX-formatted XML string
    import_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Brokers>
    <Broker name="Imported Broker B" description="Imported from SQX" timezone="UTC+2"
            postfix="_b" mtUse="true" stockpickerUse="true">
        <Stocks>
            <Stock name="TSLA"/>
            <Stock name="NVDA"/>
        </Stocks>
    </Broker>
</Brokers>
"""
    imported = broker_service.import_brokers_xml(import_xml)
    assert len(imported) == 1
    assert imported[0].name == "Imported Broker B"
    assert imported[0].server_timezone == "UTC+2"
    assert imported[0].stockpicker_use is True

    # Check imported stocks
    b_stocks = broker_service.list_stocks(imported[0].id)
    assert b_stocks == ["NVDA", "TSLA"]


def test_metatrader_xml_inspection_and_import(
    test_db: DatabaseManager, broker_service: BrokerService
) -> None:
    """Verify parsing and importing MetaTrader export XML files."""
    broker = broker_service.create_broker(
        BrokerSavePayload(name="MetaTrader XML Target", mt_timezone="UTC+2")
    )

    mt_symbols_xml = """<?xml version="1.0" encoding="UTF-8"?>
<symbols>
    <symbol name="EURUSD_RAW" description="Euro vs US Dollar" type="Forex"
            tickSize="0.00001" tickValue="1.0" point="0.00001" digits="5"
            currency="EUR" marginCurrency="EUR" spread="10"/>
    <symbol name="GBPUSD_RAW" description="Great Britain Pound vs US Dollar" type="Forex"
            tickSize="0.00001" tickValue="1.0" point="0.00001" digits="5"
            currency="GBP" marginCurrency="GBP" spread="15"/>
</symbols>
"""

    # 1. Inspect instruments overview
    items = broker_service.inspect_xml_overview(mt_symbols_xml, "instrument")
    assert len(items) == 2
    assert items[0].name == "EURUSD_RAW"
    assert items[1].name == "GBPUSD_RAW"

    # 2. Import selected instruments
    imported_count = broker_service.import_xml_records(
        xml_content=mt_symbols_xml,
        kind="instrument",
        broker_id=broker.id,
        postfix="_test",
        selected_names=["EURUSD_RAW"],
    )
    assert imported_count == 1

    inst = test_db.instruments.get_by_symbol("EURUSD_RAW_TEST")
    assert inst is not None
    assert inst["broker_id"] == broker.id
    assert inst["data_type"] == "Forex"

    # 3. Sessions XML inspection and import
    mt_sessions_xml = """<?xml version="1.0" encoding="UTF-8"?>
<sessions>
    <session symbol="EURUSD_RAW" day="1" open="00:00" close="23:59"/>
    <session symbol="GBPUSD_RAW" day="1" open="00:00" close="23:59"/>
</sessions>
"""
    session_items = broker_service.inspect_xml_overview(mt_sessions_xml, "session")
    assert len(session_items) == 2

    imported_sessions = broker_service.import_xml_records(
        xml_content=mt_sessions_xml,
        kind="session",
        broker_id=broker.id,
        postfix="",
        selected_names=["EURUSD_RAW"],
    )
    assert imported_sessions == 1
    stored_session = test_db.sessions.get_by_name("EURUSD_RAW")
    assert stored_session is not None


def test_broker_fastapi_routes(test_db: DatabaseManager, tmp_path: Path) -> None:
    """Verify all 12 FastAPI REST endpoints for broker profiles and stocks."""
    app = FastAPI()
    res_mgr = ResourceManager(root_dir=tmp_path / "resources")
    router = create_data_router(db_manager=test_db, resource_manager=res_mgr)
    app.include_router(router)
    client = TestClient(app)

    # 1. List brokers
    resp = client.get("/data/brokers")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 11

    # 2. Create broker via POST
    create_body = {
        "name": "API Broker Profile",
        "desc": "Created via REST API",
        "mt_timezone": "UTC+3",
        "postfix": "_api",
        "mt_use": True,
        "stockpicker_use": True,
    }
    resp = client.post("/data/brokers", json=create_body)
    assert resp.status_code == 200
    created_id = resp.json()["data"]["id"]
    assert created_id > 0
    assert resp.json()["data"]["name"] == "API Broker Profile"
    assert resp.json()["data"]["server_timezone"] == "UTC+3"

    # 3. Update broker via PUT
    update_body = {
        "name": "API Broker Profile Updated",
        "desc": "Updated via REST API",
        "mt_timezone": "UTC+2",
        "postfix": "_api_upd",
        "mt_use": True,
        "stockpicker_use": True,
    }
    resp = client.put(f"/data/brokers/{created_id}", json=update_body)
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "API Broker Profile Updated"
    assert resp.json()["data"]["server_timezone"] == "UTC+2"

    # 4. List broker stocks
    resp = client.get(f"/data/brokers/{created_id}/stocks")
    assert resp.status_code == 200
    assert resp.json()["data"]["stocks"] == []

    # 5. Edit broker stocks
    edit_stocks_body = {"stocks": ["AAPL", "MSFT", "TSLA"]}
    resp = client.put(f"/data/brokers/{created_id}/stocks", json=edit_stocks_body)
    assert resp.status_code == 200
    assert resp.json()["data"]["count"] == 3

    # 6. Export stocks CSV
    resp = client.get(f"/data/brokers/{created_id}/stocks/export")
    assert resp.status_code == 200
    assert "AAPL\nMSFT\nTSLA" in resp.text

    # 7. Import stocks CSV
    import_stocks_body = {"content": "NVDA\nAMZN\nAAPL\n"}
    resp = client.post(
        f"/data/brokers/{created_id}/stocks/import", json=import_stocks_body
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["count"] == 3

    # 8. Export brokers XML
    export_xml_body = {"broker_ids": [created_id]}
    resp = client.post("/data/brokers/save-xml", json=export_xml_body)
    assert resp.status_code == 200
    assert "<Brokers>" in resp.text
    assert "API Broker Profile Updated" in resp.text
    exported_xml = resp.text

    # 9. Import brokers XML
    import_xml_body = {
        "xml_content": exported_xml.replace(
            "API Broker Profile Updated", "Imported Clone Broker"
        )
    }
    resp = client.post("/data/brokers/load-xml", json=import_xml_body)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1
    clone_id = resp.json()["data"][0]["id"]

    # 10. Update broker data trigger
    resp = client.post(f"/data/brokers/{created_id}/update-data")
    assert resp.status_code == 200
    assert resp.json()["data"]["broker_id"] == created_id

    # 11. Inspect XML overview
    inspect_body = {
        "xml_content": """<symbols><symbol name="TEST_PAIR"/></symbols>""",
        "kind": "instrument",
    }
    resp = client.post("/data/brokers/import-get-overview", json=inspect_body)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1

    # 12. Delete brokers
    delete_body = {"broker_ids": [created_id, clone_id]}
    resp = client.post("/data/brokers/delete", json=delete_body)
    assert resp.status_code == 200
    assert resp.json()["data"]["deleted_count"] == 2


def test_broker_persistence_timestamps(test_db: DatabaseManager) -> None:
    """Verify created_at_utc and updated_at_utc are properly populated and updated."""
    # 1. System defaults have timestamps
    test_db.brokers.ensure_defaults()
    for row in test_db.brokers.list_profiles():
        assert "created_at_utc" in row
        assert row["created_at_utc"]
        assert "updated_at_utc" in row
        assert row["updated_at_utc"]

    # 2. Created profile populates created_at_utc and updated_at_utc
    b_id = test_db.brokers.create_profile(
        {
            "name": "Timestamp Verification Broker",
            "description": "Checks timestamp lifecycle",
        }
    )
    rec = test_db.brokers.get_profile(b_id)
    assert rec is not None
    created_at = rec["created_at_utc"]
    updated_at = rec["updated_at_utc"]
    assert created_at
    assert updated_at

    # 3. Update profile changes updated_at_utc
    test_db.brokers.update_profile(
        b_id,
        {
            "name": "Timestamp Verification Broker Updated",
            "description": "Updated timestamp lifecycle",
        },
    )
    updated_rec = test_db.brokers.get_profile(b_id)
    assert updated_rec is not None
    assert updated_rec["created_at_utc"] == created_at
    assert updated_rec["updated_at_utc"] >= updated_at

    # Cleanup
    test_db.brokers.delete_profile(b_id)


def test_broker_profile_stocks_populated(
    broker_service: BrokerService,
) -> None:
    """Verify broker profile record populates constituent stocks from datamgr_broker_stock."""
    created = broker_service.create_broker(
        BrokerSavePayload(name="Stock Test Broker", stockpicker_use=True)
    )
    broker_service.edit_stocks(created.id, ["AAPL", "MSFT", "TSLA"])
    profiles = {p.id: p for p in broker_service.list_brokers()}
    assert profiles[created.id].customized_stocks == 3
    assert profiles[created.id].stocks == ["AAPL", "MSFT", "TSLA"]

    p1 = broker_service.get_broker(created.id)
    assert p1 is not None
    assert p1.stocks == ["AAPL", "MSFT", "TSLA"]
