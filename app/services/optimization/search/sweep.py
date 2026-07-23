"""Bounded sequential candidate-search orchestration."""

from __future__ import annotations

import hashlib
import time
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

from app.services.optimization.errors import OptimizationError
from app.services.optimization.execution import (
    BacktestExecutionAdapter,
    BacktestExecutionRequest,
    execute_candidate,
)
from app.services.optimization.parameters import candidate_hash, parameter_space_hash
from app.services.optimization.scoring import calculate_candidate_score, rank_candidates
from app.services.optimization.search.contracts import (
    CandidateResult,
    CandidateState,
    SearchMethod,
    SearchRequest,
    SearchSummary,
)
from app.services.optimization.search.grid import iter_grid_candidates
from app.services.optimization.search.random import sample_random_candidates
from app.utils import canonical_json, generate_id, logger

if TYPE_CHECKING:
    from app.services.optimization.parameters import ParameterValue
    from app.services.optimization.scoring import CandidateScore

type CheckpointCallback = Callable[[int, CandidateResult], None]


def _request_hash(request: SearchRequest) -> str:
    """Hash deterministic search material excluding trace identifiers.

    Args:
        request: Search request.

    Returns:
        Lowercase SHA-256 request digest.
    """
    logger.debug("Hashing Optimization search request")
    payload = request.model_dump(mode="json")
    payload["enabled_objectives"] = sorted(payload["enabled_objectives"])
    for field in ("request_id", "workflow_id", "correlation_id"):
        payload.pop(field)
    return hashlib.sha256(canonical_json(payload).encode()).hexdigest()


def _candidates(request: SearchRequest) -> Sequence[dict[str, ParameterValue]]:
    """Generate candidates for the selected search method.

    Args:
        request: Search request.

    Returns:
        Ordered candidate mappings.

    Raises:
        ValueError: If method-specific request evidence is incomplete.
    """
    logger.debug("Selecting Optimization search candidate generator")
    if request.method is SearchMethod.GRID:
        return tuple(
            iter_grid_candidates(
                request.space,
                max_candidates=request.max_candidates,
                max_expansion=request.max_parameter_space_expansion,
                max_constraints=request.max_constraint_count,
            )
        )
    if request.seed is None or request.candidate_count is None:
        raise ValueError("random search request is incomplete")
    return sample_random_candidates(
        request.space,
        candidate_count=request.candidate_count,
        seed=request.seed,
        max_expansion=request.max_parameter_space_expansion,
        max_constraints=request.max_constraint_count,
    )


def _deterministic_execution_id(prefix: str, parent_id: str, index: int) -> str:
    """Generate a deterministic UUIDv4-style trace ID.

    Args:
        prefix: Target prefix (e.g. 'req').
        parent_id: Parent trace ID.
        index: Candidate index.

    Returns:
        Deterministic, valid trace ID.
    """
    seed_str = f"{parent_id}-{index}"
    h = hashlib.sha256(seed_str.encode("utf-8")).hexdigest()
    part1 = h[:8]
    part2 = h[8:12]
    part3 = "4" + h[13:16]
    variant_char = h[16]
    if variant_char not in "89ab":
        variant_char = "89ab"[int(variant_char, 16) % 4]
    part4 = variant_char + h[17:20]
    part5 = h[20:32]
    return f"{prefix}-{part1}-{part2}-{part3}-{part4}-{part5}"


