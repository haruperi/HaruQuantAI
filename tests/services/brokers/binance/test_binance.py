"""Unit tests for Binance broker provider."""

from __future__ import annotations

from typing import Any

import pytest
from app.contracts.broker.binance import resolve_timeframe
from app.contracts.broker.capabilities import (
    BROKER_OPERATIONS_CAPABILITY,
    PROVIDER_BINANCE_CAPABILITY,
)
from app.contracts.broker.models import (
    BrokerAccountInfo,
    BrokerSymbolInfo,
    BrokerTerminalInfo,
)
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.brokers.binance.client import BinanceClient
from app.services.brokers.binance.config import BinanceConfig
from app.services.brokers.binance.feature import BinanceFeature, feature
from app.services.brokers.binance.manifest import SPEC


def _context(
    feature_instance: BinanceFeature,
) -> tuple[DefaultFeatureContext, ServiceRegistry, FeatureScope]:
    registry = ServiceRegistry()
    scope = FeatureScope(owner_id=feature_instance.spec.feature_id)

    def register(capability: Any, provider: Any, owner_scope: FeatureScope) -> None:
        registry.register(
            capability,
            provider,
            owner_id=feature_instance.spec.feature_id,
            scope=owner_scope,
        )

    return (
        DefaultFeatureContext(
            spec=feature_instance.spec,
            scope=scope,
            resolver=registry.resolve,
            provider_registrar=register,
            event_bus=EventBus(),
        ),
        registry,
        scope,
    )


def test_binance_client_connection_and_account() -> None:
    """Verify BinanceClient connection, environment, and account data."""
    client = BinanceClient()
    assert client.is_available() is True
    assert client.is_connected() is False

    # Account info fails gracefully before connection
    acc_unconnected = client.get_account_info()
    assert acc_unconnected.status == "error"

    conn_res = client.connect(
        api_key="key_123",  # pragma: allowlist secret
        api_secret="sec_123",  # pragma: allowlist secret
        testnet=True,
    )
    assert conn_res.status == "success"
    assert conn_res.data["connected"] is True
    assert conn_res.data["status"] == "connected"
    assert client.is_connected() is True
    assert client.ping() > 0.0

    status = client.get_connection_status()
    assert status.status == "success"
    assert status.data["connected"] is True

    p_info = client.get_platform_info()
    assert p_info.data["platform"] == "binance"

    spec = client.get_provider_specification()
    assert spec.data["provider"] == "binance"
    assert spec.data["supports_spot"] is True

    acc = client.get_account_info()
    assert acc.status == "success"
    assert isinstance(acc.data, BrokerAccountInfo)
    assert acc.data.currency == "USDT"
    assert acc.data["currency"] == "USDT"

    balances = client.get_balances()
    assert balances.status == "success"
    assert balances.data["currency"] == "USDT"

    perms = client.get_permissions()
    assert "SPOT" in perms

    snap = client.get_account_snapshot()
    assert snap.status == "success"
    assert snap.data["connected"] is True

    term_info = client.get_terminal_info()
    assert term_info.status == "success"
    assert isinstance(term_info.data, BrokerTerminalInfo)
    assert term_info.data.name == "Binance"
    assert term_info.data["name"] == "Binance"


def test_binance_market_data() -> None:
    """Verify BinanceClient symbols, quotes, ticks, and streams."""
    client = BinanceClient()
    client.connect(
        api_key="key_123",  # pragma: allowlist secret
        api_secret="sec_123",  # pragma: allowlist secret
    )

    syms_res = client.get_symbols()
    assert syms_res.status == "success"
    assert len(syms_res.data) > 0
    assert any(s.symbol == "BTCUSDT" for s in syms_res.data)

    num_syms = client.get_num_of_symbols()
    assert num_syms.status == "success"
    assert num_syms.data > 0

    info = client.get_symbol_info("BTCUSDT")
    assert info.status == "success"
    assert isinstance(info.data, BrokerSymbolInfo)
    assert info.data.symbol == "BTCUSDT"
    assert info.data["symbol"] == "BTCUSDT"

    bad_info = client.get_symbol_info("INVALID_CRYPTO")
    assert bad_info.status == "error"

    assert client.enable_symbol("BTCUSDT").status == "success"
    assert client.select_symbol("BTCUSDT") is True

    tick_res = client.get_symbol_tick("BTCUSDT")
    assert tick_res.status == "success"
    assert tick_res.data["bid"] > 0

    quote = client.get_quote("BTCUSDT")
    assert quote["bid"] > 0
    assert client.get_spread("BTCUSDT") > 0

    ticks = client.get_ticks("BTCUSDT", count=5)
    assert ticks.status == "success"
    assert len(ticks.data) == 5
    assert ticks.data.index.name == "DateTime"
    assert list(ticks.data.columns) == ["Bid", "Ask", "Volume"]

    bars = client.get_bars("BTCUSDT", count=5)
    assert bars.status == "success"
    assert len(bars.data) == 5
    assert bars.data.index.name == "DateTime"
    assert list(bars.data.columns) == [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "Spread",
    ]

    depth_sub = client.subscribe_market_depth("BTCUSDT")
    assert depth_sub.status == "success"
    depth = client.get_market_depth("BTCUSDT")
    assert depth.status == "success"
    assert len(depth.data) > 0
    depth_unsub = client.unsubscribe_market_depth("BTCUSDT")
    assert depth_unsub.status == "success"

    sub_q = client.subscribe_quotes(["BTCUSDT"])
    client.subscribe_ticks(["BTCUSDT"])
    client.subscribe_bars(["BTCUSDT"], "1m")
    assert len(client.list_subscriptions()) >= 3
    assert client.unsubscribe(sub_q) is True


