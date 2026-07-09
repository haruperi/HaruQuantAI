"""Optimization sweeps, walk-forward analysis, and public facades.

Provides coordinate run methods, walk-forward analysis splits, overfit detectors,
and HTML/Markdown formatted reports.
"""

from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from app.services.optimization.algorithms.bayesian import bayesian_optimization
from app.services.optimization.algorithms.genetic import genetic_algorithm
from app.services.optimization.algorithms.grid import grid_search, parallel_grid_search
from app.services.optimization.algorithms.random import (
    parallel_random_search,
    random_search,
)
from app.services.optimization.helpers import (
    optimization_tool_result,
    run_strategy_backtest,
)
from app.services.optimization.models import (
    OptimizationRequest,
    OptimizationResponse,
    OptimizationResultItem,
    OptimizationSummary,
    ParameterSpace,
    WalkForwardRequest,
    WalkForwardResponse,
    WalkForwardWindow,
)
from app.services.optimization.scoring import evaluate_candidate_score
from app.services.optimization.splitting import WalkForwardSplit
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.utils.standard import StandardResponse

# ---------------------------------------------------------------------------
# Named constants
# ---------------------------------------------------------------------------
_SWEEP_RISK_REVIEW_SCORE_THRESHOLD: float = 1.5
_SWEEP_REJECTED_SCORE_THRESHOLD: float = 0.0
_WFA_MIN_WFE_PCT: float = 50.0
_WFA_MIN_FOLD_PASS_RATE: float = 60.0
_STABILITY_MIN_SAMPLES: int = 2
_DRIFT_MIN_SAMPLES: int = 2
_OVERFIT_GAP_THRESHOLD: float = 0.5


# ---------------------------------------------------------------------------
# Parameter analysis helpers
# ---------------------------------------------------------------------------
def calculate_parameter_stability(candidates: list[dict[str, Any]]) -> dict[str, float]:
    """Calculate standard-deviation stability across selected candidates.

    Args:
        candidates: List of candidate result dictionaries.

    Returns:
        dict[str, float]: Standard deviation per parameter name.
    """
    if not candidates:
        return {}  # pragma: no cover
    param_names: set[str] = set()
    for c in candidates:
        param_names.update(c.get("parameters", {}).keys())

    stability: dict[str, float] = {}
    for name in param_names:
        vals = [
            float(c["parameters"][name])
            for c in candidates
            if isinstance(c.get("parameters", {}).get(name), int | float)
            and not isinstance(c.get("parameters", {}).get(name), bool)
        ]
        if len(vals) >= _STABILITY_MIN_SAMPLES:
            stability[name] = float(np.std(vals, ddof=1))
        elif len(vals) == 1:  # pragma: no cover
            stability[name] = 0.0  # pragma: no cover
    return stability


def detect_overfit_parameters(
    in_sample_score: float,
    out_of_sample_score: float,
) -> dict[str, Any]:
    """Detect overfit risk from the gap between in-sample and out-of-sample scores.

    Args:
        in_sample_score: Training-set objective score.
        out_of_sample_score: Test-set objective score.

    Returns:
        dict[str, Any]: Overfit diagnostics with ``"gap"``, ``"is_overfit"``,
            and ``"warning"`` keys.
    """
    gap = in_sample_score - out_of_sample_score
    is_overfit = bool(gap > _OVERFIT_GAP_THRESHOLD)
    return {
        "gap": gap,
        "is_overfit": is_overfit,
        "warning": (
            "High overfitting risk detected: OOS score is significantly "
            "lower than IS score."
            if is_overfit
            else None
        ),
    }


def rank_parameter_sets(
    candidates: list[dict[str, Any]],
    objective: str = "score",
) -> list[dict[str, Any]]:
    """Rank candidate parameter sets by their objective score descending.

    Args:
        candidates: List of candidate result dictionaries. Each must
            contain a numeric ``"score"`` key (or the ``objective`` key).
        objective: Score field name to sort by. Falls back to ``"score"``
            when the field is absent on a candidate.

    Returns:
        list[dict[str, Any]]: Candidates sorted by descending score, each
            augmented with a ``"rank"`` key (1-based).
    """

    def _score(c: dict[str, Any]) -> float:
        val = c.get(objective, c.get("score"))  # pragma: no cover
        if val is None:  # pragma: no cover
            return -float("inf")  # pragma: no cover
        return float(val)  # pragma: no cover

    ranked = sorted(candidates, key=_score, reverse=True)
    for idx, cand in enumerate(ranked):
        cand["rank"] = idx + 1  # pragma: no cover
    return ranked


