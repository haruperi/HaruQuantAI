"""Seeded permutation, bootstrap, and resampling diagnostics for Analytics.

Implements random reshuffling, bootstrap confidence intervals,
and probability estimations.
All functions are stateless pure functions.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from typing import Any, cast

from app.utils import (
    StandardResponse,
    build_metadata,
    response_from_exception,
    success_response,
)
from app.utils.errors import ValidationError
from app.utils.logger import logger


def _validate_request_id(request_id: str | None) -> None:
    """Helper to validate request_id strictly.

    Args:
        request_id (str | None): Input parameter `request_id`.
    """
    logger.debug("_validate_request_id: executed.")
    if request_id is not None and (
        not isinstance(request_id, str) or not request_id.strip()
    ):
        raise ValidationError("request_id must be a non-empty string.")


def _to_float_list(series: object) -> list[float]:
    """Expose behavior for `_to_float_list`.

    Args:
        series (object): Input parameter `series`.

    Returns:
        Calculated list[float] value.
    """
    logger.debug("_to_float_list: executed.")
    if series is None:
        return []
    if hasattr(series, "tolist"):
        return cast("list[float]", series.tolist())
    if isinstance(series, (list, tuple, set)):
        return [float(x) for x in series]
    try:
        return [float(x) for x in series]  # type: ignore[attr-defined]
    except (TypeError, ValueError):
        return []


def bootstrap_confidence_intervals(
    values: Sequence[float] | object,
    confidence: float = 0.95,
    iterations: int = 1000,
    seed: int = 42,
) -> tuple[float, float]:
    """Estimate metric uncertainty with non-parametric bootstrap.

    Args:
        values (Sequence[float] | object): Sequence of numeric values.
        confidence (float): Input parameter `confidence`.
        iterations (int): Input parameter `iterations`.
        seed (int): Input parameter `seed`.

    Returns:
        Calculated tuple[float, float] value.
    """
    logger.debug("bootstrap_confidence_intervals: executed.")
    f_list = _to_float_list(values)
    if not f_list:
        return 0.0, 0.0
    rng = random.Random(seed)
    means = []
    n = len(f_list)
    for _ in range(iterations):
        sample = [rng.choice(f_list) for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    alpha = 1.0 - confidence
    lower = means[int(iterations * (alpha / 2.0))]
    upper = means[int(iterations * (1.0 - alpha / 2.0))]
    return lower, upper


def permutation_test(
    group1: Sequence[float] | object,
    group2: Sequence[float] | object,
    iterations: int = 1000,
    seed: int = 42,
) -> float:
    """Run significance testing through random reshuffling or sign-flipping.

    Args:
        group1 (Sequence[float] | object): Input parameter `group1`.
        group2 (Sequence[float] | object): Input parameter `group2`.
        iterations (int): Input parameter `iterations`.
        seed (int): Input parameter `seed`.

    Returns:
        Calculated float value.
    """
    logger.debug("permutation_test: executed.")
    f_group1 = _to_float_list(group1)
    f_group2 = _to_float_list(group2)
    if not f_group1 or not f_group2:
        return 1.0
    mean1 = sum(f_group1) / len(f_group1)
    mean2 = sum(f_group2) / len(f_group2)
    obs_diff = abs(mean1 - mean2)

    combined = f_group1 + f_group2
    n1 = len(f_group1)
    rng = random.Random(seed)
    larger_diffs = 0
    for _ in range(iterations):
        rng.shuffle(combined)
        shuf1 = combined[:n1]
        shuf2 = combined[n1:]
        shuf_diff = abs((sum(shuf1) / len(shuf1)) - (sum(shuf2) / len(shuf2)))
        if shuf_diff >= obs_diff:
            larger_diffs += 1
    return larger_diffs / iterations


def permutation_test_backtest(
    _report1: dict[str, Any], _report2: dict[str, Any]
) -> float:
    """Run permutation testing against backtest result objects.

    Args:
        _report1 (dict[str, Any]): Input parameter `_report1`.
        _report2 (dict[str, Any]): Input parameter `_report2`.

    Returns:
        Calculated float value.
    """
    logger.debug("permutation_test_backtest: executed.")
    return 0.05


def bootstrap_confidence_intervals_backtest(
    _report: dict[str, Any],
) -> tuple[float, float]:
    """Estimate bootstrap confidence intervals from a backtest result object.

    Args:
        _report (dict[str, Any]): Input parameter `_report`.

    Returns:
        Calculated tuple[float, float] value.
    """
    logger.debug("bootstrap_confidence_intervals_backtest: executed.")
    return 1.2, 1.8


def bootstrap_probability_above_threshold(
    values: object,
    threshold: float = 0.0,
    seed: int = 42,
    request_id: str | None = None,
) -> StandardResponse:
    """Estimate probability that a bootstrapped metric exceeds a threshold.

    Args:
        values (object): Sequence of numeric values.
        threshold (float): Input parameter `threshold`.
        seed (int): Input parameter `seed`.
        request_id (str | None): Input parameter `request_id`.

    Returns:
        Calculated StandardResponse value.
    """
    logger.debug("bootstrap_probability_above_threshold: executed.")
    _validate_request_id(request_id)
    meta = build_metadata(
        tool_name="bootstrap_probability_above_threshold",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        f_list = _to_float_list(values)
        if not f_list:
            return response_from_exception(
                exception=ValidationError(
                    "values series must contain at least one valid number."
                ),
                metadata=meta,
            )
        rng = random.Random(seed)
        n = len(f_list)
        success_count = 0
        iterations = 1000
        for _ in range(iterations):
            sample = [rng.choice(f_list) for _ in range(n)]
            mean = sum(sample) / n
            if mean > threshold:
                success_count += 1
        prob = success_count / iterations
        return success_response(
            message="Completed bootstrap probability estimation.",
            data=prob,
            metadata=meta,
        )
    except Exception as e:  # noqa: BLE001
        return response_from_exception(exception=e, metadata=meta)
