"""Unit tests for deterministic Simulation execution pricing."""
# ruff: noqa: INP001

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.simulator.execution import (
    ExecutionProfile,
    SessionInterval,
    price_order,
)
from app.services.simulator.timeline import Tick
from app.services.trading import OrderIntent, TradingRoute


def _intent(side: str = "BUY") -> OrderIntent:
    """Build one valid Trading-owned market intent."""
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    return OrderIntent(
        client_order_id=f"order-{side.lower()}",
        request_id="req-test",
        workflow_id="wf-test",
        correlation_id="cor-test",
        route=TradingRoute.SIM,
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
