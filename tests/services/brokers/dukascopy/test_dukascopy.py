"""Unit tests for Dukascopy broker provider."""

from __future__ import annotations

from typing import Any

import pytest
from app.contracts.broker.capabilities import (
    BROKER_OPERATIONS_CAPABILITY,
    PROVIDER_DUKASCOPY_CAPABILITY,
)
from app.contracts.broker.dukascopy import resolve_timeframe
from app.contracts.broker.models import (
    BrokerAccountInfo,
    BrokerSymbolInfo,
    BrokerTerminalInfo,
)
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.brokers.dukascopy.client import DukascopyClient
from app.services.brokers.dukascopy.config import DukascopyConfig
from app.services.brokers.dukascopy.feature import DukascopyFeature, feature
from app.services.brokers.dukascopy.manifest import SPEC


def _context(
    feature_instance: DukascopyFeature,
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


def test_dukascopy_client_connection_and_account() -> None:
    """Verify DukascopyClient connection, platform info, and account state."""
    client = DukascopyClient()
    assert client.is_available() is True
    assert client.is_connected() is False

    fail_res = client.connect(username=None, password=None)
    assert fail_res.status == "error"

    conn_res = client.connect(
        username="dukas_user",
        password="secret_password",  # pragma: allowlist secret
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
    assert p_info.data["platform"] == "dukascopy"

    spec = client.get_provider_specification()
    assert spec.data["provider"] == "dukascopy"

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
    assert term_info.data.name == "Dukascopy"
    assert term_info.data["name"] == "Dukascopy"


def test_dukascopy_market_data() -> None:
    """Verify DukascopyClient symbols, quotes, ticks, and bars."""
    client = DukascopyClient()
    client.connect(
        username="dukas_user",
        password="secret_password",  # pragma: allowlist secret
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


def test_dukascopy_orders_and_trading() -> None:
    """Verify DukascopyClient orders, positions, and trade calculations."""
    client = DukascopyClient()
    client.connect(
        username="dukas_user",
        password="secret_password",  # pragma: allowlist secret
    )

    assert client.get_orders() == []
    assert client.get_order_info().status == "success"
    assert client.get_num_orders().data == 0
    assert client.get_order("101") is None
    assert client.check_order({"symbol": "EURUSD", "volume": 1.0}).data["valid"] is True

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

    trade_res = client.trade({"symbol": "EURUSD", "volume": 1.0})
    assert trade_res.status == "success"
    assert trade_res.data["status"] == "ACCEPTED"

    order_res = client.place_order({"symbol": "EURUSD", "volume": 1.0})
    assert order_res["status"] == "ACCEPTED"

    assert client.modify_order({"order_id": "duk_ord_1001"})["status"] == "SUCCESS"
    assert client.cancel_order("duk_ord_1001")["status"] == "CANCELED"
    assert (
        client.modify_position({"position_id": "duk_pos_1001"})["status"] == "SUCCESS"
    )
    assert client.close_position("duk_pos_1001")["status"] == "CLOSED"

    margin_res = client.calculate_margin({"volume": 1.0, "price": 1.0850})
    assert margin_res.status == "success"
    assert margin_res.data > 0

    profit_res = client.calculate_profit(
        {"volume": 1.0, "price_open": 1.0850, "price_close": 1.0860}
    )
    assert profit_res.status == "success"
    assert profit_res.data > 0

    assert client.get_last_error() == (0, "Success")
    assert resolve_timeframe("1m") == "1m"
    assert resolve_timeframe("H1") == "1h"

    client.disconnect()
    assert client.is_connected() is False


@pytest.mark.asyncio
async def test_dukascopy_feature_mounting() -> None:
    """Verify Dukascopy feature mounting."""
    feature_instance = feature()
    assert isinstance(feature_instance, DukascopyFeature)
    assert SPEC.provides == frozenset(
        {PROVIDER_DUKASCOPY_CAPABILITY, BROKER_OPERATIONS_CAPABILITY}
    )

    context, registry, scope = _context(feature_instance)

    await feature_instance.mount(
        context,
        DukascopyConfig(
            username="demo",
            password="pwd",  # pragma: allowlist secret
        ),
    )
    resolved_ops = registry.resolve(BROKER_OPERATIONS_CAPABILITY)
    assert resolved_ops is feature_instance.client
    assert registry.resolve(PROVIDER_DUKASCOPY_CAPABILITY) is feature_instance.client

    # Verify that mounted client responds to BrokerOperationsCapability
    conn_res = resolved_ops.connect(
        username="demo",
        password="pwd",  # pragma: allowlist secret
    )
    assert conn_res.status == "success"
    assert conn_res.data["connected"] is True
    await scope.close()
