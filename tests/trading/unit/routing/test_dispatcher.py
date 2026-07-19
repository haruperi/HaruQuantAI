"""Unit tests for the sole asynchronous Trading dispatch boundary."""

# ruff: noqa: INP001

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import cast

import pytest
from app.services.brokers.contracts import (
    BrokerAdapter,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerError,
    BrokerErrorCode,
    BrokerId,
    BrokerOrderModificationRequest,
    BrokerOrderRequest,
    BrokerOrderResult,
    BrokerPosition,
    BrokerPositionCloseRequest,
    BrokerPositionModificationRequest,
    BrokerResult,
)
from app.services.trading.contracts import ExecutionReceipt, OrderIntent, TradingError
from app.services.trading.routing.dispatcher import (
    dispatch_order_intent as _dispatch_order_intent,
)

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)
BROKER_REQUEST_ID = (
    "req-dd37fc1c2cd6d665f9a7a7f9a2482efe3347c7bb51ac073ef12ef9b7eb511055"
)


async def dispatch_order_intent(
    intent: OrderIntent,
    connection: BrokerConnectionConfig | None,
    broker_adapter: BrokerAdapter | None,
    simulation_dispatch: Callable[[OrderIntent], Awaitable[ExecutionReceipt]] | None,
) -> ExecutionReceipt:
    """Invoke the public dispatcher with explicit deterministic runtime policy."""
    return await _dispatch_order_intent(
        intent,
        connection,
        broker_adapter,
        simulation_dispatch,
        operation_timeout_seconds=Decimal(10),
        clock=lambda: NOW,
    )


def _intent(*, route: str = "paper", action: str = "submit_order") -> OrderIntent:
    """Build one complete executable intent."""
    return OrderIntent(
        client_order_id="client-order-001",
        request_id="request-001",
        workflow_id="workflow-001",
        correlation_id="correlation-001",
        route=route,  # type: ignore[arg-type]
        provider_id=None if route == "sim" else "mt5",
        account_id="account-001",
        strategy_id="strategy-001",
        strategy_version="v1",
        source_intent_id="intent-001",
        symbol="EURUSD",
        action=action,  # type: ignore[arg-type]
        side="BUY",
        order_type="MARKET",
        quantity_unit="lots",
        approved_volume=Decimal("1.00"),
        risk_approved_volume=Decimal("1.00"),
        stop_loss=Decimal("0.90") if action == "modify_position" else None,
        target_broker_order_id=(
            "broker-order-001" if action in {"modify_order", "cancel_order"} else None
        ),
        target_broker_position_id=(
            "broker-position-001"
            if action in {"modify_position", "close_position", "reduce_exposure"}
            else None
        ),
        idempotency_hash="a" * 64,
        canonical_material_version="v1",
        risk_decision_id="risk-001",
        action_policy_verdict_id="verdict-001",
        approval_token_ref="approval-001",
        created_at=NOW,
        valid_until=NOW + timedelta(minutes=5),
    )


def _connection() -> BrokerConnectionConfig:
    """Build explicit demo Broker connection material."""
    return BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
        provider_enabled=True,
        connect_timeout_sec=5,
        request_timeout_sec=10,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=100,
        circuit_failure_threshold=3,
        circuit_recovery_timeout_sec=30,
        circuit_half_open_max_calls=1,
        account_reference="broker-account-001",
    )


