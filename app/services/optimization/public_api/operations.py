"""Typed orchestration operations for the Optimization public boundary."""

from __future__ import annotations

import functools
import inspect
import math
import time
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Literal, ParamSpec, TypeVar, cast

from app.services.optimization.errors import (
    OPTIMIZATION_ERROR_CATALOG,
    OptimizationError,
)
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
from app.utils import (
    build_response_metadata,
    error_response,
    generate_id,
    get_logger,
    success_response,
    validate_id,
)

type JsonValue = Any
type ResponseMetadata = Any
type StandardResponse[T] = Any
RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)

_P = ParamSpec("_P")
_R = TypeVar("_R")


def _canonical_trace_context(
    args: tuple[object, ...], kwargs: Mapping[str, object]
) -> tuple[str, str | None]:
    """Resolve caller trace fields without exposing invalid identifiers.

    Args:
        args: Positional public-operation arguments.
        kwargs: Keyword public-operation arguments.

    Returns:
        Canonical request and optional correlation identifiers.
    """
    values = (kwargs.get("request_id"), *args, *kwargs.values())
    request_id: str | None = None
    correlation_id: str | None = None
    for value in values:
        candidate = (
            value if isinstance(value, str) else getattr(value, "request_id", None)
        )
        if request_id is None and isinstance(candidate, str):
            try:
                request_id = validate_id(candidate, expected_prefix="req")
            except Exception:
                continue
        candidate_correlation = getattr(value, "correlation_id", None)
        if correlation_id is None and isinstance(candidate_correlation, str):
            try:
                correlation_id = validate_id(
                    candidate_correlation, expected_prefix="cor"
                )
            except Exception:
                continue
        if request_id is not None and correlation_id is not None:
            break
    return request_id or generate_id("req"), correlation_id


def _operation_extensions(
    function_name: str,
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
) -> Mapping[str, JsonValue]:
    """Build bounded non-payload metadata for one Optimization operation.

    Args:
        function_name: Public operation name.
        args: Positional public-operation arguments.
        kwargs: Keyword public-operation arguments.

    Returns:
        Safe metadata extensions that do not duplicate business evidence.
    """
    if function_name == "build_optimization_handoff":
        return {"advisory_only": True, "approval_required": True}
    if function_name == "run_robustness_analysis":
        request = kwargs.get("request")
        if request is None and args:
            request = args[0]
        max_simulations = kwargs.get("max_simulations", 2000)
        if not isinstance(max_simulations, int):
            max_simulations = 2000
        return {
            "analysis_mode": (
                "monte_carlo" if isinstance(request, MonteCarloRequest) else "stress"
            ),
            "max_simulations": max_simulations,
        }
    if function_name in {
        "run_parameter_sweep",
        "run_walk_forward_optimization",
        "run_walk_forward_matrix",
    }:
        adapter = kwargs.get("adapter")
        if adapter is None and len(args) > 1:
            adapter = args[1]
        return {"adapter_type": type(adapter).__name__}
    return {}


def _metadata(
    function: Callable[..., object],
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
    started: int,
    *,
    risk_level: RiskLevel,
    requires_network: bool,
) -> ResponseMetadata:
    """Build response metadata for one Optimization operation.

    Args:
        function: Wrapped public operation.
        args: Positional operation arguments.
        kwargs: Keyword operation arguments.
        started: Monotonic nanosecond start time.
        risk_level: Static operation risk classification.
        requires_network: Whether the injected operation may use a network.

    Returns:
        Immutable shared response metadata.
    """
    request_id, correlation_id = _canonical_trace_context(args, kwargs)
    operation = (
        f"{function.__module__.removeprefix('app.services.')}.{function.__name__}"
    )
    return build_response_metadata(
        name=operation,
        domain="optimization",
        risk_level=risk_level,
        request_id=request_id,
        correlation_id=correlation_id,
        start_time=started,
        read_only=True,
        writes_file=False,
        modifies_database=False,
        places_trade=False,
        requires_network=requires_network,
        extensions=_operation_extensions(function.__name__, args, kwargs),
    )


