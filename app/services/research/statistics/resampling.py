"""Seeded block bootstrap and permutation computations for Research."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from app.utils import ValidationError, logger

if TYPE_CHECKING:
    from app.services.research.contracts import StatisticalConfig


def _sample(values: NDArray[np.floating]) -> NDArray[np.float64]:
    """Validate one finite non-empty numeric sample.

    Args:
        values: Candidate numeric sample.

    Returns:
        Flattened float64 sample.

    Raises:
        ValidationError: If the sample is empty or non-finite.
    """
    logger.debug("Validating Research statistical sample")
    sample = np.asarray(values, dtype="float64").reshape(-1)
    if sample.size == 0:
        raise ValidationError("RES_INSUFFICIENT_DATA", "EMPTY_STATISTICAL_SAMPLE")
    if not np.isfinite(sample).all():
        raise ValidationError("RES_NONFINITE_DATA", "FINITE_SAMPLE_REQUIRED")
    return sample


def block_bootstrap_distribution(
    values: NDArray[np.floating],
    *,
    statistic: Callable[[NDArray[np.float64]], float],
    config: StatisticalConfig,
) -> NDArray[np.float64]:
    """Generate a seeded moving-block bootstrap statistic distribution.

    Args:
        values: Finite one-dimensional observations.
        statistic: Finite scalar statistic callable.
        config: Seed, block size, and iteration policy.

    Returns:
        Float64 bootstrap statistic distribution.

    Raises:
        ValidationError: If sample, block, or statistic is invalid.
    """
    logger.info("Generating Research block-bootstrap distribution")
    sample = _sample(values)
    if config.block_size > sample.size:
        raise ValidationError("RES_INPUT_INVALID", "BLOCK_EXCEEDS_SAMPLE")
    rng = np.random.default_rng(config.seed)
    output = np.empty(config.bootstrap_samples, dtype="float64")
    starts = np.arange(sample.size - config.block_size + 1)
    blocks_needed = int(np.ceil(sample.size / config.block_size))
    for index in range(config.bootstrap_samples):
        chosen = rng.choice(starts, size=blocks_needed, replace=True)
        resample = np.concatenate(
            [sample[start : start + config.block_size] for start in chosen]
        )[: sample.size]
        output[index] = float(statistic(resample))
    if not np.isfinite(output).all():
        raise ValidationError("RES_NONFINITE_DATA", "STATISTIC_NONFINITE")
    return output


def block_bootstrap_ci(
    values: NDArray[np.floating],
    *,
    statistic: Callable[[NDArray[np.float64]], float],
    confidence: float,
    config: StatisticalConfig,
) -> tuple[float, float]:
    """Compute a percentile interval from a seeded bootstrap distribution.

    Args:
        values: Finite observations.
        statistic: Finite scalar statistic callable.
        confidence: Open-unit-interval confidence level.
        config: Statistical settings.

    Returns:
        Lower and upper percentile interval.

    Raises:
        ValidationError: If confidence, sample, or statistic is invalid.
    """
    logger.info("Computing Research bootstrap confidence interval")
    if not 0.0 < confidence < 1.0:
        raise ValidationError("RES_INPUT_INVALID", "INVALID_CONFIDENCE")
    distribution = block_bootstrap_distribution(
        values, statistic=statistic, config=config
    )
    tail = (1.0 - confidence) / 2.0
    lower, upper = np.quantile(distribution, [tail, 1.0 - tail])
    return float(lower), float(upper)


def permutation_test(
    observed: float,
    samples: NDArray[np.floating],
    *,
    alternative: str,
    config: StatisticalConfig,
) -> float:
    """Compute a seeded empirical sign-permutation p-value.

    Args:
        observed: Observed scalar statistic.
        samples: Finite observation sample.
        alternative: ``upper``, ``lower``, or ``two-sided``.
        config: Seed and permutation count.

    Returns:
        Corrected finite empirical p-value in [0, 1].

    Raises:
        ValidationError: If inputs or alternative are invalid.
    """
    logger.info("Computing Research permutation p-value")
    sample = _sample(samples)
    if not np.isfinite(observed) or alternative not in {"upper", "lower", "two-sided"}:
        raise ValidationError("RES_INPUT_INVALID", "INVALID_PERMUTATION_POLICY")
    rng = np.random.default_rng(config.seed)
    distribution = np.empty(config.permutation_samples, dtype="float64")
    for index in range(config.permutation_samples):
        signs = rng.choice(np.asarray([-1.0, 1.0]), size=sample.size)
        distribution[index] = float(np.mean(sample * signs))
    if alternative == "upper":
        exceed = int(np.sum(distribution >= observed))
    elif alternative == "lower":
        exceed = int(np.sum(distribution <= observed))
    else:
        exceed = int(np.sum(np.abs(distribution) >= abs(observed)))
    return float((exceed + 1) / (distribution.size + 1))


__all__ = ("block_bootstrap_ci", "block_bootstrap_distribution", "permutation_test")
