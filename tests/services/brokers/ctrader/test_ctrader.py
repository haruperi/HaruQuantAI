"""Unit tests for cTrader broker provider."""

from __future__ import annotations

from typing import Any

import pytest
from app.contracts.broker.capabilities import (
    BROKER_OPERATIONS_CAPABILITY,
    PROVIDER_CTRADER_CAPABILITY,
)
from app.contracts.broker.ctrader import resolve_timeframe
from app.contracts.broker.models import (
    BrokerAccountInfo,
    BrokerSymbolInfo,
    BrokerTerminalInfo,
)
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.brokers.ctrader.client import CTraderClient
from app.services.brokers.ctrader.config import CTraderConfig
from app.services.brokers.ctrader.feature import CTraderFeature, feature
from app.services.brokers.ctrader.manifest import SPEC


def _context(
    feature_instance: CTraderFeature,
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


def test_ctrader_client_connection_and_account() -> None:
    """Verify CTraderClient connection, environment, and account data."""
    client = CTraderClient()
    assert client.is_available() is True
    assert client.is_connected() is False

    # Fails when missing credentials
    fail_res = client.connect(client_id=None, client_secret=None, access_token=None)
    assert fail_res.status == "error"

    conn_res = client.connect(
        client_id="id_1",
        client_secret="sec_1",  # pragma: allowlist secret
        access_token="tok_1",  # pragma: allowlist secret
    )
    assert conn_res.status == "success"
    assert conn_res.data["status"] == "connected"
    assert conn_res.data["connected"] is True
    assert client.is_connected() is True
    assert client.ping() > 0.0

    status = client.get_connection_status()
    assert status.status == "success"
    assert status.data["connected"] is True

    p_info = client.get_platform_info()
    assert p_info.data["platform"] == "ctrader"

    spec = client.get_provider_specification()
    assert spec.data["provider"] == "ctrader"

    acc = client.get_account_info()
    assert acc.status == "success"
    assert isinstance(acc.data, BrokerAccountInfo)
    assert acc.data.currency == "USD"
    assert acc.data["currency"] == "USD"

    balances = client.get_balances()
    assert balances.status == "success"
    assert balances.data["currency"] == "USD"

    perms = client.get_permissions()
    assert "FOREX" in perms

    snap = client.get_account_snapshot()
    assert snap.status == "success"
    assert snap.data["connected"] is True

    term_info = client.get_terminal_info()
    assert term_info.status == "success"
    assert isinstance(term_info.data, BrokerTerminalInfo)
    assert term_info.data.name == "cTrader"
    assert term_info.data["name"] == "cTrader"


def test_ctrader_market_data() -> None:
    """Verify CTraderClient symbols, quotes, ticks, and trendbars."""
    client = CTraderClient()
    client.connect(
        client_id="id_1",
        client_secret="sec_1",  # pragma: allowlist secret
        access_token="tok_1",  # pragma: allowlist secret
    )

    symbols_res = client.get_symbols()
    assert symbols_res.status == "success"
    assert len(symbols_res.data) > 0
    assert any(s.symbol == "EURUSD" for s in symbols_res.data)

    num_symbols = client.get_num_of_symbols()
    assert num_symbols.status == "success"
    assert num_symbols.data > 0

    info = client.get_symbol_info("EURUSD")
    assert info.status == "success"
    assert isinstance(info.data, BrokerSymbolInfo)
    assert info.data.symbol == "EURUSD"
    assert info.data["symbol"] == "EURUSD"

    bad_info = client.get_symbol_info("INVALID_SYM")
    assert bad_info.status == "error"

    assert client.enable_symbol("EURUSD").status == "success"
    assert client.select_symbol("EURUSD") is True

    tick_res = client.get_symbol_tick("EURUSD")
    assert tick_res.status == "success"
    assert tick_res.data["bid"] > 0

    quote = client.get_quote("EURUSD")
    assert quote["bid"] > 0
    assert client.get_spread("EURUSD") > 0

    ticks = client.get_ticks("EURUSD", count=5)
    assert ticks.status == "success"
    assert len(ticks.data) == 5
    assert ticks.data.index.name == "DateTime"
    assert list(ticks.data.columns) == ["Bid", "Ask", "Volume"]

    bars = client.get_bars("EURUSD", count=5)
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

    depth_sub = client.subscribe_market_depth("EURUSD")
    assert depth_sub.status == "success"
    depth = client.get_market_depth("EURUSD")
    assert depth.status == "success"
    assert len(depth.data) > 0
    depth_unsub = client.unsubscribe_market_depth("EURUSD")
    assert depth_unsub.status == "success"

    sub_q = client.subscribe_quotes(["EURUSD"])
    client.subscribe_ticks(["EURUSD"])
    client.subscribe_bars(["EURUSD"], "1m")
    assert len(client.list_subscriptions()) >= 3
    assert client.unsubscribe(sub_q) is True


def test_ctrader_orders_and_trading() -> None:
    """Verify CTraderClient orders, positions, and trade calculations."""
    client = CTraderClient()
    client.connect(
        client_id="id_1",
        client_secret="sec_1",  # pragma: allowlist secret
        access_token="tok_1",  # pragma: allowlist secret
    )

    assert client.get_orders() == []
    assert client.get_order_info().status == "success"
    assert client.get_num_orders().data == 0
    assert client.get_order("101") is None
    assert (
        client.check_order({"symbol": "EURUSD", "volume": 1000}).data["valid"] is True
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

    trade_res = client.trade({"symbol": "EURUSD", "volume": 1000})
    assert trade_res.status == "success"
    assert trade_res.data["status"] == "EXECUTED"

    order_res = client.place_order({"symbol": "EURUSD", "volume": 1000})
    assert order_res["status"] == "EXECUTED"

    assert client.modify_order({"orderId": 839102})["status"] == "SUCCESS"
    assert client.cancel_order("839102")["status"] == "CANCELED"
    assert client.modify_position({"positionId": 918231})["status"] == "SUCCESS"
    assert client.close_position("918231")["status"] == "CLOSED"

    margin_res = client.calculate_margin({"volume": 1.0, "price": 1.0850})
    assert margin_res.status == "success"
    assert margin_res.data > 0

    profit_res = client.calculate_profit(
        {"volume": 1.0, "price_open": 1.0850, "price_close": 1.0860}
    )
    assert profit_res.status == "success"
    assert profit_res.data > 0

    assert client.get_last_error() == (0, "Success")
    assert resolve_timeframe("1m") == "m1"
    assert resolve_timeframe("H1") == "h1"

    client.disconnect()
    assert client.is_connected() is False


@pytest.mark.asyncio
async def test_ctrader_feature_mounting() -> None:
    """Verify cTrader feature mounting."""
    feature_instance = feature()
    assert isinstance(feature_instance, CTraderFeature)
    assert SPEC.provides == frozenset(
        {PROVIDER_CTRADER_CAPABILITY, BROKER_OPERATIONS_CAPABILITY}
    )

    context, registry, scope = _context(feature_instance)

    await feature_instance.mount(
        context,
        CTraderConfig(
            client_id="cid",
            client_secret="sec",  # pragma: allowlist secret
            access_token="tok",  # pragma: allowlist secret
        ),
    )
    resolved_ops = registry.resolve(BROKER_OPERATIONS_CAPABILITY)
    assert resolved_ops is feature_instance.client
    assert registry.resolve(PROVIDER_CTRADER_CAPABILITY) is feature_instance.client

    # Verify that mounted client responds to BrokerOperationsCapability
    conn_res = resolved_ops.connect(
        client_id="cid",
        client_secret="sec",  # pragma: allowlist secret
        access_token="tok",  # pragma: allowlist secret
    )
    assert conn_res.status == "success"
    assert conn_res.data["connected"] is True
    await scope.close()
