"""Equity curve and return series calculations for Analytics.

Implements all metrics and series conversions derived from equity curves.
All functions are stateless kernel functions or official tool wrappers.
No I/O, database mutations, network calls, or broker side effects are
performed.

Module-level constants required by spec:
    NaT: Sentinel for a missing or unparseable timestamp.
    Infinity: Sentinel for a metric that diverges to positive infinity.
    VALIDATION_FAILED: Sentinel error-code string.

Side effects:
    None.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from app.services.analytics._helpers import (
    parse_utc_time,
    to_float_list,
    validate_request_id_strict,
)
from app.utils import (
    VALIDATION_FAILED,
    StandardResponse,
    build_metadata,
    response_from_exception,
    success_response,
)
from app.utils.errors import ValidationError

# Module-level sentinel exports required by spec.
NaT: str = "NaT"
Infinity: float = float("inf")

__all__ = [
    "Infinity",
    "NaT",
    "VALIDATION_FAILED",
    "annualized_return",
    "annual_returns",
    "avg_monthly_return",
    "avg_underwater_drawdown_percent",
    "benchmark_returns",
    "best_return",
    "buy_and_hold_cagr",
    "buy_and_hold_return",
    "cagr",
    "calculate_drawdown_metrics",
    "calculate_equity_metrics",
    "calculate_return_metrics",
    "compound_monthly_growth_rate",
    "compute_equity_metrics",
    "daily_returns",
    "drawdown_duration_series",
    "drawdown_series",
    "geometric_mean_return",
    "log_returns_series",
    "max_drawdown_duration_from_equity",
    "max_strategy_drawdown_date",
    "monthly_return_stddev",
    "monthly_returns",
    "relative_drawdown_series",
    "return_kurtosis",
    "return_on_initial_capital",
    "return_skewness",
    "return_volatility",
    "returns_series",
    "total_return",
    "total_return_usd",
    "weekly_returns",
    "worst_return",
]


# ---------------------------------------------------------------------------
# Internal equity-curve parsing
# ---------------------------------------------------------------------------


def _parse_equity_curve(
    equity_curve: Any,
) -> list[tuple[datetime, float]]:
    """Convert an equity curve input to a sorted list of (datetime, equity) tuples.

    Args:
        equity_curve: Equity curve in any supported format:
            * ``list[dict]`` with ``timestamp``/``equity`` keys.
            * ``list[tuple]`` or ``list[list]`` with (time, value) pairs.
            * Pandas ``DataFrame`` with a ``to_dict`` method.
            * ``None`` — returns empty list.

    Returns:
        Chronologically sorted list of ``(UTC-aware datetime, float)``
        tuples.  Points with un-parseable timestamps are silently skipped.

    Side effects:
        None.
    """
    if equity_curve is None:
        return []
    if hasattr(equity_curve, "to_dict"):
        records = equity_curve.to_dict("records")
    elif isinstance(equity_curve, list):
        records = equity_curve
    else:
        return []

    result: list[tuple[datetime, float]] = []
    for r in records:
        if isinstance(r, dict):
            t_val = (
                r.get("timestamp")
                or r.get("time")
                or r.get("date")
            )
            eq_val = (
                r.get("equity")
                or r.get("balance")
                or r.get("value")
            )
            t_dt = parse_utc_time(t_val)
            if t_dt is not None and eq_val is not None:
                result.append((t_dt, float(eq_val)))
        elif isinstance(r, (tuple, list)) and len(r) >= 2:
            t_dt = parse_utc_time(r[0])
            if t_dt is not None and r[1] is not None:
                result.append((t_dt, float(r[1])))

    result.sort(key=lambda x: x[0])
    return result


# ---------------------------------------------------------------------------
# Core return series kernels
# ---------------------------------------------------------------------------


def returns_series(equity_values: list[float]) -> list[float]:
    """Compute period-over-period simple returns.

    Args:
        equity_values: Chronological equity values.

    Returns:
        List of simple returns; ``[]`` when fewer than 2 values.  A return
        of ``0.0`` is emitted for a zero or negative preceding equity value.

    Side effects:
        None.
    """
    if len(equity_values) < 2:
        return []
    series: list[float] = []
    for i in range(1, len(equity_values)):
        prev = equity_values[i - 1]
        if prev <= 0:
            series.append(0.0)
        else:
            series.append((equity_values[i] - prev) / prev)
    return series


def log_returns_series(equity_values: list[float]) -> list[float]:
    """Compute period-over-period log returns.

    Args:
        equity_values: Chronological equity values.

    Returns:
        List of log returns; ``[]`` when fewer than 2 values.  ``0.0``
        is emitted when either side of a ratio is non-positive.

    Side effects:
        None.
    """
    if len(equity_values) < 2:
        return []
    series: list[float] = []
    for i in range(1, len(equity_values)):
        prev = equity_values[i - 1]
        curr = equity_values[i]
        if prev <= 0 or curr <= 0:
            series.append(0.0)
        else:
            series.append(math.log(curr / prev))
    return series


def geometric_mean_return(returns: list[float]) -> float:
    """Compute the geometric mean of a return series.

    Args:
        returns: Period returns on a decimal scale.

    Returns:
        Decimal geometric mean; ``0.0`` when returns is empty or the
        product of (1 + r) terms is non-positive.

    Side effects:
        None.
    """
    if not returns:
        return 0.0
    product = 1.0
    for r in returns:
        product *= 1.0 + r
    if product <= 0:
        return 0.0
    return math.pow(product, 1.0 / len(returns)) - 1.0


def annualized_return(
    returns: list[float],
    periods_per_year: int = 252,
) -> float:
    """Compute geometric annualised return.

    Args:
        returns: Period returns on a decimal scale.
        periods_per_year: Number of periods per year.

    Returns:
        Annualised return as a percentage; ``0.0`` when returns is empty
        or ``periods_per_year <= 0``.

    Side effects:
        None.
    """
    if not returns or periods_per_year <= 0:
        return 0.0
    geo = geometric_mean_return(returns)
    return (math.pow(1.0 + geo, periods_per_year) - 1.0) * 100.0


def _group_returns(
    equity_curve: Any,
    bucket: str = "daily",
) -> list[float]:
    """Group equity curve by calendar bucket and return period returns.

    Args:
        equity_curve: Equity curve in any supported format.
        bucket: One of ``"daily"``, ``"weekly"``, ``"monthly"``,
            ``"annual"``.

    Returns:
        List of grouped period returns.

    Side effects:
        None.
    """
    parsed = _parse_equity_curve(equity_curve)
    if len(parsed) < 2:
        return []
    grouped: dict[str, float] = {}
    for dt, eq in parsed:
        if bucket == "daily":
            key = dt.strftime("%Y-%m-%d")
        elif bucket == "weekly":
            key = dt.strftime("%Y-%W")
        elif bucket == "monthly":
            key = dt.strftime("%Y-%m")
        else:
            key = dt.strftime("%Y")
        grouped[key] = eq
    sorted_vals = [eq for _, eq in sorted(grouped.items())]
    return returns_series(sorted_vals)


def daily_returns(equity_curve: Any) -> list[float]:
    """Compute daily period returns from an equity curve.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        List of daily returns.

    Side effects:
        None.
    """
    return _group_returns(equity_curve, "daily")


def weekly_returns(equity_curve: Any) -> list[float]:
    """Compute weekly period returns from an equity curve.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        List of weekly returns.

    Side effects:
        None.
    """
    return _group_returns(equity_curve, "weekly")


def monthly_returns(equity_curve: Any) -> list[float]:
    """Compute monthly period returns from an equity curve.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        List of monthly returns.

    Side effects:
        None.
    """
    return _group_returns(equity_curve, "monthly")


def annual_returns(equity_curve: Any) -> list[float]:
    """Compute annual period returns from an equity curve.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        List of annual returns.

    Side effects:
        None.
    """
    return _group_returns(equity_curve, "annual")


def benchmark_returns(price_values: list[float]) -> list[float]:
    """Compute period returns from a price series.

    Args:
        price_values: Chronological price values.

    Returns:
        List of period returns.

    Side effects:
        None.
    """
    return returns_series(price_values)


# ---------------------------------------------------------------------------
# Total return kernels
# ---------------------------------------------------------------------------


def total_return_usd(equity_curve: Any) -> float:
    """Compute absolute return in account currency.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        Ending equity minus starting equity; ``0.0`` when fewer than 2
        data points.

    Side effects:
        None.
    """
    parsed = _parse_equity_curve(equity_curve)
    if len(parsed) < 2:
        return 0.0
    return parsed[-1][1] - parsed[0][1]


def total_return(equity_curve: Any) -> float:
    """Compute total percentage return from an equity curve.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        Total return as a percentage; ``None`` is not returned here — a
        ``ValidationError`` is raised by the official tool when initial
        equity is missing or non-positive.  At the kernel level ``0.0``
        is returned for safety in internal aggregations.

    Side effects:
        None.
    """
    parsed = _parse_equity_curve(equity_curve)
    if len(parsed) < 2 or parsed[0][1] <= 0:
        return 0.0
    return ((parsed[-1][1] - parsed[0][1]) / parsed[0][1]) * 100.0


def return_on_initial_capital(equity_curve: Any) -> float:
    """Alias for ``total_return``.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        Total return percentage.

    Side effects:
        None.
    """
    return total_return(equity_curve)


def buy_and_hold_return(price_values: list[float]) -> float:
    """Compute total buy-and-hold return from a price series.

    Args:
        price_values: Chronological price values.

    Returns:
        Percentage return; ``0.0`` when fewer than 2 values or first
        price is non-positive.

    Side effects:
        None.
    """
    if len(price_values) < 2 or price_values[0] <= 0:
        return 0.0
    return (
        (price_values[-1] - price_values[0]) / price_values[0]
    ) * 100.0


def cagr(
    initial_value: float,
    final_value: float,
    years: float,
) -> float:
    """Compute compound annual growth rate.

    Args:
        initial_value: Starting equity or price.
        final_value: Ending equity or price.
        years: Elapsed years.

    Returns:
        CAGR as a percentage; ``0.0`` when any argument is non-positive.

    Side effects:
        None.
    """
    if initial_value <= 0 or final_value <= 0 or years <= 0:
        return 0.0
    return (math.pow(final_value / initial_value, 1.0 / years) - 1.0) * 100.0


def compound_monthly_growth_rate(
    initial_value: float,
    final_value: float,
    months: float,
) -> float:
    """Compute compound monthly growth rate.

    Args:
        initial_value: Starting equity or price.
        final_value: Ending equity or price.
        months: Elapsed months.

    Returns:
        CMGR as a percentage; ``0.0`` when any argument is non-positive.

    Side effects:
        None.
    """
    if initial_value <= 0 or final_value <= 0 or months <= 0:
        return 0.0
    return (
        math.pow(final_value / initial_value, 1.0 / months) - 1.0
    ) * 100.0


def buy_and_hold_cagr(price_values: list[float], years: float) -> float:
    """Compute buy-and-hold CAGR from price data.

    Args:
        price_values: Chronological price values.
        years: Elapsed years.

    Returns:
        CAGR as a percentage; ``0.0`` when fewer than 2 values.

    Side effects:
        None.
    """
    if len(price_values) < 2:
        return 0.0
    return cagr(price_values[0], price_values[-1], years)


def avg_monthly_return(equity_curve: Any) -> float:
    """Compute arithmetic average monthly return.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        Average monthly return as a percentage; ``0.0`` when no monthly
        data exists.

    Side effects:
        None.
    """
    monthly = monthly_returns(equity_curve)
    if not monthly:
        return 0.0
    return (sum(monthly) / len(monthly)) * 100.0


def monthly_return_stddev(equity_curve: Any) -> float:
    """Compute sample standard deviation of monthly returns.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        Std of monthly returns as a percentage.

    Side effects:
        None.
    """
    monthly = monthly_returns(equity_curve)
    return return_volatility(monthly) * 100.0


def best_return(returns: list[float]) -> float:
    """Find the best single-period return.

    Args:
        returns: Period return series.

    Returns:
        Maximum return; ``0.0`` when series is empty.

    Side effects:
        None.
    """
    return max(returns, default=0.0)


def worst_return(returns: list[float]) -> float:
    """Find the worst single-period return.

    Args:
        returns: Period return series.

    Returns:
        Minimum return; ``0.0`` when series is empty.

    Side effects:
        None.
    """
    return min(returns, default=0.0)


# ---------------------------------------------------------------------------
# Volatility / distribution kernels
# ---------------------------------------------------------------------------


def return_volatility(returns: list[float]) -> float:
    """Compute sample standard deviation of a return series.

    Args:
        returns: Period return series.

    Returns:
        Sample std; ``0.0`` when fewer than 2 returns.

    Side effects:
        None.
    """
    if len(returns) < 2:
        return 0.0
    avg = sum(returns) / len(returns)
    variance = (
        sum((v - avg) ** 2 for v in returns) / (len(returns) - 1)
    )
    return math.sqrt(variance)


def downside_return_volatility(
    returns: list[float],
    target: float = 0.0,
) -> float:
    """Compute volatility of returns below a target.

    Args:
        returns: Period return series.
        target: Minimum acceptable return threshold.

    Returns:
        Std of below-target returns; ``0.0`` when none exist.

    Side effects:
        None.
    """
    downside = [v for v in returns if v < target]
    return return_volatility(downside)


def return_skewness(returns: list[float]) -> float:
    """Compute excess skewness of the return distribution.

    Args:
        returns: Period return series.

    Returns:
        Skewness scalar; ``0.0`` when fewer than 3 returns or zero
        variance.

    Side effects:
        None.
    """
    if len(returns) < 3:
        return 0.0
    avg = sum(returns) / len(returns)
    std = return_volatility(returns)
    if std == 0:
        return 0.0
    return (
        sum(((v - avg) / std) ** 3 for v in returns) / len(returns)
    )


def return_kurtosis(returns: list[float]) -> float:
    """Compute excess kurtosis of the return distribution.

    Args:
        returns: Period return series.

    Returns:
        Excess kurtosis scalar; ``0.0`` when fewer than 4 returns or
        zero variance.

    Side effects:
        None.
    """
    if len(returns) < 4:
        return 0.0
    avg = sum(returns) / len(returns)
    std = return_volatility(returns)
    if std == 0:
        return 0.0
    return (
        sum(((v - avg) / std) ** 4 for v in returns) / len(returns)
    ) - 3.0


# ---------------------------------------------------------------------------
# Drawdown kernels
# ---------------------------------------------------------------------------


def drawdown_series(equity_values: list[float]) -> list[float]:
    """Compute peak-to-trough fractional drawdown series.

    Args:
        equity_values: Chronological equity values.

    Returns:
        Fractional drawdown at each point (0 when at or above peak);
        empty when ``equity_values`` is empty.

    Side effects:
        None.
    """
    if not equity_values:
        return []
    peak = equity_values[0]
    series: list[float] = []
    for eq in equity_values:
        peak = max(peak, eq)
        if peak <= 0:
            series.append(0.0)
        else:
            series.append((peak - eq) / peak)
    return series


def drawdown_duration_series(equity_curve: Any) -> list[float]:
    """Compute hours-since-peak drawdown duration at each equity point.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        Duration in hours since the running peak at each curve point.
        Zero indicates a new high-water mark.

    Side effects:
        None.
    """
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return []
    durations: list[float] = []
    peak = parsed[0][1]
    peak_time = parsed[0][0]
    for dt, eq in parsed:
        if eq >= peak:
            peak = eq
            peak_time = dt
            durations.append(0.0)
        else:
            durations.append(
                (dt - peak_time).total_seconds() / 3600.0
            )
    return durations


def max_drawdown_duration_from_equity(equity_curve: Any) -> float:
    """Find the maximum drawdown duration in hours.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        Maximum hours below peak; ``0.0`` when no drawdown periods.

    Side effects:
        None.
    """
    return max(drawdown_duration_series(equity_curve), default=0.0)


def max_strategy_drawdown_date(equity_curve: Any) -> str:
    """Return the ISO-8601 UTC timestamp at the deepest drawdown trough.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        UTC ISO-8601 timestamp string; fallback sentinel when no data.

    Side effects:
        None.
    """
    _fallback = "1970-01-01T00:00:00+00:00"
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return _fallback
    peak = parsed[0][1]
    max_dd = 0.0
    valley_time = parsed[0][0]
    for dt, eq in parsed:
        peak = max(peak, eq)
        if peak > 0:
            dd = (peak - eq) / peak
            if dd > max_dd:
                max_dd = dd
                valley_time = dt
    return valley_time.isoformat()


def avg_underwater_drawdown_percent(equity_curve: Any) -> float:
    """Compute average drawdown percentage during underwater periods.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        Mean drawdown percentage (0–100); ``0.0`` when never underwater.

    Side effects:
        None.
    """
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return 0.0
    equities = [eq for _, eq in parsed]
    dd_vals = drawdown_series(equities)
    underwater = [d for d in dd_vals if d > 0]
    if not underwater:
        return 0.0
    return (sum(underwater) / len(underwater)) * 100.0


def relative_drawdown_series(
    strategy_equity: list[float],
    benchmark_equity: list[float],
) -> list[float]:
    """Compute the relative drawdown of strategy vs benchmark.

    Args:
        strategy_equity: Chronological strategy equity values.
        benchmark_equity: Chronological benchmark equity values.

    Returns:
        Relative drawdown at each aligned point; ``[]`` when empty.

    Side effects:
        None.
    """
    n = min(len(strategy_equity), len(benchmark_equity))
    if n == 0:
        return []
    strat_ret = [0.0] + returns_series(strategy_equity)
    bench_ret = [0.0] + returns_series(benchmark_equity)
    cum_strat = 1.0
    cum_bench = 1.0
    rel_dd: list[float] = []
    peak_diff = -999.0
    for i in range(n):
        cum_strat *= 1.0 + strat_ret[i]
        cum_bench *= 1.0 + bench_ret[i]
        diff = cum_strat - cum_bench
        peak_diff = max(peak_diff, diff)
        rel_dd.append(max(peak_diff - diff, 0.0))
    return rel_dd


# ---------------------------------------------------------------------------
# Aggregate metric bundles (kernels)
# ---------------------------------------------------------------------------


def calculate_drawdown_metrics(equity_curve: Any) -> dict[str, Any]:
    """Compute a full drawdown metric bundle from an equity curve.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        Dict with ``max_drawdown_percent``, ``max_drawdown_duration_hours``,
        ``avg_underwater_drawdown_percent``, and ``max_drawdown_date``.
        Empty dict when no equity data.

    Side effects:
        None.
    """
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return {}
    equities = [eq for _, eq in parsed]
    dd_vals = drawdown_series(equities)
    max_dd = max(dd_vals, default=0.0)
    durations = drawdown_duration_series(equity_curve)
    max_dur = max(durations, default=0.0)
    underwater = avg_underwater_drawdown_percent(equity_curve)
    return {
        "max_drawdown_percent": max_dd * 100.0,
        "max_drawdown_duration_hours": max_dur,
        "avg_underwater_drawdown_percent": underwater,
        "max_drawdown_date": max_strategy_drawdown_date(equity_curve),
    }


def calculate_return_metrics(equity_curve: Any) -> dict[str, Any]:
    """Compute a return metric bundle from an equity curve.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        Dict with ``total_return_percent``, ``average_return_percent``,
        and ``total_return_usd``.  Empty dict when no equity data.

    Side effects:
        None.
    """
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return {}
    equities = [eq for _, eq in parsed]
    pct_returns = returns_series(equities)
    total_ret = total_return(equity_curve)
    avg_ret = sum(pct_returns) / len(pct_returns) if pct_returns else 0.0
    return {
        "total_return_percent": total_ret,
        "average_return_percent": avg_ret * 100.0,
        "total_return_usd": total_return_usd(equity_curve),
    }


def compute_equity_metrics(returns: list[float]) -> dict[str, Any]:
    """Compute equity metrics from a pre-computed return series.

    Args:
        returns: Decimal period-return series.

    Returns:
        Dict with ``total_return`` and ``return_volatility``; fallback
        zeros when ``returns`` is empty.

    Side effects:
        None.
    """
    if not returns:
        return {"total_return": 0.0, "return_volatility": 0.0}
    eq = [10000.0]
    for r in returns:
        eq.append(eq[-1] * (1.0 + r))
    vol = return_volatility(returns)
    return {
        "total_return": ((eq[-1] - eq[0]) / eq[0]) * 100.0,
        "return_volatility": vol * 100.0,
    }


# ---------------------------------------------------------------------------
# Official tool: calculate_equity_metrics
# ---------------------------------------------------------------------------


def calculate_equity_metrics(
    equity_curve: Any,
    request_id: str | None = None,
) -> StandardResponse:
    """Calculate aggregate return and drawdown metrics from an equity curve.

    Args:
        equity_curve: Equity curve in any supported format.
        request_id: Optional trace identifier.

    Returns:
        ``StandardResponse`` containing equity and drawdown metrics.

    Raises:
        ValidationError: When ``equity_curve`` contains no valid data
            points.  Caught internally and returned as an error response.

    Side effects:
        None.
    """
    validate_request_id_strict(request_id)
    meta = build_metadata(
        tool_name="calculate_equity_metrics",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        parsed = _parse_equity_curve(equity_curve)
        if not parsed:
            raise ValidationError(
                "equity_curve must contain at least one valid data point."
            )
        equities = [eq for _, eq in parsed]
        if not any(eq > 0 for eq in equities):
            raise ValidationError(
                "equity_curve must contain at least one positive equity"
                " value."
            )
        ret_metrics = calculate_return_metrics(equity_curve)
        dd_metrics = calculate_drawdown_metrics(equity_curve)
        pct_returns = returns_series(equities)
        data = {
            "total_return_percent": ret_metrics.get(
                "total_return_percent", 0.0
            ),
            "total_return_usd": ret_metrics.get("total_return_usd", 0.0),
            "average_return_percent": ret_metrics.get(
                "average_return_percent", 0.0
            ),
            "max_drawdown_percent": dd_metrics.get(
                "max_drawdown_percent", 0.0
            ),
            "max_drawdown_duration_hours": dd_metrics.get(
                "max_drawdown_duration_hours", 0.0
            ),
            "avg_underwater_drawdown_percent": dd_metrics.get(
                "avg_underwater_drawdown_percent", 0.0
            ),
            "max_drawdown_date": dd_metrics.get(
                "max_drawdown_date",
                "1970-01-01T00:00:00+00:00",
            ),
            "return_volatility": return_volatility(pct_returns) * 100.0,
            "return_skewness": return_skewness(pct_returns),
            "return_kurtosis": return_kurtosis(pct_returns),
        }
        return success_response(
            message="Successfully calculated equity metrics.",
            data=data,
            metadata=meta,
        )
    except Exception as exc:
        return response_from_exception(exception=exc, metadata=meta)
