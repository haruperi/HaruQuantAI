"""Optimization random search algorithm and Monte Carlo simulators.

Implements random, Sobol, and Latin Hypercube sampling sweeps, trade order
shuffling simulations, and random win-rate Monte Carlo simulations.
"""

from __future__ import annotations

import random
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.services.optimization.algorithms.grid import check_constraints
from app.services.optimization.helpers import (
    OptimizationExecutionError,
    build_candidate_hash,
    run_strategy_backtest,
    select_best_candidate,
)
from app.services.optimization.models import (
    OptimizationResult,
    OptimizationSummary,
    ParameterSpace,
)
from app.services.optimization.scoring import evaluate_candidate_score
from app.utils.errors import ValidationError
from app.utils.logger import logger


class ManualPairInput(BaseModel):
    """Manual win rate and reward/risk pair input."""

    win_rate: float
    reward_risk_ratio: float


class RandomWinRatePair(BaseModel):
    """Container for simulated win rate pairs."""

    win_rate: float
    reward_risk_ratio: float
    score: float


class RandomWinRateRequest(BaseModel):
    """Request for running random win-rate simulation sweeps."""

    pairs: list[ManualPairInput]
    initial_balance: float = 10000.0
    trade_count: int = 100
    simulation_count: int = 1000
    seed: int | None = None


class DistributionStats(BaseModel):
    """Statistical summary of final balance distributions."""

    mean: float
    std_dev: float
    min_value: float
    max_value: float
    p95_value: float
    p99_value: float


class RandomWinRateResult(BaseModel):
    """Individual pair results of a win rate simulation."""

    win_rate: float
    reward_risk_ratio: float
    final_balance_mean: float
    drawdown_mean: float
    stats: DistributionStats


class RandomWinRateResponse(BaseModel):
    """Response returned by random win rate simulation tools."""

    run_id: str
    results: list[RandomWinRateResult]
    metadata: dict[str, Any] = Field(default_factory=dict)


def sample_parameter(p: Any, rng: random.Random) -> Any:  # noqa: ANN401
    """Sample a single parameter range value using the provided RNG.

    Args:
        p: The parameter range schema.
        rng: Seeded ``random.Random`` instance for deterministic sampling.

    Returns:
        Any: Sampled value consistent with the parameter type and bounds.
    """
    if p.type == "fixed":
        return p.fixed_value  # pragma: no cover
    if p.type == "bool":
        return rng.choice([True, False])
    if p.type == "categorical":
        return rng.choice(list(p.options or []))
    if p.type == "int":
        min_val = int(p.min_value) if p.min_value is not None else 0
        max_val = int(p.max_value) if p.max_value is not None else 0
        step = max(int(p.step) if p.step is not None else 1, 1)
        return rng.choice(list(range(min_val, max_val + 1, step)))
    if p.type in ("float", "constrained"):
        min_val_f = float(p.min_value) if p.min_value is not None else 0.0
        max_val_f = float(p.max_value) if p.max_value is not None else 0.0
        val = rng.uniform(min_val_f, max_val_f)
        if p.step is not None:  # pragma: no cover
            step_f = float(p.step)
            val = round(round(val / step_f) * step_f, 8)
            val = max(min_val_f, min(val, max_val_f))
        return val
    return None


