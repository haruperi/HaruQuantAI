"""
metrics.py - Trade performance metrics, sequence analytics, and system quality diagnostics.

This module provides a comprehensive suite of tools for evaluating trading strategy performance,
analyzing trade sequences, and calculating risk-adjusted metrics like R-multiples, expectancy,
and system quality numbers.

Classes:
    None

Functions:
    # 1. External Tools (AI-facing)
    get_r_multiples: Calculate R-multiples for trades.
    get_ordered_closed_trades: Filter and sort closed trades by time.
    win_rate_fraction: Calculate win rate on a 0-1 scale.
    avg_win_loss: Calculate mean winning and losing outcomes.
    consecutive_wins_losses: Calculate max consecutive wins and losses.
    median_mae_mfe: Calculate median Maximum Adverse and Favorable Excursion.
    get_mae_mfe_r: Get MAE and MFE normalized to R-space.
    t_statistic: Calculate t-statistic for mean trade outcome.
    open_position_pnl: Calculate total unrealized P&L from open positions.
    total_trades: Count total number of closed trades.
    winning_trades: Count number of winning trades.
    losing_trades: Count number of losing trades.
    breakeven_trades: Count number of breakeven trades.
    long_trades: Count number of long trades.
    short_trades: Count number of short trades.
    count_open_trades: Count currently open trades.
    slippage_paid: Calculate total slippage costs.
    commission_paid: Calculate total commission costs.
    swap_paid: Calculate total swap costs.
    win_rate: Calculate win percentage (0-100).
    loss_rate: Calculate loss percentage (0-100).
    avg_win: Calculate average profit of winning trades.
    avg_loss: Calculate average loss of losing trades.
    largest_win: Find largest single trade profit.
    largest_loss: Find largest single trade loss.
    median_win: Calculate median profit of winning trades.
    median_loss: Calculate median loss of losing trades.
    expectancy: Calculate monetary expectancy.
    expectancy_r: Calculate R-multiple expectancy.
    max_size_held: Calculate maximum gross contracts held.
    max_net_size_held: Calculate maximum net directional size.
    max_long_size_held: Calculate maximum long contracts held.
    max_short_size_held: Calculate maximum short contracts held.
    avg_r_multiple: Calculate average R-multiple.
    median_r_multiple: Calculate median R-multiple.
    r_multiple_distribution: Calculate R-multiple distribution statistics.
    r_expectancy: Alias for expectancy_r.
    max_r_multiple: Find maximum R-multiple.
    min_r_multiple: Find minimum R-multiple.
    median_mae_r: Calculate median MAE in R-terms.
    median_mfe_r: Calculate median MFE in R-terms.
    max_consecutive_wins: Calculate maximum consecutive wins.
    max_consecutive_losses: Calculate maximum consecutive losses.
    avg_consecutive_wins: Calculate average length of winning streaks.
    avg_consecutive_losses: Calculate average length of losing streaks.
    win_loss_streaks: Get all winning and losing streak lengths.
    avg_time_in_trade: Calculate average trade duration in hours.
    median_time_in_trade: Calculate median trade duration in hours.
    max_time_in_trade: Calculate maximum trade duration in hours.
    min_time_in_trade: Calculate minimum trade duration in hours.
    sqn: Calculate System Quality Number (Van Tharp).
    kelly_criterion: Calculate Kelly Criterion fraction.
    compute_r_trade_metrics: Calculate summary metrics from R-multiples.
    compute_trade_metrics: Calculate summary metrics from raw trade data.
    compute_equity_metrics: Calculate equity-curve based metrics.
    trade_efficiency: Calculate trade efficiency (Realized/MFE).
    r_signal_to_noise: Calculate R-multiple signal-to-noise ratio.
    rolling_expectancy_stability: Calculate stability of expectancy over time.
    win_after_win_probability: Calculate conditional win probability.
    runs_test_zscore: Perform Wald-Wolfowitz runs test.
    trading_period_duration: Calculate total duration of trading history.
    trade_outcome_entropy: Calculate Shannon entropy of trade outcomes.
    longest_flat_period_duration: Find longest period without active trades.
    calculate_trade_metrics: High-level core trade metrics calculator.

    # 2. Internal Implementations (_impl)
    _get_r_multiples_impl: Logic for R-multiple calculation.
    _get_ordered_closed_trades_impl: Logic for ordering closed trades.
    _win_rate_fraction_impl: Logic for win rate fraction.
    _avg_win_loss_impl: Logic for mean win/loss.
    _consecutive_wins_losses_impl: Logic for consecutive counts.
    _median_mae_mfe_impl: Logic for median MAE/MFE.
    _get_mae_mfe_r_impl: Logic for R-space excursion normalization.
    _t_statistic_impl: Logic for t-statistic.
    _open_position_pnl_impl: Logic for unrealized P&L.
    _total_trades_impl: Logic for counting closed trades.
    _winning_trades_impl: Logic for counting winning trades.
    _losing_trades_impl: Logic for counting losing trades.
    _breakeven_trades_impl: Logic for counting breakeven trades.
    _long_trades_impl: Logic for counting long trades.
    _short_trades_impl: Logic for counting short trades.
    _count_open_trades_impl: Logic for counting open trades.
    _slippage_paid_impl: Logic for slippage costs.
    _commission_paid_impl: Logic for commission costs.
    _swap_paid_impl: Logic for swap costs.
    _win_rate_impl: Logic for win percentage.
    _loss_rate_impl: Logic for loss percentage.
    _avg_win_impl: Logic for average win.
    _avg_loss_impl: Logic for average loss.
    _largest_win_impl: Logic for maximum win.
    _largest_loss_impl: Logic for maximum loss.
    _median_win_impl: Logic for median win.
    _median_loss_impl: Logic for median loss.
    _expectancy_impl: Logic for monetary expectancy.
    _expectancy_r_impl: Logic for R-expectancy.
    _max_size_held_impl: Logic for gross size.
    _max_net_size_held_impl: Logic for net size.
    _max_long_size_held_impl: Logic for long size.
    _max_short_size_held_impl: Logic for short size.
    _avg_r_multiple_impl: Logic for average R.
    _median_r_multiple_impl: Logic for median R.
    _r_multiple_distribution_impl: Logic for R distribution.
    _max_r_multiple_impl: Logic for maximum R.
    _min_r_multiple_impl: Logic for minimum R.
    _median_mae_r_impl: Logic for median MAE R.
    _median_mfe_r_impl: Logic for median MFE R.
    _max_consecutive_wins_impl: Logic for max consecutive wins.
    _max_consecutive_losses_impl: Logic for max consecutive losses.
    _avg_consecutive_wins_impl: Logic for avg winning streaks.
    _avg_consecutive_losses_impl: Logic for avg losing streaks.
    _win_loss_streaks_impl: Logic for streak collection.
    _avg_time_in_trade_impl: Logic for average trade duration.
    _median_time_in_trade_impl: Logic for median trade duration.
    _max_time_in_trade_impl: Logic for maximum trade duration.
    _min_time_in_trade_impl: Logic for minimum trade duration.
    _sqn_impl: Logic for SQN calculation.
    _kelly_criterion_impl: Logic for Kelly fraction.
    _compute_r_trade_metrics_impl: Logic for summary R metrics.
    _compute_trade_metrics_impl: Logic for summary trade metrics.
    _compute_equity_metrics_impl: Logic for equity metrics.
    _trade_efficiency_impl: Logic for trade efficiency.
    _r_signal_to_noise_impl: Logic for R signal-to-noise.
    _rolling_expectancy_stability_impl: Logic for expectancy stability.
    _win_after_win_probability_impl: Logic for conditional win probability.
    _runs_test_zscore_impl: Logic for runs test.
    _trading_period_duration_impl: Logic for period duration.
    _trade_outcome_entropy_impl: Logic for outcome entropy.
    _longest_flat_period_duration_impl: Logic for flat period detection.
    _calculate_trade_metrics_impl: Logic for core metrics calculator.

    # 3. Utility Helpers
    _to_datetime_series: Convert a timestamp series safely.
    _get_size_col: Return the first recognized position-size column name.
    _consecutive_kernel: Numba-optimized streak calculator.
    _r_trade_efficiency: Calculate realized R captured relative to available MFE.
    _r_edge_ratio: Calculate excursion edge ratio as MFE divided by MAE magnitude.
"""

from typing import Any

import numpy as np
import pandas as pd

from . import drawdowns, ratios
from .common import (
    EPSILON,
    _has_col,
    _merge_intervals,
    _to_1d_float_array,
    analytics_tool_result,
    classify_trades,
    get_closed_trades,
    get_r_multiples,
    max_gross_size_held,
)

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


# =========================================================================
# Utility & Kernel Helpers
# =========================================================================