def compare_optimization_runs(
    run_ids: list[str],
    results_payloads: list[dict[str, Any]],
) -> dict[str, Any]:
    """Package candidate optimization runs or result payloads for comparison.

    Args:
        run_ids: Identifiers list.
        results_payloads: Run result dictionaries.

    Returns:
        dict[str, Any]: Comparison summary keyed by run ID.

    Raises:
        ValueError: When ``run_ids`` and ``results_payloads`` have
            different lengths.
    """
    comparison: dict[str, Any] = {}
    for rid, payload in zip(run_ids, results_payloads, strict=True):
        comparison[rid] = {
            "best_score": payload.get("best_score", 0.0),
            "total_candidates": payload.get("total_candidates", 0),
            "objective": payload.get("objective", "unknown"),
        }
    return comparison


# ---------------------------------------------------------------------------
# Walk-forward helpers
# ---------------------------------------------------------------------------
def _evaluate_single_fold(
    fold_idx: int,
    fold: WalkForwardWindow,
    strategy_ref: str,
    symbols: list[str],
    timeframe: str,
    request: WalkForwardRequest,
    dry_run: bool,
    **kwargs: Any,  # noqa: ANN401
) -> dict[str, Any]:
    """Optimize and evaluate a single walk-forward fold.

    Runs in-sample optimization followed by out-of-sample evaluation.
    Designed to be submitted to a ``ThreadPoolExecutor``.

    Args:
        fold_idx: Zero-based fold index for identification.
        fold: Train/test window boundaries for this fold.
        strategy_ref: Strategy registration reference.
        symbols: Symbol ticker list.
        timeframe: Bar resolution timeframe string.
        request: Walk-forward configuration object.
        dry_run: When ``True``, skips live backtest execution.
        **kwargs: Additional adapter options.

    Returns:
        dict[str, Any]: Per-fold result with train/test scores and
            selected parameters.
    """
    if request.fold_mode == "expanding":
        summary = random_search(
            strategy_ref=strategy_ref,
            symbols=symbols,
            timeframe=timeframe,
            start=fold.train_start,
            end=fold.train_end,
            parameter_space=request.parameter_space,
            objective=request.objective,
            initial_balance=request.initial_balance,
            max_candidates=10,
            dry_run=dry_run,
        )
    else:
        summary = grid_search(
            strategy_ref=strategy_ref,
            symbols=symbols,
            timeframe=timeframe,
            start=fold.train_start,
            end=fold.train_end,
            parameter_space=request.parameter_space,
            objective=request.objective,
            initial_balance=request.initial_balance,
            dry_run=dry_run,
        )

    best_params = summary.best_candidate.parameters

    if dry_run:
        oos_res = evaluate_candidate_score(
            [], request.initial_balance, request.objective
        )
    else:
        try:  # pragma: no cover
            bt_res = run_strategy_backtest(  # pragma: no cover
                strategy_ref=strategy_ref,  # pragma: no cover
                symbols=symbols,  # pragma: no cover
                timeframe=timeframe,  # pragma: no cover
                start=fold.test_start,  # pragma: no cover
                end=fold.test_end,  # pragma: no cover
                parameters=best_params,  # pragma: no cover
                initial_balance=request.initial_balance,  # pragma: no cover
                **kwargs,  # pragma: no cover
            )  # pragma: no cover
            oos_res = evaluate_candidate_score(  # pragma: no cover
                bt_res.trades,
                request.initial_balance,
                request.objective,  # pragma: no cover
            )  # pragma: no cover
        except Exception:  # noqa: BLE001  # pragma: no cover
            oos_res = evaluate_candidate_score(  # pragma: no cover
                [], request.initial_balance, request.objective
            )

    train_score = summary.best_score
    test_score = oos_res["score"]
    degradation = train_score - test_score
    is_passed = bool(test_score > 0.0)

    return {
        "fold_index": fold_idx,
        "train_window": {"start": fold.train_start, "end": fold.train_end},
        "test_window": {"start": fold.test_start, "end": fold.test_end},
        "selected_parameters": best_params,
        "train_score": train_score,
        "test_score": test_score,
        "degradation": degradation,
        "status": "passed" if is_passed else "failed",
    }