def run_bounded_search(
    request: SearchRequest,
    adapter: BacktestExecutionAdapter,
    *,
    deterministic_only: bool = True,
    checkpoint: CheckpointCallback | None = None,
) -> SearchSummary:
    """Run one bounded sequential search and retain candidate failures.

    Args:
        request: Validated bounded search request.
        adapter: Compatible deterministic execution adapter.
        deterministic_only: Whether non-deterministic execution is forbidden.
        checkpoint: Optional callback after every completed candidate.

    Returns:
        Completed deterministic search summary.

    Raises:
        OptimizationError: If a terminal cap or adapter failure occurs.
        ValueError: If parameter generation is invalid.
    """
    logger.info("Running bounded sequential Optimization search")
    started = time.monotonic()
    request_digest = _request_hash(request)
    search_id = f"search-{request_digest}"
    space_digest = parameter_space_hash(request.space)
    results: list[CandidateResult] = []
    try:
        candidates = _candidates(request)
    except ValueError as error:
        logger.bind(
            event="optimization.validation_failure",
            result="validation_failed",
            request_id=generate_id("req"),
            workflow_id=request.workflow_id,
            correlation_id=request.correlation_id,
            error_type=type(error).__name__,
        ).warning("Rejected invalid Optimization search candidate space")
        raise
    for index, parameters in enumerate(candidates):
        elapsed_seconds = time.monotonic() - started
        if elapsed_seconds > request.max_runtime_seconds:
            logger.bind(
                event="optimization.cap_rejection",
                result="cap_rejected",
                request_id=request.request_id,
                workflow_id=request.workflow_id,
                correlation_id=request.correlation_id,
                limit_name="max_runtime_seconds",
                duration_ms=round(elapsed_seconds * 1000, 3),
                candidate_count=len(results),
            ).warning("Rejected Optimization search exceeding runtime cap")
            raise OptimizationError("OPT_LIMIT_EXCEEDED", "SEARCH_RUNTIME_EXCEEDED")
        context = request.execution_context
        identity = candidate_hash(
            strategy_hash=context.strategy_config_hash,
            data_hash=context.data_hash,
            cost_model_hash=context.cost_model_hash,
            realism_hash=context.realism_hash,
            objective_hash=context.objective_hash,
            engine_type=context.engine_type,
            engine_version=context.engine_version,
            module_version=context.module_version,
            space_hash=space_digest,
            executable_parameters=parameters,
        )
        execution_request = BacktestExecutionRequest(
            candidate_hash=identity,
            executable_parameters=parameters,
            seed=(request.seed or 0) + index,
            request_id=_deterministic_execution_id("req", request.request_id, index),
            workflow_id=request.workflow_id,
            correlation_id=request.correlation_id,
            context=context,
        )
        try:
            measured = execute_candidate(
                execution_request,
                adapter,
                deterministic_only=deterministic_only,
            )
            score = calculate_candidate_score(
                measured.analytics_report,
                candidate_hash=identity,
                objective=request.objective,
                enabled_objectives=request.enabled_objectives,
            )
            result = CandidateResult(
                candidate_hash=identity,
                executable_parameters=parameters,
                state=CandidateState.ACCEPTED,
                score=score,
                evidence={
                    "simulation_run_id": measured.simulation_run_id,
                    "analytics_report_id": measured.analytics_report.report_id,
                },
            )
        except OptimizationError as error:
            if error.code != "OPT_EXECUTION_FAILED":
                raise
            logger.bind(
                event="optimization.candidate_failure",
                result="candidate_failed",
                request_id=request.request_id,
                workflow_id=request.workflow_id,
                correlation_id=request.correlation_id,
                candidate_hash=identity,
                reason_code=error.detail,
            ).warning("Recorded controlled Optimization candidate failure")
            result = CandidateResult(
                candidate_hash=identity,
                executable_parameters=parameters,
                state=CandidateState.FAILED,
                reason_code=error.detail,
            )
        results.append(result)
        if checkpoint is not None:
            checkpoint(index + 1, result)
    ranked = rank_candidates(
        tuple(item.score for item in results if item.score is not None)
    )
    runtime_ms = (time.monotonic() - started) * 1000
    warnings = () if ranked else ("no_successful_candidate",)
    logger.bind(
        event="optimization.search_completed",
        result="success",
        request_id=request.request_id,
        workflow_id=request.workflow_id,
        correlation_id=request.correlation_id,
        duration_ms=round(runtime_ms, 3),
        candidate_count=len(results),
        accepted_candidate_count=sum(
            item.state is CandidateState.ACCEPTED for item in results
        ),
        failed_candidate_count=sum(
            item.state is CandidateState.FAILED for item in results
        ),
    ).info("Completed bounded Optimization search")
    return SearchSummary(
        search_id=search_id,
        request_hash=request_digest,
        method=request.method,
        objective=request.objective,
        candidates=tuple(results),
        best_candidate_hash=ranked[0].candidate_hash if ranked else None,
        runtime_ms=runtime_ms,
        warnings=warnings,
    )


def select_top_candidates(
    summary: SearchSummary, limit: int
) -> tuple[CandidateResult, ...]:
    """Return the first N accepted candidates in canonical ranked order.

    Args:
        summary: Completed deterministic search evidence.
        limit: Positive maximum returned candidates.

    Returns:
        Accepted candidates ordered by the canonical score ranking.

    Raises:
        ValueError: If limit is not positive.
    """
    logger.info("Selecting top Optimization search candidates")
    if limit <= 0:
        raise ValueError("top-candidate limit must be positive")
    accepted = {
        item.candidate_hash: item
        for item in summary.candidates
        if item.state is CandidateState.ACCEPTED and item.score is not None
    }
    scores: list[CandidateScore] = []
    for item in accepted.values():
        if item.score is not None:
            scores.append(item.score)
    ranked = rank_candidates(scores)
    return tuple(accepted[item.candidate_hash] for item in ranked[:limit])


__all__ = ["CheckpointCallback", "run_bounded_search", "select_top_candidates"]
