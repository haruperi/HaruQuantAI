"""Executable Optimization public API usage example.

Demonstrates FEAT-OPT-09 parameter sweeps, walk-forward optimization, robustness analysis, optimization comparison, parameter stability, overfit detection, and value functions.
"""

from __future__ import annotations

import asyncio
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.optimization import (
    build_optimization_evidence,
    build_optimization_handoff,
    calculate_parameter_stability,
    calculate_robustness_score,
    compare_optimization_runs,
    create_optimization_value,
    detect_overfit_parameters,
    dump_optimization_value,
    rank_parameter_sets,
    run_parameter_sweep,
    run_robustness_analysis,
    run_walk_forward_matrix,
    run_walk_forward_optimization,
)
from tests.optimization.usage._support import (
    candidate_score,
    evidence_request,
    genuine_execution_bundle,
    monte_carlo_request,
    search_request,
    walk_forward_request,
)


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
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def fr_opt_056() -> None:
    """FR-OPT-056: Stage 3 — Parameter Sweep Execution.

    The system shall run one bounded parameter sweep through the injected adapter and assemble advisory baseline evidence.
    """
    _header("Stage 3: Parameter Sweep - Run Parameter Sweep (FR-OPT-056)")
    dataset, _, adapter = genuine_execution_bundle()
    sweep_response = asyncio.run(run_parameter_sweep(search_request(dataset), adapter))
    sweep_res = sweep_response.data
    print(_format_result(sweep_response))
    print(
        f"Data -> ranked_candidates_count={len(sweep_res.ranked_candidates) if sweep_res else 0}"
    )


def fr_opt_057() -> None:
    """FR-OPT-057: Stage 3 — Walk-Forward Optimization & Matrix.

    The system shall run one walk-forward optimization or a caller-bounded compatible matrix through the canonical WFA workflow.
    """
    _header("Stage 3: WFA Execution - Run Walk-Forward Optimization (FR-OPT-057)")
    dataset, _, adapter = genuine_execution_bundle()
    request = walk_forward_request(dataset)
    wf_response = asyncio.run(run_walk_forward_optimization(request, adapter))
    wf_res = wf_response.data
    matrix_response = asyncio.run(
        run_walk_forward_matrix((request,), adapter, max_requests=1)
    )
    matrix_res = matrix_response.data
    print(_format_result(wf_response))
    print(
        f"Data -> wf_diagnostics_present={'walk_forward' in wf_res.diagnostics if wf_res else False}, matrix_count={len(matrix_res) if matrix_res else 0}"
    )


def fr_opt_058() -> None:
    """FR-OPT-058: Stage 3 — Robustness Analysis.

    The system shall run exactly one typed Monte Carlo or explicit same-unit execution-stress analysis.
    """
    _header("Stage 3: Robustness Analysis - Run Robustness Analysis (FR-OPT-058)")
    analysis_request = monte_carlo_request(
        outcomes=(Decimal("1.5"), Decimal("-0.5"), Decimal(2)),
        simulations=5,
        seed=22,
    )
    analysis_response = run_robustness_analysis(analysis_request)
    analysis_res = analysis_response.data
    print(_format_result(analysis_response))
    print(
        f"Data -> mc_simulations={analysis_res.monte_carlo.simulations if analysis_res and analysis_res.monte_carlo else None}"
    )


def fr_opt_059() -> None:
    """FR-OPT-059: Stage 3 — Optimization Run Comparison.

    The system shall compare only non-empty schema-compatible result sequences without recomputing evidence.
    """
    _header("Stage 3: Run Comparison - Compare Optimization Runs (FR-OPT-059)")
    assembly_request = evidence_request()
    first_ev = build_optimization_evidence(assembly_request)
    second_values = dump_optimization_value(first_ev)
    second_values["search_id"] = "search-two"
    second_ev = create_optimization_value("OptimizationResult", **second_values)
    comp_response = compare_optimization_runs((first_ev, second_ev))
    comp_res = comp_response.data
    print(_format_result(comp_response))
    print(
        f"Data -> compared_search_ids_count={len(comp_res.search_ids) if comp_res else 0}"
    )