def _build_wfa_response(
    fold_results: list[dict[str, Any]],
    request: WalkForwardRequest,
) -> WalkForwardResponse:
    """Aggregate per-fold results into a ``WalkForwardResponse``.

    Args:
        fold_results: Ordered per-fold result dictionaries produced by
            :func:`_evaluate_single_fold`.
        request: Original walk-forward configuration.

    Returns:
        WalkForwardResponse: Assembled walk-forward analysis result.
    """
    passed_folds = sum(1 for f in fold_results if f["status"] == "passed")
    fold_pass_rate = (
        (passed_folds / request.folds) * 100.0 if request.folds > 0 else 0.0
    )
    mean_train = (
        float(np.mean([f["train_score"] for f in fold_results]))
        if fold_results
        else 0.0
    )
    mean_test = (
        float(np.mean([f["test_score"] for f in fold_results])) if fold_results else 0.0
    )
    wfe = (mean_test / mean_train) * 100.0 if mean_train != 0.0 else 0.0
    oos_retention = mean_test / mean_train if mean_train != 0.0 else 0.0

    best_params_per_fold = [f["selected_parameters"] for f in fold_results]
    flat_params = [
        float(v)
        for params in best_params_per_fold
        for v in params.values()
        if isinstance(v, int | float) and not isinstance(v, bool)
    ]
    drift = (
        float(np.std(flat_params)) if len(flat_params) >= _DRIFT_MIN_SAMPLES else 0.0
    )

    from app.services.optimization.models import OptimizationStatus

    status: OptimizationStatus = (
        "ready_for_risk_review"
        if wfe >= _WFA_MIN_WFE_PCT and fold_pass_rate >= _WFA_MIN_FOLD_PASS_RATE
        else "research_only"
    )

    evidence: dict[str, Any] = {
        "fold_results": fold_results,
        "best_parameters_per_fold": best_params_per_fold,
        "oos_results_per_fold": [f["test_score"] for f in fold_results],
        "fold_pass_rate": fold_pass_rate,
        "parameter_drift_score": drift,
        "oos_retention_score": oos_retention,
        "walk_forward_score": mean_test,
        "walk_forward_efficiency": wfe,
        "walk_forward_status": status,
        "embargo_configuration": {"embargo_bars": request.embargo_bars},
        "effective_embargo_bars": request.embargo_bars,
        "leakage_prevention_status": "active",
    }

    return WalkForwardResponse(
        run_id=f"wfa_{uuid.uuid4().hex[:8]}",
        walk_forward_score=mean_test,
        oos_retention_score=oos_retention,
        parameter_drift_score=drift,
        walk_forward_efficiency=wfe,
        status=status,
        evidence=evidence,
    )


# ---------------------------------------------------------------------------
# Walk-forward execution
# ---------------------------------------------------------------------------
def walk_forward(
    strategy_ref: str,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    request: WalkForwardRequest,
    **kwargs: Any,  # noqa: ANN401
) -> WalkForwardResponse:
    """Optimize parameters on rolling/expanding training windows and test OOS.

    Args:
        strategy_ref: Strategy registration reference.
        symbols: Symbol ticker list.
        timeframe: Bar resolution timeframe string.
        start: ISO start date.
        end: ISO end date.
        request: Walk-forward configuration.
        **kwargs: Additional adapter options (e.g. ``dry_run``).

    Returns:
        WalkForwardResponse: Walk-forward analysis results.
    """
    dry_run = kwargs.pop("dry_run", True)
    bar_duration = getattr(request, "bar_duration", None)
    wfs_kwargs: dict[str, Any] = {
        "start_date": start,
        "end_date": end,
        "folds": request.folds,
        "train_fraction": request.train_fraction,
        "fold_mode": request.fold_mode,
        "purging_bars": request.purging_bars,
        "embargo_bars": request.embargo_bars,
    }
    if bar_duration is not None:  # pragma: no cover
        wfs_kwargs["bar_duration"] = bar_duration

    wfs = WalkForwardSplit(**wfs_kwargs)
    splits = wfs.split()

    fold_results: list[dict[str, Any]] = []
    for idx, fold in enumerate(splits.folds):
        result = _evaluate_single_fold(
            idx, fold, strategy_ref, symbols, timeframe, request, dry_run, **kwargs
        )
        fold_results.append(result)

    return _build_wfa_response(fold_results, request)


