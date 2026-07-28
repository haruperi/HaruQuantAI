"""Executable Optimization public API usage example.

Demonstrates parameter sweeps, walk-forward optimization, execution stress analysis,
optimization comparison, parameter stability, and overfit detection.
"""

import sys
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.optimization.evidence import build_optimization_evidence
from app.services.optimization.public_api import (
    build_optimization_handoff,
    calculate_parameter_stability,
    calculate_robustness_score,
    compare_optimization_runs,
    detect_overfit_parameters,
    rank_parameter_sets,
    run_parameter_sweep,
    run_robustness_analysis,
    run_walk_forward_matrix,
    run_walk_forward_optimization,
)
from app.services.optimization.public_api.contracts import (
    ExecutionStressAnalysisRequest,
)
from app.services.optimization.robustness import ExecutionStressRequest
from tests.optimization.unit.test_evidence_contracts import evidence_request
from tests.optimization.unit.test_ranking import _score
from tests.optimization.unit.test_search_contracts import search_request
from tests.optimization.unit.test_sweep import FakeAdapter
from tests.optimization.unit.test_validation_contracts import walk_forward_request


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def example_public_api() -> None:
    """Demonstrate top-level public Optimization operations."""
    _header("Demonstrate top-level public Optimization operations.")
    print("Optimization Example 9: Public API Operations")

    adapter = FakeAdapter()

    # 1. Parameter sweep
    sweep_response = run_parameter_sweep(search_request(), adapter)
    assert sweep_response.data is not None
    sweep_res = sweep_response.data
    print(
        f"Parameter sweep ranked candidates count: {len(sweep_res.ranked_candidates)}"
    )

    # 2. Walk-forward optimization
    wf_response = run_walk_forward_optimization(walk_forward_request(), adapter)
    assert wf_response.data is not None
    wf_res = wf_response.data
    print(
        "Walk-forward optimization diagnostic key present: "
        f"{'walk_forward' in wf_res.diagnostics}"
    )

    # 3. Walk-forward matrix
    matrix_response = run_walk_forward_matrix(
        (walk_forward_request(),), adapter, max_requests=1
    )
    assert matrix_response.data is not None
    matrix_res = matrix_response.data
    print(f"Walk-forward matrix result count: {len(matrix_res)}")

    # 4. Robustness analysis
    stress_req = ExecutionStressAnalysisRequest(
        outcomes=({"pnl": Decimal(2)},),
        stress=ExecutionStressRequest(kind="spread", value=Decimal(1)),
    )
    analysis_response = run_robustness_analysis(stress_req)
    assert analysis_response.data is not None
    analysis_res = analysis_response.data
    print(f"Stressed outcomes count: {len(analysis_res.stressed_outcomes)}")

    # 5. Compare optimization runs
    first_ev = build_optimization_evidence(evidence_request())
    second_ev = first_ev.model_copy(update={"search_id": "search-two"})
    comp_response = compare_optimization_runs((first_ev, second_ev))
    assert comp_response.data is not None
    comp_res = comp_response.data
    print(f"Compared search IDs count: {len(comp_res.search_ids)}")

    # 6. Parameter stability and overfit detection
    stability_response = calculate_parameter_stability(
        ({"executable_parameters": {"period": 10}},)
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
    ranked_response = rank_parameter_sets((_score("a" * 64, 1.0, 1),))
    assert ranked_response.data is not None
    ranked = ranked_response.data
    print(f"Ranked parameter set top available: {ranked[0].available}")

    score_response = calculate_robustness_score((True,))
    assert score_response.data is not None
    r_score = score_response.data
    print(f"Calculated robustness score percentage: {r_score.percentage}%")

    # 8. Optimization handoff
    handoff_response = build_optimization_handoff(evidence_request())
    assert handoff_response.data is not None
    handoff = handoff_response.data
    print(f"Optimization handoff contract version: {handoff.contract_version}")


def main() -> None:
    """Run Optimization public API usage example."""
    example_public_api()


if __name__ == "__main__":
    main()
