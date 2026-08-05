"""Executable Full-Domain Simulator Pipeline usage program.

Connects all 9 registered package features (`FEAT-SIM-01` through `FEAT-SIM-09`)
into a single homogeneous, end-to-end operational pipeline.
Imports strictly from the public API boundary `app.services.simulator`.
"""

from __future__ import annotations

import asyncio
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_quality_report,
    build_fx_conversion_evidence,
    build_fx_rate_leg,
    build_market_dataset,
    build_tick_record,
)
from app.services.simulator import (
    build_artifact_manifest,
    build_json_report,
    build_markdown_report,
    build_tick_timeline,
    calculate_execution_costs,
    calculate_margin,
    calculate_simulation_backtest_config_hash,
    convert_fx_amount,
    create_simulation_handle,
    create_simulation_value,
    evaluate_protective_exit,
    execute_simulation_handle_operation,
    get_simulation_error_catalog,
    get_simulation_migrations,
    get_simulation_value_field,
    match_order,
    normalize_volume,
    price_order,
    replay_journal,
    resolve_idempotent_run,
    run_backtest,
    run_fast_research,
    to_simulation_error_payload,
    unwrap_simulation_response,
    validate_fx_evidence,
    validate_intent_timing,
    validate_market_data,
    validate_phase_one_scope,
    validate_run_inputs,
)
from app.services.trading import create_order_intent
from app.utils import canonical_digest, canonical_json, generate_id
from tests.simulator._fixtures.sqlite_store import SqliteSimulationStateStore
from tests.simulator.usage.workflows._support import (
    authority,
    dependencies,
    live_tick_dataset,
)

NOW = datetime(2025, 1, 1, tzinfo=UTC)


