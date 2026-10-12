"""Unit tests verifying 100% SQX parity for stock groups and baskets.

Key Capabilities Verified:
    - FR-DATA-BASKETS-GROUPS: Stock group metadata, CRUD, and system group immutability.
    - FR-DATA-BASKETS-SURVIVORSHIP: Historical entry/exit dates (date_from, date_to).
    - FR-DATA-BASKETS-INTERCHANGE: CSV text and SQX XML schema import/export.
    - FR-DATA-BASKETS-DIAGNOSTICS: Data readiness evaluation and missing symbol reporting.
    - FR-DATA-INTEGRATION-BASKETS: REST routes for CSV/XML interchange and diagnostics.
"""

from __future__ import annotations

import contextlib
import logging
import re
import sqlite3
from pathlib import Path
from typing import Any

import pytest
from app.host.persistence import DatabaseManager, ValidationError
from app.host.resources import ResourceManager
from app.workspace.data_manager.baskets import (
    BasketDefinition,
    BasketItem,
    BasketService,
    export_groups_xml,
    format_stock_lines,
    import_groups_xml,
    normalize_sqx_date,
    parse_stock_lines,
)
from app.workspace.data_manager.instruments import InstrumentService
from app.workspace.data_manager.routes import create_data_router
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def test_db(tmp_path: Path) -> DatabaseManager:
    """Fixture providing an isolated SQLite database."""
    db_file = tmp_path / "test_baskets_parity.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()
    InstrumentService(db).ensure_defaults()
    return db


def test_survivorship_dates_persistence(
    test_db: DatabaseManager, caplog: pytest.LogCaptureFixture
) -> None:
    """Validate that constituent date intervals (from and to) are persisted and restored."""
    caplog.set_level(logging.DEBUG)
    service = BasketService(test_db)

    basket = BasketDefinition(
        name="SP500_Sample",
        description="Standard & Poor's 500 Historical Sample",
        items=[
            BasketItem(
                symbol="AAPL",
                date_from="1980-12-12",
                date_to=None,
            ),
            BasketItem(
                symbol="AMZN",
                date_from="2007-04-15",
                date_to="2015-05-30",
            ),
            BasketItem(
                symbol="TSLA",
                date_from="2020-12-01",
                date_to=None,
            ),
        ],
    )

    group_id = service.save_basket(basket)
    assert group_id > 0
    assert any("FR-DATA-BASKETS-GROUPS" in rec.message for rec in caplog.records)

    retrieved = service.get_basket("SP500_Sample")
    assert retrieved is not None
    assert retrieved.name == "SP500_Sample"
    assert len(retrieved.items) == 3

    items_map = {item.symbol: item for item in retrieved.items}
    assert items_map["AAPL"].date_from == "1980-12-12"
    assert items_map["AAPL"].date_to is None
    assert items_map["AMZN"].date_from == "2007-04-15"
    assert items_map["AMZN"].date_to == "2015-05-30"
    assert items_map["TSLA"].date_from == "2020-12-01"
    assert items_map["TSLA"].date_to is None

    # Retrieve by ID
    by_id = service.get_basket_by_id(group_id)
    assert by_id is not None
    assert by_id.name == "SP500_Sample"
    assert len(by_id.items) == 3


def test_system_group_immutability(test_db: DatabaseManager) -> None:
    """Validate that system stock groups cannot be overwritten or deleted."""
    service = BasketService(test_db)

    system_basket = BasketDefinition(
        name="[[S&P 100 limited]]",
        description="Core immutable benchmark group",
        system=True,
        items=[
            BasketItem(symbol="AAPL"),
            BasketItem(symbol="MSFT"),
        ],
    )
    # Initial creation with override
    service.save_basket(system_basket, override_system=True)

    stored = service.get_basket("[[S&P 100 limited]]")
    assert stored is not None
    assert stored.system is True

    # Attempting to overwrite existing system basket raises ValueError
    modified = BasketDefinition(
        name="[[S&P 100 limited]]",
        description="Attempted illegal modification",
        items=[BasketItem(symbol="GOOGL")],
    )
    with pytest.raises(ValueError, match=r"System stock group '.*' cannot be modified"):
        service.save_basket(modified)

    # Attempting to delete system group fails and returns False
    assert service.delete_basket("[[S&P 100 limited]]") is False
    assert service.get_basket("[[S&P 100 limited]]") is not None

    # Deleting non-system group succeeds
    normal = BasketDefinition(
        name="NormalBasket",
        items=[BasketItem(symbol="NVDA")],
    )
    service.save_basket(normal)
    assert service.delete_basket("NormalBasket") is True
    assert service.get_basket("NormalBasket") is None


