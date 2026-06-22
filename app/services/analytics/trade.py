"""Trade metrics calculations for Analytics.

Implements all metrics, statistics, and calculations derived from trade
history logs.  All functions are stateless kernel functions or official
tool wrappers.  No I/O, database mutations, network calls, or broker
side effects are performed.

Side effects:
    None.
"""

from __future__ import annotations

import math
import random as _random_module
from typing import Any

from app.services.analytics._helpers import (
    parse_utc_time,
    to_trade_list,
    validate_request_id_strict,
)
from app.services.analytics.models import AnalyticsConfig
from app.utils import (
    StandardResponse,
    build_metadata,
    response_from_exception,
    success_response,
)
from app.utils.errors import ValidationError

_DEFAULT_CONFIG = AnalyticsConfig()
_RNG = _random_module.Random(42)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_trade_pnl(trade: dict[str, Any]) -> float:
    """Extract the net PnL value from a trade record.

    Args:
        trade: Single trade record dict.

    Returns:
        Float PnL; ``0.0`` when no recognised PnL key is present.

    Side effects:
        None.
    """
    for key in (
        "net_pnl",
        "profit_loss",
        "pnl",
        "profit",
        "profit_loss_usd",
    ):
        if key in trade:
            val = trade[key]
            if val is not None:
                return float(val)
    return 0.0


def _get_trade_duration(trade: dict[str, Any]) -> float:
    """Calculate trade duration in hours from open/close timestamps.

    Args:
        trade: Single trade record dict.

    Returns:
        Duration in hours; ``0.0`` when timestamps are missing or invalid.

    Side effects:
        None.
    """
    ot = parse_utc_time(
        trade.get("open_time") or trade.get("open_timestamp")
    )
    ct = parse_utc_time(
        trade.get("close_time") or trade.get("close_timestamp")
    )
    if ot and ct:
        return max((ct - ot).total_seconds() / 3600.0, 0.0)
    return 0.0


