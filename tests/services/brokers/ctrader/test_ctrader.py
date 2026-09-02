"""Unit tests for cTrader broker provider."""

from __future__ import annotations

from typing import Any

import pytest
from app.contracts.broker.capabilities import (
    BROKER_OPERATIONS_CAPABILITY,
    PROVIDER_CTRADER_CAPABILITY,
)
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.brokers.ctrader.client import (
    calculate_margin,
    calculate_profit,
    cancel_order,
    check_order,
    close_position,
    connect,
    disconnect,
    fr_brk_ctrader,
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
from app.services.brokers.ctrader.config import CTraderConfig
from app.services.brokers.ctrader.feature import (
    CTraderFeature,
    feature,
)
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


def test_ctrader_connection_and_account() -> None:
    """Verify cTrader connection, environment, and account data."""
    with pytest.raises(
        RuntimeError, match="Missing client_id, client_secret, or access_token"
    ):
        connect(client_id=None, client_secret=None, access_token=None)

    conn_res = connect(
        client_id="id_1",
        client_secret="sec_1",  # pragma: allowlist secret
        access_token="tok_1",  # pragma: allowlist secret
    )
    assert conn_res["status"] == "connected"
    assert is_connected() is True
    assert ping() > 0.0

    status = get_connection_status()
    assert status["connected"] is True

    p_info = get_platform_info()
    assert p_info["platform"] == "ctrader"

    spec = get_provider_specification()
    assert spec["provider"] == "ctrader"

    acc = get_account_info()
    assert acc["balance"] == 100000.0

    balances = get_balances()
    assert balances["currency"] == "USD"

    perms = get_permissions()
    assert "trading:execute" in perms

    snap = get_account_snapshot()
    assert snap["connected"] is True


def test_ctrader_market_data() -> None:
    """Verify cTrader symbols, quotes, ticks, and trendbars."""
    connect(
        client_id="id_1",
        client_secret="sec_1",  # pragma: allowlist secret
        access_token="tok_1",  # pragma: allowlist secret
    )

    symbols = get_symbols()
    assert "EURUSD" in symbols

    info = get_symbol_info("EURUSD")
    assert info["symbolName"] == "EURUSD"

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


def test_ctrader_orders_and_trading() -> None:
    """Verify cTrader orders, positions, and trade calculations."""
    connect(
        client_id="id_1",
        client_secret="sec_1",  # pragma: allowlist secret
        access_token="tok_1",  # pragma: allowlist secret
    )

    assert get_orders() == []
    assert get_order("101") is None
    assert check_order({"symbol": "EURUSD", "volume": 1000})["valid"] is True

    assert list_order_history() == []
    assert get_history_order("101") is None

    assert get_deals() == []
    assert list_deal_history() == []
    assert list_account_transactions() == []

    assert get_positions() == []
    assert get_position("101") is None

    order_res = place_order({"symbol": "EURUSD", "volume": 1000})
    assert order_res["status"] == "ACCEPTED"

    assert modify_order({"orderId": 839102})["status"] == "MODIFIED"
    assert cancel_order("839102")["status"] == "CANCELLED"
    assert modify_position({"positionId": 918231})["status"] == "MODIFIED"
    assert close_position("918231")["status"] == "CLOSED"

    assert calculate_margin({"volume": 1.0}) > 0
    assert calculate_profit({"volume": 1.0}) > 0

    assert get_last_error() == (0, "Success")
    assert fr_brk_ctrader()["platform"] == "ctrader"

    disconnect()
    assert is_connected() is False


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
    assert registry.resolve(PROVIDER_CTRADER_CAPABILITY) is feature_instance.service
    assert registry.resolve(BROKER_OPERATIONS_CAPABILITY) is feature_instance.service
    await scope.close()
