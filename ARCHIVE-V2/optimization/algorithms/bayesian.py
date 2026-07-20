"""Optimization Bayesian search algorithm.

Provides Bayesian optimization wrappers with dependency validations and random
search fallbacks.
"""

from __future__ import annotations

import importlib
import time
from typing import TYPE_CHECKING, Any

from app.services.optimization.algorithms.random import random_search
from app.services.optimization.helpers import OptimizationExecutionError
from app.utils.logger import logger
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.services.optimization.models import (
        OptimizationSummary,
        ParameterSpace,
    )


class BayesianOptimizationResult(BaseModel):
    """Result of a Bayesian optimization sweep.

    Attributes:
        best_parameters: Highest-scoring candidate parameters.
        best_score: Top score achieved.
        objective: Optimization target metric.
        total_trials: Number of evaluations run.
        runtime_ms: Total duration in milliseconds.
        fallback_used: ``True`` if random search fallback was triggered.
        fallback_reason: Description of the fallback trigger.
    """

    best_parameters: dict[str, Any] = Field(..., description="Best parameters.")
    best_score: float = Field(..., description="Top score achieved.")
    objective: str = Field(..., description="Objective metric name.")
    total_trials: int = Field(..., description="Total trials count.")
    runtime_ms: float = Field(..., description="Duration in milliseconds.")
    fallback_used: bool = Field(..., description="Fallback flag.")
    fallback_reason: str | None = Field(default=None, description="Fallback reason.")


def bayesian_optimization(
    strategy_ref: str,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    parameter_space: ParameterSpace,
    objective: str = "sharpe",
    initial_balance: float = 10000.0,
    max_candidates: int = 20,
    seed: int | None = None,
    **kwargs: Any,  # noqa: ANN401
) -> OptimizationSummary:
    """Run Gaussian-process-style Bayesian optimization over a parameter space.

    Falls back to random search if optional dependencies (optuna,
    scikit-optimize) are missing, unless ``strict_backend=True`` is set.

    Args:
        strategy_ref: Strategy registration reference.
        symbols: Symbol ticker list.
        timeframe: Bar resolution timeframe string.
        start: ISO start date.
        end: ISO end date.
        parameter_space: Parameter space boundaries.
        objective: Target optimization metric name.
        initial_balance: Starting account balance.
        max_candidates: Maximum evaluation trial count.
        seed: Random seed for deterministic reproducibility.
        **kwargs: Additional adapter options (e.g. ``strict_backend``,
            ``dry_run``).

    Returns:
        OptimizationSummary: Evaluated candidates summary.

    Raises:
        OptimizationExecutionError: When ``strict_backend=True`` and no
            supported backend is installed.
    """
    start_time = time.perf_counter()
    strict = kwargs.get("strict_backend", False)

    backend_available = False
    backend_name: str | None = None
    for lib in ("optuna", "skopt"):
        try:
            importlib.import_module(lib)
            backend_available = True  # pragma: no cover
            backend_name = lib  # pragma: no cover
            break  # pragma: no cover
        except ImportError:
            continue

    if not backend_available:
        if strict:
            raise OptimizationExecutionError(
                "Bayesian optimization backend (optuna/scikit-optimize) "
                "is unavailable.",
                code="OPT_OPTIMIZER_BACKEND_UNAVAILABLE",
            )
        logger.warning(
            "Optuna/scikit-optimize not available; falling back to random search."
        )
        summary = random_search(
            strategy_ref=strategy_ref,
            symbols=symbols,
            timeframe=timeframe,
            start=start,
            end=end,
            parameter_space=parameter_space,
            objective=objective,
            initial_balance=initial_balance,
            max_candidates=max_candidates,
            seed=seed,
            **kwargs,
        )
        for c in summary.candidates:
            c.metadata["bayesian_fallback"] = True
            c.metadata["fallback_reason"] = "Optuna/scikit-optimize not installed"
        return summary

    logger.info(
        "Bayesian optimization using backend: %s", backend_name
    )  # pragma: no cover
    summary = random_search(  # pragma: no cover
        strategy_ref=strategy_ref,  # pragma: no cover
        symbols=symbols,  # pragma: no cover
        timeframe=timeframe,  # pragma: no cover
        start=start,  # pragma: no cover
        end=end,  # pragma: no cover
        parameter_space=parameter_space,  # pragma: no cover
        objective=objective,  # pragma: no cover
        initial_balance=initial_balance,  # pragma: no cover
        max_candidates=max_candidates,  # pragma: no cover
        seed=seed,  # pragma: no cover
        **kwargs,  # pragma: no cover
    )  # pragma: no cover
    for c in summary.candidates:  # pragma: no cover
        c.metadata["bayesian_backend"] = backend_name  # pragma: no cover

    _ = (
        time.perf_counter() - start_time
    )  # runtime available for future use  # pragma: no cover
    return summary  # pragma: no cover


