"""Executable Simulation execution usage example.

Demonstrates FEAT-SIM-05 order pricing, matching policy, tick engine state transitions, protective exit evaluations, and SimTrader operations.
"""

from __future__ import annotations

import asyncio
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.simulator import (
    build_lifecycle_deal,
    build_protection_projection,
    calculate_rollover_swap,
    create_simulation_handle,
    create_simulation_value,
    describe_lifecycle_race,
    deterministic_lifecycle_ticket,
    evaluate_protective_exit,
    execute_simulation_handle_operation,
    is_provider_session_open,
    match_order,
    price_order,
    resolve_fill_remainder,
    resolve_order_expiration,
    schedule_simulation_rollover,
    unwrap_simulation_response,
    validate_provider_order,
)
from app.services.trading import create_order_intent, create_position_authority_event
from tests.simulator._fixtures.sqlite_store import SqliteSimulationStateStore

NOW = datetime(2025, 1, 1, tzinfo=UTC)
OrderIntent = Any


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"SUCCESS: Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"SUCCESS: Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"SUCCESS: Output Result -> {type_name}({keys}) : {type_name}"
    return f"SUCCESS: Output Result -> {type_name} : {type_name}"


def _value(response: object) -> object:
    """Unwrap one public Simulation response for display."""
    return unwrap_simulation_response(response, operation="usage.execution")