def test_csv_constituent_parsing_and_formatting() -> None:
    """Validate parsing and formatting of SQX Ticker;DD.MM.YYYY;DD.MM.YYYY lines."""
    donor_text = """
AAPL
TSLA;01.12.2020
AMZN;15.04.2007;30.05.2015
# comment line
    """
    items = parse_stock_lines(donor_text)
    assert len(items) == 3

    assert items[0].symbol == "AAPL"
    assert items[0].date_from is None
    assert items[0].date_to is None

    assert items[1].symbol == "TSLA"
    assert items[1].date_from == "2020-12-01"
    assert items[1].date_to is None

    assert items[2].symbol == "AMZN"
    assert items[2].date_from == "2007-04-15"
    assert items[2].date_to == "2015-05-30"

    # Format back to text
    formatted = format_stock_lines(items)
    lines = [ln.strip() for ln in formatted.splitlines() if ln.strip()]
    assert lines == [
        "AAPL",
        "TSLA;01.12.2020",
        "AMZN;15.04.2007;30.05.2015",
    ]


def test_xml_interchange_schema() -> None:
    """Validate exporting and importing SQX canonical <Groups><Group>... XML."""
    baskets = [
        BasketDefinition(
            name="TechTrio",
            description="Leading Tech Stocks",
            items=[
                BasketItem(symbol="AAPL", date_from="2010-01-01"),
                BasketItem(symbol="MSFT", date_from="2010-01-01", date_to="2024-01-01"),
            ],
        )
    ]

    xml_text = export_groups_xml(baskets)
    assert "<Groups>" in xml_text
    assert '<Group name="TechTrio">' in xml_text
    assert "<Desc>Leading Tech Stocks</Desc>" in xml_text
    assert '<Stock name="AAPL"' in xml_text
    assert '<Stock name="MSFT"' in xml_text

    imported = import_groups_xml(xml_text)
    assert len(imported) == 1
    assert imported[0].name == "TechTrio"
    assert imported[0].description == "Leading Tech Stocks"
    assert len(imported[0].items) == 2
    assert imported[0].items[0].symbol == "AAPL"
    assert imported[0].items[0].date_from == "2010-01-01"
    assert imported[0].items[1].symbol == "MSFT"
    assert imported[0].items[1].date_from == "2010-01-01"
    assert imported[0].items[1].date_to == "2024-01-01"


def test_readiness_diagnostics(
    test_db: DatabaseManager, caplog: pytest.LogCaptureFixture
) -> None:
    """Validate data availability diagnostics and missing symbol identification."""
    caplog.set_level(logging.DEBUG)
    service = BasketService(test_db)

    basket = BasketDefinition(
        name="DiagnosticsGroup",
        items=[
            BasketItem(symbol="AAPL"),
            BasketItem(symbol="MSFT"),
            BasketItem(symbol="NVDA"),
        ],
    )
    service.save_basket(basket)

    # Only AAPL and MSFT are downloaded
    available = {"AAPL", "msft"}  # case-insensitive check
    readiness = service.check_readiness(basket, available)

    assert readiness.is_ready is False
    assert readiness.downloaded_count == 2
    assert readiness.total_count == 3
    assert readiness.missing_symbols == ["NVDA"]
    assert any("FR-DATA-BASKETS-DIAGNOSTICS" in rec.message for rec in caplog.records)

    # Provide all constituents
    available_all = {"AAPL", "MSFT", "NVDA"}
    readiness_all = service.check_readiness(basket, available_all)
    assert readiness_all.is_ready is True
    assert readiness_all.downloaded_count == 3
    assert readiness_all.missing_symbols == []


