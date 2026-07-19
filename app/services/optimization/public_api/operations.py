"""Thin typed orchestration operations for the Optimization domain."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from app.services.optimization.evidence import (
    EvidenceAssemblyRequest,
    OptimizationResult,
    build_optimization_evidence,
)
from app.services.optimization.execution import BacktestExecutionAdapter  # noqa: TC001
from app.services.optimization.public_api.contracts import (
    OptimizationComparison,
    OverfitParameterEvidence,
    ParameterStabilityEvidence,
    RobustnessAnalysisResult,
    RobustnessRequest,
    RobustnessScore,
)
from app.services.optimization.public_api.validation import (
    validate_compatible_results,
    validate_request_id,
    validate_walk_forward_matrix,
)
from app.services.optimization.robustness import (
    MonteCarloRequest,
    apply_execution_cost_stress,
    run_monte_carlo,
)
from app.services.optimization.scoring import CandidateScore, rank_candidates
from app.services.optimization.search import SearchRequest, run_bounded_search
from app.services.optimization.validation import (
    WalkForwardRequest,
    run_walk_forward_validation,
)
from app.utils import logger


def _with_request_id(request: SearchRequest, request_id: str | None) -> SearchRequest:
    """Propagate an optional request ID into an immutable search request.

    Args:
        request: Validated search request.
        request_id: Optional caller-owned trace identity.

    Returns:
        Original or updated immutable request.
    """
    logger.debug("Propagating Optimization public request ID")
    validated = validate_request_id(request_id)
    return (
        request
        if validated is None
        else request.model_copy(update={"request_id": validated})
    )


def run_parameter_sweep(
    request: SearchRequest,
    adapter: BacktestExecutionAdapter,
    *,
    request_id: str | None = None,
) -> OptimizationResult:
    """Run a bounded search and assemble advisory baseline evidence.

    Args:
        request: Validated bounded search request.
        adapter: Injected deterministic Simulation boundary.
        request_id: Optional trace identity override.

    Returns:
        Advisory Optimization result version one.
    """
    logger.info("Running Optimization public parameter sweep")
    summary = run_bounded_search(_with_request_id(request, request_id), adapter)
    return build_optimization_evidence(EvidenceAssemblyRequest(search=summary))


def run_walk_forward_optimization(
    request: WalkForwardRequest,
    adapter: BacktestExecutionAdapter,
    *,
    request_id: str | None = None,
) -> OptimizationResult:
    """Run baseline search plus walk-forward validation and assemble evidence.

    Args:
        request: Validated walk-forward request.
        adapter: Injected deterministic Simulation boundary.
        request_id: Optional trace identity override.

    Returns:
        Advisory Optimization result containing walk-forward evidence.
    """
    logger.info("Running Optimization public walk-forward optimization")
    search = _with_request_id(request.search, request_id)
    normalized = request.model_copy(update={"search": search})
    summary = run_bounded_search(search, adapter)
    walk_forward = run_walk_forward_validation(normalized, adapter)
    return build_optimization_evidence(
        EvidenceAssemblyRequest(search=summary, walk_forward=walk_forward)
    )


def run_walk_forward_matrix(
    requests: Sequence[WalkForwardRequest],
    adapter: BacktestExecutionAdapter,
    *,
    max_requests: int,
    request_id: str | None = None,
) -> tuple[OptimizationResult, ...]:
    """Run a bounded compatible sequence of walk-forward requests.

    Args:
        requests: Compatible walk-forward requests.
        adapter: Injected deterministic Simulation boundary.
        max_requests: Explicit matrix cap.
        request_id: Optional base trace identity.

    Returns:
        Ordered Optimization results.
    """
    logger.info("Running bounded Optimization walk-forward matrix")
    values = validate_walk_forward_matrix(requests, max_requests=max_requests)
    base_id = validate_request_id(request_id)
    return tuple(
        run_walk_forward_optimization(
            item,
            adapter,
            request_id=None if base_id is None else f"{base_id}-{index}",
        )
        for index, item in enumerate(values)
    )


def run_robustness_analysis(
    request: RobustnessRequest,
    *,
    max_simulations: int = 2000,
    request_id: str | None = None,
) -> RobustnessAnalysisResult:
    """Run one approved Monte Carlo or execution-stress request.

    Args:
        request: Typed Monte Carlo or stress analysis request.
        max_simulations: Explicit Monte Carlo path cap.
        request_id: Optional trace identity for observability.

    Returns:
        Versioned robustness evidence.
    """
    logger.info("Running Optimization public robustness analysis")
    validate_request_id(request_id)
    if isinstance(request, MonteCarloRequest):
        return RobustnessAnalysisResult(
            monte_carlo=run_monte_carlo(request, max_simulations=max_simulations)
        )
    return RobustnessAnalysisResult(
        stressed_outcomes=apply_execution_cost_stress(request.outcomes, request.stress)
    )


def compare_optimization_runs(
    results: Sequence[OptimizationResult], *, request_id: str | None = None
) -> OptimizationComparison:
    """Compare compatible results without recomputing their evidence.

    Args:
        results: Compatible versioned Optimization results.
        request_id: Optional trace identity.

    Returns:
        Typed ordered comparison evidence.
    """
    logger.info("Comparing compatible Optimization runs")
    validate_request_id(request_id)
    values = validate_compatible_results(results)
    return OptimizationComparison(
        search_ids=tuple(item.search_id for item in values),
        decisions=tuple(item.final_decision.value for item in values),
        best_candidate_hashes=tuple(
            (
                str(item.ranked_candidates[0].get("candidate_hash"))
                if item.ranked_candidates
                else None
            )
            for item in values
        ),
    )


def calculate_parameter_stability(
    ranked_candidates: Sequence[Mapping[str, object]],
    *,
    request_id: str | None = None,
) -> ParameterStabilityEvidence:
    """Calculate exact-match stability over supplied executable parameters.

    Args:
        ranked_candidates: Candidate evidence with executable parameters.
        request_id: Optional trace identity.

    Returns:
        Typed stability evidence.

    Raises:
        ValueError: If candidates or parameter mappings are invalid.
    """
    logger.info("Calculating Optimization parameter stability")
    validate_request_id(request_id)
    values = tuple(ranked_candidates)
    if not values:
        raise ValueError("parameter stability candidates cannot be empty")
    parameters: list[Mapping[str, object]] = []
    for candidate in values:
        item = candidate.get("executable_parameters")
        if not isinstance(item, Mapping) or not item:
            raise ValueError("candidate executable parameters are required")
        parameters.append(item)
    names = set(parameters[0])
    if any(set(item) != names for item in parameters[1:]):
        raise ValueError("candidate parameter names must match")
    stable = tuple(
        sorted(
            name
            for name in names
            if len({repr(item[name]) for item in parameters}) == 1
        )
    )
    varying = tuple(sorted(names.difference(stable)))
    return ParameterStabilityEvidence(
        candidate_count=len(parameters),
        stable_parameters=stable,
        varying_parameters=varying,
        stability_percentage=100.0 * len(stable) / len(names),
    )


def detect_overfit_parameters(
    in_sample: Mapping[str, float],
    out_of_sample: Mapping[str, float],
    *,
    threshold: float,
    request_id: str | None = None,
) -> OverfitParameterEvidence:
    """Detect parameter evidence whose relative score degradation exceeds a threshold.

    Args:
        in_sample: Parameter-name to in-sample score mapping.
        out_of_sample: Matching out-of-sample scores.
        threshold: Non-negative relative degradation threshold.
        request_id: Optional trace identity.

    Returns:
        Typed per-parameter overfit evidence.

    Raises:
        ValueError: If keys, scores, or threshold are invalid.
    """
    logger.info("Detecting supplied Optimization overfit parameters")
    validate_request_id(request_id)
    if (
        not math.isfinite(threshold)
        or threshold < 0
        or not in_sample
        or set(in_sample) != set(out_of_sample)
    ):
        raise ValueError("overfit parameter evidence is incompatible")
    degradation: dict[str, float | None] = {}
    for name in sorted(in_sample):
        in_value = in_sample[name]
        out_value = out_of_sample[name]
        if not math.isfinite(in_value) or not math.isfinite(out_value):
            raise ValueError("overfit parameter scores must be finite")
        degradation[name] = (
            None if in_value == 0 else (in_value - out_value) / abs(in_value)
        )
    flagged = tuple(
        name
        for name, value in degradation.items()
        if value is not None and value > threshold
    )
    return OverfitParameterEvidence(
        threshold=threshold,
        degradation=degradation,
        flagged_parameters=flagged,
    )


def rank_parameter_sets(
    candidates: Sequence[CandidateScore], *, request_id: str | None = None
) -> tuple[CandidateScore, ...]:
    """Delegate deterministic ranking to the scoring capability.

    Args:
        candidates: Supplied candidate scores.
        request_id: Optional trace identity.

    Returns:
        Deterministically ranked candidate scores.
    """
    logger.info("Ranking Optimization parameter sets")
    validate_request_id(request_id)
    return rank_candidates(candidates)


def calculate_robustness_score(
    checks: Sequence[bool], *, request_id: str | None = None
) -> RobustnessScore:
    """Calculate a percentage over non-empty applicable Boolean checks.

    Args:
        checks: Applicable pass/fail checks.
        request_id: Optional trace identity.

    Returns:
        Typed robustness score.

    Raises:
        ValueError: If no applicable check is supplied.
    """
    logger.info("Calculating Optimization public robustness score")
    validate_request_id(request_id)
    values = tuple(checks)
    if not values:
        raise ValueError("robustness checks cannot be empty")
    passed = sum(values)
    return RobustnessScore(
        passed_checks=passed,
        applicable_checks=len(values),
        percentage=100.0 * passed / len(values),
    )


def build_optimization_handoff(
    request: EvidenceAssemblyRequest, *, request_id: str | None = None
) -> OptimizationResult:
    """Build the canonical versioned Optimization handoff result.

    Args:
        request: Supplied evidence assembly request.
        request_id: Optional trace identity.

    Returns:
        Canonical advisory Optimization result.
    """
    logger.info("Building Optimization public evidence handoff")
    validate_request_id(request_id)
    return build_optimization_evidence(request)


__all__ = [
    "build_optimization_handoff",
    "calculate_parameter_stability",
    "calculate_robustness_score",
    "compare_optimization_runs",
    "detect_overfit_parameters",
    "rank_parameter_sets",
    "run_parameter_sweep",
    "run_robustness_analysis",
    "run_walk_forward_matrix",
    "run_walk_forward_optimization",
]