def fr_opt_060() -> None:
    """FR-OPT-060: Stage 3 — Parameter Stability Calculation.

    The system shall calculate exact-match stability from non-empty ranked executable-parameter evidence.
    """
    _header("Stage 3: Parameter Stability - Calculate Parameter Stability (FR-OPT-060)")
    stability_response = calculate_parameter_stability(
        (
            {"executable_parameters": {"period": 10}},
            {"executable_parameters": {"period": 12}},
        )
    )
    stability = stability_response.data
    print(_format_result(stability_response))
    print(
        f"Data -> stability_percentage={stability.stability_percentage if stability else None}"
    )


def fr_opt_061() -> None:
    """FR-OPT-061: Stage 3 — Parameter Overfit Detection.

    The system shall report parameter-level IS/OOS degradation against a caller-supplied non-negative threshold.
    """
    _header("Stage 3: Overfit Detection - Detect Overfit Parameters (FR-OPT-061)")
    overfit_response = detect_overfit_parameters(
        {"period": 1.0}, {"period": 0.0}, threshold=0.5
    )
    overfit = overfit_response.data
    print(_format_result(overfit_response))
    print(
        f"Data -> flagged_parameters={overfit.flagged_parameters if overfit else None}"
    )


def fr_opt_062() -> None:
    """FR-OPT-062: Stage 3 — Parameter Set Ranking.

    The system shall delegate public candidate ranking to the canonical direction-aware ranking policy.
    """
    _header("Stage 3: Parameter Ranking - Rank Parameter Sets (FR-OPT-062)")
    ranked_response = rank_parameter_sets((candidate_score("a" * 64, 1.0),))
    ranked = ranked_response.data
    print(_format_result(ranked_response))
    print(f"Data -> top_ranked_available={ranked[0].available if ranked else None}")


def fr_opt_063() -> None:
    """FR-OPT-063: Stage 3 — Robustness Score Calculation.

    The system shall calculate a typed percentage over a non-empty sequence of applicable Boolean checks.
    """
    _header("Stage 3: Robustness Score - Calculate Robustness Score (FR-OPT-063)")
    score_response = calculate_robustness_score((True,))
    r_score = score_response.data
    print(_format_result(score_response))
    print(
        f"Data -> robustness_score_percentage={r_score.percentage if r_score else None}"
    )


def fr_opt_064() -> None:
    """FR-OPT-064: Stage 3 — Advisory Handoff Assembly.

    The system shall build the canonical advisory handoff solely from supplied assembly evidence.
    """
    _header("Stage 3: Handoff Handoff - Build Optimization Handoff (FR-OPT-064)")
    assembly_request = evidence_request()
    handoff_response = build_optimization_handoff(assembly_request)
    handoff = handoff_response.data
    handoff_values = dump_optimization_value(handoff)
    print(_format_result(handoff_response))
    print(
        f"Data -> search_id='{handoff_values.get('search_id')}', final_decision='{handoff_values.get('final_decision')}'"
    )


def fr_opt_069() -> None:
    """FR-OPT-069: Stage 1 — Value Function Inspection & Construction.

    The public boundary shall construct, inspect, dump, and identify documented Optimization values through standalone functions while keeping every contract class internal.
    """
    _header("Stage 1: Value Functions - Construct & Inspect Values (FR-OPT-069)")
    val = create_optimization_value(
        "ExecutionStressRequest", kind="spread", value=Decimal("0.5")
    )
    print(_format_result(val))
    print(f"Data -> kind='{getattr(val, 'kind', None)}'")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-OPT-09 — public_api/ — Typed Optimization Boundary\n\n"
        "Purpose: Expose top-level typed Optimization operations (sweeps, walk-forward optimization, robustness analysis, run comparisons, parameter stability, and advisory handoffs).\n\n"
        "Module flow:\n"
        "-> Stage 1: Value inspection/construction functions\n"
        "-> Stage 2: Input payload validation\n"
        "-> Stage 3: Typed public operations (sweep, WFA, matrix, robustness, stability, comparison, and handoff)"
    )

    # Stage 1: Value functions
    fr_opt_069()

    # Stage 3: Typed operations
    fr_opt_056()
    fr_opt_057()
    fr_opt_058()
    fr_opt_059()
    fr_opt_060()
    fr_opt_061()
    fr_opt_062()
    fr_opt_063()
    fr_opt_064()


if __name__ == "__main__":
    main()
