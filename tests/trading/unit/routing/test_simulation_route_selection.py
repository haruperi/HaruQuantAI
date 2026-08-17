"""Exact simulation route/environment admission tests."""

# ruff: noqa: INP001

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.brokers import build_broker_connection_config
from app.services.trading.contracts import ExecutionReceipt, OrderIntent, TradingError
from app.services.trading.routing.dispatcher import _dispatch_order_intent_value
from tests.trading.unit.routing.test_dispatcher import _Adapter

NOW = datetime(2026, 8, 15, tzinfo=UTC)


def _intent(route: str = "sim") -> OrderIntent:
    """Build one bounded executable intent.

    Args:
        route: Exact Trading route.

    Returns:
        Validated intent.
    """
    return OrderIntent(
        source_intent_id="intent-route-selection",
        client_order_id="client-route-selection",
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        account_id="account-route-selection",
        strategy_id="strategy-route-selection",
        strategy_version="v1",
        idempotency_hash="a" * 64,
        action="submit_order",
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        approved_volume=Decimal(1),
        risk_approved_volume=Decimal(1),
        quantity_unit="lots",
        route=route,  # type: ignore[arg-type]
        provider_id=None if route == "sim" else "mt5",
        canonical_material_version="v1",
        risk_decision_id="risk-route-selection",
        action_policy_verdict_id="verdict-route-selection",
        approval_token_ref="approval-route-selection",
        created_at=NOW,
        valid_until=NOW + timedelta(minutes=5),
    )


def _receipt(intent: OrderIntent) -> ExecutionReceipt:
    """Build one exact-scope Simulator receipt."""
    return ExecutionReceipt(
        receipt_id="sim-route-receipt",
        intent_id=intent.source_intent_id,
        client_order_id=intent.client_order_id,
        route="sim",
        authority="simulator",
        provider_order_id="sim-route-order",
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


def _dispatch(intent: OrderIntent) -> ExecutionReceipt:
    """Dispatch with deterministic runtime policy.

    Args:
        intent: Intent to dispatch.
    Returns:
        Confirmed receipt.
    """

    async def source(value: OrderIntent) -> ExecutionReceipt:
        assert value is intent
        return _receipt(value)

    return asyncio.run(
        _dispatch_order_intent_value(
            intent,
            None,
            None,
            operation_timeout_seconds=Decimal(1),
            clock=lambda: NOW,
            simulation_execution_source=source,
        )
    )


def test_sim_route_requires_exact_simulation_pair() -> None:
    """The exact sim/simulation pair dispatches once."""
    assert _dispatch(_intent()).status == "accepted"


@pytest.mark.parametrize("environment", ["live", "demo", "testnet", "sandbox"])
def test_sim_route_rejects_every_other_environment(environment: str) -> None:
    """No provider-like environment aliases simulation.

    Args:
        environment: Non-simulation environment under test.
    """
    connection = build_broker_connection_config("sim", environment)
    with pytest.raises(TradingError) as captured:
        asyncio.run(
            _dispatch_order_intent_value(
                _intent(),
                connection,
                _Adapter(broker="sim", environment="simulation"),
                operation_timeout_seconds=Decimal(1),
                clock=lambda: NOW,
                simulation_execution_source=lambda _: None,
            )
        )
    assert captured.value.code == "SCOPE_MISMATCH"


def test_sim_route_rejects_disabled_and_wrong_identity() -> None:
    """Admission fails before callback for disabled or wrong identity."""
    exact = build_broker_connection_config("sim", "simulation")
    with pytest.raises(TradingError) as disabled:
        asyncio.run(
            _dispatch_order_intent_value(
                _intent(),
                replace(exact, provider_enabled=False),
                _Adapter(broker="sim", environment="simulation"),
                operation_timeout_seconds=Decimal(1),
                clock=lambda: NOW,
                simulation_execution_source=lambda _: None,
            )
        )
    assert disabled.value.code == "SCOPE_MISMATCH"
    wrong = build_broker_connection_config("mt5", "simulation")
    with pytest.raises(TradingError) as mismatch:
        asyncio.run(
            _dispatch_order_intent_value(
                _intent(),
                wrong,
                _Adapter(broker="sim", environment="simulation"),
                operation_timeout_seconds=Decimal(1),
                clock=lambda: NOW,
                simulation_execution_source=lambda _: None,
            )
        )
    assert mismatch.value.code == "SCOPE_MISMATCH"


@pytest.mark.parametrize("route", ["demo", "live"])
def test_non_sim_routes_forbid_simulation_environment(route: str) -> None:
    """Every non-sim executable route rejects simulation.

    Args:
        route: Non-sim route under test.
    """
    connection = build_broker_connection_config("mt5", "simulation")
    with pytest.raises(TradingError) as captured:
        asyncio.run(
            _dispatch_order_intent_value(
                _intent(route),
                connection,
                _Adapter(),
                operation_timeout_seconds=Decimal(1),
                clock=lambda: NOW,
            )
        )
    assert captured.value.code == "SCOPE_MISMATCH"