class _Adapter:
    """Minimal test adapter exposing the invoked Broker mutation."""

    contract_version = "v1"
    schema_id = "brokers.adapter.v1"

    def __init__(self) -> None:
        """Initialize observable mutation evidence."""
        self.calls = 0
        self.request: BrokerOrderRequest | None = None
        self.mutations: list[object] = []

    def _order_result(
        self,
        operation: BrokerCapabilityId,
    ) -> BrokerResult[BrokerOrderResult]:
        """Build one acknowledged Broker order result."""
        return BrokerResult(
            status="success",
            broker=BrokerId.MT5,
            operation=operation,
            request_id=BROKER_REQUEST_ID,
            timestamp=NOW,
            environment=BrokerEnvironment.DEMO,
            adapter_version="test-v1",
            data=BrokerOrderResult(
                acknowledged=True,
                outcome="ACCEPTED",
                retrieved_at=NOW,
                order_id="broker-order-001",
            ),
        )

    async def place_order(
        self,
        request: BrokerOrderRequest,
    ) -> BrokerResult[BrokerOrderResult]:
        """Record and acknowledge one Broker placement."""
        self.calls += 1
        self.request = request
        self.mutations.append(request)
        return self._order_result(BrokerCapabilityId.PLACE_ORDER)

    async def modify_order(
        self,
        request: BrokerOrderModificationRequest,
    ) -> BrokerResult[BrokerOrderResult]:
        """Record and acknowledge one Broker order modification."""
        self.calls += 1
        self.mutations.append(request)
        return self._order_result(BrokerCapabilityId.MODIFY_ORDER)

    async def cancel_order(
        self,
        order_id: str,
        client_request_id: str | None = None,
    ) -> BrokerResult[BrokerOrderResult]:
        """Record and acknowledge one Broker cancellation."""
        self.calls += 1
        self.mutations.append((order_id, client_request_id))
        return self._order_result(BrokerCapabilityId.CANCEL_ORDER)

    async def modify_position(
        self,
        request: BrokerPositionModificationRequest,
    ) -> BrokerResult[BrokerPosition]:
        """Record and acknowledge one Broker position modification."""
        self.calls += 1
        self.mutations.append(request)
        return BrokerResult(
            status="success",
            broker=BrokerId.MT5,
            operation=BrokerCapabilityId.MODIFY_POSITION,
            request_id=BROKER_REQUEST_ID,
            timestamp=NOW,
            environment=BrokerEnvironment.DEMO,
            adapter_version="test-v1",
            data=BrokerPosition(
                position_id="broker-position-001",
                symbol="EURUSD",
                side="LONG",
                quantity=Decimal("1.00"),
                quantity_unit="lots",
                retrieved_at=NOW,
            ),
        )

    async def close_position(
        self,
        request: BrokerPositionCloseRequest,
    ) -> BrokerResult[BrokerOrderResult]:
        """Record and acknowledge one Broker position close."""
        self.calls += 1
        self.mutations.append(request)
        return self._order_result(BrokerCapabilityId.CLOSE_POSITION)


class _ErrorAdapter(_Adapter):
    """Test adapter returning one canonical Broker failure."""

    def __init__(self, code: BrokerErrorCode) -> None:
        """Initialize the selected Broker failure code."""
        super().__init__()
        self.code = code

    async def place_order(
        self,
        request: BrokerOrderRequest,
    ) -> BrokerResult[BrokerOrderResult]:
        """Return one explicit or ambiguous Broker failure."""
        self.calls += 1
        self.mutations.append(request)
        return BrokerResult(
            status="error",
            broker=BrokerId.MT5,
            operation=BrokerCapabilityId.PLACE_ORDER,
            request_id=BROKER_REQUEST_ID,
            timestamp=NOW,
            environment=BrokerEnvironment.DEMO,
            adapter_version="test-v1",
            error=BrokerError(code=self.code, message="Redacted Broker failure"),
        )


class _TimeoutAdapter(_Adapter):
    """Test adapter that exceeds every supplied short operation timeout."""

    async def place_order(
        self,
        request: BrokerOrderRequest,
    ) -> BrokerResult[BrokerOrderResult]:
        """Remain pending until the dispatch boundary cancels the call."""
        await asyncio.sleep(1)
        return await super().place_order(request)


