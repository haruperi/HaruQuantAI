"""
Description:
    Unit tests for InstrumentService and CatalogService validating Phase 2 Task 2.1.
    Tests instrument definition CRUD, dataset catalog persistence, series discovery,
    availability evaluation, and broker profile queries.

Purpose:
    FEAT-DATA-CATALOG, FEAT-DATA-INSTRUMENTS

Key Capabilities:
    FR-DATA-INSTRUMENTS-CRUD: Validates instrument persistence and lifecycle.
    FR-DATA-CATALOG-DATASET-REGISTRY: Validates dataset registry persistence and lookup.
    FR-DATA-CATALOG-SERIES-DISCOVERY: Validates series availability discrimination.
    FR-DATA-CATALOG-BROKER-PROFILES: Validates broker profile queries.

Python API Usage:
    Run via pytest:
    `pytest tests/unit/v2/phase_02/test_catalog.py -v --no-cov`
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
from app.host.persistence import DatabaseManager
from app.plugins.data.catalog import CatalogService, DatasetRecord
from app.plugins.data.instruments import InstrumentDefinition, InstrumentService


@pytest.fixture
def test_db(tmp_path: Path) -> DatabaseManager:
    """Fixture providing an isolated in-memory or temporary SQLite database."""
    db_file = tmp_path / "test_data.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()
    return db


def test_instrument_crud(
    test_db: DatabaseManager, caplog: pytest.LogCaptureFixture
) -> None:
    """Validate full instrument definition lifecycle via InstrumentService."""
    caplog.set_level(logging.DEBUG)
    service = InstrumentService(test_db)

    # Initial state contains baseline seeds
    assert service.count_instruments() == 3
    initial_symbols = [inst.symbol for inst in service.list_instruments()]
    assert "EURUSD" in initial_symbols
    assert "USDJPY" in initial_symbols
    assert service.get_instrument("AUDUSD") is None

    # Create / Save
    audusd = InstrumentDefinition(
        symbol="AUDUSD",
        connection="Direct",
        broker_id=1,
        description="Australian Dollar spot",
        tick_size=0.0001,
        tick_step=0.0001,
        tick_value_in_money=1.0,
        point_value=100000.0,
        decimals=4,
        default_spread=1.2,
        default_slippage=0.5,
        min_volume=0.01,
        max_volume=100.0,
        lot_step=0.01,
        margin_rate=0.033,
        swap_long=-5.4,
        swap_short=1.2,
        swap_3day_day=3,
        commissions="3.5",
        data_type="Forex",
        exchange="FXCM",
        country="AU",
        sector="Currencies",
    )
    service.save_instrument(audusd)

    # FR log verification
    assert any(
        "FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD" in rec.message for rec in caplog.records
    )

    # Read
    assert service.count_instruments() == 4
    retrieved = service.get_instrument("AUDUSD")
    assert retrieved is not None
    assert retrieved.symbol == "AUDUSD"
    assert retrieved.tick_size == 0.0001
    assert retrieved.decimals == 4
    assert retrieved.data_type == "Forex"

    # List
    all_insts = service.list_instruments()
    assert len(all_insts) == 4
    assert any(i.symbol == "AUDUSD" for i in all_insts)

    # Update
    updated_audusd = retrieved.model_copy(update={"default_spread": 0.8})
    service.save_instrument(updated_audusd)
    retrieved2 = service.get_instrument("AUDUSD")
    assert retrieved2 is not None
    assert retrieved2.default_spread == 0.8

    # Delete
    deleted = service.delete_instrument("AUDUSD")
    assert deleted is True
    assert service.count_instruments() == 3
    assert service.get_instrument("AUDUSD") is None

    # Delete nonexistent returns False
    assert service.delete_instrument("NONEXISTENT") is False


def test_instrument_validation(test_db: DatabaseManager) -> None:
    """Validate InstrumentDefinition input validation rules."""
    # Invalid symbol: empty
    with pytest.raises(ValueError, match="Instrument symbol cannot be empty"):
        InstrumentDefinition(symbol="   ")

    # Invalid tick_size: <= 0
    with pytest.raises(ValueError, match="greater than 0"):
        InstrumentDefinition(symbol="AAPL", tick_size=0.0)

    # Invalid decimals: negative
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        InstrumentDefinition(symbol="AAPL", decimals=-1)

    # Invalid min_volume: <= 0
    with pytest.raises(ValueError, match="greater than 0"):
        InstrumentDefinition(symbol="AAPL", min_volume=-0.1)


def test_catalog_dataset_lifecycle(
    test_db: DatabaseManager, caplog: pytest.LogCaptureFixture
) -> None:
    """Validate dataset registration, query, filtering, and deletion."""
    caplog.set_level(logging.DEBUG)
    catalog = CatalogService(test_db)

    assert catalog.count_datasets() == 0

    d1 = DatasetRecord(
        id="ds_eurusd_m1",
        symbol="EURUSD",
        timeframe="M1",
        source="Dukascopy",
        bars=150000,
        date_from="2020-01-01T00:00:00Z",
        date_to="2020-12-31T23:59:00Z",
    )
    d2 = DatasetRecord(
        id="ds_gbpusd_m5",
        symbol="GBPUSD",
        timeframe="M5",
        source="Darwinex",
        bars=30000,
    )
    catalog.save_dataset(d1)
    catalog.save_dataset(d2)

    assert catalog.count_datasets() == 2

    # FR log verification
    assert any(
        "FR-DATA-CATALOG-DATASET-REGISTRY" in rec.message for rec in caplog.records
    )

    # Get by ID
    got1 = catalog.get_dataset("ds_eurusd_m1")
    assert got1 is not None
    assert got1.symbol == "EURUSD"
    assert got1.bars == 150000

    assert catalog.get_dataset("unknown_id") is None

    # Filtered list
    dukascopy_list = catalog.list_datasets(source="Dukascopy")
    assert len(dukascopy_list) == 1
    assert dukascopy_list[0].id == "ds_eurusd_m1"

    gbp_list = catalog.list_datasets(symbol="GBPUSD")
    assert len(gbp_list) == 1
    assert gbp_list[0].id == "ds_gbpusd_m5"

    # Delete
    assert catalog.delete_dataset("ds_gbpusd_m5") is True
    assert catalog.count_datasets() == 1
    assert catalog.delete_dataset("ds_gbpusd_m5") is False


def test_catalog_series_availability(
    test_db: DatabaseManager, caplog: pytest.LogCaptureFixture
) -> None:
    """Validate check_availability distinguishes missing, empty, and available series."""
    caplog.set_level(logging.DEBUG)
    catalog = CatalogService(test_db)

    # 1. Missing series -> UNAVAILABLE
    avail, reason = catalog.check_availability("BTCUSD", "M1")
    assert avail is False
    assert reason == "UNAVAILABLE"

    # 2. Registered with 0 bars -> EMPTY_SERIES
    empty_ds = DatasetRecord(
        id="ds_btcusd_m1",
        symbol="BTCUSD",
        timeframe="M1",
        source="Binance",
        bars=0,
    )
    catalog.save_dataset(empty_ds)
    avail, reason = catalog.check_availability("BTCUSD", "M1")
    assert avail is False
    assert reason == "EMPTY_SERIES"

    # 3. Available series with bars > 0 -> AVAILABLE
    funded_ds = DatasetRecord(
        id="ds_btcusd_m1",
        symbol="BTCUSD",
        timeframe="M1",
        source="Binance",
        bars=5000,
    )
    catalog.save_dataset(funded_ds)
    avail, reason = catalog.check_availability("BTCUSD", "M1")
    assert avail is True
    assert reason == "AVAILABLE"

    assert any(
        "FR-DATA-CATALOG-SERIES-DISCOVERY" in rec.message for rec in caplog.records
    )


def test_catalog_broker_profiles(test_db: DatabaseManager) -> None:
    """Validate default broker profiles and querying."""
    catalog = CatalogService(test_db)
    brokers = catalog.list_brokers()
    assert len(brokers) >= 3

    names = {b.name for b in brokers}
    assert "Default" in names
    assert "Dukascopy" in names
    assert "Darwinex" in names

    b = catalog.get_broker("dukascopy")
    assert b is not None
    assert b.name == "Dukascopy"
    assert b.server_timezone == "UTC"

    assert catalog.get_broker("nonexistent_broker") is None


def test_resolve_alias(
    test_db: DatabaseManager, caplog: pytest.LogCaptureFixture
) -> None:
    """Validate instrument alias resolution logic and logging."""
    caplog.set_level(logging.DEBUG)
    service = InstrumentService(test_db)

    inst = InstrumentDefinition(
        symbol="EURUSD",
        alias="EUR/USD, EURUSD_SB, FX:EURUSD",
        description="Euro vs US Dollar",
    )
    service.save_instrument(inst)

    # Direct match
    assert service.resolve_alias("EURUSD") == "EURUSD"
    # Alias match
    assert service.resolve_alias("eur/usd") == "EURUSD"
    assert service.resolve_alias("EURUSD_SB") == "EURUSD"
    # Unknown symbol returned verbatim
    assert service.resolve_alias("UNKNOWN_SYM") == "UNKNOWN_SYM"

    assert any(
        "FR-DATA-INSTRUMENTS-ALIAS-RESOLUTION" in rec.message for rec in caplog.records
    )


def test_catalog_broker_profiles_from_db(test_db: DatabaseManager) -> None:
    """Validate reading broker profiles from existing datamgr_broker table."""
    with test_db.connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS datamgr_broker (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                is_system INTEGER DEFAULT 0,
                description TEXT DEFAULT '',
                server_timezone TEXT DEFAULT 'UTC',
                postfix TEXT DEFAULT '',
                enabled INTEGER DEFAULT 1,
                mt_use INTEGER DEFAULT 0,
                stockpicker_use INTEGER DEFAULT 0
            );
            """
        )
        conn.execute(
            """
            INSERT INTO datamgr_broker (id, name, server_timezone)
            VALUES (1, 'InteractiveBrokers', 'US/Eastern');
            """
        )

    catalog = CatalogService(test_db)
    brokers = catalog.list_brokers()
    assert len(brokers) == 1
    assert brokers[0].name == "InteractiveBrokers"
    assert brokers[0].server_timezone == "US/Eastern"
