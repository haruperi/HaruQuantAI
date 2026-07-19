"""Unit tests for deterministic Simulation order matching."""
# ruff: noqa: INP001

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import app.services.simulator.execution.matching as matching_module
import pytest
from app.services.simulator.errors import SimulationError
from app.services.simulator.execution import (
    ExecutionProfile,
    SessionInterval,
    match_order,
)
from app.services.simulator.execution.matching import evaluate_protective_exit
from app.services.simulator.timeline import Tick
from app.services.trading import OrderIntent, TradingRoute


def _intent() -> OrderIntent:
    """Build one IOC market intent."""
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    return OrderIntent(
        client_order_id="order-ioc",
        request_id="req-test",
        workflow_id="wf-test",
        correlation_id="cor-test",
        route=TradingRoute.SIM,
        provider_id=None,
        account_id="account",
        strategy_id="strategy",
        strategy_version="v1",
        source_intent_id="intent-ioc",
        symbol="EURUSD",
        action="submit_order",
        side="BUY",
        order_type="MARKET",
        quantity_unit="lot",
        approved_volume=Decimal(2),
        risk_approved_volume=Decimal(2),
        time_in_force="IOC",
        idempotency_hash="a" * 64,
        canonical_material_version="v1",
        risk_decision_id="risk",
        action_policy_verdict_id="verdict",
        approval_token_ref="approval",
        created_at=instant,
        valid_until=instant + timedelta(days=1),
    )


def test_match_order_journals_ioc_remainder() -> None:
    """Return exact partial and cancelled remainder quantities."""
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    tick = Tick(
        symbol="EURUSD",
        timestamp=instant,
        bid=Decimal("1.1"),
        ask=Decimal("1.2"),
        source_id="fixture",
        sequence=1,
        available_at=instant,
        volume=Decimal(1),
        volume_unit="lot",
    )
    profile = ExecutionProfile(
        slippage_mode="none",
        fixed_slippage_points=Decimal(0),
        point_value=Decimal("0.0001"),
        price_quantum=Decimal("0.0001"),
        maximum_slippage_points=Decimal(0),
        maximum_gap_points=Decimal(10),
        liquidity_mode="tick_volume",
        participation_rate=Decimal(1),
        sessions=(SessionInterval(start_week_second=0, end_week_second=604_800),),
    )
    result = match_order(_intent(), tick, profile)
    assert result.status == "partial"
    assert result.filled_quantity == Decimal(1)
    assert result.cancelled_quantity == Decimal(1)


def test_match_order_rejects_ambiguous_event_priority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fail closed if configured same-tick precedence becomes ambiguous."""
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    tick = Tick(
        symbol="EURUSD",
        timestamp=instant,
        bid=Decimal("1.1"),
        ask=Decimal("1.2"),
        source_id="fixture",
        sequence=1,
        available_at=instant,
    )
    profile = ExecutionProfile(
        slippage_mode="none",
        fixed_slippage_points=Decimal(0),
        point_value=Decimal("0.0001"),
        price_quantum=Decimal("0.0001"),
        maximum_slippage_points=Decimal(0),
        maximum_gap_points=Decimal(10),
        liquidity_mode="unbounded",
        participation_rate=Decimal(0),
        sessions=(SessionInterval(start_week_second=0, end_week_second=604_800),),
    )
    monkeypatch.setattr(
        matching_module,
        "SAME_TICK_PRIORITY",
        ("STOP_LOSS", "STOP_LOSS", "PENDING_ACTIVATION"),
    )
    with pytest.raises(SimulationError) as captured:
        match_order(_intent(), tick, profile)
    assert captured.value.code == "SIM_EVENT_PRIORITY_AMBIGUOUS"


def _exit_tick(bid: Decimal, ask: Decimal) -> Tick:
    """Build one canonical tick at an explicit price.

    Args:
        bid: Explicit bid price.
        ask: Explicit ask price.

    Returns:
        Canonical tick.
    """
    instant = datetime(2025, 1, 1, tzinfo=UTC) + timedelta(seconds=1)
    return Tick(
        symbol="EURUSD",
        timestamp=instant,
        bid=bid,
        ask=ask,
        source_id="fixture",
        sequence=1,
        available_at=instant,
    )


def _position(
    side: str,
    stop_loss: Decimal | None,
    take_profit: Decimal | None,
) -> dict[str, object]:
    """Build one open simulated position projection.

    Args:
        side: Position direction.
        stop_loss: Optional protective stop price.
        take_profit: Optional protective target price.

    Returns:
        Open position mapping.
    """
    return {"side": side, "stop_loss": stop_loss, "take_profit": take_profit}


def test_protective_exit_is_none_when_no_level_is_crossed() -> None:
    """Leave a position open when neither protective level triggers."""
    position = _position("BUY", Decimal("1.0000"), Decimal("1.5000"))
    tick = _exit_tick(Decimal("1.1"), Decimal("1.2"))
    assert evaluate_protective_exit(position, tick) is None


def test_long_stop_loss_triggers_on_adverse_bid() -> None:
    """Trigger a long stop when the exit bid falls to the stop."""
    position = _position("BUY", Decimal("1.1500"), None)
    tick = _exit_tick(Decimal("1.1000"), Decimal("1.2000"))
    assert evaluate_protective_exit(position, tick) == "STOP_LOSS"


def test_short_stop_loss_triggers_on_adverse_ask() -> None:
    """Trigger a short stop when the exit ask rises to the stop."""
    position = _position("SELL", Decimal("1.1500"), None)
    tick = _exit_tick(Decimal("1.1000"), Decimal("1.2000"))
    assert evaluate_protective_exit(position, tick) == "STOP_LOSS"


def test_long_take_profit_triggers_on_favourable_bid() -> None:
    """Trigger a long target when the exit bid reaches the target."""
    position = _position("BUY", None, Decimal("1.0500"))
    tick = _exit_tick(Decimal("1.1000"), Decimal("1.2000"))
    assert evaluate_protective_exit(position, tick) == "TAKE_PROFIT"


def test_stop_loss_wins_same_tick_conflict_with_take_profit() -> None:
    """Resolve a same-tick conflict by SAME_TICK_PRIORITY, so the stop wins."""
    position = _position("BUY", Decimal("1.1500"), Decimal("1.0500"))
    tick = _exit_tick(Decimal("1.1000"), Decimal("1.2000"))
    assert evaluate_protective_exit(position, tick) == "STOP_LOSS"


def test_protective_exit_fails_closed_on_undeclared_precedence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject a detected condition that has no declared precedence."""
    monkeypatch.setattr(
        matching_module,
        "SAME_TICK_PRIORITY",
        ("TAKE_PROFIT", "PENDING_ACTIVATION", "UNUSED"),
    )
    position = _position("BUY", Decimal("1.1500"), None)
    tick = _exit_tick(Decimal("1.1000"), Decimal("1.2000"))
    with pytest.raises(SimulationError) as captured:
        evaluate_protective_exit(position, tick)
    assert captured.value.code == "SIM_EVENT_PRIORITY_AMBIGUOUS"
