"""FEAT-BRK-00: exercise the canonical provider-neutral contract surface.

Constructs every registered contract family through the documented public API,
demonstrating immutability, UTC/Decimal semantics, redaction, schema identity,
and the structural invariants that reject fabricated provider evidence.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import _support  # noqa: F401 - resolves the repository root for direct execution
from app.services.brokers import (
    BrokerAccountInfo,
    BrokerBalance,
    BrokerBar,
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionEvent,
    BrokerConnectionState,
    BrokerEnvironment,
    BrokerError,
    BrokerErrorCode,
    BrokerId,
    BrokerOrderRequest,
    BrokerPage,
    BrokerQuote,
    BrokerResult,
)

_NOW = datetime(2026, 1, 1, tzinfo=UTC)
_REQUEST_ID = "req-2f1d5a6c-8b3e-4c17-9f52-70a1c8d94e33"


def example_enums_are_explicit() -> None:
    """FR-BRK-001-005: canonical values have no aliases or implicit defaults."""
    print("brokers", tuple(item.value for item in BrokerId))
    print("environments", tuple(item.value for item in BrokerEnvironment))
    print("states", tuple(item.value for item in BrokerConnectionState))
    print("error codes", len(tuple(BrokerErrorCode)))
    print("capabilities", len(tuple(BrokerCapabilityId)))


def example_result_envelope_invariants() -> None:
    """FR-BRK-008: success excludes an error; failure excludes data."""
    success: BrokerResult[None] = BrokerResult(
        status="success",
        broker=BrokerId.MT5,
        operation=BrokerCapabilityId.CONNECT,
        request_id=_REQUEST_ID,
        timestamp=_NOW,
        environment=BrokerEnvironment.DEMO,
        adapter_version="1.0.0",
        latency_ms=12.5,
        provider_latency_ms=10.0,
        adapter_overhead_ms=2.5,
    )
    print(
        "success",
        success.is_success,
        success.contract_version,
        success.schema_id,
        f"latency={success.latency_ms} provider={success.provider_latency_ms}",
    )

    failure: BrokerResult[None] = BrokerResult(
        status="error",
        broker=BrokerId.MT5,
        operation=BrokerCapabilityId.PLACE_ORDER,
        request_id=_REQUEST_ID,
        timestamp=_NOW,
        environment=BrokerEnvironment.DEMO,
        adapter_version="1.0.0",
        error=BrokerError(
            code=BrokerErrorCode.BROKER_UNKNOWN_OUTCOME,
            message="uncertain transmission",
            retryable=False,
        ),
    )
    print(
        "failure",
        failure.is_success,
        failure.error.code.value if failure.error else None,
    )

    try:
        BrokerResult(
            status="success",
            broker=BrokerId.MT5,
            operation=BrokerCapabilityId.CONNECT,
            request_id=_REQUEST_ID,
            timestamp=_NOW,
            environment=BrokerEnvironment.DEMO,
            adapter_version="1.0.0",
            error=BrokerError(
                code=BrokerErrorCode.BROKER_TIMEOUT, message="conflicting"
            ),
        )
    except ValueError as error:
        print("conflicting envelope rejected:", error)


def example_observation_dtos_reject_fabrication() -> None:
    """FR-BRK-022-024: observations are Decimal, UTC-aware, and never guessed."""
    quote = BrokerQuote(
        symbol="EURUSD",
        price_unit="quote_currency",
        quantity_unit="lots",
        bid=Decimal("1.10500"),
        ask=Decimal("1.10520"),
        retrieved_at=_NOW,
    )
    print("quote", quote.bid, quote.ask, quote.schema_id)

    bar = BrokerBar(
        symbol="EURUSD",
        opening_timestamp=_NOW,
        closing_timestamp=_NOW + timedelta(minutes=1),
        is_closed=True,
        open=Decimal("1.10"),
        high=Decimal("1.11"),
        low=Decimal("1.09"),
        close=Decimal("1.105"),
        provider_timeframe="M1",
        requested_timeframe="M1",
        price_unit="quote_currency",
        quantity_unit="lots",
    )
    print("bar", bar.open, bar.close, bar.closing_timestamp - bar.opening_timestamp)

    try:
        BrokerQuote(
            symbol="EURUSD",
            price_unit="quote_currency",
            quantity_unit="lots",
            retrieved_at=_NOW,
        )
    except ValueError as error:
        print("quote without a genuine price rejected:", error)


def example_page_bounds_are_explicit() -> None:
    """FR-BRK-009: pages expose their bound, count, and truncation state."""
    page = BrokerPage(items=(1, 2, 3), limit=3, truncated=True, next_cursor="c-2")
    print("page", page.returned_count, page.limit, page.truncated, page.next_cursor)


def example_capability_release_gate() -> None:
    """FR-BRK-010: an available write requires evidence and owner approval."""
    gated = BrokerCapability(
        capability=BrokerCapabilityId.PLACE_ORDER,
        implementation_status="IMPLEMENTED",
        availability="UNAVAILABLE",
        access_mode="WRITE",
        requirement="PERMISSION",
        verification_status="NOT_TESTED",
        execution_model="PROVIDER_CALL",
        reason="Release evidence is not recorded",
    )
    print("gated write", gated.availability, gated.reason)

    try:
        BrokerCapability(
            capability=BrokerCapabilityId.PLACE_ORDER,
            implementation_status="IMPLEMENTED",
            availability="AVAILABLE",
            access_mode="WRITE",
            requirement="PERMISSION",
            verification_status="NOT_TESTED",
            execution_model="PROVIDER_CALL",
        )
    except ValueError as error:
        print("unapproved available write rejected:", error)


def example_account_and_request_contracts() -> None:
    """FR-BRK-016/033: account truth is preserved; requests infer nothing."""
    account = BrokerAccountInfo(
        account_id="100001",
        account_reference_redacted="***001",
        currency="USD",
        balance=Decimal("10500.75"),
        retrieved_at=_NOW,
    )
    print("account", account.account_id, account.account_reference_redacted)

    balance = BrokerBalance(
        asset="USD",
        total=Decimal("10500.75"),
        unit="account_currency",
        retrieved_at=_NOW,
    )
    print("balance", balance.asset, balance.total, balance.unit)

    request = BrokerOrderRequest(
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal("0.01"),
        quantity_unit="lots",
        environment=BrokerEnvironment.DEMO,
    )
    print("order request", request.symbol, request.side, request.quantity)

    try:
        BrokerOrderRequest(
            symbol="EURUSD",
            side="BUY",
            order_type="MARKET",
            quantity=Decimal(-1),
            quantity_unit="lots",
            environment=BrokerEnvironment.DEMO,
        )
    except ValueError as error:
        print("non-positive quantity rejected:", error)


def example_lifecycle_event_contract() -> None:
    """FR-BRK-013: every transition carries UTC and session evidence."""
    event = BrokerConnectionEvent(
        previous_state=BrokerConnectionState.CONNECTING,
        new_state=BrokerConnectionState.READY,
        timestamp=_NOW,
        session_generation=1,
    )
    print("event", event.previous_state.value, "->", event.new_state.value)


def main() -> None:
    """Exercise every FEAT-BRK-00 contract family."""
    example_enums_are_explicit()
    example_result_envelope_invariants()
    example_observation_dtos_reject_fabrication()
    example_page_bounds_are_explicit()
    example_capability_release_gate()
    example_account_and_request_contracts()
    example_lifecycle_event_contract()


if __name__ == "__main__":
    main()
