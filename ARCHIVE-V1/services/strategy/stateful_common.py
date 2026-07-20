"""Stateful strategy helper tools.

Purpose:
    Provide AI-callable utility tools for strategy signal columns, tick prices,
    rolling indicators, and position basket calculations.

Exported AI Tools:
    - ensure_signal_columns: Add canonical signal columns to market data.
    - ensure_no_signal_columns: Add neutral signal columns to market data.
    - is_bar_close: Detect whether a stateful context is at bar close.
    - current_mid_price: Calculate the current bid/ask midpoint.
    - historical_mid_prices: Build historical midpoint prices from tick data.
    - rolling_rsi: Calculate latest rolling RSI.
    - rolling_sma: Calculate latest rolling SMA.
    - positions_for_side: Filter context positions by side.
    - basket_pnl: Sum open position profit/loss.
    - weighted_average_price: Calculate volume-weighted open price.
    - oldest_position: Return the oldest position in a basket.

Classes:
    None.
"""

from __future__ import annotations

import math
import numbers
from collections.abc import Iterable
from typing import Any

import pandas as pd
from app.services.trading.stateful import PositionSnapshot, StrategyContext
from app.services.utils.logger import logger

TOOL_NAME = "stateful_strategy_helpers"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "strategy"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False

SIGNAL_COLUMN_DEFAULTS: dict[str, Any] = {
    "entry_signal": 0,
    "exit_signal": 0,
    "pending_signal": 0,
    "cancel_pending_signal": 0,
    "pending_signal_2": 0,
    "cancel_pending_signal_2": 0,
    "price": float("nan"),
    "price_2": float("nan"),
    "stop_loss": float("nan"),
    "take_profit": float("nan"),
    "signal_reason": "",
    "setup_id": "",
    "group_id": "",
}

ACTIVATOR_COLUMN_DEFAULTS: dict[str, bool] = {
    "buy_setup_active": False,
    "sell_setup_active": False,
    "buy_add_active": False,
    "sell_add_active": False,
    "buy_exit_active": False,
    "sell_exit_active": False,
    "buy_pyramid_active": False,
    "sell_pyramid_active": False,
    "buy_martingale_active": False,
    "sell_martingale_active": False,
    "buy_decompose_active": False,
    "sell_decompose_active": False,
    "buy_trail_active": False,
    "sell_trail_active": False,
}


def ensure_signal_columns(
    data: pd.DataFrame,
    *,
    include_activators: bool = False,
    include_compat_columns: bool = True,
) -> pd.DataFrame:
    """
    Return bars with the HaruQuant v1.0 strategy signal schema.

    Use this tool when an agent needs to prepare OHLCV/tick data for strategy
    execution by ensuring expected signal, price, stop, target, and optional
    activator columns exist.

    Args:
        data (pd.DataFrame): Source market data.
        include_activators (bool): Whether to add event activator columns.
        include_compat_columns (bool): Whether to add legacy sl/tp columns.

    Returns:
        pd.DataFrame: Copy of data with missing signal columns added.
    """
    logger.info("ensure_signal_columns called | rows=%s", len(data))
    out = data.copy()
    defaults: dict[str, Any] = dict(SIGNAL_COLUMN_DEFAULTS)
    if include_activators:
        defaults.update(ACTIVATOR_COLUMN_DEFAULTS)
    if include_compat_columns:
        defaults.update({"sl": 0.0, "tp": 0.0})

    for column, default in defaults.items():
        if column not in out.columns:
            out[column] = default
    logger.info("ensure_signal_columns completed | columns=%s", len(out.columns))
    return out


def ensure_no_signal_columns(data: pd.DataFrame) -> pd.DataFrame:
    """
    Return bars with neutral signal columns for tick generation.

    Use this tool when an agent needs a data frame that explicitly contains no
    active entries, exits, pending orders, or activator events.

    Args:
        data (pd.DataFrame): Source market data.

    Returns:
        pd.DataFrame: Copy of data with all signal fields set to neutral values.
    """
    logger.info("ensure_no_signal_columns called | rows=%s", len(data))
    out = ensure_signal_columns(data, include_activators=True)
    for column in (
        "entry_signal",
        "exit_signal",
        "pending_signal",
        "cancel_pending_signal",
        "pending_signal_2",
        "cancel_pending_signal_2",
    ):
        out[column] = 0
    for column in ("price", "price_2", "stop_loss", "take_profit"):
        out[column] = float("nan")
    for column in ("signal_reason", "setup_id", "group_id"):
        out[column] = ""
    for column in ACTIVATOR_COLUMN_DEFAULTS:
        out[column] = False
    out["sl"] = 0.0
    out["tp"] = 0.0
    logger.info("ensure_no_signal_columns completed | rows=%s", len(out))
    return out


