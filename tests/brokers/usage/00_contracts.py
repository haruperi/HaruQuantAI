"""FEAT-BRK-00: exercise the canonical provider-neutral contract surface."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import _support  # noqa: F401
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
    BrokerId,
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
    BrokerQuote,
    BrokerResult,
    BrokerSubscriptionInfo,
    BrokerSymbolInfo,
    BrokerTick,
    BrokerTradingSession,
)

_NOW = datetime(2026, 1, 1, tzinfo=UTC)
_REQ = "req-2f1d5a6c-8b3e-4c17-9f52-70a1c8d94e33"


def fr_brokers_001() -> None:
    """FR-BRK-001: Identify registered broker profiles without aliases."""
    print("FR-BRK-001:", tuple(item.value for item in BrokerId))


def fr_brokers_002() -> None:
    """FR-BRK-002: Require explicit environment without live default."""
    print("FR-BRK-002:", tuple(item.value for item in BrokerEnvironment))


def fr_brokers_003() -> None:
    """FR-BRK-003: Expose minimal validated lifecycle states."""
    print("FR-BRK-003:", tuple(item.value for item in BrokerConnectionState))


def fr_brokers_004() -> None:
    """FR-BRK-004: Expose stable accepted BROKER_* error taxonomy."""
    print("FR-BRK-004:", len(tuple(BrokerErrorCode)))


def fr_brokers_005() -> None:
    """FR-BRK-005: Expose identifier for every accepted canonical capability."""
    print("FR-BRK-005:", len(tuple(BrokerCapabilityId)))


def fr_brokers_006() -> None:
    """FR-BRK-006: Carry immutable connection configuration without secret leakage."""
    config = BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=8,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
    )
    print("FR-BRK-006:", config.broker_id, config.environment)


def fr_brokers_007() -> None:
    """FR-BRK-007: Represent structured operational error evidence."""
    err = BrokerError(
        code=BrokerErrorCode.BROKER_UNKNOWN_OUTCOME,
        message="uncertain outcome",
        retryable=False,
    )
    print("FR-BRK-007:", err.code, err.message)


def fr_brokers_008() -> None:
    """FR-BRK-008: Return versioned status/broker/operation/time/data/error envelope."""
    res: BrokerResult[None] = BrokerResult(
        status="success",
        broker=BrokerId.MT5,
        operation=BrokerCapabilityId.CONNECT,
        request_id=_REQ,
        timestamp=_NOW,
        environment=BrokerEnvironment.DEMO,
        adapter_version="1.0.0",
    )
    print("FR-BRK-008:", res.is_success, res.contract_version)


def fr_brokers_009() -> None:
    """FR-BRK-009: Return bounded records with explicit truncation metadata."""
    page = BrokerPage(items=(1, 2), limit=2, truncated=True, next_cursor="c1")
    print("FR-BRK-009:", page.returned_count, page.truncated)


def fr_brokers_010() -> None:
    """FR-BRK-010: Report capability availability, requirement, and verification
    status."""
    cap = BrokerCapability(
        capability=BrokerCapabilityId.PLACE_ORDER,
        implementation_status="IMPLEMENTED",
        availability="UNAVAILABLE",
        access_mode="WRITE",
        requirement="PERMISSION",
        verification_status="NOT_TESTED",
        execution_model="PROVIDER_CALL",
    )
    print("FR-BRK-010:", cap.capability, cap.availability)


def fr_brokers_011() -> None:
    """FR-BRK-011: Return feature flags catalogue for profile and environment."""
    cap = BrokerCapability(
        capability=BrokerCapabilityId.PLACE_ORDER,
        implementation_status="IMPLEMENTED",
        availability="UNAVAILABLE",
        access_mode="WRITE",
        requirement="PERMISSION",
        verification_status="NOT_TESTED",
        execution_model="PROVIDER_CALL",
    )
    print("FR-BRK-011:", cap.capability, cap.availability)


def fr_brokers_012() -> None:
    """FR-BRK-012: Distinguish transport, auth, permission, and lifecycle state."""
    status = BrokerConnectionStatus(
        state=BrokerConnectionState.DISCONNECTED,
        transport_connected=False,
        environment=BrokerEnvironment.DEMO,
        session_generation=0,
        observed_at=_NOW,
    )
    print("FR-BRK-012:", status.state, status.transport_connected)


def fr_brokers_013() -> None:
    """FR-BRK-013: Expose previous/new state, reason, UTC time, and session
    generation."""
    event = BrokerConnectionEvent(
        previous_state=BrokerConnectionState.CONNECTING,
        new_state=BrokerConnectionState.READY,
        timestamp=_NOW,
        session_generation=1,
    )
    print("FR-BRK-013:", event.previous_state, event.new_state)


def fr_brokers_014() -> None:
    """FR-BRK-014: Expose provider, version, endpoint metadata, and environment."""
    plat = BrokerPlatformInfo(
        broker_id=BrokerId.MT5,
        provider_name="MetaTrader 5",
        product_profile="mt5",
        environment=BrokerEnvironment.DEMO,
        observed_at=_NOW,
    )
    print("FR-BRK-014:", plat.broker_id, plat.provider_name)


def fr_brokers_015() -> None:
    """FR-BRK-015: Expose provider permissions reported for authenticated session."""
    perm = BrokerPermissions(
        observed_at=_NOW, market_data_read=True, trade_write=False, subscription=True
    )
    print("FR-BRK-015:", perm.market_data_read, perm.trade_write)


def fr_brokers_016() -> None:
    """FR-BRK-016: Preserve provider account identity, balances, and timestamps."""
    acc = BrokerAccountInfo(
        account_id="10001",
        account_reference_redacted="***001",
        currency="USD",
        balance=Decimal("1000.00"),
        retrieved_at=_NOW,
    )
    print("FR-BRK-016:", acc.account_id, acc.balance)


def fr_brokers_017() -> None:
    """FR-BRK-017: Represent provider balance values with exact decimals and units."""
    bal = BrokerBalance(
        asset="USD",
        total=Decimal("1000.00"),
        unit="USD",
        retrieved_at=_NOW,
    )
    print("FR-BRK-017:", bal.asset, bal.total)


def fr_brokers_018() -> None:
    """FR-BRK-018: Represent provider asset metadata structurally."""
    asset = BrokerAssetInfo(asset_id="USD", provider_name="US Dollar")
    print("FR-BRK-018:", asset.asset_id, asset.provider_name)


def fr_brokers_019() -> None:
    """FR-BRK-019: Preserve exact provider-native symbol identifier and flags."""
    sym = BrokerSymbolInfo(
        provider_symbol="EURUSD",
        product_profile="mt5",
        price_unit="quote_currency",
        quantity_unit="lots",
    )
    print("FR-BRK-019:", sym.provider_symbol, sym.product_profile)


def fr_brokers_020() -> None:
    """FR-BRK-020: Represent provider-reported open, closed, or unknown market
    status."""
    status = BrokerMarketStatus(
        symbol="EURUSD",
        status="OPEN",
        retrieved_at=_NOW,
    )
    print("FR-BRK-020:", status.symbol, status.status)


def fr_brokers_021() -> None:
    """FR-BRK-021: Represent trading windows as timezone-aware UTC intervals."""
    sess = BrokerTradingSession(
        symbol="EURUSD",
        opens_at=_NOW,
        closes_at=_NOW + timedelta(hours=8),
    )
    print("FR-BRK-021:", sess.symbol, sess.opens_at)


def fr_brokers_022() -> None:
    """FR-BRK-022: Expose genuine bid/ask/last values with exact decimals."""
    quote = BrokerQuote(
        symbol="EURUSD",
        price_unit="quote_currency",
        quantity_unit="lots",
        bid=Decimal("1.1000"),
        ask=Decimal("1.1002"),
        retrieved_at=_NOW,
    )
    print("FR-BRK-022:", quote.symbol, quote.bid, quote.ask)


def fr_brokers_023() -> None:
    """FR-BRK-023: Preserve provider sequence, event time, and tick type."""
    tick = BrokerTick(
        symbol="EURUSD",
        bid=Decimal("1.1000"),
        ask=Decimal("1.1002"),
        event_timestamp=_NOW,
        provider_receipt_timestamp=_NOW,
        price_unit="quote_currency",
        quantity_unit="lots",
    )
    print("FR-BRK-023:", tick.symbol, tick.event_timestamp)


def fr_brokers_024() -> None:
    """FR-BRK-024: Preserve UTC OHLC, closed state, volume, and spread."""
    bar = BrokerBar(
        symbol="EURUSD",
        opening_timestamp=_NOW,
        closing_timestamp=_NOW + timedelta(minutes=1),
        is_closed=True,
        open=Decimal("1.10"),
        high=Decimal("1.11"),
        low=Decimal("1.09"),
        close=Decimal("1.105"),
        provider_timeframe="1m",
        requested_timeframe="1m",
        price_unit="quote_currency",
        quantity_unit="lots",
    )
    print("FR-BRK-024:", bar.symbol, bar.open, bar.close)


def fr_brokers_025() -> None:
    """FR-BRK-025: Represent order-book snapshot/delta state and sequence."""
    book = BrokerOrderBook(
        symbol="EURUSD",
        bids=(),
        asks=(),
        is_snapshot=True,
        resnapshot_required=False,
        event_timestamp=_NOW,
        price_unit="quote_currency",
        quantity_unit="lots",
    )
    print("FR-BRK-025:", book.symbol, book.event_timestamp)


def fr_brokers_026() -> None:
    """FR-BRK-026: Represent metadata for adapter-scoped subscription."""
    info = BrokerSubscriptionInfo(
        subscription_id="sub-1",
        capability=BrokerCapabilityId.SUBSCRIBE_QUOTES,
        symbols=("EURUSD",),
        created_at=_NOW,
        buffer_size=8,
    )
    print("FR-BRK-026:", info.subscription_id, info.capability)


def fr_brokers_027() -> None:
    """FR-BRK-027: Preserve provider position ID, symbol, side, and P&L."""
    pos = BrokerPosition(
        position_id="p1",
        symbol="EURUSD",
        side="LONG",
        state="OPEN",
        quantity=Decimal("1.0"),
        quantity_unit="lots",
        retrieved_at=_NOW,
    )
    print("FR-BRK-027:", pos.position_id, pos.side)


def fr_brokers_028() -> None:
    """FR-BRK-028: Express structural order filters without selection policy."""
    filt = BrokerOrderFilter(symbol="EURUSD")
    print("FR-BRK-028:", filt.symbol)


def fr_brokers_029() -> None:
    """FR-BRK-029: Express structural position filters only."""
    filt = BrokerPositionFilter(symbol="EURUSD")
    print("FR-BRK-029:", filt.symbol)


def fr_brokers_030() -> None:
    """FR-BRK-030: Preserve provider order IDs, side, type, state, and quantity."""
    ord_ = BrokerOrder(
        order_id="o1",
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        state="FILLED",
        quantity=Decimal("1.0"),
        filled=Decimal("1.0"),
        remaining=Decimal("0.0"),
        quantity_unit="lots",
        retrieved_at=_NOW,
    )
    print("FR-BRK-030:", ord_.order_id, ord_.state)


def fr_brokers_031() -> None:
    """FR-BRK-031: Preserve provider deal/fill ID, order ref, and fee."""
    deal = BrokerDeal(
        deal_id="d1",
        order_id="o1",
        symbol="EURUSD",
        side="BUY",
        quantity=Decimal("1.0"),
        quantity_unit="lots",
        price=Decimal("1.10"),
        partial=False,
        retrieved_at=_NOW,
    )
    print("FR-BRK-031:", deal.deal_id, deal.price)


def fr_brokers_032() -> None:
    """FR-BRK-032: Represent provider account transactions with exact values."""
    tx = BrokerAccountTransaction(
        transaction_id="t1",
        transaction_type="DEPOSIT",
        asset="USD",
        currency="USD",
        amount=Decimal("1000.00"),
        provider_timestamp=_NOW,
        retrieved_at=_NOW,
    )
    print("FR-BRK-032:", tx.transaction_id, tx.amount)


def fr_brokers_033() -> None:
    """FR-BRK-033: Require complete V1 order request matching field manifest."""
    req = BrokerOrderRequest(
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal("0.01"),
        quantity_unit="lots",
        environment=BrokerEnvironment.DEMO,
    )
    print("FR-BRK-033:", req.symbol, req.order_type)


def fr_brokers_034() -> None:
    """FR-BRK-034: Identify one provider order and caller modifications."""
    mod = BrokerOrderModificationRequest(order_id="o1", limit_price=Decimal("1.11"))
    print("FR-BRK-034:", mod.order_id, mod.limit_price)


def fr_brokers_035() -> None:
    """FR-BRK-035: Distinguish provider order check from final acceptance."""
    chk = BrokerOrderCheck(
        accepted_for_submission=True, estimated_margin=Decimal("100.00")
    )
    print("FR-BRK-035:", chk.accepted_for_submission, chk.estimated_margin)


def fr_brokers_036() -> None:
    """FR-BRK-036: Represent explicit provider order result acknowledgement."""
    res = BrokerOrderResult(
        acknowledged=True,
        outcome="ACCEPTED",
        retrieved_at=_NOW,
        order_id="o1",
    )
    print("FR-BRK-036:", res.outcome, res.order_id)


def fr_brokers_037() -> None:
    """FR-BRK-037: Identify position and caller stop/take-profit modifications."""
    mod = BrokerPositionModificationRequest(position_id="p1", stop_loss=Decimal("1.09"))
    print("FR-BRK-037:", mod.position_id, mod.stop_loss)


def fr_brokers_038() -> None:
    """FR-BRK-038: Identify position and exact close/reduce quantity."""
    close = BrokerPositionCloseRequest(
        position_id="p1",
        quantity=Decimal("0.5"),
        quantity_unit="lots",
    )
    print("FR-BRK-038:", close.position_id, close.quantity)


def main() -> None:
    """Execute every FR-BRK-001..038 usage function."""
    fr_brokers_001()
    fr_brokers_002()
    fr_brokers_003()
    fr_brokers_004()
    fr_brokers_005()
    fr_brokers_006()
    fr_brokers_007()
    fr_brokers_008()
    fr_brokers_009()
    fr_brokers_010()
    fr_brokers_011()
    fr_brokers_012()
    fr_brokers_013()
    fr_brokers_014()
    fr_brokers_015()
    fr_brokers_016()
    fr_brokers_017()
    fr_brokers_018()
    fr_brokers_019()
    fr_brokers_020()
    fr_brokers_021()
    fr_brokers_022()
    fr_brokers_023()
    fr_brokers_024()
    fr_brokers_025()
    fr_brokers_026()
    fr_brokers_027()
    fr_brokers_028()
    fr_brokers_029()
    fr_brokers_030()
    fr_brokers_031()
    fr_brokers_032()
    fr_brokers_033()
    fr_brokers_034()
    fr_brokers_035()
    fr_brokers_036()
    fr_brokers_037()
    fr_brokers_038()


if __name__ == "__main__":
    main()