def test_basket_service_csv_import_export(test_db: DatabaseManager) -> None:
    """Validate BasketService helper methods for CSV constituent import and export."""
    service = BasketService(test_db)
    basket = BasketDefinition(
        name="CsvTestGroup",
        items=[BasketItem(symbol="INITIAL")],
    )
    service.save_basket(basket)

    csv_data = "AAPL;01.01.2020\nMSFT;01.01.2020;31.12.2023\n"
    updated = service.import_stocks_from_csv("CsvTestGroup", csv_data)
    assert len(updated.items) == 2
    assert updated.items[0].symbol == "AAPL"
    assert updated.items[0].date_from == "2020-01-01"
    assert updated.items[1].symbol == "MSFT"
    assert updated.items[1].date_to == "2023-12-31"

    exported = service.export_stocks_to_csv("CsvTestGroup")
    assert "AAPL;01.01.2020" in exported
    assert "MSFT;01.01.2020;31.12.2023" in exported


def test_basket_routes_api(test_db: DatabaseManager, tmp_path: Path) -> None:
    """Validate FastAPI endpoints for basket CSV/XML interchange and readiness."""
    app = FastAPI()
    res_mgr = ResourceManager(root_dir=tmp_path / "resources")
    router = create_data_router(db_manager=test_db, resource_manager=res_mgr)
    app.include_router(router)
    client = TestClient(app)

    # 1. Create a basket
    create_payload = {
        "name": "RouteGroup",
        "description": "API Route Test Group",
        "items": [
            {"symbol": "AAPL", "weight": 1.0, "date_from": "2020-01-01"},
            {"symbol": "MSFT", "weight": 1.0, "date_from": "2020-01-01"},
        ],
    }
    resp = client.post("/data/baskets", json=create_payload)
    assert resp.status_code == 201
    assert resp.json()["data"]["name"] == "RouteGroup"

    # 2. Get the basket
    resp = client.get("/data/baskets/RouteGroup")
    assert resp.status_code == 200
    assert len(resp.json()["data"]["items"]) == 2

    # 3. Export CSV
    resp = client.get("/data/baskets/RouteGroup/export-csv")
    assert resp.status_code == 200
    assert "AAPL;01.01.2020" in resp.text

    # 4. Import CSV
    import_payload = {
        "basket_name": "RouteGroup",
        "csv_text": "GOOGL;15.06.2021\nAMZN;01.01.2018;01.01.2022\n",
    }
    resp = client.post("/data/baskets/import-csv", json=import_payload)
    assert resp.status_code == 200
    assert len(resp.json()["data"]["items"]) == 2

    # 5. Export XML
    export_xml_payload = {"basket_names": ["RouteGroup"]}
    resp = client.post("/data/baskets/export-xml", json=export_xml_payload)
    assert resp.status_code == 200
    assert "<Groups>" in resp.text
    assert '<Group name="RouteGroup">' in resp.text
    xml_content = resp.text

    # 6. Import XML
    import_xml_payload = {"xml_content": xml_content, "overwrite": True}
    resp = client.post("/data/baskets/import-xml", json=import_xml_payload)
    assert resp.status_code == 200
    assert resp.json()["data"][0]["name"] == "RouteGroup"

    # 7. Check readiness
    resp = client.get("/data/baskets/RouteGroup/readiness")
    assert resp.status_code == 200
    assert "is_ready" in resp.json()["data"]

    # 8. Delete basket
    resp = client.delete("/data/baskets/RouteGroup")
    assert resp.status_code == 200
    assert resp.json()["data"]["deleted"] is True


