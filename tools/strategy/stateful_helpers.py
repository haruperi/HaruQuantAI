"""Helper functions for stateful HaruQuant strategy examples.

Functions here do not execute trades. They help strategies inspect current
context, prices, baskets, and rolling indicators.
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from tools.strategy.contracts import PositionSnapshot, StrategyContext


def is_bar_close(context: StrategyContext) -> bool:
    """Return True when current_tick metadata indicates a bar close."""
    phase = str((context.current_tick or {}).get("is_bar_close", "") or "")
    return "close" in {part.strip().lower() for part in phase.split("|")}


def current_mid_price(context: StrategyContext) -> float:
    """Calculate the current bid/ask midpoint from a strategy context."""
    tick = context.current_tick or {}
    bid = float(tick.get("bid", 0.0) or 0.0)
    ask = float(tick.get("ask", bid) or bid)
    if bid <= 0.0:
        return ask
    if ask <= 0.0:
        return bid
    return (bid + ask) / 2.0


def historical_mid_prices(context: StrategyContext) -> pd.Series:
    """Build historical midpoint prices up to the current tick index."""
    data = context.market_data
    tick_index = int((context.metadata or {}).get("tick_index", 0) or 0)
    if data is None or data.empty or "bid" not in data.columns:
        return pd.Series(dtype="float64")
    window = data.iloc[: tick_index + 1]
    bid = pd.to_numeric(window["bid"], errors="coerce")
    ask = (
        pd.to_numeric(window["ask"], errors="coerce")
        if "ask" in window.columns
        else bid
    )
    return ((bid + ask) / 2.0).dropna()


def rolling_rsi(prices: pd.Series, period: int) -> float | None:
    """Return latest RSI value for a price series, or None for insufficient data."""
    if period <= 0:
        raise ValueError("period must be positive.")
    if len(prices) < period + 1:
        return None
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    last_loss = float(avg_loss.iloc[-1] or 0.0)
    if last_loss <= 0.0:
        return 100.0
    rs = float(avg_gain.iloc[-1] or 0.0) / last_loss
    return float(100 - (100 / (1 + rs)))


def rolling_sma(prices: pd.Series, period: int) -> float | None:
    """Return latest SMA value for a price series, or None for insufficient data."""
    if period <= 0:
        raise ValueError("period must be positive.")
    if len(prices) < period:
        return None
    value = prices.rolling(window=period, min_periods=period).mean().iloc[-1]
    return None if pd.isna(value) else float(value)


def positions_for_side(context: StrategyContext, side: str) -> list[PositionSnapshot]:
    """Return open positions for the context symbol matching BUY or SELL side."""
    target = str(side).upper()
    if target not in {"BUY", "SELL"}:
        raise ValueError("side must be BUY or SELL.")
    return [
        position
        for position in context.positions_for_symbol()
        if position.side == target
    ]


def basket_pnl(positions: Iterable[PositionSnapshot]) -> float:
    """Sum position profit/loss for a basket."""
    return float(sum(float(position.profit_loss or 0.0) for position in positions))


def weighted_average_price(positions: Iterable[PositionSnapshot]) -> float | None:
    """Return volume-weighted average open price for positions."""
    rows = list(positions)
    total_volume = sum(float(position.volume or 0.0) for position in rows)
    if total_volume <= 0.0:
        return None
    weighted = sum(
        float(row.open_price or 0.0) * float(row.volume or 0.0) for row in rows
    )
    return float(weighted / total_volume)


def oldest_position(positions: Iterable[PositionSnapshot]) -> PositionSnapshot | None:
    """Return oldest position by opened_at, or None for empty input."""
    rows = list(positions)
    if not rows:
        return None
    return sorted(rows, key=lambda position: str(position.opened_at or ""))[0]
