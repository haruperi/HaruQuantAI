"""Executable Simulation execution usage example.

Demonstrates pricing orders, matching orders, SimTrader operations, and protective exit evaluations.
"""

import asyncio
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.simulator.accounting import (
    AccountLedger,
    ExecutionCostModel,
    SymbolSpecification,
)
from app.services.simulator.execution import (
    EventDrivenExecutionEngine,
    ExecutionProfile,
    SessionInterval,
    SimTrader,
    evaluate_protective_exit,
    match_order,
    price_order,
)
from app.services.simulator.journal import JournalWriter
from app.services.simulator.timeline import Tick
from app.services.trading import OrderIntent, TradingRoute
from tests.simulator._fixtures.sqlite_store import SqliteSimulationStateStore

NOW = datetime(2025, 1, 1, tzinfo=UTC)


def _intent() -> OrderIntent:
    """Build one approved sim market intent."""
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
    print("=" * 80)
    print("Simulator Example 5: Execution Engine and Order Pricing")
    print("=" * 80)

    # 1. Price order
    priced = price_order(_intent(), _tick(), _profile())
    print(f"Priced BUY order: {priced}")

    # 2. Match order
    matched = match_order(_intent(), _tick(), _profile())
    print(f"Matched order status: {matched.status}")

    # 3. SimTrader Operations with temporary directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        engine = _engine(tmp_path, "usage-close")
        trader = SimTrader(engine)
        asyncio.run(trader.submit_order(_intent()))
        engine.execute_tick(_tick())
        close_res = trader.close_position("sim-position-order-engine", Decimal(1))
        print(f"Closed position quantity: {close_res['quantity']}")

        snapshot = trader.snapshot()
        print(f"SimTrader snapshot engine version: {snapshot['engine_version']}")

    # 4. Protective exit
    position = {
        "side": "BUY",
        "stop_loss": Decimal("1.20000"),
        "take_profit": Decimal("1.05000"),
    }
    exit_type = evaluate_protective_exit(position, _tick())
    print(f"Evaluated protective exit type: {exit_type}")


def main() -> None:
    """Run Simulator execution usage example."""
    example_execution()


if __name__ == "__main__":
    main()
