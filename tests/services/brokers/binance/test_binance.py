"""Unit tests for Binance broker provider."""

from __future__ import annotations

from typing import Any

import pytest
from app.contracts.broker.capabilities import (
    BROKER_OPERATIONS_CAPABILITY,
    PROVIDER_BINANCE_CAPABILITY,
)
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.brokers.binance.client import (
    calculate_margin,
    calculate_profit,
    cancel_order,
    check_order,
    close_position,
    connect,
    disconnect,
    fr_brk_binance,
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
from app.services.brokers.binance.config import BinanceConfig
from app.services.brokers.binance.feature import (
    BinanceFeature,
    feature,
)
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


def test_binance_connection_and_account() -> None:
    """Verify Binance connection, environment, and account data."""
    connect(api_key=None, api_secret=None)
    with pytest.raises(RuntimeError, match="Missing API key or secret"):
        get_account_info()

    conn_res = connect(
        api_key="key_123",  # pragma: allowlist secret
        api_secret="sec_123",  # pragma: allowlist secret
        testnet=True,
    )
    assert conn_res["status"] == "connected"
    assert is_connected() is True
    assert ping() > 0.0

    status = get_connection_status()
    assert status["connected"] is True

    p_info = get_platform_info()
    assert p_info["platform"] == "binance"

    spec = get_provider_specification()
    assert spec["provider"] == "binance"
    assert spec["supports_spot"] is True

    acc = get_account_info()
    assert acc["account_type"] == "SPOT"

    balances = get_balances()
    assert balances["currency"] == "USDT"

    perms = get_permissions()
    assert "SPOT" in perms

    snap = get_account_snapshot()
    assert snap["connected"] is True


def test_binance_market_data() -> None:
    """Verify Binance symbols, quotes, ticks, and streams."""
    connect(
        api_key="key_123",  # pragma: allowlist secret
        api_secret="sec_123",  # pragma: allowlist secret
    )

    symbols = get_symbols()
    assert "BTCUSDT" in symbols

    info = get_symbol_info("BTCUSDT")
    assert info["symbol"] == "BTCUSDT"

    with pytest.raises(ValueError, match="not found"):
        get_symbol_info("INVALID_CRYPTO")

    assert select_symbol("BTCUSDT") is True

    quote = get_quote("BTCUSDT")
    assert quote["bid"] > 0
    assert get_spread("BTCUSDT") > 0

    ticks = get_ticks("BTCUSDT", count=5)
    assert len(ticks) == 5

    bars = get_historical_bars("BTCUSDT", count=5)
    assert len(bars) == 5

    sub_q = subscribe_quotes(["BTCUSDT"])
    subscribe_ticks(["BTCUSDT"])
    subscribe_bars(["BTCUSDT"], "1m")
    assert len(list_subscriptions()) >= 3
    assert unsubscribe(sub_q) is True


def test_binance_orders_and_trading() -> None:
    """Verify Binance orders, positions, and execution calculations."""
    connect(
        api_key="key_123",  # pragma: allowlist secret
        api_secret="sec_123",  # pragma: allowlist secret
    )

    assert get_orders() == []
    assert get_order("101") is None
    assert check_order({"symbol": "BTCUSDT", "volume": 1.0})["valid"] is True

    assert list_order_history() == []
    assert get_history_order("101") is None

    assert get_deals() == []
    assert list_deal_history() == []
    assert list_account_transactions() == []

    assert get_positions() == []
    assert get_position("101") is None

    order_res = place_order({"symbol": "BTCUSDT", "volume": 0.1})
    assert order_res["status"] == "FILLED"

    assert modify_order({"orderId": 2831924})["status"] == "SUCCESS"
    assert cancel_order("2831924")["status"] == "CANCELED"
    assert modify_position({"symbol": "BTCUSDT"})["status"] == "SUCCESS"
    assert close_position("pos_101")["status"] == "CLOSED"

    assert calculate_margin({"volume": 1.0, "price": 65000.0, "leverage": 10}) == 6500.0
    assert (
        calculate_profit({"volume": 1.0, "price_open": 65000.0, "price_close": 66000.0})
        == 1000.0
    )

    assert get_last_error() == (0, "Success")
    assert fr_brk_binance()["platform"] == "binance"

    disconnect()
    assert is_connected() is False


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
    assert registry.resolve(PROVIDER_BINANCE_CAPABILITY) is feature_instance.service
    assert registry.resolve(BROKER_OPERATIONS_CAPABILITY) is feature_instance.service
    await scope.close()
