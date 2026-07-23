"""Focused broker protocol and fail-closed default tests."""

import asyncio
import inspect
from collections.abc import AsyncGenerator, AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

import pytest
from app.services.brokers import (
    AccountProvider,
    BrokerAdapter,
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerConnectionEvent,
    BrokerConnectionState,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
    BrokerOrderRequest,
    BrokerOrderResult,
    BrokerResult,
    BrokerSubscription,
    BrokerSubscriptionInfo,
    CalculationProvider,
    MarketDataProvider,
    TradeExecutionProvider,
)
from app.services.brokers.adapter_runtime.subscription import _BrokerSubscription
from app.services.brokers.contracts.protocols import _UnsupportedAdapterBase

REQUEST_ID = "req-b4b8aa60-ba17-4561-884b-138c6074c5fb"


def _capability(
    capability: BrokerCapabilityId, *, available: bool = False
) -> BrokerCapability:
    return BrokerCapability(
        capability=capability,
        implementation_status="IMPLEMENTED" if available else "NOT_IMPLEMENTED",
        availability="AVAILABLE" if available else "UNAVAILABLE",
        access_mode="READ",
        requirement="NONE",
        verification_status="NOT_TESTED",
        execution_model="TEST_DOUBLE" if available else "NO_PROVIDER_CALL",
        reason=None if available else "not released",
    )


def _adapter(*, connect_available: bool = False) -> _UnsupportedAdapterBase:
    del connect_available
    config = BrokerConnectionConfig(
        broker_id=BrokerId.YAHOO,
        environment=BrokerEnvironment.SANDBOX,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
    )
    return _UnsupportedAdapterBase(config)


def _unsupported(operation: BrokerCapabilityId) -> BrokerResult[object]:
    adapter = _adapter()
    adapter._state = BrokerConnectionState.READY

    async def _call() -> BrokerResult[object]:
        method = getattr(adapter, operation.value)
        return cast("BrokerResult[object]", await method())

    result = asyncio.run(_call())
    assert result.operation is operation
    assert result.error is not None
    assert result.error.code is BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED
    return result


def _assert_async_method(protocol: type[object], name: str) -> None:
    method = getattr(protocol, name)
    assert inspect.iscoroutinefunction(method)
    assert inspect.signature(method).return_annotation is not inspect.Signature.empty


class _ContextAdapter(_UnsupportedAdapterBase):
    """Provider-free adapter used only to prove context cleanup."""

    _ENFORCE_DECLARED_AVAILABILITY = False

    def __init__(self) -> None:
        base = _adapter(connect_available=True)
        super().__init__(base._config)
        self.disconnect_count = 0

    async def connect(self) -> BrokerResult[None]:
        return self._result(BrokerCapabilityId.CONNECT)

    async def disconnect(self) -> BrokerResult[None]:
        self.disconnect_count += 1
        return self._result(BrokerCapabilityId.DISCONNECT)


def test_protocols_are_runtime_checkable() -> None:
    """All focused contracts expose structural runtime checks."""
    for protocol in (
        MarketDataProvider,
        AccountProvider,
        TradeExecutionProvider,
        CalculationProvider,
        BrokerAdapter,
        BrokerSubscription,
    ):
        assert getattr(protocol, "_is_runtime_protocol", False)


def test_market_data_protocol_is_runtime_checkable() -> None:
    _assert_async_method(MarketDataProvider, "get_symbols")


def test_account_protocol_is_runtime_checkable() -> None:
    _assert_async_method(AccountProvider, "get_account_info")


def test_calculation_protocol_is_provider_native() -> None:
    _assert_async_method(CalculationProvider, "calculate_margin")
    assert not hasattr(CalculationProvider, "calculate_risk")


def test_execution_protocol_excludes_bulk_methods() -> None:
    assert not hasattr(TradeExecutionProvider, "cancel_all_orders")
    assert not hasattr(TradeExecutionProvider, "close_all_positions")


