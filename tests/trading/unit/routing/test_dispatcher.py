"""Unit tests for the sole asynchronous Trading dispatch boundary."""

# ruff: noqa: INP001

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from app.contracts.common.models import StandardResponse
from app.services.brokers import (
    build_broker_connection_config,
    build_broker_value,
    get_broker_capability_id,
    get_broker_environment,
    get_broker_error_code,
    get_broker_id,
    get_broker_value_field,
)
from app.services.trading import build_order_intent, parse_order_intent
from app.services.trading.contracts import ExecutionReceipt, OrderIntent, TradingError
from app.services.trading.routing.dispatcher import (
    _broker_evidence,
)
from app.services.trading.routing.dispatcher import (
    dispatch_order_intent as _dispatch_order_intent,
)
from tests.brokers.response_factory import broker_response

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)
BROKER_REQUEST_ID = "req-dd37fc1c-2cd6-4d66-9f9a-7a7f9a2482ef"


def test_broker_evidence_rejects_incomplete_or_malformed_metadata() -> None:
    """Authority metadata cannot be inferred when absent or malformed."""
    with pytest.raises(TradingError, match="MALFORMED_RECEIPT"):
        _broker_evidence(SimpleNamespace(metadata=SimpleNamespace(extensions={})))
    extensions = {
        "broker": "mt5",
        "operation": "place_order",
        "environment": "demo",
        "timestamp": "not-a-timestamp",
    }
    with pytest.raises(TradingError, match="MALFORMED_RECEIPT"):
        _broker_evidence(
            SimpleNamespace(metadata=SimpleNamespace(extensions=extensions))
        )


async def dispatch_order_intent(
    intent: OrderIntent,
    connection: object | None,
    broker_adapter: object | None,
) -> ExecutionReceipt:
    """Invoke the public dispatcher with explicit deterministic runtime policy."""

    async def simulation_source(value: OrderIntent) -> ExecutionReceipt:
        """Return one exact-scope virtual receipt for SIM tests."""
        return ExecutionReceipt(
            receipt_id="sim-receipt-001",
            intent_id=value.source_intent_id,
            client_order_id=value.client_order_id,
            route="sim",
            authority="simulator",
            provider_order_id="sim-order-001",
            status="accepted",
            requested_quantity=value.approved_volume,
            filled_quantity=Decimal(0),
            authority_timestamp=NOW,
            received_at=NOW,
            response_classification="confirmed",
            retry_safe=False,
            reconciliation_required=False,
            request_id=value.request_id,
            correlation_id=value.correlation_id,
        )

    result = await _dispatch_order_intent(
        intent,
        None if intent.route.value == "sim" else connection,
        None if intent.route.value == "sim" else broker_adapter,
        operation_timeout_seconds=Decimal(10),
        clock=lambda: NOW,
        simulation_execution_source=(
            simulation_source if intent.route.value == "sim" else None
        ),
    )
    if result.status == "error" or not isinstance(result.data, ExecutionReceipt):
        code = "UNKNOWN_ERROR" if result.error is None else result.error.code
        raise TradingError(code, "Dispatcher response failed")
    return result.data


