"""Unit tests for the canonical Simulation tick engine."""
# ruff: noqa: INP001

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.simulator.accounting import (
    AccountLedger,
    ExecutionCostModel,
    SymbolSpecification,
)
from app.services.simulator.errors import SimulationError
from app.services.simulator.execution import (
    EventDrivenExecutionEngine,
    ExecutionProfile,
    SessionInterval,
)
from app.services.simulator.journal import JournalWriter
from app.services.simulator.timeline import Tick
from app.services.trading import OrderIntent, TradingRoute
from tests.simulator._fixtures.sqlite_store import SqliteSimulationStateStore


def _engine(tmp_path: Path, suffix: str) -> EventDrivenExecutionEngine:
    """Build one isolated deterministic engine."""
    store = SqliteSimulationStateStore(tmp_path / f"{suffix}.db", tmp_path / suffix)
    writer = JournalWriter(store, f"run-{suffix}", "req-test", "cor-test")
    writer.append(
        "run_started",
        {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
        datetime(2025, 1, 1, tzinfo=UTC),
    )
    ledger = AccountLedger(
        Decimal(10_000),
        "USD",
        SymbolSpecification(
            minimum_volume=Decimal("0.01"),
            maximum_volume=Decimal(100),
            volume_step=Decimal("0.01"),
            contract_size=Decimal(100_000),
            leverage=Decimal(100),
        ),
        ExecutionCostModel(
            commission_per_lot_per_side=Decimal(0),
            long_swap_per_lot_rollover=Decimal(0),
            short_swap_per_lot_rollover=Decimal(0),
        ),
    )
    profile = ExecutionProfile(
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
    return EventDrivenExecutionEngine(ledger, writer, profile, "v1")


def _intent() -> OrderIntent:
    """Build one approved sim market intent."""
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    return OrderIntent(
        client_order_id="order-engine",
        request_id="req-test",
        workflow_id="wf-test",
        correlation_id="cor-test",
        route=TradingRoute.SIM,
        provider_id=None,
        account_id="account",
        strategy_id="strategy",
        strategy_version="v1",
        source_intent_id="intent-engine",
        symbol="EURUSD",
        action="submit_order",
        side="BUY",
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


def _tick() -> Tick:
    """Build the next eligible execution tick."""
    instant = datetime(2025, 1, 1, tzinfo=UTC) + timedelta(seconds=1)
    return Tick(
        symbol="EURUSD",
        timestamp=instant,
        bid=Decimal("1.10000"),
        ask=Decimal("1.10002"),
        source_id="fixture",
        sequence=1,
        available_at=instant,
    )


def test_execute_tick_is_deterministic(tmp_path: Path) -> None:
    """Produce equal receipts from equal isolated engine state."""
    first = _engine(tmp_path, "first")
    second = _engine(tmp_path, "second")
    first.submit_order(_intent())
    second.submit_order(_intent())
    assert first.execute_tick(_tick()) == second.execute_tick(_tick())


def test_execute_tick_rejects_missing_order_state(tmp_path: Path) -> None:
    """Fail closed when pending and authoritative order state diverge."""
    engine = _engine(tmp_path, "missing-order")
    engine.submit_order(_intent())
    engine._orders.clear()
    with pytest.raises(SimulationError) as captured:
        engine.execute_tick(_tick())
    assert captured.value.code == "SIM_ORDER_NOT_FOUND"


def _protected_intent(
    stop_loss: Decimal | None,
    take_profit: Decimal | None,
) -> OrderIntent:
    """Build one approved sim intent carrying protective levels.

    Args:
        stop_loss: Optional protective stop price.
        take_profit: Optional protective target price.

    Returns:
        Trading-owned order intent with protective levels.
    """
    return _intent().model_copy(
        update={"stop_loss": stop_loss, "take_profit": take_profit}
    )


def _later_tick(bid: Decimal, ask: Decimal, sequence: int) -> Tick:
    """Build a later canonical tick at an explicit price.

    Args:
        bid: Explicit bid price.
        ask: Explicit ask price.
        sequence: Strictly increasing tick sequence.

    Returns:
        Canonical tick.
    """
    instant = datetime(2025, 1, 1, tzinfo=UTC) + timedelta(seconds=1 + sequence)
    return Tick(
        symbol="EURUSD",
        timestamp=instant,
        bid=bid,
        ask=ask,
        source_id="fixture",
        sequence=1 + sequence,
        available_at=instant,
    )


def test_execute_tick_closes_position_on_stop_loss(tmp_path: Path) -> None:
    """Close an open long position when the bid crosses its stop."""
    engine = _engine(tmp_path, "stop-loss")
    engine.submit_order(_protected_intent(Decimal("1.09000"), None))
    engine.execute_tick(_tick())
    assert engine.snapshot()["positions"]
    engine.execute_tick(_later_tick(Decimal("1.08500"), Decimal("1.08502"), 1))
    assert not engine.snapshot()["positions"]
    assert len(engine.closed_trades) == 1
    assert engine.closed_trades[0].exit_price == Decimal("1.08500")


def test_execute_tick_closes_position_on_take_profit(tmp_path: Path) -> None:
    """Close an open long position when the bid reaches its target."""
    engine = _engine(tmp_path, "take-profit")
    engine.submit_order(_protected_intent(None, Decimal("1.11000")))
    engine.execute_tick(_tick())
    engine.execute_tick(_later_tick(Decimal("1.11500"), Decimal("1.11502"), 1))
    assert len(engine.closed_trades) == 1
    assert engine.closed_trades[0].profit > Decimal(0)


def test_stop_loss_wins_same_tick_conflict_with_take_profit(tmp_path: Path) -> None:
    """Resolve a same-tick stop/target conflict in favour of the stop.

    A long position crosses both levels on one tick only when the target sits
    at or below the stop. The bid at 1.10450 satisfies `bid <= stop_loss` and
    `bid >= take_profit` simultaneously, which is exactly the ambiguity
    `SAME_TICK_PRIORITY` exists to resolve.
    """
    engine = _engine(tmp_path, "same-tick")
    engine.submit_order(_protected_intent(Decimal("1.10500"), Decimal("1.10400")))
    engine.execute_tick(_tick())
    engine.execute_tick(_later_tick(Decimal("1.10450"), Decimal("1.10452"), 1))
    assert len(engine.closed_trades) == 1
    assert engine.closed_trades[0].exit_price == Decimal("1.10450")


def test_closed_trade_carries_observed_excursions(tmp_path: Path) -> None:
    """Prove MAE and MFE are observed during execution, not reconstructed."""
    engine = _engine(tmp_path, "excursions")
    engine.submit_order(_protected_intent(Decimal("1.09000"), None))
    engine.execute_tick(_tick())
    engine.execute_tick(_later_tick(Decimal("1.10500"), Decimal("1.10502"), 1))
    engine.execute_tick(_later_tick(Decimal("1.08900"), Decimal("1.08902"), 2))
    record = engine.closed_trades[0]
    assert record.mfe is not None
    assert record.mfe > Decimal(0)
    assert record.mae is not None
    assert record.mae < Decimal(0)
    assert record.magic == "strategy"
    assert record.ticket == "sim-position-order-engine"


def test_tick_outside_session_is_skipped_not_fatal(tmp_path: Path) -> None:
    """Skip a closed-market tick deterministically instead of aborting."""
    store = SqliteSimulationStateStore(tmp_path / "closed.db", tmp_path / "closed")
    writer = JournalWriter(store, "run-closed", "req-test", "cor-test")
    writer.append(
        "run_started",
        {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
        datetime(2025, 1, 1, tzinfo=UTC),
    )
    ledger = AccountLedger(
        Decimal(10_000),
        "USD",
        SymbolSpecification(
            minimum_volume=Decimal("0.01"),
            maximum_volume=Decimal(100),
            volume_step=Decimal("0.01"),
            contract_size=Decimal(100_000),
            leverage=Decimal(100),
        ),
        ExecutionCostModel(
            commission_per_lot_per_side=Decimal(0),
            long_swap_per_lot_rollover=Decimal(0),
            short_swap_per_lot_rollover=Decimal(0),
        ),
    )
    profile = ExecutionProfile(
        slippage_mode="none",
        fixed_slippage_points=Decimal(0),
        point_value=Decimal("0.00001"),
        price_quantum=Decimal("0.00001"),
        maximum_slippage_points=Decimal(0),
        maximum_gap_points=Decimal(10),
        liquidity_mode="unbounded",
        participation_rate=Decimal(0),
        sessions=(SessionInterval(start_week_second=0, end_week_second=60),),
    )
    engine = EventDrivenExecutionEngine(ledger, writer, profile, "v1")
    engine.submit_order(_intent())
    assert engine.execute_tick(_tick()) == ()
    assert not engine.snapshot()["positions"]


def test_pre_tick_submission_invents_no_price(tmp_path: Path) -> None:
    """Accept an order before the first tick without fabricating a price."""
    engine = _engine(tmp_path, "pre-tick")
    receipt = engine.submit_order(_intent())
    assert receipt.average_price is None
    assert receipt.status == "accepted"
    assert receipt.authority_timestamp == datetime(2025, 1, 1, tzinfo=UTC)
