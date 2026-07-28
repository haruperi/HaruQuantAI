"""Executable Simulation execution usage example.

Demonstrates pricing orders, matching orders, SimTrader operations, and
protective exit evaluations.
"""

import asyncio
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.simulator import (
    AccountLedger,
    EventDrivenExecutionEngine,
    ExecutionCostModel,
    ExecutionProfile,
    JournalWriter,
    SessionInterval,
    SimTrader,
    SymbolSpecification,
    Tick,
    evaluate_protective_exit,
    match_order,
    price_order,
    unwrap_simulation_response,
)
from app.services.trading import OrderIntent, TradingRoute
from tests.simulator._fixtures.sqlite_store import SqliteSimulationStateStore

NOW = datetime(2025, 1, 1, tzinfo=UTC)


def _value(response: object) -> object:
    """Unwrap one public Simulation response for display."""
    return unwrap_simulation_response(response, operation="usage.execution")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _intent() -> OrderIntent:
    """Build one approved sim market intent."""
    return OrderIntent(
        client_order_id="order-engine",
        request_id="req-123e4567-e89b-42d3-a456-426614174000",
        workflow_id="wf-123e4567-e89b-42d3-a456-426614174001",
        correlation_id="cor-123e4567-e89b-42d3-a456-426614174002",
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
        created_at=NOW,
        valid_until=NOW + timedelta(days=1),
    )


def _tick() -> Tick:
    """Build the next tick."""
    instant = NOW + timedelta(seconds=1)
    return Tick(
        symbol="EURUSD",
        timestamp=instant,
        bid=Decimal("1.10000"),
        ask=Decimal("1.10002"),
        source_id="fixture",
        sequence=1,
        available_at=instant,
    )


def _profile() -> ExecutionProfile:
    """Build execution profile."""
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


