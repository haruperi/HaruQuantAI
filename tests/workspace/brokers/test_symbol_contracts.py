"""Regression coverage for broker adapters using nested symbol contracts."""

import asyncio
from dataclasses import asdict
from unittest.mock import AsyncMock, Mock

import pytest
from app.include.contracts import SymbolInfo, SymbolMargin, SymbolPrice, TradeRequest
from app.include.enums import OrderFilling, OrderType, TradeAction, TradeRetcode
from app.include.trading import SymbolProxy
from app.workspace.brokers import (
    BinanceClient,
    DarwinexClient,
    DukascopyClient,
    FilesClient,
    SimulatorClient,
    SQEquityClient,
    SQFuturesClient,
    YahooClient,
)
from app.workspace.brokers.ctrader import CTraderClient
from app.workspace.brokers.metatrader import MetaTraderClient
from app.workspace.brokers.tick_downloader import TickDownloaderClient


@pytest.mark.parametrize(
    "client_type", [DukascopyClient, DarwinexClient, SQEquityClient, SQFuturesClient]
)
def test_catalogs_construct_nested_symbols(tmp_path, client_type):
    path = tmp_path / "catalog.csv"
    if client_type is DukascopyClient:
        content = "EURUSD;x;x;x;x;x;5;0.00001;2;x;100000\n"
    elif client_type is DarwinexClient:
        content = "EURUSD;x;5;100000;x;x;0.00001;2\n"
    else:
        content = (
            "symbol;decimals;point;spread;contract_size\nEURUSD;5;0.00001;2;100000\n"
        )
    path.write_text(content, encoding="utf-8")
    info = client_type(catalog_path=path).get_symbol_info("EURUSD")
    assert info.price.digits == 5
    assert info.price.tick_size == 0.00001
    assert info.price.contract_size == 100000
    assert info.spread.default == 2


@pytest.mark.parametrize(
    "client_type", [FilesClient, MetaTraderClient, TickDownloaderClient, YahooClient]
)
def test_simple_clients_construct_nested_symbols(client_type):
    info = client_type().get_symbol_info("EURUSD")
    assert isinstance(info, SymbolInfo)
    assert isinstance(info.price, SymbolPrice)
    assert info.price.tick_size > 0
    assert info.price.contract_size > 0
    if client_type is FilesClient:
        assert info.state.custom


def test_crypto_symbol_specification(monkeypatch):
    client = BinanceClient()
    response = Mock()
    response.headers = {}
    response.content = b"{}"
    response.status_code = 200
    response.json.return_value = {
        "symbols": [
            {
                "baseAsset": "BTC",
                "quoteAsset": "USDT",
                "filters": [
                    {"filterType": "PRICE_FILTER", "tickSize": "0.01"},
                    {"filterType": "LOT_SIZE", "stepSize": "0.001"},
                ],
            }
        ]
    }
    monkeypatch.setattr(client.session, "get", Mock(return_value=response))
    info = client.get_symbol_info("BTCUSDT")
    assert info.price.digits == 2
    assert info.price.tick_size == 0.01
    assert info.price.tick_step == 0.01
    assert info.margin.currency_base == "BTC"
    assert info.margin.currency_profit == "USDT"
    assert not info.state.custom


def test_ctrader_constructs_nested_symbol(monkeypatch):
    client = CTraderClient()
    monkeypatch.setattr(client, "_require_auth", lambda: None)
    info = client.get_symbol_info("EURUSD")
    assert info.price.digits == 5
    assert info.price.ask > info.price.bid
    assert info.spread.default == 20
    assert info.margin.currency_base == "EUR"
    assert info.margin.currency_profit == "USD"
    assert info.volume.step == 0.01


def test_bridge_snapshot_coerces_nested_wire_sections():
    backend = Mock()
    backend.call = AsyncMock(
        return_value={
            "name": "EURUSD",
            "description": "Euro vs Dollar",
            "data_type": "Forex",
            "price": {
                "digits": 5,
                "tick_size": 0.00001,
                "tick_step": 0.00001,
                "contract_size": 100000,
                "bid": 1.1,
                "ask": 1.1001,
            },
            "margin": {"currency_base": "EUR", "currency_profit": "USD", "initial": 0},
            "spread": {"floating": True, "default": 10},
            "trade": {
                "mode": "Full access",
                "execution": "Market",
                "filling": ["Immediate or Cancel"],
            },
            "volume": {"min": 0.01, "max": 100, "step": 0.01},
            "swap": {
                "mode": "Points",
                "long": -2,
                "short": 1,
                "rollover3days": "Wednesday",
            },
            "session": [
                {"day_of_week": 1, "start_time": "00:00:00", "end_time": "23:59:59"}
            ],
            "state": {"custom": False, "selected": True, "visible": True},
            "commission": 0,
        }
    )
    info = asyncio.run(SymbolProxy(backend).SymbolInfo())
    assert isinstance(info.price, SymbolPrice)
    assert info.price.contract_size == 100000
    assert info.trade.execution == "Market"
    assert info.session[0].start_time == "00:00:00"


def test_simulator_uses_nested_specs_without_mutating_inputs():
    client = SimulatorClient()
    info = SymbolInfo(
        name="EURUSD",
        price=SymbolPrice(contract_size=100000),
        margin=SymbolMargin(initial=0),
    )
    original = asdict(info)
    client.add_symbol(info)
    client.feed_tick("EURUSD", bid=1.10, ask=1.1001)
    snapshot = client.symbol("EURUSD")
    assert snapshot.price.bid == 1.10
    snapshot.price.bid = 9
    assert client.symbol("EURUSD").price.bid == 1.10
    assert client.calc_profit(
        OrderType.BUY, "EURUSD", 0.1, 1.1, 1.101
    ) == pytest.approx(10)
    assert client.select_symbol("EURUSD", False)
    assert not client.symbol("EURUSD").state.selected
    assert asdict(info) == original
    request = TradeRequest(
        action=TradeAction.DEAL,
        symbol="EURUSD",
        volume=0.1,
        order_type=OrderType.BUY,
        type_filling=OrderFilling.IOC,
    )
    assert client.order_check(request).retcode == TradeRetcode.DONE
    assert client.order_send(request).retcode == TradeRetcode.DONE
    assert client.info_value("symbol", "session_deals", "EURUSD") == 1