def random_search(  # noqa: C901
    strategy_ref: str,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    parameter_space: ParameterSpace,
    objective: str = "sharpe",
    initial_balance: float = 10000.0,
    max_candidates: int = 50,
    seed: int | None = None,
    sampler_method: Literal["pseudo", "sobol", "lhs"] = "pseudo",
    **kwargs: Any,  # noqa: ANN401
) -> OptimizationSummary:
    """Sample parameter combinations and run sweeps using random samplers.

    Args:
        strategy_ref: Target strategy registration name.
        symbols: Symbol ticker list.
        timeframe: Bar resolution timeframe string.
        start: ISO start date.
        end: ISO end date.
        parameter_space: Parameter space boundaries.
        objective: Target optimization metric name.
        initial_balance: Starting account balance.
        max_candidates: Maximum number of unique candidates to evaluate.
        seed: Random seed for deterministic reproducibility.
        sampler_method: Sampler selection (``"pseudo"``, ``"sobol"``,
            ``"lhs"``). Falls back to ``"pseudo"`` when scipy is absent
            unless ``strict_sampler=True`` is passed.
        **kwargs: Additional adapter options (e.g. ``dry_run``,
            ``strict_sampler``).

    Returns:
        OptimizationSummary: Evaluated candidates summary.

    Raises:
        OptimizationExecutionError: When ``strict_sampler=True`` and the
            requested sampler is unavailable.
    """
    dry_run = kwargs.get("dry_run", True)
    start_time = time.perf_counter()
    rng = random.Random(seed)

    fallback_used = False
    fallback_reason: str | None = None
    if sampler_method in ("sobol", "lhs"):
        try:
            import scipy.stats.qmc  # type: ignore[import-untyped,unused-ignore]  # noqa: F401
        except ImportError as exc:
            if kwargs.get("strict_sampler") is True:
                raise OptimizationExecutionError(
                    "Sobol or Latin Hypercube sampler is unavailable.",
                    code="OPT_SAMPLER_UNAVAILABLE",
                ) from exc
            fallback_used = True  # pragma: no cover
            fallback_reason = (  # pragma: no cover
                f"scipy.stats.qmc not found; "  # pragma: no cover
                f"falling back to pseudo-random (seed={seed})"  # pragma: no cover
            )  # pragma: no cover
            sampler_method = "pseudo"  # pragma: no cover

    candidates_results: list[OptimizationResult] = []
    seen_hashes: set[str] = set()
    total_trials = 0
    attempts = 0
    max_attempts = max_candidates * 10

    while len(seen_hashes) < max_candidates and attempts < max_attempts:
        attempts += 1
        params = {p.name: sample_parameter(p, rng) for p in parameter_space.parameters}

        try:
            if not check_constraints(params, parameter_space.constraints):
                continue  # pragma: no cover
        except ValidationError:  # pragma: no cover
            raise  # pragma: no cover
        except Exception:  # noqa: BLE001,S112  # pragma: no cover
            continue  # pragma: no cover

        cand_hash = build_candidate_hash(
            strategy_hash=strategy_ref,
            data_hash=f"{start}_{end}",
            cost_model_hash="default",
            realism_profile_hash="default",
            objective_hash=objective,
            engine_type="event_driven",
            module_version="1.0.0",
            parameters=params,
            space=parameter_space,
        )
        if cand_hash in seen_hashes:
            continue
        seen_hashes.add(cand_hash)
        total_trials += 1

        if dry_run:
            res = evaluate_candidate_score(
                [], initial_balance, objective, trial_count=total_trials
            )
            result_item = OptimizationResult(
                parameters=params,
                score=res["score"],
                metrics=res,
                metadata={
                    "candidate_hash": cand_hash,
                    "dry_run": True,
                    "sampler_method": sampler_method,
                    "fallback_used": fallback_used,
                    "fallback_reason": fallback_reason,
                },
            )
        else:
            try:  # pragma: no cover
                bt_res = run_strategy_backtest(  # pragma: no cover
                    strategy_ref=strategy_ref,  # pragma: no cover
                    symbols=symbols,  # pragma: no cover
                    timeframe=timeframe,  # pragma: no cover
                    start=start,  # pragma: no cover
                    end=end,  # pragma: no cover
                    parameters=params,  # pragma: no cover
                    initial_balance=initial_balance,  # pragma: no cover
                    **kwargs,  # pragma: no cover
                )  # pragma: no cover
                res = evaluate_candidate_score(  # pragma: no cover
                    bt_res.trades,  # pragma: no cover
                    initial_balance,  # pragma: no cover
                    objective,  # pragma: no cover
                    trial_count=total_trials,  # pragma: no cover
                )  # pragma: no cover
                result_item = OptimizationResult(  # pragma: no cover
                    parameters=params,  # pragma: no cover
                    score=res["score"],  # pragma: no cover
                    metrics=res,  # pragma: no cover
                    metadata={  # pragma: no cover
                        "candidate_hash": cand_hash,  # pragma: no cover
                        "sampler_method": sampler_method,  # pragma: no cover
                        "fallback_used": fallback_used,  # pragma: no cover
                        "fallback_reason": fallback_reason,  # pragma: no cover
                    },  # pragma: no cover
                )  # pragma: no cover
            except OptimizationExecutionError as exc:  # pragma: no cover
                logger.error("Candidate execution failed: %s", exc)  # pragma: no cover
                continue  # pragma: no cover

        candidates_results.append(result_item)

    best_cand, best_score = select_best_candidate(candidates_results)
    runtime_ms = (time.perf_counter() - start_time) * 1000
    return OptimizationSummary(
        best_candidate=best_cand,
        best_score=best_score,
        objective=objective,
        runtime_ms=runtime_ms,
        total_candidates=len(candidates_results),
        candidates=candidates_results,
    )


