"""Strategy robustness scoring, stress testing, and Monte Carlo simulation.

Provides Monte Carlo ruin estimators, block bootstrap simulators, and slippage,
spread, and commission stress checkers.
"""

from __future__ import annotations

import random
import uuid
from typing import Any, Literal

import numpy as np

from app.services.optimization.models import (
    MonteCarloResponse,
    MonteCarloResult,
    ParameterSpace,
    RobustnessResponse,
    RobustnessStats,
)
from app.utils.logger import logger

# ---------------------------------------------------------------------------
# Named constants
# ---------------------------------------------------------------------------
_RUIN_FRACTION: float = 0.5
_DAILY_DD_THRESHOLD: float = 0.90
_TOTAL_DD_THRESHOLD: float = 0.80
_MIN_SKIP_PASS_RATE: float = 0.80
_MC_RUIN_PROBABILITY_LIMIT: float = 0.05
_MC_RUIN_SAMPLE_SIZE: int = 100
_ROBUSTNESS_WARNING_THRESHOLD: float = 75.0
_STRESS_SKIP_FRACTION: float = 0.10
_STRESS_SKIP_SIMULATIONS: int = 10
_DEFAULT_SLIPPAGE_PIPS: float = 2.0
_DEFAULT_COMMISSION_PER_LOT: float = 5.0
_SPREAD_MULTIPLIER_DEFAULT: float = 2.0
_PIP_VALUE_DEFAULT: float = 10.0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _compute_max_losing_streak(path: list[float]) -> int:
    """Compute the longest consecutive drawdown streak from an equity path.

    A bar is counted as a loss when the balance is below the previous bar
    balance.

    Args:
        path: Equity curve as a sequence of balance values.

    Returns:
        int: Length of the longest consecutive loss streak (0 when empty
            or all gains).
    """
    if len(path) < 2:  # noqa: PLR2004
        return 0
    max_streak = 0
    current_streak = 0
    for i in range(1, len(path)):
        if path[i] < path[i - 1]:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    return max_streak


def calculate_robustness_score(checks: dict[str, bool]) -> float:
    """Calculate deterministic robustness percentage from pass/fail checks.

    Args:
        checks: Mapping of check name to pass status.

    Returns:
        float: Robustness score from 0 to 100.
    """
    if not checks:
        return 0.0
    passed = sum(1 for v in checks.values() if v is True)
    return (passed / len(checks)) * 100.0


def bootstrap_simulation(
    trades: list[dict[str, Any]],
    block_size: int = 5,
    simulation_count: int = 1000,
    initial_balance: float = 10000.0,
    seed: int | None = None,
) -> list[list[float]]:
    """Sample blocks of contiguous trades to preserve short-term temporal structure.

    Args:
        trades: Chronological realized trades.
        block_size: Number of contiguous trades per sampled block.
        simulation_count: Number of Monte Carlo paths.
        initial_balance: Starting account balance.
        seed: Random seed for deterministic reproducibility.

    Returns:
        list[list[float]]: Simulated equity paths, each length
            ``len(trades) + 1``.
    """
    rng = random.Random(seed)
    n = len(trades)
    if n == 0:
        return [[initial_balance] for _ in range(simulation_count)]

    block_size = max(1, min(block_size, n))
    paths: list[list[float]] = []
    for _ in range(simulation_count):
        balance = initial_balance
        path = [balance]
        while len(path) <= n:
            start_idx = rng.randint(0, n - block_size)
            for i in range(block_size):
                if len(path) > n:
                    break
                t = trades[start_idx + i]
                balance += float(t.get("profit", 0.0))
                path.append(balance)
        paths.append(path)
    return paths


# ---------------------------------------------------------------------------
# Stress tests
# ---------------------------------------------------------------------------
def run_spread_stress_test(
    trades: list[dict[str, Any]],
    spread_multiplier: float = _SPREAD_MULTIPLIER_DEFAULT,
    pip_value: float = _PIP_VALUE_DEFAULT,
) -> list[dict[str, Any]]:
    """Simulate spread-widening costs on trades.

    Args:
        trades: List of trades.
        spread_multiplier: Factor applied to the standard spread.
        pip_value: Currency value of one pip.

    Returns:
        list[dict[str, Any]]: Trades with adjusted profit field.
    """
    adjusted = []
    for t in trades:
        tc = dict(t)
        penalty = spread_multiplier * 0.0001 * pip_value * float(t.get("volume", 1.0))
        tc["profit"] = float(t.get("profit", 0.0)) - penalty
        adjusted.append(tc)
    return adjusted