def is_bar_close(context: StrategyContext) -> bool:
    """
    Detect whether the current strategy context is at bar close.

    Args:
        context (StrategyContext): Stateful strategy context containing the
            current tick metadata.

    Returns:
        bool: True when current_tick["is_bar_close"] contains "close".
    """
    phase: object = ""
    if context.current_tick:
        phase = context.current_tick.get("is_bar_close", "") or ""
    if isinstance(phase, bool):
        return phase
    if isinstance(phase, numbers.Real):
        value = float(phase)
        if not math.isfinite(value):
            return False
        return bool(int(value) & 8)
    return "close" in {part.strip().lower() for part in str(phase).split("|")}


def current_mid_price(context: StrategyContext) -> float:
    """
    Calculate the current bid/ask midpoint from a strategy context.

    Args:
        context (StrategyContext): Context with current_tick bid and ask values.

    Returns:
        float: Midpoint price, or the available side when bid or ask is absent.
    """
    tick = context.current_tick or {}
    bid = float(tick.get("bid", 0.0) or 0.0)
    ask = float(tick.get("ask", bid) or bid)
    if bid <= 0.0:
        return ask
    if ask <= 0.0:
        return bid
    return (bid + ask) / 2.0


def historical_mid_prices(context: StrategyContext) -> pd.Series:
    """
    Build historical midpoint prices up to the current tick index.

    Args:
        context (StrategyContext): Context containing market_data and metadata.

    Returns:
        pd.Series: Non-null midpoint series derived from bid/ask columns.
    """
    data = context.market_data
    tick_index = int(context.metadata.get("tick_index", 0) if context.metadata else 0)
    if data is None or data.empty:
        return pd.Series(dtype="float64")
    window = data.iloc[: tick_index + 1]
    if "bid" not in window.columns:
        return pd.Series(dtype="float64")
    bid = pd.to_numeric(window["bid"], errors="coerce")
    ask = (
        pd.to_numeric(window["ask"], errors="coerce")
        if "ask" in window.columns
        else bid
    )
    mid = (bid + ask) / 2.0
    return mid.dropna()


def rolling_rsi(prices: pd.Series, period: int) -> float | None:
    """
    Calculate the latest rolling RSI value.

    Args:
        prices (pd.Series): Price series.
        period (int): RSI period.

    Returns:
        float | None: Latest RSI, or None when insufficient history exists.
    """
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
    """
    Calculate the latest simple moving average value.

    Args:
        prices (pd.Series): Price series.
        period (int): SMA period.

    Returns:
        float | None: Latest SMA, or None when insufficient history exists.
    """
    if len(prices) < period:
        return None
    value = prices.rolling(window=period, min_periods=period).mean().iloc[-1]
    return None if pd.isna(value) else float(value)


def positions_for_side(
    context: StrategyContext,
    side: str,
) -> list[PositionSnapshot]:
    """
    Return open positions in the current context matching a side.

    Args:
        context (StrategyContext): Strategy context with open positions.
        side (str): BUY or SELL side to match case-insensitively.

    Returns:
        list[PositionSnapshot]: Matching positions for the context symbol.
    """
    target = str(side).upper()
    return [
        position
        for position in context.positions_for_symbol()
        if str(position.side).upper() == target
    ]


def basket_pnl(positions: Iterable[PositionSnapshot]) -> float:
    """
    Sum profit/loss for a basket of positions.

    Args:
        positions (Iterable[PositionSnapshot]): Positions to aggregate.

    Returns:
        float: Total position profit/loss.
    """
    return float(sum(float(position.profit_loss or 0.0) for position in positions))


def weighted_average_price(positions: Iterable[PositionSnapshot]) -> float | None:
    """
    Calculate volume-weighted average open price for a basket.

    Args:
        positions (Iterable[PositionSnapshot]): Positions to aggregate.

    Returns:
        float | None: Weighted average open price, or None when volume is zero.
    """
    rows = list(positions)
    total_volume = sum(float(position.volume or 0.0) for position in rows)
    if total_volume <= 0.0:
        return None
    weighted = sum(
        float(position.open_price or 0.0) * float(position.volume or 0.0)
        for position in rows
    )
    return float(weighted / total_volume)


def oldest_position(positions: Iterable[PositionSnapshot]) -> PositionSnapshot | None:
    """
    Return the oldest position in a basket.

    Args:
        positions (Iterable[PositionSnapshot]): Positions to inspect.

    Returns:
        PositionSnapshot | None: Oldest position by opened_at, or None for an
        empty basket.
    """
    rows = list(positions)
    if not rows:
        return None
    return sorted(rows, key=lambda position: str(position.opened_at or ""))[0]