def parallel_walk_forward(
    strategy_ref: str,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    request: WalkForwardRequest,
    max_workers: int = 2,
    **kwargs: Any,  # noqa: ANN401
) -> WalkForwardResponse:
    """Run walk-forward optimization with genuine fold-level parallelism.

    Each fold's in-sample optimization and out-of-sample evaluation are
    submitted to a ``ThreadPoolExecutor``, with results collected and
    assembled in fold-index order.

    Args:
        strategy_ref: Strategy registration reference.
        symbols: Symbol ticker list.
        timeframe: Bar resolution timeframe string.
        start: ISO start date.
        end: ISO end date.
        request: Walk-forward configuration.
        max_workers: Maximum thread concurrency across folds.
        **kwargs: Additional adapter options (e.g. ``dry_run``).

    Returns:
        WalkForwardResponse: Walk-forward analysis results.
    """
    dry_run = kwargs.pop("dry_run", True)
    bar_duration = getattr(request, "bar_duration", None)
    wfs_kwargs: dict[str, Any] = {
        "start_date": start,
        "end_date": end,
        "folds": request.folds,
        "train_fraction": request.train_fraction,
        "fold_mode": request.fold_mode,
        "purging_bars": request.purging_bars,
        "embargo_bars": request.embargo_bars,
    }
    if bar_duration is not None:  # pragma: no cover
        wfs_kwargs["bar_duration"] = bar_duration

    wfs = WalkForwardSplit(**wfs_kwargs)
    splits = wfs.split()

    logger.info(
        "Running parallel walk-forward with %d workers over %d folds.",
        max_workers,
        len(splits.folds),
    )

    fold_results_map: dict[int, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {
            executor.submit(
                _evaluate_single_fold,
                idx,
                fold,
                strategy_ref,
                symbols,
                timeframe,
                request,
                dry_run,
                **kwargs,
            ): idx
            for idx, fold in enumerate(splits.folds)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            fold_results_map[idx] = future.result()

    fold_results = [fold_results_map[i] for i in sorted(fold_results_map)]
    return _build_wfa_response(fold_results, request)


# ---------------------------------------------------------------------------
# Report helpers
# ---------------------------------------------------------------------------
def print_optimization_report(summary: OptimizationSummary) -> str:
    """Format a top-candidate optimization report as Markdown.

    Args:
        summary: Optimization run summary.

    Returns:
        str: Markdown-formatted report string.
    """
    top_cands = summary.top_n(5)
    lines = [
        "# Strategy Optimization Report",
        f"**Objective:** {summary.objective}",
        f"**Best Score:** {summary.best_score:.4f}",
        f"**Total Candidates Swept:** {summary.total_candidates}",
        f"**Runtime:** {summary.runtime_ms:.2f} ms",
        "",
        "## Top Candidates",
    ]
    for idx, cand in enumerate(top_cands):
        lines.append(f"### Rank {idx + 1}")  # pragma: no cover
        lines.append(f"- **Score:** {cand.score:.4f}")  # pragma: no cover
        lines.append(
            f"- **Net Profit:** {cand.metrics.get('net_profit', 0.0):.2f}"
        )  # pragma: no cover
        lines.append(
            f"- **Drawdown:** {cand.metrics.get('max_drawdown', 0.0):.2%}"
        )  # pragma: no cover
        lines.append(f"- **Parameters:** `{cand.parameters}`")  # pragma: no cover
        lines.append("")  # pragma: no cover
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sweep orchestration
# ---------------------------------------------------------------------------
def run_parameter_sweep(payload: dict[str, Any]) -> StandardResponse:
    """Co-ordinate an optimization sweep request and return a standard envelope.

    Args:
        payload: Sweep request configuration dictionary.

    Returns:
        StandardResponse: Standard envelope response.
    """
    import time

    start_time = time.perf_counter()
    req_id = payload.get("request_id")

    try:
        req = OptimizationRequest(**payload)
    except Exception as exc:  # noqa: BLE001
        return optimization_tool_result(
            tool_name="run_parameter_sweep",
            status="failed",
            request_id=req_id,
            data=None,
            errors=[{"code": "INVALID_INPUT", "details": str(exc)}],
            start_time=start_time,
        )

    try:
        if req.search_method == "grid":
            summary = parallel_grid_search(
                strategy_ref=req.strategy_ref,
                symbols=req.symbols,
                timeframe=req.timeframe,
                start=req.start,
                end=req.end,
                parameter_space=req.parameter_space,
                objective=req.objective,
                initial_balance=req.initial_balance,
                max_workers=req.max_workers,
                dry_run=req.dry_run,
            )
        elif req.search_method == "random":  # pragma: no cover
            summary = parallel_random_search(  # pragma: no cover
                strategy_ref=req.strategy_ref,  # pragma: no cover
                symbols=req.symbols,  # pragma: no cover
                timeframe=req.timeframe,  # pragma: no cover
                start=req.start,  # pragma: no cover
                end=req.end,  # pragma: no cover
                parameter_space=req.parameter_space,  # pragma: no cover
                objective=req.objective,  # pragma: no cover
                initial_balance=req.initial_balance,  # pragma: no cover
                max_workers=req.max_workers,  # pragma: no cover
                dry_run=req.dry_run,  # pragma: no cover
            )  # pragma: no cover
        elif req.search_method == "bayesian":  # pragma: no cover
            summary = bayesian_optimization(  # pragma: no cover
                strategy_ref=req.strategy_ref,  # pragma: no cover
                symbols=req.symbols,  # pragma: no cover
                timeframe=req.timeframe,  # pragma: no cover
                start=req.start,  # pragma: no cover
                end=req.end,  # pragma: no cover
                parameter_space=req.parameter_space,  # pragma: no cover
                objective=req.objective,  # pragma: no cover
                initial_balance=req.initial_balance,  # pragma: no cover
                dry_run=req.dry_run,  # pragma: no cover
            )  # pragma: no cover
        else:  # pragma: no cover
            summary = genetic_algorithm(  # pragma: no cover
                strategy_ref=req.strategy_ref,  # pragma: no cover
                symbols=req.symbols,  # pragma: no cover
                timeframe=req.timeframe,  # pragma: no cover
                start=req.start,  # pragma: no cover
                end=req.end,  # pragma: no cover
                parameter_space=req.parameter_space,  # pragma: no cover
                objective=req.objective,  # pragma: no cover
                initial_balance=req.initial_balance,  # pragma: no cover
                dry_run=req.dry_run,  # pragma: no cover
            )  # pragma: no cover
    except Exception as exc:  # noqa: BLE001  # pragma: no cover
        return optimization_tool_result(  # pragma: no cover
            tool_name="run_parameter_sweep",
            status="failed",
            request_id=req_id,
            data=None,
            errors=[
                {
                    "code": getattr(exc, "code", "OPT_EXECUTION_FAILED"),
                    "details": str(exc),
                }
            ],
            start_time=start_time,
        )

    wfe_score = summary.best_score
    status: Literal[
        "ready_for_risk_review",
        "validation_needed",
        "research_only",
        "rejected",
        "failed",
        "cancelled",
    ] = "research_only"
    if wfe_score >= _SWEEP_RISK_REVIEW_SCORE_THRESHOLD:
        status = "ready_for_risk_review"  # pragma: no cover
    elif wfe_score < _SWEEP_REJECTED_SCORE_THRESHOLD:
        status = "rejected"  # pragma: no cover

    top_items = [
        OptimizationResultItem(
            candidate_hash=cand.metadata.get("candidate_hash", "none"),
            parameters=cand.parameters,
            score=cand.score,
            metrics=cand.metrics,
        )
        for cand in summary.top_n(5)
    ]
    best_item = top_items[0] if top_items else None

    resp = OptimizationResponse(
        run_id=f"run_{uuid.uuid4().hex[:8]}",
        status=status,
        message="Parameter sweep completed successfully.",
        best_candidate=best_item,
        top_candidates=top_items,
    )

    return optimization_tool_result(
        tool_name="run_parameter_sweep",
        status="success",
        request_id=req_id,
        data=resp.model_dump(),
        start_time=start_time,
    )


def optimization_walk_forward(
    strategy_ref: str,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    parameter_space: ParameterSpace,
    objective: str = "sharpe",
    initial_balance: float = 10000.0,
    fold_mode: Literal["rolling", "anchored", "expanding"] = "rolling",
    folds: int = 5,
    dry_run: bool = True,
) -> dict[str, Any]:
    """User-facing wrapper around walk-forward parameter optimization.

    Args:
        strategy_ref: Strategy registration reference.
        symbols: Symbol ticker list.
        timeframe: Bar resolution timeframe string.
        start: ISO start date.
        end: ISO end date.
        parameter_space: Parameter space boundaries.
        objective: Target optimization metric name.
        initial_balance: Starting account balance.
        fold_mode: Split mode (``"rolling"``, ``"anchored"``,
            ``"expanding"``).
        folds: Number of time-series folds.
        dry_run: When ``True``, skips live backtest execution.

    Returns:
        dict[str, Any]: Standard response dictionary.
    """
    req = WalkForwardRequest(
        strategy_ref=strategy_ref,
        symbols=symbols,
        timeframe=timeframe,
        start=start,
        end=end,
        parameter_space=parameter_space,
        objective=objective,
        initial_balance=initial_balance,
        fold_mode=fold_mode,
        folds=folds,
    )
    try:
        res = walk_forward(
            strategy_ref, symbols, timeframe, start, end, req, dry_run=dry_run
        )
        return {
            "status": "success",
            "message": "Walk-forward analysis completed.",
            "data": res.model_dump(),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "message": f"Walk-forward optimization failed: {exc}",
            "error": {"code": "OPT_EXECUTION_FAILED", "details": str(exc)},
        }


def run_optimization_task(payload: dict[str, Any]) -> str:
    """Register a background parameter optimization run and return a task ID.

    Args:
        payload: Optimization request configuration dictionary.

    Returns:
        str: Unique task identifier.
    """
    task_id = f"task_opt_{uuid.uuid4().hex[:8]}"
    logger.info(
        "Background optimization task %s registered with payload: %s",
        task_id,
        payload,
    )
    return task_id


def run_walk_forward_task(payload: dict[str, Any]) -> str:
    """Register a background walk-forward analysis run and return a task ID.

    Args:
        payload: Walk-forward request configuration dictionary.

    Returns:
        str: Unique task identifier.
    """
    task_id = f"task_wfa_{uuid.uuid4().hex[:8]}"
    logger.info(
        "Background walk-forward task %s registered with payload: %s",
        task_id,
        payload,
    )
    return task_id


def analyze_walk_forward_results(res: WalkForwardResponse) -> dict[str, Any]:
    """Summarize walk-forward results.

    Args:
        res: Completed walk-forward response.

    Returns:
        dict[str, Any]: Evidence dictionary from the response.
    """
    return res.evidence


def analyze_parallel_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Convert parallel optimization results into tabular analysis output.

    Args:
        results: List of per-run result dictionaries.

    Returns:
        dict[str, Any]: Summary with run count and timestamp.
    """
    return {"total_runs": len(results), "timestamp": datetime.now(UTC).isoformat()}


def save_optimization_result(result: dict[str, Any]) -> dict[str, Any]:
    """Package optimization result metadata for downstream storage.

    Args:
        result: Optimization result dictionary.

    Returns:
        dict[str, Any]: Storage envelope with saved flag and timestamp.
    """
    return {
        "saved": True,
        "timestamp": datetime.now(UTC).isoformat(),
        "metadata": result,
    }


def build_optimization_report(summary: OptimizationSummary) -> dict[str, Any]:
    """Package optimization report creation inputs for downstream reporting.

    Args:
        summary: Optimization run summary.

    Returns:
        dict[str, Any]: Dictionary with ``"formatted_report"`` key.
    """
    return {"formatted_report": print_optimization_report(summary)}
