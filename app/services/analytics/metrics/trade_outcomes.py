# ruff: noqa: ARG001, PLR2004, E501, DTZ006, RUF100
"""Trade outcomes calculation kernel (ANL-NFR-021).

Partitions trades, calculates win/loss rates, consecutive streaks, and Shannon entropy.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from app.services.analytics._helpers import parse_utc_time
from app.services.analytics.contracts import MetricConfig, MetricResult

type TradeRecord = dict[str, Any]


def _get_trade_pnl(t: TradeRecord) -> float:
    """Helper to retrieve PnL of a trade record."""
    return float(t.get("pnl") or t.get("profit") or t.get("realized_pnl") or 0.0)


def get_closed_trades(
    trades: Sequence[TradeRecord],
    config: MetricConfig | None = None,
) -> tuple[TradeRecord, ...]:
    """Filter to closed trades (ANL-NFR-111, ANL-NFR-101)."""
    closed = []
    for t in trades:
        close_time = t.get("close_time") or t.get("close_timestamp")
        if close_time is not None and not t.get("is_open", False):
            closed.append(t)
    return tuple(closed)


def get_ordered_closed_trades(
    trades: Sequence[TradeRecord],
    config: MetricConfig | None = None,
) -> tuple[TradeRecord, ...]:
    """Sort closed trades chronologically (ANL-NFR-133)."""
    closed = get_closed_trades(trades)

    def _close_ts(t: dict[str, Any]) -> float:
        ct = t.get("close_time") or t.get("close_timestamp")
        dt = parse_utc_time(ct)
        return dt.timestamp() if dt else 0.0

    return tuple(sorted(closed, key=_close_ts))


def classify_trades(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> dict[str, list[TradeRecord]]:
    """Partition trades into wins, losses, and breakevens (ANL-NFR-112, ANL-NFR-102)."""
    eps = config.breakeven_epsilon if config is not None else 1e-9
    wins: list[TradeRecord] = []
    losses: list[TradeRecord] = []
    breakevens: list[TradeRecord] = []
    for t in trades:
        pnl = _get_trade_pnl(t)
        if pnl > eps:
            wins.append(t)
        elif pnl < -eps:
            losses.append(t)
        else:
            breakevens.append(t)
    return {"wins": wins, "losses": losses, "breakevens": breakevens}


def win_rate_fraction(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate win rate on a 0-to-1 scale (ANL-NFR-021)."""
    closed = get_closed_trades(trades)
    if not closed:
        return MetricResult(value=0.0)
    classes = classify_trades(closed, config)
    val = len(classes["wins"]) / len(closed)
    return MetricResult(value=val)


