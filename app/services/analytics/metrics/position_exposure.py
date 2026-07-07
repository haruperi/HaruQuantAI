# ruff: noqa: ARG001, PLR2004
"""Position exposure metrics calculation kernel (ANL-NFR-018).

Calculates gross/net size, open-PnL, time-in-market, and cost totals.
"""

from __future__ import annotations

import datetime
from collections.abc import Sequence
from typing import Any

from app.services.analytics._helpers import parse_utc_time
from app.services.analytics.contracts import MetricConfig, MetricResult

type TradeRecord = dict[str, Any]
type Duration = datetime.timedelta | float


def max_gross_size_held(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate the maximum individual absolute trade size (ANL-NFR-018)."""
    val = max(
        (abs(float(t.get("size") or t.get("volume") or 0.0)) for t in trades),
        default=0.0,
    )
    return MetricResult(value=val)


def max_size_held(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate maximum total contracts held (ANL-NFR-031)."""
    val = max(
        (abs(float(t.get("size") or t.get("volume") or 0.0)) for t in trades),
        default=0.0,
    )
    return MetricResult(value=val)


def max_net_size_held(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate maximum net directional size held (ANL-NFR-032)."""
    ordered = sorted(
        trades,
        key=lambda t: (
            parse_utc_time(t.get("open_time") or t.get("open_timestamp") or 0)
            or datetime.datetime.min.replace(tzinfo=datetime.UTC)
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
    return MetricResult(value=max_abs_net)


def max_long_size_held(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate maximum total long contracts held (ANL-NFR-033)."""
    longs = [
        float(t.get("size") or t.get("volume") or 0.0)
        for t in trades
        if str(t.get("direction", "")).lower() in ("long", "buy")
    ]
    val = max(longs, default=0.0)
    return MetricResult(value=val)


def max_short_size_held(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate maximum total short contracts held (ANL-NFR-034)."""
    shorts = [
        float(t.get("size") or t.get("volume") or 0.0)
        for t in trades
        if str(t.get("direction", "")).lower() in ("short", "sell")
    ]
    val = max(shorts, default=0.0)
    return MetricResult(value=val)


def time_in_market_duration(trades: Sequence[TradeRecord]) -> float:
    """Helper to compute total duration where at least one position was open."""
    intervals = []
    for t in trades:
        ot = parse_utc_time(t.get("open_time") or t.get("open_timestamp"))
        ct = parse_utc_time(t.get("close_time") or t.get("close_timestamp"))
        if ot and ct:
            intervals.append((ot.timestamp(), ct.timestamp()))
    if not intervals:
        return 0.0
    intervals.sort()
    merged = []
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
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate percent of the trading period spent in the market (ANL-NFR-019)."""
    valid_trades = []
    for t in trades:
        ot = parse_utc_time(t.get("open_time") or t.get("open_timestamp"))
        if ot is not None:
            valid_trades.append((ot, t))
    if len(valid_trades) < 2:
        return MetricResult(value=0.0)
    valid_trades.sort(key=lambda x: x[0].timestamp())
    ot_first = valid_trades[0][0]
    ct_val = valid_trades[-1][1].get("close_time") or valid_trades[-1][1].get(
        "close_timestamp"
    )
    ct_last = parse_utc_time(ct_val)
    if ct_last is None:
        return MetricResult(value=0.0)

    total_hours = (ct_last.timestamp() - ot_first.timestamp()) / 3600.0
    if total_hours <= 0:
        return MetricResult(value=0.0)

    in_market_hours = time_in_market_duration(trades)
    val = in_market_hours / total_hours
    return MetricResult(value=val)


def open_position_pnl(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate total unrealized PnL from open positions (ANL-NFR-025)."""
    val = sum(
        float(t.get("unrealized_pnl") or t.get("pnl") or 0.0)
        for t in trades
        if t.get("is_open", False) or t.get("close_time") is None
    )
    return MetricResult(value=val)


def slippage_paid(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate total absolute slippage costs paid (ANL-NFR-026)."""
    val = sum(abs(float(t.get("slippage") or 0.0)) for t in trades)
    return MetricResult(value=val)


def commission_paid(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate total absolute commission costs paid (ANL-NFR-027)."""
    val = sum(abs(float(t.get("commission") or 0.0)) for t in trades)
    return MetricResult(value=val)


def swap_paid(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate total absolute swap costs paid (ANL-NFR-028)."""
    val = sum(abs(float(t.get("swap") or t.get("swap_cost") or 0.0)) for t in trades)
    return MetricResult(value=val)