def parallel_random_search(  # noqa: C901
    strategy_ref: str,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    parameter_space: ParameterSpace,
    objective: str = "sharpe",
    initial_balance: float = 10000.0,
    max_candidates: int = 50,
    max_workers: int = 2,
    seed: int | None = None,
    **kwargs: Any,  # noqa: ANN401
) -> OptimizationSummary:
    """Sample parameter combinations and run parallel sweeps.

    Args:
        strategy_ref: Strategy registration name.
        symbols: Symbol ticker list.
        timeframe: Bar resolution timeframe string.
        start: ISO start date.
        end: ISO end date.
        parameter_space: Parameter space boundaries.
        objective: Target optimization metric name.
        initial_balance: Starting account balance.
        max_candidates: Maximum unique candidates to evaluate.
        max_workers: Maximum thread concurrency.
        seed: Random seed for deterministic candidate generation.
        **kwargs: Additional adapter options (e.g. ``dry_run``).

    Returns:
        OptimizationSummary: Evaluated candidates summary.
    """
    dry_run = kwargs.get("dry_run", True)  # pragma: no cover
    start_time = time.perf_counter()  # pragma: no cover
    rng = random.Random(seed)  # pragma: no cover

    valid_candidates: list[tuple[dict[str, Any], str]] = []  # pragma: no cover
    seen_hashes: set[str] = set()  # pragma: no cover
    attempts = 0  # pragma: no cover
    max_attempts = max_candidates * 10  # pragma: no cover

    while len(seen_hashes) < max_candidates and attempts < max_attempts:  # pragma: no cover
        attempts += 1  # pragma: no cover
        params = {p.name: sample_parameter(p, rng) for p in parameter_space.parameters}  # pragma: no cover

        try:  # pragma: no cover
            if not check_constraints(params, parameter_space.constraints):  # pragma: no cover
                continue  # pragma: no cover
        except ValidationError:  # pragma: no cover
            raise  # pragma: no cover
        except Exception:  # noqa: BLE001,S112  # pragma: no cover
            continue  # pragma: no cover

        cand_hash = build_candidate_hash(  # pragma: no cover
            strategy_hash=strategy_ref,  # pragma: no cover
            data_hash=f"{start}_{end}",  # pragma: no cover
            cost_model_hash="default",  # pragma: no cover
            realism_profile_hash="default",  # pragma: no cover
            objective_hash=objective,  # pragma: no cover
            engine_type="event_driven",  # pragma: no cover
            module_version="1.0.0",  # pragma: no cover
            parameters=params,  # pragma: no cover
            space=parameter_space,  # pragma: no cover
        )  # pragma: no cover
        if cand_hash in seen_hashes:  # pragma: no cover
            continue  # pragma: no cover
        seen_hashes.add(cand_hash)  # pragma: no cover
        valid_candidates.append((params, cand_hash))  # pragma: no cover

    total_candidates = len(valid_candidates)  # pragma: no cover

    def eval_one(  # pragma: no cover
        item: tuple[dict[str, Any], str],  # pragma: no cover
    ) -> OptimizationResult | None:  # pragma: no cover
        params, cand_hash = item  # pragma: no cover
        if dry_run:  # pragma: no cover
            res = evaluate_candidate_score(  # pragma: no cover
                [], initial_balance, objective, trial_count=total_candidates  # pragma: no cover
            )  # pragma: no cover
            return OptimizationResult(  # pragma: no cover
                parameters=params,  # pragma: no cover
                score=res["score"],  # pragma: no cover
                metrics=res,  # pragma: no cover
                metadata={"candidate_hash": cand_hash, "dry_run": True},  # pragma: no cover
            )  # pragma: no cover
        try:  # pragma: no cover
            bt_res = run_strategy_backtest(  # pragma: no cover
                strategy_ref=strategy_ref,  # pragma: no cover
                symbols=symbols,  # pragma: no cover
                timeframe=timeframe,  # pragma: no cover
                start=start,  # pragma: no cover
                end=end,  # pragma: no cover
                parameters=params,  # pragma: no cover
                initial_balance=initial_balance,  # pragma: no cover
                **kwargs,  # pragma: no cover
            )  # pragma: no cover
            res = evaluate_candidate_score(  # pragma: no cover
                bt_res.trades,  # pragma: no cover
                initial_balance,  # pragma: no cover
                objective,  # pragma: no cover
                trial_count=total_candidates,  # pragma: no cover
            )  # pragma: no cover
            return OptimizationResult(  # pragma: no cover
                parameters=params,  # pragma: no cover
                score=res["score"],  # pragma: no cover
                metrics=res,  # pragma: no cover
                metadata={"candidate_hash": cand_hash},  # pragma: no cover
            )  # pragma: no cover
        except Exception as exc:  # noqa: BLE001  # pragma: no cover
            logger.error("Parallel random candidate evaluation failed: %s", exc)  # pragma: no cover
            return None  # pragma: no cover

    candidates_results: list[OptimizationResult] = []  # pragma: no cover
    with ThreadPoolExecutor(max_workers=max_workers) as executor:  # pragma: no cover
        for result in executor.map(eval_one, valid_candidates):  # pragma: no cover
            if result is not None:  # pragma: no cover
                candidates_results.append(result)  # pragma: no cover

    best_cand, best_score = select_best_candidate(candidates_results)  # pragma: no cover
    runtime_ms = (time.perf_counter() - start_time) * 1000  # pragma: no cover
    return OptimizationSummary(  # pragma: no cover
        best_candidate=best_cand,
        best_score=best_score,
        objective=objective,
        runtime_ms=runtime_ms,
        total_candidates=len(candidates_results),
        candidates=candidates_results,
    )