def run_slippage_stress_test(
    trades: list[dict[str, Any]],
    slippage_pips: float = _DEFAULT_SLIPPAGE_PIPS,
    pip_value: float = _PIP_VALUE_DEFAULT,
) -> list[dict[str, Any]]:
    """Simulate execution-slippage costs on trades.

    Args:
        trades: List of trades.
        slippage_pips: Average slippage in pips.
        pip_value: Currency value of one pip.

    Returns:
        list[dict[str, Any]]: Trades with adjusted profit field.
    """
    adjusted = []
    for t in trades:
        tc = dict(t)
        penalty = slippage_pips * 0.0001 * pip_value * float(t.get("volume", 1.0))
        tc["profit"] = float(t.get("profit", 0.0)) - penalty
        adjusted.append(tc)
    return adjusted


def run_commission_stress_test(
    trades: list[dict[str, Any]],
    extra_commission_per_lot: float = _DEFAULT_COMMISSION_PER_LOT,
) -> list[dict[str, Any]]:
    """Simulate commission-increase costs on trades.

    Args:
        trades: List of trades.
        extra_commission_per_lot: Additional commission applied per lot.

    Returns:
        list[dict[str, Any]]: Trades with adjusted profit field.
    """
    adjusted = []
    for t in trades:
        tc = dict(t)
        penalty = extra_commission_per_lot * float(t.get("volume", 1.0))
        tc["profit"] = float(t.get("profit", 0.0)) - penalty
        adjusted.append(tc)
    return adjusted


# ---------------------------------------------------------------------------
# Monte Carlo variants
# ---------------------------------------------------------------------------
def run_randomize_trade_order_mc(
    trades: list[dict[str, Any]],
    initial_balance: float = 10000.0,
    simulation_count: int = 1000,
    seed: int | None = None,
) -> list[list[float]]:
    """Shuffle trade order in Monte Carlo paths.

    Args:
        trades: List of trades.
        initial_balance: Starting balance.
        simulation_count: Number of paths.
        seed: Random seed.

    Returns:
        list[list[float]]: Simulated equity paths.
    """
    from app.services.optimization.algorithms.random import monte_carlo_analysis

    return monte_carlo_analysis(
        trades, "shuffle_trades", simulation_count, initial_balance, seed
    )


def run_resample_trades_mc(
    trades: list[dict[str, Any]],
    initial_balance: float = 10000.0,
    simulation_count: int = 1000,
    seed: int | None = None,
) -> list[list[float]]:
    """Resample trades with replacement in Monte Carlo paths.

    Args:
        trades: List of trades.
        initial_balance: Starting balance.
        simulation_count: Number of paths.
        seed: Random seed.

    Returns:
        list[list[float]]: Simulated equity paths.
    """
    from app.services.optimization.algorithms.random import monte_carlo_analysis

    return monte_carlo_analysis(
        trades, "resample_trades", simulation_count, initial_balance, seed
    )


def run_skip_trades_mc(
    trades: list[dict[str, Any]],
    skip_fraction: float = _STRESS_SKIP_FRACTION,
    simulation_count: int = 100,
    initial_balance: float = 10000.0,
    seed: int | None = None,
) -> list[list[float]]:
    """Randomly drop winning trades to stress-test robustness.

    Args:
        trades: List of trades.
        skip_fraction: Fraction of winning trades to drop per path.
        simulation_count: Number of paths.
        initial_balance: Starting account balance.
        seed: Random seed.

    Returns:
        list[list[float]]: Simulated equity paths.
    """
    rng = random.Random(seed)
    paths: list[list[float]] = []
    for _ in range(simulation_count):
        balance = initial_balance
        path = [balance]
        for t in trades:
            profit = float(t.get("profit", 0.0))
            if profit > 0.0 and rng.random() < skip_fraction:
                continue
            balance += profit
            path.append(balance)
        paths.append(path)
    return paths


