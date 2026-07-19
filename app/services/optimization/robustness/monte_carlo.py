"""Deterministic Monte Carlo and parametric robustness calculations."""

from __future__ import annotations

import random
from collections.abc import Sequence
from decimal import Decimal

from app.services.optimization.robustness.contracts import (
    MonteCarloMethod,
    MonteCarloRequest,
    MonteCarloResult,
)
from app.utils import logger

_SUB_SEED_POLICY = "seed_plus_path_index_v1"


def _validate_decimal_values(values: Sequence[Decimal]) -> tuple[Decimal, ...]:
    """Validate a non-empty finite Decimal sample.

    Args:
        values: Decimal sample.

    Returns:
        Immutable validated values.

    Raises:
        ValueError: If the sample is empty or non-finite.
    """
    logger.debug("Validating Optimization decimal robustness sample")
    sample = tuple(values)
    if not sample or any(not value.is_finite() for value in sample):
        raise ValueError("robustness values must be non-empty and finite")
    return sample


def _draw_path(request: MonteCarloRequest, path_index: int) -> tuple[Decimal, ...]:
    """Draw one deterministic path for the selected method.

    Args:
        request: Validated Monte Carlo request.
        path_index: Zero-based path number.

    Returns:
        One sampled outcome path.

    Raises:
        ValueError: If block-bootstrap policy is unexpectedly absent.
    """
    logger.debug("Drawing Optimization Monte Carlo path %s", path_index)
    rng = random.Random(request.seed + path_index)
    outcomes = list(request.outcomes)
    if request.method is MonteCarloMethod.SHUFFLE_TRADES:
        rng.shuffle(outcomes)
        return tuple(outcomes)
    if request.method is MonteCarloMethod.RESAMPLE_RETURNS:
        return tuple(rng.choice(outcomes) for _ in outcomes)
    block_size = request.block_size
    if block_size is None:
        raise ValueError("block bootstrap requires a block size")
    sampled: list[Decimal] = []
    while len(sampled) < len(outcomes):
        start = rng.randrange(len(outcomes))
        sampled.extend(
            outcomes[(start + offset) % len(outcomes)] for offset in range(block_size)
        )
    return tuple(sampled[: len(outcomes)])


def _path_summary(
    outcomes: Sequence[Decimal], initial_balance: Decimal
) -> tuple[Decimal, Decimal]:
    """Calculate final equity and maximum absolute drawdown for one path.

    Args:
        outcomes: Ordered profit-and-loss outcomes.
        initial_balance: Starting equity.

    Returns:
        Final equity and maximum absolute drawdown.
    """
    logger.debug("Summarizing Optimization Monte Carlo path")
    equity = initial_balance
    peak = initial_balance
    max_drawdown = Decimal(0)
    for outcome in outcomes:
        equity += outcome
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
    return equity, max_drawdown


def calculate_probability_of_ruin(
    values: Sequence[Decimal], *, ruin_threshold: Decimal
) -> float:
    """Calculate the empirical fraction at or below a ruin threshold.

    Args:
        values: Equity or compatible path values.
        ruin_threshold: Explicit ruin boundary in the same unit.

    Returns:
        Empirical ruin probability.

    Raises:
        ValueError: If values or threshold are invalid.
    """
    logger.info("Calculating Optimization probability of ruin")
    sample = _validate_decimal_values(values)
    if not ruin_threshold.is_finite() or ruin_threshold < 0:
        raise ValueError("ruin threshold must be finite and non-negative")
    return sum(value <= ruin_threshold for value in sample) / len(sample)


