"""ratios.py - Calculate risk-adjusted return ratios and trade payoff ratios.

Classes:
    None.

Functions:
    _closed_pnl: Helper to get realized P&L series from a trade frame.
    _avg_win: Mean profit of winning trades.
    _avg_loss: Mean loss of losing trades.
    _win_rate: Win rate fraction (0-1).
    _loss_rate: Loss rate fraction (0-1).
    _largest_loss: Maximum loss from a single trade.
    _expectancy_1d: Calculate mean outcome from a trade frame or 1D numeric input.
    win_rate_fraction: Calculate win rate on a 0-1 scale from 1D numeric input.
    _avg_win_loss_1d: Calculate mean winning and losing outcomes from 1D numeric input.
    sharpe_ratio: Sharpe Ratio - excess return per unit of volatility.
    annualized_sharpe_ratio: Annualized Sharpe Ratio from monthly inputs.
    sortino_ratio: Sortino Ratio - excess return per unit of downside volatility.
    calmar_ratio: Calmar Ratio = annualized return percentage / max drawdown percentage.
    information_ratio: Information Ratio - excess return per unit of tracking error.
    fouse_ratio: Fouse Ratio (Fouse DD Index). Formula: rc - rt * dd^2.
    upside_potential_ratio: Upside Potential Ratio - upside potential / downside risk.
    omega_ratio: Omega Ratio - probability-weighted ratio of gains vs losses.
    gain_to_pain_ratio: Gain-to-Pain Ratio - sum of returns / sum of absolute negative returns.
    kappa_ratio: Kappa Ratio - generalization of Sortino using higher moments.
    sterling_ratio: Sterling Ratio. Formula: CAGR / (AvgYearlyMaxDD + 10%).
    rina_index: RINA Index: Select Net Profit / (Average Drawdown * Percent Time in Market).
    profit_factor: Measure profit factor: Gross Profit / |Gross Loss|.
    payoff_ratio: Measure payoff ratio: |Avg Win| / |Avg Loss|.
    edge_ratio: Edge Ratio: (Avg Win / |Avg Loss|) x Win Rate.
    profit_to_mae_ratio: Profit-to-MAE Ratio - measures efficiency of profit capture.
    mfe_to_mae_ratio: MFE-to-MAE Ratio - favorable excursion vs adverse excursion.
    return_over_drawdown: Return-over-Drawdown Ratio - total return / max trade drawdown.
    expectancy_over_std: Expectancy-over-Std Ratio - stability of edge (Expectancy / Standard Deviation).
    net_profit_as_percent_of_largest_loss: (Net Profit / |Largest Loss|) * 100.
    net_profit_as_percent_of_max_trade_drawdown: (Net Profit / Max Trade Drawdown) * 100.
    net_profit_as_percent_of_max_strategy_drawdown: (Net Profit / Max Strategy Drawdown) * 100.
    select_net_profit_as_percent_of_largest_loss: (Select Net Profit / |Largest Loss|) * 100.
    select_net_profit_as_percent_of_max_trade_drawdown: (Select Net Profit / Max Trade Drawdown) * 100.
    select_net_profit_as_percent_of_max_strategy_drawdown: (Select Net Profit / Max Strategy Drawdown) * 100.
    adjusted_net_profit_as_percent_of_largest_loss: (Adjusted Net Profit / |Largest Loss|) * 100.
    adjusted_net_profit_as_percent_of_max_trade_drawdown: (Adjusted Net Profit / Max Trade Drawdown) * 100.
    adjusted_net_profit_as_percent_of_max_strategy_drawdown: (Adjusted Net Profit / Max Strategy Drawdown) * 100.
    adjusted_profit_factor: Adjusted Gross Profit / |Adjusted Gross Loss|.
    select_profit_factor: Select Gross Profit / |Select Gross Loss|.
    expectancy: (Win% x Avg Win) + (Loss% x Avg Loss).
    expectancy_r: Average R-multiple value.
    calculate_ratio_metrics: Calculate Sharpe and Sortino ratios from return values.
"""

from typing import Any

import numpy as np
import pandas as pd

from . import common, drawdowns, returns
from .common import EPSILON, _to_1d_float_array, analytics_tool_result

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


# =========================================================================
# Local Trade Helpers (to avoid circular dependency with metrics.py)
# =========================================================================


def _closed_pnl(trades: pd.DataFrame) -> pd.Series:
    """Helper to get realized P&L series from a trade frame."""
    data = common.__get_closed_trades_impl_impl(trades)
    if data.empty or "profit_loss" not in data.columns:
        return pd.Series(dtype=float)
    return data["profit_loss"].astype(float)


def _avg_win(trades: pd.DataFrame) -> float:
    """Mean profit of winning trades."""
    pnl = _closed_pnl(trades)
    wins = pnl[pnl > EPSILON]
    return float(wins.mean()) if not wins.empty else 0.0


def _avg_loss(trades: pd.DataFrame) -> float:
    """Mean loss of losing trades."""
    pnl = _closed_pnl(trades)
    losses = pnl[pnl < -EPSILON]
    return float(losses.mean()) if not losses.empty else 0.0


def _win_rate(trades: pd.DataFrame) -> float:
    """Win rate fraction (0-1)."""
    pnl = _closed_pnl(trades)
    if pnl.empty:
        return 0.0
    return float((pnl > EPSILON).mean())


def _loss_rate(trades: pd.DataFrame) -> float:
    """Loss rate fraction (0-1)."""
    pnl = _closed_pnl(trades)
    if pnl.empty:
        return 0.0
    return float((pnl < -EPSILON).mean())


def _largest_loss(trades: pd.DataFrame) -> float:
    """Maximum loss from a single trade."""
    pnl = _closed_pnl(trades)
    return float(pnl.min()) if not pnl.empty else 0.0


# =========================================================================
# Utility Helpers
# =========================================================================


def _expectancy_1d(values) -> float:
    """Calculate mean outcome from a trade frame or 1D numeric input."""
    if isinstance(values, pd.DataFrame):
        if len(values) == 0:
            return 0.0
        return float(values["profit_loss"].mean())

    normalized = _to_1d_float_array(values)
    if len(normalized) == 0:
        return float("nan")
    return float(np.mean(normalized))


def _win_rate_fraction_impl(values) -> float:
    """Calculate win rate on a 0-1 scale from 1D numeric input.

    Purpose:
        Calculate win rate on a 0-1 scale from 1D numeric input.
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
    if len(normalized) == 0:
        return float("nan")
    return float(np.mean(normalized > EPSILON))


def _avg_win_loss_1d(values) -> tuple[float, float]:
    """Calculate mean winning and losing outcomes from 1D numeric input."""
    normalized = _to_1d_float_array(values)
    wins = normalized[normalized > EPSILON]
    losses = normalized[normalized < -EPSILON]
    avg_win = float(np.mean(wins)) if len(wins) else float("nan")
    avg_loss = float(np.mean(losses)) if len(losses) else float("nan")
    return avg_win, avg_loss


# =========================================================================
# Classical Risk-Adjusted Ratios
# =========================================================================


def _sharpe_ratio_impl(
    returns_in: pd.Series | np.ndarray,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
    annualize: bool = True,
) -> float:
    """Sharpe Ratio - excess return per unit of volatility.

    Purpose:
        Sharpe Ratio - excess return per unit of volatility.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        returns_in:
            Analytics input consumed by this function.
        risk_free_rate:
            Analytics input consumed by this function.
        periods_per_year:
            Analytics input consumed by this function.
        annualize:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    normalized = _to_1d_float_array(returns_in)

    if len(normalized) < 2:
        return 0.0

    period_rf = risk_free_rate / periods_per_year
    excess_returns = normalized - period_rf

    std_excess = excess_returns.std(ddof=1)
    if std_excess == 0:
        return 0.0

    sharpe = excess_returns.mean() / std_excess

    if annualize:
        sharpe *= np.sqrt(periods_per_year)

    return float(sharpe)


def _annualized_sharpe_ratio_impl(
    monthly_returns: pd.Series, risk_free_rate_monthly: float = 0.0
) -> float:
    """Annualized Sharpe Ratio from monthly inputs.

    Purpose:
        Annualized Sharpe Ratio from monthly inputs.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        monthly_returns:
            Analytics input consumed by this function.
        risk_free_rate_monthly:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    normalized = _to_1d_float_array(monthly_returns)

    if len(normalized) < 2:
        return 0.0

    excess = normalized - risk_free_rate_monthly
    std = excess.std(ddof=1)

    if std == 0:
        return 0.0

    return float((excess.mean() / std) * np.sqrt(12))


def _sortino_ratio_impl(
    returns_in: pd.Series | np.ndarray,
    target_return: float = 0.0,
    periods_per_year: int = 252,
    annualize: bool = True,
) -> float:
    """Sortino Ratio - excess return per unit of downside volatility.

    Purpose:
        Sortino Ratio - excess return per unit of downside volatility.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        returns_in:
            Analytics input consumed by this function.
        target_return:
            Analytics input consumed by this function.
        periods_per_year:
            Analytics input consumed by this function.
        annualize:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    normalized = _to_1d_float_array(returns_in)

    if len(normalized) < 2:
        return 0.0

    excess_returns = normalized - target_return
    mean_excess = excess_returns.mean()

    # Downside risk calculated using the full-period denominator
    downside_diffs = np.minimum(normalized - target_return, 0.0)
    downside_risk = np.sqrt(np.mean(downside_diffs**2))

    if downside_risk == 0:
        return float("inf") if mean_excess > 0 else 0.0

    sortino = mean_excess / downside_risk

    if annualize:
        sortino *= np.sqrt(periods_per_year)

    return float(sortino)


