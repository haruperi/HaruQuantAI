"""Executable Full-Domain Optimization Pipeline usage program.

Connects all 9 registered package features (`FEAT-OPT-01` through `FEAT-OPT-09`)
into a single homogeneous, end-to-end operational pipeline.
Imports strictly from the public API boundary `app.services.optimization`.
"""

from __future__ import annotations

import asyncio
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.analytics import get_analytics_value_field
from app.services.optimization import (
    apply_execution_cost_stress,
    assess_overfit_evidence,
    assess_strategy_robustness,
    build_optimization_artifact_path,
    build_optimization_evidence,
    build_optimization_handoff,
    build_report_package,
    build_time_series_splits,
    calculate_candidate_score,
    calculate_confidence_intervals,
    calculate_deflated_sharpe,
    calculate_parameter_stability,
    calculate_probability_of_ruin,
    calculate_robustness_score,
    candidate_hash,
    compare_optimization_runs,
    count_nominal_trials,
    create_optimization_value,
    detect_overfit_parameters,
    dump_optimization_value,
    estimate_drawdown_mode_sensitivity,
    estimate_first_passage,
    estimate_joint_first_passage,
    evaluate_constraints,
    execute_candidate,
    get_executable_parameters,
    get_optimization_migrations,
    get_optimization_value_field,
    iter_grid_candidates,
    load_search_checkpoint,
    parameter_space_hash,
    persist_optimization_result,
    rank_candidates,
    rank_parameter_sets,
    run_bounded_search,
    run_monte_carlo,
    run_parameter_sweep,
    run_parametric_simulation,
    run_robustness_analysis,
    run_walk_forward_matrix,
    run_walk_forward_optimization,
    run_walk_forward_validation,
    sample_random_candidates,
    save_search_checkpoint,
    select_pareto_candidates,
    select_top_candidates,
    validate_parameter_space,
)
from app.services.risk import create_firm_mandate
from tests.optimization.usage._support import (
    SqliteOptimizationStore,
    candidate_score,
    checkpoint,
    conditional_parameter_space,
    evidence_request,
    genuine_execution_bundle,
    monte_carlo_request,
    parameter_space,
    performance_report,
    search_request,
    walk_forward_request,
)

RETURNS = (Decimal("0.02"), Decimal("-0.01"), Decimal("0.015"), Decimal("-0.005"))


def _mandate(account_id: str = "account-1") -> object:
    """Build a bounded verified mandate through Risk's public API."""
    return create_firm_mandate(
        account_id=account_id,
        mandate_version="2026.07.28-01",
        firm="Example Firm",
        model="fx_cfd",
        phase="evaluation_p1",
        initial_balance=Decimal(1000),
        currency="USD",
        terms_url="https://example.invalid/terms",
        terms_accessed="2026-07-28",
        terms_source_hash="a" * 64,
        verified=True,
        profit_target={"type": "percent_of_initial", "value": Decimal("0.1")},
        daily_loss={
            "basis": "initial_balance",
            "value": Decimal("0.05"),
            "includes_unrealised": True,
            "reset_time": "00:00",
            "reset_tz": "UTC",
        },
        max_drawdown={
            "mode": "static",
            "basis": "initial_balance",
            "value": Decimal("0.1"),
            "trails_on_unrealised": False,
            "trail_stops_at_initial": False,
        },
    )


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