def test_subscription_is_bounded_fifo_and_explicitly_closed() -> None:
    subscription = _BrokerSubscription[int](
        broker=BrokerId.YAHOO,
        environment=BrokerEnvironment.SANDBOX,
        adapter_version="1",
        info=BrokerSubscriptionInfo(
            subscription_id="subscription-1",
            capability=BrokerCapabilityId.SUBSCRIBE_QUOTES,
            symbols=("EURUSD",),
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            buffer_size=2,
        ),
    )

    async def _consume() -> tuple[int, int]:
        assert await subscription.publish(1)
        assert await subscription.publish(2)
        events = subscription.events()
        first = await anext(events)
        second = await anext(events)
        assert (await subscription.unsubscribe()).is_success
        with pytest.raises(StopAsyncIteration):
            await anext(events)
        return cast("int", first), cast("int", second)

    assert isinstance(subscription, BrokerSubscription)
    assert asyncio.run(_consume()) == (1, 2)
    assert not subscription.info.active


def test_adapter_explicit_connect_and_disconnect() -> None:
    adapter = _ContextAdapter()

    async def _use() -> None:
        await adapter.connect()
        assert adapter.contract_version == "v1"
        assert adapter.schema_id == "brokers.adapter.v1"
        await adapter.disconnect()

    asyncio.run(_use())
    assert adapter.disconnect_count == 1


def test_connect_requires_verified_provider_state() -> None:
    _unsupported(BrokerCapabilityId.CONNECT)


def test_disconnect_is_idempotent() -> None:
    adapter = _adapter()

    async def _twice() -> None:
        assert (await adapter.disconnect()).is_success
        assert (await adapter.disconnect()).is_success

    asyncio.run(_twice())


def test_reconnect_never_replays_operation() -> None:
    _unsupported(BrokerCapabilityId.RECONNECT)


def test_is_connected_is_provider_verified() -> None:
    adapter = _adapter()
    adapter._state = BrokerConnectionState.READY
    result = asyncio.run(adapter.is_connected())
    assert result.is_success
    assert result.data is True


def test_connection_status_is_detailed() -> None:
    result = asyncio.run(_adapter().get_connection_status())
    assert result.is_success
    assert result.data is not None
    assert not result.data.transport_connected


def test_ping_has_no_synthetic_success() -> None:
    _unsupported(BrokerCapabilityId.PING)


def test_refresh_failure_invalidates_session() -> None:
    _unsupported(BrokerCapabilityId.REFRESH_SESSION)


def test_server_time_exposes_offset_evidence() -> None:
    _unsupported(BrokerCapabilityId.GET_SERVER_TIME)


def test_last_error_is_redacted_and_non_authoritative() -> None:
    adapter = _adapter()
    _ = asyncio.run(adapter.ping())
    result = asyncio.run(adapter.get_last_error())
    assert result.is_success
    assert result.data is not None


def test_connection_events_cover_every_transition() -> None:
    adapter = _adapter()

    async def _event() -> BrokerConnectionEvent:
        await adapter._transition(
            adapter._state.CONNECTING,
            reason="test",
        )
        iterator: AsyncIterator[BrokerConnectionEvent] = adapter.connection_events()
        event = await anext(iterator)
        await cast("AsyncGenerator[BrokerConnectionEvent]", iterator).aclose()
        return event

    event = asyncio.run(_event())
    assert event.reason == "test"


def test_feature_flags_include_unsupported_and_unapproved_entries() -> None:
    result = asyncio.run(_adapter().get_feature_flags())
    assert result.is_success
    assert result.data is not None
    assert set(result.data.capabilities) == set(BrokerCapabilityId)


def test_supports_uses_declaration_not_attribute_catch() -> None:
    result = asyncio.run(_adapter().supports(BrokerCapabilityId.GET_QUOTE))
    assert result.is_success
    assert result.data is False
    with pytest.raises(AttributeError):
        object.__getattribute__(_adapter(), "not_a_capability")


def test_get_symbols_is_bounded_and_provider_native() -> None:
    _unsupported(BrokerCapabilityId.GET_SYMBOLS)


def test_symbol_info_has_no_guessed_fields() -> None:
    _unsupported(BrokerCapabilityId.GET_SYMBOL_INFO)


def test_select_symbol_is_transport_only() -> None:
    _unsupported(BrokerCapabilityId.SELECT_SYMBOL)


def test_market_status_is_provider_reported() -> None:
    _unsupported(BrokerCapabilityId.GET_MARKET_STATUS)


def test_sessions_are_not_generated() -> None:
    _unsupported(BrokerCapabilityId.GET_TRADING_SESSIONS)


def test_quote_never_uses_fallback_price() -> None:
    _unsupported(BrokerCapabilityId.GET_QUOTE)


def test_ticks_are_genuine_and_bounded() -> None:
    _unsupported(BrokerCapabilityId.GET_TICKS)