def _calmar_ratio_impl(
    cagr_value: float | pd.Series | np.ndarray,
    max_dd: float | None = None,
    periods_per_year: int = 252,
) -> float:
    """Calmar Ratio = annualized return percentage / max drawdown percentage.

    Purpose:
        Calmar Ratio = annualized return percentage / max drawdown percentage.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        cagr_value:
            Analytics input consumed by this function.
        max_dd:
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
    if max_dd is None and not np.isscalar(cagr_value):
        normalized = _to_1d_float_array(cagr_value)
        if len(normalized) < 2:
            return 0.0

        annual_return_pct = returns.__annualized_return_impl_impl(
            pd.Series(normalized),
            periods_per_year=periods_per_year,
        )
        drawdown_pct = abs(drawdowns.__max_drawdown_impl_impl(normalized)) * 100.0

        if drawdown_pct == 0:
            return float("inf") if annual_return_pct > 0 else 0.0

        return float(annual_return_pct / drawdown_pct)

    if max_dd is None:
        raise ValueError("max_dd is required when cagr_value is scalar")

    if max_dd == 0:
        return float("inf") if cagr_value > 0 else 0.0

    return float(cagr_value / max_dd)


def _information_ratio_impl(
    returns_in: pd.Series,
    benchmark_returns: pd.Series,
    annualize: bool = True,
    periods_per_year: int = 252,
) -> float:
    """Information Ratio - excess return per unit of tracking error.

    Purpose:
        Information Ratio - excess return per unit of tracking error.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        returns_in:
            Analytics input consumed by this function.
        benchmark_returns:
            Analytics input consumed by this function.
        annualize:
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
    if len(returns_in) < 2 or len(benchmark_returns) < 2:
        return 0.0

    aligned_returns = pd.DataFrame(
        {"strategy": returns_in, "benchmark": benchmark_returns}
    ).dropna()

    if len(aligned_returns) < 2:
        return 0.0

    excess_returns = aligned_returns["strategy"] - aligned_returns["benchmark"]
    mean_excess = excess_returns.mean()
    tracking_error = excess_returns.std()

    if tracking_error == 0:
        return 0.0

    ir = mean_excess / tracking_error

    if annualize:
        ir = ir * np.sqrt(periods_per_year)

    return float(ir)


# =========================================================================
# Modern & Specialized Ratios
# =========================================================================


def _fouse_ratio_impl(
    monthly_returns: pd.Series | np.ndarray,
    risk_tolerance: float,
    risk_free_rate_monthly: float = 0.0,
) -> float:
    """Fouse Ratio (Fouse DD Index). Formula: rc - rt * dd^2.

    Purpose:
        Fouse Ratio (Fouse DD Index). Formula: rc - rt * dd^2.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        monthly_returns:
            Analytics input consumed by this function.
        risk_tolerance:
            Analytics input consumed by this function.
        risk_free_rate_monthly:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    normalized = _to_1d_float_array(monthly_returns)
    if len(normalized) == 0:
        return 0.0

    growth_factors = 1 + normalized
    rc = growth_factors.prod() ** (1 / len(normalized)) - 1

    target = risk_free_rate_monthly
    deviations = normalized - target
    downside_deviations = np.minimum(deviations, 0.0)
    dd = np.sqrt(np.mean(downside_deviations**2))

    fouse = rc - (risk_tolerance * (dd**2))
    return float(fouse)


def _upside_potential_ratio_impl(returns_in: pd.Series, target: float = 0.0) -> float:
    """Upside Potential Ratio - upside potential / downside risk.

    Purpose:
        Upside Potential Ratio - upside potential / downside risk.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        returns_in:
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
    normalized = _to_1d_float_array(returns_in)
    if len(normalized) < 2:
        return 0.0

    deviations = normalized - target

    # Downside Risk
    downside_diffs = np.minimum(deviations, 0.0)
    downside_risk = np.sqrt(np.mean(downside_diffs**2))

    # Upside Potential
    upside_potential = np.mean(np.maximum(deviations, 0.0))

    if downside_risk == 0:
        return float("inf") if upside_potential > 0 else 0.0

    return float(upside_potential / downside_risk)


def _omega_ratio_impl(returns_in: pd.Series, threshold: float = 0.0) -> float:
    """Omega Ratio - probability-weighted ratio of gains vs losses.

    Purpose:
        Omega Ratio - probability-weighted ratio of gains vs losses.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        returns_in:
            Analytics input consumed by this function.
        threshold:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    normalized = _to_1d_float_array(returns_in)
    if len(normalized) == 0:
        return 0.0

    gains = np.maximum(normalized - threshold, 0.0)
    losses = np.maximum(threshold - normalized, 0.0)

    sum_gains = np.sum(gains)
    sum_losses = np.sum(losses)

    if sum_losses == 0:
        return float("inf") if sum_gains > 0 else 1.0

    return float(sum_gains / sum_losses)


def _gain_to_pain_ratio_impl(returns_in: pd.Series) -> float:
    """Gain-to-Pain Ratio - sum of returns / sum of absolute negative returns.

    Purpose:
        Gain-to-Pain Ratio - sum of returns / sum of absolute negative returns.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        returns_in:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    normalized = _to_1d_float_array(returns_in)
    if len(normalized) == 0:
        return 0.0

    sum_returns = np.sum(normalized)
    sum_negative = np.abs(np.sum(normalized[normalized < 0]))

    if sum_negative == 0:
        return float("inf") if sum_returns > 0 else 0.0

    return float(sum_returns / sum_negative)


def _kappa_ratio_impl(
    returns_in: pd.Series | np.ndarray, target: float = 0.0, order: int = 3
) -> float:
    """Kappa Ratio - generalization of Sortino using higher moments.

    Purpose:
        Kappa Ratio - generalization of Sortino using higher moments.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        returns_in:
            Analytics input consumed by this function.
        target:
            Analytics input consumed by this function.
        order:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    normalized = _to_1d_float_array(returns_in)
    if len(normalized) < 2:
        return 0.0

    mean_excess = np.mean(normalized - target)

    # Lower Partial Moment (LPM) calculation including all observations
    shortfall = np.maximum(target - normalized, 0.0)
    lpm = np.mean(shortfall**order) ** (1.0 / order)

    if lpm == 0:
        return float("inf") if mean_excess > 0 else 0.0

    return float(mean_excess / lpm)


def _sterling_ratio_impl(cagr_value: float, avg_yearly_max_dd: float) -> float:
    """Sterling Ratio. Formula: CAGR / (AvgYearlyMaxDD + 10%).

    Purpose:
        Sterling Ratio. Formula: CAGR / (AvgYearlyMaxDD + 10%).
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        cagr_value:
            Analytics input consumed by this function.
        avg_yearly_max_dd:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    risk = avg_yearly_max_dd + 10.0
    if risk == 0:
        return 0.0 if cagr_value == 0 else float("inf")
    return float(cagr_value / risk)


def _rina_index_impl(
    select_net_profit: float, avg_drawdown: float, percent_time_in_market: float
) -> float:
    """RINA Index: Select Net Profit / (Average Drawdown * Percent Time in Market).

    Purpose:
        RINA Index: Select Net Profit / (Average Drawdown * Percent Time in Market).
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        select_net_profit:
            Analytics input consumed by this function.
        avg_drawdown:
            Analytics input consumed by this function.
        percent_time_in_market:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if avg_drawdown == 0 or percent_time_in_market == 0:
        return 0.0

    time_factor = percent_time_in_market
    if time_factor > 1.0:
        time_factor = time_factor / 100.0

    denominator = avg_drawdown * time_factor
    if denominator == 0:
        return float("inf") if select_net_profit > 0 else 0.0

    return float(select_net_profit / denominator)


# =========================================================================
# Trade-Based Performance Ratios
# =========================================================================


def _profit_factor_impl(trades: pd.DataFrame | pd.Series | np.ndarray) -> float:
    """Measure profit factor: Gross Profit / |Gross Loss|.

    Purpose:
        Measure profit factor: Gross Profit / |Gross Loss|.
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
    if not isinstance(trades, pd.DataFrame):
        normalized = _to_1d_float_array(trades)
        wins = normalized[normalized > EPSILON].sum()
        gross_l = np.abs(normalized[normalized < -EPSILON].sum())
        if gross_l == 0:
            return float("inf") if wins > EPSILON else 0.0
        return float(wins / gross_l)

    gross_p = returns.__gross_profit_impl_impl(trades)
    gross_l = np.abs(returns.__gross_loss_impl_impl(trades))

    if gross_l == 0:
        return float("inf") if gross_p > EPSILON else 0.0

    return float(gross_p / gross_l)


def _payoff_ratio_impl(trades: pd.DataFrame | pd.Series | np.ndarray) -> float:
    """Measure payoff ratio: |Avg Win| / |Avg Loss|.

    Purpose:
        Measure payoff ratio: |Avg Win| / |Avg Loss|.
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
    if not isinstance(trades, pd.DataFrame):
        avg_win_val, avg_loss_val = _avg_win_loss_1d(trades)
        if np.isnan(avg_loss_val) or avg_loss_val == 0:
            return (
                float("inf") if not np.isnan(avg_win_val) and avg_win_val != 0 else 0.0
            )
        return float(np.abs(avg_win_val / avg_loss_val))

    avg_win_val = _avg_win(trades)
    avg_loss_val = np.abs(_avg_loss(trades))

    if avg_loss_val == 0:
        return float("inf") if avg_win_val > EPSILON else 0.0

    return float(avg_win_val / avg_loss_val)


def _edge_ratio_impl(trades: pd.DataFrame) -> float:
    """Edge Ratio: (Avg Win / |Avg Loss|) x Win Rate.

    Purpose:
        Edge Ratio: (Avg Win / |Avg Loss|) x Win Rate.
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
    payoff = _payoff_ratio_impl(trades)
    win_pct = _win_rate(trades)
    return float(payoff * win_pct)


def _profit_to_mae_ratio_impl(trades: pd.DataFrame) -> float:
    """Profit-to-MAE Ratio - measures efficiency of profit capture.

    Purpose:
        Profit-to-MAE Ratio - measures efficiency of profit capture.
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
    if (
        trades.empty
        or "profit_loss" not in trades.columns
        or "mae_usd" not in trades.columns
    ):
        return 0.0

    data = common.__get_closed_trades_impl_impl(trades)
    if data.empty:
        return 0.0

    pnl = data["profit_loss"].astype(float).values
    mae = np.abs(data["mae_usd"].astype(float).values)

    valid = mae > EPSILON
    if not valid.any():
        return 0.0

    return float((pnl[valid] / mae[valid]).mean())


def _mfe_to_mae_ratio_impl(trades: pd.DataFrame) -> float:
    """MFE-to-MAE Ratio - favorable excursion vs adverse excursion.

    Purpose:
        MFE-to-MAE Ratio - favorable excursion vs adverse excursion.
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
    if (
        trades.empty
        or "mfe_usd" not in trades.columns
        or "mae_usd" not in trades.columns
    ):
        return 0.0

    data = common.__get_closed_trades_impl_impl(trades)
    if data.empty:
        return 0.0

    mfe = np.maximum(data["mfe_usd"].astype(float).values, 0.0)
    mae = np.abs(data["mae_usd"].astype(float).values)

    valid = mae > EPSILON
    if not valid.any():
        return 0.0

    return float((mfe[valid] / mae[valid]).mean())