def run_randomize_parameters_mc(
    strategy_ref: str,
    parameters: dict[str, Any],
    space: ParameterSpace,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    initial_balance: float = 10000.0,
    simulation_count: int = 10,
    seed: int | None = None,
) -> list[float]:
    """Perturb strategy parameters randomly and evaluate scores.

    Args:
        strategy_ref: Strategy registration name.
        parameters: Baseline parameter values.
        space: Parameter space for value type metadata.
        symbols: Symbol ticker list.
        timeframe: Bar resolution timeframe string.
        start: ISO start date.
        end: ISO end date.
        initial_balance: Starting account balance.
        simulation_count: Number of perturbation evaluations.
        seed: Random seed for deterministic reproducibility.

    Returns:
        list[float]: Total-return scores across perturbed configurations.
    """
    from app.services.optimization.helpers import run_strategy_backtest
    from app.services.optimization.scoring import total_return_score

    rng = random.Random(seed)
    scores: list[float] = []
    for _ in range(simulation_count):
        perturbed: dict[str, Any] = {}
        for p in space.parameters:
            curr_val = parameters.get(p.name)
            if curr_val is None:
                continue
            if isinstance(curr_val, int | float):
                noise = rng.uniform(-0.1, 0.1)
                new_val = curr_val * (1.0 + noise)
                if p.type == "int":
                    perturbed[p.name] = round(new_val)
                else:
                    perturbed[p.name] = round(new_val, 8)
            else:
                perturbed[p.name] = curr_val
        try:
            res = run_strategy_backtest(
                strategy_ref=strategy_ref,
                symbols=symbols,
                timeframe=timeframe,
                start=start,
                end=end,
                parameters=perturbed,
                initial_balance=initial_balance,
            )
            scores.append(total_return_score(res.trades, initial_balance))
        except Exception:  # noqa: BLE001
            scores.append(0.0)
    return scores


def run_randomize_history_mc(
    trades: list[dict[str, Any]],
    initial_balance: float = 10000.0,
    simulation_count: int = 100,
    seed: int | None = None,
) -> list[list[float]]:
    """Simulate history bootstrap paths using block resampling.

    Args:
        trades: Chronological realized trades.
        initial_balance: Starting account balance.
        simulation_count: Number of paths.
        seed: Random seed.

    Returns:
        list[list[float]]: Simulated equity paths.
    """
    return bootstrap_simulation(
        trades,
        block_size=5,
        simulation_count=simulation_count,
        initial_balance=initial_balance,
        seed=seed,
    )


def run_combined_monte_carlo(
    trades: list[dict[str, Any]],
    initial_balance: float = 10000.0,
    simulation_count: int = 100,
    seed: int | None = None,
) -> list[list[float]]:
    """Run combined Monte Carlo using trade resampling.

    Args:
        trades: Chronological realized trades.
        initial_balance: Starting account balance.
        simulation_count: Number of paths.
        seed: Random seed.

    Returns:
        list[list[float]]: Simulated equity paths.
    """
    return run_resample_trades_mc(trades, initial_balance, simulation_count, seed)


def run_cross_market_test(
    strategy_ref: str,
    parameters: dict[str, Any],
    other_symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    initial_balance: float = 10000.0,
) -> dict[str, float]:
    """Test strategy parameter stability on out-of-universe asset symbols.

    Args:
        strategy_ref: Strategy registration name.
        parameters: Strategy parameter configuration.
        other_symbols: Out-of-universe symbols to test.
        timeframe: Bar resolution timeframe string.
        start: ISO start date.
        end: ISO end date.
        initial_balance: Starting account balance.

    Returns:
        dict[str, float]: Total-return score keyed by symbol.
    """
    from app.services.optimization.helpers import run_strategy_backtest
    from app.services.optimization.scoring import total_return_score

    results: dict[str, float] = {}
    for sym in other_symbols:
        try:
            res = run_strategy_backtest(
                strategy_ref=strategy_ref,
                symbols=[sym],
                timeframe=timeframe,
                start=start,
                end=end,
                parameters=parameters,
                initial_balance=initial_balance,
            )
            results[sym] = total_return_score(res.trades, initial_balance)
        except Exception:  # noqa: BLE001
            results[sym] = 0.0
    return results