def avg_win_loss(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate ratio of mean winning to mean losing outcomes (ANL-NFR-022)."""
    closed = get_closed_trades(trades)
    if not closed:
        return MetricResult(value=0.0)
    classes = classify_trades(closed, config)
    wins = classes["wins"]
    losses = classes["losses"]
    if not wins or not losses:
        return MetricResult(value=0.0)
    mean_win = sum(_get_trade_pnl(t) for t in wins) / len(wins)
    mean_loss = sum(abs(_get_trade_pnl(t)) for t in losses) / len(losses)
    if mean_loss == 0:
        return MetricResult(value=0.0)
    val = mean_win / mean_loss
    return MetricResult(value=val)


def consecutive_wins_losses(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[dict[str, int]]:
    """Calculate maximum consecutive wins and losses from numeric outcomes (ANL-NFR-023)."""
    ordered = get_ordered_closed_trades(trades)
    if not ordered:
        return MetricResult(value={"wins": 0, "losses": 0})
    max_wins = 0
    max_losses = 0
    curr_wins = 0
    curr_losses = 0
    eps = config.breakeven_epsilon if config is not None else 1e-9
    for t in ordered:
        pnl = _get_trade_pnl(t)
        if pnl > eps:
            curr_wins += 1
            curr_losses = 0
            max_wins = max(max_wins, curr_wins)
        elif pnl < -eps:
            curr_losses += 1
            curr_wins = 0
            max_losses = max(max_losses, curr_losses)
        else:
            curr_wins = 0
            curr_losses = 0
    return MetricResult(value={"wins": max_wins, "losses": max_losses})


def t_statistic(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate the t-statistic for mean outcome (ANL-NFR-024)."""
    closed = get_closed_trades(trades)
    n = len(closed)
    if n < 2:
        return MetricResult(value=0.0)
    pnls = [_get_trade_pnl(t) for t in closed]
    mean = sum(pnls) / n
    var = sum((x - mean) ** 2 for x in pnls) / (n - 1)
    if var == 0:
        return MetricResult(value=0.0)
    val = mean / (math.sqrt(var) / math.sqrt(n))
    return MetricResult(value=val)


def expectancy_r(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate R-expectancy (ANL-NFR-030)."""
    closed = get_closed_trades(trades)
    if not closed:
        return MetricResult(value=0.0)
    r_multiples = []
    for t in closed:
        risk = float(t.get("initial_risk") or 1.0)
        pnl = _get_trade_pnl(t)
        r_multiples.append(pnl / risk if risk > 0 else pnl)
    if not r_multiples:
        return MetricResult(value=0.0)
    val = sum(r_multiples) / len(r_multiples)
    return MetricResult(value=val)


def avg_r_multiple(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate average R-multiple (ANL-NFR-035)."""
    return expectancy_r(trades, config)


def median_r_multiple(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate median R-multiple (ANL-NFR-036)."""
    closed = get_closed_trades(trades)
    if not closed:
        return MetricResult(value=0.0)
    r_multiples = []
    for t in closed:
        risk = float(t.get("initial_risk") or 1.0)
        pnl = _get_trade_pnl(t)
        r_multiples.append(pnl / risk if risk > 0 else pnl)
    if not r_multiples:
        return MetricResult(value=0.0)
    r_multiples.sort()
    n = len(r_multiples)
    if n % 2 == 1:
        val = r_multiples[n // 2]
    else:
        val = (r_multiples[n // 2 - 1] + r_multiples[n // 2]) / 2.0
    return MetricResult(value=val)


def r_expectancy(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate R-space expectancy (ANL-NFR-037)."""
    return expectancy_r(trades, config)


def max_r_multiple(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate maximum R-multiple (ANL-NFR-038)."""
    closed = get_closed_trades(trades)
    if not closed:
        return MetricResult(value=0.0)
    r_multiples = []
    for t in closed:
        risk = float(t.get("initial_risk") or 1.0)
        pnl = _get_trade_pnl(t)
        r_multiples.append(pnl / risk if risk > 0 else pnl)
    val = max(r_multiples, default=0.0)
    return MetricResult(value=val)


def min_r_multiple(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate minimum R-multiple (ANL-NFR-039)."""
    closed = get_closed_trades(trades)
    if not closed:
        return MetricResult(value=0.0)
    r_multiples = []
    for t in closed:
        risk = float(t.get("initial_risk") or 1.0)
        pnl = _get_trade_pnl(t)
        r_multiples.append(pnl / risk if risk > 0 else pnl)
    val = min(r_multiples, default=0.0)
    return MetricResult(value=val)


def avg_consecutive_wins(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate average length of winning streaks (ANL-NFR-040)."""
    ordered = get_ordered_closed_trades(trades)
    if not ordered:
        return MetricResult(value=0.0)
    streaks = []
    curr = 0
    eps = config.breakeven_epsilon if config is not None else 1e-9
    for t in ordered:
        if _get_trade_pnl(t) > eps:
            curr += 1
        elif curr > 0:
            streaks.append(curr)
            curr = 0
    if curr > 0:
        streaks.append(curr)
    val = sum(streaks) / len(streaks) if streaks else 0.0
    return MetricResult(value=val)


def avg_consecutive_losses(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate average length of losing streaks (ANL-NFR-041)."""
    ordered = get_ordered_closed_trades(trades)
    if not ordered:
        return MetricResult(value=0.0)
    streaks = []
    curr = 0
    eps = config.breakeven_epsilon if config is not None else 1e-9
    for t in ordered:
        if _get_trade_pnl(t) < -eps:
            curr += 1
        elif curr > 0:
            streaks.append(curr)
            curr = 0
    if curr > 0:
        streaks.append(curr)
    val = sum(streaks) / len(streaks) if streaks else 0.0
    return MetricResult(value=val)


def r_signal_to_noise(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate mean R relative to R volatility (ANL-NFR-042)."""
    closed = get_closed_trades(trades)
    if len(closed) < 2:
        return MetricResult(value=0.0)
    r_multiples = []
    for t in closed:
        risk = float(t.get("initial_risk") or 1.0)
        pnl = _get_trade_pnl(t)
        r_multiples.append(pnl / risk if risk > 0 else pnl)
    mean = sum(r_multiples) / len(r_multiples)
    var = sum((x - mean) ** 2 for x in r_multiples) / (len(r_multiples) - 1)
    if var == 0:
        return MetricResult(value=0.0)
    val = mean / math.sqrt(var)
    return MetricResult(value=val)


def rolling_expectancy_stability(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate expectancy stability over a rolling window (ANL-NFR-043)."""
    # Assuming window size = 10 (or dynamically configured)
    window = 10
    closed = get_ordered_closed_trades(trades)
    if len(closed) < window:
        return MetricResult(value=0.0)
    pnls = [_get_trade_pnl(t) for t in closed]
    expectancies = [
        sum(pnls[i : i + window]) / window for i in range(len(pnls) - window + 1)
    ]
    n = len(expectancies)
    if n < 2:
        return MetricResult(value=0.0)
    mean = sum(expectancies) / n
    var = sum((x - mean) ** 2 for x in expectancies) / (n - 1)
    val = math.sqrt(var)
    return MetricResult(value=val)


def win_after_win_probability(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate probability that a win follows a win (ANL-NFR-044)."""
    ordered = get_ordered_closed_trades(trades)
    if len(ordered) < 2:
        return MetricResult(value=0.0)
    wins_after_win = 0
    total_wins = 0
    eps = config.breakeven_epsilon if config is not None else 1e-9
    for i in range(len(ordered) - 1):
        if _get_trade_pnl(ordered[i]) > eps:
            total_wins += 1
            if _get_trade_pnl(ordered[i + 1]) > eps:
                wins_after_win += 1
    val = wins_after_win / total_wins if total_wins > 0 else 0.0
    return MetricResult(value=val)


def runs_test_zscore(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate Wald-Wolfowitz runs-test z-score (ANL-NFR-045)."""
    ordered = get_ordered_closed_trades(trades)
    n = len(ordered)
    if n < 2:
        return MetricResult(value=0.0)
    eps = config.breakeven_epsilon if config is not None else 1e-9
    signs = [1 if _get_trade_pnl(t) > eps else -1 for t in ordered]
    runs = 1
    for i in range(1, n):
        if signs[i] != signs[i - 1]:
            runs += 1
    n1 = sum(1 for x in signs if x == 1)
    n2 = n - n1
    if n1 == 0 or n2 == 0:
        return MetricResult(value=0.0)
    mu = (2.0 * n1 * n2) / n + 1.0
    var = (2.0 * n1 * n2 * (2.0 * n1 * n2 - n)) / (n * n * (n - 1.0))
    if var == 0:
        return MetricResult(value=0.0)
    val = (runs - mu) / math.sqrt(var)
    return MetricResult(value=val)


def avg_loss(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate the mean loss of losing trades (ANL-NFR-113)."""
    closed = get_closed_trades(trades)
    classes = classify_trades(closed, config)
    losses = classes["losses"]
    if not losses:
        return MetricResult(value=0.0)
    val = sum(_get_trade_pnl(t) for t in losses) / len(losses)
    return MetricResult(value=val)


def total_trades(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[int]:
    """Count closed trades (ANL-NFR-134)."""
    val = len(get_closed_trades(trades))
    return MetricResult(value=val)


def winning_trades(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[int]:
    """Count closed winning trades (ANL-NFR-135)."""
    closed = get_closed_trades(trades)
    classes = classify_trades(closed, config)
    val = len(classes["wins"])
    return MetricResult(value=val)


def losing_trades(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[int]:
    """Count closed losing trades (ANL-NFR-136)."""
    closed = get_closed_trades(trades)
    classes = classify_trades(closed, config)
    val = len(classes["losses"])
    return MetricResult(value=val)


def breakeven_trades(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[int]:
    """Count closed breakeven trades (ANL-NFR-137)."""
    closed = get_closed_trades(trades)
    classes = classify_trades(closed, config)
    val = len(classes["breakevens"])
    return MetricResult(value=val)


def long_trades(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[int]:
    """Count closed long trades (ANL-NFR-138)."""
    closed = get_closed_trades(trades)
    val = sum(
        1 for t in closed if str(t.get("direction", "")).lower() in ("long", "buy")
    )
    return MetricResult(value=val)


def short_trades(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[int]:
    """Count closed short trades (ANL-NFR-139)."""
    closed = get_closed_trades(trades)
    val = sum(
        1 for t in closed if str(t.get("direction", "")).lower() in ("short", "sell")
    )
    return MetricResult(value=val)


def count_open_trades(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[int]:
    """Count currently open trades (ANL-NFR-140)."""
    val = sum(
        1 for t in trades if t.get("is_open", False) or t.get("close_time") is None
    )
    return MetricResult(value=val)


def win_rate(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate percentage of winning trades (ANL-NFR-141)."""
    closed = get_closed_trades(trades)
    if not closed:
        return MetricResult(value=0.0)
    classes = classify_trades(closed, config)
    val = (len(classes["wins"]) / len(closed)) * 100.0
    return MetricResult(value=val)


def loss_rate(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate percentage of losing trades (ANL-NFR-142)."""
    closed = get_closed_trades(trades)
    if not closed:
        return MetricResult(value=0.0)
    classes = classify_trades(closed, config)
    val = (len(classes["losses"]) / len(closed)) * 100.0
    return MetricResult(value=val)


def avg_win(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate mean profit of winning trades (ANL-NFR-143)."""
    closed = get_closed_trades(trades)
    classes = classify_trades(closed, config)
    wins = classes["wins"]
    if not wins:
        return MetricResult(value=0.0)
    val = sum(_get_trade_pnl(t) for t in wins) / len(wins)
    return MetricResult(value=val)


def largest_win(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate maximum single-trade profit (ANL-NFR-144)."""
    closed = get_closed_trades(trades)
    if not closed:
        return MetricResult(value=0.0)
    val = max((_get_trade_pnl(t) for t in closed), default=0.0)
    return MetricResult(value=max(0.0, val))


def largest_loss(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate maximum single-trade loss (ANL-NFR-145)."""
    closed = get_closed_trades(trades)
    if not closed:
        return MetricResult(value=0.0)
    val = min((_get_trade_pnl(t) for t in closed), default=0.0)
    return MetricResult(value=min(0.0, val))


def median_win(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate median PnL of winning trades (ANL-NFR-146)."""
    closed = get_closed_trades(trades)
    classes = classify_trades(closed, config)
    wins = sorted([_get_trade_pnl(t) for t in classes["wins"]])
    if not wins:
        return MetricResult(value=0.0)
    n = len(wins)
    val = wins[n // 2] if n % 2 == 1 else (wins[n // 2 - 1] + wins[n // 2]) / 2.0
    return MetricResult(value=val)


def median_loss(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate median PnL of losing trades (ANL-NFR-147)."""
    closed = get_closed_trades(trades)
    classes = classify_trades(closed, config)
    losses = sorted([_get_trade_pnl(t) for t in classes["losses"]])
    if not losses:
        return MetricResult(value=0.0)
    n = len(losses)
    val = losses[n // 2] if n % 2 == 1 else (losses[n // 2 - 1] + losses[n // 2]) / 2.0
    return MetricResult(value=val)


def expectancy(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate trade expectancy (ANL-NFR-148)."""
    closed = get_closed_trades(trades)
    if not closed:
        return MetricResult(value=0.0)
    val = sum(_get_trade_pnl(t) for t in closed) / len(closed)
    return MetricResult(value=val)


def max_consecutive_wins(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[int]:
    """Calculate maximum consecutive winning trades (ANL-NFR-149)."""
    res = consecutive_wins_losses(trades, config)
    # Extract the dictionary value
    val = res.value["wins"] if res.value else 0
    return MetricResult(value=val)


def max_consecutive_losses(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[int]:
    """Calculate maximum consecutive losing trades (ANL-NFR-150)."""
    res = consecutive_wins_losses(trades, config)
    val = res.value["losses"] if res.value else 0
    return MetricResult(value=val)


def trade_outcome_entropy(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate Shannon entropy of trade outcomes (ANL-NFR-158)."""
    closed = get_closed_trades(trades)
    if not closed:
        return MetricResult(value=0.0)
    classes = classify_trades(closed, config)
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
    return MetricResult(value=entropy)


def avg_win_metric(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Expose average win as MetricResult."""
    return avg_win(trades, config)


def avg_loss_metric(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Expose average loss as MetricResult."""
    return avg_loss(trades, config)


def expectancy_metric(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Expose trade expectancy as MetricResult."""
    return expectancy(trades, config)


def loss_rate_fraction(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Expose loss rate fraction as MetricResult."""
    return loss_rate(trades, config)


shannon_entropy = trade_outcome_entropy