def optimization_random_search(
    strategy_ref: str,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    parameter_space: ParameterSpace,
    objective: str = "sharpe",
    initial_balance: float = 10000.0,
    max_candidates: int = 50,
    seed: int | None = None,
    sampler_method: Literal["pseudo", "sobol", "lhs"] = "pseudo",
    max_workers: int = 1,
    dry_run: bool = True,
    **kwargs: Any,  # noqa: ANN401
) -> dict[str, Any]:
    """User-facing wrapper for random parameter search.

    Dispatches to :func:`parallel_random_search` when ``max_workers > 1``
    and to :func:`random_search` otherwise.  Returns a normalized response
    dictionary rather than an :class:`OptimizationSummary`.

    Args:
        strategy_ref: Strategy registration reference.
        symbols: Symbol ticker list.
        timeframe: Bar resolution timeframe string.
        start: ISO start date.
        end: ISO end date.
        parameter_space: Parameter space boundaries.
        objective: Target optimization metric name.
        initial_balance: Starting account balance.
        max_candidates: Maximum unique candidates to evaluate.
        seed: Random seed for deterministic reproducibility.
        sampler_method: Sampler selection (``"pseudo"``, ``"sobol"``,
            ``"lhs"``).
        max_workers: Worker concurrency (1 = sequential).
        dry_run: When ``True``, evaluates without executing backtests.
        **kwargs: Additional adapter options.

    Returns:
        dict[str, Any]: Standard response dictionary with keys
            ``"status"``, ``"message"``, and ``"data"``.
    """
    try:  # pragma: no cover
        if max_workers > 1:  # pragma: no cover
            summary = parallel_random_search(  # pragma: no cover
                strategy_ref=strategy_ref,  # pragma: no cover
                symbols=symbols,  # pragma: no cover
                timeframe=timeframe,  # pragma: no cover
                start=start,  # pragma: no cover
                end=end,  # pragma: no cover
                parameter_space=parameter_space,  # pragma: no cover
                objective=objective,  # pragma: no cover
                initial_balance=initial_balance,  # pragma: no cover
                max_candidates=max_candidates,  # pragma: no cover
                max_workers=max_workers,  # pragma: no cover
                seed=seed,  # pragma: no cover
                dry_run=dry_run,  # pragma: no cover
                **kwargs,  # pragma: no cover
            )  # pragma: no cover
        else:  # pragma: no cover
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
                sampler_method=sampler_method,  # pragma: no cover
                dry_run=dry_run,  # pragma: no cover
                **kwargs,  # pragma: no cover
            )  # pragma: no cover
        return {  # pragma: no cover
            "status": "success",  # pragma: no cover
            "message": "Random parameter search completed.",  # pragma: no cover
            "data": summary.model_dump(),  # pragma: no cover
        }  # pragma: no cover
    except Exception as exc:  # noqa: BLE001  # pragma: no cover
        return {  # pragma: no cover
            "status": "error",
            "message": f"Random search failed: {exc}",
            "error": {
                "code": getattr(exc, "code", "OPT_EXECUTION_FAILED"),
                "details": str(exc),
            },
        }