def _intent(*, route: str = "demo", action: str = "submit_order") -> OrderIntent:
    """Build one complete executable intent."""
    return OrderIntent(
        client_order_id="client-order-001",
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
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


def test_order_intent_v1_transport_requires_complete_lineage() -> None:
    """Operational intent transport round-trips only complete governed lineage."""
    material = _intent(route="sim").model_dump()
    with pytest.raises(ValueError, match="complete versioned lineage"):
        build_order_intent(**material)
    material.update(
        {
            "trade_plan_id": "plan-001",
            "trade_plan_version": "v1",
            "risk_decision_version": "v1",
            "policy_version": "v1",
            "profile_version": "v1",
        }
    )
    mapping = build_order_intent(**material)
    assert parse_order_intent(mapping).trade_plan_id == "plan-001"


def _connection() -> object:
    """Build explicit demo Broker connection material."""
    return build_broker_connection_config(
        broker_id="mt5",
        environment="demo",
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


def _sim_connection() -> object:
    """Build the exact enabled simulation Broker connection material."""
    return build_broker_connection_config(
        broker_id="sim",
        environment="simulation",
        provider_enabled=True,
    )


class _Adapter:
    """Minimal test adapter exposing the invoked Broker mutation."""

    contract_version = "v1"
    schema_id = "brokers.adapter.v1"

    def __init__(self, *, broker: str = "mt5", environment: str = "demo") -> None:
        """Initialize observable mutation evidence."""
        self.calls = 0
        self.request: object | None = None
        self.mutations: list[object] = []
        self.broker = broker
        self.environment = environment

    def _order_result(
        self,
        operation: object,
    ) -> StandardResponse[object]:
        """Build one acknowledged Broker order result."""
        return broker_response(
            operation,
            broker=get_broker_id(self.broker),
            request_id=BROKER_REQUEST_ID,
            timestamp=NOW,
            environment=get_broker_environment(self.environment),
            adapter_version="test-v1",
            data=build_broker_value(
                "order_result",
                acknowledged=True,
                outcome="ACCEPTED",
                retrieved_at=NOW,
                order_id="broker-order-001",
            ),
        )

    async def place_order(
        self,
        request: object,
    ) -> StandardResponse[object]:
        """Record and acknowledge one Broker placement."""
        self.calls += 1
        self.request = request
        self.mutations.append(request)
        return self._order_result(get_broker_capability_id("place_order"))

    async def modify_order(
        self,
        request: object,
    ) -> StandardResponse[object]:
        """Record and acknowledge one Broker order modification."""
        self.calls += 1
        self.mutations.append(request)
        return self._order_result(get_broker_capability_id("modify_order"))

    async def cancel_order(
        self,
        order_id: str,
        client_request_id: str | None = None,
    ) -> StandardResponse[object]:
        """Record and acknowledge one Broker cancellation."""
        self.calls += 1
        self.mutations.append((order_id, client_request_id))
        return self._order_result(get_broker_capability_id("cancel_order"))

    async def modify_position(
        self,
        request: object,
    ) -> StandardResponse[object]:
        """Record and acknowledge one Broker position modification."""
        self.calls += 1
        self.mutations.append(request)
        return broker_response(
            get_broker_capability_id("modify_position"),
            broker=get_broker_id(self.broker),
            request_id=BROKER_REQUEST_ID,
            timestamp=NOW,
            environment=get_broker_environment(self.environment),
            adapter_version="test-v1",
            data=build_broker_value(
                "position",
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
        request: object,
    ) -> StandardResponse[object]:
        """Record and acknowledge one Broker position close."""
        self.calls += 1
        self.mutations.append(request)
        return self._order_result(get_broker_capability_id("close_position"))


class _ErrorAdapter(_Adapter):
    """Test adapter returning one canonical Broker failure."""

    def __init__(
        self, code: object, *, broker: str = "mt5", environment: str = "demo"
    ) -> None:
        """Initialize the selected Broker failure code."""
        super().__init__(broker=broker, environment=environment)
        self.code = code

    async def place_order(
        self,
        request: object,
    ) -> StandardResponse[object]:
        """Return one explicit or ambiguous Broker failure."""
        self.calls += 1
        self.mutations.append(request)
        return self._error_result(get_broker_capability_id("place_order"))

    def _error_result(self, operation: object) -> StandardResponse[object]:
        """Return one selected canonical Broker failure."""
        return broker_response(
            operation,
            broker=get_broker_id(self.broker),
            request_id=BROKER_REQUEST_ID,
            timestamp=NOW,
            environment=get_broker_environment(self.environment),
            adapter_version="test-v1",
            error=build_broker_value(
                "error", code=self.code, message="Redacted Broker failure"
            ),
        )

    async def cancel_order(
        self, order_id: str, client_request_id: str | None = None
    ) -> StandardResponse[object]:
        """Return the selected failure for cancellation."""
        self.calls += 1
        self.mutations.append((order_id, client_request_id))
        return self._error_result(get_broker_capability_id("cancel_order"))


class _TimeoutAdapter(_Adapter):
    """Test adapter that exceeds every supplied short operation timeout."""

    async def place_order(
        self,
        request: object,
    ) -> StandardResponse[object]:
        """Remain pending until the dispatch boundary cancels the call."""
        await asyncio.sleep(1)
        return await super().place_order(request)


class _RaisingAdapter(_Adapter):
    """Test adapter raising an unexpected provider exception."""

    async def place_order(
        self,
        request: object,
    ) -> StandardResponse[object]:
        """Raise secret-bearing provider text at the external boundary."""
        self.calls += 1
        self.mutations.append(request)
        raise RuntimeError("password=hunter2")


def test_dispatch_has_single_mutation_boundary() -> None:
    """Each route invokes exactly one selected async mutation authority."""
    adapter = _Adapter()
    receipt = asyncio.run(
        dispatch_order_intent(
            _intent(),
            _connection(),
            adapter,
        )
    )
    assert adapter.calls == 1
    assert receipt.status == "accepted"
    assert adapter.request is not None
    assert get_broker_value_field(
        adapter.request, "environment"
    ) == get_broker_environment("demo")
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
                adapter,
            )
        )
    assert (
        get_broker_value_field(adapter.mutations[1], "order_id") == "broker-order-001"
    )
    assert adapter.mutations[2] == ("broker-order-001", None)
    assert (
        get_broker_value_field(adapter.mutations[3], "position_id")
        == "broker-position-001"
    )
    assert (
        get_broker_value_field(adapter.mutations[4], "position_id")
        == "broker-position-001"
    )
    assert (
        get_broker_value_field(adapter.mutations[5], "position_id")
        == "broker-position-001"
    )
    assert get_broker_value_field(adapter.mutations[5], "quantity_unit") == "lots"

    rejected_adapter = _ErrorAdapter(get_broker_error_code("BROKER_REQUEST_REJECTED"))
    rejected_receipt = asyncio.run(
        dispatch_order_intent(
            _intent(),
            _connection(),
            rejected_adapter,
        )
    )
    assert rejected_receipt.status == "rejected"
    assert rejected_receipt.response_classification == "confirmed"
    assert not rejected_receipt.reconciliation_required
    limited_adapter = _ErrorAdapter(get_broker_error_code("BROKER_RATE_LIMITED"))
    limited_response = asyncio.run(
        _dispatch_order_intent(
            _intent(),
            _connection(),
            limited_adapter,
            operation_timeout_seconds=Decimal(10),
            clock=lambda: NOW,
        )
    )
    assert limited_response.status == "error"
    assert limited_response.data is None
    assert limited_response.error is not None
    assert limited_response.error.code == "UNKNOWN_OUTCOME"
    assert limited_response.metadata.extensions["legacy_status"] == "unknown_outcome"

    seen: list[OrderIntent] = []

    async def simulation_source(intent: OrderIntent) -> ExecutionReceipt:
        """Record the unchanged intent and return confirmed virtual evidence."""
        seen.append(intent)
        return ExecutionReceipt(
            receipt_id="sim-receipt-direct",
            intent_id=intent.source_intent_id,
            client_order_id=intent.client_order_id,
            route="sim",
            authority="simulator",
            provider_order_id="sim-order-direct",
            status="accepted",
            requested_quantity=intent.approved_volume,
            filled_quantity=Decimal(0),
            authority_timestamp=NOW,
            received_at=NOW,
            response_classification="confirmed",
            retry_safe=False,
            reconciliation_required=False,
            request_id=intent.request_id,
            correlation_id=intent.correlation_id,
        )

    intent = _intent(route="sim")
    sim_receipt = asyncio.run(
        _dispatch_order_intent(
            intent,
            None,
            None,
            operation_timeout_seconds=Decimal(10),
            clock=lambda: NOW,
            simulation_execution_source=simulation_source,
        )
    )
    assert sim_receipt.data is not None
    assert seen == [intent]
    assert sim_receipt.data.status == "accepted"


def test_dispatch_rejects_mismatched_authority_selection() -> None:
    """Absent, disabled, or cross-route authorities fail before mutation."""
    adapter = _Adapter()
    broker = adapter
    from app.services.trading.routing.dispatcher import _dispatch_order_intent_value

    with pytest.raises(TradingError):
        asyncio.run(
            _dispatch_order_intent_value(
                _intent(route="sim"),
                None,
                None,
                operation_timeout_seconds=Decimal(10),
                clock=lambda: NOW,
            )
        )
    with pytest.raises(TradingError):
        asyncio.run(dispatch_order_intent(_intent(), None, None))
    with pytest.raises(TradingError):
        asyncio.run(
            _dispatch_order_intent_value(
                _intent(route="sim"),
                _connection(),
                broker,
                operation_timeout_seconds=Decimal(10),
                clock=lambda: NOW,
                simulation_execution_source=lambda _: None,
            )
        )
    with pytest.raises(TradingError):
        asyncio.run(
            dispatch_order_intent(
                _intent(),
                replace(_connection(), provider_enabled=False),
                broker,
            )
        )
    with pytest.raises(TradingError):
        asyncio.run(
            dispatch_order_intent(
                _intent(),
                replace(_connection(), broker_id=get_broker_id("ctrader")),
                broker,
            )
        )
    with pytest.raises(TradingError):
        asyncio.run(
            dispatch_order_intent(
                _intent(route="live"),
                _connection(),
                broker,
            )
        )
    with pytest.raises(TradingError):
        asyncio.run(
            dispatch_order_intent(
                _intent(),
                replace(_connection(), environment=get_broker_environment("live")),
                broker,
            )
        )


def test_timeout_replay_has_deterministic_receipt_identity() -> None:
    """Identical timed-out material produces the same receipt identity."""

    async def timeout_once() -> ExecutionReceipt:
        """Dispatch one intentionally timed-out Broker placement."""
        from app.services.trading.routing.dispatcher import _dispatch_order_intent_value

        return await _dispatch_order_intent_value(
            _intent(),
            _connection(),
            _TimeoutAdapter(),
            operation_timeout_seconds=Decimal("0.001"),
            clock=lambda: NOW,
        )

    first = asyncio.run(timeout_once())
    second = asyncio.run(timeout_once())
    assert first.status == "unknown_outcome"
    assert first.receipt_id == second.receipt_id
    assert first.received_at == second.received_at == NOW


def test_provider_exception_becomes_redacted_unknown_receipt() -> None:
    """Unexpected provider exceptions never cross the Trading public boundary."""
    response = asyncio.run(
        _dispatch_order_intent(
            _intent(),
            _connection(),
            _RaisingAdapter(),
            operation_timeout_seconds=Decimal(10),
            clock=lambda: NOW,
        )
    )
    assert response.status == "error"
    assert response.data is None
    assert response.error is not None
    assert response.error.code == "UNKNOWN_OUTCOME"
    assert response.metadata.extensions["legacy_status"] == "unknown_outcome"
    assert "hunter2" not in response.model_dump_json()
