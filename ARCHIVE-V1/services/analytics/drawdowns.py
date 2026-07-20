"""drawdowns.py - Calculate equity and trade-level drawdown depth, duration, and recovery metrics.

This module provides comprehensive analytics for assessing the downside risk of trading strategies,
including traditional equity curve drawdowns, trade-level excursions, and pain-based indices.

Classes:
    None.

Functions:
    _clean_equity: Helper to ensure equity series is clean, sorted, and datetime-indexed.
    _sort_trades_for_drawdown: Safely sort trades by close_time or open_time for drawdown analysis.
    _returns_array: Normalize returns-like input to a float NumPy array.
    _max_drawdown_duration_kernel: Return the longest run of periods below the running equity peak.
    _drawdown_duration_series_kernel: Return the current drawdown duration at each equity observation.
    _max_close_to_close_drawdown_kernel: Calculate maximum trade-path drawdown using MFE, MAE, and closing PnL.
    _max_close_to_close_drawdown_percent_kernel: Calculate maximum trade-path drawdown as a percentage of peak.
    _drawdown_series_impl: Internal implementation for drawdown series calculation.
    _drawdown_duration_series_impl: Internal implementation for drawdown duration series calculation.
    _max_strategy_drawdown_impl: Internal implementation for maximum strategy drawdown (currency).
    _max_strategy_drawdown_percent_impl: Internal implementation for maximum strategy drawdown percentage.
    _max_drawdown_impl: Internal implementation for maximum drawdown from returns.
    _avg_drawdown_impl: Internal implementation for average drawdown depth.
    _drawdown_distribution_impl: Internal implementation for drawdown distribution statistics.
    _max_drawdown_duration_from_equity_impl: Internal implementation for max drawdown duration from equity.
    _max_drawdown_duration_from_returns_impl: Internal implementation for max drawdown duration from returns.
    _max_drawdown_duration_impl: Internal implementation for maximum drawdown duration.
    _avg_drawdown_duration_impl: Internal implementation for average drawdown duration.
    _time_to_recovery_impl: Internal implementation for list of recovery periods.
    _recovery_factor_impl: Internal implementation for recovery factor.
    _trade_level_drawdowns_impl: Internal implementation for trade-level drawdowns.
    _max_close_to_close_drawdown_impl: Internal implementation for maximum close-to-close drawdown.
    _max_close_to_close_drawdown_percent_impl: Internal implementation for max close-to-close drawdown percentage.
    _avg_trade_drawdown_impl: Internal implementation for average trade-level drawdown.
    _account_size_required_impl: Internal implementation for capital required.
    _max_consecutive_drawdown_trades_impl: Internal implementation for max consecutive drawdown trades.
    _avg_yearly_max_drawdown_impl: Internal implementation for average of yearly max drawdowns.
    _max_strategy_drawdown_date_impl: Internal implementation for date of deepest strategy drawdown.
    _max_close_to_close_drawdown_date_impl: Internal implementation for date of deepest trade-level valley.
    _ulcer_index_impl: Internal implementation for Ulcer Index.
    _pain_index_impl: Internal implementation for Pain Index.
    _avg_underwater_drawdown_percent_impl: Internal implementation for average underwater drawdown.
    _pain_ratio_impl: Internal implementation for Pain Ratio.
    _calculate_drawdown_metrics_impl: Internal implementation for bulk drawdown metrics.
    drawdown_series: AI Tool for calculating drawdown series from equity.
    drawdown_duration_series: AI Tool for calculating drawdown duration series.
    max_strategy_drawdown: AI Tool for deepest peak-to-valley decline (currency).
    max_strategy_drawdown_percent: AI Tool for deepest percentage decline.
    max_drawdown: AI Tool for maximum drawdown from returns.
    avg_drawdown: AI Tool for average depth of drawdown periods.
    drawdown_distribution: AI Tool for detailed drawdown distribution statistics.
    max_drawdown_duration_from_equity: AI Tool for max periods in drawdown from equity.
    max_drawdown_duration_from_returns: AI Tool for max periods in drawdown from returns.
    max_drawdown_duration: AI Tool for maximum periods spent in drawdown.
    avg_drawdown_duration: AI Tool for average duration of drawdown episodes.
    time_to_recovery: AI Tool for recovery periods for each unique drawdown.
    recovery_factor: AI Tool for net profit relative to maximum drawdown.
    trade_level_drawdowns: AI Tool for cumulative P&L drawdowns at trade close.
    max_close_to_close_drawdown: AI Tool for max drawdown including intra-trade excursions.
    max_close_to_close_drawdown_percent: AI Tool for percentage version of close-to-close drawdown.
    avg_trade_drawdown: AI Tool for mean depth of trade-level drawdowns.
    account_size_required: AI Tool for capital required to withstand max dips.
    max_consecutive_drawdown_trades: AI Tool for max consecutive trades in strategy drawdown.
    avg_yearly_max_drawdown: AI Tool for average of maximum drawdowns in each year.
    max_strategy_drawdown_date: AI Tool for date of absolute deepest strategy valley.
    max_close_to_close_drawdown_date: AI Tool for date of deepest trade-level valley.
    ulcer_index: AI Tool for Ulcer Index.
    pain_index: AI Tool for Pain Index.
    avg_underwater_drawdown_percent: AI Tool for average underwater drawdown depth.
    pain_ratio: AI Tool for Pain Ratio.
    calculate_drawdown_metrics: AI Tool for bulk drawdown metrics from equity.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.services.utils.logger import logger

from .common import _has_col, analytics_tool_result, get_closed_trades

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "analytics"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False
CREATES = False
READS = True
UPDATES = False
DELETES = False
TRADES = False


try:
    from numba import njit
except ImportError:

    def njit(*args, **kwargs):
        """Return a no-op decorator when numba is unavailable."""

        def decorator(f):
            """Return the original function unchanged."""
            return f

        return decorator


def _clean_equity(equity: pd.Series) -> pd.Series:
    """Helper to ensure equity series is clean, sorted, and datetime-indexed.

    Logic:
        1. Checks if the series is empty.
        2. Replaces infinity values with NaN and drops all NaN entries.
        3. Attempts to convert the index to a DatetimeIndex if it isn't one.
        4. Sorts the series by index to ensure chronological order.

    Args:
        equity (pd.Series): Raw equity series.

    Returns:
        pd.Series: Cleaned and sorted equity series.
    """
    if equity is None or len(equity) == 0:
        return pd.Series(dtype=float)

    equity = equity.replace([np.inf, -np.inf], np.nan).dropna()

    if not isinstance(equity.index, pd.DatetimeIndex):
        try:
            equity.index = pd.to_datetime(equity.index)
        except (ValueError, TypeError):
            # If conversion fails, keep as is (likely numeric index)
            pass

    return equity.sort_index()


def _sort_trades_for_drawdown(trades: pd.DataFrame) -> pd.DataFrame:
    """Safely sort trades by close_time or open_time for drawdown analysis.

    Logic:
        1. Prefers 'close_time' for sorting to reflect the realized PnL sequence.
        2. Falls back to 'open_time' if 'close_time' is missing.
        3. Returns a copy of the DataFrame to avoid side effects.

    Args:
        trades (pd.DataFrame): Trade data.

    Returns:
        pd.DataFrame: Sorted copy of the trades.
    """
    if "close_time" in trades.columns:
        return trades.sort_values("close_time")
    if "open_time" in trades.columns:
        return trades.sort_values("open_time")
    return trades.copy()


# =========================================================================
# Utility & Kernel Helpers
# =========================================================================


def _returns_array(values) -> np.ndarray:
    """Normalize returns-like input to a float NumPy array.

    Logic:
        1. Converts input (Series or list-like) to a float NumPy array.
        2. Handles scalar inputs by reshaping.
        3. Filters out non-finite values (NaN, Inf).

    Args:
        values: Returns data (Series, list, or array).

    Returns:
        np.ndarray: Cleaned float array of returns.
    """
    if isinstance(values, pd.Series):
        array = values.astype(float).to_numpy()
    else:
        array = np.asarray(values, dtype=float)

    if array.ndim == 0:
        array = array.reshape(1)

    return array[np.isfinite(array)]


@njit(cache=True)
def _max_drawdown_duration_kernel(cumulative_equity):
    """Return the longest run of periods below the running equity peak.

    Logic:
        Iterates through the cumulative equity curve maintaining a 'running_max'.
        Whenever the current value is >= running_max, the peak is reset and duration is 0.
        Otherwise, 'current_duration' increments. The maximum seen 'current_duration'
        is tracked and returned.

    Args:
        cumulative_equity (np.ndarray): Array of cumulative equity values.

    Returns:
        int: Maximum number of consecutive periods spent underwater.
    """
    running_max = -1e18
    max_duration = 0
    current_duration = 0
    for val in cumulative_equity:
        if val >= running_max:
            running_max = val
            current_duration = 0
        else:
            current_duration += 1
            max_duration = max(max_duration, current_duration)
    return max_duration


@njit(cache=True)
def _drawdown_duration_series_kernel(equity_arr):
    """Return the current drawdown duration at each equity observation.

    Logic:
        Similar to the duration kernel but stores the 'current_duration' at
        each step in an output array. This identifies how long the strategy
        has been in the current drawdown at any specific point in time.

    Args:
        equity_arr (np.ndarray): Array of equity values.

    Returns:
        np.ndarray: Array of integers representing duration at each point.
    """
    n = len(equity_arr)
    durations = np.zeros(n, dtype=np.int64)
    running_max = -1e18
    current_duration = 0
    for i in range(n):
        val = equity_arr[i]
        if val >= running_max:
            running_max = val
            current_duration = 0
        else:
            current_duration += 1
        durations[i] = current_duration
    return durations


@njit(cache=True)
def _max_close_to_close_drawdown_kernel(mfe_arr, mae_arr, pnl_arr, initial_equity):
    """Calculate maximum trade-path drawdown using MFE, MAE, and closing PnL.

    Logic:
        Simulates the equity curve trade-by-trade. For each trade:
        1. Peak = current_equity + MFE (Maximum Favorable Excursion).
        2. Valley = current_equity - MAE (Maximum Adverse Excursion).
        3. Close = current_equity + PnL.
        Updates 'running_max_equity' if the trade peak exceeds it.
        Calculates drawdown at the valley and at the close relative to the peak.
        Returns the maximum drawdown depth encountered (in currency).

    Args:
        mfe_arr (np.ndarray): Array of trade MFEs.
        mae_arr (np.ndarray): Array of trade MAEs.
        pnl_arr (np.ndarray): Array of trade realized PnLs.
        initial_equity (float): Starting equity for the simulation.

    Returns:
        float: Deepest drawdown depth encountered during the sequence.
    """
    current_equity = initial_equity
    running_max_equity = initial_equity
    max_dd = 0.0

    for i in range(len(mfe_arr)):
        mfe = mfe_arr[i]
        mae = mae_arr[i]
        pnl = pnl_arr[i]

        trade_peak = current_equity + mfe
        trade_valley = current_equity - mae
        trade_close = current_equity + pnl

        running_max_equity = max(running_max_equity, trade_peak)

        dd_valley = running_max_equity - trade_valley
        dd_close = running_max_equity - trade_close

        max_dd = max(max_dd, dd_valley)
        max_dd = max(max_dd, dd_close)

        current_equity = trade_close
    return max_dd


@njit(cache=True)
def _max_close_to_close_drawdown_percent_kernel(
    mfe_arr, mae_arr, pnl_arr, initial_balance
):
    """Calculate maximum trade-path drawdown as a percentage of the running peak.

    Logic:
        Identical to the currency version but calculates drawdown as:
        (Peak - Value) / Peak * 100.
        Uses a small epsilon (1e-9) to avoid division by zero.

    Args:
        mfe_arr (np.ndarray): Array of trade MFEs.
        mae_arr (np.ndarray): Array of trade MAEs.
        pnl_arr (np.ndarray): Array of trade realized PnLs.
        initial_balance (float): Starting balance.

    Returns:
        float: Deepest percentage drawdown encountered.
    """
    current_equity = initial_balance
    running_max_equity = initial_balance
    max_dd_pct = 0.0

    for i in range(len(mfe_arr)):
        mfe = mfe_arr[i]
        mae = mae_arr[i]
        pnl = pnl_arr[i]

        trade_peak = current_equity + mfe
        trade_valley = current_equity - mae
        trade_close = current_equity + pnl

        running_max_equity = max(running_max_equity, trade_peak)

        peak_ref = running_max_equity if running_max_equity > 0 else 1e-9

        dd_valley_pct = (running_max_equity - trade_valley) / peak_ref * 100
        dd_close_pct = (running_max_equity - trade_close) / peak_ref * 100

        max_dd_pct = max(max_dd_pct, dd_valley_pct)
        max_dd_pct = max(max_dd_pct, dd_close_pct)

        current_equity = trade_close
    return max_dd_pct


# =========================================================================
# Utility Functions
# =========================================================================


def _drawdown_series_impl(equity_curve: pd.Series) -> pd.Series:
    """Calculate drawdown series from equity curve.

    Logic:
        1. Cleans the equity curve using _clean_equity.
        2. Calculates the running maximum (peak) using an expanding window.
        3. Subtracts the running maximum from the current equity to get the
           drawdown depth (negative values or zero).

    Args:
        equity_curve (pd.Series): The strategy equity curve.

    Returns:
        pd.Series: Series of drawdown values in currency.
    """
    equity_curve = _clean_equity(equity_curve)
    if len(equity_curve) == 0:
        return pd.Series(dtype=float)
    running_max = equity_curve.expanding().max()
    return equity_curve - running_max


def _drawdown_duration_series_impl(equity_curve: pd.Series) -> pd.Series:
    """Calculate drawdown duration series.

    Logic:
        1. Cleans the equity curve.
        2. Converts to a NumPy array for performance.
        3. Uses the _drawdown_duration_series_kernel to compute the
           consecutive periods spent underwater at each point.

    Args:
        equity_curve (pd.Series): The strategy equity curve.

    Returns:
        pd.Series: Series of duration counts (integers).
    """
    equity_curve = _clean_equity(equity_curve)
    if len(equity_curve) == 0:
        return pd.Series(dtype=int)
    equity_arr = equity_curve.astype(float).to_numpy()
    durations = _drawdown_duration_series_kernel(equity_arr)
    return pd.Series(durations, index=equity_curve.index)


# =========================================================================
# Core Equity Drawdowns
# =========================================================================


def _max_strategy_drawdown_impl(equity_curve: pd.Series) -> float:
    """Deepest peak-to-valley decline in the equity curve (currency).

    Logic:
        1. Generates the drawdown series.
        2. Finds the minimum (most negative) value.
        3. Returns the absolute value as the maximum drawdown depth.

    Args:
        equity_curve (pd.Series): The strategy equity curve.

    Returns:
        float: Absolute maximum drawdown depth in currency.
    """
    equity_curve = _clean_equity(equity_curve)
    if len(equity_curve) == 0:
        return 0.0
    dd_series = _drawdown_series_impl(equity_curve)
    return float(abs(dd_series.min()))


def _max_strategy_drawdown_percent_impl(equity_curve: pd.Series) -> float:
    """Deepest percentage decline relative to running peak.

    Logic:
        1. Cleans the equity curve.
        2. Calculates the running maximum peak.
        3. Replaces non-positive peaks with a small epsilon to avoid division errors.
        4. Calculates (Equity - Peak) / Peak * 100.
        5. Returns the absolute minimum of this percentage series.

    Args:
        equity_curve (pd.Series): The strategy equity curve.

    Returns:
        float: Maximum percentage drawdown (positive number).
    """
    equity_curve = _clean_equity(equity_curve)
    if len(equity_curve) == 0:
        return 0.0
    running_max = equity_curve.expanding().max()
    # Guard against zero/negative peaks for percentage calculation
    running_max = running_max.replace(0, np.nan).ffill().fillna(1e-9)
    pct_drawdown = ((equity_curve - running_max) / running_max) * 100
    return float(abs(pct_drawdown.min()))


def _max_drawdown_impl(returns: pd.Series | np.ndarray) -> float:
    """Maximum drawdown from returns as a negative fraction.

    Logic:
        1. Normalizes returns to a NumPy array.
        2. Constructs a cumulative wealth index starting at 1.0.
        3. Tracks the running maximum of the wealth index.
        4. Calculates drawdown as (Current Wealth - Max Wealth) / Max Wealth.
        5. Returns the minimum fraction (e.g., -0.25 for a 25% drawdown).

    Args:
        returns: Returns data.

    Returns:
        float: Maximum drawdown as a negative fraction.
    """
    normalized = _returns_array(returns)
    if len(normalized) == 0:
        return 0.0

    cumulative = np.concatenate([[1.0], np.cumprod(1.0 + normalized)])
    running_max = np.maximum.accumulate(cumulative)
    drawdowns_vals = (cumulative - running_max) / running_max

    return float(np.min(drawdowns_vals))


def _avg_drawdown_impl(equity_curve: pd.Series) -> float:
    """Average depth of drawdown periods.

    Logic:
        1. Calculates the drawdown series.
        2. Filters for all points where the strategy is underwater (drawdown < 0).
        3. Returns the absolute mean of these depths.

    Args:
        equity_curve (pd.Series): The strategy equity curve.

    Returns:
        float: Mean depth of drawdown periods.
    """
    if len(equity_curve) == 0:
        return 0.0
    dd_series = _drawdown_series_impl(equity_curve)
    dd_values = dd_series[dd_series < 0]
    if len(dd_values) == 0:
        return 0.0
    return float(abs(dd_values.mean()))


def _drawdown_distribution_impl(equity_curve: pd.Series) -> dict[str, float]:
    """Detailed drawdown distribution statistics.

    Logic:
        1. Calculates the absolute drawdown series for all underwater points.
        2. Computes descriptive statistics: max, mean, median, std dev, and 95th percentile.

    Args:
        equity_curve (pd.Series): The strategy equity curve.

    Returns:
        Dict[str, float]: Dictionary of distribution metrics.
    """
    if len(equity_curve) == 0:
        return {"max": 0.0, "avg": 0.0, "median": 0.0, "std": 0.0, "p95": 0.0}
    dd_series = _drawdown_series_impl(equity_curve)
    dd_values = abs(dd_series[dd_series < 0])
    if len(dd_values) == 0:
        return {"max": 0.0, "avg": 0.0, "median": 0.0, "std": 0.0, "p95": 0.0}
    return {
        "max": float(dd_values.max()),
        "avg": float(dd_values.mean()),
        "median": float(dd_values.median()),
        "std": float(dd_values.std()),
        "p95": float(dd_values.quantile(0.95)),
    }


# =========================================================================
# Drawdown Duration & Recovery
# =========================================================================


def _max_drawdown_duration_from_equity_impl(equity_curve: pd.Series) -> int:
    """Maximum number of periods spent in drawdown from equity curve.

    Logic:
        1. Cleans the equity curve.
        2. Passes the array to the Numba kernel which tracks peaks and valley durations.

    Args:
        equity_curve (pd.Series): The strategy equity curve.

    Returns:
        int: Longest underwater streak.
    """
    equity_curve = _clean_equity(equity_curve)
    if len(equity_curve) == 0:
        return 0
    equity_arr = equity_curve.astype(float).to_numpy()
    return _max_drawdown_duration_kernel(equity_arr)


def _max_drawdown_duration_from_returns_impl(returns: pd.Series | np.ndarray) -> int:
    """Maximum number of periods spent in drawdown from returns series.

    Logic:
        1. Normalizes returns and builds a cumulative wealth curve.
        2. Uses the drawdown duration kernel to find the longest underwater streak.

    Args:
        returns: Returns data.

    Returns:
        int: Longest underwater streak.
    """
    rets = _returns_array(returns)
    if len(rets) == 0:
        return 0

    cumulative = np.concatenate([[1.0], np.cumprod(1.0 + rets)])
    duration = _max_drawdown_duration_kernel(cumulative)
    return max(0, int(duration))


def _max_drawdown_duration_impl(values, input_type: str = "equity") -> int:
    """Maximum number of periods spent in drawdown.

    Logic:
        Dispatches to either the equity-based or returns-based duration implementation
        depending on the 'input_type' provided.

    Args:
        values: Data series.
        input_type (str): Either 'equity' or 'returns'.

    Returns:
        int: Maximum duration count.
    """
    if input_type == "returns":
        return _max_drawdown_duration_from_returns_impl(values)
    return _max_drawdown_duration_from_equity_impl(values)


def _avg_drawdown_duration_impl(equity_curve: pd.Series) -> float:
    """Average duration of drawdown episodes (recovery intervals).

    Logic:
        1. Calculates the list of recovery times for all finished drawdowns.
        2. Returns the mean of these durations.

    Args:
        equity_curve (pd.Series): The strategy equity curve.

    Returns:
        float: Mean recovery time.
    """
    recoveries = _time_to_recovery_impl(equity_curve)
    return float(np.mean(recoveries)) if recoveries else 0.0


def _time_to_recovery_impl(equity_curve: pd.Series) -> list[int]:
    """List of recovery periods for each unique drawdown.

    Logic:
        Iterates through the equity curve tracking 'in_drawdown' state.
        When a new peak is hit after being underwater, the duration of that
        drawdown is recorded. Note: unfinished drawdowns (the current one)
        are typically excluded.

    Args:
        equity_curve (pd.Series): The strategy equity curve.

    Returns:
        List[int]: List of period counts for each recovery.
    """
    equity_curve = _clean_equity(equity_curve)
    if len(equity_curve) == 0:
        return []
    running_max = equity_curve.expanding().max()
    at_high = equity_curve >= running_max
    recovery_times = []
    current_duration = 0
    in_drawdown = False
    for is_high in at_high:
        if not is_high:
            in_drawdown = True
            current_duration += 1
        elif in_drawdown:
            recovery_times.append(current_duration)
            current_duration = 0
            in_drawdown = False
    return recovery_times


def _recovery_factor_impl(equity_curve: pd.Series | np.ndarray) -> float:
    """Net profit relative to maximum drawdown.

    Logic:
        Calculates Total Net Profit / Max Drawdown Depth.
        Reflects how many times the strategy has 'earned back' its worst dip.
        Handles both returns-based and equity-based inputs.

    Args:
        equity_curve: Data series.

    Returns:
        float: Recovery factor ratio.
    """
    if not isinstance(equity_curve, pd.Series):
        normalized = _returns_array(equity_curve)
        if len(normalized) == 0:
            return float("nan")

        total_return = np.prod(1.0 + normalized) - 1.0
        drawdown = abs(_max_drawdown_impl(normalized))

        if drawdown == 0:
            return float("inf") if total_return > 0 else float("nan")

        return float(total_return / drawdown)

    equity_curve = _clean_equity(equity_curve)
    if len(equity_curve) < 2:
        return 0.0

    net_profit_val = equity_curve.iloc[-1] - equity_curve.iloc[0]
    max_dd_val = _max_strategy_drawdown_impl(equity_curve)

    if max_dd_val == 0:
        return 0.0 if net_profit_val == 0 else float("inf")

    return float(net_profit_val / max_dd_val)


# =========================================================================
# Trade-Level Drawdowns
# =========================================================================


def _trade_level_drawdowns_impl(
    trades: pd.DataFrame, closed_only: bool = True
) -> pd.Series:
    """Calculate cumulative P&L drawdowns at trade close points, starting from 0.

    Logic:
        1. Filters for closed trades.
        2. Sorts trades chronologically.
        3. Calculates the cumulative PnL series.
        4. Treats this PnL series as an equity curve starting at 0.
        5. Returns the peak-to-current drawdown for each trade close.

    Args:
        trades (pd.DataFrame): Trade data.
        closed_only (bool): Whether to ignore open trades.

    Returns:
        pd.Series: Trade-by-trade drawdown depth.
    """
    data = get_closed_trades(trades) if closed_only else trades
    if data.empty or "profit_loss" not in data.columns:
        return pd.Series(dtype=float)

    sorted_trades = _sort_trades_for_drawdown(data)
    pnl = sorted_trades["profit_loss"].astype(float)
    cumulative_pnl = pnl.cumsum()

    # Prepend starting equity 0
    zero_idx = pd.Index(["START"])
    full_curve = pd.concat([pd.Series([0.0], index=zero_idx), cumulative_pnl])

    running_max = full_curve.expanding().max()
    dd_curve = full_curve - running_max
    return dd_curve.iloc[1:]  # Drop START


def _max_close_to_close_drawdown_impl(
    trades: pd.DataFrame, closed_only: bool = True
) -> float:
    """Max drawdown from peak (including MFE) to valley (including MAE or close).

    Logic:
        Uses MFE/MAE if available to find the absolute deepest valley
        encountered within the sequence of trades. If not available,
        it falls back to a simple cumulative PnL peak-to-valley search.

    Args:
        trades (pd.DataFrame): Trade data.
        closed_only (bool): Whether to ignore open trades.

    Returns:
        float: Deepest excursion drawdown (currency).
    """
    data = get_closed_trades(trades) if closed_only else trades
    if data.empty:
        return 0.0

    sorted_trades = _sort_trades_for_drawdown(data)

    # Check if we have high-fidelity excursion data
    if _has_col(sorted_trades, "mfe_usd") and _has_col(sorted_trades, "mae_usd"):
        mfe_arr = np.maximum(sorted_trades["mfe_usd"].astype(float).to_numpy(), 0.0)
        mae_arr = np.abs(sorted_trades["mae_usd"].astype(float).to_numpy())
        pnl_arr = sorted_trades["profit_loss"].astype(float).to_numpy()
        return _max_close_to_close_drawdown_kernel(mfe_arr, mae_arr, pnl_arr, 0.0)

    # Fallback: starting balance 0.0
    if _has_col(sorted_trades, "profit_loss"):
        pnl = sorted_trades["profit_loss"].astype(float).to_numpy()
        cumulative_pnl = np.concatenate([[0.0], np.cumsum(pnl)])
        running_max = np.maximum.accumulate(cumulative_pnl)
        return float(np.max(running_max - cumulative_pnl))

    return 0.0


def _max_close_to_close_drawdown_percent_impl(
    trades: pd.DataFrame, initial_balance: float, closed_only: bool = True
) -> float:
    """Percentage version of close-to-close drawdown.

    Logic:
        Simulates equity using MFE/MAE to find the deepest percentage drop
        relative to the running peak equity reached.

    Args:
        trades (pd.DataFrame): Trade data.
        initial_balance (float): Starting balance.
        closed_only (bool): Filter open trades.

    Returns:
        float: Deepest percentage drawdown.
    """
    data = get_closed_trades(trades) if closed_only else trades
    if data.empty or initial_balance <= 0:
        return 0.0

    sorted_trades = _sort_trades_for_drawdown(data)

    if _has_col(sorted_trades, "mfe_usd") and _has_col(sorted_trades, "mae_usd"):
        mfe_arr = np.maximum(sorted_trades["mfe_usd"].astype(float).to_numpy(), 0.0)
        mae_arr = np.abs(sorted_trades["mae_usd"].astype(float).to_numpy())
        pnl_arr = sorted_trades["profit_loss"].astype(float).to_numpy()
        return _max_close_to_close_drawdown_percent_kernel(
            mfe_arr, mae_arr, pnl_arr, float(initial_balance)
        )

    # Fallback
    if _has_col(sorted_trades, "profit_loss"):
        pnl_arr = sorted_trades["profit_loss"].astype(float).to_numpy()
        cumulative_pnl = np.concatenate([[0.0], np.cumsum(pnl_arr)]) + initial_balance
        return _max_strategy_drawdown_percent_impl(pd.Series(cumulative_pnl))

    return 0.0


def _avg_trade_drawdown_impl(trades: pd.DataFrame) -> float:
    """Mean depth of trade-level close-to-close drawdowns.

    Logic:
        Calculates the drawdown depth at each trade close and returns the average.

    Args:
        trades (pd.DataFrame): Trade data.

    Returns:
        float: Average trade-level drawdown.
    """
    if len(trades) == 0:
        return 0.0
    dd_series = _trade_level_drawdowns_impl(trades)
    dd_values = dd_series[dd_series < 0]
    if len(dd_values) == 0:
        return 0.0
    return float(abs(dd_values.mean()))


def _account_size_required_impl(trades: pd.DataFrame) -> float:
    """Capital required to withstand max close-to-close dips.

    Logic:
        Returns the absolute maximum currency drawdown encountered,
        which represents the minimum buffer needed to stay solvent
        through the worst historical valley.

    Args:
        trades (pd.DataFrame): Trade data.

    Returns:
        float: Capital required.
    """
    return _max_close_to_close_drawdown_impl(trades)


def _max_consecutive_drawdown_trades_impl(
    trades: pd.DataFrame, closed_only: bool = True
) -> int:
    """Maximum number of consecutive trades within a single strategy drawdown.

    Logic:
        Tracks how many trades in a row the cumulative PnL remains below its previous peak.
        Resets whenever a new cumulative PnL high is reached.

    Args:
        trades (pd.DataFrame): Trade data.
        closed_only (bool): Filter open trades.

    Returns:
        int: Maximum consecutive trades spent underwater.
    """
    data = get_closed_trades(trades) if closed_only else trades
    if data.empty or "profit_loss" not in data.columns:
        return 0

    sorted_trades = _sort_trades_for_drawdown(data)
    pnl = sorted_trades["profit_loss"].astype(float)
    cumulative_pnl = pnl.cumsum()

    running_max = cumulative_pnl.expanding().max()
    is_underwater = cumulative_pnl < running_max

    max_streak = 0
    current_streak = 0

    for underwater in is_underwater:
        if underwater:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0

    return int(max_streak)


# =========================================================================
# Periodic & Time-Based Metrics
# =========================================================================


def _avg_yearly_max_drawdown_impl(equity_curve: pd.Series) -> float:
    """Average of the maximum drawdowns observed in each year.

    Logic:
        1. Groups the equity curve by calendar year.
        2. Calculates the Max Strategy Drawdown for each year independently.
        3. Returns the average of these yearly maximums.

    Args:
        equity_curve (pd.Series): The strategy equity curve.

    Returns:
        float: Average yearly max drawdown.
    """
    equity_curve = _clean_equity(equity_curve)
    if len(equity_curve) == 0 or not isinstance(equity_curve.index, pd.DatetimeIndex):
        return 0.0
    yearly_groups = equity_curve.groupby(pd.Grouper(freq="YE"))
    max_dds = []
    for _, yearly_equity in yearly_groups:
        if len(yearly_equity) > 0:
            max_dds.append(_max_strategy_drawdown_impl(yearly_equity))
    return float(np.mean(max_dds)) if max_dds else 0.0


def _max_strategy_drawdown_date_impl(equity_curve: pd.Series) -> pd.Timestamp | None:
    """Date of the absolute deepest strategy equity valley.

    Logic:
        Calculates the drawdown series and identifies the index (timestamp)
        where the minimum value occurs.

    Args:
        equity_curve (pd.Series): The strategy equity curve.

    Returns:
        Optional[pd.Timestamp]: Date of the deepest valley.
    """
    equity_curve = _clean_equity(equity_curve)
    if len(equity_curve) == 0:
        return None
    dd_series = _drawdown_series_impl(equity_curve)
    try:
        return dd_series.idxmin()
    except (ValueError, TypeError):
        return None


def _max_close_to_close_drawdown_date_impl(
    trades: pd.DataFrame, closed_only: bool = True
) -> pd.Timestamp | None:
    """Date of the deepest trade-level valley.

    Logic:
        Identifies the close time of the trade that caused the deepest
        valley (considering MFE/MAE excursions if available).

    Args:
        trades (pd.DataFrame): Trade data.
        closed_only (bool): Filter open trades.

    Returns:
        Optional[pd.Timestamp]: Date of the deepest valley.
    """
    data = get_closed_trades(trades) if closed_only else trades
    if data.empty:
        return None

    time_col = (
        "close_time"
        if "close_time" in data.columns
        else "open_time"
        if "open_time" in data.columns
        else None
    )
    if time_col is None:
        return None

    sorted_trades = _sort_trades_for_drawdown(data)
    if "mfe_usd" not in data.columns or "mae_usd" not in data.columns:
        pnl = sorted_trades["profit_loss"].astype(float).to_numpy()
        cumulative_pnl = np.concatenate([[0.0], np.cumsum(pnl)])
        running_max = np.maximum.accumulate(cumulative_pnl)
        drawdown = running_max - cumulative_pnl

        if len(drawdown) < 2:
            return None
        # idxmin/argmax of the drawdown (positive)
        idx = np.argmax(drawdown)
        if idx == 0:
            return None  # No drawdown
        return sorted_trades.iloc[idx - 1][time_col]

    current_equity, running_max_equity, max_dd = 0.0, 0.0, 0.0
    max_dd_date = None
    for _, trade in sorted_trades.iterrows():
        mfe = max(float(trade.get("mfe_usd", 0.0)), 0.0)
        mae = abs(float(trade.get("mae_usd", 0.0)))
        pnl = float(trade.get("profit_loss", 0.0))

        trade_peak = current_equity + mfe
        trade_valley = current_equity - mae
        trade_close = current_equity + pnl

        running_max_equity = max(running_max_equity, trade_peak)
        dd_valley = running_max_equity - trade_valley
        dd_close = running_max_equity - trade_close

        if dd_valley > max_dd:
            max_dd = dd_valley
            max_dd_date = trade[time_col]
        if dd_close > max_dd:
            max_dd = dd_close
            max_dd_date = trade[time_col]

        current_equity = trade_close
    return max_dd_date


# =========================================================================
# Pain & Volatility Indices
# =========================================================================


def _ulcer_index_impl(equity_curve: pd.Series) -> float:
    """Ulcer Index: sqrt(mean(drawdown_pct^2)).

    Logic:
        1. Calculates the percentage drawdown at every point.
        2. Squares these percentage drawdowns.
        3. Takes the mean of the squared values.
        4. Returns the square root of that mean.
        Higher values indicate deeper and longer drawdowns.

    Args:
        equity_curve (pd.Series): The strategy equity curve.

    Returns:
        float: Ulcer Index value.
    """
    equity_curve = _clean_equity(equity_curve)
    if len(equity_curve) == 0:
        return 0.0
    running_max = equity_curve.expanding().max()
    # Guard against non-positive peaks
    ref_max = running_max.where(running_max > 0).ffill().fillna(1e-9)
    pct_drawdown = ((equity_curve - ref_max) / ref_max) * 100
    return float(np.sqrt((pct_drawdown**2).mean()))


def _pain_index_impl(equity_curve: pd.Series) -> float:
    """Pain Index: mean absolute percentage drawdown across all periods.

    Logic:
        Calculates the average depth of all percentage drawdowns (including zero
        for points at new highs). Reflects the 'average pain' felt over time.

    Args:
        equity_curve (pd.Series): The strategy equity curve.

    Returns:
        float: Pain Index value.
    """
    equity_curve = _clean_equity(equity_curve)
    if len(equity_curve) == 0:
        return 0.0

    running_max = equity_curve.expanding().max()
    ref_max = running_max.where(running_max > 0).ffill().fillna(1e-9)

    pct_drawdown = ((equity_curve - ref_max) / ref_max) * 100.0
    return float(abs(pct_drawdown).mean())


def _avg_underwater_drawdown_percent_impl(equity_curve: pd.Series) -> float:
    """Average drawdown depth only for periods where equity is below peak.

    Logic:
        Calculates percentage drawdowns but ignores all points where
        drawdown is zero (new highs). Returns the average of the non-zero dips.

    Args:
        equity_curve (pd.Series): The strategy equity curve.

    Returns:
        float: Mean depth of dips.
    """
    equity_curve = _clean_equity(equity_curve)
    if len(equity_curve) == 0:
        return 0.0

    running_max = equity_curve.expanding().max()
    ref_max = running_max.where(running_max > 0).ffill().fillna(1e-9)

    pct_drawdown = ((equity_curve - ref_max) / ref_max) * 100.0
    dips = pct_drawdown[pct_drawdown < 0]

    return float(abs(dips.mean())) if not dips.empty else 0.0


def _pain_ratio_impl(equity_curve: pd.Series) -> float:
    """Pain Ratio: Total Percentage Return / Pain Index.

    Logic:
        A risk-adjusted return metric that uses the Pain Index as the
        denominator. Similar to the Sharpe ratio but penalizes all
        drawdown depth rather than just volatility.

    Args:
        equity_curve (pd.Series): The strategy equity curve.

    Returns:
        float: Pain Ratio.
    """
    equity_curve = _clean_equity(equity_curve)
    if len(equity_curve) < 2:
        return 0.0
    pain = _pain_index_impl(equity_curve)
    if pain == 0:
        return 0.0
    total_return_pct = ((equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1.0) * 100.0
    return float(total_return_pct / pain)


def _calculate_drawdown_metrics_impl(equity_curve: pd.Series) -> dict[str, float]:
    """Bulk drawdown metrics from equity.

    Logic:
        Aggregates all major drawdown metrics into a single dictionary.
        Calls specialized implementations for each metric.

    Args:
        equity_curve (pd.Series): The strategy equity curve.

    Returns:
        Dict[str, float]: Dictionary of all computed drawdown metrics.
    """
    equity_curve = _clean_equity(equity_curve)
    if len(equity_curve) == 0:
        return {}

    return {
        "max_drawdown": _max_strategy_drawdown_impl(equity_curve),
        "max_drawdown_percent": _max_strategy_drawdown_percent_impl(equity_curve),
        "avg_drawdown": _avg_drawdown_impl(equity_curve),
        "max_drawdown_duration": _max_drawdown_duration_from_equity_impl(equity_curve),
        "avg_drawdown_duration": _avg_drawdown_duration_impl(equity_curve),
        "recovery_factor": _recovery_factor_impl(equity_curve),
        "ulcer_index": _ulcer_index_impl(equity_curve),
        "pain_index": _pain_index_impl(equity_curve),
        "pain_ratio": _pain_ratio_impl(equity_curve),
    }


# =========================================================================
# =========================================================================
# Agent-Facing Function Tools
# =========================================================================


def _drawdown_series_impl(
    equity_curve: list[float] | pd.Series,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate a time-series of drawdown values (equity - running_peak).

    This tool is essential for visualizing 'underwater' periods and identifying
    all historical valleys in currency terms.

    Args:
        equity_curve: Series or list of equity values.
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'drawdown_series' payload.
    """
    try:
        # 1. Input Validation
        if equity_curve is None:
            return {"status": "error", "message": "equity_curve is required"}

        # 2. Core Execution
        if isinstance(equity_curve, list):
            equity_curve = pd.Series(equity_curve)
        res = _drawdown_series_impl(equity_curve)

        # 3. Structured Return
        payload = res.tolist() if hasattr(res, "tolist") else res
        logger.info("Executed drawdown_series tool successfully")
        return analytics_tool_result(
            "drawdown_series",
            data={"drawdown_series": payload},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in drawdown_series: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _drawdown_duration_series_impl(
    equity_curve: list[float] | pd.Series,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate a time-series of current drawdown durations (consecutive periods underwater).

    Identifies how long the strategy has been below its previous peak at
    any given point in time.

    Args:
        equity_curve: Series or list of equity values.
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'drawdown_duration_series' payload.
    """
    try:
        # 1. Input Validation
        if equity_curve is None:
            return {"status": "error", "message": "equity_curve is required"}

        # 2. Core Execution
        if isinstance(equity_curve, list):
            equity_curve = pd.Series(equity_curve)
        res = _drawdown_duration_series_impl(equity_curve)

        # 3. Structured Return
        payload = res.tolist() if hasattr(res, "tolist") else res
        logger.info("Executed drawdown_duration_series tool successfully")
        return analytics_tool_result(
            "drawdown_duration_series",
            data={"drawdown_duration_series": payload},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in drawdown_duration_series: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _max_strategy_drawdown_impl(
    equity_curve: list[float] | pd.Series,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate the deepest absolute peak-to-valley decline (currency).

    Represents the worst-case historical loss in account value.

    Args:
        equity_curve: Series or list of equity values.
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'max_strategy_drawdown' payload.
    """
    try:
        # 1. Input Validation
        if equity_curve is None:
            return {"status": "error", "message": "equity_curve is required"}

        # 2. Core Execution
        if isinstance(equity_curve, list):
            equity_curve = pd.Series(equity_curve)
        res = _max_strategy_drawdown_impl(equity_curve)

        # 3. Structured Return
        logger.info("Executed max_strategy_drawdown tool successfully")
        return analytics_tool_result(
            "max_strategy_drawdown",
            data={"max_strategy_drawdown": float(res)},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in max_strategy_drawdown: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _max_strategy_drawdown_percent_impl(
    equity_curve: list[float] | pd.Series,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate the deepest percentage decline relative to the running peak.

    Standard industry metric for maximum historical risk (e.g. 15% drawdown).

    Args:
        equity_curve: Series or list of equity values.
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'max_strategy_drawdown_percent' payload.
    """
    try:
        # 1. Input Validation
        if equity_curve is None:
            return {"status": "error", "message": "equity_curve is required"}

        # 2. Core Execution
        if isinstance(equity_curve, list):
            equity_curve = pd.Series(equity_curve)
        res = _max_strategy_drawdown_percent_impl(equity_curve)

        # 3. Structured Return
        logger.info("Executed max_strategy_drawdown_percent tool successfully")
        return analytics_tool_result(
            "max_strategy_drawdown_percent",
            data={"max_strategy_drawdown_percent": float(res)},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in max_strategy_drawdown_percent: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _max_drawdown_impl(
    returns: list[float] | pd.Series | np.ndarray,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate maximum drawdown from a series of returns (negative fraction).

    Used when equity curve is not available. Returns values like -0.15 for 15%.

    Args:
        returns: Series, list, or array of returns.
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'max_drawdown' payload.
    """
    try:
        # 1. Input Validation
        if returns is None:
            return {"status": "error", "message": "returns is required"}

        # 2. Core Execution
        res = _max_drawdown_impl(returns)

        # 3. Structured Return
        logger.info("Executed max_drawdown tool successfully")
        return analytics_tool_result(
            "max_drawdown",
            data={"max_drawdown": float(res)},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in max_drawdown: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _avg_drawdown_impl(
    equity_curve: list[float] | pd.Series,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate the average depth of all drawdown periods.

    Provides a measure of typical strategy pullbacks.

    Args:
        equity_curve: Series or list of equity values.
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'avg_drawdown' payload.
    """
    try:
        # 1. Input Validation
        if equity_curve is None:
            return {"status": "error", "message": "equity_curve is required"}

        # 2. Core Execution
        if isinstance(equity_curve, list):
            equity_curve = pd.Series(equity_curve)
        res = _avg_drawdown_impl(equity_curve)

        # 3. Structured Return
        logger.info("Executed avg_drawdown tool successfully")
        return analytics_tool_result(
            "avg_drawdown",
            data={"avg_drawdown": float(res)},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in avg_drawdown: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _drawdown_distribution_impl(
    equity_curve: list[float] | pd.Series,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate detailed statistics for the distribution of drawdown depths.

    Returns metrics like mean, median, standard deviation, and 95th percentile
    of drawdown depth.

    Args:
        equity_curve: Series or list of equity values.
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'drawdown_distribution' payload.
    """
    try:
        # 1. Input Validation
        if equity_curve is None:
            return {"status": "error", "message": "equity_curve is required"}

        # 2. Core Execution
        if isinstance(equity_curve, list):
            equity_curve = pd.Series(equity_curve)
        res = _drawdown_distribution_impl(equity_curve)

        # 3. Structured Return
        logger.info("Executed drawdown_distribution tool successfully")
        return analytics_tool_result(
            "drawdown_distribution",
            data={"drawdown_distribution": res},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in drawdown_distribution: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _max_drawdown_duration_from_equity_impl(
    equity_curve: list[float] | pd.Series,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate the maximum number of periods spent underwater from an equity curve.

    Identifies the longest historical streak without reaching a new equity high.

    Args:
        equity_curve: Series or list of equity values.
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'max_drawdown_duration_from_equity' payload.
    """
    try:
        # 1. Input Validation
        if equity_curve is None:
            return {"status": "error", "message": "equity_curve is required"}

        # 2. Core Execution
        if isinstance(equity_curve, list):
            equity_curve = pd.Series(equity_curve)
        res = _max_drawdown_duration_from_equity_impl(equity_curve)

        # 3. Structured Return
        logger.info("Executed max_drawdown_duration_from_equity tool successfully")
        return analytics_tool_result(
            "max_drawdown_duration_from_equity",
            data={"max_drawdown_duration_from_equity": int(res)},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in max_drawdown_duration_from_equity: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _max_drawdown_duration_from_returns_impl(
    returns: list[float] | pd.Series | np.ndarray,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate the maximum number of periods spent underwater from a returns series.

    Used when equity curve is not available.

    Args:
        returns: Series, list, or array of returns.
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'max_drawdown_duration_from_returns' payload.
    """
    try:
        # 1. Input Validation
        if returns is None:
            return {"status": "error", "message": "returns is required"}

        # 2. Core Execution
        res = _max_drawdown_duration_from_returns_impl(returns)

        # 3. Structured Return
        logger.info("Executed max_drawdown_duration_from_returns tool successfully")
        return analytics_tool_result(
            "max_drawdown_duration_from_returns",
            data={"max_drawdown_duration_from_returns": int(res)},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in max_drawdown_duration_from_returns: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _max_drawdown_duration_impl(
    values: list[float] | pd.Series | np.ndarray,
    input_type: str = "equity",
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate the maximum number of periods spent underwater.

    Flexible tool that accepts either equity or returns input.

    Args:
        values: Series, list, or array of values.
        input_type: Type of input ('equity' or 'returns').
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'max_drawdown_duration' payload.
    """
    try:
        # 1. Input Validation
        if values is None:
            return {"status": "error", "message": "values is required"}

        # 2. Core Execution
        if isinstance(values, list):
            values = pd.Series(values)
        res = _max_drawdown_duration_impl(values, input_type=input_type)

        # 3. Structured Return
        logger.info("Executed max_drawdown_duration tool successfully")
        return analytics_tool_result(
            "max_drawdown_duration",
            data={"max_drawdown_duration": int(res)},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in max_drawdown_duration: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _avg_drawdown_duration_impl(
    equity_curve: list[float] | pd.Series,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate the average duration of drawdown episodes (recovery intervals).

    Provides a measure of the typical time required to reach a new equity high.

    Args:
        equity_curve: Series or list of equity values.
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'avg_drawdown_duration' payload.
    """
    try:
        # 1. Input Validation
        if equity_curve is None:
            return {"status": "error", "message": "equity_curve is required"}

        # 2. Core Execution
        if isinstance(equity_curve, list):
            equity_curve = pd.Series(equity_curve)
        res = _avg_drawdown_duration_impl(equity_curve)

        # 3. Structured Return
        logger.info("Executed avg_drawdown_duration tool successfully")
        return analytics_tool_result(
            "avg_drawdown_duration",
            data={"avg_drawdown_duration": float(res)},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in avg_drawdown_duration: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _time_to_recovery_impl(
    equity_curve: list[float] | pd.Series,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Return a list of recovery periods for each unique completed drawdown.

    Useful for analyzing the distribution of recovery times.

    Args:
        equity_curve: Series or list of equity values.
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'time_to_recovery' payload.
    """
    try:
        # 1. Input Validation
        if equity_curve is None:
            return {"status": "error", "message": "equity_curve is required"}

        # 2. Core Execution
        if isinstance(equity_curve, list):
            equity_curve = pd.Series(equity_curve)
        res = _time_to_recovery_impl(equity_curve)

        # 3. Structured Return
        logger.info("Executed time_to_recovery tool successfully")
        return analytics_tool_result(
            "time_to_recovery",
            data={"time_to_recovery": res},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in time_to_recovery: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _recovery_factor_impl(
    equity_curve: list[float] | pd.Series | np.ndarray,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate the ratio of net profit to maximum drawdown.

    A higher recovery factor indicates the strategy earns significantly
    more than its worst-case risk.

    Args:
        equity_curve: Series, list, or array of equity or returns.
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'recovery_factor' payload.
    """
    try:
        # 1. Input Validation
        if equity_curve is None:
            return {"status": "error", "message": "equity_curve is required"}

        # 2. Core Execution
        if isinstance(equity_curve, list):
            equity_curve = pd.Series(equity_curve)
        res = _recovery_factor_impl(equity_curve)

        # 3. Structured Return
        logger.info("Executed recovery_factor tool successfully")
        return analytics_tool_result(
            "recovery_factor",
            data={"recovery_factor": float(res)},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in recovery_factor: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _trade_level_drawdowns_impl(
    trades: list[dict[str, Any]] | pd.DataFrame,
    closed_only: bool = True,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate cumulative P&L drawdowns at each trade close point.

    Treats the cumulative realized PnL as an equity curve starting from zero.

    Args:
        trades: DataFrame or list of trade dictionaries.
        closed_only: Whether to include only closed trades (default: True).
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'trade_level_drawdowns' payload.
    """
    try:
        # 1. Input Validation
        if trades is None:
            return {"status": "error", "message": "trades is required"}

        # 2. Core Execution
        if isinstance(trades, list):
            trades = pd.DataFrame(trades)
        res = _trade_level_drawdowns_impl(trades, closed_only=closed_only)

        # 3. Structured Return
        payload = res.tolist() if hasattr(res, "tolist") else res
        logger.info("Executed trade_level_drawdowns tool successfully")
        return analytics_tool_result(
            "trade_level_drawdowns",
            data={"trade_level_drawdowns": payload},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in trade_level_drawdowns: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _max_close_to_close_drawdown_impl(
    trades: list[dict[str, Any]] | pd.DataFrame,
    closed_only: bool = True,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate max drawdown considering intra-trade excursions (MFE/MAE).

    If mfe_usd and mae_usd columns are present, this reflects the true maximum
    historical valley encountered including price movement while trades were open.

    Args:
        trades: DataFrame or list of trade dictionaries.
        closed_only: Whether to include only closed trades (default: True).
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'max_close_to_close_drawdown' payload.
    """
    try:
        # 1. Input Validation
        if trades is None:
            return {"status": "error", "message": "trades is required"}

        # 2. Core Execution
        if isinstance(trades, list):
            trades = pd.DataFrame(trades)
        res = _max_close_to_close_drawdown_impl(trades, closed_only=closed_only)

        # 3. Structured Return
        logger.info("Executed max_close_to_close_drawdown tool successfully")
        return analytics_tool_result(
            "max_close_to_close_drawdown",
            data={"max_close_to_close_drawdown": float(res)},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in max_close_to_close_drawdown: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _max_close_to_close_drawdown_percent_impl(
    trades: list[dict[str, Any]] | pd.DataFrame,
    initial_balance: float,
    closed_only: bool = True,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate percentage version of max close-to-close drawdown.

    Requires an initial_balance to normalize currency excursions into percentages.

    Args:
        trades: DataFrame or list of trade dictionaries.
        initial_balance: Starting account balance for percentage calculation.
        closed_only: Whether to include only closed trades (default: True).
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'max_close_to_close_drawdown_percent' payload.
    """
    try:
        # 1. Input Validation
        if trades is None:
            return {"status": "error", "message": "trades is required"}
        if initial_balance <= 0:
            return {
                "status": "error",
                "message": "initial_balance must be greater than 0",
            }

        # 2. Core Execution
        if isinstance(trades, list):
            trades = pd.DataFrame(trades)
        res = _max_close_to_close_drawdown_percent_impl(
            trades, initial_balance, closed_only=closed_only
        )

        # 3. Structured Return
        logger.info("Executed max_close_to_close_drawdown_percent tool successfully")
        return analytics_tool_result(
            "max_close_to_close_drawdown_percent",
            data={"max_close_to_close_drawdown_percent": float(res)},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in max_close_to_close_drawdown_percent: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _avg_trade_drawdown_impl(
    trades: list[dict[str, Any]] | pd.DataFrame,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate the mean depth of all trade-level close-to-close drawdowns.

    Reflects the typical realized drawdown depth per trade.

    Args:
        trades: DataFrame or list of trade dictionaries.
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'avg_trade_drawdown' payload.
    """
    try:
        # 1. Input Validation
        if trades is None:
            return {"status": "error", "message": "trades is required"}

        # 2. Core Execution
        if isinstance(trades, list):
            trades = pd.DataFrame(trades)
        res = _avg_trade_drawdown_impl(trades)

        # 3. Structured Return
        logger.info("Executed avg_trade_drawdown tool successfully")
        return analytics_tool_result(
            "avg_trade_drawdown",
            data={"avg_trade_drawdown": float(res)},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in avg_trade_drawdown: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _account_size_required_impl(
    trades: list[dict[str, Any]] | pd.DataFrame,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate capital required to withstand historical max close-to-close dips.

    Identifies the minimum buffer needed to prevent total account depletion.

    Args:
        trades: DataFrame or list of trade dictionaries.
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'account_size_required' payload.
    """
    try:
        # 1. Input Validation
        if trades is None:
            return {"status": "error", "message": "trades is required"}

        # 2. Core Execution
        if isinstance(trades, list):
            trades = pd.DataFrame(trades)
        res = _account_size_required_impl(trades)

        # 3. Structured Return
        logger.info("Executed account_size_required tool successfully")
        return analytics_tool_result(
            "account_size_required",
            data={"account_size_required": float(res)},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in account_size_required: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _max_consecutive_drawdown_trades_impl(
    trades: list[dict[str, Any]] | pd.DataFrame,
    closed_only: bool = True,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate the maximum number of consecutive trades within a single strategy drawdown.

    Identifies the longest 'losing streak' or period of frustration where equity
    failed to reach a new high.

    Args:
        trades: DataFrame or list of trade dictionaries.
        closed_only: Whether to include only closed trades (default: True).
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'max_consecutive_drawdown_trades' payload.
    """
    try:
        # 1. Input Validation
        if trades is None:
            return {"status": "error", "message": "trades is required"}

        # 2. Core Execution
        if isinstance(trades, list):
            trades = pd.DataFrame(trades)
        res = _max_consecutive_drawdown_trades_impl(trades, closed_only=closed_only)

        # 3. Structured Return
        logger.info("Executed max_consecutive_drawdown_trades tool successfully")
        return analytics_tool_result(
            "max_consecutive_drawdown_trades",
            data={"max_consecutive_drawdown_trades": int(res)},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in max_consecutive_drawdown_trades: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _avg_yearly_max_drawdown_impl(
    equity_curve: list[float] | pd.Series,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate the average of the maximum drawdowns observed in each calendar year.

    Helps normalize risk expectations across different years.

    Args:
        equity_curve: Series or list of equity values.
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'avg_yearly_max_drawdown' payload.
    """
    try:
        # 1. Input Validation
        if equity_curve is None:
            return {"status": "error", "message": "equity_curve is required"}

        # 2. Core Execution
        if isinstance(equity_curve, list):
            equity_curve = pd.Series(equity_curve)
        res = _avg_yearly_max_drawdown_impl(equity_curve)

        # 3. Structured Return
        logger.info("Executed avg_yearly_max_drawdown tool successfully")
        return analytics_tool_result(
            "avg_yearly_max_drawdown",
            data={"avg_yearly_max_drawdown": float(res)},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in avg_yearly_max_drawdown: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _max_strategy_drawdown_date_impl(
    equity_curve: list[float] | pd.Series,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate the date of the absolute deepest strategy equity valley.

    Pinpoints when the strategy experienced its worst historical currency loss.

    Args:
        equity_curve: Series or list of equity values.
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'max_strategy_drawdown_date' payload.
    """
    try:
        # 1. Input Validation
        if equity_curve is None:
            return {"status": "error", "message": "equity_curve is required"}

        # 2. Core Execution
        if isinstance(equity_curve, list):
            equity_curve = pd.Series(equity_curve)
        res = _max_strategy_drawdown_date_impl(equity_curve)

        # 3. Structured Return
        payload = str(res) if isinstance(res, (pd.Timestamp, pd.Timedelta)) else res
        logger.info("Executed max_strategy_drawdown_date tool successfully")
        return analytics_tool_result(
            "max_strategy_drawdown_date",
            data={"max_strategy_drawdown_date": payload},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in max_strategy_drawdown_date: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _max_close_to_close_drawdown_date_impl(
    trades: list[dict[str, Any]] | pd.DataFrame,
    closed_only: bool = True,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate the date of the deepest trade-level valley.

    Identifies the timestamp of the deepest excursion (MAE) or close PnL.

    Args:
        trades: DataFrame or list of trade dictionaries.
        closed_only: Whether to include only closed trades (default: True).
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'max_close_to_close_drawdown_date' payload.
    """
    try:
        # 1. Input Validation
        if trades is None:
            return {"status": "error", "message": "trades is required"}

        # 2. Core Execution
        if isinstance(trades, list):
            trades = pd.DataFrame(trades)
        res = _max_close_to_close_drawdown_date_impl(trades, closed_only=closed_only)

        # 3. Structured Return
        payload = str(res) if isinstance(res, (pd.Timestamp, pd.Timedelta)) else res
        logger.info("Executed max_close_to_close_drawdown_date tool successfully")
        return analytics_tool_result(
            "max_close_to_close_drawdown_date",
            data={"max_close_to_close_drawdown_date": payload},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in max_close_to_close_drawdown_date: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _ulcer_index_impl(
    equity_curve: list[float] | pd.Series,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate the Ulcer Index (square root of the mean squared percentage drawdown).

    A measure of downside risk that heavily penalizes deep and long drawdowns.

    Args:
        equity_curve: Series or list of equity values.
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'ulcer_index' payload.
    """
    try:
        # 1. Input Validation
        if equity_curve is None:
            return {"status": "error", "message": "equity_curve is required"}

        # 2. Core Execution
        if isinstance(equity_curve, list):
            equity_curve = pd.Series(equity_curve)
        res = _ulcer_index_impl(equity_curve)

        # 3. Structured Return
        logger.info("Executed ulcer_index tool successfully")
        return analytics_tool_result(
            "ulcer_index",
            data={"ulcer_index": float(res)},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in ulcer_index: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _pain_index_impl(
    equity_curve: list[float] | pd.Series,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate the Pain Index (mean absolute percentage drawdown).

    Reflects the average percentage 'pain' felt by the investor over the entire period.

    Args:
        equity_curve: Series or list of equity values.
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'pain_index' payload.
    """
    try:
        # 1. Input Validation
        if equity_curve is None:
            return {"status": "error", "message": "equity_curve is required"}

        # 2. Core Execution
        if isinstance(equity_curve, list):
            equity_curve = pd.Series(equity_curve)
        res = _pain_index_impl(equity_curve)

        # 3. Structured Return
        logger.info("Executed pain_index tool successfully")
        return analytics_tool_result(
            "pain_index",
            data={"pain_index": float(res)},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in pain_index: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _avg_underwater_drawdown_percent_impl(
    equity_curve: list[float] | pd.Series,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate average drawdown depth only for periods where equity is below peak.

    Ignores periods where the strategy is at a new high (drawdown = 0).

    Args:
        equity_curve: Series or list of equity values.
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'avg_underwater_drawdown_percent' payload.
    """
    try:
        # 1. Input Validation
        if equity_curve is None:
            return {"status": "error", "message": "equity_curve is required"}

        # 2. Core Execution
        if isinstance(equity_curve, list):
            equity_curve = pd.Series(equity_curve)
        res = _avg_underwater_drawdown_percent_impl(equity_curve)

        # 3. Structured Return
        logger.info("Executed avg_underwater_drawdown_percent tool successfully")
        return analytics_tool_result(
            "avg_underwater_drawdown_percent",
            data={"avg_underwater_drawdown_percent": float(res)},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in avg_underwater_drawdown_percent: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _pain_ratio_impl(
    equity_curve: list[float] | pd.Series,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate the Pain Ratio (Total Percentage Return / Pain Index).

    A risk-adjusted performance measure that uses the Pain Index as the
    denominator for drawdown-based risk.

    Args:
        equity_curve: Series or list of equity values.
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with 'pain_ratio' payload.
    """
    try:
        # 1. Input Validation
        if equity_curve is None:
            return {"status": "error", "message": "equity_curve is required"}

        # 2. Core Execution
        if isinstance(equity_curve, list):
            equity_curve = pd.Series(equity_curve)
        res = _pain_ratio_impl(equity_curve)

        # 3. Structured Return
        logger.info("Executed pain_ratio tool successfully")
        return analytics_tool_result(
            "pain_ratio",
            data={"pain_ratio": float(res)},
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in pain_ratio: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def _calculate_drawdown_metrics_impl(
    equity_curve: list[float] | pd.Series,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool: Calculate a comprehensive suite of drawdown and underwater metrics from equity.

    Returns bulk metrics including max drawdown, duration, recovery factor,
    ulcer index, and pain ratio.

    Args:
        equity_curve: Series or list of equity values.
        request_id: Optional request identifier.
        agent_name: Optional agent name.
        environment: Environment name (default: "development").
        dry_run: Whether this is a dry run (default: True).

    Returns:
        Dict[str, Any]: Standard HaruQuant tool result with bulk metrics.
    """
    try:
        # 1. Input Validation
        if equity_curve is None:
            return {"status": "error", "message": "equity_curve is required"}

        # 2. Core Execution
        if isinstance(equity_curve, list):
            equity_curve = pd.Series(equity_curve)
        res = _calculate_drawdown_metrics_impl(equity_curve)

        # 3. Structured Return
        logger.info("Executed calculate_drawdown_metrics tool successfully")
        return analytics_tool_result(
            "calculate_drawdown_metrics",
            data=res,
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )

    # 4. Graceful Error Handling
    except Exception as e:
        logger.error(f"Error in calculate_drawdown_metrics: {e!s}")
        return {"status": "error", "message": f"Tool execution failed: {e!s}"}


def drawdown_series(equity_curve: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _drawdown_series_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity_curve = equity_curve
        if "equity_curve" in ["trades", "open_trades"] and isinstance(
            arg_equity_curve, (list, dict)
        ):
            arg_equity_curve = pd.DataFrame(arg_equity_curve)
        elif "equity_curve" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_equity_curve, list):
            arg_equity_curve = pd.Series(arg_equity_curve)
        kwargs["equity_curve"] = arg_equity_curve

        res = _drawdown_series_impl(**kwargs)
        logger.info("Executed drawdown_series tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "drawdown_series", data={"drawdown_series": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def drawdown_duration_series(equity_curve: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _drawdown_duration_series_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity_curve = equity_curve
        if "equity_curve" in ["trades", "open_trades"] and isinstance(
            arg_equity_curve, (list, dict)
        ):
            arg_equity_curve = pd.DataFrame(arg_equity_curve)
        elif "equity_curve" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_equity_curve, list):
            arg_equity_curve = pd.Series(arg_equity_curve)
        kwargs["equity_curve"] = arg_equity_curve

        res = _drawdown_duration_series_impl(**kwargs)
        logger.info("Executed drawdown_duration_series tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "drawdown_duration_series", data={"drawdown_duration_series": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_strategy_drawdown(equity_curve: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _max_strategy_drawdown_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity_curve = equity_curve
        if "equity_curve" in ["trades", "open_trades"] and isinstance(
            arg_equity_curve, (list, dict)
        ):
            arg_equity_curve = pd.DataFrame(arg_equity_curve)
        elif "equity_curve" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_equity_curve, list):
            arg_equity_curve = pd.Series(arg_equity_curve)
        kwargs["equity_curve"] = arg_equity_curve

        res = _max_strategy_drawdown_impl(**kwargs)
        logger.info("Executed max_strategy_drawdown tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "max_strategy_drawdown", data={"max_strategy_drawdown": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_strategy_drawdown_percent(equity_curve: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _max_strategy_drawdown_percent_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity_curve = equity_curve
        if "equity_curve" in ["trades", "open_trades"] and isinstance(
            arg_equity_curve, (list, dict)
        ):
            arg_equity_curve = pd.DataFrame(arg_equity_curve)
        elif "equity_curve" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_equity_curve, list):
            arg_equity_curve = pd.Series(arg_equity_curve)
        kwargs["equity_curve"] = arg_equity_curve

        res = _max_strategy_drawdown_percent_impl(**kwargs)
        logger.info("Executed max_strategy_drawdown_percent tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "max_strategy_drawdown_percent",
            data={"max_strategy_drawdown_percent": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_drawdown(returns: pd.Series | np.ndarray) -> dict[str, Any]:
    """AI Tool wrapper for _max_drawdown_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_returns = returns
        if "returns" in ["trades", "open_trades"] and isinstance(
            arg_returns, (list, dict)
        ):
            arg_returns = pd.DataFrame(arg_returns)
        elif "returns" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_returns, list):
            arg_returns = pd.Series(arg_returns)
        kwargs["returns"] = arg_returns

        res = _max_drawdown_impl(**kwargs)
        logger.info("Executed max_drawdown tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "max_drawdown", data={"max_drawdown": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def avg_drawdown(equity_curve: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _avg_drawdown_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity_curve = equity_curve
        if "equity_curve" in ["trades", "open_trades"] and isinstance(
            arg_equity_curve, (list, dict)
        ):
            arg_equity_curve = pd.DataFrame(arg_equity_curve)
        elif "equity_curve" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_equity_curve, list):
            arg_equity_curve = pd.Series(arg_equity_curve)
        kwargs["equity_curve"] = arg_equity_curve

        res = _avg_drawdown_impl(**kwargs)
        logger.info("Executed avg_drawdown tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "avg_drawdown", data={"avg_drawdown": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def drawdown_distribution(equity_curve: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _drawdown_distribution_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity_curve = equity_curve
        if "equity_curve" in ["trades", "open_trades"] and isinstance(
            arg_equity_curve, (list, dict)
        ):
            arg_equity_curve = pd.DataFrame(arg_equity_curve)
        elif "equity_curve" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_equity_curve, list):
            arg_equity_curve = pd.Series(arg_equity_curve)
        kwargs["equity_curve"] = arg_equity_curve

        res = _drawdown_distribution_impl(**kwargs)
        logger.info("Executed drawdown_distribution tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "drawdown_distribution", data={"drawdown_distribution": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_drawdown_duration_from_equity(equity_curve: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _max_drawdown_duration_from_equity_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity_curve = equity_curve
        if "equity_curve" in ["trades", "open_trades"] and isinstance(
            arg_equity_curve, (list, dict)
        ):
            arg_equity_curve = pd.DataFrame(arg_equity_curve)
        elif "equity_curve" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_equity_curve, list):
            arg_equity_curve = pd.Series(arg_equity_curve)
        kwargs["equity_curve"] = arg_equity_curve

        res = _max_drawdown_duration_from_equity_impl(**kwargs)
        logger.info("Executed max_drawdown_duration_from_equity tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "max_drawdown_duration_from_equity",
            data={"max_drawdown_duration_from_equity": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_drawdown_duration_from_returns(
    returns: pd.Series | np.ndarray,
) -> dict[str, Any]:
    """AI Tool wrapper for _max_drawdown_duration_from_returns_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_returns = returns
        if "returns" in ["trades", "open_trades"] and isinstance(
            arg_returns, (list, dict)
        ):
            arg_returns = pd.DataFrame(arg_returns)
        elif "returns" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_returns, list):
            arg_returns = pd.Series(arg_returns)
        kwargs["returns"] = arg_returns

        res = _max_drawdown_duration_from_returns_impl(**kwargs)
        logger.info("Executed max_drawdown_duration_from_returns tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "max_drawdown_duration_from_returns",
            data={"max_drawdown_duration_from_returns": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_drawdown_duration(values, input_type: str = "equity") -> dict[str, Any]:
    """AI Tool wrapper for _max_drawdown_duration_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_values = values
        if "values" in ["trades", "open_trades"] and isinstance(
            arg_values, (list, dict)
        ):
            arg_values = pd.DataFrame(arg_values)
        elif "values" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_values, list):
            arg_values = pd.Series(arg_values)
        kwargs["values"] = arg_values

        arg_input_type = input_type
        if "input_type" in ["trades", "open_trades"] and isinstance(
            arg_input_type, (list, dict)
        ):
            arg_input_type = pd.DataFrame(arg_input_type)
        elif "input_type" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_input_type, list):
            arg_input_type = pd.Series(arg_input_type)
        kwargs["input_type"] = arg_input_type

        res = _max_drawdown_duration_impl(**kwargs)
        logger.info("Executed max_drawdown_duration tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "max_drawdown_duration", data={"max_drawdown_duration": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def avg_drawdown_duration(equity_curve: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _avg_drawdown_duration_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity_curve = equity_curve
        if "equity_curve" in ["trades", "open_trades"] and isinstance(
            arg_equity_curve, (list, dict)
        ):
            arg_equity_curve = pd.DataFrame(arg_equity_curve)
        elif "equity_curve" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_equity_curve, list):
            arg_equity_curve = pd.Series(arg_equity_curve)
        kwargs["equity_curve"] = arg_equity_curve

        res = _avg_drawdown_duration_impl(**kwargs)
        logger.info("Executed avg_drawdown_duration tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "avg_drawdown_duration", data={"avg_drawdown_duration": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def time_to_recovery(equity_curve: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _time_to_recovery_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity_curve = equity_curve
        if "equity_curve" in ["trades", "open_trades"] and isinstance(
            arg_equity_curve, (list, dict)
        ):
            arg_equity_curve = pd.DataFrame(arg_equity_curve)
        elif "equity_curve" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_equity_curve, list):
            arg_equity_curve = pd.Series(arg_equity_curve)
        kwargs["equity_curve"] = arg_equity_curve

        res = _time_to_recovery_impl(**kwargs)
        logger.info("Executed time_to_recovery tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "time_to_recovery", data={"time_to_recovery": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def recovery_factor(equity_curve: pd.Series | np.ndarray) -> dict[str, Any]:
    """AI Tool wrapper for _recovery_factor_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity_curve = equity_curve
        if "equity_curve" in ["trades", "open_trades"] and isinstance(
            arg_equity_curve, (list, dict)
        ):
            arg_equity_curve = pd.DataFrame(arg_equity_curve)
        elif "equity_curve" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_equity_curve, list):
            arg_equity_curve = pd.Series(arg_equity_curve)
        kwargs["equity_curve"] = arg_equity_curve

        res = _recovery_factor_impl(**kwargs)
        logger.info("Executed recovery_factor tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "recovery_factor", data={"recovery_factor": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def trade_level_drawdowns(
    trades: pd.DataFrame, closed_only: bool = True
) -> dict[str, Any]:
    """AI Tool wrapper for _trade_level_drawdowns_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        arg_closed_only = closed_only
        if "closed_only" in ["trades", "open_trades"] and isinstance(
            arg_closed_only, (list, dict)
        ):
            arg_closed_only = pd.DataFrame(arg_closed_only)
        elif "closed_only" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_closed_only, list):
            arg_closed_only = pd.Series(arg_closed_only)
        kwargs["closed_only"] = arg_closed_only

        res = _trade_level_drawdowns_impl(**kwargs)
        logger.info("Executed trade_level_drawdowns tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "trade_level_drawdowns", data={"trade_level_drawdowns": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_close_to_close_drawdown(
    trades: pd.DataFrame, closed_only: bool = True
) -> dict[str, Any]:
    """AI Tool wrapper for _max_close_to_close_drawdown_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        arg_closed_only = closed_only
        if "closed_only" in ["trades", "open_trades"] and isinstance(
            arg_closed_only, (list, dict)
        ):
            arg_closed_only = pd.DataFrame(arg_closed_only)
        elif "closed_only" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_closed_only, list):
            arg_closed_only = pd.Series(arg_closed_only)
        kwargs["closed_only"] = arg_closed_only

        res = _max_close_to_close_drawdown_impl(**kwargs)
        logger.info("Executed max_close_to_close_drawdown tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "max_close_to_close_drawdown",
            data={"max_close_to_close_drawdown": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_close_to_close_drawdown_percent(
    trades: pd.DataFrame, initial_balance: float, closed_only: bool = True
) -> dict[str, Any]:
    """AI Tool wrapper for _max_close_to_close_drawdown_percent_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        arg_initial_balance = initial_balance
        if "initial_balance" in ["trades", "open_trades"] and isinstance(
            arg_initial_balance, (list, dict)
        ):
            arg_initial_balance = pd.DataFrame(arg_initial_balance)
        elif "initial_balance" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_initial_balance, list):
            arg_initial_balance = pd.Series(arg_initial_balance)
        kwargs["initial_balance"] = arg_initial_balance

        arg_closed_only = closed_only
        if "closed_only" in ["trades", "open_trades"] and isinstance(
            arg_closed_only, (list, dict)
        ):
            arg_closed_only = pd.DataFrame(arg_closed_only)
        elif "closed_only" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_closed_only, list):
            arg_closed_only = pd.Series(arg_closed_only)
        kwargs["closed_only"] = arg_closed_only

        res = _max_close_to_close_drawdown_percent_impl(**kwargs)
        logger.info("Executed max_close_to_close_drawdown_percent tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "max_close_to_close_drawdown_percent",
            data={"max_close_to_close_drawdown_percent": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def avg_trade_drawdown(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _avg_trade_drawdown_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        res = _avg_trade_drawdown_impl(**kwargs)
        logger.info("Executed avg_trade_drawdown tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "avg_trade_drawdown", data={"avg_trade_drawdown": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def account_size_required(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _account_size_required_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        res = _account_size_required_impl(**kwargs)
        logger.info("Executed account_size_required tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "account_size_required", data={"account_size_required": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_consecutive_drawdown_trades(
    trades: pd.DataFrame, closed_only: bool = True
) -> dict[str, Any]:
    """AI Tool wrapper for _max_consecutive_drawdown_trades_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        arg_closed_only = closed_only
        if "closed_only" in ["trades", "open_trades"] and isinstance(
            arg_closed_only, (list, dict)
        ):
            arg_closed_only = pd.DataFrame(arg_closed_only)
        elif "closed_only" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_closed_only, list):
            arg_closed_only = pd.Series(arg_closed_only)
        kwargs["closed_only"] = arg_closed_only

        res = _max_consecutive_drawdown_trades_impl(**kwargs)
        logger.info("Executed max_consecutive_drawdown_trades tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "max_consecutive_drawdown_trades",
            data={"max_consecutive_drawdown_trades": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def avg_yearly_max_drawdown(equity_curve: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _avg_yearly_max_drawdown_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity_curve = equity_curve
        if "equity_curve" in ["trades", "open_trades"] and isinstance(
            arg_equity_curve, (list, dict)
        ):
            arg_equity_curve = pd.DataFrame(arg_equity_curve)
        elif "equity_curve" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_equity_curve, list):
            arg_equity_curve = pd.Series(arg_equity_curve)
        kwargs["equity_curve"] = arg_equity_curve

        res = _avg_yearly_max_drawdown_impl(**kwargs)
        logger.info("Executed avg_yearly_max_drawdown tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "avg_yearly_max_drawdown", data={"avg_yearly_max_drawdown": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_strategy_drawdown_date(equity_curve: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _max_strategy_drawdown_date_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity_curve = equity_curve
        if "equity_curve" in ["trades", "open_trades"] and isinstance(
            arg_equity_curve, (list, dict)
        ):
            arg_equity_curve = pd.DataFrame(arg_equity_curve)
        elif "equity_curve" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_equity_curve, list):
            arg_equity_curve = pd.Series(arg_equity_curve)
        kwargs["equity_curve"] = arg_equity_curve

        res = _max_strategy_drawdown_date_impl(**kwargs)
        logger.info("Executed max_strategy_drawdown_date tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "max_strategy_drawdown_date",
            data={"max_strategy_drawdown_date": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_close_to_close_drawdown_date(
    trades: pd.DataFrame, closed_only: bool = True
) -> dict[str, Any]:
    """AI Tool wrapper for _max_close_to_close_drawdown_date_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        arg_closed_only = closed_only
        if "closed_only" in ["trades", "open_trades"] and isinstance(
            arg_closed_only, (list, dict)
        ):
            arg_closed_only = pd.DataFrame(arg_closed_only)
        elif "closed_only" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_closed_only, list):
            arg_closed_only = pd.Series(arg_closed_only)
        kwargs["closed_only"] = arg_closed_only

        res = _max_close_to_close_drawdown_date_impl(**kwargs)
        logger.info("Executed max_close_to_close_drawdown_date tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "max_close_to_close_drawdown_date",
            data={"max_close_to_close_drawdown_date": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def ulcer_index(equity_curve: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _ulcer_index_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity_curve = equity_curve
        if "equity_curve" in ["trades", "open_trades"] and isinstance(
            arg_equity_curve, (list, dict)
        ):
            arg_equity_curve = pd.DataFrame(arg_equity_curve)
        elif "equity_curve" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_equity_curve, list):
            arg_equity_curve = pd.Series(arg_equity_curve)
        kwargs["equity_curve"] = arg_equity_curve

        res = _ulcer_index_impl(**kwargs)
        logger.info("Executed ulcer_index tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result("ulcer_index", data={"ulcer_index": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def pain_index(equity_curve: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _pain_index_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity_curve = equity_curve
        if "equity_curve" in ["trades", "open_trades"] and isinstance(
            arg_equity_curve, (list, dict)
        ):
            arg_equity_curve = pd.DataFrame(arg_equity_curve)
        elif "equity_curve" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_equity_curve, list):
            arg_equity_curve = pd.Series(arg_equity_curve)
        kwargs["equity_curve"] = arg_equity_curve

        res = _pain_index_impl(**kwargs)
        logger.info("Executed pain_index tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result("pain_index", data={"pain_index": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def avg_underwater_drawdown_percent(equity_curve: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _avg_underwater_drawdown_percent_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity_curve = equity_curve
        if "equity_curve" in ["trades", "open_trades"] and isinstance(
            arg_equity_curve, (list, dict)
        ):
            arg_equity_curve = pd.DataFrame(arg_equity_curve)
        elif "equity_curve" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_equity_curve, list):
            arg_equity_curve = pd.Series(arg_equity_curve)
        kwargs["equity_curve"] = arg_equity_curve

        res = _avg_underwater_drawdown_percent_impl(**kwargs)
        logger.info("Executed avg_underwater_drawdown_percent tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "avg_underwater_drawdown_percent",
            data={"avg_underwater_drawdown_percent": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def pain_ratio(equity_curve: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _pain_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity_curve = equity_curve
        if "equity_curve" in ["trades", "open_trades"] and isinstance(
            arg_equity_curve, (list, dict)
        ):
            arg_equity_curve = pd.DataFrame(arg_equity_curve)
        elif "equity_curve" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_equity_curve, list):
            arg_equity_curve = pd.Series(arg_equity_curve)
        kwargs["equity_curve"] = arg_equity_curve

        res = _pain_ratio_impl(**kwargs)
        logger.info("Executed pain_ratio tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result("pain_ratio", data={"pain_ratio": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def calculate_drawdown_metrics(equity_curve: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_drawdown_metrics_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity_curve = equity_curve
        if "equity_curve" in ["trades", "open_trades"] and isinstance(
            arg_equity_curve, (list, dict)
        ):
            arg_equity_curve = pd.DataFrame(arg_equity_curve)
        elif "equity_curve" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_equity_curve, list):
            arg_equity_curve = pd.Series(arg_equity_curve)
        kwargs["equity_curve"] = arg_equity_curve

        res = _calculate_drawdown_metrics_impl(**kwargs)
        logger.info("Executed calculate_drawdown_metrics tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "calculate_drawdown_metrics",
            data={"calculate_drawdown_metrics": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}