def _engine(tmp_path: Path, suffix: str) -> EventDrivenExecutionEngine:
    """Build execution engine."""
    store = SqliteSimulationStateStore(tmp_path / f"{suffix}.db", tmp_path / suffix)
    writer = JournalWriter(store, f"run-{suffix}", "req-test", "cor-test")
    writer.append(
        "run_started",
        {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
        NOW,
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
    return EventDrivenExecutionEngine(ledger, writer, _profile(), "v1")


def example_execution() -> None:
    """Demonstrate execution pricing, matching, SimTrader, and protective exits."""
    _header("Demonstrate execution pricing, matching, SimTrader, and protective exits.")
    print("Simulator Example 5: Execution Engine and Order Pricing")

    # 1. Price order
    priced = _value(price_order(_intent(), _tick(), _profile()))
    print(f"Priced BUY order: {priced}")

    # 2. Match order
    matched = _value(match_order(_intent(), _tick(), _profile()))
    print(f"Matched order status: {matched.status}")

    # 3. SimTrader Operations with temporary directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        engine = _engine(tmp_path, "usage-close")
        trader = SimTrader(engine)
        _value(asyncio.run(trader.submit_order(_intent())))
        _value(engine.execute_tick(_tick()))
        close_res = _value(trader.close_position("sim-position-order-engine", Decimal(1)))
        print(f"Closed position quantity: {close_res['quantity']}")

        snapshot = _value(trader.snapshot())
        print(f"SimTrader snapshot engine version: {snapshot['engine_version']}")

    # 4. Protective exit
    position = {
        "side": "BUY",
        "stop_loss": Decimal("1.20000"),
        "take_profit": Decimal("1.05000"),
    }
    exit_type = _value(evaluate_protective_exit(position, _tick()))
    print(f"Evaluated protective exit type: {exit_type}")


def fr_sim_018() -> None:
    """Demonstrate FR-SIM-018.

    Responsibility:
        The system shall derive an executable bid/ask price from the current tick and
        approved spread/slippage model without using future ticks.
    """
    _header(
        "Demonstrate FR-SIM-018. Responsibility: The system shall derive an executable bid/ask price from the current tick and approved spread/slippage model without using future ticks."
    )
    print(f"Priced order: {_value(price_order(_intent(), _tick(), _profile()))}")


def fr_sim_019() -> None:
    """Demonstrate FR-SIM-019.

    Responsibility:
        The system shall deterministically match supported FX market and pending intents
        using configured trigger, gap, liquidity, FOK/IOC, and same-tick priority rules,
        explicitly recording partial or cancelled remainder outcomes.
    """
    _header(
        "Demonstrate FR-SIM-019. Responsibility: The system shall deterministically match supported FX market and pending intents using configured trigger, gap, liquidity, FOK/IOC, and same-tick priority rules, explicitly recording partial or cancelled remainder outcomes."
    )
    print(f"Match status: {_value(match_order(_intent(), _tick(), _profile())).status}")


def fr_sim_043() -> None:
    """Demonstrate FR-SIM-043.

    Responsibility:
        The system shall resolve the protective exit of one open position against the
        current tick, triggering stop-loss when the position's exit side crosses its
        stop and take-profit when it crosses its target, and shall resolve a same-tick
        stop-loss/take-profit conflict by `SAME_TICK_PRIORITY` order so stop-loss always
        wins. A condition absent from `SAME_TICK_PRIORITY` is ambiguous and fails
        closed.
    """
    _header(
        "Demonstrate FR-SIM-043. Responsibility: The system shall resolve the protective exit of one open position against the current tick, triggering stop-loss when the position's exit side crosses its stop and take-profit when it crosses its target, and shall resolve a same-tick stop-loss/take-profit conflict by `SAME_TICK_PRIORITY` order so stop-loss always wins. A condition absent from `SAME_TICK_PRIORITY` is ambiguous and fails closed."
    )
    position = {
        "side": "BUY",
        "stop_loss": Decimal("1.20000"),
        "take_profit": Decimal("1.05000"),
    }
    print(f"Protective exit: {_value(evaluate_protective_exit(position, _tick()))}")


def fr_sim_020() -> None:
    """Demonstrate FR-SIM-020.

    Responsibility:
        The system shall process one canonical tick at a time, enforce timing and state
        transitions, apply fills through the ledger, append journal events, maintain
        per-open-position maximum adverse and favourable excursion so that `mae` and
        `mfe` are observed rather than reconstructed, and retain immutable end-of-tick
        mark-to-market equity observations for portfolio measurement. Each tick
        evaluates every open position for a protective exit before pending orders are
        matched, closes triggered positions through the ledger, and records one
        `ClosedTradeRecord` per terminal close carrying the excursions observed during
        execution.
    """
    _header(
        "Demonstrate FR-SIM-020. Responsibility: The system shall process one canonical tick at a time, enforce timing and state transitions, apply fills through the ledger, append journal events, maintain per-open-position maximum adverse and favourable excursion so that `mae` and `mfe` are observed rather than reconstructed, and retain immutable end-of-tick mark-to-market equity observations for portfolio measurement. Each tick evaluates every open position for a protective exit before pending orders are matched, closes triggered positions through the ledger, and records one `ClosedTradeRecord` per terminal close carrying the excursions observed during execution."
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        engine = _engine(Path(tmp_dir), "usage-engine")
        engine.submit_order(_intent())
        print(f"Execution receipts: {len(_value(engine.execute_tick(_tick())))}")


def fr_sim_021() -> None:
    """Demonstrate FR-SIM-021.

    Responsibility:
        The system shall accept only a Trading-owned `OrderIntent` for route `sim`,
        preserve its final approved volume, submit it to the active simulation engine
        without any broker call, and return a Trading-owned `ExecutionReceipt`
        constructed from the simulated outcome.
    """
    _header(
        "Demonstrate FR-SIM-021. Responsibility: The system shall accept only a Trading-owned `OrderIntent` for route `sim`, preserve its final approved volume, submit it to the active simulation engine without any broker call, and return a Trading-owned `ExecutionReceipt` constructed from the simulated outcome."
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        trader = SimTrader(_engine(Path(tmp_dir), "usage-submit"))
        receipt = _value(asyncio.run(trader.submit_order(_intent())))
        print(f"Submission status: {receipt.status}")


def fr_sim_038() -> None:
    """Demonstrate FR-SIM-038.

    Responsibility:
        The system shall expose the bound asynchronous `SimTrader.submit_order` method
        whose signature is exactly the port Trading injects for the `sim` route,
        `Callable[[OrderIntent], Awaitable[ExecutionReceipt]]`, delegating to its active
        engine and importing no Trading internals beyond public contracts.
    """
    _header(
        "Demonstrate FR-SIM-038. Responsibility: The system shall expose the bound asynchronous `SimTrader.submit_order` method whose signature is exactly the port Trading injects for the `sim` route, `Callable[[OrderIntent], Awaitable[ExecutionReceipt]]`, delegating to its active engine and importing no Trading internals beyond public contracts."
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        trader = SimTrader(_engine(Path(tmp_dir), "usage-port"))
        receipt = _value(asyncio.run(trader.submit_order(_intent())))
        print(f"Async port status: {receipt.status}")


def fr_sim_022() -> None:
    """Demonstrate FR-SIM-022.

    Responsibility:
        The system shall close an existing simulated position by approved quantity using
        the current canonical tick and journal the resulting fill.
    """
    _header(
        "Demonstrate FR-SIM-022. Responsibility: The system shall close an existing simulated position by approved quantity using the current canonical tick and journal the resulting fill."
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        engine = _engine(Path(tmp_dir), "usage-close-fr")
        trader = SimTrader(engine)
        _value(asyncio.run(trader.submit_order(_intent())))
        _value(engine.execute_tick(_tick()))
        print(_value(trader.close_position("sim-position-order-engine", Decimal(1))))


def fr_sim_023() -> None:
    """Demonstrate FR-SIM-023.

    Responsibility:
        The system shall expose immutable read-only orders, positions, pending orders,
        deals, and account state for the current run without leaking mutable engine
        objects.
    """
    _header(
        "Demonstrate FR-SIM-023. Responsibility: The system shall expose immutable read-only orders, positions, pending orders, deals, and account state for the current run without leaking mutable engine objects."
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        trader = SimTrader(_engine(Path(tmp_dir), "usage-snapshot"))
        print(f"Snapshot engine: {_value(trader.snapshot())['engine_version']}")


def main() -> None:
    """Run Simulator execution usage example."""
    fr_sim_018()
    fr_sim_019()
    fr_sim_043()
    fr_sim_020()
    fr_sim_021()
    fr_sim_038()
    fr_sim_022()
    fr_sim_023()


if __name__ == "__main__":
    main()
