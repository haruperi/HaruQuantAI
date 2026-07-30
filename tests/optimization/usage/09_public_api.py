"""Executable Optimization public API usage example.

Demonstrates parameter sweeps, walk-forward optimization, robustness analysis,
optimization comparison, parameter stability, and overfit detection.
"""

import sys
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

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


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def example_public_api() -> None:  # noqa: PLR0915
    """Demonstrate top-level public Optimization operations."""
    _header("Demonstrate top-level public Optimization operations.")
    print("Optimization Example 9: Public API Operations")

    dataset, _, adapter = genuine_execution_bundle()

    # 1. Parameter sweep
    sweep_response = run_parameter_sweep(search_request(dataset), adapter)
    assert sweep_response.data is not None
    sweep_res = sweep_response.data
    print(
        f"Parameter sweep ranked candidates count: {len(sweep_res.ranked_candidates)}"
    )

    # 2. Walk-forward optimization
    request = walk_forward_request(dataset)
    wf_response = run_walk_forward_optimization(request, adapter)
    assert wf_response.data is not None
    wf_res = wf_response.data
    print(
        "Walk-forward optimization diagnostic key present: "
        f"{'walk_forward' in wf_res.diagnostics}"
    )

    # 3. Walk-forward matrix
    matrix_response = run_walk_forward_matrix((request,), adapter, max_requests=1)
    assert matrix_response.data is not None
    matrix_res = matrix_response.data
    print(f"Walk-forward matrix result count: {len(matrix_res)}")

    # 4. Robustness analysis
    analysis_request = monte_carlo_request(
        outcomes=(Decimal("1.5"), Decimal("-0.5"), Decimal(2)),
        simulations=5,
        seed=22,
    )
    analysis_response = run_robustness_analysis(analysis_request)
    assert analysis_response.data is not None
    analysis_res = analysis_response.data
    if analysis_res.monte_carlo is not None:
        print(f"Monte Carlo simulation count: {analysis_res.monte_carlo.simulations}")

    # 5. Compare optimization runs
    assembly_request = evidence_request()
    first_ev = build_optimization_evidence(assembly_request)
    second_values = dump_optimization_value(first_ev)
    second_values["search_id"] = "search-two"
    second_ev = create_optimization_value("OptimizationResult", **second_values)
    comp_response = compare_optimization_runs((first_ev, second_ev))
    assert comp_response.data is not None
    comp_res = comp_response.data
    print(f"Compared search IDs count: {len(comp_res.search_ids)}")

    # 6. Parameter stability and overfit detection
    stability_response = calculate_parameter_stability(
        (
            {"executable_parameters": {"period": 10}},
            {"executable_parameters": {"period": 12}},
        )
    )
    assert stability_response.data is not None
    stability = stability_response.data
    print(f"Parameter stability percentage: {stability.stability_percentage}%")

    overfit_response = detect_overfit_parameters(
        {"period": 1.0}, {"period": 0.0}, threshold=0.5
    )
    assert overfit_response.data is not None
    overfit = overfit_response.data
    print(f"Flagged overfit parameters: {overfit.flagged_parameters}")

    # 7. Rank parameter sets and robustness score
    ranked_response = rank_parameter_sets((candidate_score("a" * 64, 1.0),))
    assert ranked_response.data is not None
    ranked = ranked_response.data
    print(f"Ranked parameter set top available: {ranked[0].available}")

    score_response = calculate_robustness_score((True,))
    assert score_response.data is not None
    r_score = score_response.data
    print(f"Calculated robustness score percentage: {r_score.percentage}%")

    # 8. Optimization handoff
    handoff_response = build_optimization_handoff(assembly_request)
    assert handoff_response.data is not None
    handoff = handoff_response.data
    handoff_values = dump_optimization_value(handoff)
    print(
        "Optimization handoff from genuine MT5 evidence:",
        {
            "search_id": handoff_values["search_id"],
            "reproducibility_hash": handoff_values["reproducibility_hash"],
            "ranked_candidate_count": len(handoff_values["ranked_candidates"]),
            "candidate_scores": tuple(
                candidate["score"]["value"]
                for candidate in handoff_values["ranked_candidates"]
            ),
            "warnings": handoff_values["warnings"],
            "final_decision": handoff_values["final_decision"],
        },
    )


def main() -> None:
    """Run Optimization public API usage example."""
    example_public_api()


if __name__ == "__main__":
    main()