def _type_seven_quantile(values: Sequence[Decimal], probability: Decimal) -> Decimal:
    """Calculate one deterministic Hyndman-Fan type-seven quantile.

    Args:
        values: Sorted or unsorted Decimal values.
        probability: Decimal quantile probability in the closed unit interval.

    Returns:
        Interpolated quantile.
    """
    logger.debug("Calculating Optimization empirical quantile")
    ordered = sorted(values)
    position = probability * Decimal(len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - Decimal(lower)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def calculate_confidence_intervals(
    values: Sequence[Decimal], *, confidence_level: float
) -> tuple[Decimal, Decimal]:
    """Calculate a central empirical confidence interval.

    Args:
        values: Finite metric samples.
        confidence_level: Central interval probability in ``(0, 1)``.

    Returns:
        Lower and upper type-seven empirical quantiles.

    Raises:
        ValueError: If sample or confidence level is invalid.
    """
    logger.info("Calculating Optimization empirical confidence interval")
    sample = _validate_decimal_values(values)
    if not 0 < confidence_level < 1:
        raise ValueError("confidence level must be between zero and one")
    tail = (Decimal(1) - Decimal(str(confidence_level))) / Decimal(2)
    return (
        _type_seven_quantile(sample, tail),
        _type_seven_quantile(sample, Decimal(1) - tail),
    )


def run_monte_carlo(
    request: MonteCarloRequest, *, max_simulations: int
) -> MonteCarloResult:
    """Run the selected bounded Monte Carlo method deterministically.

    Args:
        request: Validated Monte Carlo request.
        max_simulations: Approved positive path cap.

    Returns:
        Reproducible path summaries and optional requested evidence.

    Raises:
        ValueError: If the cap is invalid or exceeded.
    """
    logger.info("Running bounded Optimization Monte Carlo analysis")
    if max_simulations <= 0 or request.simulations > max_simulations:
        raise ValueError("Monte Carlo simulation cap is invalid or exceeded")
    summaries = tuple(
        _path_summary(_draw_path(request, index), request.initial_balance)
        for index in range(request.simulations)
    )
    final_equity = tuple(item[0] for item in summaries)
    max_drawdowns = tuple(item[1] for item in summaries)
    percentiles: dict[str, Decimal | None] = {}
    if request.confidence_level is not None:
        lower, upper = calculate_confidence_intervals(
            final_equity, confidence_level=request.confidence_level
        )
        percentiles = {"final_equity_lower": lower, "final_equity_upper": upper}
    ruin = (
        None
        if request.ruin_threshold is None
        else calculate_probability_of_ruin(
            final_equity, ruin_threshold=request.ruin_threshold
        )
    )
    return MonteCarloResult(
        method=request.method,
        simulations=request.simulations,
        seed=request.seed,
        sub_seed_policy=_SUB_SEED_POLICY,
        final_equity=final_equity,
        max_drawdowns=max_drawdowns,
        percentiles=percentiles,
        ruin_probability=ruin,
        warnings=("empirical_simulation_not_forecast",),
    )


def run_parametric_simulation(
    *,
    win_rate: Decimal,
    reward_risk: Decimal,
    risk_per_trade: Decimal,
    trade_count: int,
    simulations: int,
    initial_balance: Decimal,
    seed: int,
    max_simulations: int,
) -> MonteCarloResult:
    """Simulate compounding binary outcomes from explicit assumptions.

    Args:
        win_rate: Probability of a winning trade.
        reward_risk: Winning reward per unit risk.
        risk_per_trade: Fraction of current equity risked per trade.
        trade_count: Trades per path.
        simulations: Requested path count.
        initial_balance: Positive starting balance.
        seed: Deterministic root seed.
        max_simulations: Approved positive path cap.

    Returns:
        Reproducible parametric path evidence.

    Raises:
        ValueError: If assumptions or caps are invalid.
    """
    logger.info("Running bounded Optimization parametric simulation")
    if (
        not win_rate.is_finite()
        or not reward_risk.is_finite()
        or not risk_per_trade.is_finite()
        or not initial_balance.is_finite()
        or not 0 <= win_rate <= 1
        or reward_risk < 0
        or not 0 < risk_per_trade < 1
        or trade_count <= 0
        or simulations <= 0
        or simulations > max_simulations
        or max_simulations <= 0
        or initial_balance <= 0
    ):
        raise ValueError("parametric simulation assumptions are invalid")
    final_equity: list[Decimal] = []
    max_drawdowns: list[Decimal] = []
    for path_index in range(simulations):
        rng = random.Random(seed + path_index)
        equity = initial_balance
        peak = initial_balance
        drawdown = Decimal(0)
        for _ in range(trade_count):
            risk = equity * risk_per_trade
            equity += (
                risk * reward_risk if Decimal(str(rng.random())) < win_rate else -risk
            )
            peak = max(peak, equity)
            drawdown = max(drawdown, peak - equity)
        final_equity.append(equity)
        max_drawdowns.append(drawdown)
    return MonteCarloResult(
        method=MonteCarloMethod.RESAMPLE_RETURNS,
        simulations=simulations,
        seed=seed,
        sub_seed_policy=_SUB_SEED_POLICY,
        final_equity=tuple(final_equity),
        max_drawdowns=tuple(max_drawdowns),
        percentiles={},
        ruin_probability=None,
        warnings=("parametric_assumptions_not_forecast",),
    )


__all__ = [
    "calculate_confidence_intervals",
    "calculate_probability_of_ruin",
    "run_monte_carlo",
    "run_parametric_simulation",
]