def _sorted_median(values: list[float]) -> float:
    """Compute the median of a sorted list.

    Args:
        values: Pre-sorted list of floats.

    Returns:
        Median float; ``0.0`` when the list is empty.

    Side effects:
        None.
    """
    n = len(values)
    if n == 0:
        return 0.0
    if n % 2 == 1:
        return values[n // 2]
    return (values[n // 2 - 1] + values[n // 2]) / 2.0


# ---------------------------------------------------------------------------
# Closed trade filtering and ordering
# ---------------------------------------------------------------------------


def get_closed_trades(
    trades: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Filter a trade list to realised, closed trades only.

    A trade is closed when a ``close_time`` or ``close_timestamp`` key is
    present **and** ``is_open`` is falsy.

    Args:
        trades: List of trade record dicts.

    Returns:
        Subset containing only closed trades.

    Side effects:
        None.
    """
    closed = []
    for t in trades:
        close_time = t.get("close_time") or t.get("close_timestamp")
        if close_time is not None and not t.get("is_open", False):
            closed.append(t)
    return closed


def get_ordered_closed_trades(
    trades: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return closed trades sorted chronologically by close time.

    Args:
        trades: List of trade record dicts (open or closed).

    Returns:
        Chronologically ordered list of closed trades.

    Side effects:
        None.
    """
    closed = get_closed_trades(trades)

    def _close_ts(t: dict[str, Any]) -> float:
        ct = t.get("close_time") or t.get("close_timestamp")
        dt = parse_utc_time(ct)
        return dt.timestamp() if dt else 0.0

    return sorted(closed, key=_close_ts)


# ---------------------------------------------------------------------------
# Trade classification
# ---------------------------------------------------------------------------


def classify_trades(
    trades: list[dict[str, Any]],
    breakeven_epsilon: float | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Partition trades into wins, losses, and breakevens.

    Args:
        trades: List of trade record dicts.
        breakeven_epsilon: Absolute PnL tolerance for breakeven
            classification.  Defaults to
            ``AnalyticsConfig.breakeven_epsilon`` (``1e-9``).

    Returns:
        Dict with keys ``"wins"``, ``"losses"``, and ``"breakevens"``.

    Side effects:
        None.
    """
    eps = (
        breakeven_epsilon
        if breakeven_epsilon is not None
        else _DEFAULT_CONFIG.breakeven_epsilon
    )
    wins: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    breakevens: list[dict[str, Any]] = []
    for t in trades:
        pnl = _get_trade_pnl(t)
        if pnl > eps:
            wins.append(t)
        elif pnl < -eps:
            losses.append(t)
        else:
            breakevens.append(t)
    return {"wins": wins, "losses": losses, "breakevens": breakevens}


# ---------------------------------------------------------------------------
# R-multiple calculation
# ---------------------------------------------------------------------------


def get_r_multiples(
    trades: list[dict[str, Any]],
) -> tuple[list[float], list[str]]:
    """Calculate R-multiples for each trade.

    When ``initial_risk`` is missing or non-positive the proxy pattern
    (risk = 1.0) is used and a degraded-confidence warning is emitted.

    Args:
        trades: List of trade record dicts.

    Returns:
        A 2-tuple of ``(r_multiples, warnings)`` where ``warnings`` is a
        list of structured warning strings.  Returns ``([], [])`` for an
        empty trade list.

    Side effects:
        None.
    """
    r_multiples: list[float] = []
    warnings: list[str] = []
    proxy_count = 0
    for t in trades:
        pnl = _get_trade_pnl(t)
        raw_risk = (
            t.get("initial_risk")
            or t.get("risk")
            or t.get("risk_amount")
        )
        if raw_risk is None or float(raw_risk) <= 0:
            risk = 1.0
            proxy_count += 1
        else:
            risk = float(raw_risk)
        r_multiples.append(pnl / risk)
    if proxy_count:
        warnings.append(
            f"DEGRADED_CONFIDENCE: {proxy_count} trade(s) lacked"
            " initial_risk; R-multiple proxy (risk=1.0) was used."
            " Treat R-multiple metrics as estimates only."
        )
    return r_multiples, warnings


def _get_r_multiples_flat(trades: list[dict[str, Any]]) -> list[float]:
    """Return R-multiples list without warnings (kernel convenience).

    Args:
        trades: List of trade record dicts.

    Returns:
        List of R-multiple floats.

    Side effects:
        None.
    """
    values, _ = get_r_multiples(trades)
    return values


# ---------------------------------------------------------------------------
# Aggregate PnL kernels
# ---------------------------------------------------------------------------


def net_profit(trades: list[dict[str, Any]]) -> float:
    """Sum PnL across all closed trades.

    Args:
        trades: List of trade record dicts.

    Returns:
        Net profit in account currency.

    Side effects:
        None.
    """
    return sum(_get_trade_pnl(t) for t in get_closed_trades(trades))


def gross_profit(trades: list[dict[str, Any]]) -> float:
    """Sum positive PnL across all closed trades.

    Args:
        trades: List of trade record dicts.

    Returns:
        Gross profit in account currency; ``0.0`` when no winning trades.

    Side effects:
        None.
    """
    return sum(
        _get_trade_pnl(t)
        for t in get_closed_trades(trades)
        if _get_trade_pnl(t) > 0
    )


def gross_loss(trades: list[dict[str, Any]]) -> float:
    """Sum negative PnL across all closed trades.

    Args:
        trades: List of trade record dicts.

    Returns:
        Gross loss (negative number) in account currency; ``0.0`` when
        no losing trades.

    Side effects:
        None.
    """
    return sum(
        _get_trade_pnl(t)
        for t in get_closed_trades(trades)
        if _get_trade_pnl(t) < 0
    )


# ---------------------------------------------------------------------------
# Count kernels
# ---------------------------------------------------------------------------


def winning_trades(trades: list[dict[str, Any]]) -> int:
    """Count winning closed trades.

    Args:
        trades: List of trade record dicts.

    Returns:
        Count of winning trades.

    Side effects:
        None.
    """
    return len(classify_trades(trades)["wins"])


def losing_trades(trades: list[dict[str, Any]]) -> int:
    """Count losing closed trades.

    Args:
        trades: List of trade record dicts.

    Returns:
        Count of losing trades.

    Side effects:
        None.
    """
    return len(classify_trades(trades)["losses"])


def breakeven_trades(trades: list[dict[str, Any]]) -> int:
    """Count breakeven closed trades.

    Args:
        trades: List of trade record dicts.

    Returns:
        Count of breakeven trades.

    Side effects:
        None.
    """
    return len(classify_trades(trades)["breakevens"])


def long_trades(trades: list[dict[str, Any]]) -> int:
    """Count long (buy-direction) trades.

    Args:
        trades: List of trade record dicts.

    Returns:
        Count of long trades.

    Side effects:
        None.
    """
    return sum(
        1
        for t in trades
        if str(t.get("direction", "")).lower() in ("long", "buy")
    )


def short_trades(trades: list[dict[str, Any]]) -> int:
    """Count short (sell-direction) trades.

    Args:
        trades: List of trade record dicts.

    Returns:
        Count of short trades.

    Side effects:
        None.
    """
    return sum(
        1
        for t in trades
        if str(t.get("direction", "")).lower() in ("short", "sell")
    )


def count_open_trades(trades: list[dict[str, Any]]) -> int:
    """Count open (unrealised) trades.

    Args:
        trades: List of trade record dicts.

    Returns:
        Count of open trades.

    Side effects:
        None.
    """
    return sum(
        1
        for t in trades
        if t.get("is_open", False) or t.get("close_time") is None
    )


# ---------------------------------------------------------------------------
# Win / loss rate kernels
# ---------------------------------------------------------------------------


def win_rate_fraction(trades: list[dict[str, Any]]) -> float:
    """Compute win rate as a 0-to-1 fraction.

    Args:
        trades: List of trade record dicts.

    Returns:
        Win rate fraction; ``0.0`` when no closed trades.

    Side effects:
        None.
    """
    closed = get_closed_trades(trades)
    if not closed:
        return 0.0
    return winning_trades(closed) / len(closed)


def loss_rate(trades: list[dict[str, Any]]) -> float:
    """Compute loss rate as a 0-to-1 fraction.

    Args:
        trades: List of trade record dicts.

    Returns:
        Loss rate fraction; ``0.0`` when no closed trades.

    Side effects:
        None.
    """
    closed = get_closed_trades(trades)
    if not closed:
        return 0.0
    return losing_trades(closed) / len(closed)


# ---------------------------------------------------------------------------
# Average win / loss kernels
# ---------------------------------------------------------------------------


def avg_win(trades: list[dict[str, Any]]) -> float:
    """Compute average winning PnL per trade.

    Args:
        trades: List of trade record dicts.

    Returns:
        Average win; ``0.0`` when no winning trades.

    Side effects:
        None.
    """
    wins = classify_trades(trades)["wins"]
    if not wins:
        return 0.0
    return sum(_get_trade_pnl(t) for t in wins) / len(wins)


def avg_loss(trades: list[dict[str, Any]]) -> float:
    """Compute average losing PnL per trade.

    Args:
        trades: List of trade record dicts.

    Returns:
        Average loss (negative); ``0.0`` when no losing trades.

    Side effects:
        None.
    """
    losses = classify_trades(trades)["losses"]
    if not losses:
        return 0.0
    return sum(_get_trade_pnl(t) for t in losses) / len(losses)


def avg_win_loss(trades: list[dict[str, Any]]) -> float:
    """Compute average win to average absolute loss ratio.

    Args:
        trades: List of trade record dicts.

    Returns:
        Win/loss ratio; ``0.0`` when avg_loss is zero.

    Side effects:
        None.
    """
    aw = avg_win(trades)
    al = abs(avg_loss(trades))
    if al == 0:
        return 0.0
    return aw / al


def largest_win(trades: list[dict[str, Any]]) -> float:
    """Find the largest single winning PnL.

    Args:
        trades: List of trade record dicts.

    Returns:
        Largest win; ``0.0`` when no closed trades.

    Side effects:
        None.
    """
    closed = get_closed_trades(trades)
    return max((_get_trade_pnl(t) for t in closed), default=0.0)


def largest_loss(trades: list[dict[str, Any]]) -> float:
    """Find the most negative single PnL.

    Args:
        trades: List of trade record dicts.

    Returns:
        Largest loss (negative); ``0.0`` when no closed trades.

    Side effects:
        None.
    """
    closed = get_closed_trades(trades)
    return min((_get_trade_pnl(t) for t in closed), default=0.0)


def median_win(trades: list[dict[str, Any]]) -> float:
    """Compute the median winning PnL.

    Args:
        trades: List of trade record dicts.

    Returns:
        Median win; ``0.0`` when no winning trades.

    Side effects:
        None.
    """
    wins = sorted(_get_trade_pnl(t) for t in classify_trades(trades)["wins"])
    return _sorted_median(wins)


def median_loss(trades: list[dict[str, Any]]) -> float:
    """Compute the median losing PnL.

    Args:
        trades: List of trade record dicts.

    Returns:
        Median loss; ``0.0`` when no losing trades.

    Side effects:
        None.
    """
    losses = sorted(
        _get_trade_pnl(t) for t in classify_trades(trades)["losses"]
    )
    return _sorted_median(losses)


def expectancy(trades: list[dict[str, Any]]) -> float:
    """Compute mean PnL across closed trades (arithmetic expectancy).

    Args:
        trades: List of trade record dicts.

    Returns:
        Arithmetic expectancy per trade; ``0.0`` when no closed trades.

    Side effects:
        None.
    """
    closed = get_closed_trades(trades)
    if not closed:
        return 0.0
    return sum(_get_trade_pnl(t) for t in closed) / len(closed)


# ---------------------------------------------------------------------------
# Consecutive-streak kernels
# ---------------------------------------------------------------------------


def max_consecutive_wins(trades: list[dict[str, Any]]) -> int:
    """Find the longest consecutive winning streak.

    Args:
        trades: List of trade record dicts.

    Returns:
        Maximum consecutive-win count; ``0`` when no closed trades.

    Side effects:
        None.
    """
    ordered = get_ordered_closed_trades(trades)
    max_streak = 0
    current_streak = 0
    for t in ordered:
        if _get_trade_pnl(t) > 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    return max_streak


def max_consecutive_losses(trades: list[dict[str, Any]]) -> int:
    """Find the longest consecutive losing streak.

    Args:
        trades: List of trade record dicts.

    Returns:
        Maximum consecutive-loss count; ``0`` when no closed trades.

    Side effects:
        None.
    """
    ordered = get_ordered_closed_trades(trades)
    max_streak = 0
    current_streak = 0
    for t in ordered:
        if _get_trade_pnl(t) < 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    return max_streak


def avg_consecutive_wins(trades: list[dict[str, Any]]) -> float:
    """Compute the average length of consecutive winning streaks.

    Args:
        trades: List of trade record dicts.

    Returns:
        Average streak length; ``0.0`` when no streaks exist.

    Side effects:
        None.
    """
    ordered = get_ordered_closed_trades(trades)
    streaks: list[int] = []
    curr = 0
    for t in ordered:
        if _get_trade_pnl(t) > 0:
            curr += 1
        elif curr > 0:
            streaks.append(curr)
            curr = 0
    if curr > 0:
        streaks.append(curr)
    return sum(streaks) / len(streaks) if streaks else 0.0


def avg_consecutive_losses(trades: list[dict[str, Any]]) -> float:
    """Compute the average length of consecutive losing streaks.

    Args:
        trades: List of trade record dicts.

    Returns:
        Average streak length; ``0.0`` when no streaks exist.

    Side effects:
        None.
    """
    ordered = get_ordered_closed_trades(trades)
    streaks: list[int] = []
    curr = 0
    for t in ordered:
        if _get_trade_pnl(t) < 0:
            curr += 1
        elif curr > 0:
            streaks.append(curr)
            curr = 0
    if curr > 0:
        streaks.append(curr)
    return sum(streaks) / len(streaks) if streaks else 0.0


def consecutive_wins_losses(trades: list[dict[str, Any]]) -> dict[str, int]:
    """Compute max consecutive win and loss counts.

    Args:
        trades: List of trade record dicts.

    Returns:
        Dict with ``"wins"`` and ``"losses"`` counts.

    Side effects:
        None.
    """
    return {
        "wins": max_consecutive_wins(trades),
        "losses": max_consecutive_losses(trades),
    }


def win_loss_streaks(
    trades: list[dict[str, Any]],
) -> dict[str, list[int]]:
    """Enumerate all winning and losing streak lengths.

    Args:
        trades: List of trade record dicts.

    Returns:
        Dict with ``"wins"`` and ``"losses"`` lists of streak lengths.

    Side effects:
        None.
    """
    ordered = get_ordered_closed_trades(trades)
    wins: list[int] = []
    losses: list[int] = []
    curr_w = 0
    curr_l = 0
    for t in ordered:
        pnl = _get_trade_pnl(t)
        if pnl > 0:
            curr_w += 1
            if curr_l > 0:
                losses.append(curr_l)
                curr_l = 0
        elif pnl < 0:
            curr_l += 1
            if curr_w > 0:
                wins.append(curr_w)
                curr_w = 0
    if curr_w > 0:
        wins.append(curr_w)
    if curr_l > 0:
        losses.append(curr_l)
    return {"wins": wins, "losses": losses}


# ---------------------------------------------------------------------------
# Time-in-trade kernels
# ---------------------------------------------------------------------------


def avg_time_in_trade(trades: list[dict[str, Any]]) -> float:
    """Compute mean trade duration in hours.

    Args:
        trades: List of trade record dicts.

    Returns:
        Average duration in hours; ``0.0`` when no closed trades.

    Side effects:
        None.
    """
    durations = [
        _get_trade_duration(t) for t in get_closed_trades(trades)
    ]
    if not durations:
        return 0.0
    return sum(durations) / len(durations)


def median_time_in_trade(trades: list[dict[str, Any]]) -> float:
    """Compute median trade duration in hours.

    Args:
        trades: List of trade record dicts.

    Returns:
        Median duration in hours; ``0.0`` when no closed trades.

    Side effects:
        None.
    """
    durations = sorted(
        _get_trade_duration(t) for t in get_closed_trades(trades)
    )
    return _sorted_median(durations)


def max_time_in_trade(trades: list[dict[str, Any]]) -> float:
    """Find the longest trade duration in hours.

    Args:
        trades: List of trade record dicts.

    Returns:
        Maximum duration in hours; ``0.0`` when no closed trades.

    Side effects:
        None.
    """
    return max(
        (_get_trade_duration(t) for t in get_closed_trades(trades)),
        default=0.0,
    )


def min_time_in_trade(trades: list[dict[str, Any]]) -> float:
    """Find the shortest trade duration in hours.

    Args:
        trades: List of trade record dicts.

    Returns:
        Minimum duration in hours; ``0.0`` when no closed trades.

    Side effects:
        None.
    """
    return min(
        (_get_trade_duration(t) for t in get_closed_trades(trades)),
        default=0.0,
    )


def time_in_market_duration(trades: list[dict[str, Any]]) -> float:
    """Compute total time-in-market by merging overlapping trade intervals.

    Args:
        trades: List of trade record dicts.

    Returns:
        Total merged exposure duration in hours; ``0.0`` when no closed
        trades have parseable timestamps.

    Side effects:
        None.
    """
    closed = get_ordered_closed_trades(trades)
    if not closed:
        return 0.0
    intervals: list[tuple[float, float]] = []
    for t in closed:
        ot = parse_utc_time(
            t.get("open_time") or t.get("open_timestamp")
        )
        ct = parse_utc_time(
            t.get("close_time") or t.get("close_timestamp")
        )
        if ot and ct:
            intervals.append((ot.timestamp(), ct.timestamp()))
    if not intervals:
        return 0.0
    intervals.sort()
    merged: list[tuple[float, float]] = []
    curr = intervals[0]
    for nxt in intervals[1:]:
        if nxt[0] <= curr[1]:
            curr = (curr[0], max(curr[1], nxt[1]))
        else:
            merged.append(curr)
            curr = nxt
    merged.append(curr)
    return sum(end - start for start, end in merged) / 3600.0


def percent_time_in_market(
    trades: list[dict[str, Any]],
    period_duration_hours: float,
) -> float:
    """Compute fraction of the period spent in a trade.

    Args:
        trades: List of trade record dicts.
        period_duration_hours: Total period length in hours.

    Returns:
        Fraction in [0, 1]; ``0.0`` when ``period_duration_hours <= 0``.

    Side effects:
        None.
    """
    if period_duration_hours <= 0:
        return 0.0
    return time_in_market_duration(trades) / period_duration_hours


def trading_period_duration(trades: list[dict[str, Any]]) -> float:
    """Compute total span between first open and last close in hours.

    Args:
        trades: List of trade record dicts.

    Returns:
        Span in hours; ``0.0`` when fewer than two closed trades or
        timestamps are missing.

    Side effects:
        None.
    """
    ordered = get_ordered_closed_trades(trades)
    if len(ordered) < 2:
        return 0.0
    ot = parse_utc_time(
        ordered[0].get("open_time") or ordered[0].get("open_timestamp")
    )
    ct = parse_utc_time(
        ordered[-1].get("close_time")
        or ordered[-1].get("close_timestamp")
    )
    if ot and ct:
        return (ct - ot).total_seconds() / 3600.0
    return 0.0


# ---------------------------------------------------------------------------
# Size kernels
# ---------------------------------------------------------------------------


def max_gross_size_held(trades: list[dict[str, Any]]) -> float:
    """Find the maximum individual absolute trade size.

    Args:
        trades: List of trade record dicts.

    Returns:
        Maximum absolute size; ``0.0`` when no trades.

    Side effects:
        None.
    """
    return max(
        (
            abs(float(t.get("size") or t.get("volume") or 0.0))
            for t in trades
        ),
        default=0.0,
    )


def max_size_held(trades: list[dict[str, Any]]) -> float:
    """Alias for ``max_gross_size_held``.

    Args:
        trades: List of trade record dicts.

    Returns:
        Maximum absolute size; ``0.0`` when no trades.

    Side effects:
        None.
    """
    return max_gross_size_held(trades)


def max_net_size_held(trades: list[dict[str, Any]]) -> float:
    """Find the maximum absolute net position held at any point.

    Iterates trades chronologically, accumulating a running signed net
    position (long size adds, short size subtracts) and returns the
    maximum absolute value observed.

    Args:
        trades: List of trade record dicts.

    Returns:
        Maximum absolute net position; ``0.0`` when no trades.

    Side effects:
        None.
    """
    ordered = sorted(
        trades,
        key=lambda t: (
            parse_utc_time(
                t.get("open_time") or t.get("open_timestamp") or 0
            )
            or 0
        ),
    )
    net = 0.0
    max_abs_net = 0.0
    for t in ordered:
        size = float(t.get("size") or t.get("volume") or 0.0)
        direction = str(t.get("direction", "")).lower()
        if direction in ("long", "buy"):
            net += size
        elif direction in ("short", "sell"):
            net -= size
        max_abs_net = max(max_abs_net, abs(net))
    return max_abs_net


def max_long_size_held(trades: list[dict[str, Any]]) -> float:
    """Find the maximum size across long trades.

    Args:
        trades: List of trade record dicts.

    Returns:
        Maximum long size; ``0.0`` when no long trades.

    Side effects:
        None.
    """
    longs = [
        float(t.get("size") or 0.0)
        for t in trades
        if str(t.get("direction", "")).lower() in ("long", "buy")
    ]
    return max(longs, default=0.0)


def max_short_size_held(trades: list[dict[str, Any]]) -> float:
    """Find the maximum size across short trades.

    Args:
        trades: List of trade record dicts.

    Returns:
        Maximum short size; ``0.0`` when no short trades.

    Side effects:
        None.
    """
    shorts = [
        float(t.get("size") or 0.0)
        for t in trades
        if str(t.get("direction", "")).lower() in ("short", "sell")
    ]
    return max(shorts, default=0.0)


# ---------------------------------------------------------------------------
# R-multiple derived kernels
# ---------------------------------------------------------------------------


def compute_r_trade_metrics(
    r_multiples: list[float],
) -> dict[str, float]:
    """Compute mean, std, and expectancy from a list of R-multiples.

    Args:
        r_multiples: Pre-computed R-multiple values.

    Returns:
        Dict with ``"avg"``, ``"std"``, and ``"expectancy"`` keys.

    Side effects:
        None.
    """
    if not r_multiples:
        return {"avg": 0.0, "std": 0.0, "expectancy": 0.0}
    n = len(r_multiples)
    avg = sum(r_multiples) / n
    var = sum((x - avg) ** 2 for x in r_multiples) / max(n - 1, 1)
    return {"avg": avg, "std": math.sqrt(var), "expectancy": avg}


def compute_trade_metrics(
    r_values: list[float],
    mae: list[float] | None = None,
    mfe: list[float] | None = None,
) -> dict[str, float]:
    """Compute aggregate trade metrics from R-values.

    Args:
        r_values: Pre-computed R-multiple values.
        mae: Optional per-trade MAE values (currently unused).
        mfe: Optional per-trade MFE values (currently unused).

    Returns:
        Dict with ``"avg"``, ``"std"``, and ``"expectancy"`` keys.

    Side effects:
        None.
    """
    return compute_r_trade_metrics(r_values)


def expectancy_r(trades: list[dict[str, Any]]) -> float:
    """Compute mean R-multiple (R expectancy).

    Args:
        trades: List of trade record dicts.

    Returns:
        Mean R-multiple; ``0.0`` when no R-multiples can be computed.

    Side effects:
        None.
    """
    r_mults = _get_r_multiples_flat(trades)
    if not r_mults:
        return 0.0
    return sum(r_mults) / len(r_mults)


def avg_r_multiple(trades: list[dict[str, Any]]) -> float:
    """Alias for ``expectancy_r``.

    Args:
        trades: List of trade record dicts.

    Returns:
        Mean R-multiple; ``0.0`` when no R-multiples can be computed.

    Side effects:
        None.
    """
    return expectancy_r(trades)


def median_r_multiple(trades: list[dict[str, Any]]) -> float:
    """Compute the median R-multiple.

    Args:
        trades: List of trade record dicts.

    Returns:
        Median R-multiple; ``0.0`` when no R-multiples can be computed.

    Side effects:
        None.
    """
    r_mults = sorted(_get_r_multiples_flat(trades))
    return _sorted_median(r_mults)


def max_r_multiple(trades: list[dict[str, Any]]) -> float:
    """Find the maximum R-multiple.

    Args:
        trades: List of trade record dicts.

    Returns:
        Maximum R-multiple; ``0.0`` when no trades.

    Side effects:
        None.
    """
    return max(_get_r_multiples_flat(trades), default=0.0)


def min_r_multiple(trades: list[dict[str, Any]]) -> float:
    """Find the minimum R-multiple.

    Args:
        trades: List of trade record dicts.

    Returns:
        Minimum R-multiple; ``0.0`` when no trades.

    Side effects:
        None.
    """
    return min(_get_r_multiples_flat(trades), default=0.0)


def r_signal_to_noise(trades: list[dict[str, Any]]) -> float:
    """Compute the R-multiple signal-to-noise ratio.

    Args:
        trades: List of trade record dicts.

    Returns:
        Mean / std of R-multiples; ``0.0`` when undefined.

    Side effects:
        None.
    """
    r_mults = _get_r_multiples_flat(trades)
    n = len(r_mults)
    if n < 2:
        return 0.0
    avg = sum(r_mults) / n
    var = sum((x - avg) ** 2 for x in r_mults) / (n - 1)
    if var == 0:
        return 0.0
    return avg / math.sqrt(var)


# ---------------------------------------------------------------------------
# MAE / MFE kernels
# ---------------------------------------------------------------------------


def median_mae_mfe(trades: list[dict[str, Any]]) -> dict[str, float]:
    """Compute median MAE and MFE values across trades.

    Args:
        trades: List of trade record dicts.

    Returns:
        Dict with ``"mae"`` and ``"mfe"`` median values.

    Side effects:
        None.
    """
    maes = sorted(float(t.get("mae") or 0.0) for t in trades if "mae" in t)
    mfes = sorted(float(t.get("mfe") or 0.0) for t in trades if "mfe" in t)
    return {"mae": _sorted_median(maes), "mfe": _sorted_median(mfes)}


def get_mae_mfe_r(
    trades: list[dict[str, Any]],
) -> list[dict[str, float]]:
    """Compute per-trade MAE and MFE expressed as R-multiples.

    Args:
        trades: List of trade record dicts.

    Returns:
        List of dicts with ``"mae_r"`` and ``"mfe_r"`` keys.

    Side effects:
        None.
    """
    result = []
    for t in trades:
        risk = float(t.get("initial_risk") or 1.0)
        mae = float(t.get("mae") or 0.0)
        mfe = float(t.get("mfe") or 0.0)
        result.append({"mae_r": mae / risk, "mfe_r": mfe / risk})
    return result


def median_mae_r(trades: list[dict[str, Any]]) -> float:
    """Compute the median MAE expressed as an R-multiple.

    Args:
        trades: List of trade record dicts.

    Returns:
        Median MAE-R; ``0.0`` when no trades.

    Side effects:
        None.
    """
    r_maes = sorted(
        float(t.get("mae") or 0.0) / float(t.get("initial_risk") or 1.0)
        for t in trades
    )
    return _sorted_median(r_maes)


def median_mfe_r(trades: list[dict[str, Any]]) -> float:
    """Compute the median MFE expressed as an R-multiple.

    Args:
        trades: List of trade record dicts.

    Returns:
        Median MFE-R; ``0.0`` when no trades.

    Side effects:
        None.
    """
    r_mfes = sorted(
        float(t.get("mfe") or 0.0) / float(t.get("initial_risk") or 1.0)
        for t in trades
    )
    return _sorted_median(r_mfes)


# ---------------------------------------------------------------------------
# MFE / MAE efficiency kernels (defined here to break circular import)
# ---------------------------------------------------------------------------


def mfe_efficiency(trades: list[dict[str, Any]]) -> float:
    """Compute mean MFE capture ratio across winning trades.

    Ratio of realised PnL to Maximum Favourable Excursion.

    Args:
        trades: List of trade record dicts.

    Returns:
        Mean capture ratio in [0, 1]; ``1.0`` when no winning trades have
        MFE data.

    Side effects:
        None.
    """
    wins = classify_trades(trades)["wins"]
    if not wins:
        return 1.0
    effs = []
    for t in wins:
        mfe = float(t.get("mfe") or 0.0)
        pnl = _get_trade_pnl(t)
        if mfe > 0:
            effs.append(pnl / mfe)
    return sum(effs) / len(effs) if effs else 1.0


def loss_containment_efficiency(trades: list[dict[str, Any]]) -> float:
    """Compute mean MAE containment ratio across losing trades.

    Ratio of realised loss to Maximum Adverse Excursion (MAE).

    Args:
        trades: List of trade record dicts.

    Returns:
        Mean containment ratio in [0, 1]; ``1.0`` when no losing trades
        have MAE data.

    Side effects:
        None.
    """
    losses = classify_trades(trades)["losses"]
    if not losses:
        return 1.0
    effs = []
    for t in losses:
        mae = float(t.get("mae") or 0.0)
        pnl = abs(_get_trade_pnl(t))
        if mae > 0:
            effs.append(pnl / mae)
    return sum(effs) / len(effs) if effs else 1.0


def mae_efficiency(trades: list[dict[str, Any]]) -> float:
    """Alias for ``loss_containment_efficiency``.

    Args:
        trades: List of trade record dicts.

    Returns:
        Mean MAE containment ratio.

    Side effects:
        None.
    """
    return loss_containment_efficiency(trades)


def aggregate_mfe_capture_ratio(trades: list[dict[str, Any]]) -> float:
    """Alias for ``mfe_efficiency``.

    Args:
        trades: List of trade record dicts.

    Returns:
        Mean MFE capture ratio.

    Side effects:
        None.
    """
    return mfe_efficiency(trades)


def aggregate_loss_containment_efficiency(
    trades: list[dict[str, Any]],
) -> float:
    """Alias for ``loss_containment_efficiency``.

    Args:
        trades: List of trade record dicts.

    Returns:
        Mean MAE containment ratio.

    Side effects:
        None.
    """
    return loss_containment_efficiency(trades)


# ---------------------------------------------------------------------------
# Statistical kernels
# ---------------------------------------------------------------------------


def t_statistic(trades: list[dict[str, Any]]) -> float:
    """Compute the one-sample t-statistic for trade PnL.

    Args:
        trades: List of trade record dicts.

    Returns:
        T-statistic; ``0.0`` when fewer than 2 closed trades or variance
        is zero.

    Side effects:
        None.
    """
    closed = get_closed_trades(trades)
    n = len(closed)
    if n < 2:
        return 0.0
    pnls = [_get_trade_pnl(t) for t in closed]
    mean = sum(pnls) / n
    var = sum((x - mean) ** 2 for x in pnls) / (n - 1)
    if var == 0:
        return 0.0
    return mean / (math.sqrt(var) / math.sqrt(n))


def sqn(trades: list[dict[str, Any]]) -> float:
    """Compute System Quality Number.

    ``sqrt(n) * mean_pnl / std_pnl``

    Args:
        trades: List of trade record dicts.

    Returns:
        SQN; ``0.0`` when fewer than 2 closed trades or variance is zero.

    Side effects:
        None.
    """
    closed = get_closed_trades(trades)
    n = len(closed)
    if n < 2:
        return 0.0
    pnls = [_get_trade_pnl(t) for t in closed]
    mean = sum(pnls) / n
    var = sum((x - mean) ** 2 for x in pnls) / (n - 1)
    if var == 0:
        return 0.0
    return math.sqrt(n) * mean / math.sqrt(var)


def kelly_criterion(trades: list[dict[str, Any]]) -> float:
    """Compute the full Kelly position sizing fraction.

    ``win_rate - (1 - win_rate) / payoff_ratio``

    Args:
        trades: List of trade record dicts.

    Returns:
        Kelly fraction; ``0.0`` when payoff_ratio <= 0 or no closed trades.

    Side effects:
        None.
    """
    closed = get_closed_trades(trades)
    if not closed:
        return 0.0
    w = win_rate_fraction(closed)
    r = avg_win_loss(closed)
    if r <= 0:
        return 0.0
    return w - (1.0 - w) / r


def rolling_expectancy_stability(
    trades: list[dict[str, Any]],
    window: int = 10,
) -> float:
    """Compute std of rolling-window expectancies as a stability measure.

    Args:
        trades: List of trade record dicts.
        window: Rolling window size in trades.

    Returns:
        Std of rolling expectancies; ``0.0`` when fewer trades than window.

    Side effects:
        None.
    """
    closed = get_ordered_closed_trades(trades)
    if len(closed) < window:
        return 0.0
    pnls = [_get_trade_pnl(t) for t in closed]
    expectancies = [
        sum(pnls[i : i + window]) / window
        for i in range(len(pnls) - window + 1)
    ]
    n = len(expectancies)
    if n < 2:
        return 0.0
    avg_exp = sum(expectancies) / n
    var = sum((x - avg_exp) ** 2 for x in expectancies) / (n - 1)
    return math.sqrt(var)


def win_after_win_probability(trades: list[dict[str, Any]]) -> float:
    """Compute the conditional probability of a win following a win.

    Args:
        trades: List of trade record dicts.

    Returns:
        Conditional win probability; ``0.0`` when insufficient history.

    Side effects:
        None.
    """
    ordered = get_ordered_closed_trades(trades)
    if len(ordered) < 2:
        return 0.0
    wins_after_win = 0
    total_wins = 0
    for i in range(len(ordered) - 1):
        if _get_trade_pnl(ordered[i]) > 0:
            total_wins += 1
            if _get_trade_pnl(ordered[i + 1]) > 0:
                wins_after_win += 1
    return wins_after_win / total_wins if total_wins > 0 else 0.0


def runs_test_zscore(trades: list[dict[str, Any]]) -> float:
    """Compute the Wald–Wolfowitz runs-test z-score for trade outcomes.

    Args:
        trades: List of trade record dicts.

    Returns:
        Z-score; ``0.0`` when all outcomes are the same or < 2 trades.

    Side effects:
        None.
    """
    ordered = get_ordered_closed_trades(trades)
    n = len(ordered)
    if n < 2:
        return 0.0
    signs = [1 if _get_trade_pnl(t) > 0 else -1 for t in ordered]
    runs = 1
    for i in range(1, n):
        if signs[i] != signs[i - 1]:
            runs += 1
    n1 = sum(1 for x in signs if x == 1)
    n2 = n - n1
    if n1 == 0 or n2 == 0:
        return 0.0
    mu = (2.0 * n1 * n2) / n + 1.0
    var = (
        2.0 * n1 * n2 * (2.0 * n1 * n2 - n)
    ) / (n * n * (n - 1.0))
    if var == 0:
        return 0.0
    return (runs - mu) / math.sqrt(var)


# ---------------------------------------------------------------------------
# Exposure / cost kernels
# ---------------------------------------------------------------------------


def open_position_pnl(trades: list[dict[str, Any]]) -> float:
    """Sum unrealised PnL across currently-open positions.

    Args:
        trades: List of trade record dicts.

    Returns:
        Total unrealised PnL; ``0.0`` when no open positions.

    Side effects:
        None.
    """
    return sum(
        float(t.get("unrealized_pnl") or t.get("pnl") or 0.0)
        for t in trades
        if t.get("is_open", False) or t.get("close_time") is None
    )


def slippage_paid(trades: list[dict[str, Any]]) -> float:
    """Sum absolute slippage across all trades.

    Args:
        trades: List of trade record dicts.

    Returns:
        Total slippage paid; ``0.0`` when no slippage data.

    Side effects:
        None.
    """
    return sum(abs(float(t.get("slippage") or 0.0)) for t in trades)


def commission_paid(trades: list[dict[str, Any]]) -> float:
    """Sum absolute commission across all trades.

    Args:
        trades: List of trade record dicts.

    Returns:
        Total commission paid; ``0.0`` when no commission data.

    Side effects:
        None.
    """
    return sum(abs(float(t.get("commission") or 0.0)) for t in trades)


def swap_paid(trades: list[dict[str, Any]]) -> float:
    """Sum absolute swap charges across all trades.

    Args:
        trades: List of trade record dicts.

    Returns:
        Total swap paid; ``0.0`` when no swap data.

    Side effects:
        None.
    """
    return sum(abs(float(t.get("swap") or 0.0)) for t in trades)


def avg_trade_nominal_exposure(trades: list[dict[str, Any]]) -> float:
    """Compute mean nominal exposure per closed trade.

    Args:
        trades: List of trade record dicts.

    Returns:
        Mean exposure in account currency; ``0.0`` when no closed trades.

    Side effects:
        None.
    """
    closed = get_closed_trades(trades)
    if not closed:
        return 0.0
    exposures = [
        float(t.get("size", 0.0)) * float(t.get("open_price", 1.0))
        for t in closed
    ]
    return sum(exposures) / len(exposures)


def max_single_trade_margin_utilization(
    trades: list[dict[str, Any]],
) -> float:
    """Find the peak single-trade margin utilisation.

    Args:
        trades: List of trade record dicts.

    Returns:
        Peak margin; ``0.0`` when no closed trades.

    Side effects:
        None.
    """
    closed = get_closed_trades(trades)
    return max((float(t.get("margin") or 0.0) for t in closed), default=0.0)


def avg_single_trade_margin_utilization(
    trades: list[dict[str, Any]],
) -> float:
    """Compute mean per-trade margin utilisation.

    Args:
        trades: List of trade record dicts.

    Returns:
        Mean margin; ``0.0`` when no closed trades.

    Side effects:
        None.
    """
    closed = get_closed_trades(trades)
    if not closed:
        return 0.0
    margins = [float(t.get("margin") or 0.0) for t in closed]
    return sum(margins) / len(margins)


# ---------------------------------------------------------------------------
# Adjusted PnL kernels
# ---------------------------------------------------------------------------


def adjusted_gross_profit(
    trades: list[dict[str, Any]],
    outlier_std_factor: float = 3.0,
) -> float:
    """Sum winning PnL excluding extreme outliers.

    Args:
        trades: List of trade record dicts.
        outlier_std_factor: Std multiplier for outlier threshold.

    Returns:
        Adjusted gross profit; ``0.0`` when no winning trades.

    Side effects:
        None.
    """
    wins = [_get_trade_pnl(t) for t in classify_trades(trades)["wins"]]
    if not wins:
        return 0.0
    avg = sum(wins) / len(wins)
    std = (
        math.sqrt(sum((x - avg) ** 2 for x in wins) / len(wins))
        if len(wins) > 1
        else 0.0
    )
    limit = avg + outlier_std_factor * std
    return sum(x for x in wins if x <= limit)


def adjusted_gross_loss(
    trades: list[dict[str, Any]],
    outlier_std_factor: float = 3.0,
) -> float:
    """Sum losing PnL excluding extreme outliers.

    Args:
        trades: List of trade record dicts.
        outlier_std_factor: Std multiplier for outlier threshold.

    Returns:
        Adjusted gross loss (negative); ``0.0`` when no losing trades.

    Side effects:
        None.
    """
    losses = [_get_trade_pnl(t) for t in classify_trades(trades)["losses"]]
    if not losses:
        return 0.0
    avg = sum(losses) / len(losses)
    std = (
        math.sqrt(sum((x - avg) ** 2 for x in losses) / len(losses))
        if len(losses) > 1
        else 0.0
    )
    limit = avg - outlier_std_factor * std
    return sum(x for x in losses if x >= limit)


def adjusted_net_profit(trades: list[dict[str, Any]]) -> float:
    """Compute net profit after removing outliers from both tails.

    Args:
        trades: List of trade record dicts.

    Returns:
        Adjusted net profit.

    Side effects:
        None.
    """
    return adjusted_gross_profit(trades) + adjusted_gross_loss(trades)


def select_net_profit(trades: list[dict[str, Any]]) -> float:
    """Compute net profit after trimming 2 % from each tail.

    Args:
        trades: List of trade record dicts.

    Returns:
        Trimmed net profit; ``0.0`` when no closed trades.

    Side effects:
        None.
    """
    pnls = sorted(_get_trade_pnl(t) for t in get_closed_trades(trades))
    if not pnls:
        return 0.0
    trim = int(len(pnls) * 0.02)
    trimmed = pnls[trim : len(pnls) - trim] if trim > 0 else pnls
    return sum(trimmed)


def select_gross_profit(trades: list[dict[str, Any]]) -> float:
    """Compute gross profit after trimming the top 2 % of wins.

    Args:
        trades: List of trade record dicts.

    Returns:
        Trimmed gross profit; ``0.0`` when no winning trades.

    Side effects:
        None.
    """
    wins = sorted(_get_trade_pnl(t) for t in classify_trades(trades)["wins"])
    if not wins:
        return 0.0
    trim = int(len(wins) * 0.02)
    return sum(wins[: len(wins) - trim] if trim > 0 else wins)


def select_gross_loss(trades: list[dict[str, Any]]) -> float:
    """Compute gross loss after trimming the bottom 2 % of losses.

    Args:
        trades: List of trade record dicts.

    Returns:
        Trimmed gross loss; ``0.0`` when no losing trades.

    Side effects:
        None.
    """
    losses = sorted(
        _get_trade_pnl(t) for t in classify_trades(trades)["losses"]
    )
    if not losses:
        return 0.0
    trim = int(len(losses) * 0.02)
    return sum(losses[trim:] if trim > 0 else losses)


def select_net_profit_as_percent_of_max_trade_drawdown(
    net_prof: float,
    max_dd: float,
) -> float:
    """Express select net profit as a percentage of max drawdown.

    Args:
        net_prof: Net profit value.
        max_dd: Maximum drawdown value.

    Returns:
        Ratio * 100; ``0.0`` when max_dd <= 0.

    Side effects:
        None.
    """
    if max_dd <= 0:
        return 0.0
    return (net_prof / max_dd) * 100.0


def adjusted_net_profit_as_percent_of_max_trade_drawdown(
    net_prof: float,
    max_dd: float,
) -> float:
    """Express adjusted net profit as a percentage of max drawdown.

    Args:
        net_prof: Adjusted net profit value.
        max_dd: Maximum drawdown value.

    Returns:
        Ratio * 100; ``0.0`` when max_dd <= 0.

    Side effects:
        None.
    """
    if max_dd <= 0:
        return 0.0
    return (net_prof / max_dd) * 100.0


def net_profit_as_percent_of_max_trade_drawdown(
    net_prof: float,
    max_dd: float,
) -> float:
    """Express net profit as a percentage of max drawdown.

    Args:
        net_prof: Net profit value.
        max_dd: Maximum drawdown value.

    Returns:
        Ratio * 100; ``0.0`` when max_dd <= 0.

    Side effects:
        None.
    """
    if max_dd <= 0:
        return 0.0
    return (net_prof / max_dd) * 100.0


def return_over_drawdown(net_prof: float, max_dd: float) -> float:
    """Compute the return-over-drawdown ratio.

    Args:
        net_prof: Net profit value.
        max_dd: Maximum drawdown value.

    Returns:
        Ratio; ``0.0`` when max_dd <= 0.

    Side effects:
        None.
    """
    if max_dd <= 0:
        return 0.0
    return net_prof / max_dd


# ---------------------------------------------------------------------------
# Balance / equity curve construction
# ---------------------------------------------------------------------------


def balance_curve_from_closed_trades(
    trades: list[dict[str, Any]],
    initial_balance: float = 10000.0,
    currency: str = "USD",
) -> list[dict[str, Any]]:
    """Build an equity curve dict-list from ordered closed trades.

    Args:
        trades: List of trade record dicts.
        initial_balance: Starting account balance.
        currency: ISO-4217 currency code for each curve point.

    Returns:
        List of ``{"timestamp": str, "equity": float, "currency": str}``
        dicts ordered chronologically.

    Side effects:
        None.
    """
    ordered = get_ordered_closed_trades(trades)
    curve: list[dict[str, Any]] = []
    current_balance = initial_balance
    start_time = "1970-01-01T00:00:00+00:00"
    if ordered:
        ot_raw = ordered[0].get("open_time") or ordered[0].get(
            "open_timestamp"
        )
        dt = parse_utc_time(ot_raw)
        if dt:
            start_time = dt.isoformat()
        elif isinstance(ot_raw, str):
            start_time = ot_raw
    curve.append(
        {
            "timestamp": start_time,
            "equity": current_balance,
            "currency": currency,
        }
    )
    for t in ordered:
        current_balance += _get_trade_pnl(t)
        ct_raw = t.get("close_time") or t.get("close_timestamp")
        dt = parse_utc_time(ct_raw)
        if dt:
            timestamp = dt.isoformat()
        elif isinstance(ct_raw, str):
            timestamp = ct_raw
        else:
            timestamp = "1970-01-01T00:00:00+00:00"
        curve.append(
            {
                "timestamp": timestamp,
                "equity": current_balance,
                "currency": currency,
            }
        )
    return curve


def balance_curve(
    trades: list[dict[str, Any]],
    initial_balance: float = 10000.0,
    currency: str = "USD",
) -> list[dict[str, Any]]:
    """Alias for ``balance_curve_from_closed_trades``.

    Args:
        trades: List of trade record dicts.
        initial_balance: Starting account balance.
        currency: ISO-4217 currency code.

    Returns:
        Chronological equity curve.

    Side effects:
        None.
    """
    return balance_curve_from_closed_trades(trades, initial_balance, currency)


def equity_curve(
    trades: list[dict[str, Any]],
    initial_balance: float = 10000.0,
    currency: str = "USD",
) -> list[dict[str, Any]]:
    """Alias for ``balance_curve_from_closed_trades``.

    Args:
        trades: List of trade record dicts.
        initial_balance: Starting account balance.
        currency: ISO-4217 currency code.

    Returns:
        Chronological equity curve.

    Side effects:
        None.
    """
    return balance_curve_from_closed_trades(trades, initial_balance, currency)


# ---------------------------------------------------------------------------
# Simulation kernels
# ---------------------------------------------------------------------------


def risk_of_ruin(
    trades: list[dict[str, Any]],
    initial_balance: float,
    ruin_threshold: float,
    iterations: int = 1000,
) -> float:
    """Estimate probability of ruin via Monte Carlo resampling.

    Args:
        trades: List of trade record dicts.
        initial_balance: Starting account balance.
        ruin_threshold: Balance level considered ruinous.
        iterations: Number of Monte Carlo paths.

    Returns:
        Estimated ruin probability; ``0.0`` when no closed trades or
        ``initial_balance <= ruin_threshold``.

    Side effects:
        None (uses a seeded RNG).
    """
    closed = get_closed_trades(trades)
    if not closed or initial_balance <= ruin_threshold:
        return 0.0
    pnl_outcomes = [_get_trade_pnl(t) for t in closed]
    rng = _random_module.Random(42)
    ruined_sims = 0
    for _ in range(iterations):
        balance = initial_balance
        for _ in range(100):
            outcome = rng.choice(pnl_outcomes)
            balance += outcome
            if balance <= ruin_threshold:
                ruined_sims += 1
                break
    return ruined_sims / iterations


def risk_of_ruin_with_custom_horizon(
    trades: list[dict[str, Any]],
    initial_balance: float,
    ruin_threshold: float,
    horizon: int = 50,
) -> float:
    """Estimate probability of ruin over a fixed trade horizon.

    Args:
        trades: List of trade record dicts.
        initial_balance: Starting account balance.
        ruin_threshold: Balance level considered ruinous.
        horizon: Number of trades per simulated path.

    Returns:
        Estimated ruin probability; ``0.0`` when no closed trades.

    Side effects:
        None (uses a seeded RNG).
    """
    closed = get_closed_trades(trades)
    if not closed:
        return 0.0
    pnl_outcomes = [_get_trade_pnl(t) for t in closed]
    rng = _random_module.Random(42)
    ruined_sims = 0
    for _ in range(1000):
        balance = initial_balance
        for _ in range(horizon):
            balance += rng.choice(pnl_outcomes)
            if balance <= ruin_threshold:
                ruined_sims += 1
                break
    return ruined_sims / 1000.0


def max_loss_probability(
    trades: list[dict[str, Any]],
    threshold: float,
) -> float:
    """Compute empirical probability of a loss >= threshold.

    Args:
        trades: List of trade record dicts.
        threshold: Absolute loss threshold.

    Returns:
        Empirical probability; ``0.0`` when no closed trades.

    Side effects:
        None.
    """
    closed = get_closed_trades(trades)
    if not closed:
        return 0.0
    bad_count = sum(
        1 for t in closed if _get_trade_pnl(t) <= -abs(threshold)
    )
    return bad_count / len(closed)


# ---------------------------------------------------------------------------
# Period / session analysis kernels
# ---------------------------------------------------------------------------


def calculate_period_analysis(
    trades: list[dict[str, Any]],
    bucket: str = "monthly",
) -> dict[str, float]:
    """Aggregate net PnL per calendar bucket (monthly or annual).

    Args:
        trades: List of trade record dicts.
        bucket: ``"monthly"`` or ``"annual"``.

    Returns:
        Dict mapping bucket label to aggregate PnL.

    Side effects:
        None.
    """
    ordered = get_ordered_closed_trades(trades)
    results: dict[str, float] = {}
    for t in ordered:
        ct = parse_utc_time(
            t.get("close_time") or t.get("close_timestamp")
        )
        if not ct:
            continue
        key = (
            ct.strftime("%Y-%m")
            if bucket == "monthly"
            else ct.strftime("%Y")
        )
        results[key] = results.get(key, 0.0) + _get_trade_pnl(t)
    return results


def calculate_long_short_split(
    trades: list[dict[str, Any]],
) -> dict[str, float]:
    """Split net PnL into long and short components.

    Args:
        trades: List of trade record dicts.

    Returns:
        Dict with ``"long_pnl"`` and ``"short_pnl"`` keys.

    Side effects:
        None.
    """
    closed = get_closed_trades(trades)
    longs = [
        t
        for t in closed
        if str(t.get("direction", "")).lower() in ("long", "buy")
    ]
    shorts = [
        t
        for t in closed
        if str(t.get("direction", "")).lower() in ("short", "sell")
    ]
    return {
        "long_pnl": sum(_get_trade_pnl(t) for t in longs),
        "short_pnl": sum(_get_trade_pnl(t) for t in shorts),
    }


def calculate_session_performance(
    trades: list[dict[str, Any]],
) -> dict[str, float]:
    """Aggregate PnL per trading session (Asian / London / New York).

    Args:
        trades: List of trade record dicts.

    Returns:
        Dict with ``"asian"``, ``"london"``, and ``"newyork"`` PnL.

    Side effects:
        None.
    """
    ordered = get_ordered_closed_trades(trades)
    sessions = {"asian": 0.0, "london": 0.0, "newyork": 0.0}
    for t in ordered:
        ct = parse_utc_time(
            t.get("close_time") or t.get("close_timestamp")
        )
        if not ct:
            continue
        hr = ct.hour
        if hr < 8:
            sessions["asian"] += _get_trade_pnl(t)
        elif hr < 16:
            sessions["london"] += _get_trade_pnl(t)
        else:
            sessions["newyork"] += _get_trade_pnl(t)
    return sessions


def longest_flat_period_duration(
    trades: list[dict[str, Any]],
    period_start: Any = None,
    period_end: Any = None,
) -> float:
    """Find the longest gap between trades (flat period) in hours.

    Args:
        trades: List of trade record dicts.
        period_start: Optional analysis window start timestamp.
        period_end: Optional analysis window end timestamp.

    Returns:
        Longest flat period in hours; ``0.0`` when no ordered trades.

    Side effects:
        None.
    """
    ordered = get_ordered_closed_trades(trades)
    if not ordered:
        return 0.0
    max_flat = 0.0
    prev_close = parse_utc_time(period_start) if period_start else None
    for t in ordered:
        ot = parse_utc_time(
            t.get("open_time") or t.get("open_timestamp")
        )
        ct = parse_utc_time(
            t.get("close_time") or t.get("close_timestamp")
        )
        if prev_close and ot:
            flat = (ot - prev_close).total_seconds() / 3600.0
            max_flat = max(max_flat, flat)
        prev_close = ct
    if period_end and prev_close:
        end = parse_utc_time(period_end)
        if end:
            flat = (end - prev_close).total_seconds() / 3600.0
            max_flat = max(max_flat, flat)
    return max_flat


# ---------------------------------------------------------------------------
# Trade-level drawdown kernels
# ---------------------------------------------------------------------------


def trade_level_drawdowns(trades: list[dict[str, Any]]) -> list[float]:
    """Compute balance-drawdown series at each trade close.

    Args:
        trades: List of trade record dicts.

    Returns:
        List of drawdown values (absolute, in account currency).

    Side effects:
        None.
    """
    closed = get_ordered_closed_trades(trades)
    if not closed:
        return []
    balance = 10000.0
    balances = [balance]
    for t in closed:
        balance += _get_trade_pnl(t)
        balances.append(balance)
    peak = balances[0]
    drawdowns: list[float] = []
    for b in balances:
        peak = max(peak, b)
        drawdowns.append(peak - b)
    return drawdowns


def max_close_to_close_drawdown(trades: list[dict[str, Any]]) -> float:
    """Find the maximum close-to-close balance drawdown.

    Args:
        trades: List of trade record dicts.

    Returns:
        Maximum drawdown in account currency; ``0.0`` when no trades.

    Side effects:
        None.
    """
    return max(trade_level_drawdowns(trades), default=0.0)


def avg_trade_drawdown(trades: list[dict[str, Any]]) -> float:
    """Compute the mean close-to-close balance drawdown.

    Args:
        trades: List of trade record dicts.

    Returns:
        Mean drawdown in account currency; ``0.0`` when no trades.

    Side effects:
        None.
    """
    dds = trade_level_drawdowns(trades)
    return sum(dds) / len(dds) if dds else 0.0


def max_consecutive_drawdown_trades(trades: list[dict[str, Any]]) -> int:
    """Count the maximum consecutive trades spent in drawdown.

    Args:
        trades: List of trade record dicts.

    Returns:
        Maximum count; ``0`` when no trades.

    Side effects:
        None.
    """
    dds = trade_level_drawdowns(trades)
    max_con = 0
    curr_con = 0
    for d in dds:
        if d > 0:
            curr_con += 1
            max_con = max(max_con, curr_con)
        else:
            curr_con = 0
    return max_con


def max_close_to_close_drawdown_date(trades: list[dict[str, Any]]) -> str:
    """Return the timestamp of the maximum close-to-close drawdown.

    Args:
        trades: List of trade record dicts.

    Returns:
        ISO-8601 UTC timestamp string; ``"1970-01-01T00:00:00+00:00"``
        when no trades.

    Side effects:
        None.
    """
    _fallback = "1970-01-01T00:00:00+00:00"
    closed = get_ordered_closed_trades(trades)
    if not closed:
        return _fallback
    dds = trade_level_drawdowns(trades)
    if not dds:
        return _fallback
    max_dd = max(dds)
    max_idx = dds.index(max_dd)
    if max_idx == 0:
        return _fallback
    t = closed[max_idx - 1]
    ct_raw = t.get("close_time") or t.get("close_timestamp")
    dt = parse_utc_time(ct_raw)
    if dt:
        return dt.isoformat()
    if isinstance(ct_raw, str):
        return ct_raw
    return _fallback


# ---------------------------------------------------------------------------
# Efficiency helpers
# ---------------------------------------------------------------------------


def position_size_efficiency(trades: list[dict[str, Any]]) -> float:
    """Compute correlation between position size and PnL.

    Args:
        trades: List of trade record dicts.

    Returns:
        Pearson correlation of size and PnL; ``0.0`` when undefined.

    Side effects:
        None.
    """
    closed = get_closed_trades(trades)
    if len(closed) < 2:
        return 0.0
    sizes = [float(t.get("size") or 0.0) for t in closed]
    pnls = [_get_trade_pnl(t) for t in closed]
    n = len(closed)
    mean_s = sum(sizes) / n
    mean_p = sum(pnls) / n
    num = sum((sizes[i] - mean_s) * (pnls[i] - mean_p) for i in range(n))
    den_s = sum((x - mean_s) ** 2 for x in sizes)
    den_p = sum((x - mean_p) ** 2 for x in pnls)
    if den_s == 0 or den_p == 0:
        return 0.0
    return num / math.sqrt(den_s * den_p)


def trade_efficiency(trade: dict[str, Any]) -> float:
    """Compute single-trade exit efficiency (pnl / mfe).

    Args:
        trade: Single trade record dict.

    Returns:
        Efficiency ratio in [-1, 1]; ``0.0`` when MFE is non-positive.

    Side effects:
        None.
    """
    pnl = _get_trade_pnl(trade)
    mfe = float(trade.get("mfe") or 0.0)
    if mfe <= 0:
        return 0.0
    return max(pnl / mfe, -1.0)


def trade_outcome_entropy(trades: list[dict[str, Any]]) -> float:
    """Compute Shannon entropy of win / loss / breakeven outcome classes.

    Args:
        trades: List of trade record dicts.

    Returns:
        Entropy in bits; ``0.0`` when no closed trades.

    Side effects:
        None.
    """
    closed = get_closed_trades(trades)
    if not closed:
        return 0.0
    classes = classify_trades(closed)
    n = len(closed)
    entropy = 0.0
    for count in (
        len(classes["wins"]),
        len(classes["losses"]),
        len(classes["breakevens"]),
    ):
        p = count / n
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


# ---------------------------------------------------------------------------
# Return / performance helpers
# ---------------------------------------------------------------------------


def return_on_account(net_prof: float, account_size: float) -> float:
    """Compute return on account as a percentage.

    Args:
        net_prof: Net profit.
        account_size: Account size.

    Returns:
        Return percentage; ``0.0`` when account_size <= 0.

    Side effects:
        None.
    """
    if account_size <= 0:
        return 0.0
    return (net_prof / account_size) * 100.0


def max_runup(
    trades: list[dict[str, Any]],
    initial_balance: float = 10000.0,
) -> float:
    """Find the maximum run-up from a trough to the next peak.

    Args:
        trades: List of trade record dicts.
        initial_balance: Starting balance.

    Returns:
        Maximum run-up in account currency; ``0.0`` when no trades.

    Side effects:
        None.
    """
    curve = balance_curve(trades, initial_balance)
    if not curve:
        return 0.0
    equities = [c["equity"] for c in curve]
    running_min = equities[0]
    max_run = 0.0
    for eq in equities:
        running_min = min(running_min, eq)
        max_run = max(max_run, eq - running_min)
    return max_run


def max_runup_date(
    trades: list[dict[str, Any]],
    initial_balance: float = 10000.0,
) -> str:
    """Return the timestamp at which the maximum run-up occurred.

    Args:
        trades: List of trade record dicts.
        initial_balance: Starting balance.

    Returns:
        ISO-8601 UTC timestamp string; fallback sentinel when no trades.

    Side effects:
        None.
    """
    _fallback = "1970-01-01T00:00:00+00:00"
    curve = balance_curve(trades, initial_balance)
    if not curve:
        return _fallback
    equities = [c["equity"] for c in curve]
    running_min = equities[0]
    max_run = 0.0
    peak_idx = 0
    for i, eq in enumerate(equities):
        running_min = min(running_min, eq)
        run = eq - running_min
        if run > max_run:
            max_run = run
            peak_idx = i
    return str(curve[peak_idx]["timestamp"])


def return_per_trade_hour(trades: list[dict[str, Any]]) -> float:
    """Compute net profit per hour spent in trades.

    Args:
        trades: List of trade record dicts.

    Returns:
        PnL per trade-hour; ``0.0`` when no time-in-trade.

    Side effects:
        None.
    """
    closed = get_closed_trades(trades)
    pnl = sum(_get_trade_pnl(t) for t in closed)
    tot_hours = sum(_get_trade_duration(t) for t in closed)
    return pnl / tot_hours if tot_hours > 0 else 0.0


def return_per_market_hour(trades: list[dict[str, Any]]) -> float:
    """Compute net profit per hour of market exposure.

    Args:
        trades: List of trade record dicts.

    Returns:
        PnL per market-exposure hour; ``0.0`` when no exposure.

    Side effects:
        None.
    """
    closed = get_closed_trades(trades)
    pnl = sum(_get_trade_pnl(t) for t in closed)
    tot_hours = time_in_market_duration(trades)
    return pnl / tot_hours if tot_hours > 0 else 0.0


def trades_per_day(
    trades: list[dict[str, Any]],
    duration_days: float = 30.0,
) -> float:
    """Compute average closed trades per day.

    Args:
        trades: List of trade record dicts.
        duration_days: Observation window length in days.

    Returns:
        Trades per day; ``0.0`` when ``duration_days <= 0``.

    Side effects:
        None.
    """
    if duration_days <= 0:
        return 0.0
    return len(get_closed_trades(trades)) / duration_days


def profit_per_trade_per_day(
    trades: list[dict[str, Any]],
    duration_days: float = 30.0,
) -> float:
    """Compute expectancy normalised by observation window length.

    Args:
        trades: List of trade record dicts.
        duration_days: Observation window length in days.

    Returns:
        Expectancy per day; ``0.0`` when no closed trades or
        ``duration_days <= 0``.

    Side effects:
        None.
    """
    closed = get_closed_trades(trades)
    if not closed or duration_days <= 0:
        return 0.0
    return expectancy(closed) / duration_days


def avg_return_per_risk_unit(trades: list[dict[str, Any]]) -> float:
    """Compute mean R-multiple (avg profit per risk unit).

    Args:
        trades: List of trade record dicts.

    Returns:
        Mean R-multiple; ``0.0`` when no trades.

    Side effects:
        None.
    """
    r_mults = _get_r_multiples_flat(trades)
    return sum(r_mults) / len(r_mults) if r_mults else 0.0


def avg_trade_notional_efficiency(trades: list[dict[str, Any]]) -> float:
    """Compute mean PnL per unit of notional exposure.

    Args:
        trades: List of trade record dicts.

    Returns:
        Mean PnL / exposure ratio; ``0.0`` when no closed trades.

    Side effects:
        None.
    """
    closed = get_closed_trades(trades)
    if not closed:
        return 0.0
    effs = []
    for t in closed:
        pnl = abs(_get_trade_pnl(t))
        exposure = float(t.get("size", 0.0)) * float(
            t.get("open_price", 1.0)
        )
        if exposure > 0:
            effs.append(pnl / exposure)
    return sum(effs) / len(effs) if effs else 0.0


def calculate_spread_cost_impact(trades: list[dict[str, Any]]) -> float:
    """Sum spread costs across all trades.

    Args:
        trades: List of trade record dicts.

    Returns:
        Total spread cost; ``0.0`` when no data.

    Side effects:
        None.
    """
    return sum(float(t.get("spread_cost") or 0.0) for t in trades)


def calculate_slippage_impact(trades: list[dict[str, Any]]) -> float:
    """Sum slippage costs across all trades.

    Args:
        trades: List of trade record dicts.

    Returns:
        Total slippage; ``0.0`` when no data.

    Side effects:
        None.
    """
    return slippage_paid(trades)


def calculate_commission_impact(trades: list[dict[str, Any]]) -> float:
    """Sum commission costs across all trades.

    Args:
        trades: List of trade record dicts.

    Returns:
        Total commission; ``0.0`` when no data.

    Side effects:
        None.
    """
    return commission_paid(trades)


# ---------------------------------------------------------------------------
# Distribution summary kernel
# ---------------------------------------------------------------------------


def trade_pnl_distribution(
    trades: list[dict[str, Any]],
) -> dict[str, float]:
    """Compute summary statistics of the closed-trade PnL distribution.

    Args:
        trades: List of trade record dicts.

    Returns:
        Dict with ``"mean"``, ``"std"``, ``"min"``, ``"max"``, and
        ``"median"`` keys; empty when no closed trades.

    Side effects:
        None.
    """
    pnls = sorted(_get_trade_pnl(t) for t in get_closed_trades(trades))
    if not pnls:
        return {}
    n = len(pnls)
    mean = sum(pnls) / n
    return {
        "mean": mean,
        "std": math.sqrt(
            sum((x - mean) ** 2 for x in pnls) / max(n - 1, 1)
        ),
        "min": pnls[0],
        "max": pnls[-1],
        "median": _sorted_median(pnls),
    }


# ---------------------------------------------------------------------------
# Official tool: total_trades
# ---------------------------------------------------------------------------


def total_trades(
    trades: Any,
    request_id: str | None = None,
) -> StandardResponse:
    """Return the total number of closed trades.

    Args:
        trades: Trade records in any supported format.
        request_id: Optional trace identifier.

    Returns:
        ``StandardResponse`` with ``data`` set to closed-trade count.

    Side effects:
        None.
    """
    validate_request_id_strict(request_id)
    meta = build_metadata(
        tool_name="total_trades",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        t_list = to_trade_list(trades)
        count = len(get_closed_trades(t_list))
        return success_response(
            message="Calculated total closed trades.",
            data=count,
            metadata=meta,
        )
    except Exception as exc:
        return response_from_exception(exception=exc, metadata=meta)


# ---------------------------------------------------------------------------
# Official tool: win_rate
# ---------------------------------------------------------------------------


def win_rate(
    trades: Any,
    request_id: str | None = None,
) -> StandardResponse:
    """Return the win rate on a 0-to-1 scale.

    Args:
        trades: Trade records in any supported format.
        request_id: Optional trace identifier.

    Returns:
        ``StandardResponse`` with ``data`` set to win-rate fraction.

    Side effects:
        None.
    """
    validate_request_id_strict(request_id)
    meta = build_metadata(
        tool_name="win_rate",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        t_list = to_trade_list(trades)
        closed = get_closed_trades(t_list)
        if not closed:
            return success_response(
                message="No closed trades to calculate win rate.",
                data=0.0,
                metadata=meta,
            )
        rate = len(classify_trades(closed)["wins"]) / len(closed)
        return success_response(
            message="Calculated win rate.",
            data=rate,
            metadata=meta,
        )
    except Exception as exc:
        return response_from_exception(exception=exc, metadata=meta)


# ---------------------------------------------------------------------------
# Official tool: profit_factor
# ---------------------------------------------------------------------------


def profit_factor(
    trades: Any,
    request_id: str | None = None,
) -> StandardResponse:
    """Return the profit factor (gross profit / gross loss).

    Args:
        trades: Trade records in any supported format.
        request_id: Optional trace identifier.

    Returns:
        ``StandardResponse`` with ``data`` set to profit factor.  Returns
        ``999.0`` when gross loss is zero to distinguish from no-trades (0.0).

    Side effects:
        None.
    """
    validate_request_id_strict(request_id)
    meta = build_metadata(
        tool_name="profit_factor",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        t_list = to_trade_list(trades)
        closed = get_closed_trades(t_list)
        if not closed:
            return success_response(
                message="No closed trades to calculate profit factor.",
                data=0.0,
                metadata=meta,
            )
        gross_prof = sum(
            _get_trade_pnl(t) for t in closed if _get_trade_pnl(t) > 0
        )
        gross_l = sum(
            abs(_get_trade_pnl(t))
            for t in closed
            if _get_trade_pnl(t) < 0
        )
        factor = gross_prof / gross_l if gross_l > 0 else 999.0
        return success_response(
            message="Calculated profit factor.",
            data=factor,
            metadata=meta,
        )
    except Exception as exc:
        return response_from_exception(exception=exc, metadata=meta)


# ---------------------------------------------------------------------------
# Official tool: calculate_trade_metrics
# ---------------------------------------------------------------------------


def calculate_analytics_for_subset(
    trades: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute a full summary of trade metrics for a trade subset.

    Args:
        trades: Pre-filtered list of trade record dicts.

    Returns:
        Dict of aggregate trade metrics.

    Side effects:
        None.
    """
    closed = get_closed_trades(trades)
    if not closed:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "breakeven_trades": 0,
            "long_trades": 0,
            "short_trades": 0,
            "win_rate": 0.0,
            "net_profit": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "largest_win": 0.0,
            "largest_loss": 0.0,
            "expectancy": 0.0,
            "profit_factor": 0.0,
            "sqn": 0.0,
            "kelly_criterion": 0.0,
            "max_consecutive_wins": 0,
            "max_consecutive_losses": 0,
            "avg_time_in_trade": 0.0,
            "avg_r_multiple": 0.0,
            "slippage_paid": 0.0,
            "commission_paid": 0.0,
        }
    classes = classify_trades(closed)
    n_wins = len(classes["wins"])
    n_losses = len(classes["losses"])
    gp = sum(_get_trade_pnl(t) for t in classes["wins"])
    gl = sum(abs(_get_trade_pnl(t)) for t in classes["losses"])
    return {
        "total_trades": len(closed),
        "winning_trades": n_wins,
        "losing_trades": n_losses,
        "breakeven_trades": len(classes["breakevens"]),
        "long_trades": long_trades(closed),
        "short_trades": short_trades(closed),
        "win_rate": n_wins / len(closed),
        "net_profit": net_profit(closed),
        "gross_profit": gp,
        "gross_loss": -gl,
        "avg_win": avg_win(closed),
        "avg_loss": avg_loss(closed),
        "largest_win": largest_win(closed),
        "largest_loss": largest_loss(closed),
        "expectancy": expectancy(closed),
        "profit_factor": gp / gl if gl > 0 else 999.0,
        "sqn": sqn(closed),
        "kelly_criterion": kelly_criterion(closed),
        "max_consecutive_wins": max_consecutive_wins(closed),
        "max_consecutive_losses": max_consecutive_losses(closed),
        "avg_time_in_trade": avg_time_in_trade(closed),
        "avg_r_multiple": avg_r_multiple(closed),
        "slippage_paid": slippage_paid(closed),
        "commission_paid": commission_paid(closed),
    }


def calculate_trade_metrics(
    trades: Any,
    request_id: str | None = None,
) -> StandardResponse:
    """Calculate aggregate core trade metrics from normalised trade records.

    Args:
        trades: Trade records in any supported format.
        request_id: Optional trace identifier.

    Returns:
        ``StandardResponse`` with ``data`` containing the metrics dict.

    Side effects:
        None.
    """
    validate_request_id_strict(request_id)
    meta = build_metadata(
        tool_name="calculate_trade_metrics",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        t_list = to_trade_list(trades)
        data = calculate_analytics_for_subset(t_list)
        return success_response(
            message="Successfully calculated trade metrics.",
            data=data,
            metadata=meta,
        )
    except Exception as exc:
        return response_from_exception(exception=exc, metadata=meta)


# ---------------------------------------------------------------------------
# Official tool: get_analytics_overview
# ---------------------------------------------------------------------------


def get_analytics_overview(
    trades: Any,
    initial_balance: float = 10000.0,
    start_time: Any = None,
    end_time: Any = None,
    request_id: str | None = None,
) -> StandardResponse:
    """Calculate analytics overview across all, long, and short subsets.

    Args:
        trades: Trade records in any supported format.
        initial_balance: Starting account balance.
        start_time: Optional filter window start (any parseable timestamp).
        end_time: Optional filter window end (any parseable timestamp).
        request_id: Optional trace identifier.

    Returns:
        ``StandardResponse`` with ``data`` containing per-subset metrics.

    Side effects:
        None.
    """
    validate_request_id_strict(request_id)
    meta = build_metadata(
        tool_name="get_analytics_overview",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        t_list = to_trade_list(trades)
        closed = get_closed_trades(t_list)
        start_dt = parse_utc_time(start_time)
        end_dt = parse_utc_time(end_time)
        filtered = []
        for t in closed:
            ct = parse_utc_time(
                t.get("close_time") or t.get("close_timestamp")
            )
            if not ct:
                continue
            if start_dt and ct < start_dt:
                continue
            if end_dt and ct > end_dt:
                continue
            filtered.append(t)

        long_subset = [
            t
            for t in filtered
            if str(t.get("direction", "")).lower() in ("long", "buy")
        ]
        short_subset = [
            t
            for t in filtered
            if str(t.get("direction", "")).lower() in ("short", "sell")
        ]
        data = {
            "all": calculate_analytics_for_subset(filtered),
            "long": calculate_analytics_for_subset(long_subset),
            "short": calculate_analytics_for_subset(short_subset),
            "initial_balance": initial_balance,
        }
        return success_response(
            message="Successfully generated analytics overview.",
            data=data,
            metadata=meta,
        )
    except Exception as exc:
        return response_from_exception(exception=exc, metadata=meta)


def calculate_efficiency_metrics(
    trades: list[dict[str, Any]],
) -> dict[str, float]:
    """Compute MFE and MAE efficiency metrics for a trade list.

    Args:
        trades: List of trade record dicts.

    Returns:
        Dict with ``"mfe_efficiency"`` and ``"mae_efficiency"`` keys.

    Side effects:
        None.
    """
    return {
        "mfe_efficiency": mfe_efficiency(trades),
        "mae_efficiency": loss_containment_efficiency(trades),
    }