def test_binance_orders_and_trading() -> None:
    """Verify BinanceClient orders, positions, and execution calculations."""
    client = BinanceClient()
    client.connect(
        api_key="key_123",  # pragma: allowlist secret
        api_secret="sec_123",  # pragma: allowlist secret
    )

    assert client.get_orders() == []
    assert client.get_order_info().status == "success"
    assert client.get_num_orders().data == 0
    assert client.get_order("101") is None
    assert (
        client.check_order({"symbol": "BTCUSDT", "volume": 1.0}).data["valid"] is True
    )

    assert client.list_order_history() == []
    assert client.get_history_order_info().status == "success"
    assert client.get_num_history_orders().data == 0
    assert client.get_history_order("101") is None

    assert client.get_deals() == []
    assert client.get_history_deal_info().status == "success"
    assert client.get_num_history_deals().data == 0
    assert client.list_deal_history() == []
    assert client.list_account_transactions() == []

    assert client.get_positions() == []
    assert client.get_position_info().status == "success"
    assert client.get_num_positions().data == 0
    assert client.get_position("101") is None

    trade_res = client.trade({"symbol": "BTCUSDT", "volume": 0.1})
    assert trade_res.status == "success"
    assert trade_res.data["status"] == "FILLED"

    order_res = client.place_order({"symbol": "BTCUSDT", "volume": 0.1})
    assert order_res["status"] == "FILLED"

    assert client.modify_order({"orderId": 2831924})["status"] == "SUCCESS"
    assert client.cancel_order("2831924")["status"] == "CANCELED"
    assert client.modify_position({"symbol": "BTCUSDT"})["status"] == "SUCCESS"
    assert client.close_position("pos_101")["status"] == "CLOSED"

    margin_res = client.calculate_margin(
        {"volume": 1.0, "price": 65000.0, "leverage": 10}
    )
    assert margin_res.status == "success"
    assert margin_res.data == 6500.0

    profit_res = client.calculate_profit(
        {
            "volume": 1.0,
            "price_open": 65000.0,
            "price_close": 66000.0,
        }
    )
    assert profit_res.status == "success"
    assert profit_res.data == 1000.0

    assert client.get_last_error() == (0, "Success")
    assert resolve_timeframe("1h") == "1h"
    assert resolve_timeframe("H1") == "1h"

    client.disconnect()
    assert client.is_connected() is False


@pytest.mark.asyncio
async def test_binance_feature_mounting() -> None:
    """Verify Binance feature mounting."""
    feature_instance = feature()
    assert isinstance(feature_instance, BinanceFeature)
    assert SPEC.provides == frozenset(
        {PROVIDER_BINANCE_CAPABILITY, BROKER_OPERATIONS_CAPABILITY}
    )

    context, registry, scope = _context(feature_instance)

    await feature_instance.mount(
        context,
        BinanceConfig(
            api_key="key",  # pragma: allowlist secret
            api_secret="sec",  # pragma: allowlist secret
        ),
    )
    resolved_ops = registry.resolve(BROKER_OPERATIONS_CAPABILITY)
    assert resolved_ops is feature_instance.client
    assert registry.resolve(PROVIDER_BINANCE_CAPABILITY) is feature_instance.client

    # Verify that mounted client responds to BrokerOperationsCapability
    conn_res = resolved_ops.connect(api_key="test_key", api_secret="test_secret")
    assert conn_res.status == "success"
    assert conn_res.data["connected"] is True
    await scope.close()
