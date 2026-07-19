"""Walk-forward search and out-of-sample evaluation."""

from __future__ import annotations

from itertools import pairwise

from app.services.optimization.errors import OptimizationError
from app.services.optimization.execution import (
    BacktestExecutionAdapter,
    BacktestExecutionRequest,
    execute_candidate,
)
from app.services.optimization.scoring import (
    ObjectiveDirection,
    calculate_candidate_score,
)
from app.services.optimization.search import CandidateState, run_bounded_search
from app.services.optimization.validation.contracts import (
    WalkForwardFoldResult,
    WalkForwardRequest,
    WalkForwardResult,
)
from app.services.optimization.validation.splits import build_time_series_splits
from app.utils import derive_stable_id, logger


def _utility(value: float, direction: ObjectiveDirection) -> float:
    """Normalize an objective value to maximizing utility.

    Args:
        value: Finite objective value.
        direction: Explicit objective direction.

    Returns:
        Maximizing utility value.
    """
    logger.debug("Projecting walk-forward score utility")
    return value if direction is ObjectiveDirection.MAXIMIZE else -value


def run_walk_forward_validation(
    request: WalkForwardRequest,
    adapter: BacktestExecutionAdapter,
    *,
    deterministic_only: bool = True,
) -> WalkForwardResult:
    """Select in-sample candidates and measure them out of sample.

    Args:
        request: Validated walk-forward request.
        adapter: Compatible deterministic execution adapter.
        deterministic_only: Whether non-deterministic execution is forbidden.

    Returns:
        Fold-level and aggregate walk-forward evidence.

    Raises:
        OptimizationError: If a fold has no successful training candidate.
        ValueError: If split construction or score evidence is invalid.
    """
    logger.info("Running Optimization walk-forward validation")
    splits = build_time_series_splits(request)
    folds: list[WalkForwardFoldResult] = []
    for split in splits:
        train_context = request.search.execution_context.model_copy(
            update={"start": split.train_start, "end": split.train_end}
        )
        train_search = request.search.model_copy(
            update={
                "execution_context": train_context,
                "request_id": derive_stable_id(
                    "req", f"{request.search.request_id}:{split.fold_id}:train"
                ),
            }
        )
        summary = run_bounded_search(
            train_search,
            adapter,
            deterministic_only=deterministic_only,
        )
        selected = next(
            (
                item
                for item in summary.candidates
                if item.candidate_hash == summary.best_candidate_hash
                and item.state is CandidateState.ACCEPTED
            ),
            None,
        )
        if selected is None or selected.score is None:
            raise OptimizationError(
                "OPT_EXECUTION_FAILED",
                "WALK_FORWARD_TRAINING_FAILED",
            )
        test_context = request.search.execution_context.model_copy(
            update={"start": split.test_start, "end": split.test_end}
        )
        test_request = BacktestExecutionRequest(
            candidate_hash=selected.candidate_hash,
            executable_parameters=selected.executable_parameters,
            seed=request.search.seed or 0,
            request_id=derive_stable_id(
                "req", f"{request.search.request_id}:{split.fold_id}:test"
            ),
            workflow_id=request.search.workflow_id,
            correlation_id=request.search.correlation_id,
            context=test_context,
        )
        measured = execute_candidate(
            test_request,
            adapter,
            deterministic_only=deterministic_only,
        )
        out_of_sample = calculate_candidate_score(
            measured.analytics_report,
            candidate_hash=selected.candidate_hash,
            objective=request.search.objective,
            enabled_objectives=request.search.enabled_objectives,
        )
        degradation = None
        if selected.score.value is not None and out_of_sample.value is not None:
            train_utility = _utility(selected.score.value, selected.score.direction)
            test_utility = _utility(out_of_sample.value, out_of_sample.direction)
            degradation = (
                None
                if train_utility == 0
                else (train_utility - test_utility) / abs(train_utility)
            )
        folds.append(
            WalkForwardFoldResult(
                fold_id=split.fold_id,
                candidate_hash=selected.candidate_hash,
                selected_parameters=selected.executable_parameters,
                train_score=selected.score,
                out_of_sample_score=out_of_sample,
                degradation=degradation,
            )
        )
    successful = tuple(item for item in folds if item.out_of_sample_score.available)
    pass_rate = len(successful) / len(folds)
    changes = sum(
        left.selected_parameters != right.selected_parameters
        for left, right in pairwise(folds)
    )
    drift = 0.0 if len(folds) == 1 else changes / (len(folds) - 1)
    ratios = tuple(
        _utility(item.out_of_sample_score.value, item.out_of_sample_score.direction)
        / abs(_utility(item.train_score.value, item.train_score.direction))
        for item in successful
        if item.out_of_sample_score.value is not None
        and item.train_score.value is not None
        and item.train_score.value != 0
    )
    retention = sum(ratios) / len(ratios) if ratios else None
    train_total = sum(
        _utility(item.train_score.value, item.train_score.direction)
        for item in successful
        if item.train_score.value is not None
    )
    test_total = sum(
        _utility(item.out_of_sample_score.value, item.out_of_sample_score.direction)
        for item in successful
        if item.out_of_sample_score.value is not None
    )
    efficiency = None if train_total == 0 else test_total / abs(train_total)
    status = "completed" if len(folds) >= request.minimum_fold_count else "incomplete"
    return WalkForwardResult(
        splits=splits,
        folds=tuple(folds),
        fold_pass_rate=pass_rate,
        parameter_drift_score=drift,
        oos_retention_score=retention,
        walk_forward_efficiency=efficiency,
        status=status,
        warnings=() if status == "completed" else ("minimum_fold_count_not_met",),
    )


__all__ = ["run_walk_forward_validation"]
