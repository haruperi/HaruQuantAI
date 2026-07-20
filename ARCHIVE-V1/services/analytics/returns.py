"""returns.py - Calculate equity curves, realized returns, periodic performance, and growth metrics.

Classes:
    None.

Functions:
    _clean_equity: Helper to ensure equity series is clean, sorted, and datetime-indexed.
    _clean_rets: Normalize numeric series, replace infinities, drop NaNs.
    _equity_curve_kernel: Build a cumulative equity curve from PnL deltas and an initial balance.
    _outlier_mask_kernel: Return a boolean mask that excludes sigma-based PnL outliers.
    _remove_pnl_outliers: Remove trades that are outliers (> sigma * std) based on raw P&L.
    total_return_usd: Total return in currency units from equity curve.
    total_return: Total return as a percentage of initial capital.
    net_profit: Total realized profit/loss from closed trades.
    gross_profit: Sum of all winning trades (> EPSILON).
    gross_loss: Sum of all losing trades (< -EPSILON).
    balance_curve_from_closed_trades: Generate a realized balance curve from closed trades.
    balance_curve: Alias for balance_curve_from_closed_trades.
    equity_curve: Alias for balance_curve_from_closed_trades (common orchestration name).
    returns_series: Calculate percentage returns between equity points.
    log_returns_series: Calculate logarithmic returns.
    daily_returns: Daily percentage returns from equity curve.
    weekly_returns: Weekly percentage returns with forward-filling for flat weeks.
    monthly_returns: Monthly percentage returns (ME) with forward-filling for flat months.
    annual_returns: Annual percentage returns (YE) with forward-filling for flat years.
    cagr: Compound Annual Growth Rate as percentage.
    compound_monthly_growth_rate: Compound Monthly Growth Rate as percentage.
    avg_monthly_return: Arithmetic mean of monthly returns as percentage.
    monthly_return_stddev: Volatility of monthly returns as percentage.
    annualized_return: Geometric annualized return as percentage.
    geometric_mean_return: Calculate geometric mean return as a percentage.
    best_return: Maximum single-period return as percentage.
    worst_return: Minimum single-period return as percentage.
    buy_and_hold_return: Total percentage return of asset if bought and held.
    buy_and_hold_cagr: CAGR of a buy-and-hold position based on price data.
    return_volatility: Standard deviation of returns as a percentage.
    downside_return_volatility: Standard deviation of returns below target as a percentage.
    return_skewness: Population skewness of returns distribution.
    return_kurtosis: Fisher's population excess kurtosis of returns distribution.
    adjusted_gross_profit: Adjusted Gross Profit: (N - sqrt(N)) * AvgWin.
    adjusted_gross_loss: Adjusted Gross Loss: (N + sqrt(N)) * AvgLoss.
    adjusted_net_profit: Difference between adjusted gross profit and adjusted gross loss.
    select_net_profit: Net profit after removing 3-sigma P&L outliers.
    select_gross_profit: Gross profit after removing 3-sigma P&L outliers.
    select_gross_loss: Gross loss after removing 3-sigma P&L outliers.
    return_on_max_strategy_drawdown: Total Return (USD) / Max Strategy Drawdown (USD).
    return_on_max_close_to_close_drawdown: Net Profit / Max Close-to-Close Drawdown.
    return_on_account: Return on required account size.
    return_on_initial_capital: Net profit as a percentage of initial capital.
    max_runup: Max Run-up: maximum gain from a valley to a peak.
    max_runup_date: Date of Max Run-up peak.
    calculate_return_metrics: Calculate cumulative and average returns from an equity curve.
    calculate_period_analysis: Calculate timestamp bucket performance analysis.
    calculate_long_short_split: Calculate long versus short profit split.
    calculate_session_performance: Calculate session performance from supplied timestamp records.
"""

from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, skew

from . import drawdowns
from .common import EPSILON, _has_col, analytics_tool_result, get_closed_trades

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
    """Helper to ensure equity series is clean, sorted, and datetime-indexed."""
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


def _clean_rets(rets: pd.Series) -> pd.Series:
    """Normalize numeric series, replace infinities, drop NaNs."""
    if rets is None or len(rets) == 0:
        return pd.Series(dtype=float)
    s = pd.to_numeric(rets, errors="coerce")
    return s.replace([np.inf, -np.inf], np.nan).dropna().astype(float)


@njit(cache=True)
def _equity_curve_kernel(pnl_arr, initial_balance):
    """Build a cumulative equity curve from PnL deltas and an initial balance."""
    n = len(pnl_arr)
    out = np.empty(n + 1, dtype=np.float64)
    out[0] = initial_balance
    curr = initial_balance
    for i in range(n):
        curr += pnl_arr[i]
        out[i + 1] = curr
    return out


@njit(cache=True)
def _outlier_mask_kernel(pnl_arr, mean, std, sigma):
    """Return a boolean mask that excludes sigma-based PnL outliers."""
    n = len(pnl_arr)
    mask = np.ones(n, dtype=np.bool_)
    lower = mean - (sigma * std)
    upper = mean + (sigma * std)
    for i in range(n):
        if pnl_arr[i] < lower or pnl_arr[i] > upper:
            mask[i] = False
    return mask


def _remove_pnl_outliers(trades: pd.DataFrame, sigma: float = 3.0) -> pd.DataFrame:
    """Remove trades that are outliers (> sigma * std) based on raw P&L."""
    if len(trades) < 2 or not _has_col(trades, "profit_loss"):
        return trades
    pnl_arr = trades["profit_loss"].values.astype(np.float64)
    mean = np.mean(pnl_arr)
    std = np.std(pnl_arr)
    if std == 0:
        return trades
    mask = _outlier_mask_kernel(pnl_arr, float(mean), float(std), float(sigma))
    return trades[mask]


# =========================================================================
# Basic Profit & Loss
# =========================================================================


def _total_return_usd_impl(equity: pd.Series) -> float:
    """Total return in currency units from equity curve.

    Purpose:
        Total return in currency units from equity curve.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        equity:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    equity = _clean_equity(equity)
    if len(equity) < 2:
        return 0.0
    return float(equity.iloc[-1] - equity.iloc[0])


def _total_return_impl(equity: pd.Series) -> float:
    """Total return as a percentage of initial capital.

    Purpose:
        Total return as a percentage of initial capital.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        equity:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    equity = _clean_equity(equity)
    if len(equity) < 2 or equity.iloc[0] == 0:
        return 0.0
    profit = _total_return_usd_impl(equity)
    initial_capital = float(equity.iloc[0])
    return (profit / initial_capital) * 100.0


def _net_profit_impl(trades: pd.DataFrame, closed_only: bool = True) -> float:
    """Total realized profit/loss from closed trades.

    Purpose:
        Total realized profit/loss from closed trades.
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
        return 0.0
    return float(data["profit_loss"].sum())


def _gross_profit_impl(trades: pd.DataFrame, closed_only: bool = True) -> float:
    """Sum of all winning trades (> EPSILON).

    Purpose:
        Sum of all winning trades (> EPSILON).
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
        return 0.0
    wins = data[data["profit_loss"] > EPSILON]
    return float(wins["profit_loss"].sum())


def _gross_loss_impl(trades: pd.DataFrame, closed_only: bool = True) -> float:
    """Sum of all losing trades (< -EPSILON).

    Purpose:
        Sum of all losing trades (< -EPSILON).
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
        return 0.0
    losses = data[data["profit_loss"] < -EPSILON]
    return float(losses["profit_loss"].sum())


# =========================================================================
# Equity & Returns Generation
# =========================================================================


def _balance_curve_from_closed_trades_impl(
    trades: pd.DataFrame,
    initial_balance: float,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> pd.Series:
    """Generate a realized balance curve from closed trades.

    Purpose:
        Generate a realized balance curve from closed trades.
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
        initial_balance:
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
        idx = []
        vals = []
        if start_time:
            idx.append(start_time)
            vals.append(initial_balance)
        if end_time:
            idx.append(end_time)
            vals.append(initial_balance)
        if not idx:
            return pd.Series([initial_balance], dtype=float)
        return pd.Series(vals, index=pd.DatetimeIndex(idx))

    closed = get_closed_trades(trades)
    if closed.empty:
        idx = [start_time] if start_time else [trades["open_time"].min()]
        if end_time:
            idx.append(end_time)
        return pd.Series([initial_balance] * len(idx), index=pd.DatetimeIndex(idx))

    sorted_trades = closed.sort_values("close_time")
    pnl_arr = sorted_trades["profit_loss"].values.astype(np.float64)
    equity_values = _equity_curve_kernel(pnl_arr, float(initial_balance))

    first_time = start_time if start_time else sorted_trades.iloc[0]["open_time"]
    indices = np.concatenate(
        [np.array([first_time]), sorted_trades["close_time"].values]
    )

    if end_time and end_time > indices[-1]:
        indices = np.concatenate([indices, np.array([end_time])])
        equity_values = np.concatenate([equity_values, np.array([equity_values[-1]])])

    curve = pd.Series(equity_values, index=pd.to_datetime(indices))
    return curve.groupby(level=0).last()


