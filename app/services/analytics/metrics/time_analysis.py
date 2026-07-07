# ruff: noqa: ARG001, PLR2004, E501, DTZ006, RUF100
"""Trade duration and market presence calculations (ANL-NFR-061)."""

from __future__ import annotations

import datetime
from collections.abc import Sequence
from typing import Any

from app.services.analytics.contracts import MetricConfig, MetricResult
from app.services.analytics.metrics.efficiency import (
    _get_trade_duration,
    _sorted_median,
)
from app.services.analytics.metrics.position_exposure import time_in_market_duration
from app.services.analytics.metrics.trade_outcomes import (
    _get_trade_pnl,
    get_closed_trades,
    get_ordered_closed_trades,
    parse_utc_time,
)
from app.utils.logger import logger

type TradeRecord = dict[str, Any]
type Duration = datetime.timedelta | float


def calculate_period_analysis(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Aggregate net PnL per calendar bucket (ANL-NFR-061).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated dict[str, float value.
    """
    logger.debug("calculate_period_analysis: executed.")
    bucket = config.metadata.get("bucket", "monthly")
    ordered = get_ordered_closed_trades(trades)
    results: dict[str, float] = {}
    for t in ordered:
        ct = parse_utc_time(t.get("close_time") or t.get("close_timestamp"))
        if not ct:
            continue
        key = ct.strftime("%Y-%m") if bucket == "monthly" else ct.strftime("%Y")
        results[key] = results.get(key, 0.0) + _get_trade_pnl(t)
    return MetricResult(value=results)


def calculate_long_short_split(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Split net PnL into long and short components (ANL-NFR-062).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated dict[str, float value.
    """
    logger.debug("calculate_long_short_split: executed.")
    closed = get_closed_trades(trades)
    longs = [
        t for t in closed if str(t.get("direction", "")).lower() in ("long", "buy")
    ]
    shorts = [
        t for t in closed if str(t.get("direction", "")).lower() in ("short", "sell")
    ]
    val = {
        "long_pnl": sum(_get_trade_pnl(t) for t in longs),
        "short_pnl": sum(_get_trade_pnl(t) for t in shorts),
    }
    return MetricResult(value=val)


def calculate_session_performance(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Aggregate PnL per trading session (ANL-NFR-063).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated dict[str, float value.
    """
    logger.debug("calculate_session_performance: executed.")
    ordered = get_ordered_closed_trades(trades)
    sessions = {"asian": 0.0, "london": 0.0, "newyork": 0.0}
    for t in ordered:
        ct = parse_utc_time(t.get("close_time") or t.get("close_timestamp"))
        if not ct:
            continue
        hr = ct.hour
        if hr < 8:
            sessions["asian"] += _get_trade_pnl(t)
        elif hr < 16:
            sessions["london"] += _get_trade_pnl(t)
        else:
            sessions["newyork"] += _get_trade_pnl(t)
    return MetricResult(value=sessions)


def avg_time_in_trade(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate average trade duration in hours (ANL-NFR-191).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("avg_time_in_trade: executed.")
    durations = [_get_trade_duration(t) for t in get_closed_trades(trades)]
    if not durations:
        return MetricResult(value=0.0)
    val = sum(durations) / len(durations)
    return MetricResult(value=val)


def median_time_in_trade(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate median trade duration in hours (ANL-NFR-192).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("median_time_in_trade: executed.")
    durations = sorted(_get_trade_duration(t) for t in get_closed_trades(trades))
    val = _sorted_median(durations)
    return MetricResult(value=val)


def max_time_in_trade(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate maximum trade duration in hours (ANL-NFR-193).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("max_time_in_trade: executed.")
    val = max(
        (_get_trade_duration(t) for t in get_closed_trades(trades)),
        default=0.0,
    )
    return MetricResult(value=val)


def min_time_in_trade(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate minimum trade duration in hours (ANL-NFR-194).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("min_time_in_trade: executed.")
    closed = get_closed_trades(trades)
    if not closed:
        return MetricResult(value=0.0)
    val = min(_get_trade_duration(t) for t in closed)
    return MetricResult(value=val)


def time_in_market_duration_metric(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate total duration where at least one position was open in hours (ANL-NFR-313).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("time_in_market_duration_metric: executed.")
    val = time_in_market_duration(trades)
    return MetricResult(value=val)


def trading_period_duration(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate total duration of the trading period in hours (ANL-NFR-314).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("trading_period_duration: executed.")
    ordered = get_ordered_closed_trades(trades)
    if len(ordered) < 2:
        return MetricResult(value=0.0)
    ot = parse_utc_time(ordered[0].get("open_time") or ordered[0].get("open_timestamp"))
    ct = parse_utc_time(
        ordered[-1].get("close_time") or ordered[-1].get("close_timestamp")
    )
    if ot and ct:
        val = max((ct - ot).total_seconds() / 3600.0, 0.0)
        return MetricResult(value=val)
    return MetricResult(value=0.0)