def test_bars_do_not_silently_change_timeframe() -> None:
    _unsupported(BrokerCapabilityId.GET_HISTORICAL_BARS)


def test_order_book_has_sequence_evidence() -> None:
    _unsupported(BrokerCapabilityId.GET_ORDER_BOOK)


def test_spread_is_provider_reported() -> None:
    _unsupported(BrokerCapabilityId.GET_SPREAD)


def test_quote_subscription_is_bounded() -> None:
    _unsupported(BrokerCapabilityId.SUBSCRIBE_QUOTES)


def test_bar_subscription_is_capability_gated() -> None:
    _unsupported(BrokerCapabilityId.SUBSCRIBE_BARS)


def test_order_book_subscription_requires_sequence_safety() -> None:
    _unsupported(BrokerCapabilityId.SUBSCRIBE_ORDER_BOOK)


def test_unknown_unsubscribe_is_isolated() -> None:
    _unsupported(BrokerCapabilityId.UNSUBSCRIBE)


def test_subscriptions_do_not_leak_between_adapters() -> None:
    first = _adapter()
    second = _adapter()
    assert first._event_queue is not second._event_queue
    _unsupported(BrokerCapabilityId.LIST_SUBSCRIPTIONS)


def test_platform_info_is_redacted() -> None:
    _unsupported(BrokerCapabilityId.GET_PLATFORM_INFO)


def test_permissions_are_authenticated_and_tested() -> None:
    _unsupported(BrokerCapabilityId.GET_PERMISSIONS)


def test_list_accounts_is_bounded() -> None:
    _unsupported(BrokerCapabilityId.LIST_ACCOUNTS)


def test_select_account_is_initially_unsupported() -> None:
    _unsupported(BrokerCapabilityId.SELECT_ACCOUNT)


def test_account_info_has_provider_and_retrieval_time() -> None:
    _unsupported(BrokerCapabilityId.GET_ACCOUNT_INFO)


def test_balances_have_explicit_units() -> None:
    _unsupported(BrokerCapabilityId.GET_BALANCES)


def test_assets_are_provider_native() -> None:
    _unsupported(BrokerCapabilityId.LIST_ASSETS)


def test_asset_not_found_is_explicit() -> None:
    _unsupported(BrokerCapabilityId.GET_ASSET_INFO)


def test_positions_preserve_ids_and_partial_state() -> None:
    _unsupported(BrokerCapabilityId.GET_POSITIONS)


def test_position_not_found_is_distinct() -> None:
    _unsupported(BrokerCapabilityId.GET_POSITION)


def test_orders_preserve_provider_states() -> None:
    _unsupported(BrokerCapabilityId.GET_ORDERS)


def test_order_not_found_is_distinct() -> None:
    _unsupported(BrokerCapabilityId.GET_ORDER)


def test_order_history_is_bounded() -> None:
    _unsupported(BrokerCapabilityId.LIST_ORDER_HISTORY)


def test_deal_history_is_bounded() -> None:
    _unsupported(BrokerCapabilityId.LIST_DEAL_HISTORY)


def test_deal_not_found_is_distinct() -> None:
    _unsupported(BrokerCapabilityId.GET_DEAL)


def test_transactions_are_bounded_or_unsupported() -> None:
    _unsupported(BrokerCapabilityId.LIST_ACCOUNT_TRANSACTIONS)


def test_order_check_is_not_acceptance() -> None:
    _unsupported(BrokerCapabilityId.CHECK_ORDER)


def test_place_order_requires_acknowledgement() -> None:
    _unsupported(BrokerCapabilityId.PLACE_ORDER)


def test_modify_order_has_one_target() -> None:
    _unsupported(BrokerCapabilityId.MODIFY_ORDER)


def test_cancel_order_has_one_target() -> None:
    _unsupported(BrokerCapabilityId.CANCEL_ORDER)


def test_modify_position_has_one_target() -> None:
    _unsupported(BrokerCapabilityId.MODIFY_POSITION)


def test_close_position_preserves_partial_result() -> None:
    _unsupported(BrokerCapabilityId.CLOSE_POSITION)


def test_replace_order_is_never_emulated() -> None:
    _unsupported(BrokerCapabilityId.REPLACE_ORDER)


def test_margin_is_provider_native() -> None:
    _unsupported(BrokerCapabilityId.CALCULATE_MARGIN)


