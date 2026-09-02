"""Unit tests for Yahoo Finance broker provider."""

from __future__ import annotations

from typing import Any

import pytest
from app.contracts.broker.capabilities import (
    BROKER_OPERATIONS_CAPABILITY,
    PROVIDER_YAHOO_CAPABILITY,
)
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.brokers.yahoo.client import (
    calculate_margin,
    calculate_profit,
    cancel_order,
    check_order,
    close_position,
    connect,
    disconnect,
    fr_brk_yahoo,
    get_account_info,
    get_account_snapshot,
    get_balances,
    get_connection_status,
    get_deals,
    get_historical_bars,
    get_history_order,
    get_last_error,
    get_order,
    get_orders,
    get_permissions,
    get_platform_info,
    get_position,
    get_positions,
    get_provider_specification,
    get_quote,
    get_spread,
    get_symbol_info,
    get_symbols,
    get_ticks,
    is_connected,
    list_account_transactions,
    list_deal_history,
    list_order_history,
    list_subscriptions,
    modify_order,
    modify_position,
    ping,
    place_order,
    select_symbol,
    subscribe_bars,
    subscribe_quotes,
    subscribe_ticks,
    unsubscribe,
)
from app.services.brokers.yahoo.config import YahooConfig
from app.services.brokers.yahoo.feature import (
    YahooFeature,
    feature,
)
from app.services.brokers.yahoo.manifest import SPEC


def _context(
    feature_instance: YahooFeature,
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


def test_yahoo_connection_and_market_data() -> None:
    """Verify Yahoo Finance market data and unsupported capability exceptions."""
    conn_res = connect()
    assert conn_res["status"] == "connected"
    assert is_connected() is True
    assert ping() > 0.0

    status = get_connection_status()
    assert status["connected"] is True

    p_info = get_platform_info()
    assert p_info["platform"] == "yahoo"

    spec = get_provider_specification()
    assert spec["supports_trading"] is False
    assert spec["supports_quotes"] is True

    symbols = get_symbols()
    assert "AAPL" in symbols

    info = get_symbol_info("AAPL")
    assert info["symbol"] == "AAPL"

    with pytest.raises(ValueError, match="not found"):
        get_symbol_info("NON_EXISTENT_TICKER")

    assert select_symbol("AAPL") is True

    quote = get_quote("AAPL")
    assert quote["bid"] > 0
    assert get_spread("AAPL") >= 0

    bars = get_historical_bars("AAPL", count=5)
    assert len(bars) == 5

    sub_q = subscribe_quotes(["AAPL"])
    subscribe_bars(["AAPL"], "1d")
    assert len(list_subscriptions()) >= 2
    assert unsubscribe(sub_q) is True

    assert get_last_error() == (0, "Success")
    assert fr_brk_yahoo()["platform"] == "yahoo"


def test_yahoo_unsupported_capabilities_raise_not_implemented() -> None:
    """Verify that calling unsupported trading and account capabilities raises NotImplementedError."""
    with pytest.raises(NotImplementedError, match="account:read"):
        get_account_info()

    with pytest.raises(NotImplementedError, match="account:balances"):
        get_balances()

    with pytest.raises(NotImplementedError, match="account:snapshot"):
        get_account_snapshot()

    perms = get_permissions()
    assert "quotes:read" in perms

    with pytest.raises(NotImplementedError, match="ticks:stream"):
        get_ticks("AAPL")

    with pytest.raises(NotImplementedError, match="subscriptions:ticks"):
        subscribe_ticks(["AAPL"])

    with pytest.raises(NotImplementedError, match="orders:get"):
        get_orders()

    with pytest.raises(NotImplementedError, match="orders:get"):
        get_order("101")

    with pytest.raises(NotImplementedError, match="orders:check"):
        check_order({"symbol": "AAPL"})

    with pytest.raises(NotImplementedError, match="orders:history"):
        list_order_history()

    with pytest.raises(NotImplementedError, match="orders:history"):
        get_history_order("101")

    with pytest.raises(NotImplementedError, match="deals:get"):
        get_deals()

    with pytest.raises(NotImplementedError, match="deals:history"):
        list_deal_history()

    with pytest.raises(NotImplementedError, match="transactions:list"):
        list_account_transactions()

    with pytest.raises(NotImplementedError, match="positions:get"):
        get_positions()

    with pytest.raises(NotImplementedError, match="positions:get"):
        get_position("101")

    with pytest.raises(NotImplementedError, match="orders:place"):
        place_order({"symbol": "AAPL"})

    with pytest.raises(NotImplementedError, match="orders:modify"):
        modify_order({"order_id": "101"})

    with pytest.raises(NotImplementedError, match="orders:cancel"):
        cancel_order("101")

    with pytest.raises(NotImplementedError, match="positions:modify"):
        modify_position({"position_id": "101"})

    with pytest.raises(NotImplementedError, match="positions:close"):
        close_position("101")

    with pytest.raises(NotImplementedError, match="margin:calculate"):
        calculate_margin({})

    with pytest.raises(NotImplementedError, match="profit:calculate"):
        calculate_profit({})

    disconnect()
    assert is_connected() is False


@pytest.mark.asyncio
async def test_yahoo_feature_mounting() -> None:
    """Verify Yahoo Finance feature mounting."""
    feature_instance = feature()
    assert isinstance(feature_instance, YahooFeature)
    assert SPEC.provides == frozenset(
        {PROVIDER_YAHOO_CAPABILITY, BROKER_OPERATIONS_CAPABILITY}
    )

    context, registry, scope = _context(feature_instance)

    await feature_instance.mount(context, YahooConfig())
    assert registry.resolve(PROVIDER_YAHOO_CAPABILITY) is feature_instance.service
    assert registry.resolve(BROKER_OPERATIONS_CAPABILITY) is feature_instance.service
    await scope.close()