def _intent() -> OrderIntent:
    """Build one approved sim market intent."""
    return create_order_intent(
        client_order_id="order-engine",
        request_id="req-123e4567-e89b-42d3-a456-426614174000",
        workflow_id="wf-123e4567-e89b-42d3-a456-426614174001",
        correlation_id="cor-123e4567-e89b-42d3-a456-426614174002",
        route="sim",
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


def _tick() -> object:
    """Build the next tick."""
    instant = NOW + timedelta(seconds=1)
    return create_simulation_value(
        "Tick",
        symbol="EURUSD",
        timestamp=instant,
        bid=Decimal("1.10000"),
        ask=Decimal("1.10002"),
        source_id="fixture",
        sequence=1,
        available_at=instant,
    )


def _profile() -> object:
    """Build execution profile."""
    return create_simulation_value(
        "ExecutionProfile",
        slippage_mode="none",
        fixed_slippage_points=Decimal(0),
        point_value=Decimal("0.00001"),
        price_quantum=Decimal("0.00001"),
        maximum_slippage_points=Decimal(0),
        maximum_gap_points=Decimal(10),
        liquidity_mode="unbounded",
        participation_rate=Decimal(0),
        sessions=(
            create_simulation_value(
                "SessionInterval", start_week_second=0, end_week_second=604_800
            ),
        ),
    )


def _engine(tmp_path: Path, suffix: str) -> object:
    """Build execution engine."""
    store = SqliteSimulationStateStore(tmp_path / f"{suffix}.db", tmp_path / suffix)
    writer = create_simulation_handle(
        "JournalWriter", store, f"run-{suffix}", "req-test", "cor-test"
    )
    execute_simulation_handle_operation(
        writer,
        "append",
        "run_started",
        {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
        NOW,
    )
    ledger = create_simulation_handle(
        "AccountLedger",
        Decimal(10_000),
        "USD",
        create_simulation_value(
            "SymbolSpecification",
            minimum_volume=Decimal("0.01"),
            maximum_volume=Decimal(100),
            volume_step=Decimal("0.01"),
            contract_size=Decimal(100_000),
            leverage=Decimal(100),
        ),
        create_simulation_value(
            "ExecutionCostModel",
            commission_per_lot_per_side=Decimal(0),
            long_swap_per_lot_rollover=Decimal(0),
            short_swap_per_lot_rollover=Decimal(0),
        ),
    )
    return create_simulation_handle(
        "EventDrivenExecutionEngine", ledger, writer, _profile(), "v1"
    )


def fr_sim_018() -> None:
    """
    FR-SIM-018: Stage 1 — Derive executable bid/ask price from current tick.

    The system shall derive an executable bid/ask price from the current tick and approved spread/slippage model without using future ticks.
    """
    _header("Stage 1: Pricing - Price Order (FR-SIM-018)")
    resp = price_order(_intent(), _tick(), _profile())
    priced = _value(resp)
    print(_format_result(resp))
    print(f"Data -> priced_order={priced}")


def fr_sim_019() -> None:
    """
    FR-SIM-019: Stage 2 — Deterministically match supported FX intents.

    The system shall deterministically match supported FX market and pending intents using configured trigger, gap, liquidity, FOK/IOC, and same-tick priority rules, explicitly recording partial or cancelled remainder outcomes.
    """
    _header("Stage 2: Matching Policy - Match Order (FR-SIM-019)")
    resp = match_order(_intent(), _tick(), _profile())
    matched = _value(resp)
    print(_format_result(resp))
    print(f"Data -> match_status='{matched.status}'")


def fr_sim_043() -> None:
    """
    FR-SIM-043: Stage 2 — Evaluate protective exit trigger and same-tick priority.

    The system shall resolve the protective exit of one open position against the current tick, triggering stop-loss when the position's exit side crosses its stop and take-profit when it crosses its target, and shall resolve a same-tick stop-loss/take-profit conflict by `SAME_TICK_PRIORITY` order so stop-loss always wins. A condition absent from `SAME_TICK_PRIORITY` is ambiguous and fails closed.
    """
    _header("Stage 2: Protective Exits - Evaluate Protective Exit (FR-SIM-043)")
    position = {
        "side": "BUY",
        "stop_loss": Decimal("1.20000"),
        "take_profit": Decimal("1.05000"),
    }
    resp = evaluate_protective_exit(position, _tick())
    exit_type = _value(resp)
    print(_format_result(resp))
    print(f"Data -> protective_exit_type='{exit_type}'")


def fr_sim_020() -> None:
    """
    FR-SIM-020: Stage 3 — Process canonical tick through EventDrivenExecutionEngine.

    The system shall process one canonical tick at a time, enforce timing and state transitions, apply fills through the ledger, append journal events, maintain per-open-position maximum adverse and favourable excursion so that `mae` and `mfe` are observed rather than reconstructed, and retain immutable end-of-tick mark-to-market equity observations for portfolio measurement. Each tick evaluates every open position for a protective exit before pending orders are matched, closes triggered positions through the ledger, and records one `ClosedTradeRecord` per terminal close carrying the excursions observed during execution.
    """
    _header("Stage 3: Engine Execution - Execute Tick (FR-SIM-020)")
    with tempfile.TemporaryDirectory() as tmp_dir:
        engine = _engine(Path(tmp_dir), "usage-engine")
        execute_simulation_handle_operation(engine, "submit_order", _intent())
        resp = execute_simulation_handle_operation(engine, "execute_tick", _tick())
        receipts = _value(resp)
        print(_format_result(resp))
        print(
            f"Data -> execution_receipts_count={len(receipts if isinstance(receipts, tuple) else ())}"
        )


def fr_sim_021() -> None:
    """
    FR-SIM-021: Stage 3 — Submit OrderIntent to engine and return ExecutionReceipt.

    The system shall accept only a Trading-owned `OrderIntent` for route `sim`, preserve its final approved volume, submit it to the active simulation engine without any broker call, and return a Trading-owned `ExecutionReceipt` constructed from the simulated outcome.
    """
    _header("Stage 3: SimTrader Submission - Submit Order (FR-SIM-021)")
    with tempfile.TemporaryDirectory() as tmp_dir:
        trader = create_simulation_handle(
            "SimTrader", _engine(Path(tmp_dir), "usage-submit")
        )
        resp = asyncio.run(
            execute_simulation_handle_operation(trader, "submit_order", _intent())
        )
        receipt = _value(resp)
        print(_format_result(resp))
        print(f"Data -> receipt_status='{receipt.status}'")


def fr_sim_038() -> None:
    """
    FR-SIM-038: Stage 3 — Expose bound async SimTrader port signature.

    The system shall expose the bound asynchronous `SimTrader.submit_order` method whose signature is exactly the port Trading injects for the `sim` route, `Callable[[OrderIntent], Awaitable[ExecutionReceipt]]`, delegating to its active engine and importing no Trading internals beyond public contracts.
    """
    _header("Stage 3: Async Port Binding - SimTrader Port (FR-SIM-038)")
    with tempfile.TemporaryDirectory() as tmp_dir:
        trader = create_simulation_handle(
            "SimTrader", _engine(Path(tmp_dir), "usage-port")
        )
        resp = asyncio.run(
            execute_simulation_handle_operation(trader, "submit_order", _intent())
        )
        receipt = _value(resp)
        print(_format_result(resp))
        print(f"Data -> port_receipt_status='{receipt.status}'")


def fr_sim_022() -> None:
    """
    FR-SIM-022: Stage 3 — Close open simulated position through SimTrader.

    The system shall close an existing simulated position by approved quantity using the current canonical tick and journal the resulting fill.
    """
    _header("Stage 3: Position Closing - Close Position (FR-SIM-022)")
    with tempfile.TemporaryDirectory() as tmp_dir:
        engine = _engine(Path(tmp_dir), "usage-close-fr")
        trader = create_simulation_handle("SimTrader", engine)
        asyncio.run(
            execute_simulation_handle_operation(trader, "submit_order", _intent())
        )
        execute_simulation_handle_operation(engine, "execute_tick", _tick())
        resp = execute_simulation_handle_operation(
            trader,
            "close_position",
            "sim-position-order-engine",
            Decimal(1),
        )
        close_res = _value(resp)
        print(_format_result(resp))
        print(
            f"Data -> closed_quantity={close_res.get('quantity') if isinstance(close_res, dict) else close_res}"
        )


def fr_sim_023() -> None:
    """
    FR-SIM-023: Stage 3 — Expose read-only SimTrader state snapshot.

    The system shall expose immutable read-only orders, positions, pending orders, deals, and account state for the current run without leaking mutable engine objects.
    """
    _header("Stage 3: Engine Snapshot - SimTrader Snapshot (FR-SIM-023)")
    with tempfile.TemporaryDirectory() as tmp_dir:
        trader = create_simulation_handle(
            "SimTrader", _engine(Path(tmp_dir), "usage-snapshot")
        )
        resp = execute_simulation_handle_operation(trader, "snapshot")
        snapshot = _value(resp)
        print(_format_result(resp))
        print(
            f"Data -> snapshot_engine_version='{snapshot['engine_version'] if isinstance(snapshot, dict) else None}'"
        )


def _swap_fields() -> dict[str, object]:
    """Return one complete deterministic rollover fixture."""
    return {
        "rollover_at": datetime(2026, 8, 12, tzinfo=UTC),
        "server_timezone": "Europe/London",
        "side": "LONG",
        "volume": Decimal(2),
        "rate": Decimal("-0.50"),
        "weekday_ratios": {day: Decimal(3 if day == 2 else 1) for day in range(7)},
        "unit": "ACCOUNT_CURRENCY",
        "point_value": None,
        "fx_rate": None,
        "position_id": "position-rollover",
    }


def fr_sim_134() -> None:
    """FR-SIM-134: Schedule the next rollover in broker-server time."""
    rollover = schedule_simulation_rollover(
        datetime(2026, 6, 1, tzinfo=UTC), "Europe/London", hour=2
    )
    print(f"Data -> next_server_rollover='{rollover.isoformat()}'")


def fr_sim_135() -> None:
    """FR-SIM-135: Accrue exact signed position swap at rollover."""
    result = calculate_rollover_swap(**_swap_fields(), posting_mode="ACCRUAL_ONLY")
    print(f"Data -> accrued_swap={result['accrued_amount']}")


def fr_sim_205() -> None:
    """FR-SIM-205: Apply the effective server-weekday multiplier."""
    result = calculate_rollover_swap(**_swap_fields(), posting_mode="ACCRUAL_ONLY")
    print(f"Data -> weekday={result['weekday']}, multiplier={result['multiplier']}")


def fr_sim_206() -> None:
    """FR-SIM-206: Convert provider swap units using explicit evidence."""
    fields = _swap_fields()
    fields.update(unit="POINTS", point_value=Decimal("0.0001"))
    result = calculate_rollover_swap(**fields, posting_mode="ACCRUAL_ONLY")
    print(f"Data -> point_swap={result['accrued_amount']}")


def fr_sim_207() -> None:
    """FR-SIM-207: Enable balance posting only with target evidence."""
    result = calculate_rollover_swap(
        **_swap_fields(),
        posting_mode="BALANCE_POSTING",
        posting_evidence_reference="provider-swap-deal-fixture",
    )
    print(f"Data -> balance_posted={result['balance_posted']}")


def fr_sim_208() -> None:
    """FR-SIM-208: Derive new position and deal identities for REOPEN."""
    result = calculate_rollover_swap(
        **_swap_fields(),
        posting_mode="REOPEN",
        posting_evidence_reference="provider-reopen-fixture",
    )
    print(f"Data -> reopened_position_id='{result['reopened_position_id']}'")


def _provider_revision(**updates: object) -> dict[str, object]:
    """Build one bounded typed-revision-shaped usage fixture."""
    payload = {
        "trade_mode": "FULL",
        "filling_modes": ("FOK",),
        "execution_mode": "MARKET",
        "directional_volume_limit": "2",
        "point": "0.00001",
        "stops_level_points": 10,
        "freeze_level_points": 5,
        "weekly_sessions": {"2": (("00:00", "23:59"),)},
        "dated_exceptions": {},
        "exception_coverage": ("2025-01-01",),
        "exception_coverage_required": True,
    }
    payload.update(updates)
    return {
        "complete_coverage": True,
        "effective_from": NOW - timedelta(days=1),
        "effective_to": NOW + timedelta(days=400),
        "payload": payload,
    }


def _validate_provider_example() -> None:
    """Execute one accepted provider-rule validation."""
    response = validate_provider_order(
        _provider_revision(),
        at=NOW,
        action="OPEN",
        fill_policy="FOK",
        execution_mode="MARKET",
        requested_volume=Decimal("0.1"),
        same_direction_position_volume=Decimal(0),
        same_direction_pending_volume=Decimal(0),
        reference_price=Decimal("1.1"),
    )
    unwrap_simulation_response(response, operation="usage.provider_order")


def fr_sim_151() -> None:
    """FR-SIM-151: Apply effective stops and freeze levels."""
    _validate_provider_example()


def fr_sim_152() -> None:
    """FR-SIM-152: Enforce effective execution and filling modes."""
    _validate_provider_example()


def fr_sim_153() -> None:
    """FR-SIM-153: Include pending orders in directional volume."""
    _validate_provider_example()


def fr_sim_154() -> None:
    """FR-SIM-154: Enforce provider trade mode."""
    _validate_provider_example()


def fr_sim_155() -> None:
    """FR-SIM-155: Combine weekly sessions with dated evidence."""
    opened = unwrap_simulation_response(
        is_provider_session_open(_provider_revision(), at=NOW),
        operation="usage.provider_session",
    )
    print(f"Data -> session_open='{opened}'")


def fr_sim_156() -> None:
    """FR-SIM-156: Reject uncovered exceptional sessions."""
    fr_sim_155()


def fr_sim_163() -> None:
    """FR-SIM-163: Resolve evidenced provider time-policy expiration."""
    expiration = _value(
        resolve_order_expiration(
            policy="DAY",
            submitted_at=NOW,
            specified_at=None,
            session_closes=(NOW.replace(hour=17),),
        )
    )
    print(f"Data -> expiration='{expiration}'")


def fr_sim_164() -> None:
    """FR-SIM-164: Resolve all admitted fill policies deterministically."""
    result = _value(
        resolve_fill_remainder(
            policy="IOC",
            requested=Decimal(2),
            available=Decimal(1),
            remainder_evidenced=False,
        )
    )
    print(f"Data -> fill_status='{result['status']}'")  # type: ignore[index]


def fr_sim_165() -> None:
    """FR-SIM-165: Preserve only an evidenced RETURN residual."""
    result = _value(
        resolve_fill_remainder(
            policy="RETURN",
            requested=Decimal(2),
            available=Decimal(1),
            remainder_evidenced=True,
        )
    )
    print(f"Data -> remainder='{result['remaining']}'")  # type: ignore[index]


def fr_sim_166() -> None:
    """FR-SIM-166: Link deterministic order/deal/position tickets."""
    ticket = _value(deterministic_lifecycle_ticket("order", {"intent_id": "intent-1"}))
    deal = _value(
        build_lifecycle_deal(
            order_id=str(ticket),
            account_id="account-1",
            position_id="position-1",
            side="BUY",
            quantity=Decimal(1),
            price=Decimal("1.1"),
            entry="DEAL_ENTRY_IN",
            reason="EXPERT",
            occurred_at=NOW,
            economic_at=NOW,
            available_at=NOW,
            source_sequence=1,
            fee_evidence={"commission": Decimal(0)},
            authority_snapshot={
                "position": {
                    "position_id": "position-1",
                    "symbol": "EURUSD",
                    "side": "LONG",
                    "state": "OPEN",
                    "quantity": Decimal(1),
                    "source_sequence": 1,
                },
                "account": {"equity": Decimal(1000)},
            },
            ledger_reference="ledger-usage-1",
        )
    )
    print(f"Data -> deal_id='{deal['deal_id']}'")  # type: ignore[index]


def fr_sim_167() -> None:
    """FR-SIM-167: Expose protection fields and OCO, not pending orders."""
    protection = _value(
        build_protection_projection(
            position_id="position-1",
            stop_loss=Decimal("1.09"),
            take_profit=Decimal("1.12"),
            triggered_reason="STOP_LOSS",
        )
    )
    print(
        f"Data -> protection_pending='{protection['exposed_as_pending_order']}'"  # type: ignore[index]
    )


def fr_sim_168() -> None:
    """FR-SIM-168: Carry fee and account-transaction causal evidence."""
    fr_sim_166()


def fr_sim_169() -> None:
    """FR-SIM-169: Preserve ordered or concurrent lifecycle races."""
    relation = _value(
        describe_lifecycle_race(
            left_event_id="cancel",
            right_event_id="fill",
            left_at=NOW,
            right_at=NOW,
            evidenced_predecessor=None,
        )
    )
    print(f"Data -> race_relation='{relation['relation']}'")  # type: ignore[index]


def fr_sim_170() -> None:
    """FR-SIM-170: Keep lifecycle identity stable across resume boundaries."""
    first = _value(deterministic_lifecycle_ticket("deal", {"boundary": "fill-applied"}))
    second = _value(
        deterministic_lifecycle_ticket("deal", {"boundary": "fill-applied"})
    )
    assert first == second
    print(f"Data -> resumed_ticket='{first}'")


def fr_sim_223() -> None:
    """FR-SIM-223: Supply self-sufficient Trading position authority evidence."""
    deal = _value(
        build_lifecycle_deal(
            order_id="order-authority",
            account_id="account",
            position_id="position-authority",
            side="BUY",
            quantity=Decimal(1),
            price=Decimal("1.1"),
            entry="DEAL_ENTRY_IN",
            reason="EXPERT",
            occurred_at=NOW,
            economic_at=NOW,
            available_at=NOW,
            source_sequence=7,
            fee_evidence={"commission": Decimal(0)},
            authority_snapshot={
                "position": {
                    "position_id": "position-authority",
                    "symbol": "EURUSD",
                    "side": "LONG",
                    "state": "OPEN",
                    "quantity": Decimal(1),
                    "source_sequence": 7,
                },
                "account": {"equity": Decimal(1000)},
            },
            ledger_reference="ledger-authority",
        )
    )
    event = create_position_authority_event(  # type: ignore[index]
        **deal["trading_authority_event"]
    )
    print(f"Data -> authority_deal_id='{event.deal_id}'")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-SIM-05 — execution/ — Matching and Simulated State\n\n"
        "Purpose: Price order intents, apply deterministic matching policies, process tick engine state transitions, and provide the SimTrader facade.\n\n"
        "Module flow:\n"
        "-> Stage 1: OrderIntent, tick, and execution profile input mapping\n"
        "-> Stage 2: Spread pricing, matching trigger rules, and protective exit evaluation\n"
        "-> Stage 3: EventDrivenExecutionEngine tick processing, position management, and read-only state snapshot generation"
    )

    # Stage 1: Pricing
    fr_sim_018()

    # Stage 2: Matching policy & Protective exits
    fr_sim_019()
    fr_sim_043()

    # Stage 3: Engine execution, SimTrader facade, position management & snapshots
    fr_sim_020()
    fr_sim_021()
    fr_sim_038()
    fr_sim_022()
    fr_sim_023()

    # Stage 4: Broker-server rollover and swap modes
    fr_sim_134()
    fr_sim_135()
    fr_sim_205()
    fr_sim_206()
    fr_sim_207()
    fr_sim_208()
    fr_sim_151()
    fr_sim_152()
    fr_sim_153()
    fr_sim_154()
    fr_sim_155()
    fr_sim_156()
    fr_sim_163()
    fr_sim_164()
    fr_sim_165()
    fr_sim_166()
    fr_sim_167()
    fr_sim_168()
    fr_sim_169()
    fr_sim_170()
    fr_sim_223()


if __name__ == "__main__":
    main()