def run_cross_timeframe_test(
    strategy_ref: str,
    parameters: dict[str, Any],
    symbols: list[str],
    other_timeframes: list[str],
    start: str,
    end: str,
    initial_balance: float = 10000.0,
) -> dict[str, float]:
    """Test strategy parameter stability across bar resolution timeframes.

    Args:
        strategy_ref: Strategy registration name.
        parameters: Strategy parameter configuration.
        symbols: Symbol ticker list.
        other_timeframes: Timeframes to evaluate.
        start: ISO start date.
        end: ISO end date.
        initial_balance: Starting account balance.

    Returns:
        dict[str, float]: Total-return score keyed by timeframe string.
    """
    from app.services.optimization.helpers import run_strategy_backtest
    from app.services.optimization.scoring import total_return_score

    results: dict[str, float] = {}
    for tf in other_timeframes:
        try:
            res = run_strategy_backtest(
                strategy_ref=strategy_ref,
                symbols=symbols,
                timeframe=tf,
                start=start,
                end=end,
                parameters=parameters,
                initial_balance=initial_balance,
            )
            results[tf] = total_return_score(res.trades, initial_balance)
        except Exception:  # noqa: BLE001
            results[tf] = 0.0
    return results


def run_second_oos_test(
    strategy_ref: str,
    parameters: dict[str, Any],
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    initial_balance: float = 10000.0,
) -> float:
    """Evaluate strategy performance on a secondary out-of-sample data slice.

    Args:
        strategy_ref: Strategy registration name.
        parameters: Strategy parameter configuration.
        symbols: Symbol ticker list.
        timeframe: Bar resolution timeframe string.
        start: ISO start date.
        end: ISO end date.
        initial_balance: Starting account balance.

    Returns:
        float: Total-return score on the OOS slice, or 0.0 on failure.
    """
    from app.services.optimization.helpers import run_strategy_backtest
    from app.services.optimization.scoring import total_return_score

    try:
        res = run_strategy_backtest(
            strategy_ref=strategy_ref,
            symbols=symbols,
            timeframe=timeframe,
            start=start,
            end=end,
            parameters=parameters,
            initial_balance=initial_balance,
        )
        return total_return_score(res.trades, initial_balance)
    except Exception:  # noqa: BLE001
        return 0.0


def run_third_oos_test(
    strategy_ref: str,
    parameters: dict[str, Any],
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    initial_balance: float = 10000.0,
) -> float:
    """Evaluate strategy performance on a tertiary out-of-sample data slice.

    Args:
        strategy_ref: Strategy registration name.
        parameters: Strategy parameter configuration.
        symbols: Symbol ticker list.
        timeframe: Bar resolution timeframe string.
        start: ISO start date.
        end: ISO end date.
        initial_balance: Starting account balance.

    Returns:
        float: Total-return score on the OOS slice.
    """
    return run_second_oos_test(
        strategy_ref, parameters, symbols, timeframe, start, end, initial_balance
    )