def test_dispatch_has_single_mutation_boundary() -> None:
    """Each route invokes exactly one selected async mutation authority."""
    adapter = _Adapter()
    receipt = asyncio.run(
        dispatch_order_intent(
            _intent(),
            _connection(),
            cast("BrokerAdapter", adapter),
            None,
        )
    )
    assert adapter.calls == 1
    assert receipt.status == "accepted"
    assert adapter.request is not None
    assert adapter.request.environment is BrokerEnvironment.DEMO
    assert adapter.request.account_reference == "broker-account-001"
    assert adapter.request.order_type == "MARKET"
    assert adapter.request.quantity_unit == "lots"

    for action in (
        "modify_order",
        "cancel_order",
        "modify_position",
        "close_position",
        "reduce_exposure",
    ):
        asyncio.run(
            dispatch_order_intent(
                _intent(action=action),
                _connection(),
                cast("BrokerAdapter", adapter),
                None,
            )
        )
    assert isinstance(adapter.mutations[1], BrokerOrderModificationRequest)
    assert adapter.mutations[2] == ("broker-order-001", None)
    assert isinstance(adapter.mutations[3], BrokerPositionModificationRequest)
    assert isinstance(adapter.mutations[4], BrokerPositionCloseRequest)
    assert isinstance(adapter.mutations[5], BrokerPositionCloseRequest)
    close_request = cast("BrokerPositionCloseRequest", adapter.mutations[5])
    assert close_request.position_id == "broker-position-001"
    assert close_request.quantity_unit == "lots"

    rejected_adapter = _ErrorAdapter(BrokerErrorCode.BROKER_REQUEST_REJECTED)
    rejected = asyncio.run(
        dispatch_order_intent(
            _intent(),
            _connection(),
            cast("BrokerAdapter", rejected_adapter),
            None,
        )
    )
    assert rejected.status == "rejected"
    limited_adapter = _ErrorAdapter(BrokerErrorCode.BROKER_RATE_LIMITED)
    limited = asyncio.run(
        dispatch_order_intent(
            _intent(),
            _connection(),
            cast("BrokerAdapter", limited_adapter),
            None,
        )
    )
    assert limited.status == "unknown_outcome"
    assert limited.response_classification == "rate_limited"

    simulation_calls = 0

    async def simulation_dispatch(intent: OrderIntent) -> ExecutionReceipt:
        """Return one canonical simulated fill."""
        nonlocal simulation_calls
        simulation_calls += 1
        return ExecutionReceipt(
            receipt_id="sim-receipt-001",
            intent_id=intent.source_intent_id,
            client_order_id=intent.client_order_id,
            route="sim",
            authority="simulator",
            provider_order_id="sim-order-001",
            status="filled",
            requested_quantity=intent.approved_volume,
            filled_quantity=intent.approved_volume,
            authority_timestamp=NOW,
            received_at=NOW,
            response_classification="confirmed",
            retry_safe=False,
            reconciliation_required=False,
            request_id=intent.request_id,
            correlation_id=intent.correlation_id,
        )

    sim_receipt = asyncio.run(
        dispatch_order_intent(_intent(route="sim"), None, None, simulation_dispatch)
    )
    assert simulation_calls == 1
    assert sim_receipt.status == "filled"


def test_dispatch_rejects_mismatched_authority_selection() -> None:
    """Absent, disabled, or cross-route authorities fail before mutation."""
    adapter = _Adapter()
    broker = cast("BrokerAdapter", adapter)
    with pytest.raises(TradingError):
        asyncio.run(dispatch_order_intent(_intent(route="sim"), None, None, None))
    with pytest.raises(TradingError):
        asyncio.run(dispatch_order_intent(_intent(), None, None, None))
    with pytest.raises(TradingError):
        asyncio.run(
            dispatch_order_intent(
                _intent(route="sim"),
                _connection(),
                broker,
                None,
            )
        )

    async def unused_simulation(intent: OrderIntent) -> ExecutionReceipt:
        """Fail if a mismatched callback is ever invoked."""
        raise AssertionError(intent.client_order_id)

    with pytest.raises(TradingError):
        asyncio.run(
            dispatch_order_intent(
                _intent(),
                _connection(),
                broker,
                unused_simulation,
            )
        )
    with pytest.raises(TradingError):
        asyncio.run(
            dispatch_order_intent(
                _intent(),
                replace(_connection(), provider_enabled=False),
                broker,
                None,
            )
        )
    with pytest.raises(TradingError):
        asyncio.run(
            dispatch_order_intent(
                _intent(),
                replace(_connection(), broker_id=BrokerId.CTRADER),
                broker,
                None,
            )
        )
    with pytest.raises(TradingError):
        asyncio.run(
            dispatch_order_intent(
                _intent(route="live"),
                _connection(),
                broker,
                None,
            )
        )
    with pytest.raises(TradingError):
        asyncio.run(
            dispatch_order_intent(
                _intent(),
                replace(_connection(), environment=BrokerEnvironment.LIVE),
                broker,
                None,
            )
        )


def test_timeout_replay_has_deterministic_receipt_identity() -> None:
    """Identical timed-out material produces the same receipt identity."""

    async def timeout_once() -> ExecutionReceipt:
        """Dispatch one intentionally timed-out Broker placement."""
        return await _dispatch_order_intent(
            _intent(),
            _connection(),
            cast("BrokerAdapter", _TimeoutAdapter()),
            None,
            operation_timeout_seconds=Decimal("0.001"),
            clock=lambda: NOW,
        )

    first = asyncio.run(timeout_once())
    second = asyncio.run(timeout_once())
    assert first.status == "unknown_outcome"
    assert first.receipt_id == second.receipt_id
    assert first.received_at == second.received_at == NOW