def get_r_multiples(trades: pd.DataFrame, closed_only: bool = True) -> pd.Series:
    """Get R-multiples for trades.

    Purpose:
        Get R-multiples for trades.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.
        closed_only:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    data = get_closed_trades(trades) if closed_only else trades
    if data.empty or not _has_col(data, "profit_loss"):
        return pd.Series(dtype=float)

    # 1. Official Risk Amount (Monetary)
    for col in ["initial_risk_amount", "initial_risk"]:
        if col in data.columns:
            risk = data[col].abs().replace(0, np.nan)
            r = data["profit_loss"] / risk
            r = r.replace([np.inf, -np.inf], np.nan).dropna()
            if not r.empty:
                return r

    # 2. Fallback: Use Average Loss as proxy for 1R baseline
    avg_l = abs(avg_loss(data))
    if avg_l > EPSILON:
        r = data["profit_loss"] / avg_l
        return r.replace([np.inf, -np.inf], np.nan).dropna()

    return pd.Series(dtype=float)


def _get_ordered_closed_trades_impl(trades: pd.DataFrame) -> pd.DataFrame:
    """Filter for closed trades and sort them by time to ensure sequence-dependent metrics are correct.

    Purpose:
        Filter for closed trades and sort them by time to ensure sequence-dependent metrics are correct.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    closed = get_closed_trades(trades).copy()
    if closed.empty:
        return closed

    if "close_time" in closed.columns:
        return closed.sort_values("close_time")
    if "open_time" in closed.columns:
        return closed.sort_values("open_time")
    return closed


def _to_datetime_series(series: pd.Series) -> pd.Series:
    """Convert a timestamp series safely, supporting datetime values and Unix seconds."""
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_datetime(series, unit="s")
    return pd.to_datetime(series)


def _win_rate_fraction_impl(values, epsilon: float = EPSILON) -> float:
    """Win rate on a 0-1 scale.

    Purpose:
        Win rate on a 0-1 scale.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        values:
            Analytics input consumed by this function.
        epsilon:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    normalized = _to_1d_float_array(values)
    if len(normalized) == 0:
        return float("nan")
    return float(np.mean(normalized > epsilon))


def _avg_win_loss_impl(values, epsilon: float = EPSILON) -> tuple[float, float]:
    """Mean winning and losing outcomes.

    Purpose:
        Mean winning and losing outcomes.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        values:
            Analytics input consumed by this function.
        epsilon:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    normalized = _to_1d_float_array(values)
    wins = normalized[normalized > epsilon]
    losses = normalized[normalized < -epsilon]

    avg_win = float(np.mean(wins)) if len(wins) else float("nan")
    avg_loss = float(np.mean(losses)) if len(losses) else float("nan")
    return avg_win, avg_loss


def _consecutive_wins_losses_impl(values, epsilon: float = EPSILON) -> tuple[int, int]:
    """Max consecutive wins and losses from a 1D array.

    Purpose:
        Max consecutive wins and losses from a 1D array.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        values:
            Analytics input consumed by this function.
        epsilon:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    normalized = _to_1d_float_array(values)

    max_wins = 0
    max_losses = 0
    curr_wins = 0
    curr_losses = 0

    for val in normalized:
        if val > epsilon:
            curr_wins += 1
            curr_losses = 0
        elif val < -epsilon:
            curr_losses += 1
            curr_wins = 0
        else:
            curr_wins = 0
            curr_losses = 0

        max_wins = max(max_wins, curr_wins)
        max_losses = max(max_losses, curr_losses)

    return max_wins, max_losses


# Helper kernels and functions moved or unified above.


def _median_mae_mfe_impl(mae: np.ndarray, mfe: np.ndarray) -> tuple[float, float]:
    """Calculate median MAE and MFE.

    Purpose:
        Calculate median MAE and MFE.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        mae:
            Analytics input consumed by this function.
        mfe:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    mae = np.asarray(mae, dtype=float)
    mfe = np.asarray(mfe, dtype=float)
    return (
        float(np.median(mae)) if len(mae) else 0.0,
        float(np.median(mfe)) if len(mfe) else 0.0,
    )