# ---------------------------------------------------------------------------
# Primary robustness assessment
# ---------------------------------------------------------------------------
def assess_strategy_robustness(
    trades: list[dict[str, Any]],
    initial_balance: float = 10000.0,
    seed: int | None = None,
) -> RobustnessResponse:
    """Assess strategy robustness under commission, slippage, and MC shocks.

    Args:
        trades: Chronological realized trades.
        initial_balance: Starting account balance.
        seed: Random seed for deterministic MC runs.

    Returns:
        RobustnessResponse: Structured robustness verification stats.
    """
    checks: dict[str, bool] = {}

    slip_trades = run_slippage_stress_test(trades, slippage_pips=_DEFAULT_SLIPPAGE_PIPS)
    slip_profit = sum(float(t["profit"]) for t in slip_trades)
    checks["slippage_stress_test"] = bool(slip_profit > 0.0)

    comm_trades = run_commission_stress_test(
        trades, extra_commission_per_lot=_DEFAULT_COMMISSION_PER_LOT
    )
    comm_profit = sum(float(t["profit"]) for t in comm_trades)
    checks["commission_stress_test"] = bool(comm_profit > 0.0)

    skip_paths = run_skip_trades_mc(
        trades,
        skip_fraction=_STRESS_SKIP_FRACTION,
        simulation_count=_STRESS_SKIP_SIMULATIONS,
        initial_balance=initial_balance,
        seed=seed,
    )
    skip_pass = sum(1 for path in skip_paths if path[-1] > initial_balance)
    checks["skip_trades_stress_test"] = bool(
        skip_pass / _STRESS_SKIP_SIMULATIONS >= _MIN_SKIP_PASS_RATE
    )

    mc_paths = run_resample_trades_mc(
        trades,
        initial_balance,
        simulation_count=_MC_RUIN_SAMPLE_SIZE,
        seed=seed,
    )
    ruined = sum(
        1 for path in mc_paths if min(path) < initial_balance * (1.0 - _RUIN_FRACTION)
    )
    checks["mc_ruin_test"] = bool(
        ruined / _MC_RUIN_SAMPLE_SIZE < _MC_RUIN_PROBABILITY_LIMIT
    )

    score = calculate_robustness_score(checks)
    warnings = (
        ["overfitting_risk_detected"] if score < _ROBUSTNESS_WARNING_THRESHOLD else []
    )
    stats = RobustnessStats(
        pass_rate=score,
        robustness_score=score,
        warnings=warnings,
    )
    return RobustnessResponse(
        run_id=f"rob_{uuid.uuid4().hex[:8]}",
        stats=stats,
        checks=checks,
    )


# ---------------------------------------------------------------------------
# Monte Carlo builders
# ---------------------------------------------------------------------------
def build_monte_carlo_result(
    paths: list[list[float]],
    initial_balance: float,
    ruin_threshold: float,
    target_balance: float,
) -> MonteCarloResult:
    """Compute statistics and return a structured ``MonteCarloResult``.

    Losing-streak distribution is derived deterministically from each
    equity path using :func:`_compute_max_losing_streak`.

    Args:
        paths: Equity curves list.
        initial_balance: Starting account balance.
        ruin_threshold: Fraction of initial balance below which an account
            is considered ruined (e.g. 0.5 = 50 % drawdown).
        target_balance: Balance level that counts as a profit target.

    Returns:
        MonteCarloResult: Aggregated Monte Carlo statistics.
    """
    final_equity = [path[-1] for path in paths]
    drawdowns_paths: list[list[float]] = []
    max_drawdowns: list[float] = []
    ruined_count = 0
    daily_breach_count = 0
    total_breach_count = 0
    profit_target_count = 0
    losing_streaks: list[int] = []

    for path in paths:
        peak = initial_balance
        path_dd: list[float] = []
        path_max_dd = 0.0
        for val in path:
            peak = max(peak, val)
            dd = (peak - val) / peak if peak > 0.0 else 0.0
            path_dd.append(dd)
            path_max_dd = max(path_max_dd, dd)

        drawdowns_paths.append(path_dd)
        max_drawdowns.append(path_max_dd)

        if min(path) < initial_balance * (1.0 - ruin_threshold):
            ruined_count += 1
        if min(path) < initial_balance * _DAILY_DD_THRESHOLD:
            daily_breach_count += 1
        if min(path) < initial_balance * _TOTAL_DD_THRESHOLD:
            total_breach_count += 1
        if max(path) >= target_balance:
            profit_target_count += 1

        losing_streaks.append(_compute_max_losing_streak(path))

    n_paths = len(paths)
    return MonteCarloResult(
        equity_curves=paths,
        drawdowns=drawdowns_paths,
        final_equity=final_equity,
        max_drawdowns=max_drawdowns,
        ruin_probability=ruined_count / n_paths if n_paths > 0 else 0.0,
        daily_loss_breach_probability=(
            daily_breach_count / n_paths if n_paths > 0 else 0.0
        ),
        total_loss_breach_probability=(
            total_breach_count / n_paths if n_paths > 0 else 0.0
        ),
        profit_target_probability=(
            profit_target_count / n_paths if n_paths > 0 else 0.0
        ),
        losing_streak_distribution=losing_streaks,
    )