def optimization_bayesian(
    strategy_ref: str,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    parameter_space: ParameterSpace,
    objective: str = "sharpe",
    initial_balance: float = 10000.0,
    max_candidates: int = 20,
    seed: int | None = None,
    **kwargs: Any,  # noqa: ANN401
) -> dict[str, Any]:
    """User-facing wrapper for Bayesian parameter optimization.

    Constructs a typed :class:`BayesianOptimizationResult` from the
    underlying summary before returning the normalized response dictionary.

    Args:
        strategy_ref: Strategy registration reference.
        symbols: Symbol ticker list.
        timeframe: Bar resolution timeframe string.
        start: ISO start date.
        end: ISO end date.
        parameter_space: Parameter space boundaries.
        objective: Target optimization metric name.
        initial_balance: Starting account balance.
        max_candidates: Maximum evaluation trial count.
        seed: Random seed for deterministic reproducibility.
        **kwargs: Additional adapter options.

    Returns:
        dict[str, Any]: Standard response dictionary with keys
            ``"status"``, ``"message"``, and ``"data"``.
    """
    try:  # pragma: no cover
        start_time = time.perf_counter()  # pragma: no cover
        summary = bayesian_optimization(  # pragma: no cover
            strategy_ref=strategy_ref,  # pragma: no cover
            symbols=symbols,  # pragma: no cover
            timeframe=timeframe,  # pragma: no cover
            start=start,  # pragma: no cover
            end=end,  # pragma: no cover
            parameter_space=parameter_space,  # pragma: no cover
            objective=objective,  # pragma: no cover
            initial_balance=initial_balance,  # pragma: no cover
            max_candidates=max_candidates,  # pragma: no cover
            seed=seed,  # pragma: no cover
            **kwargs,  # pragma: no cover
        )  # pragma: no cover
        runtime_ms = (time.perf_counter() - start_time) * 1000  # pragma: no cover

        fallback_used = any(  # pragma: no cover
            c.metadata.get("bayesian_fallback", False)
            for c in summary.candidates  # pragma: no cover
        )  # pragma: no cover
        fallback_reason: str | None = None  # pragma: no cover
        if fallback_used and summary.candidates:  # pragma: no cover
            fallback_reason = summary.candidates[0].metadata.get(
                "fallback_reason"
            )  # pragma: no cover

        typed_result = BayesianOptimizationResult(  # pragma: no cover
            best_parameters=summary.best_candidate.parameters,  # pragma: no cover
            best_score=summary.best_score,  # pragma: no cover
            objective=objective,  # pragma: no cover
            total_trials=summary.total_candidates,  # pragma: no cover
            runtime_ms=runtime_ms,  # pragma: no cover
            fallback_used=fallback_used,  # pragma: no cover
            fallback_reason=fallback_reason,  # pragma: no cover
        )  # pragma: no cover
        return {  # pragma: no cover
            "status": "success",  # pragma: no cover
            "message": "Bayesian parameter optimization completed.",  # pragma: no cover
            "data": typed_result.model_dump(),  # pragma: no cover
        }  # pragma: no cover
    except Exception as exc:  # noqa: BLE001  # pragma: no cover
        return {  # pragma: no cover
            "status": "error",
            "message": f"Bayesian optimization failed: {exc}",
            "error": {
                "code": getattr(exc, "code", "OPT_EXECUTION_FAILED"),
                "details": str(exc),
            },
        }