def test_default_groups_seeding(test_db: DatabaseManager) -> None:
    """Validate that ensure_defaults populates the 10 authoritative SQX default groups."""
    service = BasketService(test_db)
    service.ensure_defaults()

    baskets = service.list_baskets()
    names = {b.name for b in baskets}

    expected_groups = {
        "[[Dow Jones Industrial Average]]",
        "[[Nasdaq 100]]",
        "[[Nasdaq Biotechnology]]",
        "[[Russell 1000]]",
        "[[Russell 2000]]",
        "[[Russell 3000]]",
        "[[S&P 100 limited]]",
        "[[S&P 100]]",
        "[[S&P 500]]",
        "[[S&P MidCap 400]]",
    }
    assert expected_groups.issubset(names)

    djia = service.get_basket("[[Dow Jones Industrial Average]]")
    assert djia is not None
    assert djia.system is True
    assert len(djia.items) == 30

    nasdaq = service.get_basket("[[Nasdaq 100]]")
    assert nasdaq is not None
    assert nasdaq.system is True
    assert len(nasdaq.items) > 0


def test_baskets_overview_metrics(test_db: DatabaseManager) -> None:
    """Validate list_baskets_overview returns the 8 SQX table grid columns."""
    service = BasketService(test_db)
    service.ensure_defaults()

    # Add historical data record for AAPL in catalog
    with test_db.transaction() as conn:
        conn.execute(
            """INSERT INTO datamgr_datasets
            (id, symbol, underlying, instrument, source, timeframe, broker, broker_name, timezone, category, date_from, date_to, bars, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "AAPL_D1",
                "AAPL",
                "AAPL",
                "AAPL",
                "Equity",
                "D1",
                "Default",
                "Default",
                "UTC",
                "Stocks",
                "2020-01-01",
                "2024-01-01",
                1000,
                "2024-01-01T00:00:00Z",
                "2024-01-01T00:00:00Z",
            ),
        )

    overview = service.list_baskets_overview()
    assert len(overview) >= 10

    by_name = {item.name: item for item in overview}
    assert "[[Dow Jones Industrial Average]]" in by_name
    djia_overview = by_name["[[Dow Jones Industrial Average]]"]
    assert djia_overview.total_count == 30
    assert djia_overview.active_count == 30
    assert djia_overview.symbols_count == 30
    # AAPL is in DJIA so downloaded_count must be at least 1
    assert djia_overview.downloaded_count >= 1
    # Not all 30 symbols downloaded, so not ready
    assert djia_overview.is_ready is False
    assert "AAPL" not in djia_overview.missing_symbols
    assert len(djia_overview.missing_symbols) > 0


def test_update_group_data_rules(test_db: DatabaseManager) -> None:
    """Validate SQX rules and exceptions for group data updates."""
    service = BasketService(test_db)
    service.ensure_defaults()

    # Rule 1: S&P 100 limited cannot be updated
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Group S&P 100 limited cannot be updated, it is only in clean installation."
        ),
    ):
        service.update_group_data("[[S&P 100 limited]]")

    # Rule 2: Empty group cannot be updated
    empty_basket = BasketDefinition(
        name="EmptyGroup",
        description="Group without stocks",
        items=[],
    )
    service.save_basket(empty_basket)
    with pytest.raises(
        ValueError,
        match=re.escape("Nothing to update. Group is without any stocks."),
    ):
        service.update_group_data("EmptyGroup")

    # Rule 3: Valid group triggers background update job
    res = service.update_group_data("[[Nasdaq 100]]")
    assert res["status"] == "started"
    assert res["basket_name"] == "[[Nasdaq 100]]"
    assert res["total_symbols"] > 0
    assert "missing_symbols" in res


def test_basket_routes_overview_and_update(
    test_db: DatabaseManager, tmp_path: Path
) -> None:
    """Validate FastAPI routes for overview and background data updates including SQX aliases."""
    app = FastAPI()
    res_mgr = ResourceManager(root_dir=tmp_path / "resources")
    router = create_data_router(db_manager=test_db, resource_manager=res_mgr)
    app.include_router(router)
    client = TestClient(app)

    # 1. GET /data/baskets/overview
    resp = client.get("/data/baskets/overview")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data, list)
    assert len(data) >= 10

    # 2. SQX alias: GET /data/basketOfStocks/list
    resp_alias = client.get("/data/basketOfStocks/list")
    assert resp_alias.status_code == 200
    assert len(resp_alias.json()["data"]) >= 10

    # 3. POST /data/baskets/update-data with S&P 100 limited returns error
    resp_err = client.post(
        "/data/baskets/update-data", json={"basket_ids": ["[[S&P 100 limited]]"]}
    )
    assert resp_err.status_code == 400
    assert "Group S&P 100 limited cannot be updated" in resp_err.json()["message"]

    # 4. POST /data/baskets/update-data with valid group returns success
    resp_ok = client.post(
        "/data/baskets/update-data",
        json={"basket_ids": ["[[Dow Jones Industrial Average]]"]},
    )
    assert resp_ok.status_code == 200
    assert (
        resp_ok.json()["message"]
        == "Data update started, please check Log tab for more information."
    )

    # 5. SQX alias: POST /data/basketOfStocks/updateData
    resp_alias_update = client.post(
        "/data/basketOfStocks/updateData",
        json={"basket_ids": ["[[Dow Jones Industrial Average]]"]},
    )
    assert resp_alias_update.status_code == 200
    assert (
        resp_alias_update.json()["message"]
        == "Data update started, please check Log tab for more information."
    )


def test_normalize_sqx_date_helper() -> None:
    """Test date normalization across SQX epoch ms, -1, ISO, and pre-1970 dates."""
    assert normalize_sqx_date(None) is None
    assert normalize_sqx_date(-1) is None
    assert normalize_sqx_date("-1") is None
    assert normalize_sqx_date("") is None
    assert normalize_sqx_date("null") is None
    # 960163200000 ms is 2000-06-05
    assert normalize_sqx_date(960163200000) == "2000-06-05"
    assert normalize_sqx_date("960163200000") == "2000-06-05"
    # Negative epoch millisecond (-630892800000 ms is 1950-01-04)
    assert normalize_sqx_date(-630892800000) == "1950-01-04"
    # ISO strings
    assert normalize_sqx_date("1900-01-01") == "1900-01-01"
    assert normalize_sqx_date("2024-05-15T12:00:00") == "2024-05-15"
    # European format DD.MM.YYYY
    assert normalize_sqx_date("05.06.2000") == "2000-06-05"


def test_sqx_legacy_schema_and_date_formats(tmp_path: Path) -> None:
    """Validate compatibility with legacy SQX uppercase SQLite schema and integer dates."""
    db_path = tmp_path / "legacy_sqx.db"
    conn = sqlite3.connect(db_path)
    # Replicate exact SQX table DDL (uppercase columns, no unique constraint on NAME)
    conn.execute(
        """
        CREATE TABLE datamgr_stock_group (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            NAME VARCHAR(50) NOT NULL,
            SYSTEM BOOLEAN NOT NULL,
            DESC VARCHAR(250)
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE datamgr_stock (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            TICKER VARCHAR(20) NOT NULL,
            BASKET_ID INTEGER NOT NULL,
            DATE_FROM INTEGER NOT NULL,
            DATE_TO INTEGER NOT NULL
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE datamgr_datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol VARCHAR(20) NOT NULL,
            date_from VARCHAR(30),
            date_to VARCHAR(30),
            bars INTEGER
        );
        """
    )
    # Insert legacy rows with epoch ms and -1
    conn.execute(
        "INSERT INTO datamgr_stock_group (ID, NAME, SYSTEM, DESC) "
        "VALUES (1, '[[S&P 500]]', 1, 'Standard & Poor 500')"
    )
    conn.execute(
        "INSERT INTO datamgr_stock (ID, TICKER, BASKET_ID, DATE_FROM, DATE_TO) "
        "VALUES (10, 'AAPL', 1, 960163200000, -1)"
    )
    conn.execute(
        "INSERT INTO datamgr_stock (ID, TICKER, BASKET_ID, DATE_FROM, DATE_TO) "
        "VALUES (11, 'OLD', 1, -630892800000, 1497571200000)"
    )
    conn.commit()
    conn.close()

    db = DatabaseManager(database_path=db_path)
    service = BasketService(db)

    # 1. Test get_basket with uppercase columns
    basket = service.get_basket("[[S&P 500]]")
    assert basket is not None
    assert basket.id == 1
    assert basket.name == "[[S&P 500]]"
    assert basket.description == "Standard & Poor 500"
    assert basket.system is True
    assert len(basket.items) == 2

    aapl = next(i for i in basket.items if i.symbol == "AAPL")
    assert aapl.date_from == "2000-06-05"
    assert aapl.date_to is None

    old = next(i for i in basket.items if i.symbol == "OLD")
    assert old.date_from == "1950-01-04"
    assert old.date_to == "2017-06-16"

    # 2. Test list_baskets_overview with uppercase columns and integer timestamps
    overview = service.list_baskets_overview()
    assert len(overview) == 1
    ov = overview[0]
    assert ov.id == 1
    assert ov.name == "[[S&P 500]]"
    assert ov.total_count == 2
    # AAPL is active, OLD expired in 2017
    assert ov.active_count == 1
    assert ov.symbols_count == 2
    assert "AAPL" in ov.missing_symbols
    assert "OLD" in ov.missing_symbols

    # 3. Test saving a new basket on legacy table without UNIQUE constraint
    new_basket = BasketDefinition(
        name="Custom Tech",
        description="Custom tech stock group",
        system=False,
        items=[BasketItem(symbol="MSFT", date_from="2010-01-01", date_to=None)],
    )
    new_id = service.save_basket(new_basket)
    assert new_id > 1

    retrieved = service.get_basket("Custom Tech")
    assert retrieved is not None
    assert retrieved.name == "Custom Tech"
    assert len(retrieved.items) == 1
    assert retrieved.items[0].symbol == "MSFT"


def test_ensure_defaults_canonical_sqx_groups(test_db: DatabaseManager) -> None:
    """Verify that ensure_defaults seeds exactly the 10 canonical SQX double-bracketed groups."""
    service = BasketService(test_db)
    service.ensure_defaults()
    store = test_db.baskets

    groups = store.list_groups()
    assert len(groups) == 10

    names = {g["name"] for g in groups}
    expected = {
        "[[Dow Jones Industrial Average]]",
        "[[Nasdaq 100]]",
        "[[Nasdaq Biotechnology]]",
        "[[Russell 1000]]",
        "[[Russell 2000]]",
        "[[Russell 3000]]",
        "[[S&P 100 limited]]",
        "[[S&P 100]]",
        "[[S&P 500]]",
        "[[S&P MidCap 400]]",
    }
    assert names == expected
    for g in groups:
        assert g["system"] == 1
        assert g["name"].startswith("[[") and g["name"].endswith("]]")

    # Idempotent re-run
    service.ensure_defaults()
    assert store.count() == 10


def test_read_overview_rows_query_count(test_db: DatabaseManager) -> None:
    """Verify read_overview_rows executes exactly 3 queries under one read transaction."""
    queries: list[str] = []
    orig_connection = test_db.connection

    @contextlib.contextmanager
    def tracked_connection(*args: Any, **kwargs: Any):
        with orig_connection(*args, **kwargs) as conn:
            conn.set_trace_callback(queries.append)
            try:
                yield conn
            finally:
                conn.set_trace_callback(None)

    test_db.connection = tracked_connection  # type: ignore[assignment]
    try:
        groups, stocks, datasets = test_db.baskets.read_overview_rows()
    finally:
        test_db.connection = orig_connection

    select_queries = [q for q in queries if q.strip().upper().startswith("SELECT")]
    assert len(select_queries) == 3
    assert any("datamgr_stock_group" in q for q in select_queries)
    assert any("datamgr_stock" in q for q in select_queries)
    assert any("datamgr_datasets" in q for q in select_queries)
    assert not any("sqlite_master" in q.lower() for q in queries)


def test_read_overview_rows_fails_closed_when_datasets_missing(tmp_path: Path) -> None:
    """Verify read_overview_rows fails closed if datamgr_datasets table is missing."""
    db_path = tmp_path / "missing_datasets.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE datamgr_stock_group "
        "(id INTEGER PRIMARY KEY, name TEXT, system INT, description TEXT)"
    )
    conn.execute(
        "CREATE TABLE datamgr_stock "
        "(id INTEGER PRIMARY KEY, ticker TEXT, basket_id INTEGER, date_from TEXT, date_to TEXT)"
    )
    conn.close()

    db = DatabaseManager(database_path=db_path)
    with pytest.raises(
        sqlite3.OperationalError, match="no such table: datamgr_datasets"
    ):
        db.baskets.read_overview_rows()


def test_expired_member_active_count_is_zero(test_db: DatabaseManager) -> None:
    """Verify BasketService calculates active_count as 0 for past expired constituents."""
    # Ensure BasketStore no longer retains duplicate list_groups_overview
    assert not hasattr(test_db.baskets, "list_groups_overview")

    service = BasketService(test_db)
    basket = BasketDefinition(
        name="Expired Historical Group",
        description="Constituent expired in 2020",
        system=False,
        items=[
            BasketItem(
                symbol="DEAD",
                date_from="2000-01-01",
                date_to="2020-01-01",
            )
        ],
    )
    service.save_basket(basket)

    overview = service.list_baskets_overview()
    target = next((o for o in overview if o.name == "Expired Historical Group"), None)
    assert target is not None
    assert target.total_count == 1
    assert target.active_count == 0
    assert target.symbols_count == 1


def test_seed_defaults_rejects_incomplete_group_record(
    test_db: DatabaseManager,
) -> None:
    """Verify seed_defaults fails closed on missing group fields without inventing defaults."""
    # Missing system
    with pytest.raises(ValidationError, match="missing required 'system' field"):
        test_db.baskets.seed_defaults(
            [{"name": "No System", "description": "desc", "members": []}]
        )

    # Missing description
    with pytest.raises(ValidationError, match="missing required 'description' field"):
        test_db.baskets.seed_defaults([{"name": "No Desc", "system": 1, "members": []}])

    # Missing members
    with pytest.raises(ValidationError, match="missing required 'members' list"):
        test_db.baskets.seed_defaults(
            [{"name": "No Members", "system": 1, "description": "desc"}]
        )

    # Empty name
    with pytest.raises(ValidationError, match="must contain a non-empty 'name'"):
        test_db.baskets.seed_defaults(
            [{"name": "  ", "system": 1, "description": "desc", "members": []}]
        )


def test_seed_defaults_rejects_incomplete_member_record(
    test_db: DatabaseManager,
) -> None:
    """Verify seed_defaults fails closed on missing constituent member fields without inventing defaults."""
    # Missing date_from
    with pytest.raises(ValidationError, match="must have explicit 'date_from'"):
        test_db.baskets.seed_defaults(
            [
                {
                    "name": "Group",
                    "system": 1,
                    "description": "desc",
                    "members": [{"ticker": "AAPL", "date_to": None}],
                }
            ]
        )

    # Missing date_to
    with pytest.raises(ValidationError, match="must have explicit 'date_to'"):
        test_db.baskets.seed_defaults(
            [
                {
                    "name": "Group",
                    "system": 1,
                    "description": "desc",
                    "members": [{"ticker": "AAPL", "date_from": "1900-01-01"}],
                }
            ]
        )

    # Missing/empty ticker
    with pytest.raises(ValidationError, match="must have a non-empty 'ticker'"):
        test_db.baskets.seed_defaults(
            [
                {
                    "name": "Group",
                    "system": 1,
                    "description": "desc",
                    "members": [
                        {"ticker": "", "date_from": "1900-01-01", "date_to": None}
                    ],
                }
            ]
        )