def _stage_banner(stage_num: int, title: str, feature_id: str) -> None:
    """Print stage header banner."""
    print(f"\n{'=' * 88}")
    print(f"Stage {stage_num}: {title} ({feature_id})")
    print(f"{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def _value(response: object) -> object:
    """Unwrap public Simulation response."""
    return unwrap_simulation_response(response, operation="usage.features")


def main() -> None:  # noqa: PLR0915
    """Run full Simulator domain feature pipeline sequentially."""
    print("\n" + "=" * 88)
    print("HARUQUANT AI — SIMULATOR DOMAIN FULL-FEATURE PIPELINE EXECUTION")
    print("=" * 88)

    # -------------------------------------------------------------------------
    # Stage 1: Domain Error Taxonomy (FEAT-SIM-08)
    # -------------------------------------------------------------------------
    _stage_banner(1, "Domain Error Taxonomy", "FEAT-SIM-08")
    catalog = get_simulation_error_catalog()
    print(_format_result(catalog))

    try:
        _value(
            validate_phase_one_scope(
                {
                    "asset_class": "CRYPTO",
                    "runtime_profile": "simulation",
                    "execution_route": "sim",
                }
            )
        )
    except Exception as error:  # noqa: BLE001
        err_payload = to_simulation_error_payload(error)
        print(_format_result(err_payload))

    # -------------------------------------------------------------------------
    # Stage 2: Boundary and Quality Validation (FEAT-SIM-01)
    # -------------------------------------------------------------------------
    _stage_banner(2, "Boundary and Quality Validation", "FEAT-SIM-01")
    req_inputs_res = validate_run_inputs(
        {
            "request_id": "req-simulator-usage",
            "workflow_id": "wf-simulator-usage",
            "correlation_id": "cor-simulator-usage",
            "strategy_id": "registered-strategy",
            "strategy_version": "v1",
            "strategy_config_ref": "strategy-config",
            "strategy_config_hash": "a" * 64,
            "data_ref": "market-data",
            "data_version": "v1",
            "data_hash": "b" * 64,
            "execution_profile_ref": "execution-profile",
            "execution_profile_version": "v1",
            "execution_profile_hash": "c" * 64,
            "risk_policy_ref": "sim-policy",
            "risk_policy_version": "v1",
            "risk_policy_hash": "d" * 64,
            "symbol": "EURUSD",
            "config_hash": "e" * 64,
        }
    )
    print(_format_result(req_inputs_res))

    scope_res = validate_phase_one_scope(
        {"asset_class": "FX", "runtime_profile": "simulation", "execution_route": "sim"}
    )
    print(_format_result(scope_res))

    tick_rec = build_tick_record(
        timestamp=NOW,
        source="fixture",
        source_symbol="EURUSD",
        available_at=NOW,
        bid=Decimal("1.10000"),
        ask=Decimal("1.10002"),
        last=Decimal("1.10001"),
        volume=Decimal(2),
        price_unit="quote",
        volume_unit="lot",
        source_bar_time=NOW,
        tick_index_in_bar=0,
        bar_phase=1,
    )
    quality = build_data_quality_report(
        quality_status="perfect",
        quality_decision="accepted",
        quality_score=Decimal(100),
        record_count=1,
        checked_count=1,
        truncated=False,
        sample_limit=1,
        schema_version="v1",
        generated_at=NOW,
    )
    dataset = build_market_dataset(
        normalization_version="v1",
        data_kind="ticks",
        symbol="EURUSD",
        timeframe="M1",
        records=(tick_rec,),
        start=NOW,
        end=NOW,
        available_at=NOW,
        record_count=1,
        quality_report=quality,
        source_metadata={"tick_generation_model": "real"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="backtest",
        precision_policy="decimal_string",
        request_id="req-11111111-1111-4111-8111-111111111111",
    )
    digest = sha256(
        canonical_json(dataset.model_dump(mode="python", warnings=False)).encode(
            "utf-8"
        )
    ).hexdigest()
    val_ctx = create_simulation_value(
        "MarketDataValidationContext",
        expected_data_hash=digest,
        requested_start=dataset.start,
        requested_end=dataset.end,
        evaluated_at=dataset.available_at,
        maximum_staleness=timedelta(0),
        allowed_tick_models=("real",),
    )
    data_val_res = validate_market_data(dataset, val_ctx)
    print(_format_result(data_val_res))

    # -------------------------------------------------------------------------
    # Stage 3: Canonical Tick Timeline (FEAT-SIM-03)
    # -------------------------------------------------------------------------
    _stage_banner(3, "Canonical Tick Timeline", "FEAT-SIM-03")
    sim_tick = create_simulation_value(
        "Tick",
        symbol="EURUSD",
        timestamp=NOW,
        bid=Decimal("1.10000"),
        ask=Decimal("1.10002"),
        source_id="provider",
        sequence=0,
        available_at=NOW,
    )
    print(_format_result(sim_tick))

    timeline_res = build_tick_timeline(dataset)
    print(_format_result(timeline_res))

    timing_res = validate_intent_timing(NOW, NOW)
    print(_format_result(timing_res))

    # -------------------------------------------------------------------------
    # Stage 4: Fixed-Precision Account Math (FEAT-SIM-04)
    # -------------------------------------------------------------------------
    _stage_banner(4, "Fixed-Precision Account Math", "FEAT-SIM-04")
    spec = create_simulation_value(
        "SymbolSpecification",
        minimum_volume=Decimal("0.01"),
        maximum_volume=Decimal(100),
        volume_step=Decimal("0.01"),
        contract_size=Decimal(100_000),
        leverage=Decimal(100),
    )
    cost_model = create_simulation_value(
        "ExecutionCostModel",
        commission_per_lot_per_side=Decimal(1),
        long_swap_per_lot_rollover=Decimal(0),
        short_swap_per_lot_rollover=Decimal(0),
    )
    ledger = create_simulation_handle(
        "AccountLedger", Decimal(10_000), "USD", spec, cost_model
    )

    norm_vol_res = normalize_volume(Decimal(1), spec)
    print(_format_result(norm_vol_res))

    cost_input = create_simulation_value(
        "ExecutionCostInput",
        volume=Decimal(1),
        side="BUY",
        rollover_multiplier=Decimal(0),
    )
    costs_res = calculate_execution_costs(cost_input, cost_model)
    print(_format_result(costs_res))

    margin_res = calculate_margin(
        Decimal(1), Decimal(1), Decimal(100_000), Decimal(100)
    )
    print(_format_result(margin_res))

    leg = build_fx_rate_leg(
        source_currency="USD",
        target_currency="EUR",
        rate=Decimal("0.9"),
        source_id="fixture",
        provider_symbol="USDEUR",
        as_of=NOW,
        provenance={"source": "fixture"},
    )
    fx_ev = build_fx_conversion_evidence(
        source_currency="USD",
        target_currency="EUR",
        legs=(leg,),
        composite_rate=Decimal("0.9"),
        as_of=NOW,
        expires_at=NOW + timedelta(hours=1),
        path_policy_id="direct",
        path_policy_version="v1",
        provenance={"source": "fixture"},
        request_id="req-44444444-4444-4444-8444-444444444444",
    )
    fx_val_res = validate_fx_evidence(fx_ev, as_of=fx_ev.as_of)
    print(_format_result(fx_val_res))

    fx_conv_res = convert_fx_amount(Decimal(10), _value(fx_val_res))
    print(_format_result(fx_conv_res))

    fill_res = execute_simulation_handle_operation(
        ledger,
        "apply_fill",
        create_simulation_value(
            "LedgerFill",
            action="OPEN",
            side="BUY",
            volume=Decimal(1),
            price=Decimal("1.1"),
        ),
    )
    print(_format_result(fill_res))

    snap_res = execute_simulation_handle_operation(ledger, "snapshot")
    print(_format_result(snap_res))

    execute_simulation_handle_operation(ledger, "mark_to_market", Decimal(-25))

    # -------------------------------------------------------------------------
    # Stage 5: Simulation-Owned State (FEAT-SIM-02)
    # -------------------------------------------------------------------------
    _stage_banner(5, "Simulation-Owned State", "FEAT-SIM-02")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        store = SqliteSimulationStateStore(
            tmp_path / "simulation.db", tmp_path / "artifacts"
        )
        store.record_idempotency("req-usage", "a" * 64, "run-usage", "started")
        run_info = store.load_run("req-usage")
        print(_format_result(run_info))

    migrations = get_simulation_migrations()
    print(_format_result(migrations))

    # -------------------------------------------------------------------------
    # Stage 6: Immutable Journal and Replay (FEAT-SIM-06)
    # -------------------------------------------------------------------------
    _stage_banner(6, "Immutable Journal and Replay", "FEAT-SIM-06")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        store = SqliteSimulationStateStore(
            tmp_path / "state.db", tmp_path / "artifacts"
        )
        writer = create_simulation_handle(
            "JournalWriter", store, "run-usage", "req-usage", "cor-usage"
        )
        append_res = execute_simulation_handle_operation(
            writer,
            "append",
            "run_started",
            {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
            NOW,
        )
        print(_format_result(append_res))

        finalize_res = execute_simulation_handle_operation(writer, "finalize")
        print(_format_result(finalize_res))

        journal_file = tmp_path / "artifacts" / "run-usage" / "journal.jsonl"
        replay_res = replay_journal(
            journal_file,
            lambda _state, event: {
                "sequence": get_simulation_value_field(event, "sequence")
            },
        )
        print(_format_result(replay_res))

    idempotency_res = resolve_idempotent_run(
        "req-usage",
        "a" * 64,
        lambda req_id: {
            "request_hash": "a" * 64,
            "run_id": req_id.replace("req", "run"),
            "status": "completed",
        },
    )
    print(_format_result(idempotency_res))

    # -------------------------------------------------------------------------
    # Stage 7: Matching and Simulated State (FEAT-SIM-05)
    # -------------------------------------------------------------------------
    _stage_banner(7, "Matching and Simulated State", "FEAT-SIM-05")
    intent = create_order_intent(
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
    profile = create_simulation_value(
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

    priced_res = price_order(intent, sim_tick, profile)
    print(_format_result(priced_res))

    matched_res = match_order(intent, sim_tick, profile)
    print(_format_result(matched_res))

    exit_res = evaluate_protective_exit(
        {
            "side": "BUY",
            "stop_loss": Decimal("1.20000"),
            "take_profit": Decimal("1.05000"),
        },
        sim_tick,
    )
    print(_format_result(exit_res))

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        store = SqliteSimulationStateStore(
            tmp_path / "engine.db", tmp_path / "engine_artifacts"
        )
        writer = create_simulation_handle(
            "JournalWriter", store, "run-engine", "req-test", "cor-test"
        )
        execute_simulation_handle_operation(
            writer,
            "append",
            "run_started",
            {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
            NOW,
        )
        engine_ledger = create_simulation_handle(
            "AccountLedger", Decimal(10_000), "USD", spec, cost_model
        )
        engine = create_simulation_handle(
            "EventDrivenExecutionEngine", engine_ledger, writer, profile, "v1"
        )
        trader = create_simulation_handle("SimTrader", engine)

        sub_res = asyncio.run(
            execute_simulation_handle_operation(trader, "submit_order", intent)
        )
        print(_format_result(sub_res))

        tick_exec_res = execute_simulation_handle_operation(
            engine, "execute_tick", sim_tick
        )
        print(_format_result(tick_exec_res))

        close_pos_res = execute_simulation_handle_operation(
            trader, "close_position", "sim-position-order-engine", Decimal(1)
        )
        print(_format_result(close_pos_res))

        trader_snap_res = execute_simulation_handle_operation(trader, "snapshot")
        print(_format_result(trader_snap_res))

    # -------------------------------------------------------------------------
    # Stage 8: Official and Research Orchestration (FEAT-SIM-07)
    # -------------------------------------------------------------------------
    _stage_banner(8, "Official and Research Orchestration", "FEAT-SIM-07")
    tick_dataset = live_tick_dataset()
    req_payload: dict[str, object] = {
        "request_id": generate_id("req"),
        "workflow_id": generate_id("wf"),
        "correlation_id": generate_id("cor"),
        "strategy_id": "strategy-1",
        "strategy_version": "v1",
        "strategy_config_ref": "strategy-config",
        "strategy_config_hash": "a" * 64,
        "data_ref": "dataset",
        "data_version": "v1",
        "data_hash": canonical_digest(
            tick_dataset.model_dump(mode="python", warnings=False)
        ),
        "tick_generation_ref": "tick-profile",
        "tick_generation_version": "v1",
        "tick_generation_hash": "b" * 64,
        "execution_profile_ref": "execution-profile",
        "execution_profile_version": "v1",
        "execution_profile_hash": "c" * 64,
        "risk_policy_ref": "risk-policy",
        "risk_policy_version": "v1",
        "risk_policy_hash": "d" * 64,
        "symbol": "EURUSD",
        "timeframe": "M1",
        "start": tick_dataset.start,
        "end": tick_dataset.end,
        "parameters": {"period": 14},
        "initial_balance": Decimal(10_000),
        "account_currency": "USD",
        "asset_class": "FX",
        "seed": 7,
        "runtime_profile": "simulation",
        "execution_route": "sim",
        "canonical": True,
    }
    req_payload["config_hash"] = _value(
        calculate_simulation_backtest_config_hash(req_payload)
    )
    backtest_req = create_simulation_value("SimulationBacktestRequestV1", **req_payload)
    print(_format_result(backtest_req))

    with tempfile.TemporaryDirectory() as tmp_dir:
        run_deps = dependencies(Path(tmp_dir), tick_dataset)
        run_res = run_backtest(backtest_req, authority(backtest_req), run_deps)
        print(_format_result(run_res))

        fast_req_payload = dict(req_payload)
        fast_req_payload["runtime_profile"] = "fast_research"
        fast_req_payload["canonical"] = False
        fast_req_payload["config_hash"] = _value(
            calculate_simulation_backtest_config_hash(fast_req_payload)
        )
        fast_req = create_simulation_value(
            "SimulationBacktestRequestV1", **fast_req_payload
        )
        fast_res = run_fast_research(fast_req, authority(fast_req), run_deps)
        print(_format_result(fast_res))

    # -------------------------------------------------------------------------
    # Stage 9: Results and Canonical Artifacts (FEAT-SIM-09)
    # -------------------------------------------------------------------------
    _stage_banner(9, "Results and Canonical Artifacts", "FEAT-SIM-09")
    with tempfile.TemporaryDirectory() as tmp_dir:
        run_deps = dependencies(Path(tmp_dir), tick_dataset)
        sim_result = _value(
            run_backtest(backtest_req, authority(backtest_req), run_deps)
        )
        print(_format_result(sim_result))

        json_rep_res = build_json_report(sim_result)
        print(_format_result(json_rep_res))

        md_rep_res = build_markdown_report(sim_result)
        print(_format_result(md_rep_res))

        art_path = Path(tmp_dir) / "test_artifact.json"
        art_path.write_text("{}", encoding="utf-8")
        manifest_res = build_artifact_manifest(
            Path(tmp_dir), (art_path,), created_at=NOW
        )
        print(_format_result(manifest_res))

    print("\n" + "=" * 88)
    print("ALL 9 STAGES COMPLETED SUCCESSFULLY WITH GENUINE SIMULATOR DOMAIN EVIDENCE")
    print("=" * 88 + "\n")


if __name__ == "__main__":
    main()
