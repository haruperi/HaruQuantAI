"""Tests for all official Optimization public operations."""

# ruff: noqa: INP001

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
from tests.optimization.unit.test_robustness_contracts import monte_carlo_request
from tests.optimization.unit.test_search_contracts import search_request
from tests.optimization.unit.test_sweep import FakeAdapter
from tests.optimization.unit.test_validation_contracts import walk_forward_request


def test_run_parameter_sweep_returns_advisory_result() -> None:
    """Public sweep delegates search and evidence assembly."""
    result = run_parameter_sweep(search_request(), FakeAdapter())
    assert result.schema_id == "optimization.result.v1"


def test_run_walk_forward_optimization_returns_fold_evidence() -> None:
    """Public WFA delegates the canonical walk-forward workflow."""
    result = run_walk_forward_optimization(walk_forward_request(), FakeAdapter())
    assert result.diagnostics["walk_forward"] is not None


def test_run_walk_forward_matrix_is_bounded_and_ordered() -> None:
    """Public matrix preserves request ordering within its cap."""
    result = run_walk_forward_matrix(
        (walk_forward_request(),), FakeAdapter(), max_requests=1
    )
    assert len(result) == 1


def test_run_robustness_analysis_supports_both_request_forms() -> None:
    """Public robustness accepts MC or explicit stress without ambiguity."""
    monte_carlo = run_robustness_analysis(monte_carlo_request(), max_simulations=5)
    stress = run_robustness_analysis(
        ExecutionStressAnalysisRequest(
            outcomes=({"pnl": Decimal(2)},),
            stress=ExecutionStressRequest(kind="commission", value=Decimal(1)),
        )
    )
    assert monte_carlo.monte_carlo is not None
    assert stress.stressed_outcomes[0]["pnl"] == Decimal(1)


def test_compare_optimization_runs_preserves_existing_decisions() -> None:
    """Public comparison reads compatible evidence without recomputation."""
    first = build_optimization_evidence(evidence_request())
    second = first.model_copy(update={"search_id": "search-two"})
    comparison = compare_optimization_runs((first, second))
    assert comparison.search_ids == (first.search_id, "search-two")


def test_calculate_parameter_stability_uses_exact_values() -> None:
    """Public stability separates exact stable and varying parameters."""
    evidence = calculate_parameter_stability(
        (
            {"executable_parameters": {"period": 10, "enabled": True}},
            {"executable_parameters": {"period": 12, "enabled": True}},
        )
    )
    assert evidence.stable_parameters == ("enabled",)
    assert evidence.varying_parameters == ("period",)


def test_detect_overfit_parameters_uses_explicit_threshold() -> None:
    """Public overfit detection flags only threshold-exceeding degradation."""
    evidence = detect_overfit_parameters(
        {"period": 10.0, "threshold": 5.0},
        {"period": 5.0, "threshold": 4.5},
        threshold=0.2,
    )
    assert evidence.flagged_parameters == ("period",)


def test_rank_parameter_sets_delegates_canonical_ranking() -> None:
    """Public ranking preserves canonical score direction and tie-breakers."""
    ranked = rank_parameter_sets((_score("a" * 64, 1.0, 1), _score("b" * 64, 2.0, 1)))
    assert ranked[0].candidate_hash == "b" * 64


def test_calculate_robustness_score_counts_applicable_checks() -> None:
    """Public score denominator includes only supplied checks."""
    score = calculate_robustness_score((True, False, True))
    assert score.passed_checks == 2
    assert score.applicable_checks == 3


def test_build_optimization_handoff_delegates_canonical_assembly() -> None:
    """Public handoff equals direct canonical evidence assembly."""
    request = evidence_request()
    assert build_optimization_handoff(request) == build_optimization_evidence(request)