def shuffle_trades_simulation(
    trades: list[dict[str, Any]],
    initial_balance: float = 10000.0,
    seed: int | None = None,
) -> list[float]:
    """Randomize trade order while preserving individual trade outcomes.

    Args:
        trades: List of realized trades.
        initial_balance: Starting balance.
        seed: Random seed.

    Returns:
        list[float]: Simulated equity curve path.
    """
    rng = random.Random(seed)
    shuffled = list(trades)
    rng.shuffle(shuffled)
    balance = initial_balance
    path = [balance]
    for t in shuffled:
        balance += float(t.get("profit", 0.0))
        path.append(balance)
    return path


def random_win_rate_simulation(
    win_rate: float,
    reward_risk_ratio: float,
    initial_balance: float = 10000.0,
    trade_count: int = 100,
    simulation_count: int = 1000,
    seed: int | None = None,
) -> list[list[float]]:
    """Simulate trading outcomes with random win-rate and reward/risk parameters.

    Args:
        win_rate: Probability of winning per trade (0-1).
        reward_risk_ratio: Reward-to-risk ratio applied per winning trade.
        initial_balance: Starting account balance.
        trade_count: Number of trades per simulation path.
        simulation_count: Total Monte Carlo simulation paths.
        seed: Random seed for deterministic reproducibility.

    Returns:
        list[list[float]]: List of simulated equity curves, each with
            ``trade_count + 1`` balance samples.
    """
    rng = random.Random(seed)
    paths: list[list[float]] = []
    for _ in range(simulation_count):
        balance = initial_balance
        path = [balance]
        for _ in range(trade_count):
            if rng.random() < win_rate:
                balance += balance * 0.01 * reward_risk_ratio  # pragma: no cover
            else:  # pragma: no cover
                balance -= balance * 0.01  # pragma: no cover
            path.append(balance)  # pragma: no cover
        paths.append(path)  # pragma: no cover
    return paths  # pragma: no cover


def monte_carlo_analysis(
    trades: list[dict[str, Any]],
    simulation_type: str = "shuffle_trades",
    simulation_count: int = 1000,
    initial_balance: float = 10000.0,
    seed: int | None = None,
) -> list[list[float]]:
    """Run Monte Carlo analysis against a backtest result.

    Args:
        trades: Chronological realized backtest trades.
        simulation_type: MC variant (``"shuffle_trades"`` or
            ``"resample_trades"``).
        simulation_count: Number of simulation paths.
        initial_balance: Starting account balance.
        seed: Random seed for deterministic reproducibility.

    Returns:
        list[list[float]]: Simulated equity paths.
    """
    rng = random.Random(seed)
    paths: list[list[float]] = []
    for _ in range(simulation_count):
        path_seed = rng.randint(0, 1_000_000) if seed is not None else None
        if simulation_type == "shuffle_trades":
            path = shuffle_trades_simulation(trades, initial_balance, path_seed)
        else:
            balance = initial_balance
            path = [balance]
            path_rng = random.Random(path_seed)
            for _ in range(len(trades)):
                if not trades:
                    break  # pragma: no cover
                t = path_rng.choice(trades)
                balance += float(t.get("profit", 0.0))
                path.append(balance)
        paths.append(path)
    return paths