def _balance_curve_impl(
    trades: pd.DataFrame,
    initial_balance: float,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> pd.Series:
    """Alias for balance_curve_from_closed_trades.

    Purpose:
        Alias for balance_curve_from_closed_trades.
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
        initial_balance:
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
    return _balance_curve_from_closed_trades_impl(
        trades=trades,
        initial_balance=initial_balance,
        start_time=start_time,
        end_time=end_time,
    )


def _equity_curve_impl(
    trades: pd.DataFrame,
    initial_balance: float,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> pd.Series:
    """Alias for balance_curve_from_closed_trades (common orchestration name).

    Purpose:
        Alias for balance_curve_from_closed_trades (common orchestration name).
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
        initial_balance:
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
    return _balance_curve_from_closed_trades_impl(
        trades=trades,
        initial_balance=initial_balance,
        start_time=start_time,
        end_time=end_time,
    )


def _returns_series_impl(equity: pd.Series) -> pd.Series:
    """Calculate percentage returns between equity points.

    Purpose:
        Calculate percentage returns between equity points.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        equity:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    equity = _clean_equity(equity)
    if len(equity) < 2:
        return pd.Series(dtype=float)

    rets = equity.pct_change().dropna()
    return rets.replace([np.inf, -np.inf], np.nan).dropna()


def _log_returns_series_impl(equity: pd.Series) -> pd.Series:
    """Calculate logarithmic returns.

    Purpose:
        Calculate logarithmic returns.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        equity:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    equity = _clean_equity(equity)
    if len(equity) < 2:
        return pd.Series(dtype=float)

    equity = equity[equity > 0]
    return np.log(equity / equity.shift(1)).dropna()


# =========================================================================
# Resampled Period Returns
# =========================================================================


def _daily_returns_impl(equity: pd.Series, calendar: str = "D") -> pd.Series:
    """Daily percentage returns from equity curve.

    Purpose:
        Daily percentage returns from equity curve.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        equity:
            Analytics input consumed by this function.
        calendar:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    equity = _clean_equity(equity)
    if len(equity) < 2:
        return pd.Series(dtype=float)

    daily_equity = equity.resample(calendar).last().ffill()
    return daily_equity.pct_change().fillna(0.0)


def _weekly_returns_impl(equity: pd.Series) -> pd.Series:
    """Weekly percentage returns with forward-filling for flat weeks.

    Purpose:
        Weekly percentage returns with forward-filling for flat weeks.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        equity:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    equity = _clean_equity(equity)
    if len(equity) < 2:
        return pd.Series(dtype=float)

    weekly_equity = equity.resample("W").last().ffill()
    return weekly_equity.pct_change().fillna(0.0)


def _monthly_returns_impl(equity: pd.Series) -> pd.Series:
    """Monthly percentage returns (ME) with forward-filling for flat months.

    Purpose:
        Monthly percentage returns (ME) with forward-filling for flat months.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        equity:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    equity = _clean_equity(equity)
    if len(equity) < 2:
        return pd.Series(dtype=float)

    monthly_equity = equity.resample("ME").last().ffill()
    return monthly_equity.pct_change().fillna(0.0)


def _annual_returns_impl(equity: pd.Series) -> pd.Series:
    """Annual percentage returns (YE) with forward-filling for flat years.

    Purpose:
        Annual percentage returns (YE) with forward-filling for flat years.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        equity:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    equity = _clean_equity(equity)
    if len(equity) < 2:
        return pd.Series(dtype=float)

    annual_equity = equity.resample("YE").last().ffill()
    return annual_equity.pct_change().fillna(0.0)


# =========================================================================
# Compounding & Growth Rates
# =========================================================================


def _cagr_impl(equity: pd.Series) -> float:
    """Compound Annual Growth Rate as percentage.

    Purpose:
        Compound Annual Growth Rate as percentage.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        equity:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    equity = _clean_equity(equity)
    if len(equity) < 2:
        return 0.0

    start_val, end_val = equity.iloc[0], equity.iloc[-1]
    if start_val <= 0:
        return 0.0

    years = (equity.index[-1] - equity.index[0]).total_seconds() / (365.25 * 24 * 3600)
    if years == 0:
        return 0.0
    if end_val <= 0:
        return -100.0
    return float(((end_val / start_val) ** (1 / years) - 1) * 100.0)


def _compound_monthly_growth_rate_impl(equity: pd.Series) -> float:
    """Compound Monthly Growth Rate as percentage.

    Purpose:
        Compound Monthly Growth Rate as percentage.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        equity:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    equity = _clean_equity(equity)
    if len(equity) < 2:
        return 0.0

    start_val, end_val = equity.iloc[0], equity.iloc[-1]
    if start_val <= 0:
        return 0.0

    months = (equity.index[-1] - equity.index[0]).total_seconds() / (30.44 * 24 * 3600)
    if months == 0:
        return 0.0
    if end_val <= 0:
        return -100.0
    return float(((end_val / start_val) ** (1 / months) - 1) * 100.0)


def _avg_monthly_return_impl(equity: pd.Series) -> float:
    """Arithmetic mean of monthly returns as percentage.

    Purpose:
        Arithmetic mean of monthly returns as percentage.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        equity:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    m_ret = _monthly_returns_impl(equity)
    return float(m_ret.mean() * 100) if len(m_ret) > 0 else 0.0


def _monthly_return_stddev_impl(equity: pd.Series) -> float:
    """Volatility of monthly returns as percentage.

    Purpose:
        Volatility of monthly returns as percentage.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        equity:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    m_ret = _monthly_returns_impl(equity)
    return float(m_ret.std() * 100) if len(m_ret) >= 2 else 0.0


def _annualized_return_impl(
    rets: pd.Series,
    periods_per_year: int = 252,
) -> float:
    """Geometric annualized return as percentage.

    Purpose:
        Geometric annualized return as percentage.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        rets:
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
    if len(rets) == 0:
        return 0.0

    rets = rets.replace([np.inf, -np.inf], np.nan).dropna()
    if len(rets) == 0:
        return 0.0

    growth = (1.0 + rets).prod()
    if growth <= 0:
        return -100.0

    return float((growth ** (periods_per_year / len(rets)) - 1.0) * 100.0)


def _geometric_mean_return_impl(rets: pd.Series) -> float:
    """Calculate geometric mean return as a percentage.

    Purpose:
        Calculate geometric mean return as a percentage.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        rets:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    rets = _clean_rets(rets)
    if len(rets) < 1:
        return 0.0

    # (Product(1 + r)) ^ (1/n) - 1
    # Adding a small shift to handle zero/negative returns gracefully if needed,
    # though usually calculated on (1+r).
    g_mean = float(np.prod(1 + rets) ** (1 / len(rets)) - 1)
    return g_mean * 100.0


def _best_return_impl(rets: pd.Series) -> float:
    """Maximum single-period return as percentage.

    Purpose:
        Maximum single-period return as percentage.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        rets:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    s = pd.Series(rets).replace([np.inf, -np.inf], np.nan).dropna()
    return float(s.max() * 100.0) if not s.empty else 0.0


def _worst_return_impl(rets: pd.Series) -> float:
    """Minimum single-period return as percentage.

    Purpose:
        Minimum single-period return as percentage.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        rets:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    s = pd.Series(rets).replace([np.inf, -np.inf], np.nan).dropna()
    return float(s.min() * 100.0) if not s.empty else 0.0


# =========================================================================
# Benchmarking
# =========================================================================


def _buy_and_hold_return_impl(price_data: pd.Series, **kwargs) -> float:
    """Total percentage return of asset if bought and held.

    Purpose:
        Total percentage return of asset if bought and held.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        price_data:
            Analytics input consumed by this function.
        **kwargs:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if price_data is None or len(price_data) < 2 or price_data.iloc[0] == 0:
        return 0.0
    return float(((price_data.iloc[-1] / price_data.iloc[0]) - 1.0) * 100.0)


def _buy_and_hold_cagr_impl(price_data: pd.Series, **kwargs) -> float:
    """CAGR of a buy-and-hold position based on price data.

    Purpose:
        CAGR of a buy-and-hold position based on price data.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        price_data:
            Analytics input consumed by this function.
        **kwargs:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if price_data is None or len(price_data) < 2:
        return 0.0
    return _cagr_impl(price_data)


# =========================================================================
# Return Stability & Moments
# =========================================================================


def _return_volatility_impl(rets: pd.Series) -> float:
    """Standard deviation of returns as a percentage.

    Purpose:
        Standard deviation of returns as a percentage.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        rets:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    vol = float(rets.std()) if len(rets) >= 2 else 0.0
    return vol * 100.0


def _downside_return_volatility_impl(rets: pd.Series, target: float = 0.0) -> float:
    """Standard deviation of returns below target as a percentage.

    Purpose:
        Standard deviation of returns below target as a percentage.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        rets:
            Analytics input consumed by this function.
        target:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    downside = rets[rets < target]
    vol = float(downside.std()) if len(downside) >= 2 else 0.0
    return vol * 100.0


def _return_skewness_impl(rets: pd.Series) -> float:
    """Population skewness of returns distribution.

    Purpose:
        Population skewness of returns distribution.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        rets:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if len(rets) < 3:
        return 0.0
    return float(skew(rets, bias=True))


def _return_kurtosis_impl(rets: pd.Series) -> float:
    """Fisher's population excess kurtosis of returns distribution.

    Purpose:
        Fisher's population excess kurtosis of returns distribution.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        rets:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if len(rets) < 4:
        return 0.0
    return float(kurtosis(rets, bias=True))


# =========================================================================
# Adjusted & Select Metrics
# =========================================================================


def _adjusted_gross_profit_impl(
    trades: pd.DataFrame, closed_only: bool = True
) -> float:
    """Adjusted Gross Profit: (N - sqrt(N)) * AvgWin.

    Purpose:
        Adjusted Gross Profit: (N - sqrt(N)) * AvgWin.
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
        return 0.0

    winners = data[data["profit_loss"] > EPSILON]
    n = len(winners)
    return float((n - np.sqrt(n)) * winners["profit_loss"].mean()) if n > 0 else 0.0


def _adjusted_gross_loss_impl(trades: pd.DataFrame, closed_only: bool = True) -> float:
    """Adjusted Gross Loss: (N + sqrt(N)) * AvgLoss.

    Purpose:
        Adjusted Gross Loss: (N + sqrt(N)) * AvgLoss.
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
        return 0.0

    losers = data[data["profit_loss"] < -EPSILON]
    n = len(losers)
    return float((n + np.sqrt(n)) * losers["profit_loss"].mean()) if n > 0 else 0.0


def _adjusted_net_profit_impl(trades: pd.DataFrame, closed_only: bool = True) -> float:
    """Difference between adjusted gross profit and adjusted gross loss.

    Purpose:
        Difference between adjusted gross profit and adjusted gross loss.
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
    return _adjusted_gross_profit_impl(trades, closed_only) + _adjusted_gross_loss_impl(
        trades, closed_only
    )


def _select_net_profit_impl(trades: pd.DataFrame, closed_only: bool = True) -> float:
    """Net profit after removing 3-sigma P&L outliers.

    Purpose:
        Net profit after removing 3-sigma P&L outliers.
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
        return 0.0
    return float(_remove_pnl_outliers(data, 3.0)["profit_loss"].sum())


def _select_gross_profit_impl(trades: pd.DataFrame, closed_only: bool = True) -> float:
    """Gross profit after removing 3-sigma P&L outliers.

    Purpose:
        Gross profit after removing 3-sigma P&L outliers.
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
        return 0.0
    filtered = _remove_pnl_outliers(data, 3.0)
    return float(filtered[filtered["profit_loss"] > EPSILON]["profit_loss"].sum())


def _select_gross_loss_impl(trades: pd.DataFrame, closed_only: bool = True) -> float:
    """Gross loss after removing 3-sigma P&L outliers.

    Purpose:
        Gross loss after removing 3-sigma P&L outliers.
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
        return 0.0
    filtered = _remove_pnl_outliers(data, 3.0)
    return float(filtered[filtered["profit_loss"] < -EPSILON]["profit_loss"].sum())


# =========================================================================
# Return Ratios & Capital Relations
# =========================================================================


def _return_on_max_strategy_drawdown_impl(equity: pd.Series) -> float:
    """Total Return (USD) / Max Strategy Drawdown (USD).

    Purpose:
        Total Return (USD) / Max Strategy Drawdown (USD).
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        equity:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    dd = drawdowns.__max_strategy_drawdown_impl_impl(equity)
    return _total_return_usd_impl(equity) / dd if dd != 0 else 0.0


def _return_on_max_close_to_close_drawdown_impl(trades: pd.DataFrame) -> float:
    """Net Profit / Max Close-to-Close Drawdown.

    Purpose:
        Net Profit / Max Close-to-Close Drawdown.
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
    dd = drawdowns.__max_close_to_close_drawdown_impl_impl(trades)
    return _net_profit_impl(trades) / dd if dd != 0 else 0.0


def _return_on_account_impl(trades: pd.DataFrame) -> float:
    """Return on required account size.

    Purpose:
        Return on required account size.
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
    return _return_on_max_close_to_close_drawdown_impl(trades)


def _return_on_initial_capital_impl(
    trades: pd.DataFrame, initial_capital: float
) -> float:
    """Net profit as a percentage of initial capital.

    Purpose:
        Net profit as a percentage of initial capital.
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
        initial_capital:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if initial_capital == 0:
        return 0.0
    return float((_net_profit_impl(trades) / initial_capital) * 100.0)


# =========================================================================
# Run-up Metrics (Valley-to-Peak Gain)
# =========================================================================


def _max_runup_impl(equity_curve: pd.Series) -> float:
    """Max Run-up: maximum gain from a valley to a peak.

    Purpose:
        Max Run-up: maximum gain from a valley to a peak.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        equity_curve:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    equity_curve = _clean_equity(equity_curve)
    if len(equity_curve) == 0:
        return 0.0
    running_min = equity_curve.expanding().min()
    runup_series = equity_curve - running_min
    return float(runup_series.max())


def _max_runup_date_impl(equity_curve: pd.Series) -> pd.Timestamp | None:
    """Date of Max Run-up peak.

    Purpose:
        Date of Max Run-up peak.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        equity_curve:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    equity_curve = _clean_equity(equity_curve)
    if len(equity_curve) == 0:
        return None
    running_min = equity_curve.expanding().min()
    runup_series = equity_curve - running_min
    try:
        return runup_series.idxmax()
    except (ValueError, TypeError):
        return None


# =========================================================================
# Agent-Facing Function Tools
# =========================================================================


def _calculate_return_metrics_impl(
    *,
    equity_curve: list[float],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Calculate cumulative and average returns from an equity curve.

    Purpose:
        Calculate cumulative and average returns from an equity curve.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        equity_curve:
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
    equity = pd.to_numeric(pd.Series(equity_curve), errors="coerce").dropna()
    returns_series = equity.pct_change().dropna()
    data = {
        "cumulative_return": float(equity.iloc[-1] / equity.iloc[0] - 1)
        if len(equity) > 1 and equity.iloc[0]
        else 0.0,
        "mean_return": float(returns_series.mean()) if len(returns_series) else 0.0,
    }
    return analytics_tool_result(
        "calculate_return_metrics",
        data=data,
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def _calculate_period_analysis_impl(
    *,
    records: list[dict[str, Any]],
    value_column: str = "return",
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Calculate timestamp bucket performance analysis.

    Purpose:
        Calculate timestamp bucket performance analysis.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        records:
            Analytics input consumed by this function.
        value_column:
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
    frame = pd.DataFrame(records)
    if "timestamp" in frame.columns:
        frame["timestamp"] = pd.to_datetime(frame["timestamp"])
        frame = frame.set_index("timestamp")
    values = pd.to_numeric(
        frame.get(value_column, pd.Series(dtype=float)), errors="coerce"
    )
    data = {
        "hour": values.groupby(frame.index.hour).mean().dropna().to_dict()
        if len(frame)
        else {}
    }
    return analytics_tool_result(
        "calculate_period_analysis",
        data=data,
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def _calculate_long_short_split_impl(
    *,
    trades: list[dict[str, Any]],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Calculate long versus short profit split.

    Purpose:
        Calculate long versus short profit split.
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
    side = frame.get("side", pd.Series(dtype=str)).astype(str).str.lower()
    pnl = pd.to_numeric(
        frame.get("profit_loss", pd.Series(dtype=float)), errors="coerce"
    )
    return analytics_tool_result(
        "calculate_long_short_split",
        data={
            "long": float(pnl[side == "long"].sum()),
            "short": float(pnl[side == "short"].sum()),
        },
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def _calculate_session_performance_impl(
    *,
    records: list[dict[str, Any]],
    value_column: str = "return",
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Calculate session performance from supplied timestamp records.

    Purpose:
        Calculate session performance from supplied timestamp records.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        records:
            Analytics input consumed by this function.
        value_column:
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
    result = _calculate_period_analysis_impl(
        records=records,
        value_column=value_column,
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )
    result["tool_name"] = "calculate_session_performance"
    return result


def _total_return_usd_impl(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _total_return_usd_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _total_return_usd_impl(**kwargs)
        logger.info("Executed total_return_usd tool successfully.")

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
            "total_return_usd", data={"total_return_usd": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _total_return_impl(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _total_return_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _total_return_impl(**kwargs)
        logger.info("Executed total_return tool successfully.")

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
            "total_return", data={"total_return": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _net_profit_impl(trades: pd.DataFrame, closed_only: bool = True) -> dict[str, Any]:
    """AI Tool wrapper for _net_profit_impl."""
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

        res = _net_profit_impl(**kwargs)
        logger.info("Executed net_profit tool successfully.")

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

        return analytics_tool_result("net_profit", data={"net_profit": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _gross_profit_impl(
    trades: pd.DataFrame, closed_only: bool = True
) -> dict[str, Any]:
    """AI Tool wrapper for _gross_profit_impl."""
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

        res = _gross_profit_impl(**kwargs)
        logger.info("Executed gross_profit tool successfully.")

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
            "gross_profit", data={"gross_profit": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _gross_loss_impl(trades: pd.DataFrame, closed_only: bool = True) -> dict[str, Any]:
    """AI Tool wrapper for _gross_loss_impl."""
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

        res = _gross_loss_impl(**kwargs)
        logger.info("Executed gross_loss tool successfully.")

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

        return analytics_tool_result("gross_loss", data={"gross_loss": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _balance_curve_from_closed_trades_impl(
    trades: pd.DataFrame,
    initial_balance: float,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _balance_curve_from_closed_trades_impl."""
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

        res = _balance_curve_from_closed_trades_impl(**kwargs)
        logger.info("Executed balance_curve_from_closed_trades tool successfully.")

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
            "balance_curve_from_closed_trades",
            data={"balance_curve_from_closed_trades": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _balance_curve_impl(
    trades: pd.DataFrame,
    initial_balance: float,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _balance_curve_impl."""
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

        res = _balance_curve_impl(**kwargs)
        logger.info("Executed balance_curve tool successfully.")

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
            "balance_curve", data={"balance_curve": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _equity_curve_impl(
    trades: pd.DataFrame,
    initial_balance: float,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _equity_curve_impl."""
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

        res = _equity_curve_impl(**kwargs)
        logger.info("Executed equity_curve tool successfully.")

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
            "equity_curve", data={"equity_curve": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _returns_series_impl(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _returns_series_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _returns_series_impl(**kwargs)
        logger.info("Executed returns_series tool successfully.")

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
            "returns_series", data={"returns_series": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _log_returns_series_impl(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _log_returns_series_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _log_returns_series_impl(**kwargs)
        logger.info("Executed log_returns_series tool successfully.")

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
            "log_returns_series", data={"log_returns_series": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _daily_returns_impl(equity: pd.Series, calendar: str = "D") -> dict[str, Any]:
    """AI Tool wrapper for _daily_returns_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        arg_calendar = calendar
        if "calendar" in ["trades", "open_trades"] and isinstance(
            arg_calendar, (list, dict)
        ):
            arg_calendar = pd.DataFrame(arg_calendar)
        elif "calendar" in [
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
        ] and isinstance(arg_calendar, list):
            arg_calendar = pd.Series(arg_calendar)
        kwargs["calendar"] = arg_calendar

        res = _daily_returns_impl(**kwargs)
        logger.info("Executed daily_returns tool successfully.")

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
            "daily_returns", data={"daily_returns": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _weekly_returns_impl(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _weekly_returns_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _weekly_returns_impl(**kwargs)
        logger.info("Executed weekly_returns tool successfully.")

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
            "weekly_returns", data={"weekly_returns": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _monthly_returns_impl(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _monthly_returns_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _monthly_returns_impl(**kwargs)
        logger.info("Executed monthly_returns tool successfully.")

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
            "monthly_returns", data={"monthly_returns": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _annual_returns_impl(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _annual_returns_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _annual_returns_impl(**kwargs)
        logger.info("Executed annual_returns tool successfully.")

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
            "annual_returns", data={"annual_returns": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _cagr_impl(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _cagr_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _cagr_impl(**kwargs)
        logger.info("Executed cagr tool successfully.")

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

        return analytics_tool_result("cagr", data={"cagr": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _compound_monthly_growth_rate_impl(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _compound_monthly_growth_rate_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _compound_monthly_growth_rate_impl(**kwargs)
        logger.info("Executed compound_monthly_growth_rate tool successfully.")

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
            "compound_monthly_growth_rate",
            data={"compound_monthly_growth_rate": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _avg_monthly_return_impl(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _avg_monthly_return_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _avg_monthly_return_impl(**kwargs)
        logger.info("Executed avg_monthly_return tool successfully.")

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
            "avg_monthly_return", data={"avg_monthly_return": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _monthly_return_stddev_impl(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _monthly_return_stddev_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _monthly_return_stddev_impl(**kwargs)
        logger.info("Executed monthly_return_stddev tool successfully.")

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
            "monthly_return_stddev", data={"monthly_return_stddev": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _annualized_return_impl(
    rets: pd.Series,
    periods_per_year: int = 252,
) -> dict[str, Any]:
    """AI Tool wrapper for _annualized_return_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_rets = rets
        if "rets" in ["trades", "open_trades"] and isinstance(arg_rets, (list, dict)):
            arg_rets = pd.DataFrame(arg_rets)
        elif "rets" in [
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
        ] and isinstance(arg_rets, list):
            arg_rets = pd.Series(arg_rets)
        kwargs["rets"] = arg_rets

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

        res = _annualized_return_impl(**kwargs)
        logger.info("Executed annualized_return tool successfully.")

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
            "annualized_return", data={"annualized_return": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _geometric_mean_return_impl(rets: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _geometric_mean_return_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_rets = rets
        if "rets" in ["trades", "open_trades"] and isinstance(arg_rets, (list, dict)):
            arg_rets = pd.DataFrame(arg_rets)
        elif "rets" in [
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
        ] and isinstance(arg_rets, list):
            arg_rets = pd.Series(arg_rets)
        kwargs["rets"] = arg_rets

        res = _geometric_mean_return_impl(**kwargs)
        logger.info("Executed geometric_mean_return tool successfully.")

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
            "geometric_mean_return", data={"geometric_mean_return": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _best_return_impl(rets: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _best_return_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_rets = rets
        if "rets" in ["trades", "open_trades"] and isinstance(arg_rets, (list, dict)):
            arg_rets = pd.DataFrame(arg_rets)
        elif "rets" in [
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
        ] and isinstance(arg_rets, list):
            arg_rets = pd.Series(arg_rets)
        kwargs["rets"] = arg_rets

        res = _best_return_impl(**kwargs)
        logger.info("Executed best_return tool successfully.")

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

        return analytics_tool_result("best_return", data={"best_return": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _worst_return_impl(rets: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _worst_return_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_rets = rets
        if "rets" in ["trades", "open_trades"] and isinstance(arg_rets, (list, dict)):
            arg_rets = pd.DataFrame(arg_rets)
        elif "rets" in [
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
        ] and isinstance(arg_rets, list):
            arg_rets = pd.Series(arg_rets)
        kwargs["rets"] = arg_rets

        res = _worst_return_impl(**kwargs)
        logger.info("Executed worst_return tool successfully.")

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
            "worst_return", data={"worst_return": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _buy_and_hold_return_impl(price_data: pd.Series, **kwargs) -> dict[str, Any]:
    """AI Tool wrapper for _buy_and_hold_return_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_price_data = price_data
        if "price_data" in ["trades", "open_trades"] and isinstance(
            arg_price_data, (list, dict)
        ):
            arg_price_data = pd.DataFrame(arg_price_data)
        elif "price_data" in [
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
        ] and isinstance(arg_price_data, list):
            arg_price_data = pd.Series(arg_price_data)
        kwargs["price_data"] = arg_price_data

        arg_kwargs = kwargs
        if "kwargs" in ["trades", "open_trades"] and isinstance(
            arg_kwargs, (list, dict)
        ):
            arg_kwargs = pd.DataFrame(arg_kwargs)
        elif "kwargs" in [
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
        ] and isinstance(arg_kwargs, list):
            arg_kwargs = pd.Series(arg_kwargs)
        kwargs["kwargs"] = arg_kwargs

        res = _buy_and_hold_return_impl(**kwargs)
        logger.info("Executed buy_and_hold_return tool successfully.")

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
            "buy_and_hold_return", data={"buy_and_hold_return": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _buy_and_hold_cagr_impl(price_data: pd.Series, **kwargs) -> dict[str, Any]:
    """AI Tool wrapper for _buy_and_hold_cagr_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_price_data = price_data
        if "price_data" in ["trades", "open_trades"] and isinstance(
            arg_price_data, (list, dict)
        ):
            arg_price_data = pd.DataFrame(arg_price_data)
        elif "price_data" in [
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
        ] and isinstance(arg_price_data, list):
            arg_price_data = pd.Series(arg_price_data)
        kwargs["price_data"] = arg_price_data

        arg_kwargs = kwargs
        if "kwargs" in ["trades", "open_trades"] and isinstance(
            arg_kwargs, (list, dict)
        ):
            arg_kwargs = pd.DataFrame(arg_kwargs)
        elif "kwargs" in [
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
        ] and isinstance(arg_kwargs, list):
            arg_kwargs = pd.Series(arg_kwargs)
        kwargs["kwargs"] = arg_kwargs

        res = _buy_and_hold_cagr_impl(**kwargs)
        logger.info("Executed buy_and_hold_cagr tool successfully.")

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
            "buy_and_hold_cagr", data={"buy_and_hold_cagr": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _return_volatility_impl(rets: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _return_volatility_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_rets = rets
        if "rets" in ["trades", "open_trades"] and isinstance(arg_rets, (list, dict)):
            arg_rets = pd.DataFrame(arg_rets)
        elif "rets" in [
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
        ] and isinstance(arg_rets, list):
            arg_rets = pd.Series(arg_rets)
        kwargs["rets"] = arg_rets

        res = _return_volatility_impl(**kwargs)
        logger.info("Executed return_volatility tool successfully.")

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
            "return_volatility", data={"return_volatility": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _downside_return_volatility_impl(
    rets: pd.Series, target: float = 0.0
) -> dict[str, Any]:
    """AI Tool wrapper for _downside_return_volatility_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_rets = rets
        if "rets" in ["trades", "open_trades"] and isinstance(arg_rets, (list, dict)):
            arg_rets = pd.DataFrame(arg_rets)
        elif "rets" in [
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
        ] and isinstance(arg_rets, list):
            arg_rets = pd.Series(arg_rets)
        kwargs["rets"] = arg_rets

        arg_target = target
        if "target" in ["trades", "open_trades"] and isinstance(
            arg_target, (list, dict)
        ):
            arg_target = pd.DataFrame(arg_target)
        elif "target" in [
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
        ] and isinstance(arg_target, list):
            arg_target = pd.Series(arg_target)
        kwargs["target"] = arg_target

        res = _downside_return_volatility_impl(**kwargs)
        logger.info("Executed downside_return_volatility tool successfully.")

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
            "downside_return_volatility",
            data={"downside_return_volatility": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _return_skewness_impl(rets: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _return_skewness_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_rets = rets
        if "rets" in ["trades", "open_trades"] and isinstance(arg_rets, (list, dict)):
            arg_rets = pd.DataFrame(arg_rets)
        elif "rets" in [
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
        ] and isinstance(arg_rets, list):
            arg_rets = pd.Series(arg_rets)
        kwargs["rets"] = arg_rets

        res = _return_skewness_impl(**kwargs)
        logger.info("Executed return_skewness tool successfully.")

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
            "return_skewness", data={"return_skewness": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _return_kurtosis_impl(rets: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _return_kurtosis_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_rets = rets
        if "rets" in ["trades", "open_trades"] and isinstance(arg_rets, (list, dict)):
            arg_rets = pd.DataFrame(arg_rets)
        elif "rets" in [
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
        ] and isinstance(arg_rets, list):
            arg_rets = pd.Series(arg_rets)
        kwargs["rets"] = arg_rets

        res = _return_kurtosis_impl(**kwargs)
        logger.info("Executed return_kurtosis tool successfully.")

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
            "return_kurtosis", data={"return_kurtosis": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _adjusted_gross_profit_impl(
    trades: pd.DataFrame, closed_only: bool = True
) -> dict[str, Any]:
    """AI Tool wrapper for _adjusted_gross_profit_impl."""
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

        res = _adjusted_gross_profit_impl(**kwargs)
        logger.info("Executed adjusted_gross_profit tool successfully.")

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
            "adjusted_gross_profit", data={"adjusted_gross_profit": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _adjusted_gross_loss_impl(
    trades: pd.DataFrame, closed_only: bool = True
) -> dict[str, Any]:
    """AI Tool wrapper for _adjusted_gross_loss_impl."""
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

        res = _adjusted_gross_loss_impl(**kwargs)
        logger.info("Executed adjusted_gross_loss tool successfully.")

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
            "adjusted_gross_loss", data={"adjusted_gross_loss": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _adjusted_net_profit_impl(
    trades: pd.DataFrame, closed_only: bool = True
) -> dict[str, Any]:
    """AI Tool wrapper for _adjusted_net_profit_impl."""
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

        res = _adjusted_net_profit_impl(**kwargs)
        logger.info("Executed adjusted_net_profit tool successfully.")

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
            "adjusted_net_profit", data={"adjusted_net_profit": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _select_net_profit_impl(
    trades: pd.DataFrame, closed_only: bool = True
) -> dict[str, Any]:
    """AI Tool wrapper for _select_net_profit_impl."""
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

        res = _select_net_profit_impl(**kwargs)
        logger.info("Executed select_net_profit tool successfully.")

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
            "select_net_profit", data={"select_net_profit": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _select_gross_profit_impl(
    trades: pd.DataFrame, closed_only: bool = True
) -> dict[str, Any]:
    """AI Tool wrapper for _select_gross_profit_impl."""
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

        res = _select_gross_profit_impl(**kwargs)
        logger.info("Executed select_gross_profit tool successfully.")

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
            "select_gross_profit", data={"select_gross_profit": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _select_gross_loss_impl(
    trades: pd.DataFrame, closed_only: bool = True
) -> dict[str, Any]:
    """AI Tool wrapper for _select_gross_loss_impl."""
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

        res = _select_gross_loss_impl(**kwargs)
        logger.info("Executed select_gross_loss tool successfully.")

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
            "select_gross_loss", data={"select_gross_loss": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _return_on_max_strategy_drawdown_impl(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _return_on_max_strategy_drawdown_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _return_on_max_strategy_drawdown_impl(**kwargs)
        logger.info("Executed return_on_max_strategy_drawdown tool successfully.")

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
            "return_on_max_strategy_drawdown",
            data={"return_on_max_strategy_drawdown": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _return_on_max_close_to_close_drawdown_impl(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _return_on_max_close_to_close_drawdown_impl."""
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

        res = _return_on_max_close_to_close_drawdown_impl(**kwargs)
        logger.info("Executed return_on_max_close_to_close_drawdown tool successfully.")

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
            "return_on_max_close_to_close_drawdown",
            data={"return_on_max_close_to_close_drawdown": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _return_on_account_impl(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _return_on_account_impl."""
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

        res = _return_on_account_impl(**kwargs)
        logger.info("Executed return_on_account tool successfully.")

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
            "return_on_account", data={"return_on_account": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _return_on_initial_capital_impl(
    trades: pd.DataFrame, initial_capital: float
) -> dict[str, Any]:
    """AI Tool wrapper for _return_on_initial_capital_impl."""
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

        arg_initial_capital = initial_capital
        if "initial_capital" in ["trades", "open_trades"] and isinstance(
            arg_initial_capital, (list, dict)
        ):
            arg_initial_capital = pd.DataFrame(arg_initial_capital)
        elif "initial_capital" in [
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
        ] and isinstance(arg_initial_capital, list):
            arg_initial_capital = pd.Series(arg_initial_capital)
        kwargs["initial_capital"] = arg_initial_capital

        res = _return_on_initial_capital_impl(**kwargs)
        logger.info("Executed return_on_initial_capital tool successfully.")

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
            "return_on_initial_capital",
            data={"return_on_initial_capital": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _max_runup_impl(equity_curve: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _max_runup_impl."""
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

        res = _max_runup_impl(**kwargs)
        logger.info("Executed max_runup tool successfully.")

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

        return analytics_tool_result("max_runup", data={"max_runup": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _max_runup_date_impl(equity_curve: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _max_runup_date_impl."""
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

        res = _max_runup_date_impl(**kwargs)
        logger.info("Executed max_runup_date tool successfully.")

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
            "max_runup_date", data={"max_runup_date": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _calculate_return_metrics_impl(
    *,
    equity_curve: list[float],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_return_metrics_impl."""
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

        res = _calculate_return_metrics_impl(**kwargs)
        logger.info("Executed calculate_return_metrics tool successfully.")

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
            "calculate_return_metrics", data={"calculate_return_metrics": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _calculate_period_analysis_impl(
    *,
    records: list[dict[str, Any]],
    value_column: str = "return",
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_period_analysis_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_records = records
        if "records" in ["trades", "open_trades"] and isinstance(
            arg_records, (list, dict)
        ):
            arg_records = pd.DataFrame(arg_records)
        elif "records" in [
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
        ] and isinstance(arg_records, list):
            arg_records = pd.Series(arg_records)
        kwargs["records"] = arg_records

        arg_value_column = value_column
        if "value_column" in ["trades", "open_trades"] and isinstance(
            arg_value_column, (list, dict)
        ):
            arg_value_column = pd.DataFrame(arg_value_column)
        elif "value_column" in [
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
        ] and isinstance(arg_value_column, list):
            arg_value_column = pd.Series(arg_value_column)
        kwargs["value_column"] = arg_value_column

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

        res = _calculate_period_analysis_impl(**kwargs)
        logger.info("Executed calculate_period_analysis tool successfully.")

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
            "calculate_period_analysis",
            data={"calculate_period_analysis": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _calculate_long_short_split_impl(
    *,
    trades: list[dict[str, Any]],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_long_short_split_impl."""
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

        res = _calculate_long_short_split_impl(**kwargs)
        logger.info("Executed calculate_long_short_split tool successfully.")

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
            "calculate_long_short_split",
            data={"calculate_long_short_split": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _calculate_session_performance_impl(
    *,
    records: list[dict[str, Any]],
    value_column: str = "return",
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_session_performance_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_records = records
        if "records" in ["trades", "open_trades"] and isinstance(
            arg_records, (list, dict)
        ):
            arg_records = pd.DataFrame(arg_records)
        elif "records" in [
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
        ] and isinstance(arg_records, list):
            arg_records = pd.Series(arg_records)
        kwargs["records"] = arg_records

        arg_value_column = value_column
        if "value_column" in ["trades", "open_trades"] and isinstance(
            arg_value_column, (list, dict)
        ):
            arg_value_column = pd.DataFrame(arg_value_column)
        elif "value_column" in [
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
        ] and isinstance(arg_value_column, list):
            arg_value_column = pd.Series(arg_value_column)
        kwargs["value_column"] = arg_value_column

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

        res = _calculate_session_performance_impl(**kwargs)
        logger.info("Executed calculate_session_performance tool successfully.")

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
            "calculate_session_performance",
            data={"calculate_session_performance": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def total_return_usd(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _total_return_usd_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _total_return_usd_impl(**kwargs)
        logger.info("Executed total_return_usd tool successfully.")

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
            "total_return_usd", data={"total_return_usd": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def total_return(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _total_return_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _total_return_impl(**kwargs)
        logger.info("Executed total_return tool successfully.")

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
            "total_return", data={"total_return": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def net_profit(trades: pd.DataFrame, closed_only: bool = True) -> dict[str, Any]:
    """AI Tool wrapper for _net_profit_impl."""
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

        res = _net_profit_impl(**kwargs)
        logger.info("Executed net_profit tool successfully.")

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

        return analytics_tool_result("net_profit", data={"net_profit": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def gross_profit(trades: pd.DataFrame, closed_only: bool = True) -> dict[str, Any]:
    """AI Tool wrapper for _gross_profit_impl."""
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

        res = _gross_profit_impl(**kwargs)
        logger.info("Executed gross_profit tool successfully.")

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
            "gross_profit", data={"gross_profit": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def gross_loss(trades: pd.DataFrame, closed_only: bool = True) -> dict[str, Any]:
    """AI Tool wrapper for _gross_loss_impl."""
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

        res = _gross_loss_impl(**kwargs)
        logger.info("Executed gross_loss tool successfully.")

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

        return analytics_tool_result("gross_loss", data={"gross_loss": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def balance_curve_from_closed_trades(
    trades: pd.DataFrame,
    initial_balance: float,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _balance_curve_from_closed_trades_impl."""
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

        res = _balance_curve_from_closed_trades_impl(**kwargs)
        logger.info("Executed balance_curve_from_closed_trades tool successfully.")

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
            "balance_curve_from_closed_trades",
            data={"balance_curve_from_closed_trades": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def balance_curve(
    trades: pd.DataFrame,
    initial_balance: float,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _balance_curve_impl."""
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

        res = _balance_curve_impl(**kwargs)
        logger.info("Executed balance_curve tool successfully.")

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
            "balance_curve", data={"balance_curve": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def equity_curve(
    trades: pd.DataFrame,
    initial_balance: float,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _equity_curve_impl."""
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

        res = _equity_curve_impl(**kwargs)
        logger.info("Executed equity_curve tool successfully.")

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
            "equity_curve", data={"equity_curve": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def returns_series(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _returns_series_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _returns_series_impl(**kwargs)
        logger.info("Executed returns_series tool successfully.")

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
            "returns_series", data={"returns_series": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def log_returns_series(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _log_returns_series_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _log_returns_series_impl(**kwargs)
        logger.info("Executed log_returns_series tool successfully.")

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
            "log_returns_series", data={"log_returns_series": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def daily_returns(equity: pd.Series, calendar: str = "D") -> dict[str, Any]:
    """AI Tool wrapper for _daily_returns_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        arg_calendar = calendar
        if "calendar" in ["trades", "open_trades"] and isinstance(
            arg_calendar, (list, dict)
        ):
            arg_calendar = pd.DataFrame(arg_calendar)
        elif "calendar" in [
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
        ] and isinstance(arg_calendar, list):
            arg_calendar = pd.Series(arg_calendar)
        kwargs["calendar"] = arg_calendar

        res = _daily_returns_impl(**kwargs)
        logger.info("Executed daily_returns tool successfully.")

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
            "daily_returns", data={"daily_returns": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def weekly_returns(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _weekly_returns_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _weekly_returns_impl(**kwargs)
        logger.info("Executed weekly_returns tool successfully.")

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
            "weekly_returns", data={"weekly_returns": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def monthly_returns(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _monthly_returns_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _monthly_returns_impl(**kwargs)
        logger.info("Executed monthly_returns tool successfully.")

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
            "monthly_returns", data={"monthly_returns": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def annual_returns(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _annual_returns_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _annual_returns_impl(**kwargs)
        logger.info("Executed annual_returns tool successfully.")

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
            "annual_returns", data={"annual_returns": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def cagr(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _cagr_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _cagr_impl(**kwargs)
        logger.info("Executed cagr tool successfully.")

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

        return analytics_tool_result("cagr", data={"cagr": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def compound_monthly_growth_rate(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _compound_monthly_growth_rate_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _compound_monthly_growth_rate_impl(**kwargs)
        logger.info("Executed compound_monthly_growth_rate tool successfully.")

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
            "compound_monthly_growth_rate",
            data={"compound_monthly_growth_rate": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def avg_monthly_return(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _avg_monthly_return_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _avg_monthly_return_impl(**kwargs)
        logger.info("Executed avg_monthly_return tool successfully.")

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
            "avg_monthly_return", data={"avg_monthly_return": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def monthly_return_stddev(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _monthly_return_stddev_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _monthly_return_stddev_impl(**kwargs)
        logger.info("Executed monthly_return_stddev tool successfully.")

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
            "monthly_return_stddev", data={"monthly_return_stddev": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def annualized_return(
    rets: pd.Series,
    periods_per_year: int = 252,
) -> dict[str, Any]:
    """AI Tool wrapper for _annualized_return_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_rets = rets
        if "rets" in ["trades", "open_trades"] and isinstance(arg_rets, (list, dict)):
            arg_rets = pd.DataFrame(arg_rets)
        elif "rets" in [
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
        ] and isinstance(arg_rets, list):
            arg_rets = pd.Series(arg_rets)
        kwargs["rets"] = arg_rets

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

        res = _annualized_return_impl(**kwargs)
        logger.info("Executed annualized_return tool successfully.")

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
            "annualized_return", data={"annualized_return": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def geometric_mean_return(rets: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _geometric_mean_return_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_rets = rets
        if "rets" in ["trades", "open_trades"] and isinstance(arg_rets, (list, dict)):
            arg_rets = pd.DataFrame(arg_rets)
        elif "rets" in [
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
        ] and isinstance(arg_rets, list):
            arg_rets = pd.Series(arg_rets)
        kwargs["rets"] = arg_rets

        res = _geometric_mean_return_impl(**kwargs)
        logger.info("Executed geometric_mean_return tool successfully.")

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
            "geometric_mean_return", data={"geometric_mean_return": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def best_return(rets: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _best_return_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_rets = rets
        if "rets" in ["trades", "open_trades"] and isinstance(arg_rets, (list, dict)):
            arg_rets = pd.DataFrame(arg_rets)
        elif "rets" in [
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
        ] and isinstance(arg_rets, list):
            arg_rets = pd.Series(arg_rets)
        kwargs["rets"] = arg_rets

        res = _best_return_impl(**kwargs)
        logger.info("Executed best_return tool successfully.")

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

        return analytics_tool_result("best_return", data={"best_return": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def worst_return(rets: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _worst_return_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_rets = rets
        if "rets" in ["trades", "open_trades"] and isinstance(arg_rets, (list, dict)):
            arg_rets = pd.DataFrame(arg_rets)
        elif "rets" in [
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
        ] and isinstance(arg_rets, list):
            arg_rets = pd.Series(arg_rets)
        kwargs["rets"] = arg_rets

        res = _worst_return_impl(**kwargs)
        logger.info("Executed worst_return tool successfully.")

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
            "worst_return", data={"worst_return": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def buy_and_hold_return(price_data: pd.Series, **kwargs) -> dict[str, Any]:
    """AI Tool wrapper for _buy_and_hold_return_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_price_data = price_data
        if "price_data" in ["trades", "open_trades"] and isinstance(
            arg_price_data, (list, dict)
        ):
            arg_price_data = pd.DataFrame(arg_price_data)
        elif "price_data" in [
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
        ] and isinstance(arg_price_data, list):
            arg_price_data = pd.Series(arg_price_data)
        kwargs["price_data"] = arg_price_data

        arg_kwargs = kwargs
        if "kwargs" in ["trades", "open_trades"] and isinstance(
            arg_kwargs, (list, dict)
        ):
            arg_kwargs = pd.DataFrame(arg_kwargs)
        elif "kwargs" in [
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
        ] and isinstance(arg_kwargs, list):
            arg_kwargs = pd.Series(arg_kwargs)
        kwargs["kwargs"] = arg_kwargs

        res = _buy_and_hold_return_impl(**kwargs)
        logger.info("Executed buy_and_hold_return tool successfully.")

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
            "buy_and_hold_return", data={"buy_and_hold_return": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def buy_and_hold_cagr(price_data: pd.Series, **kwargs) -> dict[str, Any]:
    """AI Tool wrapper for _buy_and_hold_cagr_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_price_data = price_data
        if "price_data" in ["trades", "open_trades"] and isinstance(
            arg_price_data, (list, dict)
        ):
            arg_price_data = pd.DataFrame(arg_price_data)
        elif "price_data" in [
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
        ] and isinstance(arg_price_data, list):
            arg_price_data = pd.Series(arg_price_data)
        kwargs["price_data"] = arg_price_data

        arg_kwargs = kwargs
        if "kwargs" in ["trades", "open_trades"] and isinstance(
            arg_kwargs, (list, dict)
        ):
            arg_kwargs = pd.DataFrame(arg_kwargs)
        elif "kwargs" in [
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
        ] and isinstance(arg_kwargs, list):
            arg_kwargs = pd.Series(arg_kwargs)
        kwargs["kwargs"] = arg_kwargs

        res = _buy_and_hold_cagr_impl(**kwargs)
        logger.info("Executed buy_and_hold_cagr tool successfully.")

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
            "buy_and_hold_cagr", data={"buy_and_hold_cagr": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def return_volatility(rets: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _return_volatility_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_rets = rets
        if "rets" in ["trades", "open_trades"] and isinstance(arg_rets, (list, dict)):
            arg_rets = pd.DataFrame(arg_rets)
        elif "rets" in [
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
        ] and isinstance(arg_rets, list):
            arg_rets = pd.Series(arg_rets)
        kwargs["rets"] = arg_rets

        res = _return_volatility_impl(**kwargs)
        logger.info("Executed return_volatility tool successfully.")

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
            "return_volatility", data={"return_volatility": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def downside_return_volatility(rets: pd.Series, target: float = 0.0) -> dict[str, Any]:
    """AI Tool wrapper for _downside_return_volatility_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_rets = rets
        if "rets" in ["trades", "open_trades"] and isinstance(arg_rets, (list, dict)):
            arg_rets = pd.DataFrame(arg_rets)
        elif "rets" in [
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
        ] and isinstance(arg_rets, list):
            arg_rets = pd.Series(arg_rets)
        kwargs["rets"] = arg_rets

        arg_target = target
        if "target" in ["trades", "open_trades"] and isinstance(
            arg_target, (list, dict)
        ):
            arg_target = pd.DataFrame(arg_target)
        elif "target" in [
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
        ] and isinstance(arg_target, list):
            arg_target = pd.Series(arg_target)
        kwargs["target"] = arg_target

        res = _downside_return_volatility_impl(**kwargs)
        logger.info("Executed downside_return_volatility tool successfully.")

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
            "downside_return_volatility",
            data={"downside_return_volatility": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def return_skewness(rets: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _return_skewness_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_rets = rets
        if "rets" in ["trades", "open_trades"] and isinstance(arg_rets, (list, dict)):
            arg_rets = pd.DataFrame(arg_rets)
        elif "rets" in [
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
        ] and isinstance(arg_rets, list):
            arg_rets = pd.Series(arg_rets)
        kwargs["rets"] = arg_rets

        res = _return_skewness_impl(**kwargs)
        logger.info("Executed return_skewness tool successfully.")

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
            "return_skewness", data={"return_skewness": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def return_kurtosis(rets: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _return_kurtosis_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_rets = rets
        if "rets" in ["trades", "open_trades"] and isinstance(arg_rets, (list, dict)):
            arg_rets = pd.DataFrame(arg_rets)
        elif "rets" in [
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
        ] and isinstance(arg_rets, list):
            arg_rets = pd.Series(arg_rets)
        kwargs["rets"] = arg_rets

        res = _return_kurtosis_impl(**kwargs)
        logger.info("Executed return_kurtosis tool successfully.")

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
            "return_kurtosis", data={"return_kurtosis": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def adjusted_gross_profit(
    trades: pd.DataFrame, closed_only: bool = True
) -> dict[str, Any]:
    """AI Tool wrapper for _adjusted_gross_profit_impl."""
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

        res = _adjusted_gross_profit_impl(**kwargs)
        logger.info("Executed adjusted_gross_profit tool successfully.")

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
            "adjusted_gross_profit", data={"adjusted_gross_profit": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def adjusted_gross_loss(
    trades: pd.DataFrame, closed_only: bool = True
) -> dict[str, Any]:
    """AI Tool wrapper for _adjusted_gross_loss_impl."""
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

        res = _adjusted_gross_loss_impl(**kwargs)
        logger.info("Executed adjusted_gross_loss tool successfully.")

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
            "adjusted_gross_loss", data={"adjusted_gross_loss": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def adjusted_net_profit(
    trades: pd.DataFrame, closed_only: bool = True
) -> dict[str, Any]:
    """AI Tool wrapper for _adjusted_net_profit_impl."""
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

        res = _adjusted_net_profit_impl(**kwargs)
        logger.info("Executed adjusted_net_profit tool successfully.")

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
            "adjusted_net_profit", data={"adjusted_net_profit": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def select_net_profit(trades: pd.DataFrame, closed_only: bool = True) -> dict[str, Any]:
    """AI Tool wrapper for _select_net_profit_impl."""
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

        res = _select_net_profit_impl(**kwargs)
        logger.info("Executed select_net_profit tool successfully.")

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
            "select_net_profit", data={"select_net_profit": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def select_gross_profit(
    trades: pd.DataFrame, closed_only: bool = True
) -> dict[str, Any]:
    """AI Tool wrapper for _select_gross_profit_impl."""
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

        res = _select_gross_profit_impl(**kwargs)
        logger.info("Executed select_gross_profit tool successfully.")

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
            "select_gross_profit", data={"select_gross_profit": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def select_gross_loss(trades: pd.DataFrame, closed_only: bool = True) -> dict[str, Any]:
    """AI Tool wrapper for _select_gross_loss_impl."""
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

        res = _select_gross_loss_impl(**kwargs)
        logger.info("Executed select_gross_loss tool successfully.")

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
            "select_gross_loss", data={"select_gross_loss": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def return_on_max_strategy_drawdown(equity: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _return_on_max_strategy_drawdown_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_equity = equity
        if "equity" in ["trades", "open_trades"] and isinstance(
            arg_equity, (list, dict)
        ):
            arg_equity = pd.DataFrame(arg_equity)
        elif "equity" in [
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
        ] and isinstance(arg_equity, list):
            arg_equity = pd.Series(arg_equity)
        kwargs["equity"] = arg_equity

        res = _return_on_max_strategy_drawdown_impl(**kwargs)
        logger.info("Executed return_on_max_strategy_drawdown tool successfully.")

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
            "return_on_max_strategy_drawdown",
            data={"return_on_max_strategy_drawdown": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def return_on_max_close_to_close_drawdown(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _return_on_max_close_to_close_drawdown_impl."""
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

        res = _return_on_max_close_to_close_drawdown_impl(**kwargs)
        logger.info("Executed return_on_max_close_to_close_drawdown tool successfully.")

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
            "return_on_max_close_to_close_drawdown",
            data={"return_on_max_close_to_close_drawdown": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def return_on_account(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _return_on_account_impl."""
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

        res = _return_on_account_impl(**kwargs)
        logger.info("Executed return_on_account tool successfully.")

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
            "return_on_account", data={"return_on_account": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def return_on_initial_capital(
    trades: pd.DataFrame, initial_capital: float
) -> dict[str, Any]:
    """AI Tool wrapper for _return_on_initial_capital_impl."""
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

        arg_initial_capital = initial_capital
        if "initial_capital" in ["trades", "open_trades"] and isinstance(
            arg_initial_capital, (list, dict)
        ):
            arg_initial_capital = pd.DataFrame(arg_initial_capital)
        elif "initial_capital" in [
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
        ] and isinstance(arg_initial_capital, list):
            arg_initial_capital = pd.Series(arg_initial_capital)
        kwargs["initial_capital"] = arg_initial_capital

        res = _return_on_initial_capital_impl(**kwargs)
        logger.info("Executed return_on_initial_capital tool successfully.")

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
            "return_on_initial_capital",
            data={"return_on_initial_capital": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_runup(equity_curve: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _max_runup_impl."""
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

        res = _max_runup_impl(**kwargs)
        logger.info("Executed max_runup tool successfully.")

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

        return analytics_tool_result("max_runup", data={"max_runup": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_runup_date(equity_curve: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _max_runup_date_impl."""
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

        res = _max_runup_date_impl(**kwargs)
        logger.info("Executed max_runup_date tool successfully.")

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
            "max_runup_date", data={"max_runup_date": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def calculate_return_metrics(
    *,
    equity_curve: list[float],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_return_metrics_impl."""
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

        res = _calculate_return_metrics_impl(**kwargs)
        logger.info("Executed calculate_return_metrics tool successfully.")

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
            "calculate_return_metrics", data={"calculate_return_metrics": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def calculate_period_analysis(
    *,
    records: list[dict[str, Any]],
    value_column: str = "return",
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_period_analysis_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_records = records
        if "records" in ["trades", "open_trades"] and isinstance(
            arg_records, (list, dict)
        ):
            arg_records = pd.DataFrame(arg_records)
        elif "records" in [
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
        ] and isinstance(arg_records, list):
            arg_records = pd.Series(arg_records)
        kwargs["records"] = arg_records

        arg_value_column = value_column
        if "value_column" in ["trades", "open_trades"] and isinstance(
            arg_value_column, (list, dict)
        ):
            arg_value_column = pd.DataFrame(arg_value_column)
        elif "value_column" in [
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
        ] and isinstance(arg_value_column, list):
            arg_value_column = pd.Series(arg_value_column)
        kwargs["value_column"] = arg_value_column

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

        res = _calculate_period_analysis_impl(**kwargs)
        logger.info("Executed calculate_period_analysis tool successfully.")

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
            "calculate_period_analysis",
            data={"calculate_period_analysis": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def calculate_long_short_split(
    *,
    trades: list[dict[str, Any]],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_long_short_split_impl."""
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

        res = _calculate_long_short_split_impl(**kwargs)
        logger.info("Executed calculate_long_short_split tool successfully.")

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
            "calculate_long_short_split",
            data={"calculate_long_short_split": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def calculate_session_performance(
    *,
    records: list[dict[str, Any]],
    value_column: str = "return",
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_session_performance_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_records = records
        if "records" in ["trades", "open_trades"] and isinstance(
            arg_records, (list, dict)
        ):
            arg_records = pd.DataFrame(arg_records)
        elif "records" in [
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
        ] and isinstance(arg_records, list):
            arg_records = pd.Series(arg_records)
        kwargs["records"] = arg_records

        arg_value_column = value_column
        if "value_column" in ["trades", "open_trades"] and isinstance(
            arg_value_column, (list, dict)
        ):
            arg_value_column = pd.DataFrame(arg_value_column)
        elif "value_column" in [
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
        ] and isinstance(arg_value_column, list):
            arg_value_column = pd.Series(arg_value_column)
        kwargs["value_column"] = arg_value_column

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

        res = _calculate_session_performance_impl(**kwargs)
        logger.info("Executed calculate_session_performance tool successfully.")

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
            "calculate_session_performance",
            data={"calculate_session_performance": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}