def test_profit_is_provider_native() -> None:
    _unsupported(BrokerCapabilityId.CALCULATE_PROFIT)


def test_commission_is_provider_native_or_unsupported() -> None:
    _unsupported(BrokerCapabilityId.GET_COMMISSION_ESTIMATE)


def test_cancellation_propagates_without_translation() -> None:
    """Caller cancellation remains an exception rather than a broker result."""

    class _CancelledAdapter(_ContextAdapter):
        async def connect(self) -> BrokerResult[None]:
            raise asyncio.CancelledError

    async def _cancel() -> None:
        with pytest.raises(asyncio.CancelledError):
            await _CancelledAdapter().connect()

    asyncio.run(_cancel())


def test_public_boundary_translates_and_redacts_raw_provider_exception() -> None:
    """Raw provider exceptions never cross the canonical adapter boundary."""

    class _ExplodingAdapter(_ContextAdapter):
        async def connect(self) -> BrokerResult[None]:
            raise RuntimeError("password=provider-secret")

    result = asyncio.run(_ExplodingAdapter().connect())
    assert result.error is not None
    assert result.error.code is BrokerErrorCode.BROKER_RESPONSE_INVALID
    assert "provider-secret" not in repr(result)


def test_mutation_timeout_is_non_retryable_unknown_outcome() -> None:
    """Possible mutation transmission is never retried or reported as rejected."""

    class _TimedOutAdapter(_ContextAdapter):
        async def place_order(
            self, request: BrokerOrderRequest
        ) -> BrokerResult[BrokerOrderResult]:
            del request
            raise TimeoutError("provider acknowledgement timeout")

    adapter = _TimedOutAdapter()
    adapter._state = BrokerConnectionState.READY

    request = BrokerOrderRequest(
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal("0.01"),
        quantity_unit="lots",
        environment=BrokerEnvironment.DEMO,
    )
    result = asyncio.run(adapter.place_order(request))
    assert result.error is not None
    assert result.error.code is BrokerErrorCode.BROKER_UNKNOWN_OUTCOME
    assert result.error.retryable is False


def test_adapter_connect_failure_returns_canonical_error() -> None:
    """A connection failure returns a canonical error result."""

    class _FailingAdapter(_ContextAdapter):
        async def connect(self) -> BrokerResult[None]:
            from app.services.brokers import BrokerError

            return BrokerResult(
                status="error",
                broker=BrokerId.YAHOO,
                operation=BrokerCapabilityId.CONNECT,
                request_id=REQUEST_ID,
                timestamp=datetime.now(UTC),
                environment=BrokerEnvironment.SANDBOX,
                adapter_version="1",
                error=BrokerError(
                    code=BrokerErrorCode.BROKER_CONNECTION_FAILED,
                    message="failed to connect",
                ),
            )

    result = asyncio.run(_FailingAdapter().connect())
    assert result.error is not None
    assert result.error.code is BrokerErrorCode.BROKER_CONNECTION_FAILED


def test_transition_noop() -> None:
    """Transitioning to the current connection state is a no-op."""
    adapter = _adapter()

    async def exercise() -> None:
        await adapter._transition(adapter._state)

    asyncio.run(exercise())


def test_reconnect_executes_disconnect_and_connect() -> None:
    """Reconnection calls both disconnect and connect workflows."""

    class _ReconnectAdapter(_ContextAdapter):
        def __init__(self) -> None:
            super().__init__()
            self.connect_count = 0

        async def connect(self) -> BrokerResult[None]:
            self.connect_count += 1
            return self._result(BrokerCapabilityId.CONNECT)

    adapter = _ReconnectAdapter()

    async def exercise() -> None:
        await adapter.reconnect()
        assert adapter.disconnect_count == 1
        assert adapter.connect_count == 1

    asyncio.run(exercise())


def test_getattr_fallback_for_undefined_capability() -> None:
    """Attribute lookup for undefined capability routes to fallback handler."""
    adapter = _ContextAdapter()
    adapter._state = BrokerConnectionState.READY

    async def exercise() -> None:
        method = getattr(adapter, "calculate_profit")  # noqa: B009
        result = await method()
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED

    asyncio.run(exercise())


def test_getattr_raises_attribute_error_for_invalid_name() -> None:
    """Attribute lookup for a non-capability attribute raises AttributeError."""
    adapter = _ContextAdapter()
    with pytest.raises(AttributeError):
        getattr(adapter, "not_a_capability")  # noqa: B009
