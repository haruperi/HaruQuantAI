"""Unit tests for host catalog service and instrument lookup."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from app.host.catalog import (
    CatalogService,
    CommodityRecord,
    get_catalog_service,
    normalize_commodity_code,
)


def test_normalize_commodity_code() -> None:
    """Verify commodity code normalization and '@' stripping."""
    assert normalize_commodity_code("@ES") == "ES"
    assert normalize_commodity_code("@nq") == "NQ"
    assert normalize_commodity_code("CL") == "CL"
    assert normalize_commodity_code("  @gc  ") == "GC"


def test_catalog_service_live_db_commodity() -> None:
    """Verify live database commodity lookups if data/database/haruquantai.db exists."""
    catalog = get_catalog_service()
    if not catalog.db_path.exists():
        pytest.skip("haruquantai.db not present in test environment")

    # Look up @ES (E-mini S&P 500)
    es = catalog.get_commodity("@ES")
    assert es is not None
    assert isinstance(es, CommodityRecord)
    assert es.code == "ES"
    assert es.point_value == 50.0
    assert es.tick_size == 0.25

    # Look up NQ without @
    nq = catalog.get_commodity("NQ")
    assert nq is not None
    assert nq.code == "NQ"
    assert nq.point_value == 20.0
    assert nq.tick_size == 0.25

    # List commodities
    commodities = catalog.list_commodities()
    assert len(commodities) >= 100

    # Filter commodities
    filtered = catalog.list_commodities(filter_str="crude")
    assert len(filtered) >= 1
    assert any(c.code == "CL" for c in filtered)


def test_catalog_service_live_db_instrument() -> None:
    """Verify instrument lookup from live database."""
    catalog = get_catalog_service()
    if not catalog.db_path.exists():
        pytest.skip("haruquantai.db not present in test environment")

    eurusd = catalog.get_instrument("EURUSD")
    if eurusd is not None:
        assert eurusd.symbol == "EURUSD"
        assert eurusd.decimals == 5
        assert eurusd.point_value == 100000.0


def test_catalog_service_live_db_stock() -> None:
    """Verify stock ticker lookup from live database."""
    catalog = get_catalog_service()
    if not catalog.db_path.exists():
        pytest.skip("haruquantai.db not present in test environment")

    stock = catalog.get_stock("AAPL")
    if stock is not None:
        assert stock.ticker == "AAPL"


def test_catalog_service_missing_db_fallback(tmp_path: Path) -> None:
    """Verify CatalogService handles missing database file gracefully without exceptions."""
    non_existent = tmp_path / "non_existent.db"
    catalog = CatalogService(db_path=non_existent)

    assert catalog.get_commodity("@ES") is None
    assert catalog.list_commodities() == []
    assert catalog.get_instrument("EURUSD") is None
    assert catalog.list_instruments() == []
    assert catalog.get_stock("AAPL") is None
    assert catalog.list_stocks() == []


def test_catalog_service_custom_sqlite_fixture(tmp_path: Path) -> None:
    """Verify CatalogService against an isolated SQLite test database."""
    db_file = tmp_path / "test_catalog.db"
    conn = sqlite3.connect(db_file)
    with conn:
        conn.execute(
            """
            CREATE TABLE datamgr_commodities (
                id INTEGER PRIMARY KEY,
                code TEXT NOT NULL UNIQUE,
                name TEXT,
                point_value REAL,
                tick_step REAL,
                tick_size REAL,
                order_size_multi REAL,
                order_size_step REAL,
                exchange TEXT
            )
            """
        )
        conn.execute(
            """
            INSERT INTO datamgr_commodities
            (id, code, name, point_value, tick_step, tick_size, order_size_multi, order_size_step, exchange)
            VALUES (1, 'ES', 'E-Mini S&P 500', 50.0, 0.25, 0.25, 1.0, 0.0, 'CME')
            """
        )
        conn.execute(
            """
            CREATE TABLE datamgr_instruments (
                id INTEGER PRIMARY KEY,
                symbol TEXT NOT NULL UNIQUE,
                description TEXT,
                tick_size REAL,
                tick_step REAL,
                tick_value_in_money REAL,
                point_value REAL,
                decimals INTEGER,
                default_spread REAL,
                data_type TEXT,
                exchange TEXT
            )
            """
        )
        conn.execute(
            """
            INSERT INTO datamgr_instruments
            (id, symbol, description, tick_size, tick_step, tick_value_in_money, point_value, decimals, default_spread, data_type, exchange)
            VALUES (1, 'EURUSD', 'Euro / US Dollar', 0.00001, 0.00001, 10.0, 100000.0, 5, 0.0001, 'Forex', '')
            """
        )
        conn.execute(
            """
            CREATE TABLE datamgr_stock (
                ID INTEGER PRIMARY KEY,
                TICKER TEXT NOT NULL UNIQUE,
                BASKET_ID INTEGER,
                DATE_FROM TEXT,
                DATE_TO TEXT
            )
            """
        )
        conn.execute(
            """
            INSERT INTO datamgr_stock (ID, TICKER, BASKET_ID, DATE_FROM, DATE_TO)
            VALUES (1, 'AAPL', 10, '2020-01-01', '2026-01-01')
            """
        )
    conn.close()

    service = CatalogService(db_path=db_file)

    # Commodity
    comm = service.get_commodity("@ES")
    assert comm is not None
    assert comm.code == "ES"
    assert comm.name == "E-Mini S&P 500"
    assert comm.point_value == 50.0
    assert comm.tick_size == 0.25
    assert comm.exchange == "CME"

    # Instrument
    inst = service.get_instrument("EURUSD")
    assert inst is not None
    assert inst.symbol == "EURUSD"
    assert inst.decimals == 5
    assert inst.point_value == 100000.0

    # Stock
    stk = service.get_stock("AAPL")
    assert stk is not None
    assert stk.ticker == "AAPL"
    assert stk.basket_id == 10