def _optimization_boundary(
    *, risk_level: RiskLevel, requires_network: bool
) -> Callable[[Callable[_P, _R]], Callable[_P, StandardResponse[_R]]]:
    """Create the single outer response boundary for an official operation.

    Args:
        risk_level: Static operation risk classification.
        requires_network: Whether the operation may invoke a remote adapter.

    Returns:
        Decorator returning a five-field standard response.
    """

    def decorate(function: Callable[_P, _R]) -> Callable[_P, StandardResponse[_R]]:
        """Wrap one raw Optimization operation.

        Returns:
            Decorated operation returning a standard response.
        """

        @functools.wraps(function)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> StandardResponse[_R]:
            """Execute one raw operation under the Optimization response contract.

            Returns:
                Standard response containing raw data or a safe error.
            """
            started = time.perf_counter_ns()

            def response_metadata() -> ResponseMetadata:
                """Build completion metadata after the operation finishes.

                Returns:
                    Immutable shared response metadata.
                """
                return _metadata(
                    function,
                    args,
                    kwargs,
                    started,
                    risk_level=risk_level,
                    requires_network=requires_network,
                )

            try:
                raw_result = function(*args, **kwargs)
            except OptimizationError as error:
                details: dict[str, JsonValue] = {"detail": error.detail}
                details.update(
                    {
                        key: cast("JsonValue", value)
                        for key, value in error.safe_details.items()
                    }
                )
                definition = OPTIMIZATION_ERROR_CATALOG[error.code]
                logger.info(
                    "Optimization operation returned catalogued error %s",
                    error.code,
                )
                return error_response(
                    code=error.code,
                    details=details,
                    message=definition.description,
                    metadata=response_metadata(),
                    catalog=OPTIMIZATION_ERROR_CATALOG,
                )
            except ValueError as error:
                logger.info(
                    "Optimization operation rejected invalid request: %s",
                    function.__name__,
                )
                return error_response(
                    code="OPT_INVALID_REQUEST",
                    details={
                        "detail": "INVALID_REQUEST",
                        "failure_type": type(error).__name__,
                    },
                    message=OPTIMIZATION_ERROR_CATALOG[
                        "OPT_INVALID_REQUEST"
                    ].description,
                    metadata=response_metadata(),
                    catalog=OPTIMIZATION_ERROR_CATALOG,
                )
            except Exception as error:  # noqa: BLE001 - outer fail-closed boundary.
                failure_type = type(error).__name__
                logger.error(
                    "Unexpected %s escaped Optimization operation %s",
                    failure_type,
                    function.__name__,
                )
                return error_response(
                    code="OPT_INTERNAL_ERROR",
                    details={
                        "operation": function.__name__,
                        "failure_type": failure_type,
                    },
                    message=OPTIMIZATION_ERROR_CATALOG[
                        "OPT_INTERNAL_ERROR"
                    ].description,
                    metadata=response_metadata(),
                    catalog=OPTIMIZATION_ERROR_CATALOG,
                )
            return success_response(
                raw_result,
                message=f"{function.__name__} completed successfully",
                metadata=response_metadata(),
            )

        signature = inspect.signature(function)
        return_annotation = signature.return_annotation
        if return_annotation is inspect.Signature.empty:
            return_annotation = "object"
        if isinstance(return_annotation, str):
            response_annotation = f"StandardResponse[{return_annotation}]"
        else:
            response_annotation = f"StandardResponse[{return_annotation!r}]"
        wrapper.__signature__ = signature.replace(  # type: ignore[attr-defined]
            return_annotation=response_annotation
        )
        wrapper.__annotations__ = {
            **wrapper.__annotations__,
            "return": response_annotation,
        }
        return wrapper

    return decorate


def _run_parameter_sweep(
    request: SearchRequest,
    adapter: BacktestExecutionAdapter,
    *,
    request_id: str | None = None,
) -> OptimizationResult:
    """Run a bounded search and assemble raw advisory evidence.

    Returns:
        Raw assembled Optimization evidence.
    """
    logger.info("Running Optimization public parameter sweep")
    summary = run_bounded_search(_with_request_id(request, request_id), adapter)
    return build_optimization_evidence(EvidenceAssemblyRequest(search=summary))


