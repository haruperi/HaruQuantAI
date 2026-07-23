"""Seeded matched null models and summaries for Research."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Literal

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from app.utils import ValidationError, logger

if TYPE_CHECKING:
    from app.services.research.contracts import StatisticalConfig


def _finite(values: object) -> NDArray[np.float64]:
    """Return a finite non-empty float64 vector.

    Args:
        values: Array-like numeric input.

    Returns:
        Validated flattened vector.

    Raises:
        ValidationError: If values are empty or non-finite.
    """
    logger.debug("Validating Research null sample")
    output = np.asarray(values, dtype="float64").reshape(-1)
    if output.size == 0:
        raise ValidationError("RES_INSUFFICIENT_DATA", "EMPTY_NULL_SAMPLE")
    if not np.isfinite(output).all():
        raise ValidationError("RES_NONFINITE_DATA", "FINITE_NULL_SAMPLE_REQUIRED")
    return output


def random_entry_null(
    data: pd.DataFrame,
    *,
    side: Literal["buy", "sell", "mixed"],
    hold_bars: int,
    config: StatisticalConfig,
) -> NDArray[np.float64]:
    """Generate a side- and horizon-matched random-entry log-return null.

    Args:
        data: Frame containing positive close prices.
        side: Buy, sell, or mixed direction.
        hold_bars: Positive holding horizon.
        config: Seed and null sample count.

    Returns:
        Seeded null distribution.

    Raises:
        ValidationError: If policy or data is invalid.
    """
    logger.info("Generating Research random-entry null")
    if "close" not in data or side not in {"buy", "sell", "mixed"}:
        raise ValidationError("RES_INPUT_INVALID", "INVALID_RANDOM_ENTRY_INPUT")
    close = _finite(data["close"])
    if not 0 < hold_bars < close.size or bool((close <= 0).any()):
        raise ValidationError("RES_INPUT_INVALID", "INVALID_HOLD_HORIZON")
    outcomes = np.log(close[hold_bars:] / close[:-hold_bars])
    rng = np.random.default_rng(config.seed)
    sampled = rng.choice(outcomes, size=config.null_samples, replace=True)
    if side == "sell":
        sampled = -sampled
    elif side == "mixed":
        sampled = sampled * rng.choice(np.asarray([-1.0, 1.0]), size=sampled.size)
    return sampled.astype("float64")


def r_space_null(
    samples: NDArray[np.floating], *, config: StatisticalConfig
) -> NDArray[np.float64]:
    """Generate a seeded sign-randomized R-multiple null.

    Args:
        samples: Finite R-multiple observations.
        config: Seed and null count.

    Returns:
        Seeded null distribution.

    Raises:
        ValidationError: If samples are invalid.
    """
    logger.info("Generating Research R-space null")
    values = _finite(samples)
    rng = np.random.default_rng(config.seed)
    sampled = rng.choice(np.abs(values), size=config.null_samples, replace=True)
    return np.asarray(
        sampled * rng.choice(np.asarray([-1.0, 1.0]), size=sampled.size),
        dtype="float64",
    )


def session_randomized_null(
    data: pd.DataFrame, *, session_column: str, config: StatisticalConfig
) -> NDArray[np.float64]:
    """Generate means from seeded within-session return shuffles.

    Args:
        data: Frame containing session tags and ``log_return``.
        session_column: Exact canonical session column.
        config: Seed and null count.

    Returns:
        Null distribution of shuffled overall means.

    Raises:
        ValidationError: If session or return inputs are invalid.
    """
    logger.info("Generating Research within-session null")
    if session_column not in data or "log_return" not in data:
        raise ValidationError("RES_INPUT_INVALID", "SESSION_RETURN_COLUMNS_REQUIRED")
    values = _finite(data["log_return"].dropna())
    if len(values) != int(data["log_return"].notna().sum()):
        raise ValidationError("RES_INPUT_INVALID", "INVALID_SESSION_SAMPLE")
    groups = [
        group["log_return"].dropna().to_numpy(dtype="float64")
        for _, group in data.groupby(session_column, sort=True)
    ]
    if not groups or any(group.size == 0 for group in groups):
        raise ValidationError("RES_INSUFFICIENT_DATA", "EMPTY_SESSION_GROUP")
    rng = np.random.default_rng(config.seed)
    output = np.empty(config.null_samples, dtype="float64")
    for index in range(config.null_samples):
        output[index] = float(
            np.mean(np.concatenate([rng.permutation(group) for group in groups]))
        )
    return output


def shuffle_returns_null(
    returns: pd.Series, *, config: StatisticalConfig
) -> NDArray[np.float64]:
    """Generate seeded means from shuffled return blocks.

    Args:
        returns: Finite return series.
        config: Seed, block size, and null count.

    Returns:
        Null distribution of block-shuffled means.

    Raises:
        ValidationError: If block or sample is invalid.
    """
    logger.info("Generating Research shuffled-return null")
    values = _finite(returns)
    if config.block_size > values.size:
        raise ValidationError("RES_INPUT_INVALID", "BLOCK_EXCEEDS_SAMPLE")
    blocks = [
        values[index : index + config.block_size]
        for index in range(0, values.size, config.block_size)
    ]
    rng = np.random.default_rng(config.seed)
    output = np.empty(config.null_samples, dtype="float64")
    for index in range(config.null_samples):
        order = rng.permutation(len(blocks))
        output[index] = float(
            np.mean(np.concatenate([blocks[position] for position in order]))
        )
    return output


def compute_null_percentile(
    observed: float, distribution: NDArray[np.floating]
) -> float:
    """Compute the inclusive percentile of an observed value.

    Args:
        observed: Finite observed statistic.
        distribution: Finite non-empty null distribution.

    Returns:
        Percentile in [0, 100].

    Raises:
        ValidationError: If input is invalid.
    """
    logger.debug("Computing Research null percentile")
    values = _finite(distribution)
    if not np.isfinite(observed):
        raise ValidationError("RES_NONFINITE_DATA", "OBSERVED_NONFINITE")
    return float(100.0 * np.mean(values <= observed))


def null_distribution_stats(distribution: NDArray[np.floating]) -> Mapping[str, float]:
    """Summarize count, location, dispersion, and fixed quantiles.

    Args:
        distribution: Finite non-empty null distribution.

    Returns:
        Deterministic statistical summary.

    Raises:
        ValidationError: If input is invalid.
    """
    logger.debug("Summarizing Research null distribution")
    values = _finite(distribution)
    return {
        "count": float(values.size),
        "mean": float(values.mean()),
        "std": float(values.std(ddof=0)),
        "q05": float(np.quantile(values, 0.05)),
        "q50": float(np.quantile(values, 0.5)),
        "q95": float(np.quantile(values, 0.95)),
    }


def exceeds_null_threshold(
    observed: float,
    distribution: NDArray[np.floating],
    *,
    quantile: float,
    alternative: str,
) -> bool:
    """Evaluate explicit directional null-threshold exceedance.

    Args:
        observed: Finite observed statistic.
        distribution: Finite null distribution.
        quantile: Open-unit-interval directional quantile.
        alternative: ``upper``, ``lower``, or ``two-sided``.

    Returns:
        Whether the declared threshold is exceeded.

    Raises:
        ValidationError: If policy or data is invalid.
    """
    logger.debug("Evaluating Research null threshold")
    values = _finite(distribution)
    if (
        not np.isfinite(observed)
        or not 0.0 < quantile < 1.0
        or alternative not in {"upper", "lower", "two-sided"}
    ):
        raise ValidationError("RES_INPUT_INVALID", "INVALID_NULL_THRESHOLD_POLICY")
    if alternative == "upper":
        return bool(observed >= np.quantile(values, quantile))
    if alternative == "lower":
        return bool(observed <= np.quantile(values, 1.0 - quantile))
    threshold = np.quantile(np.abs(values), quantile)
    return bool(abs(observed) >= threshold)


__all__ = (
    "compute_null_percentile",
    "exceeds_null_threshold",
    "null_distribution_stats",
    "r_space_null",
    "random_entry_null",
    "session_randomized_null",
    "shuffle_returns_null",
)
