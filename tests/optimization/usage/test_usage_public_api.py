"""Runnable usage evidence for official Optimization operations."""

from decimal import Decimal

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


def test_usage_run_parameter_sweep() -> None:
    """Run a bounded public parameter sweep."""
    assert run_parameter_sweep(search_request(), FakeAdapter()).ranked_candidates


def test_usage_run_walk_forward_optimization() -> None:
    """Run one public walk-forward optimization."""
    result = run_walk_forward_optimization(walk_forward_request(), FakeAdapter())
    assert result.diagnostics["walk_forward"]


def test_usage_run_walk_forward_matrix() -> None:
    """Run a one-request bounded public matrix."""
    assert (
        len(
            run_walk_forward_matrix(
                (walk_forward_request(),), FakeAdapter(), max_requests=1
            )
        )
        == 1
    )


def test_usage_run_robustness_analysis() -> None:
    """Run one explicit execution-cost analysis."""
    request = ExecutionStressAnalysisRequest(
        outcomes=({"pnl": Decimal(2)},),
        stress=ExecutionStressRequest(kind="spread", value=Decimal(1)),
    )
    assert run_robustness_analysis(request).stressed_outcomes


def test_usage_compare_optimization_runs() -> None:
    """Compare two compatible result contracts."""
    first = build_optimization_evidence(evidence_request())
    second = first.model_copy(update={"search_id": "search-two"})
    assert len(compare_optimization_runs((first, second)).search_ids) == 2


def test_usage_calculate_parameter_stability() -> None:
    """Calculate exact-match candidate parameter stability."""
    assert (
        calculate_parameter_stability(
            ({"executable_parameters": {"period": 10}},)
        ).stability_percentage
        == 100
    )


def test_usage_detect_overfit_parameters() -> None:
    """Detect degradation using an explicit threshold."""
    assert detect_overfit_parameters(
        {"period": 1.0}, {"period": 0.0}, threshold=0.5
    ).flagged_parameters == ("period",)


def test_usage_rank_parameter_sets() -> None:
    """Rank supplied candidate score evidence."""
    assert rank_parameter_sets((_score("a" * 64, 1.0, 1),))[0].available


def test_usage_calculate_robustness_score() -> None:
    """Calculate a score over applicable checks."""
    assert calculate_robustness_score((True,)).percentage == 100


def test_usage_build_optimization_handoff() -> None:
    """Build the canonical advisory evidence handoff."""
    assert build_optimization_handoff(evidence_request()).contract_version == "v1"