def _run_walk_forward_optimization(
    request: WalkForwardRequest,
    adapter: BacktestExecutionAdapter,
    *,
    request_id: str | None = None,
) -> OptimizationResult:
    """Run raw baseline and walk-forward evidence assembly.

    Returns:
        Raw assembled Optimization evidence.
    """
    logger.info("Running Optimization public walk-forward optimization")
    search = _with_request_id(request.search, request_id)
    normalized = request.model_copy(update={"search": search})
    summary = run_bounded_search(search, adapter)
    walk_forward = run_walk_forward_validation(normalized, adapter)
    return build_optimization_evidence(
        EvidenceAssemblyRequest(search=summary, walk_forward=walk_forward)
    )


def _run_walk_forward_matrix(
    requests: Sequence[WalkForwardRequest],
    adapter: BacktestExecutionAdapter,
    *,
    max_requests: int,
    request_id: str | None = None,
) -> tuple[OptimizationResult, ...]:
    """Run raw compatible walk-forward requests in caller order.

    Returns:
        Ordered raw Optimization evidence.
    """
    logger.info("Running bounded Optimization walk-forward matrix")
    values = validate_walk_forward_matrix(requests, max_requests=max_requests)
    validate_request_id(request_id)
    return tuple(_run_walk_forward_optimization(item, adapter) for item in values)


def _run_robustness_analysis(
    request: RobustnessRequest,
    *,
    max_simulations: int = 2000,
    request_id: str | None = None,
) -> RobustnessAnalysisResult:
    """Run raw Monte Carlo or execution-stress evidence.

    Returns:
        Raw robustness evidence.
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


def _compare_optimization_runs(
    results: Sequence[OptimizationResult], *, request_id: str | None = None
) -> OptimizationComparison:
    """Compare raw compatible Optimization evidence.

    Returns:
        Raw comparison evidence.
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


def _calculate_parameter_stability(
    ranked_candidates: Sequence[Mapping[str, object]],
    *,
    request_id: str | None = None,
) -> ParameterStabilityEvidence:
    """Calculate raw exact-match parameter stability evidence.

    Returns:
        Raw parameter stability evidence.

    Raises:
        ValueError: If candidate evidence is empty or incompatible.
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


def _detect_overfit_parameters(
    in_sample: Mapping[str, float],
    out_of_sample: Mapping[str, float],
    *,
    threshold: float,
    request_id: str | None = None,
) -> OverfitParameterEvidence:
    """Calculate raw parameter-level degradation evidence.

    Returns:
        Raw overfit evidence.

    Raises:
        ValueError: If scores, keys, or threshold are invalid.
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


def _rank_parameter_sets(
    candidates: Sequence[CandidateScore], *, request_id: str | None = None
) -> tuple[CandidateScore, ...]:
    """Return raw deterministic candidate ranking.

    Returns:
        Raw ordered candidate scores.
    """
    logger.info("Ranking Optimization parameter sets")
    validate_request_id(request_id)
    return rank_candidates(candidates)


