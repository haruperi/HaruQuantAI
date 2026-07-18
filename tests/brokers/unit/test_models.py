"""Canonical broker model tests."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from app.services.brokers import (
    BrokerAccountInfo,
    BrokerAccountTransaction,
    BrokerAssetInfo,
    BrokerBalance,
    BrokerBar,
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerConnectionEvent,
    BrokerConnectionState,
    BrokerConnectionStatus,
    BrokerDeal,
    BrokerEnvironment,
    BrokerError,
    BrokerErrorCode,
    BrokerFeatureFlags,
    BrokerFeeEstimate,
    BrokerId,
    BrokerMarginRequest,
    BrokerMarketStatus,
    BrokerOrder,
    BrokerOrderBook,
    BrokerOrderCheck,
    BrokerOrderFilter,
    BrokerOrderModificationRequest,
    BrokerOrderRequest,
    BrokerOrderResult,
    BrokerPage,
    BrokerPermissions,
    BrokerPlatformInfo,
    BrokerPosition,
    BrokerPositionCloseRequest,
    BrokerPositionFilter,
    BrokerPositionModificationRequest,
    BrokerProfitRequest,
    BrokerQuote,
    BrokerResult,
    BrokerServerTime,
    BrokerSubscriptionInfo,
    BrokerSymbolInfo,
    BrokerTick,
    BrokerTradingSession,
)
from pydantic import SecretStr

NOW = datetime(2026, 1, 1, tzinfo=UTC)
LATER = NOW + timedelta(seconds=1)
D = Decimal


def _config() -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
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
        credentials={"token": SecretStr("value")},  # pragma: allowlist secret
    )


def _capability(capability: BrokerCapabilityId) -> BrokerCapability:
    return BrokerCapability(
        capability=capability,
        implementation_status="NOT_IMPLEMENTED",
        availability="UNAVAILABLE",
        access_mode="READ",
        requirement="NONE",
        verification_status="NOT_TESTED",
        execution_model="NO_PROVIDER_CALL",
        reason="not released",
    )


def _capabilities() -> dict[BrokerCapabilityId, BrokerCapability]:
    return {capability: _capability(capability) for capability in BrokerCapabilityId}


def test_connection_config_is_immutable_and_explicit() -> None:
    """FR-BRK-006: resolved config is explicit, bounded, and immutable."""
    config = _config()
    assert config.provider_enabled
    assert config.contract_version == "v1"
    with pytest.raises(FrozenInstanceError):
        config.auto_connect = True  # type: ignore[misc]
    assert config.credentials is not None
    with pytest.raises(TypeError):
        config.credentials["other"] = SecretStr("x")  # type: ignore[index]
    with pytest.raises(ValueError, match="positive"):
        BrokerConnectionConfig(
            broker_id=BrokerId.YAHOO,
            environment=BrokerEnvironment.SANDBOX,
            provider_enabled=True,
            connect_timeout_sec=0,
            request_timeout_sec=1,
            transport_reconnect_max_attempts=0,
            stream_buffer_size=1,
            circuit_failure_threshold=1,
            circuit_recovery_timeout_sec=1,
            circuit_half_open_max_calls=1,
        )


def test_error_is_redacted_and_structured() -> None:
    """FR-BRK-007: stable errors contain only redacted bounded evidence."""
    error = BrokerError(
        code=BrokerErrorCode.BROKER_TIMEOUT,
        message="provider timeout",
        details={"api_key": "secret", "attempt": 1},  # pragma: allowlist secret
    )
    assert error.details["api_key"] != "secret"  # pragma: allowlist secret
    with pytest.raises(TypeError):
        error.details["attempt"] = 2  # type: ignore[index]


def test_result_supports_successful_none_and_exclusive_error() -> None:
    """FR-BRK-008: void success and structured error are exclusive."""
    result = BrokerResult[None](
        status="success",
        broker=BrokerId.YAHOO,
        operation=BrokerCapabilityId.DISCONNECT,
        request_id="request",
        timestamp=NOW,
        environment=BrokerEnvironment.SANDBOX,
        adapter_version="1",
        provider_metadata={"token": "secret"},  # pragma: allowlist secret
    )
    assert result.is_success
    assert result.data is None
    assert result.error is None
    assert result.provider_metadata["token"] != "secret"  # pragma: allowlist secret
    with pytest.raises(ValueError, match="error status requires"):
        BrokerResult[None](
            status="error",
            broker=BrokerId.YAHOO,
            operation=BrokerCapabilityId.DISCONNECT,
            request_id="request",
            timestamp=NOW,
            environment=BrokerEnvironment.SANDBOX,
            adapter_version="1",
        )
    with pytest.raises(ValueError, match="UTC-aware"):
        BrokerResult[None](
            status="success",
            broker=BrokerId.YAHOO,
            operation=BrokerCapabilityId.DISCONNECT,
            request_id="request",
            timestamp=NOW.replace(tzinfo=None),
            environment=BrokerEnvironment.SANDBOX,
            adapter_version="1",
        )


def test_page_exposes_cursor_and_truncation() -> None:
    """FR-BRK-009: pages expose exact bounds and truncation."""
    page = BrokerPage(items=(1,), limit=1, truncated=True, next_cursor="next")
    assert page.returned_count == 1
    with pytest.raises(ValueError, match="next cursor"):
        BrokerPage(items=(1,), limit=1, next_cursor="next")


def test_capability_requires_write_release_evidence() -> None:
    """FR-BRK-010: write availability requires evidence and approval."""
    with pytest.raises(ValueError, match="available writes"):
        BrokerCapability(
            capability=BrokerCapabilityId.PLACE_ORDER,
            implementation_status="IMPLEMENTED",
            availability="AVAILABLE",
            access_mode="WRITE",
            requirement="PERMISSION",
            verification_status="NOT_TESTED",
            execution_model="PROVIDER_CALL",
        )


def test_feature_flags_fail_closed_for_unapproved_writes() -> None:
    """FR-BRK-011: the report is complete and fail-closed."""
    flags = BrokerFeatureFlags(
        broker_id=BrokerId.YAHOO,
        environment=BrokerEnvironment.SANDBOX,
        generated_at=NOW,
        capabilities=_capabilities(),
        adapter_version="1",
    )
    assert len(flags.capabilities) == len(BrokerCapabilityId)
    with pytest.raises(ValueError, match="every capability"):
        BrokerFeatureFlags(
            broker_id=BrokerId.YAHOO,
            environment=BrokerEnvironment.SANDBOX,
            generated_at=NOW,
            capabilities={},
            adapter_version="1",
        )


def test_connection_status_is_not_boolean_only() -> None:
    """FR-BRK-012: lifecycle truth includes verified components."""
    status = BrokerConnectionStatus(
        state=BrokerConnectionState.READY,
        transport_connected=True,
        application_authenticated=True,
        environment=BrokerEnvironment.SANDBOX,
        session_generation=1,
        observed_at=NOW,
    )
    assert status.state is BrokerConnectionState.READY
    with pytest.raises(ValueError, match="ready state"):
        BrokerConnectionStatus(
            state=BrokerConnectionState.READY,
            transport_connected=False,
            environment=BrokerEnvironment.SANDBOX,
            session_generation=1,
            observed_at=NOW,
        )


def test_connection_event_records_transition() -> None:
    """FR-BRK-013: events record real transitions and generations."""
    event = BrokerConnectionEvent(
        previous_state=BrokerConnectionState.DISCONNECTED,
        new_state=BrokerConnectionState.CONNECTING,
        timestamp=NOW,
        session_generation=0,
    )
    assert event.previous_state is not event.new_state
    with pytest.raises(ValueError, match="real transition"):
        BrokerConnectionEvent(
            previous_state=BrokerConnectionState.READY,
            new_state=BrokerConnectionState.READY,
            timestamp=NOW,
            session_generation=0,
        )


def test_platform_info_is_redacted() -> None:
    """FR-BRK-014: platform metadata cannot leak credentials."""
    info = BrokerPlatformInfo(
        broker_id=BrokerId.YAHOO,
        provider_name="Yahoo",
        product_profile="historical",
        environment=BrokerEnvironment.SANDBOX,
        observed_at=NOW,
        endpoint_metadata={"password": "secret"},  # pragma: allowlist secret
    )
    assert info.endpoint_metadata["password"] != "secret"  # pragma: allowlist secret


def test_permissions_preserve_unknown() -> None:
    """FR-BRK-015: missing permission evidence remains unknown."""
    permissions = BrokerPermissions(observed_at=NOW, trade_write=None)
    assert permissions.trade_write is None


def test_account_info_preserves_provider_truth() -> None:
    """FR-BRK-016: account values retain exact decimals and timestamps."""
    info = BrokerAccountInfo(
        account_id="account-1", retrieved_at=NOW, balance=D("1.20")
    )
    assert info.balance == D("1.20")


def test_balance_uses_decimal_and_unit() -> None:
    """FR-BRK-017: balances have exact values and explicit units."""
    balance = BrokerBalance(asset="USD", unit="USD", retrieved_at=NOW, total=D("2"))
    assert balance.total == D("2")
    assert balance.unit == "USD"


def test_asset_info_is_structural_only() -> None:
    """FR-BRK-018: asset metadata has no valuation policy."""
    asset = BrokerAssetInfo(asset_id="USD", precision=2)
    assert asset.asset_id == "USD"
    assert not hasattr(asset, "value")


def test_symbol_info_contains_only_provider_native_identity() -> None:
    """FR-BRK-019: symbols expose provider identity without aliases."""
    symbol = BrokerSymbolInfo(
        provider_symbol="EURUSD",
        product_profile="spot",
        price_unit="USD",
        quantity_unit="lot",
        price_precision=5,
    )
    assert symbol.provider_symbol == "EURUSD"
    assert not hasattr(symbol, "aliases")


def test_market_status_allows_unknown() -> None:
    """FR-BRK-020: absent market truth remains UNKNOWN."""
    status = BrokerMarketStatus(symbol="EURUSD", status="UNKNOWN", retrieved_at=NOW)
    assert status.status == "UNKNOWN"


def test_trading_session_is_utc() -> None:
    """FR-BRK-021: sessions require ordered UTC bounds."""
    session = BrokerTradingSession(symbol="EURUSD", opens_at=NOW, closes_at=LATER)
    assert session.closes_at > session.opens_at
    with pytest.raises(ValueError, match="UTC-aware"):
        BrokerTradingSession(
            symbol="EURUSD",
            opens_at=NOW.astimezone(timezone(timedelta(hours=1))),
            closes_at=LATER,
        )


def test_quote_never_fabricates_price() -> None:
    """FR-BRK-022: quotes require genuine provider price evidence."""
    quote = BrokerQuote(
        symbol="EURUSD",
        price_unit="USD",
        quantity_unit="lot",
        retrieved_at=NOW,
        bid=D("1.1"),
        ask=D("1.2"),
    )
    assert quote.last_price is None
    with pytest.raises(ValueError, match="genuine price"):
        BrokerQuote(
            symbol="EURUSD",
            price_unit="USD",
            quantity_unit="lot",
            retrieved_at=NOW,
        )


def test_tick_preserves_optional_values() -> None:
    """FR-BRK-023: ticks preserve optional fields rather than deriving them."""
    tick = BrokerTick(
        symbol="EURUSD",
        event_timestamp=NOW,
        provider_receipt_timestamp=LATER,
        price_unit="USD",
        quantity_unit="lot",
        bid=D("1.1"),
    )
    assert tick.ask is None
    assert tick.last_price is None


def test_bar_has_explicit_time_volume_and_spread_semantics() -> None:
    """FR-BRK-024: bars preserve intervals, volumes, and spread evidence."""
    bar = BrokerBar(
        symbol="EURUSD",
        opening_timestamp=NOW,
        closing_timestamp=LATER,
        is_closed=True,
        open=D("1"),
        high=D("3"),
        low=D("0.5"),
        close=D("2"),
        provider_timeframe="1m",
        requested_timeframe="1m",
        price_unit="USD",
        quantity_unit="lot",
        spread=D("2"),
        spread_unit="points",
    )
    assert bar.trade_volume is None
    assert bar.is_closed
    assert bar.spread == D("2")


def test_bar_requires_spread_unit_with_spread() -> None:
    """Provider spread evidence always carries its native unit."""
    with pytest.raises(ValueError, match="provided together"):
        BrokerBar(
            symbol="EURUSD",
            opening_timestamp=NOW,
            closing_timestamp=LATER,
            is_closed=True,
            open=D("1"),
            high=D("3"),
            low=D("0.5"),
            close=D("2"),
            provider_timeframe="1m",
            requested_timeframe="1m",
            price_unit="USD",
            quantity_unit="lot",
            spread=D("2"),
        )


def test_order_book_exposes_resnapshot_state() -> None:
    """FR-BRK-025: order books preserve sequencing and resnapshot evidence."""
    book = BrokerOrderBook(
        symbol="EURUSD",
        bids=((D("1"), D("2")),),
        asks=((D("2"), D("3")),),
        is_snapshot=False,
        resnapshot_required=True,
        event_timestamp=NOW,
        price_unit="USD",
        quantity_unit="lot",
        first_sequence_id=1,
        last_sequence_id=2,
    )
    assert book.resnapshot_required


def test_subscription_info_is_adapter_scoped() -> None:
    """FR-BRK-026: subscription state is bounded and adapter-owned."""
    info = BrokerSubscriptionInfo(
        subscription_id="sub-1",
        capability=BrokerCapabilityId.SUBSCRIBE_QUOTES,
        symbols=("EURUSD",),
        created_at=NOW,
        buffer_size=2,
    )
    assert info.active
    assert info.buffer_size == 2


def test_position_preserves_provider_profit() -> None:
    """FR-BRK-027: positions retain provider-native state and profit."""
    position = BrokerPosition(
        position_id="position-1",
        symbol="EURUSD",
        side="LONG",
        quantity=D("1"),
        quantity_unit="lot",
        retrieved_at=NOW,
        profit=D("2.5"),
    )
    assert position.profit == D("2.5")


def test_order_filter_is_structural() -> None:
    """FR-BRK-028: order filters contain no selection defaults."""
    order_filter = BrokerOrderFilter(symbol="EURUSD", start=NOW, end=LATER)
    assert order_filter.symbol == "EURUSD"
    assert order_filter.status is None


def test_position_filter_is_structural() -> None:
    """FR-BRK-029: position filters contain only supplied fields."""
    position_filter = BrokerPositionFilter(side="LONG")
    assert position_filter.side == "LONG"
    assert position_filter.symbol is None


def test_order_preserves_partial_state_and_ids() -> None:
    """FR-BRK-030: provider order IDs and partial quantities are exact."""
    order = BrokerOrder(
        order_id="order-1",
        symbol="EURUSD",
        side="BUY",
        order_type="LIMIT",
        state="PARTIAL",
        quantity=D("2"),
        filled=D("1"),
        remaining=D("1"),
        quantity_unit="lot",
        retrieved_at=NOW,
    )
    assert order.filled == order.remaining == D("1")


def test_deal_never_invents_fill() -> None:
    """FR-BRK-031: deals require exact provider identifiers and quantities."""
    deal = BrokerDeal(
        deal_id="deal-1",
        symbol="EURUSD",
        side="BUY",
        quantity=D("1"),
        quantity_unit="lot",
        price=D("1.2"),
        partial=False,
        retrieved_at=NOW,
    )
    assert deal.order_id is None


def test_account_transaction_preserves_type() -> None:
    """FR-BRK-032: account transaction type and amount remain provider-native."""
    transaction = BrokerAccountTransaction(
        transaction_id="transaction-1",
        transaction_type="DEPOSIT",
        asset="USD",
        currency="USD",
        amount=D("10"),
        provider_timestamp=NOW,
        retrieved_at=LATER,
    )
    assert transaction.transaction_type == "DEPOSIT"


def test_order_request_does_not_infer_fields() -> None:
    """FR-BRK-033: V1 orders contain only exact caller-supplied intent."""
    request = BrokerOrderRequest(
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity=D("1"),
        quantity_unit="lot",
        environment=BrokerEnvironment.DEMO,
        deviation_points=2,
        magic=7,
    )
    assert request.limit_price is None
    assert not hasattr(request, "product_fields")
    with pytest.raises(ValueError, match="positive"):
        BrokerOrderRequest(
            symbol="EURUSD",
            side="BUY",
            order_type="MARKET",
            quantity=D("0"),
            quantity_unit="lot",
            environment=BrokerEnvironment.DEMO,
        )


def test_order_modification_has_one_target() -> None:
    """FR-BRK-034: modifications identify one order and at least one change."""
    request = BrokerOrderModificationRequest(order_id="order-1", quantity=D("2"))
    assert request.order_id == "order-1"
    with pytest.raises(ValueError, match="at least one"):
        BrokerOrderModificationRequest(order_id="order-1")


def test_order_check_is_not_acceptance() -> None:
    """FR-BRK-035: provider validation cannot be final acceptance."""
    check = BrokerOrderCheck(accepted_for_submission=True)
    assert check.is_final_acceptance is False


def test_order_result_requires_acknowledgement() -> None:
    """FR-BRK-036: accepted outcomes require acknowledgement and provider ID."""
    result = BrokerOrderResult(
        acknowledged=True,
        outcome="ACCEPTED",
        order_id="order-1",
        retrieved_at=NOW,
    )
    assert result.acknowledged
    with pytest.raises(ValueError, match="acknowledgement"):
        BrokerOrderResult(
            acknowledged=False,
            outcome="ACCEPTED",
            order_id="order-1",
            retrieved_at=NOW,
        )


def test_position_modification_has_one_target() -> None:
    """FR-BRK-037: position changes identify one target and supplied stops."""
    request = BrokerPositionModificationRequest(
        position_id="position-1", stop_loss=D("1")
    )
    assert request.take_profit is None
    with pytest.raises(ValueError, match="requires"):
        BrokerPositionModificationRequest(position_id="position-1")


def test_position_close_has_one_target() -> None:
    """FR-BRK-038: close requests contain one target and positive quantity."""
    request = BrokerPositionCloseRequest(
        position_id="position-1", quantity=D("1"), quantity_unit="lot"
    )
    assert request.quantity == D("1")


def test_margin_request_is_provider_native() -> None:
    """FR-BRK-039: margin input contains no local formula or policy."""
    request = BrokerMarginRequest(
        symbol="EURUSD",
        side="BUY",
        quantity=D("1"),
        quantity_unit="lot",
        product_profile="spot",
    )
    assert not hasattr(request, "leverage")


def test_profit_request_has_explicit_prices() -> None:
    """FR-BRK-040: profit input requires exact open and close prices."""
    request = BrokerProfitRequest(
        symbol="EURUSD",
        side="BUY",
        quantity=D("1"),
        quantity_unit="lot",
        open_price=D("1"),
        close_price=D("2"),
        product_profile="spot",
    )
    assert request.open_price != request.close_price


def test_fee_estimate_is_not_local_formula() -> None:
    """FR-BRK-041: fees are exact provider evidence, not a local formula."""
    estimate = BrokerFeeEstimate(amount=D("1.25"), currency_or_unit="USD")
    assert estimate.amount == D("1.25")


def test_server_time_exposes_clock_evidence() -> None:
    """FR-BRK-042: clock evidence remains explicit and ordered."""
    evidence = BrokerServerTime(
        provider_time=NOW,
        local_send_time=NOW,
        local_receive_time=LATER,
        estimated_clock_offset_ms=1.0,
        round_trip_latency_ms=1000.0,
    )
    assert evidence.local_receive_time >= evidence.local_send_time
    with pytest.raises(ValueError, match="latency"):
        BrokerServerTime(
            provider_time=NOW,
            local_send_time=NOW,
            local_receive_time=LATER,
            estimated_clock_offset_ms=0,
            round_trip_latency_ms=-1,
        )