def _get_mae_mfe_r_impl(trades: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Get MAE and MFE normalized to R-space.

    Purpose:
        Get MAE and MFE normalized to R-space.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if trades.empty:
        return pd.Series(dtype=float), pd.Series(dtype=float)

    # Prefer pre-calculated R-space columns
    if "mae_r" in trades.columns and "mfe_r" in trades.columns:
        return trades["mae_r"], trades["mfe_r"]

    # Fallback: calculate from USD and risk amount
    if "initial_risk_amount" in trades.columns:
        risk = trades["initial_risk_amount"].abs().replace(0, np.nan)
        mae_usd = (
            trades["mae_usd"]
            if "mae_usd" in trades.columns
            else pd.Series(0.0, index=trades.index)
        )
        mfe_usd = (
            trades["mfe_usd"]
            if "mfe_usd" in trades.columns
            else pd.Series(0.0, index=trades.index)
        )
        return mae_usd / risk, mfe_usd / risk

    return pd.Series(0.0, index=trades.index), pd.Series(0.0, index=trades.index)


def _t_statistic_impl(values) -> float:
    """Calculate t-statistic for mean outcome.

    Purpose:
        Calculate t-statistic for mean outcome.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        values:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    normalized = _to_1d_float_array(values)
    n = len(normalized)
    if n < 2:
        return float("nan")

    mean = np.mean(normalized)
    std = np.std(normalized, ddof=1)
    if std == 0:
        return float("inf") if mean > 0 else float("-inf") if mean < 0 else float("nan")

    return float(mean / (std / np.sqrt(n)))


# =========================================================================
# Core Trade Counts & Costs
# =========================================================================


def _open_position_pnl_impl(open_trades: pd.DataFrame) -> float:
    """Total unrealized P&L from open positions.

    Purpose:
        Total unrealized P&L from open positions.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        open_trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if open_trades.empty or not _has_col(open_trades, "profit_loss"):
        return 0.0
    return float(open_trades["profit_loss"].sum())


def _total_trades_impl(trades: pd.DataFrame) -> int:
    """Total number of closed trades.

    Purpose:
        Total number of closed trades.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    return len(get_closed_trades(trades))


def _winning_trades_impl(trades: pd.DataFrame) -> int:
    """Count of closed winning trades (> EPSILON).

    Purpose:
        Count of closed winning trades (> EPSILON).
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    wins, _, _ = classify_trades(get_closed_trades(trades))
    return len(wins)


def _losing_trades_impl(trades: pd.DataFrame) -> int:
    """Count of closed losing trades (< -EPSILON).

    Purpose:
        Count of closed losing trades (< -EPSILON).
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    _, losses, _ = classify_trades(get_closed_trades(trades))
    return len(losses)


def _breakeven_trades_impl(trades: pd.DataFrame) -> int:
    """Count of closed trades with |PnL| <= EPSILON.

    Purpose:
        Count of closed trades with |PnL| <= EPSILON.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    _, _, be = classify_trades(get_closed_trades(trades))
    return len(be)


def _long_trades_impl(trades: pd.DataFrame) -> int:
    """Count of closed long trades.

    Purpose:
        Count of closed long trades.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    closed = get_closed_trades(trades)
    if "type" not in closed.columns:
        return 0
    return len(closed[closed["type"] == "buy"])


def _short_trades_impl(trades: pd.DataFrame) -> int:
    """Count of closed short trades.

    Purpose:
        Count of closed short trades.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    closed = get_closed_trades(trades)
    if "type" not in closed.columns:
        return 0
    return len(closed[closed["type"] == "sell"])


def _count_open_trades_impl(trades: pd.DataFrame) -> int:
    """Count of trades currently open.

    Purpose:
        Count of trades currently open.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    closed = get_closed_trades(trades)
    return len(trades) - len(closed)


def _slippage_paid_impl(trades: pd.DataFrame, closed_only: bool = False) -> float:
    """Total absolute slippage costs paid (Option A: positive paid).

    Purpose:
        Total absolute slippage costs paid (Option A: positive paid).
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.
        closed_only:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    data = get_closed_trades(trades) if closed_only else trades
    if data.empty or not _has_col(data, "slippage_usd"):
        return 0.0
    return float(data["slippage_usd"].abs().sum())


def _commission_paid_impl(trades: pd.DataFrame, closed_only: bool = False) -> float:
    """Total absolute commission costs paid (Option A: positive paid).

    Purpose:
        Total absolute commission costs paid (Option A: positive paid).
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.
        closed_only:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    data = get_closed_trades(trades) if closed_only else trades
    if data.empty or not _has_col(data, "commission"):
        return 0.0
    return float(data["commission"].abs().sum())


def _swap_paid_impl(trades: pd.DataFrame, closed_only: bool = False) -> float:
    """Total absolute swap costs paid (Option A: positive paid).

    Purpose:
        Total absolute swap costs paid (Option A: positive paid).
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.
        closed_only:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    data = get_closed_trades(trades) if closed_only else trades
    if data.empty or not _has_col(data, "swap"):
        return 0.0
    return float(data["swap"].abs().sum())


# =========================================================================
# Trade P&L Statistics
# =========================================================================


def _win_rate_impl(trades: pd.DataFrame) -> float:
    """Percentage of winning trades (0-100).

    Purpose:
        Percentage of winning trades (0-100).
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    closed = get_closed_trades(trades)
    if len(closed) == 0:
        return 0.0
    return (_winning_trades_impl(closed) / len(closed)) * 100.0


def _loss_rate_impl(trades: pd.DataFrame) -> float:
    """Percentage of losing trades (0-100).

    Purpose:
        Percentage of losing trades (0-100).
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    closed = get_closed_trades(trades)
    if len(closed) == 0:
        return 0.0
    return (_losing_trades_impl(closed) / len(closed)) * 100.0


def _avg_win_impl(trades: pd.DataFrame) -> float:
    """Mean profit of winning trades.

    Purpose:
        Mean profit of winning trades.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if trades.empty or not _has_col(trades, "profit_loss"):
        return 0.0
    wins, _, _ = classify_trades(get_closed_trades(trades))
    return float(wins["profit_loss"].mean()) if not wins.empty else 0.0


def avg_loss(trades: pd.DataFrame) -> float:
    """Mean loss of losing trades.

    Purpose:
        Mean loss of losing trades.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if trades.empty or not _has_col(trades, "profit_loss"):
        return 0.0
    _, losses, _ = classify_trades(get_closed_trades(trades))
    return float(losses["profit_loss"].mean()) if not losses.empty else 0.0


def _largest_win_impl(trades: pd.DataFrame) -> float:
    """Maximum profit from a single trade.

    Purpose:
        Maximum profit from a single trade.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if trades.empty or not _has_col(trades, "profit_loss"):
        return 0.0
    closed = get_closed_trades(trades)
    return float(closed["profit_loss"].max()) if not closed.empty else 0.0


def _largest_loss_impl(trades: pd.DataFrame) -> float:
    """Maximum loss from a single trade.

    Purpose:
        Maximum loss from a single trade.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if trades.empty or not _has_col(trades, "profit_loss"):
        return 0.0
    closed = get_closed_trades(trades)
    return float(closed["profit_loss"].min()) if not closed.empty else 0.0


def _median_win_impl(trades: pd.DataFrame) -> float:
    """Median P&L of winning trades.

    Purpose:
        Median P&L of winning trades.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    wins, _, _ = classify_trades(get_closed_trades(trades))
    return float(wins["profit_loss"].median()) if not wins.empty else 0.0


def _median_loss_impl(trades: pd.DataFrame) -> float:
    """Median P&L of losing trades.

    Purpose:
        Median P&L of losing trades.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    _, losses, _ = classify_trades(get_closed_trades(trades))
    return float(losses["profit_loss"].median()) if not losses.empty else 0.0


def _expectancy_impl(trades: pd.DataFrame) -> float:
    """Calculate expectancy using ratios module.

    Purpose:
        Calculate expectancy using ratios module.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    return ratios.__expectancy_impl_impl(trades)


def _expectancy_r_impl(r_values: pd.Series | np.ndarray) -> float:
    """Calculate R-expectancy using ratios module.

    Purpose:
        Calculate R-expectancy using ratios module.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        r_values:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    return ratios.__expectancy_r_impl_impl(r_values)


def _max_size_held_impl(trades: pd.DataFrame) -> float:
    """Maximum total contracts held (Gross). Wrapper for max_gross_size_held.

    Purpose:
        Maximum total contracts held (Gross). Wrapper for max_gross_size_held.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    return max_gross_size_held(trades)


def _max_net_size_held_impl(
    trades: pd.DataFrame, end_time: pd.Timestamp | None = None
) -> float:
    """Maximum net directional size held (Long - Short). Returns absolute peak.

    Purpose:
        Maximum net directional size held (Long - Short). Returns absolute peak.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.
        end_time:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if trades.empty:
        return 0.0

    size_col = _get_size_col(trades)
    if not size_col or "type" not in trades.columns:
        return 0.0

    is_buy = (trades["type"] == "buy").values
    raw_sizes = (
        trades[size_col].abs().values
    )  # Standardize to positive size, then apply type

    open_sizes = np.where(is_buy, raw_sizes, -raw_sizes)
    close_sizes = -open_sizes

    o_times = trades["open_time"].values
    c_times = (
        trades["close_time"]
        .fillna(end_time if end_time else trades["open_time"].max())
        .values
    )

    event_times = np.concatenate([o_times, c_times])
    event_sizes = np.concatenate([open_sizes, close_sizes])

    idx = np.lexsort((-event_sizes, event_times))
    sorted_sizes = event_sizes[idx]

    current = 0.0
    peak = 0.0
    for s in sorted_sizes:
        current += s
        peak = max(peak, abs(current))

    return float(peak)


def _max_long_size_held_impl(trades: pd.DataFrame) -> float:
    """Maximum total long contracts held at any one time.

    Purpose:
        Maximum total long contracts held at any one time.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    return (
        max_gross_size_held(trades[trades["type"] == "buy"])
        if "type" in trades.columns
        else 0.0
    )


def _max_short_size_held_impl(trades: pd.DataFrame) -> float:
    """Maximum total short contracts held at any one time.

    Purpose:
        Maximum total short contracts held at any one time.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    return (
        max_gross_size_held(trades[trades["type"] == "sell"])
        if "type" in trades.columns
        else 0.0
    )


def _get_size_col(trades: pd.DataFrame) -> str | None:
    """Return the first recognized position-size column name."""
    for col in ["size", "quantity", "volume"]:
        if col in trades.columns:
            return col
    return None


# =========================================================================
# R-Multiple Analytics
# =========================================================================


def _avg_r_multiple_impl(trades: pd.DataFrame) -> float:
    """Calculate average R-multiple across all trades.

    Purpose:
        Calculate average R-multiple across all trades.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    r_values = get_r_multiples(trades)
    if r_values.empty:
        return 0.0
    return float(r_values.mean())


def _median_r_multiple_impl(trades: pd.DataFrame) -> float:
    """Calculate median R-multiple.

    Purpose:
        Calculate median R-multiple.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    r_values = get_r_multiples(trades)
    if r_values.empty:
        return 0.0
    return float(r_values.median())


def _r_multiple_distribution_impl(trades: pd.DataFrame) -> dict[str, float]:
    """Calculate R-multiple distribution statistics.

    Purpose:
        Calculate R-multiple distribution statistics.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    r_values = get_r_multiples(trades)
    if r_values.empty:
        return {
            "mean": 0.0,
            "median": 0.0,
            "std": 0.0,
            "min": 0.0,
            "max": 0.0,
            "q25": 0.0,
            "q75": 0.0,
        }

    return {
        "mean": float(r_values.mean()),
        "median": float(r_values.median()),
        "std": float(r_values.std()),
        "min": float(r_values.min()),
        "max": float(r_values.max()),
        "q25": float(r_values.quantile(0.25)),
        "q75": float(r_values.quantile(0.75)),
    }


def _r_expectancy_impl(trades: pd.DataFrame) -> float:
    """Calculate R-expectancy using ratios module.

    Purpose:
        Calculate R-expectancy using ratios module.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    return ratios.__expectancy_r_impl_impl(get_r_multiples(trades))


def _max_r_multiple_impl(trades: pd.DataFrame) -> float:
    """Calculate maximum R-multiple achieved.

    Purpose:
        Calculate maximum R-multiple achieved.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    r_values = get_r_multiples(trades)
    if r_values.empty:
        return 0.0
    return float(r_values.max())


def _min_r_multiple_impl(trades: pd.DataFrame) -> float:
    """Calculate minimum R-multiple achieved.

    Purpose:
        Calculate minimum R-multiple achieved.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    r_values = get_r_multiples(trades)
    if r_values.empty:
        return 0.0
    return float(r_values.min())


def _median_mae_r_impl(trades: pd.DataFrame) -> float:
    """Median Maximum Adverse Excursion in R-multiple terms.

    Purpose:
        Median Maximum Adverse Excursion in R-multiple terms.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if trades.empty or "mae_usd" not in trades.columns:
        return 0.0

    # Extract risk for normalization
    risk_cols = ["initial_risk_amount", "initial_risk"]
    risk = pd.Series(dtype=float)
    for col in risk_cols:
        if col in trades.columns:
            risk = trades[col].abs().replace(0, np.nan)
            break

    if risk.empty:
        # Fallback to avg loss as risk proxy if no explicit risk
        from .common import avg_loss

        risk_val = abs(avg_loss(trades))
        if risk_val < EPSILON:
            return 0.0
        mae_r = trades["mae_usd"].abs() / risk_val
    else:
        mae_r = trades["mae_usd"].abs() / risk

    return float(mae_r.dropna().median())


def _median_mfe_r_impl(trades: pd.DataFrame) -> float:
    """Median Maximum Favorable Excursion in R-multiple terms.

    Purpose:
        Median Maximum Favorable Excursion in R-multiple terms.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if trades.empty or "mfe_usd" not in trades.columns:
        return 0.0

    risk_cols = ["initial_risk_amount", "initial_risk"]
    risk = pd.Series(dtype=float)
    for col in risk_cols:
        if col in trades.columns:
            risk = trades[col].abs().replace(0, np.nan)
            break

    if risk.empty:
        from .common import avg_loss

        risk_val = abs(avg_loss(trades))
        if risk_val < EPSILON:
            return 0.0
        mfe_r = trades["mfe_usd"].abs() / risk_val
    else:
        mfe_r = trades["mfe_usd"].abs() / risk

    return float(mfe_r.dropna().median())


# =========================================================================
# Trade Sequence Quality
# =========================================================================


@njit(cache=True)
def _consecutive_kernel(is_win):
    """
    Calculates max consecutive wins or losses.
    NOTE: Input must be a boolean array where True is the event of interest (Win).
    Any non-win (Loss or Breakeven) breaks the streak.
    """
    max_streak = 0
    current_streak = 0
    for i in range(len(is_win)):
        if is_win[i]:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    return max_streak


def _max_consecutive_wins_impl(trades: pd.DataFrame) -> int:
    """Calculate maximum consecutive winning trades.

    Purpose:
        Calculate maximum consecutive winning trades.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    ordered = _get_ordered_closed_trades_impl(trades)
    if ordered.empty:
        return 0
    return int(_consecutive_kernel((ordered["profit_loss"] > EPSILON).values))


def _max_consecutive_losses_impl(trades: pd.DataFrame) -> int:
    """Calculate maximum consecutive losing trades.

    Purpose:
        Calculate maximum consecutive losing trades.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    ordered = _get_ordered_closed_trades_impl(trades)
    if ordered.empty:
        return 0
    return int(_consecutive_kernel((ordered["profit_loss"] < -EPSILON).values))


def _avg_consecutive_wins_impl(trades: pd.DataFrame) -> float:
    """Average length of winning streaks.

    Purpose:
        Average length of winning streaks.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    streaks = _win_loss_streaks_impl(trades)["win_streaks"]
    return float(np.mean(streaks)) if streaks else 0.0


def _avg_consecutive_losses_impl(trades: pd.DataFrame) -> float:
    """Average length of losing streaks.

    Purpose:
        Average length of losing streaks.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    streaks = _win_loss_streaks_impl(trades)["loss_streaks"]
    return float(np.mean(streaks)) if streaks else 0.0


def _win_loss_streaks_impl(trades: pd.DataFrame) -> dict[str, list[int]]:
    """Get all winning and losing streaks.

    Purpose:
        Get all winning and losing streaks.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    ordered = _get_ordered_closed_trades_impl(trades)
    if ordered.empty:
        return {"win_streaks": [], "loss_streaks": []}

    pnl = ordered["profit_loss"].values

    win_streaks = []
    loss_streaks = []
    current_win = 0
    current_loss = 0

    for val in pnl:
        if val > EPSILON:
            # Win
            if current_loss > 0:
                loss_streaks.append(current_loss)
                current_loss = 0
            current_win += 1
        elif val < -EPSILON:
            # Loss
            if current_win > 0:
                win_streaks.append(current_win)
                current_win = 0
            current_loss += 1
        else:
            # Breakeven - breaks both
            if current_win > 0:
                win_streaks.append(current_win)
            if current_loss > 0:
                loss_streaks.append(current_loss)
            current_win = 0
            current_loss = 0

    if current_win > 0:
        win_streaks.append(current_win)
    if current_loss > 0:
        loss_streaks.append(current_loss)

    return {"win_streaks": win_streaks, "loss_streaks": loss_streaks}


# =========================================================================
# Time-in-Trade
# =========================================================================


def _avg_time_in_trade_impl(trades: pd.DataFrame) -> float:
    """Calculate average time in trade (hours).

    Purpose:
        Calculate average time in trade (hours).
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if len(trades) == 0 or "time_in_trade" not in trades.columns:
        return 0.0
    return float(trades["time_in_trade"].mean())


def _median_time_in_trade_impl(trades: pd.DataFrame) -> float:
    """Calculate median time in trade (hours).

    Purpose:
        Calculate median time in trade (hours).
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if len(trades) == 0 or "time_in_trade" not in trades.columns:
        return 0.0
    return float(trades["time_in_trade"].median())


def _max_time_in_trade_impl(trades: pd.DataFrame) -> float:
    """Calculate maximum time in trade (hours).

    Purpose:
        Calculate maximum time in trade (hours).
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if len(trades) == 0 or "time_in_trade" not in trades.columns:
        return 0.0
    return float(trades["time_in_trade"].max())


def _min_time_in_trade_impl(trades: pd.DataFrame) -> float:
    """Calculate minimum time in trade (hours).

    Purpose:
        Calculate minimum time in trade (hours).
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if len(trades) == 0 or "time_in_trade" not in trades.columns:
        return 0.0
    return float(trades["time_in_trade"].min())


# =========================================================================
# System Quality Metrics
# =========================================================================


def _sqn_impl(trades: pd.DataFrame | pd.Series | np.ndarray) -> float:
    """Calculate System Quality Number (Van Tharp).

    Purpose:
        Calculate System Quality Number (Van Tharp).
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if isinstance(trades, pd.DataFrame):
        r_series = get_r_multiples(trades)
        if r_series.empty:
            return 0.0
        r_values = r_series.astype(float).to_numpy()
    else:
        r_values = _to_1d_float_array(trades)

    n = len(r_values)
    if n < 2:
        return 0.0

    avg_r = r_values.mean()
    std_r = np.std(r_values, ddof=1)

    if std_r == 0:
        return 0.0

    return float(np.sqrt(n) * (avg_r / std_r))


def _kelly_criterion_impl(trades: pd.DataFrame | pd.Series | np.ndarray) -> float:
    """Calculate Kelly Criterion percentage based on R-multiples (if available) or Returns.

    Purpose:
        Calculate Kelly Criterion percentage based on R-multiples (if available) or Returns.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if isinstance(trades, pd.DataFrame):
        # Prefer R-multiples for Kelly as it normalizes for position size
        values = get_r_multiples(trades).values
    else:
        values = _to_1d_float_array(trades)

    if len(values) == 0:
        return 0.0

    # Probability of win (R > EPSILON)
    wins = values[values > EPSILON]
    losses = values[values < -EPSILON]

    n_total = len(values)
    if n_total == 0:
        return 0.0

    p = len(wins) / n_total
    q = 1.0 - p

    avg_w = float(np.mean(wins)) if len(wins) > 0 else 0.0
    avg_l = abs(float(np.mean(losses))) if len(losses) > 0 else 0.0

    if avg_l == 0:
        return p if avg_w > 0 else 0.0

    if avg_w == 0:
        return -1.0 if avg_l > 0 else 0.0

    payoff_ratio = avg_w / avg_l
    kelly_fraction = p - (q / payoff_ratio)

    return float(kelly_fraction)


def _compute_r_trade_metrics_impl(
    r_values: np.ndarray,
    mae_r: np.ndarray | None = None,
    mfe_r: np.ndarray | None = None,
) -> dict[str, float]:
    """Calculate trade metrics from R-multiple space.

    Purpose:
        Calculate trade metrics from R-multiple space.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        r_values:
            Analytics input consumed by this function.
        mae_r:
            Analytics input consumed by this function.
        mfe_r:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    normalized = _to_1d_float_array(r_values)

    summary = {
        "n_trades": len(normalized),
        "expectancy": ratios.__expectancy_impl_impl(normalized),
        "win_rate": _win_rate_fraction_impl(normalized),
        "profit_factor": ratios._profit_factor_impl(normalized),
        "sqn": _sqn_impl(normalized),
        "kelly_criterion": _kelly_criterion_impl(normalized),
        "t_stat": _t_statistic_impl(normalized),
    }

    avg_win_val, avg_loss_val = _avg_win_loss_impl(normalized)
    summary["avg_win"] = avg_win_val
    summary["avg_loss"] = avg_loss_val
    summary["payoff_ratio"] = ratios._payoff_ratio_impl(normalized)

    max_cons_wins, max_cons_losses = _consecutive_wins_losses_impl(normalized)
    summary["max_consecutive_wins"] = max_cons_wins
    summary["max_consecutive_losses"] = max_cons_losses

    if mae_r is not None:
        mae = np.asarray(mae_r, dtype=float)
        summary["median_mae"] = float(np.median(mae)) if len(mae) else float("nan")

    if mfe_r is not None:
        mfe = np.asarray(mfe_r, dtype=float)
        summary["median_mfe"] = float(np.median(mfe)) if len(mfe) else float("nan")
        if mae_r is not None:
            summary["edge_ratio"] = _r_edge_ratio(mfe, mae)
            summary["trade_efficiency"] = _r_trade_efficiency(normalized, mfe)

    return summary


def _compute_trade_metrics_impl(
    r_values: np.ndarray,
    mae: np.ndarray | None = None,
    mfe: np.ndarray | None = None,
) -> dict[str, float]:
    """Compute trade metrics from numeric R values and optional MAE/MFE arrays.

    Purpose:
        Compute trade metrics from numeric R values and optional MAE/MFE arrays.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        r_values:
            Analytics input consumed by this function.
        mae:
            Analytics input consumed by this function.
        mfe:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    return _compute_r_trade_metrics_impl(r_values, mae_r=mae, mfe_r=mfe)


def _compute_equity_metrics_impl(returns_input, periods_per_year: int = 252) -> dict:
    """Compute Edge-style equity metrics from returns inputs.

    Purpose:
        Compute Edge-style equity metrics from returns inputs.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        returns_input:
            Analytics input consumed by this function.
        periods_per_year:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    normalized = _to_1d_float_array(returns_input)
    total_return = (
        float(np.prod(1 + normalized) - 1) if len(normalized) else float("nan")
    )
    annual_return = (
        float(np.mean(normalized) * periods_per_year)
        if len(normalized)
        else float("nan")
    )

    return {
        "total_return": total_return,
        "annual_return": annual_return,
        "sharpe_ratio": ratios._sharpe_ratio_impl(normalized, annualize=True),
        "sortino_ratio": ratios._sortino_ratio_impl(normalized, annualize=True),
        "calmar_ratio": ratios._calmar_ratio_impl(
            normalized, periods_per_year=periods_per_year
        ),
        "max_drawdown": drawdowns._max_drawdown_impl(normalized),
        "max_dd_duration": drawdowns._max_drawdown_duration_impl(
            normalized, input_type="returns"
        ),
        "recovery_factor": drawdowns._recovery_factor_impl(normalized),
    }


# =========================================================================
# Advanced Performance & Information (Efficiency & Entropy)
# =========================================================================


def _r_trade_efficiency(r: np.ndarray, mfe: np.ndarray) -> float:
    """Calculate realized R captured relative to available MFE."""
    r = np.asarray(r, dtype=float)
    mfe = np.asarray(mfe, dtype=float)
    if len(r) != len(mfe) or len(r) == 0:
        return float("nan")

    mask = mfe > 0
    if not np.any(mask):
        return float("nan")

    return float(np.mean(r[mask] / mfe[mask]))


def _r_edge_ratio(mfe: np.ndarray, mae: np.ndarray) -> float:
    """Calculate excursion edge ratio as MFE divided by MAE magnitude."""
    mfe = np.asarray(mfe, dtype=float)
    mae = np.asarray(mae, dtype=float)
    if len(mfe) != len(mae) or len(mfe) == 0:
        return float("nan")

    mae_abs = np.abs(mae)
    mask = mae_abs > 0
    if not np.any(mask):
        return float("inf") if np.mean(mfe) > 0 else float("nan")

    return float(np.mean(mfe[mask] / mae_abs[mask]))


def _trade_efficiency_impl(trades: pd.DataFrame) -> float:
    """Efficiency = Realized Outcome / Maximum Favorable Excursion.

    Purpose:
        Efficiency = Realized Outcome / Maximum Favorable Excursion.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    closed = get_closed_trades(trades)
    if closed.empty:
        return 0.0

    # 1. Try to get R-multiples (normalized)
    r_vals = get_r_multiples(closed, closed_only=False)

    # 2. Identify MFE source
    mfe = pd.Series(dtype=float)
    if "mfe_r" in closed.columns:
        mfe = closed["mfe_r"]
    elif "mfe_usd" in closed.columns:
        # If we have R-multiples, we need MFE in R-terms
        if not r_vals.empty and "initial_risk_amount" in closed.columns:
            risk = closed["initial_risk_amount"].abs().replace(0, np.nan)
            mfe = closed["mfe_usd"] / risk
        else:
            # Fallback: Just use USD vs USD (Ratio is still valid)
            mfe = closed["mfe_usd"]
            r_vals = (
                closed["profit_loss"]
                if "profit_loss" in closed.columns
                else pd.Series(dtype=float)
            )
    elif "mfe_pips" in closed.columns:
        mfe = closed["mfe_pips"]
        r_vals = (
            closed["profit_pips"]
            if "profit_pips" in closed.columns
            else pd.Series(dtype=float)
        )

    if mfe.empty or r_vals.empty:
        return 0.0

    # Ensure index alignment and drop non-finite
    aligned = (
        pd.concat([r_vals.rename("r"), mfe.rename("mfe")], axis=1)
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )

    # Efficiency is only defined for trades that were in profit at some point
    aligned = aligned[aligned["mfe"] > EPSILON]

    if aligned.empty:
        return 0.0

    # Mean of (Realized / MFE)
    return float((aligned["r"] / aligned["mfe"]).mean())


def _r_signal_to_noise_impl(trades: pd.DataFrame) -> float:
    """Measure of trade expectancy normalized by its volatility (Mean R / Std R).

    Purpose:
        Measure of trade expectancy normalized by its volatility (Mean R / Std R).
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    r_vals = get_r_multiples(trades)
    if len(r_vals) < 5:
        return 0.0

    mu = r_vals.mean()
    sigma = r_vals.std()

    if sigma == 0:
        return float("inf") if mu > 0 else 0.0
    return float(mu / sigma)


def _rolling_expectancy_stability_impl(trades: pd.DataFrame, window: int = 50) -> float:
    """Measure of how stable the expectancy is over time using a rolling window.

    Purpose:
        Measure of how stable the expectancy is over time using a rolling window.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.
        window:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    r = get_r_multiples(trades)
    if len(r) < window:
        return 0.0

    rolling_exp = r.rolling(window).mean().dropna()
    if rolling_exp.empty:
        return 0.0

    mu = rolling_exp.mean()
    sigma = rolling_exp.std()

    if sigma == 0:
        return float("inf") if mu > 0 else 0.0
    return float(mu / sigma)


def _win_after_win_probability_impl(trades: pd.DataFrame) -> float:
    """Probability that a win is followed by another win.

    Purpose:
        Probability that a win is followed by another win.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    ordered = _get_ordered_closed_trades_impl(trades)
    if len(ordered) < 2:
        return 0.0
    wins = (ordered["profit_loss"] > EPSILON).values

    win_followed_by_win = 0
    total_wins_except_last = 0

    for i in range(len(wins) - 1):
        if wins[i]:
            total_wins_except_last += 1
            if wins[i + 1]:
                win_followed_by_win += 1

    if total_wins_except_last == 0:
        return 0.0
    return float(win_followed_by_win / total_wins_except_last)


def _runs_test_zscore_impl(trades: pd.DataFrame) -> float:
    """Wald-Wolfowitz Runs Test Z-Score.

    Purpose:
        Wald-Wolfowitz Runs Test Z-Score.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    ordered = _get_ordered_closed_trades_impl(trades)
    if len(ordered) < 10:
        return 0.0

    # Binary sequence: 1 for Win, 0 for Loss (Breakeven treated as Loss for binary test)
    seq = (ordered["profit_loss"] > EPSILON).astype(int).values
    n1 = np.sum(seq)  # Wins
    n2 = len(seq) - n1  # Non-Wins

    if n1 == 0 or n2 == 0:
        return 0.0

    # Count runs
    runs = 1
    for i in range(1, len(seq)):
        if seq[i] != seq[i - 1]:
            runs += 1

    # Expected runs
    mu = ((2.0 * n1 * n2) / (n1 + n2)) + 1
    # Variance
    var = (2.0 * n1 * n2 * (2.0 * n1 * n2 - n1 - n2)) / (
        ((n1 + n2) ** 2) * (n1 + n2 - 1)
    )

    if var <= 0:
        return 0.0
    z = (runs - mu) / np.sqrt(var)
    return float(z)


def _trading_period_duration_impl(
    trades: pd.DataFrame,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> pd.Timedelta:
    """Calculate total duration of the trading period.

    Purpose:
        Calculate total duration of the trading period.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.
        start_time:
            Analytics input consumed by this function.
        end_time:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if start_time is not None and end_time is not None:
        return pd.Timestamp(end_time) - pd.Timestamp(start_time)

    if trades.empty or "open_time" not in trades.columns:
        return pd.Timedelta(0)

    start = pd.to_datetime(trades["open_time"]).min()
    if "close_time" in trades.columns:
        end = pd.to_datetime(trades["close_time"]).max()
    else:
        end = pd.to_datetime(trades["open_time"]).max()

    return end - start


def _trade_outcome_entropy_impl(trades: pd.DataFrame) -> float:
    """Calculate Shannon entropy of trade outcomes.

    Purpose:
        Calculate Shannon entropy of trade outcomes.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    closed = get_closed_trades(trades)
    if closed.empty:
        return 0.0

    wins = _winning_trades_impl(closed)
    losses = _losing_trades_impl(closed)
    be = _breakeven_trades_impl(closed)
    total = len(closed)

    probs = [x / total for x in [wins, losses, be] if x > 0]
    if not probs:
        return 0.0

    entropy = -sum(p * np.log2(p) for p in probs)
    return float(entropy)


def _longest_flat_period_duration_impl(
    trades: pd.DataFrame,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> pd.Timedelta:
    """Calculate longest period the strategy refrained from trading (flat).

    Purpose:
        Calculate longest period the strategy refrained from trading (flat).
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.
        start_time:
            Analytics input consumed by this function.
        end_time:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if trades.empty:
        return _trading_period_duration_impl(trades, start_time, end_time)

    merged = _merge_intervals(trades, end_time)
    if not merged:
        return _trading_period_duration_impl(trades, start_time, end_time)

    gaps_ns = []

    # Gap before first trade
    if start_time:
        s_val = start_time.value
        m_start_val = merged[0][0].value
        if m_start_val > s_val:
            gaps_ns.append(m_start_val - s_val)

    # Gaps between trades
    for i in range(len(merged) - 1):
        gap = merged[i + 1][0].value - merged[i][1].value
        if gap > 0:
            gaps_ns.append(gap)

    # Gap after last trade
    if end_time:
        e_val = end_time.value
        m_end_val = merged[-1][1].value
        if e_val > m_end_val:
            gaps_ns.append(e_val - m_end_val)

    if not gaps_ns:
        return pd.Timedelta(0)

    return pd.Timedelta(max(gaps_ns), unit="ns")


# =========================================================================
# Agent-Facing Function Tools
# =========================================================================


def _calculate_trade_metrics_impl(
    *,
    trades: list[dict[str, Any]],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Calculate core trade metrics from normalized trade records.

    Purpose:
        Calculate core trade metrics from normalized trade records.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        trades:
            Analytics input consumed by this function.
        request_id:
            Analytics input consumed by this function.
        agent_name:
            Analytics input consumed by this function.
        environment:
            Analytics input consumed by this function.
        dry_run:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    frame = pd.DataFrame(trades)
    pnl = pd.to_numeric(
        frame.get("profit_loss", pd.Series(dtype=float)), errors="coerce"
    ).dropna()
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    data = {
        "trade_count": int(len(pnl)),
        "win_rate": float(len(wins) / len(pnl)) if len(pnl) else 0.0,
        "expectancy": float(pnl.mean()) if len(pnl) else 0.0,
        "profit_factor": float(wins.sum() / abs(losses.sum()))
        if abs(losses.sum()) > 0
        else 0.0,
        "avg_win": float(wins.mean()) if len(wins) else 0.0,
        "avg_loss": float(losses.mean()) if len(losses) else 0.0,
    }
    return analytics_tool_result(
        "calculate_trade_metrics",
        data=data,
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def get_ordered_closed_trades(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _get_ordered_closed_trades_impl."""
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

        res = _get_ordered_closed_trades_impl(**kwargs)
        logger.info("Executed get_ordered_closed_trades tool successfully.")

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
            "get_ordered_closed_trades",
            data={"get_ordered_closed_trades": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def win_rate_fraction(values, epsilon: float = EPSILON) -> dict[str, Any]:
    """AI Tool wrapper for _win_rate_fraction_impl."""
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

        arg_epsilon = epsilon
        if "epsilon" in ["trades", "open_trades"] and isinstance(
            arg_epsilon, (list, dict)
        ):
            arg_epsilon = pd.DataFrame(arg_epsilon)
        elif "epsilon" in [
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
        ] and isinstance(arg_epsilon, list):
            arg_epsilon = pd.Series(arg_epsilon)
        kwargs["epsilon"] = arg_epsilon

        res = _win_rate_fraction_impl(**kwargs)
        logger.info("Executed win_rate_fraction tool successfully.")

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
            "win_rate_fraction", data={"win_rate_fraction": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def avg_win_loss(values, epsilon: float = EPSILON) -> dict[str, Any]:
    """AI Tool wrapper for _avg_win_loss_impl."""
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

        arg_epsilon = epsilon
        if "epsilon" in ["trades", "open_trades"] and isinstance(
            arg_epsilon, (list, dict)
        ):
            arg_epsilon = pd.DataFrame(arg_epsilon)
        elif "epsilon" in [
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
        ] and isinstance(arg_epsilon, list):
            arg_epsilon = pd.Series(arg_epsilon)
        kwargs["epsilon"] = arg_epsilon

        res = _avg_win_loss_impl(**kwargs)
        logger.info("Executed avg_win_loss tool successfully.")

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
            "avg_win_loss", data={"avg_win_loss": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def consecutive_wins_losses(values, epsilon: float = EPSILON) -> dict[str, Any]:
    """AI Tool wrapper for _consecutive_wins_losses_impl."""
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

        arg_epsilon = epsilon
        if "epsilon" in ["trades", "open_trades"] and isinstance(
            arg_epsilon, (list, dict)
        ):
            arg_epsilon = pd.DataFrame(arg_epsilon)
        elif "epsilon" in [
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
        ] and isinstance(arg_epsilon, list):
            arg_epsilon = pd.Series(arg_epsilon)
        kwargs["epsilon"] = arg_epsilon

        res = _consecutive_wins_losses_impl(**kwargs)
        logger.info("Executed consecutive_wins_losses tool successfully.")

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
            "consecutive_wins_losses", data={"consecutive_wins_losses": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def median_mae_mfe(mae: np.ndarray, mfe: np.ndarray) -> dict[str, Any]:
    """AI Tool wrapper for _median_mae_mfe_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_mae = mae
        if "mae" in ["trades", "open_trades"] and isinstance(arg_mae, (list, dict)):
            arg_mae = pd.DataFrame(arg_mae)
        elif "mae" in [
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
        ] and isinstance(arg_mae, list):
            arg_mae = pd.Series(arg_mae)
        kwargs["mae"] = arg_mae

        arg_mfe = mfe
        if "mfe" in ["trades", "open_trades"] and isinstance(arg_mfe, (list, dict)):
            arg_mfe = pd.DataFrame(arg_mfe)
        elif "mfe" in [
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
        ] and isinstance(arg_mfe, list):
            arg_mfe = pd.Series(arg_mfe)
        kwargs["mfe"] = arg_mfe

        res = _median_mae_mfe_impl(**kwargs)
        logger.info("Executed median_mae_mfe tool successfully.")

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
            "median_mae_mfe", data={"median_mae_mfe": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def get_mae_mfe_r(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _get_mae_mfe_r_impl."""
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

        res = _get_mae_mfe_r_impl(**kwargs)
        logger.info("Executed get_mae_mfe_r tool successfully.")

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
            "get_mae_mfe_r", data={"get_mae_mfe_r": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def t_statistic(values) -> dict[str, Any]:
    """AI Tool wrapper for _t_statistic_impl."""
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

        res = _t_statistic_impl(**kwargs)
        logger.info("Executed t_statistic tool successfully.")

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

        return analytics_tool_result("t_statistic", data={"t_statistic": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def open_position_pnl(open_trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _open_position_pnl_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_open_trades = open_trades
        if "open_trades" in ["trades", "open_trades"] and isinstance(
            arg_open_trades, (list, dict)
        ):
            arg_open_trades = pd.DataFrame(arg_open_trades)
        elif "open_trades" in [
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
        ] and isinstance(arg_open_trades, list):
            arg_open_trades = pd.Series(arg_open_trades)
        kwargs["open_trades"] = arg_open_trades

        res = _open_position_pnl_impl(**kwargs)
        logger.info("Executed open_position_pnl tool successfully.")

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
            "open_position_pnl", data={"open_position_pnl": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def total_trades(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _total_trades_impl."""
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

        res = _total_trades_impl(**kwargs)
        logger.info("Executed total_trades tool successfully.")

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
            "total_trades", data={"total_trades": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def winning_trades(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _winning_trades_impl."""
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

        res = _winning_trades_impl(**kwargs)
        logger.info("Executed winning_trades tool successfully.")

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
            "winning_trades", data={"winning_trades": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def losing_trades(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _losing_trades_impl."""
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

        res = _losing_trades_impl(**kwargs)
        logger.info("Executed losing_trades tool successfully.")

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
            "losing_trades", data={"losing_trades": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def breakeven_trades(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _breakeven_trades_impl."""
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

        res = _breakeven_trades_impl(**kwargs)
        logger.info("Executed breakeven_trades tool successfully.")

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
            "breakeven_trades", data={"breakeven_trades": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def long_trades(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _long_trades_impl."""
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

        res = _long_trades_impl(**kwargs)
        logger.info("Executed long_trades tool successfully.")

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

        return analytics_tool_result("long_trades", data={"long_trades": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def short_trades(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _short_trades_impl."""
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

        res = _short_trades_impl(**kwargs)
        logger.info("Executed short_trades tool successfully.")

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
            "short_trades", data={"short_trades": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def count_open_trades(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _count_open_trades_impl."""
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

        res = _count_open_trades_impl(**kwargs)
        logger.info("Executed count_open_trades tool successfully.")

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
            "count_open_trades", data={"count_open_trades": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def slippage_paid(trades: pd.DataFrame, closed_only: bool = False) -> dict[str, Any]:
    """AI Tool wrapper for _slippage_paid_impl."""
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

        res = _slippage_paid_impl(**kwargs)
        logger.info("Executed slippage_paid tool successfully.")

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
            "slippage_paid", data={"slippage_paid": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def commission_paid(trades: pd.DataFrame, closed_only: bool = False) -> dict[str, Any]:
    """AI Tool wrapper for _commission_paid_impl."""
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

        res = _commission_paid_impl(**kwargs)
        logger.info("Executed commission_paid tool successfully.")

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
            "commission_paid", data={"commission_paid": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def swap_paid(trades: pd.DataFrame, closed_only: bool = False) -> dict[str, Any]:
    """AI Tool wrapper for _swap_paid_impl."""
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

        res = _swap_paid_impl(**kwargs)
        logger.info("Executed swap_paid tool successfully.")

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

        return analytics_tool_result("swap_paid", data={"swap_paid": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def win_rate(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _win_rate_impl."""
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

        res = _win_rate_impl(**kwargs)
        logger.info("Executed win_rate tool successfully.")

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

        return analytics_tool_result("win_rate", data={"win_rate": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def loss_rate(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _loss_rate_impl."""
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

        res = _loss_rate_impl(**kwargs)
        logger.info("Executed loss_rate tool successfully.")

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

        return analytics_tool_result("loss_rate", data={"loss_rate": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def avg_win(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _avg_win_impl."""
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

        res = _avg_win_impl(**kwargs)
        logger.info("Executed avg_win tool successfully.")

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

        return analytics_tool_result("avg_win", data={"avg_win": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def largest_win(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _largest_win_impl."""
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

        res = _largest_win_impl(**kwargs)
        logger.info("Executed largest_win tool successfully.")

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

        return analytics_tool_result("largest_win", data={"largest_win": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def largest_loss(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _largest_loss_impl."""
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

        res = _largest_loss_impl(**kwargs)
        logger.info("Executed largest_loss tool successfully.")

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
            "largest_loss", data={"largest_loss": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def median_win(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _median_win_impl."""
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

        res = _median_win_impl(**kwargs)
        logger.info("Executed median_win tool successfully.")

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

        return analytics_tool_result("median_win", data={"median_win": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def median_loss(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _median_loss_impl."""
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

        res = _median_loss_impl(**kwargs)
        logger.info("Executed median_loss tool successfully.")

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

        return analytics_tool_result("median_loss", data={"median_loss": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def expectancy(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _expectancy_impl."""
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

        res = _expectancy_impl(**kwargs)
        logger.info("Executed expectancy tool successfully.")

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

        return analytics_tool_result("expectancy", data={"expectancy": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def expectancy_r(r_values: pd.Series | np.ndarray) -> dict[str, Any]:
    """AI Tool wrapper for _expectancy_r_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_r_values = r_values
        if "r_values" in ["trades", "open_trades"] and isinstance(
            arg_r_values, (list, dict)
        ):
            arg_r_values = pd.DataFrame(arg_r_values)
        elif "r_values" in [
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
        ] and isinstance(arg_r_values, list):
            arg_r_values = pd.Series(arg_r_values)
        kwargs["r_values"] = arg_r_values

        res = _expectancy_r_impl(**kwargs)
        logger.info("Executed expectancy_r tool successfully.")

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
            "expectancy_r", data={"expectancy_r": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_size_held(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _max_size_held_impl."""
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

        res = _max_size_held_impl(**kwargs)
        logger.info("Executed max_size_held tool successfully.")

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
            "max_size_held", data={"max_size_held": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_net_size_held(
    trades: pd.DataFrame, end_time: pd.Timestamp | None = None
) -> dict[str, Any]:
    """AI Tool wrapper for _max_net_size_held_impl."""
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

        arg_end_time = end_time
        if "end_time" in ["trades", "open_trades"] and isinstance(
            arg_end_time, (list, dict)
        ):
            arg_end_time = pd.DataFrame(arg_end_time)
        elif "end_time" in [
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
        ] and isinstance(arg_end_time, list):
            arg_end_time = pd.Series(arg_end_time)
        kwargs["end_time"] = arg_end_time

        res = _max_net_size_held_impl(**kwargs)
        logger.info("Executed max_net_size_held tool successfully.")

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
            "max_net_size_held", data={"max_net_size_held": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_long_size_held(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _max_long_size_held_impl."""
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

        res = _max_long_size_held_impl(**kwargs)
        logger.info("Executed max_long_size_held tool successfully.")

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
            "max_long_size_held", data={"max_long_size_held": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_short_size_held(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _max_short_size_held_impl."""
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

        res = _max_short_size_held_impl(**kwargs)
        logger.info("Executed max_short_size_held tool successfully.")

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
            "max_short_size_held", data={"max_short_size_held": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def avg_r_multiple(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _avg_r_multiple_impl."""
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

        res = _avg_r_multiple_impl(**kwargs)
        logger.info("Executed avg_r_multiple tool successfully.")

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
            "avg_r_multiple", data={"avg_r_multiple": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def median_r_multiple(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _median_r_multiple_impl."""
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

        res = _median_r_multiple_impl(**kwargs)
        logger.info("Executed median_r_multiple tool successfully.")

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
            "median_r_multiple", data={"median_r_multiple": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def r_multiple_distribution(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _r_multiple_distribution_impl."""
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

        res = _r_multiple_distribution_impl(**kwargs)
        logger.info("Executed r_multiple_distribution tool successfully.")

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
            "r_multiple_distribution", data={"r_multiple_distribution": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def r_expectancy(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _r_expectancy_impl."""
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

        res = _r_expectancy_impl(**kwargs)
        logger.info("Executed r_expectancy tool successfully.")

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
            "r_expectancy", data={"r_expectancy": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_r_multiple(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _max_r_multiple_impl."""
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

        res = _max_r_multiple_impl(**kwargs)
        logger.info("Executed max_r_multiple tool successfully.")

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
            "max_r_multiple", data={"max_r_multiple": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def min_r_multiple(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _min_r_multiple_impl."""
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

        res = _min_r_multiple_impl(**kwargs)
        logger.info("Executed min_r_multiple tool successfully.")

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
            "min_r_multiple", data={"min_r_multiple": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def median_mae_r(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _median_mae_r_impl."""
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

        res = _median_mae_r_impl(**kwargs)
        logger.info("Executed median_mae_r tool successfully.")

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
            "median_mae_r", data={"median_mae_r": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def median_mfe_r(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _median_mfe_r_impl."""
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

        res = _median_mfe_r_impl(**kwargs)
        logger.info("Executed median_mfe_r tool successfully.")

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
            "median_mfe_r", data={"median_mfe_r": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_consecutive_wins(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _max_consecutive_wins_impl."""
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

        res = _max_consecutive_wins_impl(**kwargs)
        logger.info("Executed max_consecutive_wins tool successfully.")

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
            "max_consecutive_wins", data={"max_consecutive_wins": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_consecutive_losses(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _max_consecutive_losses_impl."""
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

        res = _max_consecutive_losses_impl(**kwargs)
        logger.info("Executed max_consecutive_losses tool successfully.")

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
            "max_consecutive_losses", data={"max_consecutive_losses": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def avg_consecutive_wins(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _avg_consecutive_wins_impl."""
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

        res = _avg_consecutive_wins_impl(**kwargs)
        logger.info("Executed avg_consecutive_wins tool successfully.")

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
            "avg_consecutive_wins", data={"avg_consecutive_wins": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def avg_consecutive_losses(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _avg_consecutive_losses_impl."""
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

        res = _avg_consecutive_losses_impl(**kwargs)
        logger.info("Executed avg_consecutive_losses tool successfully.")

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
            "avg_consecutive_losses", data={"avg_consecutive_losses": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def win_loss_streaks(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _win_loss_streaks_impl."""
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

        res = _win_loss_streaks_impl(**kwargs)
        logger.info("Executed win_loss_streaks tool successfully.")

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
            "win_loss_streaks", data={"win_loss_streaks": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def avg_time_in_trade(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _avg_time_in_trade_impl."""
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

        res = _avg_time_in_trade_impl(**kwargs)
        logger.info("Executed avg_time_in_trade tool successfully.")

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
            "avg_time_in_trade", data={"avg_time_in_trade": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def median_time_in_trade(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _median_time_in_trade_impl."""
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

        res = _median_time_in_trade_impl(**kwargs)
        logger.info("Executed median_time_in_trade tool successfully.")

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
            "median_time_in_trade", data={"median_time_in_trade": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_time_in_trade(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _max_time_in_trade_impl."""
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

        res = _max_time_in_trade_impl(**kwargs)
        logger.info("Executed max_time_in_trade tool successfully.")

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
            "max_time_in_trade", data={"max_time_in_trade": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def min_time_in_trade(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _min_time_in_trade_impl."""
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

        res = _min_time_in_trade_impl(**kwargs)
        logger.info("Executed min_time_in_trade tool successfully.")

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
            "min_time_in_trade", data={"min_time_in_trade": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def sqn(trades: pd.DataFrame | pd.Series | np.ndarray) -> dict[str, Any]:
    """AI Tool wrapper for _sqn_impl."""
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

        res = _sqn_impl(**kwargs)
        logger.info("Executed sqn tool successfully.")

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

        return analytics_tool_result("sqn", data={"sqn": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def kelly_criterion(trades: pd.DataFrame | pd.Series | np.ndarray) -> dict[str, Any]:
    """AI Tool wrapper for _kelly_criterion_impl."""
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

        res = _kelly_criterion_impl(**kwargs)
        logger.info("Executed kelly_criterion tool successfully.")

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
            "kelly_criterion", data={"kelly_criterion": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def compute_r_trade_metrics(
    r_values: np.ndarray,
    mae_r: np.ndarray | None = None,
    mfe_r: np.ndarray | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _compute_r_trade_metrics_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_r_values = r_values
        if "r_values" in ["trades", "open_trades"] and isinstance(
            arg_r_values, (list, dict)
        ):
            arg_r_values = pd.DataFrame(arg_r_values)
        elif "r_values" in [
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
        ] and isinstance(arg_r_values, list):
            arg_r_values = pd.Series(arg_r_values)
        kwargs["r_values"] = arg_r_values

        arg_mae_r = mae_r
        if "mae_r" in ["trades", "open_trades"] and isinstance(arg_mae_r, (list, dict)):
            arg_mae_r = pd.DataFrame(arg_mae_r)
        elif "mae_r" in [
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
        ] and isinstance(arg_mae_r, list):
            arg_mae_r = pd.Series(arg_mae_r)
        kwargs["mae_r"] = arg_mae_r

        arg_mfe_r = mfe_r
        if "mfe_r" in ["trades", "open_trades"] and isinstance(arg_mfe_r, (list, dict)):
            arg_mfe_r = pd.DataFrame(arg_mfe_r)
        elif "mfe_r" in [
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
        ] and isinstance(arg_mfe_r, list):
            arg_mfe_r = pd.Series(arg_mfe_r)
        kwargs["mfe_r"] = arg_mfe_r

        res = _compute_r_trade_metrics_impl(**kwargs)
        logger.info("Executed compute_r_trade_metrics tool successfully.")

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
            "compute_r_trade_metrics", data={"compute_r_trade_metrics": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def compute_trade_metrics(
    r_values: np.ndarray,
    mae: np.ndarray | None = None,
    mfe: np.ndarray | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _compute_trade_metrics_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_r_values = r_values
        if "r_values" in ["trades", "open_trades"] and isinstance(
            arg_r_values, (list, dict)
        ):
            arg_r_values = pd.DataFrame(arg_r_values)
        elif "r_values" in [
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
        ] and isinstance(arg_r_values, list):
            arg_r_values = pd.Series(arg_r_values)
        kwargs["r_values"] = arg_r_values

        arg_mae = mae
        if "mae" in ["trades", "open_trades"] and isinstance(arg_mae, (list, dict)):
            arg_mae = pd.DataFrame(arg_mae)
        elif "mae" in [
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
        ] and isinstance(arg_mae, list):
            arg_mae = pd.Series(arg_mae)
        kwargs["mae"] = arg_mae

        arg_mfe = mfe
        if "mfe" in ["trades", "open_trades"] and isinstance(arg_mfe, (list, dict)):
            arg_mfe = pd.DataFrame(arg_mfe)
        elif "mfe" in [
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
        ] and isinstance(arg_mfe, list):
            arg_mfe = pd.Series(arg_mfe)
        kwargs["mfe"] = arg_mfe

        res = _compute_trade_metrics_impl(**kwargs)
        logger.info("Executed compute_trade_metrics tool successfully.")

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
            "compute_trade_metrics", data={"compute_trade_metrics": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def compute_equity_metrics(
    returns_input, periods_per_year: int = 252
) -> dict[str, Any]:
    """AI Tool wrapper for _compute_equity_metrics_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_returns_input = returns_input
        if "returns_input" in ["trades", "open_trades"] and isinstance(
            arg_returns_input, (list, dict)
        ):
            arg_returns_input = pd.DataFrame(arg_returns_input)
        elif "returns_input" in [
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
        ] and isinstance(arg_returns_input, list):
            arg_returns_input = pd.Series(arg_returns_input)
        kwargs["returns_input"] = arg_returns_input

        arg_periods_per_year = periods_per_year
        if "periods_per_year" in ["trades", "open_trades"] and isinstance(
            arg_periods_per_year, (list, dict)
        ):
            arg_periods_per_year = pd.DataFrame(arg_periods_per_year)
        elif "periods_per_year" in [
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
        ] and isinstance(arg_periods_per_year, list):
            arg_periods_per_year = pd.Series(arg_periods_per_year)
        kwargs["periods_per_year"] = arg_periods_per_year

        res = _compute_equity_metrics_impl(**kwargs)
        logger.info("Executed compute_equity_metrics tool successfully.")

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
            "compute_equity_metrics", data={"compute_equity_metrics": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def trade_efficiency(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _trade_efficiency_impl."""
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

        res = _trade_efficiency_impl(**kwargs)
        logger.info("Executed trade_efficiency tool successfully.")

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
            "trade_efficiency", data={"trade_efficiency": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def r_signal_to_noise(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _r_signal_to_noise_impl."""
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

        res = _r_signal_to_noise_impl(**kwargs)
        logger.info("Executed r_signal_to_noise tool successfully.")

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
            "r_signal_to_noise", data={"r_signal_to_noise": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def rolling_expectancy_stability(
    trades: pd.DataFrame, window: int = 50
) -> dict[str, Any]:
    """AI Tool wrapper for _rolling_expectancy_stability_impl."""
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

        arg_window = window
        if "window" in ["trades", "open_trades"] and isinstance(
            arg_window, (list, dict)
        ):
            arg_window = pd.DataFrame(arg_window)
        elif "window" in [
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
        ] and isinstance(arg_window, list):
            arg_window = pd.Series(arg_window)
        kwargs["window"] = arg_window

        res = _rolling_expectancy_stability_impl(**kwargs)
        logger.info("Executed rolling_expectancy_stability tool successfully.")

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
            "rolling_expectancy_stability",
            data={"rolling_expectancy_stability": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def win_after_win_probability(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _win_after_win_probability_impl."""
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

        res = _win_after_win_probability_impl(**kwargs)
        logger.info("Executed win_after_win_probability tool successfully.")

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
            "win_after_win_probability",
            data={"win_after_win_probability": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def runs_test_zscore(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _runs_test_zscore_impl."""
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

        res = _runs_test_zscore_impl(**kwargs)
        logger.info("Executed runs_test_zscore tool successfully.")

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
            "runs_test_zscore", data={"runs_test_zscore": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def trading_period_duration(
    trades: pd.DataFrame,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _trading_period_duration_impl."""
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

        arg_start_time = start_time
        if "start_time" in ["trades", "open_trades"] and isinstance(
            arg_start_time, (list, dict)
        ):
            arg_start_time = pd.DataFrame(arg_start_time)
        elif "start_time" in [
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
        ] and isinstance(arg_start_time, list):
            arg_start_time = pd.Series(arg_start_time)
        kwargs["start_time"] = arg_start_time

        arg_end_time = end_time
        if "end_time" in ["trades", "open_trades"] and isinstance(
            arg_end_time, (list, dict)
        ):
            arg_end_time = pd.DataFrame(arg_end_time)
        elif "end_time" in [
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
        ] and isinstance(arg_end_time, list):
            arg_end_time = pd.Series(arg_end_time)
        kwargs["end_time"] = arg_end_time

        res = _trading_period_duration_impl(**kwargs)
        logger.info("Executed trading_period_duration tool successfully.")

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
            "trading_period_duration", data={"trading_period_duration": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def trade_outcome_entropy(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _trade_outcome_entropy_impl."""
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

        res = _trade_outcome_entropy_impl(**kwargs)
        logger.info("Executed trade_outcome_entropy tool successfully.")

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
            "trade_outcome_entropy", data={"trade_outcome_entropy": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def longest_flat_period_duration(
    trades: pd.DataFrame,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _longest_flat_period_duration_impl."""
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

        arg_start_time = start_time
        if "start_time" in ["trades", "open_trades"] and isinstance(
            arg_start_time, (list, dict)
        ):
            arg_start_time = pd.DataFrame(arg_start_time)
        elif "start_time" in [
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
        ] and isinstance(arg_start_time, list):
            arg_start_time = pd.Series(arg_start_time)
        kwargs["start_time"] = arg_start_time

        arg_end_time = end_time
        if "end_time" in ["trades", "open_trades"] and isinstance(
            arg_end_time, (list, dict)
        ):
            arg_end_time = pd.DataFrame(arg_end_time)
        elif "end_time" in [
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
        ] and isinstance(arg_end_time, list):
            arg_end_time = pd.Series(arg_end_time)
        kwargs["end_time"] = arg_end_time

        res = _longest_flat_period_duration_impl(**kwargs)
        logger.info("Executed longest_flat_period_duration tool successfully.")

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
            "longest_flat_period_duration",
            data={"longest_flat_period_duration": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def calculate_trade_metrics(
    *,
    trades: list[dict[str, Any]],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_trade_metrics_impl."""
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

        arg_request_id = request_id
        if "request_id" in ["trades", "open_trades"] and isinstance(
            arg_request_id, (list, dict)
        ):
            arg_request_id = pd.DataFrame(arg_request_id)
        elif "request_id" in [
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
        ] and isinstance(arg_request_id, list):
            arg_request_id = pd.Series(arg_request_id)
        kwargs["request_id"] = arg_request_id

        arg_agent_name = agent_name
        if "agent_name" in ["trades", "open_trades"] and isinstance(
            arg_agent_name, (list, dict)
        ):
            arg_agent_name = pd.DataFrame(arg_agent_name)
        elif "agent_name" in [
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
        ] and isinstance(arg_agent_name, list):
            arg_agent_name = pd.Series(arg_agent_name)
        kwargs["agent_name"] = arg_agent_name

        arg_environment = environment
        if "environment" in ["trades", "open_trades"] and isinstance(
            arg_environment, (list, dict)
        ):
            arg_environment = pd.DataFrame(arg_environment)
        elif "environment" in [
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
        ] and isinstance(arg_environment, list):
            arg_environment = pd.Series(arg_environment)
        kwargs["environment"] = arg_environment

        arg_dry_run = dry_run
        if "dry_run" in ["trades", "open_trades"] and isinstance(
            arg_dry_run, (list, dict)
        ):
            arg_dry_run = pd.DataFrame(arg_dry_run)
        elif "dry_run" in [
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
        ] and isinstance(arg_dry_run, list):
            arg_dry_run = pd.Series(arg_dry_run)
        kwargs["dry_run"] = arg_dry_run

        res = _calculate_trade_metrics_impl(**kwargs)
        logger.info("Executed calculate_trade_metrics tool successfully.")

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
            "calculate_trade_metrics", data={"calculate_trade_metrics": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}
