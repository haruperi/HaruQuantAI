"""Unit tests verifying 100% SQX parity for stock groups and baskets.

Key Capabilities Verified:
    - FR-DATA-BASKETS-GROUPS: Stock group metadata, CRUD, and system group immutability.
    - FR-DATA-BASKETS-SURVIVORSHIP: Historical entry/exit dates (date_from, date_to).
    - FR-DATA-BASKETS-INTERCHANGE: CSV text and SQX XML schema import/export.
    - FR-DATA-BASKETS-DIAGNOSTICS: Data readiness evaluation and missing symbol reporting.
    - FR-DATA-INTEGRATION-BASKETS: REST routes for CSV/XML interchange and diagnostics.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
from app.host.persistence import DatabaseManager
from app.host.resources import ResourceManager
from app.workspace.data_manager.baskets import (
    BasketDefinition,
    BasketItem,
    BasketService,
    export_groups_xml,
    format_stock_lines,
    import_groups_xml,
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