def _return_over_drawdown_impl(trades: pd.DataFrame) -> float:
    """Return-over-Drawdown Ratio - total return / max trade drawdown.

    Purpose:
        Return-over-Drawdown Ratio - total return / max trade drawdown.
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
        return 0.0

    total_ret = returns.__net_profit_impl_impl(trades)
    max_dd = drawdowns.__max_close_to_close_drawdown_impl_impl(trades)

    if max_dd == 0:
        return float("inf") if total_ret > EPSILON else 0.0

    return float(total_ret / max_dd)


def _expectancy_over_std_impl(trades: pd.DataFrame) -> float:
    """Expectancy-over-Std Ratio - stability of edge (Expectancy / Standard Deviation).

    Purpose:
        Expectancy-over-Std Ratio - stability of edge (Expectancy / Standard Deviation).
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
    data = common.__get_closed_trades_impl_impl(trades)
    if data.empty or "profit_loss" not in data.columns:
        return 0.0

    pnl = data["profit_loss"].astype(float)
    expectancy_val = pnl.mean()
    std_dev = pnl.std()

    if std_dev == 0:
        return 0.0

    return float(expectancy_val / std_dev)


# =========================================================================
# Net Profit Performance Relations
# =========================================================================


def _net_profit_as_percent_of_largest_loss_impl(trades: pd.DataFrame) -> float:
    """(Net Profit / |Largest Loss|) * 100.

    Purpose:
        (Net Profit / |Largest Loss|) * 100.
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
        return 0.0
    net_p = returns.__net_profit_impl_impl(trades)
    largest_l = np.abs(_largest_loss(trades))
    if largest_l == 0:
        return float("inf") if net_p > EPSILON else 0.0
    return float((net_p / largest_l) * 100.0)


def _net_profit_as_percent_of_max_trade_drawdown_impl(trades: pd.DataFrame) -> float:
    """(Net Profit / Max Trade Drawdown) * 100.

    Purpose:
        (Net Profit / Max Trade Drawdown) * 100.
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
        return 0.0
    net_p = returns.__net_profit_impl_impl(trades)
    max_dd = drawdowns.__max_close_to_close_drawdown_impl_impl(trades)
    if max_dd == 0:
        return float("inf") if net_p > EPSILON else 0.0
    return float((net_p / max_dd) * 100.0)


def _net_profit_as_percent_of_max_strategy_drawdown_impl(
    net_profit_val: float, max_strategy_drawdown: float
) -> float:
    """(Net Profit / Max Strategy Drawdown) * 100.

    Purpose:
        (Net Profit / Max Strategy Drawdown) * 100.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        net_profit_val:
            Analytics input consumed by this function.
        max_strategy_drawdown:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if max_strategy_drawdown == 0:
        return float("inf") if net_profit_val > EPSILON else 0.0
    return float((net_profit_val / max_strategy_drawdown) * 100.0)


def _select_net_profit_as_percent_of_largest_loss_impl(trades: pd.DataFrame) -> float:
    """(Select Net Profit / |Largest Loss|) * 100.

    Purpose:
        (Select Net Profit / |Largest Loss|) * 100.
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
        return 0.0
    sel_net = returns.__select_net_profit_impl_impl(trades)
    largest_l = np.abs(_largest_loss(trades))
    if largest_l == 0:
        return float("inf") if sel_net > EPSILON else 0.0
    return float((sel_net / largest_l) * 100.0)


def _select_net_profit_as_percent_of_max_trade_drawdown_impl(
    trades: pd.DataFrame,
) -> float:
    """(Select Net Profit / Max Trade Drawdown) * 100.

    Purpose:
        (Select Net Profit / Max Trade Drawdown) * 100.
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
        return 0.0
    sel_net = returns.__select_net_profit_impl_impl(trades)
    max_dd = drawdowns.__max_close_to_close_drawdown_impl_impl(trades)
    if max_dd == 0:
        return float("inf") if sel_net > EPSILON else 0.0
    return float((sel_net / max_dd) * 100.0)


def _select_net_profit_as_percent_of_max_strategy_drawdown_impl(
    select_net_profit_val: float, max_strategy_drawdown: float
) -> float:
    """(Select Net Profit / Max Strategy Drawdown) * 100.

    Purpose:
        (Select Net Profit / Max Strategy Drawdown) * 100.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        select_net_profit_val:
            Analytics input consumed by this function.
        max_strategy_drawdown:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if max_strategy_drawdown == 0:
        return float("inf") if select_net_profit_val > EPSILON else 0.0
    return float((select_net_profit_val / max_strategy_drawdown) * 100.0)


def _adjusted_net_profit_as_percent_of_largest_loss_impl(trades: pd.DataFrame) -> float:
    """(Adjusted Net Profit / |Largest Loss|) * 100.

    Purpose:
        (Adjusted Net Profit / |Largest Loss|) * 100.
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
        return 0.0
    adj_net = returns.__adjusted_net_profit_impl_impl(trades)
    largest_l = np.abs(_largest_loss(trades))
    if largest_l == 0:
        return float("inf") if adj_net > EPSILON else 0.0
    return float((adj_net / largest_l) * 100.0)


def _adjusted_net_profit_as_percent_of_max_trade_drawdown_impl(
    trades: pd.DataFrame,
) -> float:
    """(Adjusted Net Profit / Max Trade Drawdown) * 100.

    Purpose:
        (Adjusted Net Profit / Max Trade Drawdown) * 100.
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
        return 0.0
    adj_net = returns.__adjusted_net_profit_impl_impl(trades)
    max_dd = drawdowns.__max_close_to_close_drawdown_impl_impl(trades)
    if max_dd == 0:
        return float("inf") if adj_net > EPSILON else 0.0
    return float((adj_net / max_dd) * 100.0)


def _adjusted_net_profit_as_percent_of_max_strategy_drawdown_impl(
    adjusted_net_profit_val: float, max_strategy_drawdown: float
) -> float:
    """(Adjusted Net Profit / Max Strategy Drawdown) * 100.

    Purpose:
        (Adjusted Net Profit / Max Strategy Drawdown) * 100.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        adjusted_net_profit_val:
            Analytics input consumed by this function.
        max_strategy_drawdown:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if max_strategy_drawdown == 0:
        return float("inf") if adjusted_net_profit_val > EPSILON else 0.0
    return float((adjusted_net_profit_val / max_strategy_drawdown) * 100.0)


# =========================================================================
# Advanced Profit Factors
# =========================================================================


def _adjusted_profit_factor_impl(trades: pd.DataFrame) -> float:
    """Adjusted Gross Profit / |Adjusted Gross Loss|.

    Purpose:
        Adjusted Gross Profit / |Adjusted Gross Loss|.
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
    gross_p = returns.__adjusted_gross_profit_impl_impl(trades)
    gross_l = np.abs(returns.__adjusted_gross_loss_impl_impl(trades))
    if gross_l == 0:
        return float("inf") if gross_p > EPSILON else 0.0
    return float(gross_p / gross_l)


def _select_profit_factor_impl(trades: pd.DataFrame) -> float:
    """Select Gross Profit / |Select Gross Loss|.

    Purpose:
        Select Gross Profit / |Select Gross Loss|.
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
    gross_p = returns.__select_gross_profit_impl_impl(trades)
    gross_l = np.abs(returns.__select_gross_loss_impl_impl(trades))
    if gross_l == 0:
        return float("inf") if gross_p > EPSILON else 0.0
    return float(gross_p / gross_l)


# =========================================================================
# Expectancy & Edge
# =========================================================================


def _expectancy_impl(trades: pd.DataFrame | pd.Series | np.ndarray) -> float:
    """(Win% x Avg Win) + (Loss% x Avg Loss).

    Purpose:
        (Win% x Avg Win) + (Loss% x Avg Loss).
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
    if not isinstance(trades, pd.DataFrame):
        return _expectancy_1d(trades)

    win_pct = _win_rate(trades)
    loss_pct = _loss_rate(trades)
    avg_win_val = _avg_win(trades)
    avg_loss_val = _avg_loss(trades)

    return float((win_pct * avg_win_val) + (loss_pct * avg_loss_val))


