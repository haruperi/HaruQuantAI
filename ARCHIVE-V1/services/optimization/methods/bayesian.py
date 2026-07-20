"""Bayesian Optimization.

Uses Gaussian Process-based optimization with Expected Improvement acquisition.
More efficient than random search, intelligently explores parameter space.

Classes and functions:
    bayesian_optimization: Function. Provides bayesian_optimization behavior for optimization workflows.
"""

import time
from collections.abc import Callable
from typing import Any

from app.services.strategy import BaseStrategy
from app.services.utils.logger import logger

from ..execution import run_strategy_backtest
from ..result import OptimizationResult, OptimizationSummary
from ..scoring import sharpe_score

BacktestResult = Any


def bayesian_optimization(  # noqa: C901
    strategy_class: type[BaseStrategy],
    data,
    param_space: dict[str, tuple[float, float]],
    param_types: dict[str, str] | None = None,
    n_iterations: int = 50,
    n_initial_points: int = 10,
    initial_balance: float = 10000.0,
    scoring_func: Callable[[BacktestResult], float] = sharpe_score,
    engine_type: str = "vectorized",
    max_workers: int | None = None,
    random_state: int | None = None,
    verbose: bool = True,
    progress_callback: Callable | None = None,
    symbol: str | None = None,
) -> OptimizationSummary:
    """Bayesian optimization using Gaussian Processes.

    Purpose:
        Provide deterministic optimization computation, validation, or request packaging as a focused HaruQuant tool.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None unless explicitly documented by the owning workflow.
    """
    _ = max_workers
    try:
        from skopt import gp_minimize
        from skopt.space import Integer, Real
    except ImportError:
        raise ImportError(
            "scikit-optimize is required for Bayesian optimization. "
            "Install it with: pip install scikit-optimize==0.9.0"
        )

    if verbose:
        logger.info(f"Starting Bayesian optimization: {n_iterations} iterations")
        logger.info(f"Parameter space: {param_space}")
        logger.info(f"Initial random points: {n_initial_points}")

    if param_types is None:
        param_types = {}
        for param_name, (min_val, max_val) in param_space.items():
            param_types[param_name] = (
                "int"
                if isinstance(min_val, int) and isinstance(max_val, int)
                else "float"
            )

    param_names = list(param_space.keys())
    dimensions = []
    for param_name in param_names:
        min_val, max_val = param_space[param_name]
        if param_types.get(param_name) == "int":
            dimensions.append(Integer(min_val, max_val, name=param_name))
        else:
            dimensions.append(Real(min_val, max_val, name=param_name))

    all_results = []
    best_score_so_far = float("-inf")
    best_params_so_far = None
    completed = 0
    start_time = time.time()

    if not symbol:
        symbol = data.name if hasattr(data, "name") else "UNKNOWN"

    def objective(param_values):
        nonlocal completed, best_score_so_far, best_params_so_far

        params = {}
        for i, param_name in enumerate(param_names):
            value = param_values[i]
            if param_types.get(param_name) == "int":
                value = int(round(value))
            params[param_name] = value

        if verbose and (completed + 1) % max(1, n_iterations // 10) == 0:
            logger.info(
                f"Progress: {completed + 1}/{n_iterations} ({(completed + 1) / n_iterations * 100:.1f}%)"
            )

        try:
            result = run_strategy_backtest(
                strategy_class=strategy_class,
                data=data,
                symbol=symbol,
                params=params,
                initial_balance=initial_balance,
                engine_type=engine_type,
                position_size=0.1,
            )
            result_metrics = result.summary()
            score = scoring_func(result)

            opt_result = OptimizationResult(
                parameters=params.copy(),
                result=result,
                metrics=result_metrics,
                score=score,
            )
            all_results.append(opt_result)

            if score > best_score_so_far:
                best_score_so_far = score
                best_params_so_far = params.copy()

            if progress_callback:
                progress_callback(
                    completed=completed + 1,
                    total=n_iterations,
                    current_params=params,
                    best_score=best_score_so_far,
                    best_params=best_params_so_far,
                )

            completed += 1
            return -score

        except Exception as e:
            logger.error(f"Failed for params {params}: {e}")
            completed += 1
            return 1e10

    if verbose:
        logger.info("Running Gaussian Process optimization...")

    _ = gp_minimize(
        objective,
        dimensions,
        n_calls=n_iterations,
        n_initial_points=n_initial_points,
        random_state=random_state,
        verbose=False,
        n_jobs=1,
    )

    all_results.sort(key=lambda x: x.score, reverse=True)
    for i, opt_result in enumerate(all_results):
        opt_result.rank = i + 1

    best = all_results[0] if all_results else None
    duration = time.time() - start_time

    summary = OptimizationSummary(
        best_params=best.parameters if best else {},
        best_score=best.score if best else 0.0,
        best_result=best.result if best else None,
        all_results=all_results,
        total_combinations=n_iterations,
        completed=completed,
        failed=max(0, n_iterations - completed),
        duration_seconds=duration,
    )

    if verbose:
        logger.success(f"Bayesian optimization complete in {duration:.2f}s")
        logger.info(f"Best params: {summary.best_params}")
        logger.info(f"Best score: {summary.best_score:.4f}")
        logger.info(f"Completed: {completed}/{n_iterations}")

    return summary


def optimization_bayesian(
    strategy_class: Any,
    data,
    param_space: dict[str, Any],
    n_iterations: int = 20,
    symbol: str = "SYMBOL",
    initial_balance: float = 10000.0,
    objective: str = "Sharpe Ratio",
    max_workers: int = 4,
    verbose: bool = True,
) -> Any:
    """Run Bayesian parameter optimization.

    Purpose:
        Provide a user-facing wrapper around Bayesian optimization.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        Runs local optimization compute only.
    """
    from app.services.optimization._common import service_strategy_class
    from app.services.optimization.scoring import optimization_get_scoring_func

    return bayesian_optimization(
        strategy_class=service_strategy_class(strategy_class),
        data=data,
        param_space=param_space,
        n_iterations=n_iterations,
        symbol=symbol,
        initial_balance=initial_balance,
        scoring_func=optimization_get_scoring_func(objective),
        max_workers=max_workers,
        verbose=verbose,
    )