def _calculate_robustness_score(
    checks: Sequence[bool], *, request_id: str | None = None
) -> RobustnessScore:
    """Calculate raw percentage over applicable Boolean checks.

    Returns:
        Raw robustness score.

    Raises:
        ValueError: If no checks are supplied.
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


def _build_optimization_handoff(
    request: EvidenceAssemblyRequest, *, request_id: str | None = None
) -> OptimizationResult:
    """Build raw canonical advisory handoff evidence.

    Returns:
        Raw advisory Optimization evidence.
    """
    logger.info("Building Optimization public evidence handoff")
    validate_request_id(request_id)
    return build_optimization_evidence(request)


def _with_request_id(request: SearchRequest, request_id: str | None) -> SearchRequest:
    """Propagate an optional request ID into an immutable search request.

    Returns:
        Original or request-ID-updated search request.
    """
    logger.debug("Propagating Optimization public request ID")
    validated = validate_request_id(request_id)
    return (
        request
        if validated is None
        else request.model_copy(update={"request_id": validated})
    )


@_optimization_boundary(risk_level="medium", requires_network=True)
def run_parameter_sweep(
    request: SearchRequest,
    adapter: BacktestExecutionAdapter,
    *,
    request_id: str | None = None,
) -> OptimizationResult:
    """Run a bounded search and assemble advisory baseline evidence.

    Returns:
        Standard response containing raw Optimization evidence.
    """
    return _run_parameter_sweep(request, adapter, request_id=request_id)


@_optimization_boundary(risk_level="medium", requires_network=True)
def run_walk_forward_optimization(
    request: WalkForwardRequest,
    adapter: BacktestExecutionAdapter,
    *,
    request_id: str | None = None,
) -> OptimizationResult:
    """Run baseline search plus walk-forward validation.

    Returns:
        Standard response containing raw Optimization evidence.
    """
    return _run_walk_forward_optimization(request, adapter, request_id=request_id)


@_optimization_boundary(risk_level="medium", requires_network=True)
def run_walk_forward_matrix(
    requests: Sequence[WalkForwardRequest],
    adapter: BacktestExecutionAdapter,
    *,
    max_requests: int,
    request_id: str | None = None,
) -> tuple[OptimizationResult, ...]:
    """Run a bounded compatible sequence of walk-forward requests.

    Returns:
        Standard response containing ordered raw Optimization evidence.
    """
    return _run_walk_forward_matrix(
        requests,
        adapter,
        max_requests=max_requests,
        request_id=request_id,
    )


@_optimization_boundary(risk_level="medium", requires_network=False)
def run_robustness_analysis(
    request: RobustnessRequest,
    *,
    max_simulations: int = 2000,
    request_id: str | None = None,
) -> RobustnessAnalysisResult:
    """Run one approved Monte Carlo or execution-stress request.

    Returns:
        Standard response containing raw robustness evidence.
    """
    return _run_robustness_analysis(
        request,
        max_simulations=max_simulations,
        request_id=request_id,
    )


@_optimization_boundary(risk_level="low", requires_network=False)
def compare_optimization_runs(
    results: Sequence[OptimizationResult], *, request_id: str | None = None
) -> OptimizationComparison:
    """Compare compatible results without recomputing their evidence.

    Returns:
        Standard response containing raw comparison evidence.
    """
    return _compare_optimization_runs(results, request_id=request_id)


@_optimization_boundary(risk_level="low", requires_network=False)
def calculate_parameter_stability(
    ranked_candidates: Sequence[Mapping[str, object]],
    *,
    request_id: str | None = None,
) -> ParameterStabilityEvidence:
    """Calculate exact-match stability over supplied executable parameters.

    Returns:
        Standard response containing raw stability evidence.
    """
    return _calculate_parameter_stability(
        ranked_candidates,
        request_id=request_id,
    )


@_optimization_boundary(risk_level="medium", requires_network=False)
def detect_overfit_parameters(
    in_sample: Mapping[str, float],
    out_of_sample: Mapping[str, float],
    *,
    threshold: float,
    request_id: str | None = None,
) -> OverfitParameterEvidence:
    """Detect parameter evidence whose degradation exceeds a threshold.

    Returns:
        Standard response containing raw overfit evidence.
    """
    return _detect_overfit_parameters(
        in_sample,
        out_of_sample,
        threshold=threshold,
        request_id=request_id,
    )


@_optimization_boundary(risk_level="low", requires_network=False)
def rank_parameter_sets(
    candidates: Sequence[CandidateScore], *, request_id: str | None = None
) -> tuple[CandidateScore, ...]:
    """Delegate deterministic ranking to the scoring capability.

    Returns:
        Standard response containing ordered raw candidate scores.
    """
    return _rank_parameter_sets(candidates, request_id=request_id)


@_optimization_boundary(risk_level="medium", requires_network=False)
def calculate_robustness_score(
    checks: Sequence[bool], *, request_id: str | None = None
) -> RobustnessScore:
    """Calculate a percentage over supplied applicable Boolean checks.

    Returns:
        Standard response containing raw robustness score.
    """
    return _calculate_robustness_score(checks, request_id=request_id)


@_optimization_boundary(risk_level="high", requires_network=False)
def build_optimization_handoff(
    request: EvidenceAssemblyRequest, *, request_id: str | None = None
) -> OptimizationResult:
    """Build the canonical versioned advisory Optimization handoff.

    Returns:
        Standard response containing raw advisory handoff evidence.
    """
    return _build_optimization_handoff(request, request_id=request_id)


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
