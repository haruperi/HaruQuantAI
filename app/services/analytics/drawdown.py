"""Drawdown metrics calculations for Analytics.

Implements all metrics, statistics, and indices based on drawdown series.
All functions are stateless kernel functions or official tool wrappers.
No I/O, database mutations, network calls, or broker side effects are
performed.

Side effects:
    None.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

from app.services.analytics._helpers import validate_request_id_strict
from app.services.analytics.equity import (
    _parse_equity_curve,
    drawdown_duration_series,
    drawdown_series,
    relative_drawdown_series,
)
from app.utils import (
    StandardResponse,
    build_metadata,
    response_from_exception,
    success_response,
)
from app.utils.errors import ValidationError


# ---------------------------------------------------------------------------
# Core drawdown kernels
# ---------------------------------------------------------------------------


def max_strategy_drawdown(equity_curve: Any) -> float:
    """Compute maximum absolute (currency) drawdown from equity curve.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        Maximum peak-to-trough decline in account currency; ``0.0`` when
        no equity data exists.

    Side effects:
        None.
    """
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return 0.0
    peak = parsed[0][1]
    max_dd = 0.0
    for _, eq in parsed:
        peak = max(peak, eq)
        max_dd = max(max_dd, peak - eq)
    return max_dd


def max_strategy_drawdown_percent(equity_curve: Any) -> float:
    """Compute maximum percentage drawdown from equity curve.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        Maximum peak-to-trough percentage decline (0–100); ``0.0`` when
        no equity data exists.

    Side effects:
        None.
    """
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return 0.0
    peak = parsed[0][1]
    max_dd = 0.0
    for _, eq in parsed:
        peak = max(peak, eq)
        if peak > 0:
            max_dd = max(max_dd, (peak - eq) / peak)
    return max_dd * 100.0


def max_relative_drawdown_percent(
    strategy_equity: list[float],
    benchmark_equity: list[float],
) -> float:
    """Compute maximum relative drawdown of strategy versus benchmark.

    Args:
        strategy_equity: Chronological strategy equity values.
        benchmark_equity: Chronological benchmark equity values.

    Returns:
        Maximum relative drawdown as a percentage; ``0.0`` when no data.

    Side effects:
        None.
    """
    rel_dd = relative_drawdown_series(strategy_equity, benchmark_equity)
    return max(rel_dd, default=0.0) * 100.0


def max_drawdown(returns: list[float]) -> float:
    """Compute maximum drawdown from a return series.

    Args:
        returns: Decimal period-return series.

    Returns:
        Maximum drawdown as a percentage; ``0.0`` when returns is empty.

    Side effects:
        None.
    """
    if not returns:
        return 0.0
    eq = [10000.0]
    for r in returns:
        eq.append(eq[-1] * (1.0 + r))
    dds = drawdown_series(eq)
    return max(dds, default=0.0) * 100.0


def avg_drawdown(equity_curve: Any) -> float:
    """Compute average percentage drawdown across all underwater periods.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        Average drawdown as a percentage; ``0.0`` when never underwater.

    Side effects:
        None.
    """
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return 0.0
    equities = [eq for _, eq in parsed]
    dds = drawdown_series(equities)
    active_dds = [d for d in dds if d > 0]
    if not active_dds:
        return 0.0
    return (sum(active_dds) / len(active_dds)) * 100.0


def drawdown_distribution(equity_curve: Any) -> dict[str, float]:
    """Compute descriptive statistics of the drawdown distribution.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        Dict with ``mean``, ``std``, ``50th``, ``90th``, ``95th``,
        ``99th`` percentile drawdowns.  Empty dict when no equity data.

    Side effects:
        None.
    """
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return {}
    equities = [eq for _, eq in parsed]
    dds = [d * 100.0 for d in drawdown_series(equities)]
    if not dds:
        return {}
    sorted_dds = sorted(dds)
    n = len(sorted_dds)
    mean = sum(dds) / n
    return {
        "mean": mean,
        "std": math.sqrt(
            sum((x - mean) ** 2 for x in dds) / max(n - 1, 1)
        ),
        "50th": sorted_dds[int(n * 0.50)],
        "90th": sorted_dds[int(n * 0.90)],
        "95th": sorted_dds[int(n * 0.95)],
        "99th": sorted_dds[int(n * 0.99)],
    }


def max_drawdown_duration_from_returns(returns: list[float]) -> float:
    """Compute maximum drawdown duration in hours from a return series.

    Args:
        returns: Decimal period-return series.

    Returns:
        Maximum drawdown duration in hours; ``0.0`` when returns is empty.

    Side effects:
        None.
    """
    if not returns:
        return 0.0
    eq = [10000.0]
    for r in returns:
        eq.append(eq[-1] * (1.0 + r))
    eq_curve = [
        (datetime.fromtimestamp(i * 3600, UTC), eq[i])
        for i in range(len(eq))
    ]
    return max(drawdown_duration_series(eq_curve), default=0.0)


def max_drawdown_duration(equity_curve: Any) -> float:
    """Compute maximum drawdown duration in hours from an equity curve.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        Maximum duration in hours; ``0.0`` when no drawdown periods.

    Side effects:
        None.
    """
    return max(drawdown_duration_series(equity_curve), default=0.0)


def avg_drawdown_duration(equity_curve: Any) -> float:
    """Compute average drawdown-episode length in hours.

    An episode is a contiguous sequence of points below the running peak.
    The episode length is the time from peak to trough.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        Average episode duration in hours; ``0.0`` when no drawdown
        episodes exist.

    Side effects:
        None.
    """
    parsed = _parse_equity_curve(equity_curve)
    if len(parsed) < 2:
        return 0.0
    durations = drawdown_duration_series(equity_curve)
    episodes: list[float] = []
    in_episode = False
    episode_max = 0.0
    for d in durations:
        if d > 0:
            in_episode = True
            episode_max = max(episode_max, d)
        elif in_episode:
            episodes.append(episode_max)
            in_episode = False
            episode_max = 0.0
    if in_episode:
        episodes.append(episode_max)
    return sum(episodes) / len(episodes) if episodes else 0.0


def time_to_recovery(equity_curve: Any) -> list[float]:
    """Compute recovery time (hours) for each drawdown episode.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        List of recovery times in hours; ``[]`` when fewer than 2 points.

    Side effects:
        None.
    """
    parsed = _parse_equity_curve(equity_curve)
    if len(parsed) < 2:
        return []
    recovery_times: list[float] = []
    peak = parsed[0][1]
    peak_time = parsed[0][0]
    in_drawdown = False
    for dt, eq in parsed[1:]:
        if eq >= peak:
            if in_drawdown:
                recovery_times.append(
                    (dt - peak_time).total_seconds() / 3600.0
                )
                in_drawdown = False
            peak = eq
            peak_time = dt
        else:
            in_drawdown = True
    return recovery_times


def recovery_factor(
    net_profit: float,
    max_drawdown_val: float,
) -> float:
    """Compute the recovery factor (net profit / max drawdown).

    Args:
        net_profit: Net profit in account currency.
        max_drawdown_val: Maximum drawdown value (same units).

    Returns:
        Recovery factor; ``0.0`` when ``max_drawdown_val <= 0``.

    Side effects:
        None.
    """
    if max_drawdown_val <= 0:
        return 0.0
    return net_profit / max_drawdown_val


def max_close_to_close_drawdown_percent(
    trades: list[dict[str, Any]],
    initial_balance: float = 10000.0,
) -> float:
    """Compute max close-to-close drawdown percentage from trade list.

    Args:
        trades: List of trade record dicts.
        initial_balance: Starting account balance.

    Returns:
        Maximum drawdown percentage; ``0.0`` when no trades.

    Side effects:
        None.
    """
    from app.services.analytics.trade import balance_curve

    curve = balance_curve(trades, initial_balance)
    equities = [c["equity"] for c in curve]
    dds = drawdown_series(equities)
    return max(dds, default=0.0) * 100.0


def account_size_required(
    trades: list[dict[str, Any]],
    initial_balance: float = 10000.0,
) -> float:
    """Estimate minimum account size to avoid margin calls.

    Args:
        trades: List of trade record dicts.
        initial_balance: Starting account balance.

    Returns:
        Required account size in account currency.

    Side effects:
        None.
    """
    from app.services.analytics.trade import balance_curve

    curve = balance_curve(trades, initial_balance)
    max_dd_usd = max_strategy_drawdown(curve)
    return initial_balance + max_dd_usd


def avg_yearly_max_drawdown(equity_curve: Any) -> float:
    """Compute average of per-year maximum drawdowns.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        Average yearly max drawdown percentage; ``0.0`` when no equity data.

    Side effects:
        None.
    """
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return 0.0
    by_year: dict[int, list[tuple[datetime, float]]] = {}
    for dt, eq in parsed:
        by_year.setdefault(dt.year, []).append((dt, eq))
    yearly_dds = [max_strategy_drawdown_percent(curve) for curve in by_year.values()]
    return sum(yearly_dds) / len(yearly_dds) if yearly_dds else 0.0


def ulcer_index(equity_curve: Any) -> float:
    """Compute the Ulcer Index from an equity curve.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        Ulcer Index percentage; ``0.0`` when no equity data.

    Side effects:
        None.
    """
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return 0.0
    equities = [eq for _, eq in parsed]
    dds = drawdown_series(equities)
    if not dds:
        return 0.0
    return math.sqrt(sum(d ** 2 for d in dds) / len(dds)) * 100.0


def pain_index(equity_curve: Any) -> float:
    """Compute the Pain Index from an equity curve.

    Args:
        equity_curve: Equity curve in any supported format.

    Returns:
        Pain Index percentage; ``0.0`` when no equity data.

    Side effects:
        None.
    """
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return 0.0
    equities = [eq for _, eq in parsed]
    dds = drawdown_series(equities)
    if not dds:
        return 0.0
    return (sum(dds) / len(dds)) * 100.0


def pain_ratio(
    annualized_ret: float,
    pain_idx: float,
) -> float:
    """Compute the Pain Ratio (annualized return / pain index).

    Args:
        annualized_ret: Annualized return.
        pain_idx: Pain index.

    Returns:
        Pain ratio; ``0.0`` when pain index is non-positive.

    Side effects:
        None.
    """
    if pain_idx <= 0:
        return 0.0
    return annualized_ret / pain_idx


def calmar_ratio(
    annualized_ret: float,
    max_dd: float,
) -> float:
    """Compute the Calmar Ratio (annualized return / max drawdown).

    Args:
        annualized_ret: Annualized return.
        max_dd: Maximum drawdown percentage.

    Returns:
        Calmar ratio; ``0.0`` when max_dd is non-positive.

    Side effects:
        None.
    """
    if max_dd <= 0:
        return 0.0
    return annualized_ret / max_dd


def fouse_ratio(
    annualized_ret: float,
    ulcer_idx: float,
) -> float:
    """Compute the Fouse Ratio (annualized return / ulcer index).

    Args:
        annualized_ret: Annualized return.
        ulcer_idx: Ulcer index.

    Returns:
        Fouse ratio; ``0.0`` when ulcer index is non-positive.

    Side effects:
        None.
    """
    if ulcer_idx <= 0:
        return 0.0
    return annualized_ret / ulcer_idx


def sterling_ratio(
    cagr_val: float,
    avg_yearly_max_dd: float,
) -> float:
    """Compute the Sterling Ratio.

    ``CAGR / (|avg_yearly_max_dd| + 10 %)``

    Args:
        cagr_val: Compound annual growth rate.
        avg_yearly_max_dd: Average yearly maximum drawdown percentage.

    Returns:
        Sterling ratio; ``0.0`` when denominator is non-positive.

    Side effects:
        None.
    """
    denom = abs(avg_yearly_max_dd) + 10.0
    if denom <= 0:
        return 0.0
    return cagr_val / denom


def rina_index(
    select_net_prof: float,
    avg_dd: float,
    time_in_market: float,
) -> float:
    """Compute the RINA Index.

    ``select_net_profit / (avg_drawdown * time_in_market)``

    Args:
        select_net_prof: Trimmed net profit.
        avg_dd: Average drawdown value.
        time_in_market: Fraction or duration of time in market.

    Returns:
        RINA index; ``0.0`` when denominator is non-positive.

    Side effects:
        None.
    """
    denom = avg_dd * time_in_market
    if denom <= 0:
        return 0.0
    return select_net_prof / denom


def net_profit_as_percent_of_max_strategy_drawdown(
    net_prof: float,
    max_dd_usd: float,
) -> float:
    """Express net profit as a percentage of max strategy drawdown.

    Args:
        net_prof: Net profit in account currency.
        max_dd_usd: Maximum strategy drawdown in account currency.

    Returns:
        Ratio * 100; ``0.0`` when max_dd_usd is non-positive.

    Side effects:
        None.
    """
    if max_dd_usd <= 0:
        return 0.0
    return (net_prof / max_dd_usd) * 100.0


def select_net_profit_as_percent_of_max_strategy_drawdown(
    select_net_prof: float,
    max_dd_usd: float,
) -> float:
    """Express trimmed net profit as a percentage of max strategy drawdown.

    Args:
        select_net_prof: Trimmed net profit.
        max_dd_usd: Maximum strategy drawdown in account currency.

    Returns:
        Ratio * 100; ``0.0`` when max_dd_usd is non-positive.

    Side effects:
        None.
    """
    return net_profit_as_percent_of_max_strategy_drawdown(
        select_net_prof, max_dd_usd
    )


def adjusted_net_profit_as_percent_of_max_strategy_drawdown(
    adj_net_prof: float,
    max_dd_usd: float,
) -> float:
    """Express adjusted net profit as a percentage of max strategy drawdown.

    Args:
        adj_net_prof: Adjusted net profit.
        max_dd_usd: Maximum strategy drawdown in account currency.

    Returns:
        Ratio * 100; ``0.0`` when max_dd_usd is non-positive.

    Side effects:
        None.
    """
    return net_profit_as_percent_of_max_strategy_drawdown(
        adj_net_prof, max_dd_usd
    )


def return_on_max_strategy_drawdown(
    total_ret: float,
    max_dd_pct: float,
) -> float:
    """Compute return / max-drawdown ratio.

    Args:
        total_ret: Total return value.
        max_dd_pct: Maximum drawdown percentage.

    Returns:
        Ratio; ``0.0`` when max_dd_pct is non-positive.

    Side effects:
        None.
    """
    if max_dd_pct <= 0:
        return 0.0
    return total_ret / max_dd_pct


def return_on_max_close_to_close_drawdown(
    net_prof: float,
    max_close_dd_usd: float,
) -> float:
    """Compute return / max close-to-close drawdown ratio.

    Args:
        net_prof: Net profit.
        max_close_dd_usd: Maximum close-to-close drawdown.

    Returns:
        Ratio; ``0.0`` when max_close_dd_usd is non-positive.

    Side effects:
        None.
    """
    if max_close_dd_usd <= 0:
        return 0.0
    return net_prof / max_close_dd_usd


def drawdown_probability(
    equity_curve: Any,
    threshold: float,
) -> float:
    """Compute fraction of time spent in drawdown exceeding a threshold.

    Args:
        equity_curve: Equity curve in any supported format.
        threshold: Drawdown threshold percentage.

    Returns:
        Empirical probability in [0, 1]; ``0.0`` when no equity data.

    Side effects:
        None.
    """
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return 0.0
    equities = [eq for _, eq in parsed]
    dds = [d * 100.0 for d in drawdown_series(equities)]
    if not dds:
        return 0.0
    return sum(1 for d in dds if d >= threshold) / len(dds)


# ---------------------------------------------------------------------------
# Official tool: calculate_drawdown_metrics
# ---------------------------------------------------------------------------


def calculate_drawdown_metrics(
    equity_curve: Any,
    request_id: str | None = None,
) -> StandardResponse:
    """Calculate aggregate drawdown metrics from an equity curve.

    Args:
        equity_curve: Equity curve in any supported format.
        request_id: Optional trace identifier.

    Returns:
        ``StandardResponse`` containing drawdown metric data.

    Raises:
        ValidationError: When ``equity_curve`` contains no valid data
            points.  Caught internally and returned as an error response.

    Side effects:
        None.
    """
    validate_request_id_strict(request_id)
    meta = build_metadata(
        tool_name="calculate_drawdown_metrics",
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
        dds = drawdown_series(equities)
        max_dd = max(dds, default=0.0) * 100.0
        durations = drawdown_duration_series(equity_curve)
        max_dur = max(durations, default=0.0)
        avg_dd_pct = avg_drawdown(equity_curve)
        data = {
            "max_drawdown_percent": max_dd,
            "max_drawdown_duration_hours": max_dur,
            "avg_drawdown_percent": avg_dd_pct,
            "avg_drawdown_duration_hours": avg_drawdown_duration(
                equity_curve
            ),
            "ulcer_index": ulcer_index(equity_curve),
            "pain_index": pain_index(equity_curve),
            "drawdown_date": max_strategy_drawdown_date_from_parsed(
                parsed
            ),
        }
        return success_response(
            message="Successfully calculated drawdown metrics.",
            data=data,
            metadata=meta,
        )
    except Exception as exc:
        return response_from_exception(exception=exc, metadata=meta)


def max_strategy_drawdown_date_from_parsed(
    parsed: list[tuple[Any, float]],
) -> str:
    """Extract the ISO-8601 UTC timestamp at the deepest drawdown trough.

    Args:
        parsed: Pre-parsed ``(datetime, equity)`` tuples.

    Returns:
        UTC ISO-8601 timestamp string; fallback sentinel when no data.

    Side effects:
        None.
    """
    _fallback = "1970-01-01T00:00:00+00:00"
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
    return valley_time.isoformat() if hasattr(valley_time, "isoformat") else _fallback