def main() -> None:  # noqa: PLR0915
    """Run full Optimization domain feature pipeline sequentially."""
    print("\n" + "=" * 88)
    print("HARUQUANT AI — OPTIMIZATION DOMAIN FULL-FEATURE PIPELINE EXECUTION")
    print("=" * 88)

    # -------------------------------------------------------------------------
    # Stage 1: Parameter Space and Provenance (FEAT-OPT-01)
    # -------------------------------------------------------------------------
    _stage_banner(1, "Parameter Space and Provenance", "FEAT-OPT-01")
    space = conditional_parameter_space()
    print(_format_result(space))

    validate_parameter_space(space, max_expansion=10, max_constraints=3)

    cand_valid = evaluate_constraints({"enabled": True, "period": 3}, space.constraints)
    print(f"Data -> constraint_valid={cand_valid}")

    exec_params = get_executable_parameters({"enabled": False, "period": 3}, space)
    print(_format_result(exec_params))

    sp_hash = parameter_space_hash(space)
    c_hash = candidate_hash(
        strategy_hash="a" * 64,
        data_hash="b" * 64,
        cost_model_hash="c" * 64,
        realism_hash="d" * 64,
        objective_hash="e" * 64,
        engine_type="event_driven",
        engine_version="v1",
        module_version="v1",
        space_hash=sp_hash,
        executable_parameters={"enabled": True, "period": 3},
    )
    print(f"Data -> space_hash='{sp_hash}', candidate_hash='{c_hash}'")

    # -------------------------------------------------------------------------
    # Stage 2: Objectives, Ranking, and Overfit Evidence (FEAT-OPT-02)
    # -------------------------------------------------------------------------
    _stage_banner(2, "Objectives, Ranking, and Overfit Evidence", "FEAT-OPT-02")
    report = performance_report()
    score_1 = calculate_candidate_score(
        report,
        candidate_hash="a" * 64,
        objective="net_pnl",
        enabled_objectives=frozenset({"net_pnl"}),
    )
    score_2 = calculate_candidate_score(
        report,
        candidate_hash="b" * 64,
        objective="net_pnl",
        enabled_objectives=frozenset({"net_pnl"}),
    )
    print(_format_result(score_1))

    dsr = calculate_deflated_sharpe(
        sharpe=1.0,
        variance=0.2,
        skewness=0.0,
        kurtosis=3.0,
        sample_count=100,
        nominal_trials=10,
    )
    print(f"Data -> deflated_sharpe={dsr}")

    trials = count_nominal_trials(("a" * 64, "b" * 64))
    print(f"Data -> nominal_trials={trials}")
    ranked = rank_candidates((score_1, score_2))
    print(_format_result(ranked))

    pareto = select_pareto_candidates(
        ({"net_pnl": 1.0}, {"net_pnl": 2.0}), ("net_pnl",)
    )
    print(f"Data -> pareto_indices={pareto}")

    overfit = assess_overfit_evidence(
        in_sample=score_1,
        out_of_sample=score_2,
        nominal_trials=2,
        deflated_sharpe=0.7,
        minimum_trade_count=30,
    )
    print(_format_result(overfit))

    # -------------------------------------------------------------------------
    # Stage 3: Bounded Candidate Search (FEAT-OPT-03)
    # -------------------------------------------------------------------------
    _stage_banner(3, "Bounded Candidate Search", "FEAT-OPT-03")
    dataset, _, adapter = genuine_execution_bundle()
    s_req = search_request(dataset)
    print(_format_result(s_req))

    grid_cands = list(
        iter_grid_candidates(
            parameter_space(), max_candidates=10, max_expansion=10, max_constraints=5
        )
    )
    random_cands = sample_random_candidates(
        parameter_space(),
        candidate_count=2,
        seed=3,
        max_expansion=10,
        max_constraints=5,
    )
    print(
        f"Data -> grid_candidates={len(grid_cands)}, random_candidates={len(random_cands)}"
    )

    summary = asyncio.run(run_bounded_search(s_req, adapter))
    print(_format_result(summary))

    top_cands = select_top_candidates(summary, 1)
    print(f"Data -> top_candidates_count={len(top_cands)}")

    # -------------------------------------------------------------------------
    # Stage 4: Simulation Execution Boundary (FEAT-OPT-04)
    # -------------------------------------------------------------------------
    _stage_banner(4, "Simulation Execution Boundary", "FEAT-OPT-04")
    _, c_req, c_adapter = genuine_execution_bundle()
    try:
        cand_res = asyncio.run(
            execute_candidate(c_req, c_adapter, deterministic_only=True)
        )
    except Exception as error:
        if not hasattr(error, "code") or not hasattr(error, "detail"):
            raise
        cand_res = error
    print(_format_result(cand_res))
    if hasattr(cand_res, "safe_details"):
        print(
            "Data -> controlled_outcome='canonical neutral run produced no "
            f"invented fill', reason='{cand_res.detail}'"
        )
    else:
        c_report = get_optimization_value_field(cand_res, "analytics_report")
        c_sections = get_analytics_value_field(c_report, "sections")
        print(
            f"Data -> candidate_hash='{cand_res.candidate_hash}', "
            f"sections_count={len(c_sections)}"
        )

    # -------------------------------------------------------------------------
    # Stage 5: Time-Series Validation (FEAT-OPT-08)
    # -------------------------------------------------------------------------
    _stage_banner(5, "Time-Series Validation", "FEAT-OPT-08")
    wf_req = walk_forward_request(dataset)
    splits = build_time_series_splits(wf_req)
    print(_format_result(splits))

    try:
        wf_res = asyncio.run(run_walk_forward_validation(wf_req, adapter))
    except Exception as error:
        if not hasattr(error, "code") or not hasattr(error, "detail"):
            raise
        wf_res = error
    print(_format_result(wf_res))
    if hasattr(wf_res, "safe_details"):
        print(
            "Data -> controlled_outcome='no eligible training candidate from "
            f"canonical neutral runs', reason='{wf_res.detail}'"
        )
    else:
        print(f"Data -> wf_status='{wf_res.status}', fold_count={len(wf_res.folds)}")

    # -------------------------------------------------------------------------
    # Stage 6: Monte Carlo and Stress Analysis (FEAT-OPT-05)
    # -------------------------------------------------------------------------
    _stage_banner(6, "Monte Carlo and Stress Analysis", "FEAT-OPT-05")
    mc_req = monte_carlo_request()
    mc_res = run_monte_carlo(mc_req, max_simulations=5)
    print(_format_result(mc_res))

    p_ruin = calculate_probability_of_ruin(
        (Decimal(1), Decimal(2)), ruin_threshold=Decimal(1)
    )
    lower, upper = calculate_confidence_intervals(
        (Decimal(1), Decimal(2)), confidence_level=0.5
    )
    print(f"Data -> p_ruin={p_ruin}, ci=[{lower}, {upper}]")

    param_res = run_parametric_simulation(
        win_rate=Decimal("0.5"),
        reward_risk=Decimal(1),
        risk_per_trade=Decimal("0.01"),
        trade_count=2,
        simulations=2,
        initial_balance=Decimal(100),
        seed=3,
        max_simulations=2,
    )
    print(_format_result(param_res))

    stress_req = create_optimization_value(
        "ExecutionStressRequest", kind="spread", value=Decimal("0.5")
    )
    stressed = apply_execution_cost_stress(({"pnl": Decimal(2)},), stress_req)
    print(_format_result(stressed))

    rob_assess = assess_strategy_robustness(
        monte_carlo=None, stress_checks=({"name": "spread", "passed": True},)
    )
    print(_format_result(rob_assess))

    returns_2 = (
        Decimal("0.011"),
        Decimal("-0.004"),
        Decimal("0.018"),
        Decimal("-0.009"),
    )
    fp = estimate_first_passage(RETURNS, _mandate(), paths=100, seed=7)
    joint_fp = estimate_joint_first_passage(
        {"account-1": RETURNS, "account-2": returns_2},
        {"account-1": _mandate(), "account-2": _mandate("account-2")},
        paths=100,
        seed=7,
    )
    sensitivity = estimate_drawdown_mode_sensitivity(
        RETURNS, _mandate(), paths=100, seed=7
    )
    print(
        f"Data -> target_prob={fp.probability_target}, none_survive={joint_fp.probability_none_survive}, modes={tuple(sensitivity)}"
    )

    # -------------------------------------------------------------------------
    # Stage 7: Optimization-Owned Durable State (FEAT-OPT-06)
    # -------------------------------------------------------------------------
    _stage_banner(7, "Optimization-Owned Durable State", "FEAT-OPT-06")
    store = SqliteOptimizationStore()
    ckpt = checkpoint()
    save_search_checkpoint(ckpt, store)
    loaded_ckpt = load_search_checkpoint(
        search_id=ckpt.search_id,
        reproducibility_hash=ckpt.reproducibility_hash,
        store=store,
    )
    print(_format_result(loaded_ckpt))

    ev_req = evidence_request()
    opt_evidence = build_optimization_evidence(ev_req)
    persist_res = persist_optimization_result(opt_evidence, store)
    print(_format_result(persist_res))

    art_path = build_optimization_artifact_path(
        artifact_root=Path("tmp/artifacts"),
        kind="checkpoints",
        search_id="search-one",
        reproducibility_hash="a" * 64,
    )
    print(f"Data -> artifact_suffix='{art_path.suffix}'")

    migrations = get_optimization_migrations()
    print(f"Data -> migration_count={len(migrations)}")

    # -------------------------------------------------------------------------
    # Stage 8: Versioned Results and Handoffs (FEAT-OPT-07)
    # -------------------------------------------------------------------------
    _stage_banner(8, "Versioned Results and Handoffs", "FEAT-OPT-07")
    opt_result = build_optimization_evidence(evidence_request())
    print(_format_result(opt_result))

    report_pkg = build_report_package(opt_result)
    print(_format_result(report_pkg))

    # -------------------------------------------------------------------------
    # Stage 9: Typed Optimization Boundary (FEAT-OPT-09)
    # -------------------------------------------------------------------------
    _stage_banner(9, "Typed Optimization Boundary", "FEAT-OPT-09")
    sweep_res = asyncio.run(run_parameter_sweep(search_request(dataset), adapter))
    print(_format_result(sweep_res))

    wf_opt_res = asyncio.run(run_walk_forward_optimization(wf_req, adapter))
    print(_format_result(wf_opt_res))

    wf_mat_res = asyncio.run(
        run_walk_forward_matrix((wf_req,), adapter, max_requests=1)
    )
    print(_format_result(wf_mat_res))

    rob_ana_res = run_robustness_analysis(
        monte_carlo_request(
            outcomes=(Decimal("1.5"), Decimal("-0.5"), Decimal(2)),
            simulations=5,
            seed=22,
        )
    )
    print(_format_result(rob_ana_res))

    ev_1 = build_optimization_evidence(evidence_request())
    ev_2_values = dump_optimization_value(ev_1)
    ev_2_values["search_id"] = "search-two"
    ev_2 = create_optimization_value("OptimizationResult", **ev_2_values)
    comp_res = compare_optimization_runs((ev_1, ev_2))
    print(_format_result(comp_res))

    stab_res = calculate_parameter_stability(
        (
            {"executable_parameters": {"period": 10}},
            {"executable_parameters": {"period": 12}},
        )
    )
    print(_format_result(stab_res))

    overfit_res = detect_overfit_parameters(
        {"period": 1.0}, {"period": 0.0}, threshold=0.5
    )
    print(_format_result(overfit_res))

    ranked_res = rank_parameter_sets((candidate_score("a" * 64, 1.0),))
    print(_format_result(ranked_res))

    score_res = calculate_robustness_score((True,))
    print(_format_result(score_res))

    handoff_res = build_optimization_handoff(evidence_request())
    print(_format_result(handoff_res))

    print("\n" + "=" * 88)
    print(
        "ALL 9 STAGES COMPLETED SUCCESSFULLY WITH GENUINE OPTIMIZATION DOMAIN EVIDENCE"
    )
    print("=" * 88 + "\n")


if __name__ == "__main__":
    main()
