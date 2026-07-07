"""Benchmark comparison metrics for Analytics.

Implements Beta, Alpha, R-Squared, Tracking Error,
Information Ratios, and capture ratios relative to benchmark returns.
All functions are stateless pure functions.
"""

from __future__ import annotations

import math

from app.services.analytics.benchmarks.alignment import _align_series
from app.utils import (
    StandardResponse,
    build_metadata,
    response_from_exception,
    success_response,
)
from app.utils.errors import ValidationError


def _validate_request_id(request_id: str | None) -> None:
    """Helper to validate request_id strictly."""
    if request_id is not None and (
        not isinstance(request_id, str) or not request_id.strip()
    ):
        raise ValidationError("request_id must be a non-empty string.")


def beta(strategy_returns: object, benchmark_returns: object) -> float:
    """Calculate the strategy beta coefficient relative to benchmark returns."""
    s_aligned, b_aligned = _align_series(strategy_returns, benchmark_returns)
    n = len(s_aligned)
    if n < 2:  # noqa: PLR2004
        return 1.0
    mean_s = sum(s_aligned) / n
    mean_b = sum(b_aligned) / n
    cov = sum(
        (s_aligned[i] - mean_s) * (b_aligned[i] - mean_b) for i in range(n)
    ) / (n - 1)
    var_b = sum((b_aligned[i] - mean_b) ** 2 for i in range(n)) / (n - 1)
    if var_b == 0:
        return 1.0
    return cov / var_b


def alpha(
    strategy_returns: object,
    benchmark_returns: object,
    risk_free_rate: float = 0.0,
) -> float:
    """Calculate annualized Jensen-style alpha relative to benchmark returns."""
    s_aligned, b_aligned = _align_series(strategy_returns, benchmark_returns)
    n = len(s_aligned)
    if n == 0:
        return 0.0
    b_coef = beta(s_aligned, b_aligned)
    mean_s = sum(s_aligned) / n
    mean_b = sum(b_aligned) / n
    # Annualize Jensen's Alpha assuming daily returns
    # Alpha = E(R_s) - [R_f + Beta * (E(R_b) - R_f)]
    # Daily alpha:
    daily_alpha = mean_s - (
        risk_free_rate / 252.0
        + b_coef * (mean_b - risk_free_rate / 252.0)
    )
    return daily_alpha * 252.0 * 100.0


def r_squared(strategy_returns: object, benchmark_returns: object) -> float:
    """Calculate coefficient of determination between strategy and benchmark returns."""
    s_aligned, b_aligned = _align_series(strategy_returns, benchmark_returns)
    n = len(s_aligned)
    if n < 2:  # noqa: PLR2004
        return 0.0
    mean_s = sum(s_aligned) / n
    mean_b = sum(b_aligned) / n
    cov = sum(
        (s_aligned[i] - mean_s) * (b_aligned[i] - mean_b) for i in range(n)
    ) / (n - 1)
    var_s = sum((s_aligned[i] - mean_s) ** 2 for i in range(n)) / (n - 1)
    var_b = sum((b_aligned[i] - mean_b) ** 2 for i in range(n)) / (n - 1)
    if var_s == 0 or var_b == 0:
        return 0.0
    r = cov / (math.sqrt(var_s) * math.sqrt(var_b))
    return r**2


def tracking_error(strategy_returns: object, benchmark_returns: object) -> float:
    """Calculate annualized tracking error between strategy and benchmark returns."""
    s_aligned, b_aligned = _align_series(strategy_returns, benchmark_returns)
    n = len(s_aligned)
    if n < 2:  # noqa: PLR2004
        return 0.0
    diff = [s_aligned[i] - b_aligned[i] for i in range(n)]
    mean_diff = sum(diff) / n
    var_diff = sum((x - mean_diff) ** 2 for x in diff) / (n - 1)
    # Annualized tracking error
    return math.sqrt(var_diff) * math.sqrt(252) * 100.0


def information_ratio(
    strategy_returns: object, benchmark_returns: object
) -> float:
    """Calculate relative Sharpe-style information ratio."""
    s_aligned, b_aligned = _align_series(strategy_returns, benchmark_returns)
    n = len(s_aligned)
    if n < 2:  # noqa: PLR2004
        return 0.0
    diff = [s_aligned[i] - b_aligned[i] for i in range(n)]
    mean_diff = sum(diff) / n
    var_diff = sum((x - mean_diff) ** 2 for x in diff) / (n - 1)
    std_diff = math.sqrt(var_diff)
    if std_diff == 0:
        return 0.0
    # Annualized Information Ratio
    return (mean_diff / std_diff) * math.sqrt(252)


def batting_average(strategy_returns: object, benchmark_returns: object) -> float:
    """Calculate the percentage of periods where strategy outperformed benchmark."""
    s_aligned, b_aligned = _align_series(strategy_returns, benchmark_returns)
    n = len(s_aligned)
    if n == 0:
        return 0.0
    wins = sum(1 for i in range(n) if s_aligned[i] > b_aligned[i])
    return wins / n


def up_down_capture(
    strategy_returns: object,
    benchmark_returns: object,
) -> dict[str, float]:
    """Calculate up-capture and down-capture ratios."""
    s_aligned, b_aligned = _align_series(strategy_returns, benchmark_returns)
    up_pairs = [
        (s_ret, b_ret)
        for s_ret, b_ret in zip(s_aligned, b_aligned, strict=False)
        if b_ret > 0
    ]
    down_pairs = [
        (s_ret, b_ret)
        for s_ret, b_ret in zip(s_aligned, b_aligned, strict=False)
        if b_ret < 0
    ]
    up_benchmark = sum(b_ret for _, b_ret in up_pairs)
    down_benchmark = sum(b_ret for _, b_ret in down_pairs)
    return {
        "up_capture": (
            sum(s_ret for s_ret, _ in up_pairs) / up_benchmark
            if up_benchmark != 0
            else 0.0
        ),
        "down_capture": (
            sum(s_ret for s_ret, _ in down_pairs) / down_benchmark
            if down_benchmark != 0
            else 0.0
        ),
    }


# --- Official AI Tools ---


def calculate_benchmark_metrics(
    strategy_returns: object,
    benchmark_returns: object,
    request_id: str | None = None,
) -> StandardResponse:
    """Calculate combined benchmark-relative metrics (alpha, beta, IR)."""
    _validate_request_id(request_id)
    meta = build_metadata(
        tool_name="calculate_benchmark_metrics",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        s_aligned, b_aligned = _align_series(strategy_returns, benchmark_returns)
        if not s_aligned:
            return response_from_exception(
                exception=ValidationError(
                    "Aligned returns series must contain at least one valid data point."
                ),
                metadata=meta,
            )

        data = {
            "beta": beta(s_aligned, b_aligned),
            "alpha_percent": alpha(s_aligned, b_aligned),
            "r_squared": r_squared(s_aligned, b_aligned),
            "tracking_error_percent": tracking_error(s_aligned, b_aligned),
            "information_ratio": information_ratio(s_aligned, b_aligned),
            "batting_average": batting_average(s_aligned, b_aligned),
            "capture": up_down_capture(s_aligned, b_aligned),
        }
        return success_response(
            message="Successfully calculated benchmark metrics.",
            data=data,
            metadata=meta,
        )
    except Exception as e:  # noqa: BLE001
        return response_from_exception(exception=e, metadata=meta)