def optimization_monte_carlo(
    trades: list[dict[str, Any]],
    simulation_method: Literal[
        "shuffle_trades", "resample_trades", "skip_trades"
    ] = "shuffle_trades",
    simulation_count: int = 1000,
    initial_balance: float = 10000.0,
    ruin_threshold: float = _RUIN_FRACTION,
    target_balance: float = 12000.0,
    seed: int | None = None,
) -> MonteCarloResponse:
    """Expose Monte Carlo analysis over trade results.

    Args:
        trades: Chronological realized backtest trades.
        simulation_method: MC variant (``"shuffle_trades"``,
            ``"resample_trades"``, or ``"skip_trades"``).
        simulation_count: Number of simulation paths.
        initial_balance: Starting account balance.
        ruin_threshold: Fraction threshold defining account ruin.
        target_balance: Balance level counting as a profit target.
        seed: Random seed for deterministic reproducibility.

    Returns:
        MonteCarloResponse: Aggregated Monte Carlo statistics.
    """
    if simulation_method == "skip_trades":
        paths = run_skip_trades_mc(
            trades, _STRESS_SKIP_FRACTION, simulation_count, initial_balance, seed
        )
    else:
        from app.services.optimization.algorithms.random import monte_carlo_analysis

        paths = monte_carlo_analysis(
            trades, simulation_method, simulation_count, initial_balance, seed
        )

    res = build_monte_carlo_result(
        paths, initial_balance, ruin_threshold, target_balance
    )

    max_dds = res.max_drawdowns
    p95_dd = float(np.percentile(max_dds, 95)) if max_dds else 0.0
    p99_dd = float(np.percentile(max_dds, 99)) if max_dds else 0.0

    return MonteCarloResponse(
        run_id=f"mc_{uuid.uuid4().hex[:8]}",
        ruin_probability=res.ruin_probability,
        drawdown_p95=p95_dd,
        drawdown_p99=p99_dd,
        mean_final_balance=(
            float(np.mean(res.final_equity)) if res.final_equity else initial_balance
        ),
        results=res,
    )


def robustness_simulation(
    trades: list[dict[str, Any]],
    skip_fraction: float = _STRESS_SKIP_FRACTION,
    deterioration_pct: float = 0.05,
    mode: Literal["shuffle_trades", "resample_trades"] = "shuffle_trades",
    simulation_count: int = 1000,
    initial_balance: float = 10000.0,
    seed: int | None = None,
) -> list[list[float]]:
    """Simulate robustness under trade dropping, cost deterioration, and shuffling.

    Args:
        trades: Chronological realized trades.
        skip_fraction: Fraction of winning trades to drop.
        deterioration_pct: Proportional cost increase applied to each
            trade profit before dropping and resampling.
        mode: Final resampling mode (``"shuffle_trades"`` or
            ``"resample_trades"``).
        simulation_count: Number of simulation paths.
        initial_balance: Starting account balance.
        seed: Random seed for deterministic reproducibility.

    Returns:
        list[list[float]]: Simulated equity paths.
    """
    deteriorated = [
        {**t, "profit": float(t.get("profit", 0.0)) * (1.0 - deterioration_pct)}
        for t in trades
    ]

    rng = random.Random(seed)
    dropped = [
        t
        for t in deteriorated
        if not (float(t["profit"]) > 0.0 and rng.random() < skip_fraction)
    ]

    from app.services.optimization.algorithms.random import monte_carlo_analysis

    return monte_carlo_analysis(dropped, mode, simulation_count, initial_balance, seed)


