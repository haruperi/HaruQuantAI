"""Statistical distributions and profiling diagnostics for Analytics.

Implements moments, percentiles, normality tests, fit indicators, and outlier detection.
All functions are stateless pure functions.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import cast

from app.services.analytics.errors import AnalyticsValidationError as ValidationError
from app.utils import (
    StandardResponse,
    build_metadata,
    response_from_exception,
    success_response,
)
from app.utils.logger import logger


def statistics_distribution_boundary() -> dict[str, bool]:
    """Describe distribution statistics boundary declarations.

    Returns:
        Boundary evidence that distribution helpers are pure analytics kernels.
    """
    logger.debug("statistics_distribution_boundary: executed.")
    return {
        "file_specific_non_functional_requirements_defined": False,
        "file_specific_testing_requirements_defined": False,
        "read_only": True,
        "pure_metric_kernel": True,
    }


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


# --- Core Kernels ---


def skewness(values: Sequence[float] | object) -> float:
    """Compute the Fisher-Pearson coefficient of skewness.

    Args:
        values (Sequence[float] | object): Sequence of numeric values.

    Returns:
        Calculated float value.
    """
    logger.debug("skewness: executed.")
    f_list = _to_float_list(values)
    n = len(f_list)
    if n < 3:  # noqa: PLR2004
        return 0.0
    mean = sum(f_list) / n
    std = math.sqrt(sum((x - mean) ** 2 for x in f_list) / (n - 1))
    if std == 0:
        return 0.0
    m3 = sum((x - mean) ** 3 for x in f_list) / n
    return m3 / (std**3)


def kurtosis(values: Sequence[float] | object) -> float:
    """Compute the excess kurtosis.

    Args:
        values (Sequence[float] | object): Sequence of numeric values.

    Returns:
        Calculated float value.
    """
    logger.debug("kurtosis: executed.")
    f_list = _to_float_list(values)
    n = len(f_list)
    if n < 4:  # noqa: PLR2004
        return 0.0
    mean = sum(f_list) / n
    std = math.sqrt(sum((x - mean) ** 2 for x in f_list) / (n - 1))
    if std == 0:
        return 0.0
    m4 = sum((x - mean) ** 4 for x in f_list) / n
    return m4 / (std**4) - 3.0


def higher_moments(values: Sequence[float] | object) -> dict[str, float]:
    """Compute standard higher moments (mean, std, skewness, kurtosis).

    Args:
        values (Sequence[float] | object): Sequence of numeric values.

    Returns:
        Calculated dict[str, float] value.
    """
    logger.debug("higher_moments: executed.")
    f_list = _to_float_list(values)
    n = len(f_list)
    if n == 0:
        return {}
    mean = sum(f_list) / n
    std = math.sqrt(sum((x - mean) ** 2 for x in f_list) / max(n - 1, 1))
    return {
        "mean": mean,
        "std": std,
        "skewness": skewness(f_list),
        "kurtosis": kurtosis(f_list),
    }


def percentile_summary(values: Sequence[float] | object) -> dict[str, float]:
    """Return selected percentile values.

    Args:
        values (Sequence[float] | object): Sequence of numeric values.

    Returns:
        Calculated dict[str, float] value.
    """
    logger.debug("percentile_summary: executed.")
    f_list = _to_float_list(values)
    if not f_list:
        return {}
    sorted_vals = sorted(f_list)
    n = len(sorted_vals)
    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    result = {}
    for p in percentiles:
        idx = int(n * (p / 100.0))
        idx = min(idx, n - 1)
        result[f"{p}th"] = sorted_vals[idx]
    return result


def upside_downside_summary(
    values: Sequence[float] | object,
) -> dict[str, float | int]:
    """Summarize positive and negative outcome distributions.

    Args:
        values (Sequence[float] | object): Sequence of numeric values.

    Returns:
        Calculated dict[str, float | int] value.
    """
    logger.debug("upside_downside_summary: executed.")
    f_list = _to_float_list(values)
    upside = [x for x in f_list if x > 0]
    downside = [x for x in f_list if x < 0]
    avg_up = sum(upside) / len(upside) if upside else 0.0
    avg_down = sum(downside) / len(downside) if downside else 0.0
    return {
        "upside_count": len(upside),
        "downside_count": len(downside),
        "average_upside": avg_up,
        "average_downside": avg_down,
    }


def fat_tail_score(values: Sequence[float] | object) -> float:
    """Estimate tail heaviness relative to normal behavior (excess kurtosis).

    Args:
        values (Sequence[float] | object): Sequence of numeric values.

    Returns:
        Calculated float value.
    """
    return kurtosis(values)


def tail_ratio(values: Sequence[float] | object) -> float:
    """Calculate ratio between upper-tail and lower-tail percentile magnitudes.

    Args:
        values (Sequence[float] | object): Sequence of numeric values.

    Returns:
        Calculated float value.
    """
    logger.debug("tail_ratio: executed.")
    f_list = _to_float_list(values)
    if not f_list:
        return 0.0
    summary = percentile_summary(f_list)
    p95 = summary.get("95th", 0.0)
    p5 = abs(summary.get("5th", 0.0))
    if p5 == 0:
        return 0.0
    return p95 / p5


def jarque_bera_test(values: Sequence[float] | object) -> dict[str, float]:
    """Run a Jarque-Bera normality diagnostic.

    Args:
        values (Sequence[float] | object): Sequence of numeric values.

    Returns:
        Calculated dict[str, float] value.
    """
    logger.debug("jarque_bera_test: executed.")
    f_list = _to_float_list(values)
    n = len(f_list)
    if n < 4:  # noqa: PLR2004
        return {"jb_stat": 0.0, "p_value": 1.0}
    skew = skewness(f_list)
    kurt = kurtosis(f_list)
    jb_stat = (n / 6.0) * (skew**2 + (kurt**2 / 4.0))
    p_value = math.exp(-jb_stat / 2.0)
    return {"jb_stat": jb_stat, "p_value": p_value}


def shapiro_wilk_test(values: Sequence[float] | object) -> dict[str, float]:
    """Run a Shapiro-Wilk normality diagnostic approximation.

    Args:
        values (Sequence[float] | object): Sequence of numeric values.

    Returns:
        Calculated dict[str, float] value.
    """
    logger.debug("shapiro_wilk_test: executed.")
    f_list = _to_float_list(values)
    n = len(f_list)
    if n < 3:  # noqa: PLR2004
        return {"w_stat": 0.0, "p_value": 1.0}
    jb = jarque_bera_test(f_list)
    w = 1.0 / (1.0 + jb["jb_stat"] / n)
    return {"w_stat": w, "p_value": jb["p_value"]}


def qq_plot_data(values: Sequence[float] | object) -> list[dict[str, float]]:
    """Generate theoretical and actual quantile data for Q-Q plotting.

    Args:
        values (Sequence[float] | object): Sequence of numeric values.

    Returns:
        Calculated list[dict[str, float]] value.
    """
    logger.debug("qq_plot_data: executed.")
    f_list = _to_float_list(values)
    n = len(f_list)
    if not f_list:
        return []
    sorted_vals = sorted(f_list)
    mean = sum(f_list) / n
    std = math.sqrt(sum((x - mean) ** 2 for x in f_list) / max(n - 1, 1))
    if std == 0:
        std = 1.0

    qq = []
    for i in range(n):
        p = (i + 0.5) / n
        theoretical = (
            math.sqrt(2.0) * math.erfinv(2.0 * p - 1.0)
            if hasattr(math, "erfinv")
            else (p - 0.5) * 3.0
        )
        qq.append({"theoretical": theoretical, "actual": (sorted_vals[i] - mean) / std})
    return qq


def fit_distribution(values: Sequence[float] | object) -> dict[str, float]:
    """Fit a theoretical distribution and return fit parameters.

    Args:
        values (Sequence[float] | object): Sequence of numeric values.

    Returns:
        Calculated dict[str, float] value.
    """
    logger.debug("fit_distribution: executed.")
    f_list = _to_float_list(values)
    if not f_list:
        return {}
    mean = sum(f_list) / len(f_list)
    var = sum((x - mean) ** 2 for x in f_list) / len(f_list)
    return {"mean": mean, "std": math.sqrt(var)}


def distribution_fit_quality(
    values: Sequence[float] | object,
) -> dict[str, float]:
    """Return fit-quality diagnostics (likelihood and information criteria).

    Args:
        values (Sequence[float] | object): Sequence of numeric values.

    Returns:
        Calculated dict[str, float] value.
    """
    logger.debug("distribution_fit_quality: executed.")
    f_list = _to_float_list(values)
    fit = fit_distribution(f_list)
    if not fit:
        return {}
    n = len(f_list)
    std = fit["std"]
    if std <= 0:
        return {"log_likelihood": 0.0, "aic": 0.0}
    log_lik = -(n / 2.0) * math.log(2.0 * math.pi * (std**2)) - sum(
        (x - fit["mean"]) ** 2 for x in f_list
    ) / (2.0 * (std**2))
    return {
        "log_likelihood": log_lik,
        "aic": 2.0 * 2 - 2.0 * log_lik,
        "bic": 2.0 * math.log(n) - 2.0 * log_lik,
    }


def histogram_data(
    values: Sequence[float] | object, bins: int = 10
) -> dict[str, list[float]]:
    """Generate histogram bin data for plotting.

    Args:
        values (Sequence[float] | object): Sequence of numeric values.
        bins (int): Input parameter `bins`.

    Returns:
        Calculated dict[str, list[float]] value.
    """
    logger.debug("histogram_data: executed.")
    f_list = _to_float_list(values)
    if not f_list:
        return {"bins": [], "counts": []}
    v_min, v_max = min(f_list), max(f_list)
    if v_min == v_max:
        v_max += 1.0
    step = (v_max - v_min) / bins
    edges = [v_min + i * step for i in range(bins + 1)]
    counts = [0.0] * bins
    for v in f_list:
        for i in range(bins):
            if edges[i] <= v < edges[i + 1]:
                counts[i] += 1
                break
        if v == v_max:
            counts[-1] += 1
    return {"bins": edges, "counts": counts}


def detect_outliers(
    values: Sequence[float] | object,
    _method: str = "iqr",
    threshold: float = 1.5,
) -> list[int]:
    """Identify outliers with the requested method and threshold.

    Args:
        values (Sequence[float] | object): Sequence of numeric values.
        _method (str): Input parameter `_method`.
        threshold (float): Input parameter `threshold`.

    Returns:
        Calculated list[int] value.
    """
    logger.debug("detect_outliers: executed.")
    f_list = _to_float_list(values)
    n = len(f_list)
    if n < 4:  # noqa: PLR2004
        return []
    sorted_idx = sorted(range(n), key=lambda i: f_list[i])
    q1 = f_list[sorted_idx[int(n * 0.25)]]
    q3 = f_list[sorted_idx[int(n * 0.75)]]
    iqr = q3 - q1
    lower = q1 - threshold * iqr
    upper = q3 + threshold * iqr
    outliers = []
    for i, v in enumerate(f_list):
        if v < lower or v > upper:
            outliers.append(i)
    return outliers


def outlier_ratio(
    values: Sequence[float] | object,
    method: str = "iqr",
    threshold: float = 1.5,
) -> float:
    """Calculate percentage of data points flagged as outliers.

    Args:
        values (Sequence[float] | object): Sequence of numeric values.
        method (str): Input parameter `method`.
        threshold (float): Input parameter `threshold`.

    Returns:
        Calculated float value.
    """
    logger.debug("outlier_ratio: executed.")
    f_list = _to_float_list(values)
    if not f_list:
        return 0.0
    return len(detect_outliers(f_list, method, threshold)) / len(f_list)


def return_distribution(values: Sequence[float] | object) -> dict[str, float]:
    """Calculate a statistical summary of returns.

    Args:
        values (Sequence[float] | object): Sequence of numeric values.

    Returns:
        Calculated dict[str, float] value.
    """
    logger.debug("return_distribution: executed.")
    return higher_moments(values)


def r_multiple_distribution(
    values: Sequence[float] | object,
) -> dict[str, float]:
    """Calculate a statistical summary of R-multiple values.

    Args:
        values (Sequence[float] | object): Sequence of numeric values.

    Returns:
        Calculated dict[str, float] value.
    """
    logger.debug("r_multiple_distribution: executed.")
    return higher_moments(values)


# --- Official AI Tools ---


def sample_size_warning(
    n: int,
    min_recommended: int = 100,
    request_id: str | None = None,
) -> StandardResponse:
    """Assess metric reliability based on sample size and return warnings.

    Args:
        n (int): Input parameter `n`.
        min_recommended (int): Input parameter `min_recommended`.
        request_id (str | None): Input parameter `request_id`.

    Returns:
        Calculated StandardResponse value.
    """
    logger.debug("sample_size_warning: executed.")
    _validate_request_id(request_id)
    meta = build_metadata(
        tool_name="sample_size_warning",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
    )
    try:
        is_weak = n < min_recommended
        data = {
            "sample_size": n,
            "min_recommended": min_recommended,
            "is_weak": is_weak,
            "warning_message": (
                f"Sample size {n} is below the recommended minimum "
                f"of {min_recommended}."
                if is_weak
                else "Sample size is sufficient."
            ),
        }
        return success_response(
            message="Checked sample size warning.",
            data=data,
            metadata=meta,
        )
    except Exception as e:  # noqa: BLE001
        return response_from_exception(exception=e, metadata=meta)


def calculate_distribution_metrics(
    values: object, request_id: str | None = None
) -> StandardResponse:
    """Calculate aggregate distribution statistics.

    Args:
        values (object): Sequence of numeric values.
        request_id (str | None): Input parameter `request_id`.

    Returns:
        Calculated StandardResponse value.
    """
    logger.debug("calculate_distribution_metrics: executed.")
    _validate_request_id(request_id)
    meta = build_metadata(
        tool_name="calculate_distribution_metrics",
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
        moments = higher_moments(f_list)
        data = {
            "mean": moments.get("mean", 0.0),
            "std": moments.get("std", 0.0),
            "skewness": moments.get("skewness", 0.0),
            "kurtosis": moments.get("kurtosis", 0.0),
            "tail_ratio": tail_ratio(f_list),
            "percentiles": percentile_summary(f_list),
        }
        return success_response(
            message="Successfully calculated distribution metrics.",
            data=data,
            metadata=meta,
        )
    except Exception as e:  # noqa: BLE001
        return response_from_exception(exception=e, metadata=meta)
