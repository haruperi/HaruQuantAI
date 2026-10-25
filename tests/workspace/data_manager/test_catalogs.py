"""Unit tests for Data Manager catalog services: Symbols, Sessions, Brokers, Baskets."""

from unittest.mock import patch

from app.workspace.data_manager import (
    Baskets,
    Brokers,
    Sessions,
    Symbols,
)
from app.workspace.data_manager.baskets import BasketInfo, BasketStockItem
from app.workspace.data_manager.brokers import BrokerInfo
from app.workspace.data_manager.symbols import SymbolInfo


def test_symbols_list_success(temp_db) -> None:
    service = Symbols(temp_db)
    assert service.add(name="EURUSD", datasource="test")["success"]
    response = service.list()

    assert isinstance(response, dict)
    assert response["success"] is True
    assert response["metadata"]["operation"] == "symbols.list"
    assert isinstance(response["data"], list)
    assert len(response["data"]) > 0

    first = response["data"][0]
    assert isinstance(first, dict)
    assert "name" in first
    assert "description" in first
    assert "price" in first
    assert "margin" in first
    assert "swap" in first


def test_symbols_list_failure() -> None:
    service = Symbols()
    with patch.object(service, "_read_symbols", side_effect=RuntimeError("DB boom")):
        response = service.list()
        assert response["success"] is False
        assert response["metadata"]["operation"] == "symbols.list"
        assert response["error"]["code"] == "internal"
        assert "DB boom" in response["message"]


def test_sessions_list_success() -> None:
    service = Sessions()
    response = service.list()

    assert isinstance(response, dict)
    assert response["success"] is True
    assert response["metadata"]["operation"] == "sessions.list"
    assert isinstance(response["data"], list)
    assert len(response["data"]) == 11

    names = [s["name"] for s in response["data"]]
    assert "24/5 Forex" in names
    assert "US Equities" in names

    first = response["data"][0]
    assert "timezone" in first
    assert "windows" in first


def test_sessions_list_failure() -> None:
    service = Sessions()
    with patch.object(
        service, "_read_sessions", side_effect=RuntimeError("Session error")
    ):
        response = service.list()
        assert response["success"] is False
        assert response["metadata"]["operation"] == "sessions.list"
        assert response["error"]["code"] == "internal"
        assert "Session error" in response["message"]


def test_brokers_list_success() -> None:
    service = Brokers()
    response = service.list()

    assert isinstance(response, dict)
    assert response["success"] is True
    assert response["metadata"]["operation"] == "brokers.list"
    assert isinstance(response["data"], list)
    assert len(response["data"]) == 11

    names = [b["name"] for b in response["data"]]
    assert "[[XTB]]" in names
    assert "[[RoboForex]]" in names

    first = response["data"][0]
    assert "server_timezone" in first
    assert "postfix" in first
    assert "enabled" in first
    assert "customized_stocks" in first
    assert "customized_instruments" in first
    assert "customized_sessions" in first

    by_name = {b["name"]: b for b in response["data"]}
    assert by_name["[[Darwinex Zero]]"]["customized_stocks"] == 812
    assert by_name["[[XTB]]"]["customized_stocks"] == 1334


def test_brokers_list_failure() -> None:
    service = Brokers()
    with patch.object(
        service, "_read_brokers", side_effect=RuntimeError("Broker failure")
    ):
        response = service.list()
        assert response["success"] is False
        assert response["metadata"]["operation"] == "brokers.list"
        assert response["error"]["code"] == "internal"
        assert "Broker failure" in response["message"]


def test_baskets_list_success() -> None:
    service = Baskets()
    response = service.list(include_stocks=True)

    assert isinstance(response, dict)
    assert response["success"] is True
    assert response["metadata"]["operation"] == "baskets.list"
    assert isinstance(response["data"], list)
    assert len(response["data"]) == 10

    total_stocks = sum(int(b["stocks_count"]) for b in response["data"])
    assert total_stocks == 31991

    first = response["data"][0]
    assert first["name"] == "[[S&P 500]]"
    assert first["stocks_count"] == 1354
    assert first["active_count"] > 0
    assert "date_from" in first
    assert "date_to" in first
    assert len(first["stocks"]) == 1354
    assert first["stocks"][0]["ticker"] == "A.D"


def test_baskets_list_without_stocks() -> None:
    service = Baskets()
    response = service.list(include_stocks=False)

    assert isinstance(response, dict)
    assert response["success"] is True
    assert len(response["data"]) == 10
    assert all(b["stocks_count"] == 0 for b in response["data"])
    assert all(len(b["stocks"]) == 0 for b in response["data"])


def test_baskets_list_failure() -> None:
    service = Baskets()
    with patch.object(
        service, "_read_stock_groups", side_effect=RuntimeError("Basket err")
    ):
        response = service.list()
        assert response["success"] is False
        assert response["metadata"]["operation"] == "baskets.list"
        assert response["error"]["code"] == "internal"
        assert "Basket err" in response["message"]


def test_domain_models_serialization() -> None:
    sym = SymbolInfo(name="EURUSD", description="Euro")
    assert sym.name == "EURUSD"

    broker = BrokerInfo(id=1, name="DemoBroker", server_timezone="UTC")
    assert broker.to_dict()["name"] == "DemoBroker"

    stock = BasketStockItem(id=10, ticker="AAPL", basket_id=1)
    assert stock.to_dict()["ticker"] == "AAPL"

    basket = BasketInfo(id=1, name="Tech", stocks_count=1, stocks=[stock])
    assert basket.to_dict()["name"] == "Tech"
    assert len(basket.to_dict()["stocks"]) == 1


def test_symbol_info_nested_dataclasses() -> None:
    sym = SymbolInfo(
        name="EURUSD",
        price={"digits": 5, "tick_size": 0.0001},
        spread={"floating": True, "default": 1.5},
    )
    assert sym.price.digits == 5
    assert sym.price.tick_size == 0.0001
    assert sym.spread.floating is True
    assert sym.spread.default == 1.5
    assert sym.margin.initial == 100000.0
    assert sym.volume.min == 0.01
    assert sym.trade.mode == "Full access"
    assert sym.swap.mode == "Points"
    assert sym.state.selected is True
    assert len(sym.session) == 7
    assert sym.session[0].day_of_week == 0