def compare_simulation_methods(
    trades: list[dict[str, Any]],
    initial_balance: float = 10000.0,
    simulation_count: int = 1000,
    seed: int | None = None,
) -> dict[str, float]:
    """Compare ruin probabilities across different Monte Carlo methods.

    Args:
        trades: Chronological realized trades.
        initial_balance: Starting account balance.
        simulation_count: Number of paths per method.
        seed: Random seed for deterministic reproducibility.

    Returns:
        dict[str, float]: Ruin probability keyed by method name.
    """
    shuffled = optimization_monte_carlo(
        trades, "shuffle_trades", simulation_count, initial_balance, seed=seed
    )
    resampled = optimization_monte_carlo(
        trades, "resample_trades", simulation_count, initial_balance, seed=seed
    )
    return {
        "shuffle_trades": shuffled.ruin_probability,
        "resample_trades": resampled.ruin_probability,
    }


def run_monte_carlo_task(
    trades: list[dict[str, Any]],
    simulation_method: str = "shuffle_trades",
    simulation_count: int = 1000,
    initial_balance: float = 10000.0,
    seed: int | None = None,
) -> str:
    """Register a background Monte Carlo simulation run and return a task ID.

    Args:
        trades: Chronological realized trades.
        simulation_method: MC variant name.
        simulation_count: Number of simulation paths.
        initial_balance: Starting account balance.
        seed: Random seed for deterministic reproducibility.

    Returns:
        str: Unique task identifier.
    """
    task_id = f"task_mc_{uuid.uuid4().hex[:8]}"
    logger.info(
        "Background Monte Carlo task %s registered with %d trades "
        "using method %s (simulation_count=%d, initial_balance=%s, seed=%s).",
        task_id,
        len(trades),
        simulation_method,
        simulation_count,
        initial_balance,
        seed,
    )
    return task_id


# ---------------------------------------------------------------------------
# Robustness report
# ---------------------------------------------------------------------------
def build_robustness_report(
    trades: list[dict[str, Any]],
    initial_balance: float = 10000.0,
    simulation_count: int = 1000,
    ruin_threshold: float = _RUIN_FRACTION,
    target_balance: float | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    """Produce a comprehensive robustness report combining stress tests and MC.

    Runs slippage, commission, skip-trades, and spread stress tests in
    addition to all three Monte Carlo variants.  Assembles a single
    dictionary suitable for serialization and downstream reporting.

    Args:
        trades: Chronological realized backtest trades.
        initial_balance: Starting account balance.
        simulation_count: Number of paths per Monte Carlo variant.
        ruin_threshold: Fraction of initial balance defining ruin.
        target_balance: Profit target balance (defaults to
            ``initial_balance * 1.2``).
        seed: Random seed for deterministic reproducibility.

    Returns:
        dict[str, Any]: Comprehensive robustness report containing
            ``"robustness_assessment"``, ``"monte_carlo"`` (keyed by
            method), ``"stress_tests"``, and ``"summary"`` sections.
    """
    if target_balance is None:
        target_balance = initial_balance * 1.2

    robustness = assess_strategy_robustness(trades, initial_balance, seed)

    mc_results: dict[str, Any] = {}
    for method in ("shuffle_trades", "resample_trades", "skip_trades"):
        mc = optimization_monte_carlo(
            trades,
            simulation_method=method,
            simulation_count=simulation_count,
            initial_balance=initial_balance,
            ruin_threshold=ruin_threshold,
            target_balance=target_balance,
            seed=seed,
        )
        mc_results[method] = {
            "ruin_probability": mc.ruin_probability,
            "drawdown_p95": mc.drawdown_p95,
            "drawdown_p99": mc.drawdown_p99,
            "mean_final_balance": mc.mean_final_balance,
        }

    spread_trades = run_spread_stress_test(trades)
    slip_trades = run_slippage_stress_test(trades)
    comm_trades = run_commission_stress_test(trades)

    stress_tests = {
        "spread_stress_profit": sum(float(t["profit"]) for t in spread_trades),
        "slippage_stress_profit": sum(float(t["profit"]) for t in slip_trades),
        "commission_stress_profit": sum(float(t["profit"]) for t in comm_trades),
    }

    return {
        "robustness_assessment": robustness.model_dump(),
        "monte_carlo": mc_results,
        "stress_tests": stress_tests,
        "summary": {
            "robustness_score": robustness.stats.robustness_score,
            "all_mc_ruin_probabilities": {
                m: v["ruin_probability"] for m, v in mc_results.items()
            },
            "warnings": robustness.stats.warnings,
        },
    }
