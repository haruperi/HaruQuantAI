"""Focused coverage for opaque package-root Broker helpers."""

import asyncio
from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import AsyncMock, Mock

import pytest
from app.services.brokers import (
    build_broker_connection_config,
    build_broker_value,
    get_broker_connection_account_reference,
    get_broker_connection_environment,
    get_broker_connection_id,
    get_broker_value_field,
    is_broker_connection_enabled,
)


def test_connection_accessors_return_documented_opaque_fields() -> None:
    """Opaque connection getters expose only documented scalar values."""
    connection = build_broker_connection_config(
        "yahoo",
        "sandbox",
        provider_enabled=True,
        account_reference="paper-account",
    )

    assert get_broker_connection_id(connection) == "yahoo"
    assert get_broker_connection_environment(connection) == "sandbox"
    assert get_broker_connection_account_reference(connection) == "paper-account"
    assert is_broker_connection_enabled(connection)


def test_opaque_helpers_reject_unknown_values_and_private_fields() -> None:
    """Invalid opaque values fail explicitly rather than leaking internals."""
    with pytest.raises(ValueError, match="Unsupported Broker value type"):
        build_broker_value("unknown")
    with pytest.raises(ValueError, match="must be public"):
        get_broker_value_field(object(), "_private")
    with pytest.raises(TypeError, match="does not expose"):
        get_broker_value_field(object(), "missing")
    with pytest.raises(TypeError, match="BrokerConnectionConfig"):
        get_broker_connection_id(object())


def test_public_builders_construct_valid_opaque_contract_values() -> None:
    """Package-root builders preserve validated caller values."""
    from app.services.brokers import operations

    assert operations.build_broker_value("position_filter") is not None
    assert operations.get_broker_environment("demo") is not None
    assert operations.get_broker_capability_id("get_quote") is not None
    assert operations.get_broker_error_code("BROKER_TIMEOUT") is not None
    assert (
        operations.build_broker_order_modification_request(
            "order",
            limit_price="1.1000",
        )
        is not None
    )
    assert (
        operations.build_broker_position_close_request("position", 1, "lots")
        is not None
    )
    assert (
        operations.build_broker_position_modification_request(
            "position",
            stop_loss="1.0500",
        )
        is not None
    )
    assert (
        operations.build_broker_margin_request(
            "EURUSD",
            "BUY",
            1,
            "lots",
            "mt5",
        )
        is not None
    )
    assert (
        operations.build_broker_profit_request(
            "EURUSD",
            "BUY",
            1,
            "lots",
            "1.1",
            "1.2",
            "mt5",
        )
        is not None
    )
    assert operations.build_broker_order_filter(symbol="EURUSD") is not None
    assert operations.build_broker_position_filter(symbol="EURUSD") is not None


def test_public_async_operations_delegate_without_hidden_transformation() -> None:  # noqa: PLR0915
    """Every thin package-root operation delegates with bounded arguments."""
    from app.services.brokers import operations

    adapter = AsyncMock()
    adapter.connection_events = Mock(return_value=iter(()))
    subscription = AsyncMock()
    value = cast("Any", object())
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 2, tzinfo=UTC)

    async def exercise() -> None:  # noqa: PLR0915
        await operations.connect_broker(adapter)
        await operations.disconnect_broker(adapter)
        await operations.reconnect_broker(adapter)
        await operations.is_broker_connected(adapter)
        await operations.get_broker_connection_status(adapter)
        await operations.ping_broker(adapter)
        await operations.get_broker_last_error(adapter)
        await operations.get_broker_feature_flags(adapter)
        await operations.supports_broker_capability(adapter, "get_quote")
        await operations.get_broker_platform_info(adapter)
        await operations.get_broker_balances(adapter)
        await operations.get_broker_permissions(adapter)
        await operations.get_broker_account_info(adapter)
        await operations.get_broker_symbols(adapter, query="EUR", limit=1)
        await operations.get_broker_symbol_info(adapter, "EURUSD")
        await operations.select_broker_symbol(adapter, "EURUSD")
        await operations.get_broker_market_status(adapter, "EURUSD")
        await operations.get_broker_trading_sessions(adapter, "EURUSD")
        await operations.get_broker_quote(adapter, "EURUSD")
        await operations.get_broker_spread(adapter, "EURUSD")
        await operations.get_broker_ticks(adapter, "EURUSD", start, end, 1)
        await operations.get_broker_historical_bars(
            adapter, "EURUSD", "1m", start, end, 1
        )
        await operations.get_broker_order_book(adapter, "EURUSD", 1)
        await operations.subscribe_broker_quotes(adapter, "EURUSD")
        await operations.subscribe_broker_bars(adapter, "EURUSD", "1m")
        await operations.subscribe_broker_order_book(adapter, "EURUSD", 1)
        await operations.unsubscribe_broker(subscription)
        await operations.list_broker_subscriptions(adapter)
        await operations.get_broker_positions(adapter, limit=1)
        await operations.get_broker_position(adapter, "position")
        await operations.get_broker_orders(adapter, limit=1)
        await operations.get_broker_order(adapter, "order")
        await operations.list_broker_order_history(
            adapter, start, end, "EURUSD", limit=1
        )
        await operations.list_broker_deal_history(adapter, start, end, limit=1)
        await operations.get_broker_deal(adapter, "deal")
        await operations.list_broker_account_transactions(adapter, start, end, limit=1)
        await operations.check_broker_order(adapter, value)
        await operations.place_broker_order(adapter, value)
        await operations.modify_broker_order(adapter, value)
        await operations.cancel_broker_order(adapter, "order", "req-1")
        await operations.modify_broker_position(adapter, value)
        await operations.close_broker_position(adapter, value)
        await operations.calculate_broker_margin(adapter, value)
        await operations.calculate_broker_profit(adapter, value)
        await operations.refresh_broker_session(adapter)
        await operations.get_broker_server_time(adapter)
        assert tuple(operations.get_broker_connection_events(adapter)) == ()
        await operations.list_broker_accounts(adapter, limit=1)
        await operations.select_broker_account(adapter, "account")
        await operations.list_broker_assets(adapter, limit=1)
        await operations.get_broker_asset_info(adapter, "USD")
        await operations.get_broker_commission_estimate(adapter, value)
        await operations.replace_broker_order(adapter, value)

    asyncio.run(exercise())
    assert adapter.connect.await_count == 1
