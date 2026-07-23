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


def example_public_api() -> None:
    """Demonstrate top-level public Optimization operations."""
    print("=" * 80)
    print("Optimization Example 9: Public API Operations")
    print("=" * 80)

    adapter = FakeAdapter()

    # 1. Parameter sweep
    sweep_res = run_parameter_sweep(search_request(), adapter)
    print(
        f"Parameter sweep ranked candidates count: {len(sweep_res.ranked_candidates)}"
    )

    # 2. Walk-forward optimization
    wf_res = run_walk_forward_optimization(walk_forward_request(), adapter)
    print(
        f"Walk-forward optimization diagnostic key present: {'walk_forward' in wf_res.diagnostics}"
    )

    # 3. Walk-forward matrix
    matrix_res = run_walk_forward_matrix(
        (walk_forward_request(),), adapter, max_requests=1
    )
    print(f"Walk-forward matrix result count: {len(matrix_res)}")

    # 4. Robustness analysis
    stress_req = ExecutionStressAnalysisRequest(
        outcomes=({"pnl": Decimal(2)},),
        stress=ExecutionStressRequest(kind="spread", value=Decimal(1)),
    )
    analysis_res = run_robustness_analysis(stress_req)
    print(f"Stressed outcomes count: {len(analysis_res.stressed_outcomes)}")

    # 5. Compare optimization runs
    first_ev = build_optimization_evidence(evidence_request())
    second_ev = first_ev.model_copy(update={"search_id": "search-two"})
    comp_res = compare_optimization_runs((first_ev, second_ev))
    print(f"Compared search IDs count: {len(comp_res.search_ids)}")

    # 6. Parameter stability and overfit detection
    stability = calculate_parameter_stability(
        ({"executable_parameters": {"period": 10}},)
    )
    print(f"Parameter stability percentage: {stability.stability_percentage}%")

    overfit = detect_overfit_parameters({"period": 1.0}, {"period": 0.0}, threshold=0.5)
    print(f"Flagged overfit parameters: {overfit.flagged_parameters}")

    # 7. Rank parameter sets and robustness score
    ranked = rank_parameter_sets((_score("a" * 64, 1.0, 1),))
    print(f"Ranked parameter set top available: {ranked[0].available}")

    r_score = calculate_robustness_score((True,))
    print(f"Calculated robustness score percentage: {r_score.percentage}%")

    # 8. Optimization handoff
    handoff = build_optimization_handoff(evidence_request())
    print(f"Optimization handoff contract version: {handoff.contract_version}")


def main() -> None:
    """Run Optimization public API usage example."""
    example_public_api()


if __name__ == "__main__":
    main()
