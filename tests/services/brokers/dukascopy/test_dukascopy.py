"""Unit tests for Dukascopy broker provider."""

from __future__ import annotations

from typing import Any

import pytest
from app.contracts.broker.capabilities import (
    BROKER_OPERATIONS_CAPABILITY,
    PROVIDER_DUKASCOPY_CAPABILITY,
)
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.brokers.dukascopy.client import (
    calculate_margin,
    calculate_profit,
    cancel_order,
    check_order,
    close_position,
    connect,
    disconnect,
    fr_brk_dukascopy,
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
from app.services.brokers.dukascopy.config import DukascopyConfig
from app.services.brokers.dukascopy.feature import (
    DukascopyFeature,
    feature,
)
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


def test_dukascopy_connection_and_account() -> None:
    """Verify Dukascopy connection, platform info, and account state."""
    with pytest.raises(RuntimeError, match="Missing username or password"):
        connect(username=None, password=None)

    conn_res = connect(
        username="dukas_user",
        password="secret_password",  # pragma: allowlist secret
    )
    assert conn_res["status"] == "connected"
    assert is_connected() is True
    assert ping() > 0.0

    status = get_connection_status()
    assert status["connected"] is True

    p_info = get_platform_info()
    assert p_info["platform"] == "dukascopy"

    spec = get_provider_specification()
    assert spec["provider"] == "dukascopy"

    acc = get_account_info()
    assert acc["balance"] == 25000.0

    balances = get_balances()
    assert balances["currency"] == "USD"

    perms = get_permissions()
    assert "account:read" in perms

    snap = get_account_snapshot()
    assert snap["connected"] is True


def test_dukascopy_market_data() -> None:
    """Verify Dukascopy symbols, quotes, ticks, and bars."""
    connect(
        username="dukas_user",
        password="secret_password",  # pragma: allowlist secret
    )

    symbols = get_symbols()
    assert "EURUSD" in symbols

    info = get_symbol_info("EURUSD")
    assert info["name"] == "EURUSD"

    with pytest.raises(ValueError, match="not found"):
        get_symbol_info("INVALID_SYM")

    assert select_symbol("EURUSD") is True

    quote = get_quote("EURUSD")
    assert quote["bid"] > 0
    assert get_spread("EURUSD") > 0

    ticks = get_ticks("EURUSD", count=5)
    assert len(ticks) == 5

    bars = get_historical_bars("EURUSD", count=5)
    assert len(bars) == 5

    sub_q = subscribe_quotes(["EURUSD"])
    subscribe_ticks(["EURUSD"])
    subscribe_bars(["EURUSD"], "1m")
    assert len(list_subscriptions()) >= 3
    assert unsubscribe(sub_q) is True


def test_dukascopy_orders_and_trading() -> None:
    """Verify Dukascopy orders, positions, and trade calculations."""
    connect(
        username="dukas_user",
        password="secret_password",  # pragma: allowlist secret
    )

    assert get_orders() == []
    assert get_order("101") is None
    assert check_order({"symbol": "EURUSD", "volume": 1.0})["valid"] is True

    assert list_order_history() == []
    assert get_history_order("101") is None

    assert get_deals() == []
    assert list_deal_history() == []
    assert list_account_transactions() == []

    assert get_positions() == []
    assert get_position("101") is None

    order_res = place_order({"symbol": "EURUSD", "volume": 1.0})
    assert order_res["status"] == "ACCEPTED"

    assert modify_order({"order_id": "duk_ord_1001"})["status"] == "MODIFIED"
    assert cancel_order("duk_ord_1001")["status"] == "CANCELLED"
    assert modify_position({"position_id": "duk_pos_1001"})["status"] == "MODIFIED"
    assert close_position("duk_pos_1001")["status"] == "CLOSED"

    assert calculate_margin({"volume": 1.0}) > 0
    assert calculate_profit({"volume": 1.0}) > 0

    assert get_last_error() == (0, "Success")
    assert fr_brk_dukascopy()["platform"] == "dukascopy"

    disconnect()
    assert is_connected() is False


@pytest.mark.asyncio
async def test_dukascopy_feature_mounting(tmp_path: Any) -> None:
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
    assert registry.resolve(PROVIDER_DUKASCOPY_CAPABILITY) is feature_instance.service
    assert registry.resolve(BROKER_OPERATIONS_CAPABILITY) is feature_instance.service
    await scope.close()
