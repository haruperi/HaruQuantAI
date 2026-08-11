"""Unit tests for deterministic Simulation execution pricing."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest
from app.services.simulator.errors import SimulationError
from app.services.simulator.execution import (
    ExecutionProfile,
    SessionInterval,
    price_order,
)
from app.services.simulator.timeline import Tick
from app.services.trading import create_order_intent

OrderIntent = Any


def _intent(side: str = "BUY") -> OrderIntent:
    """Build one valid Trading-owned market intent."""
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    return create_order_intent(
        client_order_id=f"order-{side.lower()}",
        request_id="req-123e4567-e89b-42d3-a456-426614174000",
        workflow_id="wf-123e4567-e89b-42d3-a456-426614174001",
        correlation_id="cor-123e4567-e89b-42d3-a456-426614174002",
        route="sim",
        provider_id=None,
        account_id="account",
        strategy_id="strategy",
        strategy_version="v1",
        source_intent_id=f"intent-{side.lower()}",
        symbol="EURUSD",
        action="submit_order",
        side=side,
        order_type="MARKET",
        quantity_unit="lot",
        approved_volume=Decimal(1),
        risk_approved_volume=Decimal(1),
        time_in_force="FOK",
        idempotency_hash="a" * 64,
        canonical_material_version="v1",
        risk_decision_id="risk",
        action_policy_verdict_id="verdict",
        approval_token_ref="approval",
        created_at=instant,
        valid_until=instant + timedelta(days=1),
    )


def _profile() -> ExecutionProfile:
    """Build an explicit no-slippage execution profile."""
    return ExecutionProfile(
        slippage_mode="none",
        fixed_slippage_points=Decimal(0),
        point_value=Decimal("0.00001"),
        price_quantum=Decimal("0.00001"),
        maximum_slippage_points=Decimal(0),
        maximum_gap_points=Decimal(10),
        liquidity_mode="unbounded",
        participation_rate=Decimal(0),
        sessions=(SessionInterval(start_week_second=0, end_week_second=604_800),),
    )


def _tick() -> Tick:
    """Build one canonical execution tick."""
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    return Tick(
        symbol="EURUSD",
        timestamp=instant,
        bid=Decimal("1.10000"),
        ask=Decimal("1.10002"),
        source_id="fixture",
        sequence=1,
        available_at=instant,
    )


def test_price_order_uses_side_correct_bid_ask() -> None:
    """Price BUY at ask and SELL at bid."""
    assert price_order(_intent("BUY"), _tick(), _profile()) == Decimal("1.10002")
    assert price_order(_intent("SELL"), _tick(), _profile()) == Decimal("1.10000")


def test_execution_profile_rejects_invalid_policy_relationships() -> None:
    """Reject invalid sessions, prices, slippage, liquidity, and empty calendars."""
    with pytest.raises(ValueError, match=r".+"):
        SessionInterval(start_week_second=1, end_week_second=1)
    base = _profile().model_dump(mode="python")
    for update in (
        {"fixed_slippage_points": Decimal(-1)},
        {"point_value": Decimal(0)},
        {
            "slippage_mode": "none",
            "fixed_slippage_points": Decimal(1),
            "maximum_slippage_points": Decimal(1),
        },
        {
            "slippage_mode": "fixed_points",
            "fixed_slippage_points": Decimal(2),
            "maximum_slippage_points": Decimal(1),
        },
        {
            "liquidity_mode": "tick_volume",
            "participation_rate": Decimal(0),
        },
        {"liquidity_mode": "unbounded", "participation_rate": Decimal("0.5")},
        {"sessions": ()},
    ):
        with pytest.raises(ValueError, match=r".+"):
            ExecutionProfile(**(base | update))


def test_price_order_rejects_invalid_price_and_slippage_outcomes() -> None:
    """Reject invalid observed prices and adverse slippage below zero."""
    invalid_tick = SimpleNamespace(bid=Decimal("NaN"), ask=Decimal("NaN"))
    with pytest.raises(SimulationError, match="invalid"):
        price_order(_intent(), invalid_tick, _profile())
    slipped = ExecutionProfile(
        slippage_mode="fixed_points",
        fixed_slippage_points=Decimal(2),
        point_value=Decimal("0.1"),
        price_quantum=Decimal("0.1"),
        maximum_slippage_points=Decimal(2),
        maximum_gap_points=Decimal(10),
        liquidity_mode="unbounded",
        participation_rate=Decimal(0),
        sessions=(SessionInterval(start_week_second=0, end_week_second=604_800),),
    )
    low_tick = SimpleNamespace(bid=Decimal("0.1"), ask=Decimal("0.2"))
    with pytest.raises(SimulationError, match="invalid"):
        price_order(_intent("SELL"), low_tick, slipped)


def test_price_realistic_execution_error_paths() -> None:
    """Test realism pricing error branches."""
    from app.services.simulator import build_latency_profile, price_realistic_execution

    latency = build_latency_profile(
        market_ms=Decimal(1),
        client_ms=Decimal(1),
        network_ms=Decimal(1),
        broker_ms=Decimal(1),
        venue_ms=Decimal(1),
        report_ms=Decimal(1),
        processing_ms=Decimal(1),
    )

    # Test invalid (non-positive) base price
    with pytest.raises(SimulationError, match="invalid"):
        price_realistic_execution(
            side="BUY",
            base_price=Decimal(0),
            quantity=Decimal(1),
            point_value=Decimal("0.0001"),
            price_quantum=Decimal("0.0001"),
            fixed_slippage_points=Decimal(0),
            impact_points_per_unit=Decimal(0),
            maximum_total_points=Decimal(10),
            latency=latency,
        )

    # Test negative config values
    with pytest.raises(SimulationError, match="non-negative"):
        price_realistic_execution(
            side="BUY",
            base_price=Decimal("1.08"),
            quantity=Decimal(1),
            point_value=Decimal("0.0001"),
            price_quantum=Decimal("0.0001"),
            fixed_slippage_points=Decimal(-1),
            impact_points_per_unit=Decimal(0),
            maximum_total_points=Decimal(10),
            latency=latency,
        )

    # Test slippage exceeded
    with pytest.raises(SimulationError, match="exceeds maximum"):
        price_realistic_execution(
            side="BUY",
            base_price=Decimal("1.08"),
            quantity=Decimal(10),
            point_value=Decimal("0.0001"),
            price_quantum=Decimal("0.0001"),
            fixed_slippage_points=Decimal(5),
            impact_points_per_unit=Decimal(1),
            maximum_total_points=Decimal(5),
            latency=latency,
        )

    # Test execution price <= 0 on SELL
    with pytest.raises(SimulationError, match="invalid price"):
        price_realistic_execution(
            side="SELL",
            base_price=Decimal("0.0001"),
            quantity=Decimal(1),
            point_value=Decimal("0.001"),
            price_quantum=Decimal("0.0001"),
            fixed_slippage_points=Decimal(10),
            impact_points_per_unit=Decimal(0),
            maximum_total_points=Decimal(100),
            latency=latency,
        )