def _expectancy_r_impl(r_multiples: pd.Series | np.ndarray) -> float:
    """Average R-multiple value.

    Purpose:
        Average R-multiple value.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        r_multiples:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    r = _to_1d_float_array(r_multiples)
    if len(r) == 0:
        return 0.0
    return float(np.mean(r))


# =========================================================================
# Agent-Facing Function Tools
# =========================================================================


def _calculate_ratio_metrics_impl(
    *,
    returns: list[float],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Calculate Sharpe and Sortino ratios from return values.

    Purpose:
        Calculate Sharpe and Sortino ratios from return values.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        returns:
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
    values = pd.to_numeric(pd.Series(returns), errors="coerce").dropna()
    downside = values[values < 0]
    std = values.std()
    downside_std = downside.std()
    data = {
        "sharpe": float(values.mean() / std) if len(values) > 1 and std else 0.0,
        "sortino": float(values.mean() / downside_std)
        if len(downside) > 1 and downside_std
        else 0.0,
    }
    return analytics_tool_result(
        "calculate_ratio_metrics",
        data=data,
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def _win_rate_fraction_impl(values) -> dict[str, Any]:
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


def _sharpe_ratio_impl(
    returns_in: pd.Series | np.ndarray,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
    annualize: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _sharpe_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_returns_in = returns_in
        if "returns_in" in ["trades", "open_trades"] and isinstance(
            arg_returns_in, (list, dict)
        ):
            arg_returns_in = pd.DataFrame(arg_returns_in)
        elif "returns_in" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_returns_in, list):
            arg_returns_in = pd.Series(arg_returns_in)
        kwargs["returns_in"] = arg_returns_in

        arg_risk_free_rate = risk_free_rate
        if "risk_free_rate" in ["trades", "open_trades"] and isinstance(
            arg_risk_free_rate, (list, dict)
        ):
            arg_risk_free_rate = pd.DataFrame(arg_risk_free_rate)
        elif "risk_free_rate" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_risk_free_rate, list):
            arg_risk_free_rate = pd.Series(arg_risk_free_rate)
        kwargs["risk_free_rate"] = arg_risk_free_rate

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

        arg_annualize = annualize
        if "annualize" in ["trades", "open_trades"] and isinstance(
            arg_annualize, (list, dict)
        ):
            arg_annualize = pd.DataFrame(arg_annualize)
        elif "annualize" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_annualize, list):
            arg_annualize = pd.Series(arg_annualize)
        kwargs["annualize"] = arg_annualize

        res = _sharpe_ratio_impl(**kwargs)
        logger.info("Executed sharpe_ratio tool successfully.")

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
            "sharpe_ratio", data={"sharpe_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _annualized_sharpe_ratio_impl(
    monthly_returns: pd.Series, risk_free_rate_monthly: float = 0.0
) -> dict[str, Any]:
    """AI Tool wrapper for _annualized_sharpe_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_monthly_returns = monthly_returns
        if "monthly_returns" in ["trades", "open_trades"] and isinstance(
            arg_monthly_returns, (list, dict)
        ):
            arg_monthly_returns = pd.DataFrame(arg_monthly_returns)
        elif "monthly_returns" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_monthly_returns, list):
            arg_monthly_returns = pd.Series(arg_monthly_returns)
        kwargs["monthly_returns"] = arg_monthly_returns

        arg_risk_free_rate_monthly = risk_free_rate_monthly
        if "risk_free_rate_monthly" in ["trades", "open_trades"] and isinstance(
            arg_risk_free_rate_monthly, (list, dict)
        ):
            arg_risk_free_rate_monthly = pd.DataFrame(arg_risk_free_rate_monthly)
        elif "risk_free_rate_monthly" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_risk_free_rate_monthly, list):
            arg_risk_free_rate_monthly = pd.Series(arg_risk_free_rate_monthly)
        kwargs["risk_free_rate_monthly"] = arg_risk_free_rate_monthly

        res = _annualized_sharpe_ratio_impl(**kwargs)
        logger.info("Executed annualized_sharpe_ratio tool successfully.")

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
            "annualized_sharpe_ratio", data={"annualized_sharpe_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _sortino_ratio_impl(
    returns_in: pd.Series | np.ndarray,
    target_return: float = 0.0,
    periods_per_year: int = 252,
    annualize: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _sortino_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_returns_in = returns_in
        if "returns_in" in ["trades", "open_trades"] and isinstance(
            arg_returns_in, (list, dict)
        ):
            arg_returns_in = pd.DataFrame(arg_returns_in)
        elif "returns_in" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_returns_in, list):
            arg_returns_in = pd.Series(arg_returns_in)
        kwargs["returns_in"] = arg_returns_in

        arg_target_return = target_return
        if "target_return" in ["trades", "open_trades"] and isinstance(
            arg_target_return, (list, dict)
        ):
            arg_target_return = pd.DataFrame(arg_target_return)
        elif "target_return" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_target_return, list):
            arg_target_return = pd.Series(arg_target_return)
        kwargs["target_return"] = arg_target_return

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

        arg_annualize = annualize
        if "annualize" in ["trades", "open_trades"] and isinstance(
            arg_annualize, (list, dict)
        ):
            arg_annualize = pd.DataFrame(arg_annualize)
        elif "annualize" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_annualize, list):
            arg_annualize = pd.Series(arg_annualize)
        kwargs["annualize"] = arg_annualize

        res = _sortino_ratio_impl(**kwargs)
        logger.info("Executed sortino_ratio tool successfully.")

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
            "sortino_ratio", data={"sortino_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _calmar_ratio_impl(
    cagr_value: float | pd.Series | np.ndarray,
    max_dd: float | None = None,
    periods_per_year: int = 252,
) -> dict[str, Any]:
    """AI Tool wrapper for _calmar_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_cagr_value = cagr_value
        if "cagr_value" in ["trades", "open_trades"] and isinstance(
            arg_cagr_value, (list, dict)
        ):
            arg_cagr_value = pd.DataFrame(arg_cagr_value)
        elif "cagr_value" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_cagr_value, list):
            arg_cagr_value = pd.Series(arg_cagr_value)
        kwargs["cagr_value"] = arg_cagr_value

        arg_max_dd = max_dd
        if "max_dd" in ["trades", "open_trades"] and isinstance(
            arg_max_dd, (list, dict)
        ):
            arg_max_dd = pd.DataFrame(arg_max_dd)
        elif "max_dd" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_max_dd, list):
            arg_max_dd = pd.Series(arg_max_dd)
        kwargs["max_dd"] = arg_max_dd

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

        res = _calmar_ratio_impl(**kwargs)
        logger.info("Executed calmar_ratio tool successfully.")

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
            "calmar_ratio", data={"calmar_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _information_ratio_impl(
    returns_in: pd.Series,
    benchmark_returns: pd.Series,
    annualize: bool = True,
    periods_per_year: int = 252,
) -> dict[str, Any]:
    """AI Tool wrapper for _information_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_returns_in = returns_in
        if "returns_in" in ["trades", "open_trades"] and isinstance(
            arg_returns_in, (list, dict)
        ):
            arg_returns_in = pd.DataFrame(arg_returns_in)
        elif "returns_in" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_returns_in, list):
            arg_returns_in = pd.Series(arg_returns_in)
        kwargs["returns_in"] = arg_returns_in

        arg_benchmark_returns = benchmark_returns
        if "benchmark_returns" in ["trades", "open_trades"] and isinstance(
            arg_benchmark_returns, (list, dict)
        ):
            arg_benchmark_returns = pd.DataFrame(arg_benchmark_returns)
        elif "benchmark_returns" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_benchmark_returns, list):
            arg_benchmark_returns = pd.Series(arg_benchmark_returns)
        kwargs["benchmark_returns"] = arg_benchmark_returns

        arg_annualize = annualize
        if "annualize" in ["trades", "open_trades"] and isinstance(
            arg_annualize, (list, dict)
        ):
            arg_annualize = pd.DataFrame(arg_annualize)
        elif "annualize" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_annualize, list):
            arg_annualize = pd.Series(arg_annualize)
        kwargs["annualize"] = arg_annualize

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

        res = _information_ratio_impl(**kwargs)
        logger.info("Executed information_ratio tool successfully.")

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
            "information_ratio", data={"information_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _fouse_ratio_impl(
    monthly_returns: pd.Series | np.ndarray,
    risk_tolerance: float,
    risk_free_rate_monthly: float = 0.0,
) -> dict[str, Any]:
    """AI Tool wrapper for _fouse_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_monthly_returns = monthly_returns
        if "monthly_returns" in ["trades", "open_trades"] and isinstance(
            arg_monthly_returns, (list, dict)
        ):
            arg_monthly_returns = pd.DataFrame(arg_monthly_returns)
        elif "monthly_returns" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_monthly_returns, list):
            arg_monthly_returns = pd.Series(arg_monthly_returns)
        kwargs["monthly_returns"] = arg_monthly_returns

        arg_risk_tolerance = risk_tolerance
        if "risk_tolerance" in ["trades", "open_trades"] and isinstance(
            arg_risk_tolerance, (list, dict)
        ):
            arg_risk_tolerance = pd.DataFrame(arg_risk_tolerance)
        elif "risk_tolerance" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_risk_tolerance, list):
            arg_risk_tolerance = pd.Series(arg_risk_tolerance)
        kwargs["risk_tolerance"] = arg_risk_tolerance

        arg_risk_free_rate_monthly = risk_free_rate_monthly
        if "risk_free_rate_monthly" in ["trades", "open_trades"] and isinstance(
            arg_risk_free_rate_monthly, (list, dict)
        ):
            arg_risk_free_rate_monthly = pd.DataFrame(arg_risk_free_rate_monthly)
        elif "risk_free_rate_monthly" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_risk_free_rate_monthly, list):
            arg_risk_free_rate_monthly = pd.Series(arg_risk_free_rate_monthly)
        kwargs["risk_free_rate_monthly"] = arg_risk_free_rate_monthly

        res = _fouse_ratio_impl(**kwargs)
        logger.info("Executed fouse_ratio tool successfully.")

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

        return analytics_tool_result("fouse_ratio", data={"fouse_ratio": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _upside_potential_ratio_impl(
    returns_in: pd.Series, target: float = 0.0
) -> dict[str, Any]:
    """AI Tool wrapper for _upside_potential_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_returns_in = returns_in
        if "returns_in" in ["trades", "open_trades"] and isinstance(
            arg_returns_in, (list, dict)
        ):
            arg_returns_in = pd.DataFrame(arg_returns_in)
        elif "returns_in" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_returns_in, list):
            arg_returns_in = pd.Series(arg_returns_in)
        kwargs["returns_in"] = arg_returns_in

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

        res = _upside_potential_ratio_impl(**kwargs)
        logger.info("Executed upside_potential_ratio tool successfully.")

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
            "upside_potential_ratio", data={"upside_potential_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _omega_ratio_impl(returns_in: pd.Series, threshold: float = 0.0) -> dict[str, Any]:
    """AI Tool wrapper for _omega_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_returns_in = returns_in
        if "returns_in" in ["trades", "open_trades"] and isinstance(
            arg_returns_in, (list, dict)
        ):
            arg_returns_in = pd.DataFrame(arg_returns_in)
        elif "returns_in" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_returns_in, list):
            arg_returns_in = pd.Series(arg_returns_in)
        kwargs["returns_in"] = arg_returns_in

        arg_threshold = threshold
        if "threshold" in ["trades", "open_trades"] and isinstance(
            arg_threshold, (list, dict)
        ):
            arg_threshold = pd.DataFrame(arg_threshold)
        elif "threshold" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_threshold, list):
            arg_threshold = pd.Series(arg_threshold)
        kwargs["threshold"] = arg_threshold

        res = _omega_ratio_impl(**kwargs)
        logger.info("Executed omega_ratio tool successfully.")

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

        return analytics_tool_result("omega_ratio", data={"omega_ratio": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _gain_to_pain_ratio_impl(returns_in: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _gain_to_pain_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_returns_in = returns_in
        if "returns_in" in ["trades", "open_trades"] and isinstance(
            arg_returns_in, (list, dict)
        ):
            arg_returns_in = pd.DataFrame(arg_returns_in)
        elif "returns_in" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_returns_in, list):
            arg_returns_in = pd.Series(arg_returns_in)
        kwargs["returns_in"] = arg_returns_in

        res = _gain_to_pain_ratio_impl(**kwargs)
        logger.info("Executed gain_to_pain_ratio tool successfully.")

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
            "gain_to_pain_ratio", data={"gain_to_pain_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _kappa_ratio_impl(
    returns_in: pd.Series | np.ndarray, target: float = 0.0, order: int = 3
) -> dict[str, Any]:
    """AI Tool wrapper for _kappa_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_returns_in = returns_in
        if "returns_in" in ["trades", "open_trades"] and isinstance(
            arg_returns_in, (list, dict)
        ):
            arg_returns_in = pd.DataFrame(arg_returns_in)
        elif "returns_in" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_returns_in, list):
            arg_returns_in = pd.Series(arg_returns_in)
        kwargs["returns_in"] = arg_returns_in

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

        arg_order = order
        if "order" in ["trades", "open_trades"] and isinstance(arg_order, (list, dict)):
            arg_order = pd.DataFrame(arg_order)
        elif "order" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_order, list):
            arg_order = pd.Series(arg_order)
        kwargs["order"] = arg_order

        res = _kappa_ratio_impl(**kwargs)
        logger.info("Executed kappa_ratio tool successfully.")

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

        return analytics_tool_result("kappa_ratio", data={"kappa_ratio": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _sterling_ratio_impl(cagr_value: float, avg_yearly_max_dd: float) -> dict[str, Any]:
    """AI Tool wrapper for _sterling_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_cagr_value = cagr_value
        if "cagr_value" in ["trades", "open_trades"] and isinstance(
            arg_cagr_value, (list, dict)
        ):
            arg_cagr_value = pd.DataFrame(arg_cagr_value)
        elif "cagr_value" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_cagr_value, list):
            arg_cagr_value = pd.Series(arg_cagr_value)
        kwargs["cagr_value"] = arg_cagr_value

        arg_avg_yearly_max_dd = avg_yearly_max_dd
        if "avg_yearly_max_dd" in ["trades", "open_trades"] and isinstance(
            arg_avg_yearly_max_dd, (list, dict)
        ):
            arg_avg_yearly_max_dd = pd.DataFrame(arg_avg_yearly_max_dd)
        elif "avg_yearly_max_dd" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_avg_yearly_max_dd, list):
            arg_avg_yearly_max_dd = pd.Series(arg_avg_yearly_max_dd)
        kwargs["avg_yearly_max_dd"] = arg_avg_yearly_max_dd

        res = _sterling_ratio_impl(**kwargs)
        logger.info("Executed sterling_ratio tool successfully.")

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
            "sterling_ratio", data={"sterling_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _rina_index_impl(
    select_net_profit: float, avg_drawdown: float, percent_time_in_market: float
) -> dict[str, Any]:
    """AI Tool wrapper for _rina_index_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_select_net_profit = select_net_profit
        if "select_net_profit" in ["trades", "open_trades"] and isinstance(
            arg_select_net_profit, (list, dict)
        ):
            arg_select_net_profit = pd.DataFrame(arg_select_net_profit)
        elif "select_net_profit" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_select_net_profit, list):
            arg_select_net_profit = pd.Series(arg_select_net_profit)
        kwargs["select_net_profit"] = arg_select_net_profit

        arg_avg_drawdown = avg_drawdown
        if "avg_drawdown" in ["trades", "open_trades"] and isinstance(
            arg_avg_drawdown, (list, dict)
        ):
            arg_avg_drawdown = pd.DataFrame(arg_avg_drawdown)
        elif "avg_drawdown" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_avg_drawdown, list):
            arg_avg_drawdown = pd.Series(arg_avg_drawdown)
        kwargs["avg_drawdown"] = arg_avg_drawdown

        arg_percent_time_in_market = percent_time_in_market
        if "percent_time_in_market" in ["trades", "open_trades"] and isinstance(
            arg_percent_time_in_market, (list, dict)
        ):
            arg_percent_time_in_market = pd.DataFrame(arg_percent_time_in_market)
        elif "percent_time_in_market" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_percent_time_in_market, list):
            arg_percent_time_in_market = pd.Series(arg_percent_time_in_market)
        kwargs["percent_time_in_market"] = arg_percent_time_in_market

        res = _rina_index_impl(**kwargs)
        logger.info("Executed rina_index tool successfully.")

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

        return analytics_tool_result("rina_index", data={"rina_index": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _profit_factor_impl(
    trades: pd.DataFrame | pd.Series | np.ndarray,
) -> dict[str, Any]:
    """AI Tool wrapper for _profit_factor_impl."""
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

        res = _profit_factor_impl(**kwargs)
        logger.info("Executed profit_factor tool successfully.")

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
            "profit_factor", data={"profit_factor": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _payoff_ratio_impl(trades: pd.DataFrame | pd.Series | np.ndarray) -> dict[str, Any]:
    """AI Tool wrapper for _payoff_ratio_impl."""
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

        res = _payoff_ratio_impl(**kwargs)
        logger.info("Executed payoff_ratio tool successfully.")

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
            "payoff_ratio", data={"payoff_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _edge_ratio_impl(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _edge_ratio_impl."""
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

        res = _edge_ratio_impl(**kwargs)
        logger.info("Executed edge_ratio tool successfully.")

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

        return analytics_tool_result("edge_ratio", data={"edge_ratio": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _profit_to_mae_ratio_impl(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _profit_to_mae_ratio_impl."""
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

        res = _profit_to_mae_ratio_impl(**kwargs)
        logger.info("Executed profit_to_mae_ratio tool successfully.")

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
            "profit_to_mae_ratio", data={"profit_to_mae_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _mfe_to_mae_ratio_impl(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _mfe_to_mae_ratio_impl."""
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

        res = _mfe_to_mae_ratio_impl(**kwargs)
        logger.info("Executed mfe_to_mae_ratio tool successfully.")

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
            "mfe_to_mae_ratio", data={"mfe_to_mae_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _return_over_drawdown_impl(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _return_over_drawdown_impl."""
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

        res = _return_over_drawdown_impl(**kwargs)
        logger.info("Executed return_over_drawdown tool successfully.")

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
            "return_over_drawdown", data={"return_over_drawdown": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _expectancy_over_std_impl(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _expectancy_over_std_impl."""
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

        res = _expectancy_over_std_impl(**kwargs)
        logger.info("Executed expectancy_over_std tool successfully.")

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
            "expectancy_over_std", data={"expectancy_over_std": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _net_profit_as_percent_of_largest_loss_impl(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _net_profit_as_percent_of_largest_loss_impl."""
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

        res = _net_profit_as_percent_of_largest_loss_impl(**kwargs)
        logger.info("Executed net_profit_as_percent_of_largest_loss tool successfully.")

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
            "net_profit_as_percent_of_largest_loss",
            data={"net_profit_as_percent_of_largest_loss": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _net_profit_as_percent_of_max_trade_drawdown_impl(
    trades: pd.DataFrame,
) -> dict[str, Any]:
    """AI Tool wrapper for _net_profit_as_percent_of_max_trade_drawdown_impl."""
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

        res = _net_profit_as_percent_of_max_trade_drawdown_impl(**kwargs)
        logger.info(
            "Executed net_profit_as_percent_of_max_trade_drawdown tool successfully."
        )

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
            "net_profit_as_percent_of_max_trade_drawdown",
            data={"net_profit_as_percent_of_max_trade_drawdown": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _net_profit_as_percent_of_max_strategy_drawdown_impl(
    net_profit_val: float, max_strategy_drawdown: float
) -> dict[str, Any]:
    """AI Tool wrapper for _net_profit_as_percent_of_max_strategy_drawdown_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_net_profit_val = net_profit_val
        if "net_profit_val" in ["trades", "open_trades"] and isinstance(
            arg_net_profit_val, (list, dict)
        ):
            arg_net_profit_val = pd.DataFrame(arg_net_profit_val)
        elif "net_profit_val" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_net_profit_val, list):
            arg_net_profit_val = pd.Series(arg_net_profit_val)
        kwargs["net_profit_val"] = arg_net_profit_val

        arg_max_strategy_drawdown = max_strategy_drawdown
        if "max_strategy_drawdown" in ["trades", "open_trades"] and isinstance(
            arg_max_strategy_drawdown, (list, dict)
        ):
            arg_max_strategy_drawdown = pd.DataFrame(arg_max_strategy_drawdown)
        elif "max_strategy_drawdown" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_max_strategy_drawdown, list):
            arg_max_strategy_drawdown = pd.Series(arg_max_strategy_drawdown)
        kwargs["max_strategy_drawdown"] = arg_max_strategy_drawdown

        res = _net_profit_as_percent_of_max_strategy_drawdown_impl(**kwargs)
        logger.info(
            "Executed net_profit_as_percent_of_max_strategy_drawdown tool successfully."
        )

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
            "net_profit_as_percent_of_max_strategy_drawdown",
            data={"net_profit_as_percent_of_max_strategy_drawdown": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _select_net_profit_as_percent_of_largest_loss_impl(
    trades: pd.DataFrame,
) -> dict[str, Any]:
    """AI Tool wrapper for _select_net_profit_as_percent_of_largest_loss_impl."""
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

        res = _select_net_profit_as_percent_of_largest_loss_impl(**kwargs)
        logger.info(
            "Executed select_net_profit_as_percent_of_largest_loss tool successfully."
        )

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
            "select_net_profit_as_percent_of_largest_loss",
            data={"select_net_profit_as_percent_of_largest_loss": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _select_net_profit_as_percent_of_max_trade_drawdown_impl(
    trades: pd.DataFrame,
) -> dict[str, Any]:
    """AI Tool wrapper for _select_net_profit_as_percent_of_max_trade_drawdown_impl."""
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

        res = _select_net_profit_as_percent_of_max_trade_drawdown_impl(**kwargs)
        logger.info(
            "Executed select_net_profit_as_percent_of_max_trade_drawdown tool successfully."
        )

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
            "select_net_profit_as_percent_of_max_trade_drawdown",
            data={"select_net_profit_as_percent_of_max_trade_drawdown": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _select_net_profit_as_percent_of_max_strategy_drawdown_impl(
    select_net_profit_val: float, max_strategy_drawdown: float
) -> dict[str, Any]:
    """AI Tool wrapper for _select_net_profit_as_percent_of_max_strategy_drawdown_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_select_net_profit_val = select_net_profit_val
        if "select_net_profit_val" in ["trades", "open_trades"] and isinstance(
            arg_select_net_profit_val, (list, dict)
        ):
            arg_select_net_profit_val = pd.DataFrame(arg_select_net_profit_val)
        elif "select_net_profit_val" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_select_net_profit_val, list):
            arg_select_net_profit_val = pd.Series(arg_select_net_profit_val)
        kwargs["select_net_profit_val"] = arg_select_net_profit_val

        arg_max_strategy_drawdown = max_strategy_drawdown
        if "max_strategy_drawdown" in ["trades", "open_trades"] and isinstance(
            arg_max_strategy_drawdown, (list, dict)
        ):
            arg_max_strategy_drawdown = pd.DataFrame(arg_max_strategy_drawdown)
        elif "max_strategy_drawdown" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_max_strategy_drawdown, list):
            arg_max_strategy_drawdown = pd.Series(arg_max_strategy_drawdown)
        kwargs["max_strategy_drawdown"] = arg_max_strategy_drawdown

        res = _select_net_profit_as_percent_of_max_strategy_drawdown_impl(**kwargs)
        logger.info(
            "Executed select_net_profit_as_percent_of_max_strategy_drawdown tool successfully."
        )

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
            "select_net_profit_as_percent_of_max_strategy_drawdown",
            data={
                "select_net_profit_as_percent_of_max_strategy_drawdown": data_payload
            },
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _adjusted_net_profit_as_percent_of_largest_loss_impl(
    trades: pd.DataFrame,
) -> dict[str, Any]:
    """AI Tool wrapper for _adjusted_net_profit_as_percent_of_largest_loss_impl."""
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

        res = _adjusted_net_profit_as_percent_of_largest_loss_impl(**kwargs)
        logger.info(
            "Executed adjusted_net_profit_as_percent_of_largest_loss tool successfully."
        )

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
            "adjusted_net_profit_as_percent_of_largest_loss",
            data={"adjusted_net_profit_as_percent_of_largest_loss": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _adjusted_net_profit_as_percent_of_max_trade_drawdown_impl(
    trades: pd.DataFrame,
) -> dict[str, Any]:
    """AI Tool wrapper for _adjusted_net_profit_as_percent_of_max_trade_drawdown_impl."""
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

        res = _adjusted_net_profit_as_percent_of_max_trade_drawdown_impl(**kwargs)
        logger.info(
            "Executed adjusted_net_profit_as_percent_of_max_trade_drawdown tool successfully."
        )

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
            "adjusted_net_profit_as_percent_of_max_trade_drawdown",
            data={"adjusted_net_profit_as_percent_of_max_trade_drawdown": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _adjusted_net_profit_as_percent_of_max_strategy_drawdown_impl(
    adjusted_net_profit_val: float, max_strategy_drawdown: float
) -> dict[str, Any]:
    """AI Tool wrapper for _adjusted_net_profit_as_percent_of_max_strategy_drawdown_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_adjusted_net_profit_val = adjusted_net_profit_val
        if "adjusted_net_profit_val" in ["trades", "open_trades"] and isinstance(
            arg_adjusted_net_profit_val, (list, dict)
        ):
            arg_adjusted_net_profit_val = pd.DataFrame(arg_adjusted_net_profit_val)
        elif "adjusted_net_profit_val" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_adjusted_net_profit_val, list):
            arg_adjusted_net_profit_val = pd.Series(arg_adjusted_net_profit_val)
        kwargs["adjusted_net_profit_val"] = arg_adjusted_net_profit_val

        arg_max_strategy_drawdown = max_strategy_drawdown
        if "max_strategy_drawdown" in ["trades", "open_trades"] and isinstance(
            arg_max_strategy_drawdown, (list, dict)
        ):
            arg_max_strategy_drawdown = pd.DataFrame(arg_max_strategy_drawdown)
        elif "max_strategy_drawdown" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_max_strategy_drawdown, list):
            arg_max_strategy_drawdown = pd.Series(arg_max_strategy_drawdown)
        kwargs["max_strategy_drawdown"] = arg_max_strategy_drawdown

        res = _adjusted_net_profit_as_percent_of_max_strategy_drawdown_impl(**kwargs)
        logger.info(
            "Executed adjusted_net_profit_as_percent_of_max_strategy_drawdown tool successfully."
        )

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
            "adjusted_net_profit_as_percent_of_max_strategy_drawdown",
            data={
                "adjusted_net_profit_as_percent_of_max_strategy_drawdown": data_payload
            },
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _adjusted_profit_factor_impl(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _adjusted_profit_factor_impl."""
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

        res = _adjusted_profit_factor_impl(**kwargs)
        logger.info("Executed adjusted_profit_factor tool successfully.")

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
            "adjusted_profit_factor", data={"adjusted_profit_factor": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _select_profit_factor_impl(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _select_profit_factor_impl."""
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

        res = _select_profit_factor_impl(**kwargs)
        logger.info("Executed select_profit_factor tool successfully.")

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
            "select_profit_factor", data={"select_profit_factor": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _expectancy_impl(trades: pd.DataFrame | pd.Series | np.ndarray) -> dict[str, Any]:
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


def _expectancy_r_impl(r_multiples: pd.Series | np.ndarray) -> dict[str, Any]:
    """AI Tool wrapper for _expectancy_r_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_r_multiples = r_multiples
        if "r_multiples" in ["trades", "open_trades"] and isinstance(
            arg_r_multiples, (list, dict)
        ):
            arg_r_multiples = pd.DataFrame(arg_r_multiples)
        elif "r_multiples" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_r_multiples, list):
            arg_r_multiples = pd.Series(arg_r_multiples)
        kwargs["r_multiples"] = arg_r_multiples

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


def _calculate_ratio_metrics_impl(
    *,
    returns: list[float],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_ratio_metrics_impl."""
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

        res = _calculate_ratio_metrics_impl(**kwargs)
        logger.info("Executed calculate_ratio_metrics tool successfully.")

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
            "calculate_ratio_metrics", data={"calculate_ratio_metrics": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def win_rate_fraction(values) -> dict[str, Any]:
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


def sharpe_ratio(
    returns_in: pd.Series | np.ndarray,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
    annualize: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _sharpe_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_returns_in = returns_in
        if "returns_in" in ["trades", "open_trades"] and isinstance(
            arg_returns_in, (list, dict)
        ):
            arg_returns_in = pd.DataFrame(arg_returns_in)
        elif "returns_in" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_returns_in, list):
            arg_returns_in = pd.Series(arg_returns_in)
        kwargs["returns_in"] = arg_returns_in

        arg_risk_free_rate = risk_free_rate
        if "risk_free_rate" in ["trades", "open_trades"] and isinstance(
            arg_risk_free_rate, (list, dict)
        ):
            arg_risk_free_rate = pd.DataFrame(arg_risk_free_rate)
        elif "risk_free_rate" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_risk_free_rate, list):
            arg_risk_free_rate = pd.Series(arg_risk_free_rate)
        kwargs["risk_free_rate"] = arg_risk_free_rate

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

        arg_annualize = annualize
        if "annualize" in ["trades", "open_trades"] and isinstance(
            arg_annualize, (list, dict)
        ):
            arg_annualize = pd.DataFrame(arg_annualize)
        elif "annualize" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_annualize, list):
            arg_annualize = pd.Series(arg_annualize)
        kwargs["annualize"] = arg_annualize

        res = _sharpe_ratio_impl(**kwargs)
        logger.info("Executed sharpe_ratio tool successfully.")

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
            "sharpe_ratio", data={"sharpe_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def annualized_sharpe_ratio(
    monthly_returns: pd.Series, risk_free_rate_monthly: float = 0.0
) -> dict[str, Any]:
    """AI Tool wrapper for _annualized_sharpe_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_monthly_returns = monthly_returns
        if "monthly_returns" in ["trades", "open_trades"] and isinstance(
            arg_monthly_returns, (list, dict)
        ):
            arg_monthly_returns = pd.DataFrame(arg_monthly_returns)
        elif "monthly_returns" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_monthly_returns, list):
            arg_monthly_returns = pd.Series(arg_monthly_returns)
        kwargs["monthly_returns"] = arg_monthly_returns

        arg_risk_free_rate_monthly = risk_free_rate_monthly
        if "risk_free_rate_monthly" in ["trades", "open_trades"] and isinstance(
            arg_risk_free_rate_monthly, (list, dict)
        ):
            arg_risk_free_rate_monthly = pd.DataFrame(arg_risk_free_rate_monthly)
        elif "risk_free_rate_monthly" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_risk_free_rate_monthly, list):
            arg_risk_free_rate_monthly = pd.Series(arg_risk_free_rate_monthly)
        kwargs["risk_free_rate_monthly"] = arg_risk_free_rate_monthly

        res = _annualized_sharpe_ratio_impl(**kwargs)
        logger.info("Executed annualized_sharpe_ratio tool successfully.")

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
            "annualized_sharpe_ratio", data={"annualized_sharpe_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def sortino_ratio(
    returns_in: pd.Series | np.ndarray,
    target_return: float = 0.0,
    periods_per_year: int = 252,
    annualize: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _sortino_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_returns_in = returns_in
        if "returns_in" in ["trades", "open_trades"] and isinstance(
            arg_returns_in, (list, dict)
        ):
            arg_returns_in = pd.DataFrame(arg_returns_in)
        elif "returns_in" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_returns_in, list):
            arg_returns_in = pd.Series(arg_returns_in)
        kwargs["returns_in"] = arg_returns_in

        arg_target_return = target_return
        if "target_return" in ["trades", "open_trades"] and isinstance(
            arg_target_return, (list, dict)
        ):
            arg_target_return = pd.DataFrame(arg_target_return)
        elif "target_return" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_target_return, list):
            arg_target_return = pd.Series(arg_target_return)
        kwargs["target_return"] = arg_target_return

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

        arg_annualize = annualize
        if "annualize" in ["trades", "open_trades"] and isinstance(
            arg_annualize, (list, dict)
        ):
            arg_annualize = pd.DataFrame(arg_annualize)
        elif "annualize" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_annualize, list):
            arg_annualize = pd.Series(arg_annualize)
        kwargs["annualize"] = arg_annualize

        res = _sortino_ratio_impl(**kwargs)
        logger.info("Executed sortino_ratio tool successfully.")

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
            "sortino_ratio", data={"sortino_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def calmar_ratio(
    cagr_value: float | pd.Series | np.ndarray,
    max_dd: float | None = None,
    periods_per_year: int = 252,
) -> dict[str, Any]:
    """AI Tool wrapper for _calmar_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_cagr_value = cagr_value
        if "cagr_value" in ["trades", "open_trades"] and isinstance(
            arg_cagr_value, (list, dict)
        ):
            arg_cagr_value = pd.DataFrame(arg_cagr_value)
        elif "cagr_value" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_cagr_value, list):
            arg_cagr_value = pd.Series(arg_cagr_value)
        kwargs["cagr_value"] = arg_cagr_value

        arg_max_dd = max_dd
        if "max_dd" in ["trades", "open_trades"] and isinstance(
            arg_max_dd, (list, dict)
        ):
            arg_max_dd = pd.DataFrame(arg_max_dd)
        elif "max_dd" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_max_dd, list):
            arg_max_dd = pd.Series(arg_max_dd)
        kwargs["max_dd"] = arg_max_dd

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

        res = _calmar_ratio_impl(**kwargs)
        logger.info("Executed calmar_ratio tool successfully.")

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
            "calmar_ratio", data={"calmar_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def information_ratio(
    returns_in: pd.Series,
    benchmark_returns: pd.Series,
    annualize: bool = True,
    periods_per_year: int = 252,
) -> dict[str, Any]:
    """AI Tool wrapper for _information_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_returns_in = returns_in
        if "returns_in" in ["trades", "open_trades"] and isinstance(
            arg_returns_in, (list, dict)
        ):
            arg_returns_in = pd.DataFrame(arg_returns_in)
        elif "returns_in" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_returns_in, list):
            arg_returns_in = pd.Series(arg_returns_in)
        kwargs["returns_in"] = arg_returns_in

        arg_benchmark_returns = benchmark_returns
        if "benchmark_returns" in ["trades", "open_trades"] and isinstance(
            arg_benchmark_returns, (list, dict)
        ):
            arg_benchmark_returns = pd.DataFrame(arg_benchmark_returns)
        elif "benchmark_returns" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_benchmark_returns, list):
            arg_benchmark_returns = pd.Series(arg_benchmark_returns)
        kwargs["benchmark_returns"] = arg_benchmark_returns

        arg_annualize = annualize
        if "annualize" in ["trades", "open_trades"] and isinstance(
            arg_annualize, (list, dict)
        ):
            arg_annualize = pd.DataFrame(arg_annualize)
        elif "annualize" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_annualize, list):
            arg_annualize = pd.Series(arg_annualize)
        kwargs["annualize"] = arg_annualize

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

        res = _information_ratio_impl(**kwargs)
        logger.info("Executed information_ratio tool successfully.")

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
            "information_ratio", data={"information_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def fouse_ratio(
    monthly_returns: pd.Series | np.ndarray,
    risk_tolerance: float,
    risk_free_rate_monthly: float = 0.0,
) -> dict[str, Any]:
    """AI Tool wrapper for _fouse_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_monthly_returns = monthly_returns
        if "monthly_returns" in ["trades", "open_trades"] and isinstance(
            arg_monthly_returns, (list, dict)
        ):
            arg_monthly_returns = pd.DataFrame(arg_monthly_returns)
        elif "monthly_returns" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_monthly_returns, list):
            arg_monthly_returns = pd.Series(arg_monthly_returns)
        kwargs["monthly_returns"] = arg_monthly_returns

        arg_risk_tolerance = risk_tolerance
        if "risk_tolerance" in ["trades", "open_trades"] and isinstance(
            arg_risk_tolerance, (list, dict)
        ):
            arg_risk_tolerance = pd.DataFrame(arg_risk_tolerance)
        elif "risk_tolerance" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_risk_tolerance, list):
            arg_risk_tolerance = pd.Series(arg_risk_tolerance)
        kwargs["risk_tolerance"] = arg_risk_tolerance

        arg_risk_free_rate_monthly = risk_free_rate_monthly
        if "risk_free_rate_monthly" in ["trades", "open_trades"] and isinstance(
            arg_risk_free_rate_monthly, (list, dict)
        ):
            arg_risk_free_rate_monthly = pd.DataFrame(arg_risk_free_rate_monthly)
        elif "risk_free_rate_monthly" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_risk_free_rate_monthly, list):
            arg_risk_free_rate_monthly = pd.Series(arg_risk_free_rate_monthly)
        kwargs["risk_free_rate_monthly"] = arg_risk_free_rate_monthly

        res = _fouse_ratio_impl(**kwargs)
        logger.info("Executed fouse_ratio tool successfully.")

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

        return analytics_tool_result("fouse_ratio", data={"fouse_ratio": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def upside_potential_ratio(
    returns_in: pd.Series, target: float = 0.0
) -> dict[str, Any]:
    """AI Tool wrapper for _upside_potential_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_returns_in = returns_in
        if "returns_in" in ["trades", "open_trades"] and isinstance(
            arg_returns_in, (list, dict)
        ):
            arg_returns_in = pd.DataFrame(arg_returns_in)
        elif "returns_in" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_returns_in, list):
            arg_returns_in = pd.Series(arg_returns_in)
        kwargs["returns_in"] = arg_returns_in

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

        res = _upside_potential_ratio_impl(**kwargs)
        logger.info("Executed upside_potential_ratio tool successfully.")

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
            "upside_potential_ratio", data={"upside_potential_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def omega_ratio(returns_in: pd.Series, threshold: float = 0.0) -> dict[str, Any]:
    """AI Tool wrapper for _omega_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_returns_in = returns_in
        if "returns_in" in ["trades", "open_trades"] and isinstance(
            arg_returns_in, (list, dict)
        ):
            arg_returns_in = pd.DataFrame(arg_returns_in)
        elif "returns_in" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_returns_in, list):
            arg_returns_in = pd.Series(arg_returns_in)
        kwargs["returns_in"] = arg_returns_in

        arg_threshold = threshold
        if "threshold" in ["trades", "open_trades"] and isinstance(
            arg_threshold, (list, dict)
        ):
            arg_threshold = pd.DataFrame(arg_threshold)
        elif "threshold" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_threshold, list):
            arg_threshold = pd.Series(arg_threshold)
        kwargs["threshold"] = arg_threshold

        res = _omega_ratio_impl(**kwargs)
        logger.info("Executed omega_ratio tool successfully.")

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

        return analytics_tool_result("omega_ratio", data={"omega_ratio": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def gain_to_pain_ratio(returns_in: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _gain_to_pain_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_returns_in = returns_in
        if "returns_in" in ["trades", "open_trades"] and isinstance(
            arg_returns_in, (list, dict)
        ):
            arg_returns_in = pd.DataFrame(arg_returns_in)
        elif "returns_in" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_returns_in, list):
            arg_returns_in = pd.Series(arg_returns_in)
        kwargs["returns_in"] = arg_returns_in

        res = _gain_to_pain_ratio_impl(**kwargs)
        logger.info("Executed gain_to_pain_ratio tool successfully.")

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
            "gain_to_pain_ratio", data={"gain_to_pain_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def kappa_ratio(
    returns_in: pd.Series | np.ndarray, target: float = 0.0, order: int = 3
) -> dict[str, Any]:
    """AI Tool wrapper for _kappa_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_returns_in = returns_in
        if "returns_in" in ["trades", "open_trades"] and isinstance(
            arg_returns_in, (list, dict)
        ):
            arg_returns_in = pd.DataFrame(arg_returns_in)
        elif "returns_in" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_returns_in, list):
            arg_returns_in = pd.Series(arg_returns_in)
        kwargs["returns_in"] = arg_returns_in

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

        arg_order = order
        if "order" in ["trades", "open_trades"] and isinstance(arg_order, (list, dict)):
            arg_order = pd.DataFrame(arg_order)
        elif "order" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_order, list):
            arg_order = pd.Series(arg_order)
        kwargs["order"] = arg_order

        res = _kappa_ratio_impl(**kwargs)
        logger.info("Executed kappa_ratio tool successfully.")

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

        return analytics_tool_result("kappa_ratio", data={"kappa_ratio": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def sterling_ratio(cagr_value: float, avg_yearly_max_dd: float) -> dict[str, Any]:
    """AI Tool wrapper for _sterling_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_cagr_value = cagr_value
        if "cagr_value" in ["trades", "open_trades"] and isinstance(
            arg_cagr_value, (list, dict)
        ):
            arg_cagr_value = pd.DataFrame(arg_cagr_value)
        elif "cagr_value" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_cagr_value, list):
            arg_cagr_value = pd.Series(arg_cagr_value)
        kwargs["cagr_value"] = arg_cagr_value

        arg_avg_yearly_max_dd = avg_yearly_max_dd
        if "avg_yearly_max_dd" in ["trades", "open_trades"] and isinstance(
            arg_avg_yearly_max_dd, (list, dict)
        ):
            arg_avg_yearly_max_dd = pd.DataFrame(arg_avg_yearly_max_dd)
        elif "avg_yearly_max_dd" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_avg_yearly_max_dd, list):
            arg_avg_yearly_max_dd = pd.Series(arg_avg_yearly_max_dd)
        kwargs["avg_yearly_max_dd"] = arg_avg_yearly_max_dd

        res = _sterling_ratio_impl(**kwargs)
        logger.info("Executed sterling_ratio tool successfully.")

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
            "sterling_ratio", data={"sterling_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def rina_index(
    select_net_profit: float, avg_drawdown: float, percent_time_in_market: float
) -> dict[str, Any]:
    """AI Tool wrapper for _rina_index_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_select_net_profit = select_net_profit
        if "select_net_profit" in ["trades", "open_trades"] and isinstance(
            arg_select_net_profit, (list, dict)
        ):
            arg_select_net_profit = pd.DataFrame(arg_select_net_profit)
        elif "select_net_profit" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_select_net_profit, list):
            arg_select_net_profit = pd.Series(arg_select_net_profit)
        kwargs["select_net_profit"] = arg_select_net_profit

        arg_avg_drawdown = avg_drawdown
        if "avg_drawdown" in ["trades", "open_trades"] and isinstance(
            arg_avg_drawdown, (list, dict)
        ):
            arg_avg_drawdown = pd.DataFrame(arg_avg_drawdown)
        elif "avg_drawdown" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_avg_drawdown, list):
            arg_avg_drawdown = pd.Series(arg_avg_drawdown)
        kwargs["avg_drawdown"] = arg_avg_drawdown

        arg_percent_time_in_market = percent_time_in_market
        if "percent_time_in_market" in ["trades", "open_trades"] and isinstance(
            arg_percent_time_in_market, (list, dict)
        ):
            arg_percent_time_in_market = pd.DataFrame(arg_percent_time_in_market)
        elif "percent_time_in_market" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_percent_time_in_market, list):
            arg_percent_time_in_market = pd.Series(arg_percent_time_in_market)
        kwargs["percent_time_in_market"] = arg_percent_time_in_market

        res = _rina_index_impl(**kwargs)
        logger.info("Executed rina_index tool successfully.")

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

        return analytics_tool_result("rina_index", data={"rina_index": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def profit_factor(trades: pd.DataFrame | pd.Series | np.ndarray) -> dict[str, Any]:
    """AI Tool wrapper for _profit_factor_impl."""
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

        res = _profit_factor_impl(**kwargs)
        logger.info("Executed profit_factor tool successfully.")

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
            "profit_factor", data={"profit_factor": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def payoff_ratio(trades: pd.DataFrame | pd.Series | np.ndarray) -> dict[str, Any]:
    """AI Tool wrapper for _payoff_ratio_impl."""
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

        res = _payoff_ratio_impl(**kwargs)
        logger.info("Executed payoff_ratio tool successfully.")

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
            "payoff_ratio", data={"payoff_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def edge_ratio(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _edge_ratio_impl."""
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

        res = _edge_ratio_impl(**kwargs)
        logger.info("Executed edge_ratio tool successfully.")

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

        return analytics_tool_result("edge_ratio", data={"edge_ratio": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def profit_to_mae_ratio(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _profit_to_mae_ratio_impl."""
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

        res = _profit_to_mae_ratio_impl(**kwargs)
        logger.info("Executed profit_to_mae_ratio tool successfully.")

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
            "profit_to_mae_ratio", data={"profit_to_mae_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def mfe_to_mae_ratio(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _mfe_to_mae_ratio_impl."""
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

        res = _mfe_to_mae_ratio_impl(**kwargs)
        logger.info("Executed mfe_to_mae_ratio tool successfully.")

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
            "mfe_to_mae_ratio", data={"mfe_to_mae_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def return_over_drawdown(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _return_over_drawdown_impl."""
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

        res = _return_over_drawdown_impl(**kwargs)
        logger.info("Executed return_over_drawdown tool successfully.")

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
            "return_over_drawdown", data={"return_over_drawdown": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def expectancy_over_std(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _expectancy_over_std_impl."""
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

        res = _expectancy_over_std_impl(**kwargs)
        logger.info("Executed expectancy_over_std tool successfully.")

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
            "expectancy_over_std", data={"expectancy_over_std": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def net_profit_as_percent_of_largest_loss(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _net_profit_as_percent_of_largest_loss_impl."""
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

        res = _net_profit_as_percent_of_largest_loss_impl(**kwargs)
        logger.info("Executed net_profit_as_percent_of_largest_loss tool successfully.")

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
            "net_profit_as_percent_of_largest_loss",
            data={"net_profit_as_percent_of_largest_loss": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def net_profit_as_percent_of_max_trade_drawdown(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _net_profit_as_percent_of_max_trade_drawdown_impl."""
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

        res = _net_profit_as_percent_of_max_trade_drawdown_impl(**kwargs)
        logger.info(
            "Executed net_profit_as_percent_of_max_trade_drawdown tool successfully."
        )

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
            "net_profit_as_percent_of_max_trade_drawdown",
            data={"net_profit_as_percent_of_max_trade_drawdown": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def net_profit_as_percent_of_max_strategy_drawdown(
    net_profit_val: float, max_strategy_drawdown: float
) -> dict[str, Any]:
    """AI Tool wrapper for _net_profit_as_percent_of_max_strategy_drawdown_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_net_profit_val = net_profit_val
        if "net_profit_val" in ["trades", "open_trades"] and isinstance(
            arg_net_profit_val, (list, dict)
        ):
            arg_net_profit_val = pd.DataFrame(arg_net_profit_val)
        elif "net_profit_val" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_net_profit_val, list):
            arg_net_profit_val = pd.Series(arg_net_profit_val)
        kwargs["net_profit_val"] = arg_net_profit_val

        arg_max_strategy_drawdown = max_strategy_drawdown
        if "max_strategy_drawdown" in ["trades", "open_trades"] and isinstance(
            arg_max_strategy_drawdown, (list, dict)
        ):
            arg_max_strategy_drawdown = pd.DataFrame(arg_max_strategy_drawdown)
        elif "max_strategy_drawdown" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_max_strategy_drawdown, list):
            arg_max_strategy_drawdown = pd.Series(arg_max_strategy_drawdown)
        kwargs["max_strategy_drawdown"] = arg_max_strategy_drawdown

        res = _net_profit_as_percent_of_max_strategy_drawdown_impl(**kwargs)
        logger.info(
            "Executed net_profit_as_percent_of_max_strategy_drawdown tool successfully."
        )

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
            "net_profit_as_percent_of_max_strategy_drawdown",
            data={"net_profit_as_percent_of_max_strategy_drawdown": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def select_net_profit_as_percent_of_largest_loss(
    trades: pd.DataFrame,
) -> dict[str, Any]:
    """AI Tool wrapper for _select_net_profit_as_percent_of_largest_loss_impl."""
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

        res = _select_net_profit_as_percent_of_largest_loss_impl(**kwargs)
        logger.info(
            "Executed select_net_profit_as_percent_of_largest_loss tool successfully."
        )

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
            "select_net_profit_as_percent_of_largest_loss",
            data={"select_net_profit_as_percent_of_largest_loss": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def select_net_profit_as_percent_of_max_trade_drawdown(
    trades: pd.DataFrame,
) -> dict[str, Any]:
    """AI Tool wrapper for _select_net_profit_as_percent_of_max_trade_drawdown_impl."""
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

        res = _select_net_profit_as_percent_of_max_trade_drawdown_impl(**kwargs)
        logger.info(
            "Executed select_net_profit_as_percent_of_max_trade_drawdown tool successfully."
        )

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
            "select_net_profit_as_percent_of_max_trade_drawdown",
            data={"select_net_profit_as_percent_of_max_trade_drawdown": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def select_net_profit_as_percent_of_max_strategy_drawdown(
    select_net_profit_val: float, max_strategy_drawdown: float
) -> dict[str, Any]:
    """AI Tool wrapper for _select_net_profit_as_percent_of_max_strategy_drawdown_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_select_net_profit_val = select_net_profit_val
        if "select_net_profit_val" in ["trades", "open_trades"] and isinstance(
            arg_select_net_profit_val, (list, dict)
        ):
            arg_select_net_profit_val = pd.DataFrame(arg_select_net_profit_val)
        elif "select_net_profit_val" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_select_net_profit_val, list):
            arg_select_net_profit_val = pd.Series(arg_select_net_profit_val)
        kwargs["select_net_profit_val"] = arg_select_net_profit_val

        arg_max_strategy_drawdown = max_strategy_drawdown
        if "max_strategy_drawdown" in ["trades", "open_trades"] and isinstance(
            arg_max_strategy_drawdown, (list, dict)
        ):
            arg_max_strategy_drawdown = pd.DataFrame(arg_max_strategy_drawdown)
        elif "max_strategy_drawdown" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_max_strategy_drawdown, list):
            arg_max_strategy_drawdown = pd.Series(arg_max_strategy_drawdown)
        kwargs["max_strategy_drawdown"] = arg_max_strategy_drawdown

        res = _select_net_profit_as_percent_of_max_strategy_drawdown_impl(**kwargs)
        logger.info(
            "Executed select_net_profit_as_percent_of_max_strategy_drawdown tool successfully."
        )

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
            "select_net_profit_as_percent_of_max_strategy_drawdown",
            data={
                "select_net_profit_as_percent_of_max_strategy_drawdown": data_payload
            },
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def adjusted_net_profit_as_percent_of_largest_loss(
    trades: pd.DataFrame,
) -> dict[str, Any]:
    """AI Tool wrapper for _adjusted_net_profit_as_percent_of_largest_loss_impl."""
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

        res = _adjusted_net_profit_as_percent_of_largest_loss_impl(**kwargs)
        logger.info(
            "Executed adjusted_net_profit_as_percent_of_largest_loss tool successfully."
        )

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
            "adjusted_net_profit_as_percent_of_largest_loss",
            data={"adjusted_net_profit_as_percent_of_largest_loss": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def adjusted_net_profit_as_percent_of_max_trade_drawdown(
    trades: pd.DataFrame,
) -> dict[str, Any]:
    """AI Tool wrapper for _adjusted_net_profit_as_percent_of_max_trade_drawdown_impl."""
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

        res = _adjusted_net_profit_as_percent_of_max_trade_drawdown_impl(**kwargs)
        logger.info(
            "Executed adjusted_net_profit_as_percent_of_max_trade_drawdown tool successfully."
        )

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
            "adjusted_net_profit_as_percent_of_max_trade_drawdown",
            data={"adjusted_net_profit_as_percent_of_max_trade_drawdown": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def adjusted_net_profit_as_percent_of_max_strategy_drawdown(
    adjusted_net_profit_val: float, max_strategy_drawdown: float
) -> dict[str, Any]:
    """AI Tool wrapper for _adjusted_net_profit_as_percent_of_max_strategy_drawdown_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_adjusted_net_profit_val = adjusted_net_profit_val
        if "adjusted_net_profit_val" in ["trades", "open_trades"] and isinstance(
            arg_adjusted_net_profit_val, (list, dict)
        ):
            arg_adjusted_net_profit_val = pd.DataFrame(arg_adjusted_net_profit_val)
        elif "adjusted_net_profit_val" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_adjusted_net_profit_val, list):
            arg_adjusted_net_profit_val = pd.Series(arg_adjusted_net_profit_val)
        kwargs["adjusted_net_profit_val"] = arg_adjusted_net_profit_val

        arg_max_strategy_drawdown = max_strategy_drawdown
        if "max_strategy_drawdown" in ["trades", "open_trades"] and isinstance(
            arg_max_strategy_drawdown, (list, dict)
        ):
            arg_max_strategy_drawdown = pd.DataFrame(arg_max_strategy_drawdown)
        elif "max_strategy_drawdown" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_max_strategy_drawdown, list):
            arg_max_strategy_drawdown = pd.Series(arg_max_strategy_drawdown)
        kwargs["max_strategy_drawdown"] = arg_max_strategy_drawdown

        res = _adjusted_net_profit_as_percent_of_max_strategy_drawdown_impl(**kwargs)
        logger.info(
            "Executed adjusted_net_profit_as_percent_of_max_strategy_drawdown tool successfully."
        )

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
            "adjusted_net_profit_as_percent_of_max_strategy_drawdown",
            data={
                "adjusted_net_profit_as_percent_of_max_strategy_drawdown": data_payload
            },
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def adjusted_profit_factor(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _adjusted_profit_factor_impl."""
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

        res = _adjusted_profit_factor_impl(**kwargs)
        logger.info("Executed adjusted_profit_factor tool successfully.")

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
            "adjusted_profit_factor", data={"adjusted_profit_factor": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def select_profit_factor(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _select_profit_factor_impl."""
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

        res = _select_profit_factor_impl(**kwargs)
        logger.info("Executed select_profit_factor tool successfully.")

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
            "select_profit_factor", data={"select_profit_factor": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def expectancy(trades: pd.DataFrame | pd.Series | np.ndarray) -> dict[str, Any]:
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


def expectancy_r(r_multiples: pd.Series | np.ndarray) -> dict[str, Any]:
    """AI Tool wrapper for _expectancy_r_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_r_multiples = r_multiples
        if "r_multiples" in ["trades", "open_trades"] and isinstance(
            arg_r_multiples, (list, dict)
        ):
            arg_r_multiples = pd.DataFrame(arg_r_multiples)
        elif "r_multiples" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_r_multiples, list):
            arg_r_multiples = pd.Series(arg_r_multiples)
        kwargs["r_multiples"] = arg_r_multiples

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


def calculate_ratio_metrics(
    *,
    returns: list[float],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_ratio_metrics_impl."""
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

        res = _calculate_ratio_metrics_impl(**kwargs)
        logger.info("Executed calculate_ratio_metrics tool successfully.")

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
            "calculate_ratio_metrics", data={"calculate_ratio_metrics": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}
