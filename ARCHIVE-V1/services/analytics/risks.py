"""risks.py - Calculate volatility, tail risk, exposure, margin utilization, and ruin metrics.

Classes:
    None.

Functions:
    _risk_of_ruin_kernel: Monte Carlo simulation of trade outcomes to estimate ruin probability.
    volatility: Standard deviation of returns as positive percentage.
    annualized_volatility: Annualized volatility as positive percentage.
    downside_volatility: Downside deviation as positive percentage.
    value_at_risk: Value at Risk as positive percentage.
    conditional_var: CVaR / Expected Shortfall as positive percentage.
    expected_shortfall: Calculate Expected Shortfall (alias for CVaR).
    max_loss_probability: Probability of a single trade loss exceeding a threshold in R-units.
    drawdown_probability: Probability that the strategy will experience a drawdown exceeding threshold_pct.
    risk_of_ruin: Monte Carlo simulation of trade outcomes to estimate ruin probability.
    max_nominal_exposure_simple: Maximum total nominal exposure held at any one time.
    max_gross_exposure: Maximum total nominal exposure held (Gross Exposure).
    avg_trade_nominal_exposure: Average nominal exposure per trade (not time-weighted).
    exposure_time_ratio: Percentage of the total period spent in the market (0-100).
    max_single_trade_margin_utilization: Maximum absolute margin used by a single trade as percentage of equity.
    avg_single_trade_margin_utilization: Average absolute margin used per trade as percentage of equity.
    _compounding_ruin_kernel: Monte Carlo simulation using dynamic compounding risk.
    _horizon_ruin_kernel: Monte Carlo simulation with a fixed trade horizon.
    time_weighted_avg_exposure: Time-weighted average notional exposure held.
    portfolio_margin_utilization_curve: Generate the curve of total aggregate margin utilization over time.
    compounding_risk_of_ruin: Monte Carlo simulation of ruin probability using dynamic compounding risk.
    risk_of_ruin_with_custom_horizon: Monte Carlo simulation of ruin probability over a fixed number of future trades.
    historical_var_by_symbol: Calculate historical VaR (as positive profit_loss units) for each symbol individually.
    portfolio_var_from_covariance: Calculate Portfolio VaR using Variance-Covariance (Parametric) method.
    calculate_risk_metrics: Calculate VaR, CVaR, and volatility from returns.

Nested functions and methods:
    historical_var_by_symbol._calc_var: Calculate positive historical VaR for one symbol group.
"""

from typing import Any, Literal

import numpy as np
import pandas as pd

from . import common
from .common import (
    _to_1d_float_array,
    analytics_tool_result,
    get_closed_trades,
    get_r_multiples,
    max_gross_size_held,
    percent_time_in_market,
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


@njit(cache=True)
def _risk_of_ruin_kernel(
    outcomes, risk_per_trade, target_drawdown, num_simulations, initial_capital
):
    """
    Monte Carlo simulation of trade outcomes to estimate ruin probability.

    This simulates fixed fractional risk based on initial capital,
    not dynamic compounding risk. Each 1R outcome is converted to
    a capital unit change based on risk_per_trade.
    """
    ruin_count = 0
    n_outcomes = len(outcomes)
    simulation_length = n_outcomes * 2
    ruin_threshold = initial_capital - target_drawdown

    for _ in range(num_simulations):
        capital = initial_capital
        for _ in range(simulation_length):
            idx = np.random.randint(0, n_outcomes)
            outcome = outcomes[idx]
            capital += outcome * risk_per_trade
            if capital <= ruin_threshold:
                ruin_count += 1
                break
    return ruin_count


# =========================================================================
# Volatility Metrics
# =========================================================================


def _volatility_impl(rets: pd.Series | np.ndarray) -> float:
    """Standard deviation of returns as positive percentage.

    Purpose:
        Standard deviation of returns as positive percentage.
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
    normalized = _to_1d_float_array(rets)
    if len(normalized) < 2:
        return 0.0
    return float(np.std(normalized, ddof=1) * 100.0)


def _annualized_volatility_impl(
    rets: pd.Series | np.ndarray, periods_per_year: int = 252
) -> float:
    """Annualized volatility as positive percentage.

    Purpose:
        Annualized volatility as positive percentage.
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
    v = _volatility_impl(rets)
    return float(v * np.sqrt(periods_per_year))


def _downside_volatility_impl(
    rets: pd.Series | np.ndarray, target: float = 0.0
) -> float:
    """Downside deviation as positive percentage.

    Purpose:
        Downside deviation as positive percentage.
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
    normalized = _to_1d_float_array(rets)
    if len(normalized) < 2:
        return 0.0

    downside_diffs = np.minimum(normalized - target, 0.0)
    downside_risk = np.sqrt(np.mean(downside_diffs**2))

    return float(downside_risk * 100.0)


# =========================================================================
# Tail Risk & Loss Thresholds
# =========================================================================


def _value_at_risk_impl(
    rets: pd.Series | np.ndarray,
    confidence: float = 0.95,
    method: Literal["historical", "parametric"] = "historical",
) -> float:
    """Value at Risk as positive percentage.

    Purpose:
        Value at Risk as positive percentage.
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
        confidence:
            Analytics input consumed by this function.
        method:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")

    normalized = _to_1d_float_array(rets)
    if len(normalized) == 0:
        return 0.0

    if method == "historical":
        q = np.quantile(normalized, 1.0 - confidence)
        return float(max(0.0, -q) * 100.0)

    if method == "parametric":
        if len(normalized) < 2:
            return 0.0

        from scipy.stats import norm

        mean = np.mean(normalized)
        std = np.std(normalized, ddof=1)
        z_score = norm.ppf(1.0 - confidence)

        var_return = mean + z_score * std
        return float(max(0.0, -var_return) * 100.0)

    raise ValueError("method must be 'historical' or 'parametric'")


def _conditional_var_impl(
    rets: pd.Series | np.ndarray, confidence: float = 0.95
) -> float:
    """CVaR / Expected Shortfall as positive percentage.

    Purpose:
        CVaR / Expected Shortfall as positive percentage.
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
        confidence:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")

    normalized = _to_1d_float_array(rets)
    if len(normalized) == 0:
        return 0.0

    var_threshold = np.quantile(normalized, 1.0 - confidence)
    tail_returns = normalized[normalized <= var_threshold]

    if len(tail_returns) == 0:
        return float(max(0.0, -var_threshold) * 100.0)

    tail_mean = np.mean(tail_returns)
    return float(max(0.0, -tail_mean) * 100.0)


def _expected_shortfall_impl(
    rets: pd.Series | np.ndarray, confidence: float = 0.95
) -> float:
    """Calculate Expected Shortfall (alias for CVaR).

    Purpose:
        Calculate Expected Shortfall (alias for CVaR).
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
        confidence:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    return _conditional_var_impl(rets, confidence)


def _max_loss_probability_impl(
    trades: pd.DataFrame, loss_threshold_r: float = -1.0
) -> float:
    """Probability of a single trade loss exceeding a threshold in R-units.

    Purpose:
        Probability of a single trade loss exceeding a threshold in R-units.
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
        loss_threshold_r:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    r_multiples = get_r_multiples(trades)
    if r_multiples.empty:
        return 0.0

    # We want losses worse than threshold (e.g. -2.5 < -2.0)
    extreme_losses = r_multiples[r_multiples < loss_threshold_r]
    return float(len(extreme_losses) / len(r_multiples))


def _drawdown_probability_impl(
    returns_in: pd.Series | np.ndarray, threshold_pct: float
) -> float:
    """Probability that the strategy will experience a drawdown exceeding threshold_pct.

    Purpose:
        Probability that the strategy will experience a drawdown exceeding threshold_pct.
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
        threshold_pct:
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

    # Prepend starting equity 1.0 to capture first-period drawdown
    equity = np.concatenate([[1.0], np.cumprod(1.0 + normalized)])
    running_max = np.maximum.accumulate(equity)
    drawdowns = (running_max - equity) / running_max

    threshold_fraction = threshold_pct / 100.0

    # Exclude synthetic point from denominator
    dd_after_start = drawdowns[1:]
    exceeded = (dd_after_start > threshold_fraction).sum()

    return float(exceeded / len(dd_after_start))


# =========================================================================
# Capital Risk & Ruin
# =========================================================================


def _risk_of_ruin_impl(
    trades: pd.DataFrame,
    risk_per_trade_pct: float | None = None,
    target_drawdown_pct: float = 50.0,
    num_simulations: int = 10000,
    **kwargs,
) -> float:
    """Monte Carlo simulation of trade outcomes to estimate ruin probability.

    Purpose:
        Monte Carlo simulation of trade outcomes to estimate ruin probability.
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
        risk_per_trade_pct:
            Analytics input consumed by this function.
        target_drawdown_pct:
            Analytics input consumed by this function.
        num_simulations:
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
    if risk_per_trade_pct is None:
        risk_per_trade_pct = kwargs.pop("risk_per_trade", 0.0)
    if "target_drawdown" in kwargs:
        target_drawdown_pct = kwargs.pop("target_drawdown")

    if risk_per_trade_pct <= 0 or target_drawdown_pct <= 0 or num_simulations <= 0:
        return 0.0

    r_outcomes = get_r_multiples(trades).values
    if len(r_outcomes) < 5:
        return 0.0

    # _risk_of_ruin_kernel uses initial_capital=100.0
    ruin_count = _risk_of_ruin_kernel(
        r_outcomes,
        float(risk_per_trade_pct),
        float(target_drawdown_pct),
        int(num_simulations),
        100.0,
    )
    return float(ruin_count / num_simulations)


# =========================================================================
# Market Exposure (Capacity & Utilization)
# =========================================================================


def _max_nominal_exposure_simple_impl(
    trades: pd.DataFrame, contract_size: float = 100000.0
) -> float:
    """Maximum total nominal exposure held at any one time.

    Purpose:
        Maximum total nominal exposure held at any one time.
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
        contract_size:
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

    max_gross_size = max_gross_size_held(trades)
    return float(max_gross_size * contract_size)


def _max_gross_exposure_impl(
    trades: pd.DataFrame, contract_size: float = 100000.0
) -> float:
    """Maximum total nominal exposure held (Gross Exposure).

    Purpose:
        Maximum total nominal exposure held (Gross Exposure).
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
        contract_size:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    return _max_nominal_exposure_simple_impl(trades, contract_size)


def _avg_trade_nominal_exposure_impl(
    trades: pd.DataFrame, contract_size: float = 100000.0
) -> float:
    """Average nominal exposure per trade (not time-weighted).

    Purpose:
        Average nominal exposure per trade (not time-weighted).
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
        contract_size:
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

    # Find size column
    size_col = None
    for col in ["size", "quantity", "volume"]:
        if col in trades.columns:
            size_col = col
            break

    if not size_col:
        return 0.0

    return float(trades[size_col].abs().mean() * contract_size)


def _exposure_time_ratio_impl(
    trades: pd.DataFrame,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> float:
    """Percentage of the total period spent in the market (0-100).

    Purpose:
        Percentage of the total period spent in the market (0-100).
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
    return percent_time_in_market(trades, start_time, end_time)


def _max_single_trade_margin_utilization_impl(
    trades: pd.DataFrame, account_equity: float
) -> float:
    """Maximum absolute margin used by a single trade as percentage of equity.

    Purpose:
        Maximum absolute margin used by a single trade as percentage of equity.
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
        account_equity:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if trades.empty or account_equity <= 0:
        return 0.0

    if "margin_used" in trades.columns:
        return float((trades["margin_used"].abs().max() / account_equity) * 100.0)

    return 0.0


def _avg_single_trade_margin_utilization_impl(
    trades: pd.DataFrame, account_equity: float
) -> float:
    """Average absolute margin used per trade as percentage of equity.

    Purpose:
        Average absolute margin used per trade as percentage of equity.
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
        account_equity:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if trades.empty or account_equity <= 0:
        return 0.0

    if "margin_used" in trades.columns:
        return float((trades["margin_used"].abs().mean() / account_equity) * 100.0)

    return 0.0


# =========================================================================
# Advanced Portfolio & Compounding Risks
# =========================================================================


@njit(cache=True)
def _compounding_ruin_kernel(
    outcomes, risk_fraction, target_drawdown, num_simulations, initial_capital
):
    """
    Monte Carlo simulation using dynamic compounding risk.
    Each 1R outcome risks a fraction of *current* capital.
    """
    ruin_count = 0
    n_outcomes = len(outcomes)
    simulation_length = n_outcomes * 2
    # target_drawdown is percentage (e.g. 50.0)
    ruin_threshold = initial_capital * (1.0 - target_drawdown / 100.0)

    for _ in range(num_simulations):
        capital = initial_capital
        for _ in range(simulation_length):
            idx = np.random.randint(0, n_outcomes)
            outcome = outcomes[idx]
            # Compounding: outcome * (current_capital * risk_fraction)
            capital += outcome * (capital * risk_fraction)
            if capital <= ruin_threshold:
                ruin_count += 1
                break
    return ruin_count


@njit(cache=True)
def _horizon_ruin_kernel(
    outcomes, risk_per_trade, target_drawdown, num_simulations, initial_capital, horizon
):
    """
    Monte Carlo simulation with a fixed trade horizon.
    """
    ruin_count = 0
    n_outcomes = len(outcomes)
    ruin_threshold = initial_capital - target_drawdown

    for _ in range(num_simulations):
        capital = initial_capital
        for _ in range(horizon):
            idx = np.random.randint(0, n_outcomes)
            outcome = outcomes[idx]
            capital += outcome * risk_per_trade
            if capital <= ruin_threshold:
                ruin_count += 1
                break
    return ruin_count


def _time_weighted_avg_exposure_impl(
    trades: pd.DataFrame,
    contract_size: float = 100000.0,
    end_time: pd.Timestamp | None = None,
) -> float:
    """Time-weighted average notional exposure held.

    Purpose:
        Time-weighted average notional exposure held.
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
        contract_size:
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

    size_col = None
    for col in ["size", "quantity", "volume"]:
        if col in trades.columns:
            size_col = col
            break
    if not size_col:
        return 0.0

    open_times = trades["open_time"].values
    fallback = end_time or trades["open_time"].max()
    close_times = trades["close_time"].fillna(fallback).values
    sizes = trades[size_col].abs().values

    event_times = np.concatenate([open_times, close_times])
    event_sizes = np.concatenate([sizes, -sizes])

    idx = np.lexsort((-event_sizes, event_times))
    sorted_times = event_times[idx].astype("datetime64[ns]").view("int64")
    sorted_sizes = event_sizes[idx]

    tw_avg = common.___time_weighted_kernel_impl_impl(sorted_times, sorted_sizes)
    return float(tw_avg * contract_size)


def _portfolio_margin_utilization_curve_impl(
    trades: pd.DataFrame, account_equity: float, end_time: pd.Timestamp | None = None
) -> pd.Series:
    """Generate the curve of total aggregate margin utilization over time.

    Purpose:
        Generate the curve of total aggregate margin utilization over time.
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
        account_equity:
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
    if trades.empty or "margin_used" not in trades.columns or account_equity <= 0:
        return pd.Series(dtype=float)

    open_times = trades["open_time"].values
    fallback = end_time or trades["open_time"].max()
    close_times = trades["close_time"].fillna(fallback).values
    margins = trades["margin_used"].abs().values

    event_times = np.concatenate([open_times, close_times])
    event_changes = np.concatenate([margins, -margins])

    idx = np.argsort(event_times)
    sorted_times = event_times[idx]
    sorted_changes = event_changes[idx]

    curve_values = common.___exposure_curve_kernel_impl_impl(
        sorted_times, sorted_changes
    )
    utilization_pct = (curve_values / account_equity) * 100.0

    return pd.Series(utilization_pct, index=pd.to_datetime(sorted_times))


def _compounding_risk_of_ruin_impl(
    trades: pd.DataFrame,
    risk_fraction: float,
    target_drawdown_pct: float = 50.0,
    num_simulations: int = 10000,
) -> float:
    """Monte Carlo simulation of ruin probability using dynamic compounding risk.

    Purpose:
        Monte Carlo simulation of ruin probability using dynamic compounding risk.
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
        risk_fraction:
            Analytics input consumed by this function.
        target_drawdown_pct:
            Analytics input consumed by this function.
        num_simulations:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if risk_fraction <= 0 or target_drawdown_pct <= 0 or num_simulations <= 0:
        return 0.0

    r_outcomes = get_r_multiples(trades).values
    if len(r_outcomes) < 5:
        return 0.0

    ruin_count = _compounding_ruin_kernel(
        r_outcomes,
        float(risk_fraction),
        float(target_drawdown_pct),
        int(num_simulations),
        100.0,
    )
    return float(ruin_count / num_simulations)


def _risk_of_ruin_with_custom_horizon_impl(
    trades: pd.DataFrame,
    risk_per_trade_pct: float,
    horizon: int,
    target_drawdown_pct: float = 50.0,
    num_simulations: int = 10000,
) -> float:
    """Monte Carlo simulation of ruin probability over a fixed number of future trades.

    Purpose:
        Monte Carlo simulation of ruin probability over a fixed number of future trades.
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
        risk_per_trade_pct:
            Analytics input consumed by this function.
        horizon:
            Analytics input consumed by this function.
        target_drawdown_pct:
            Analytics input consumed by this function.
        num_simulations:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if (
        risk_per_trade_pct <= 0
        or horizon <= 0
        or target_drawdown_pct <= 0
        or num_simulations <= 0
    ):
        return 0.0

    r_outcomes = get_r_multiples(trades).values
    if len(r_outcomes) < 5:
        return 0.0

    ruin_count = _horizon_ruin_kernel(
        r_outcomes,
        float(risk_per_trade_pct),
        float(target_drawdown_pct),
        int(num_simulations),
        100.0,
        int(horizon),
    )
    return float(ruin_count / num_simulations)


def _historical_var_by_symbol_impl(
    trades: pd.DataFrame, confidence: float = 0.95
) -> pd.Series:
    """Calculate historical VaR (as positive profit_loss units) for each symbol individually.

    Purpose:
        Calculate historical VaR (as positive profit_loss units) for each symbol individually.
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
        confidence:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")

    data = get_closed_trades(trades)
    if data.empty or "symbol" not in data.columns or "profit_loss" not in data.columns:
        return pd.Series(dtype=float)

    def _calc_var(group):
        """Calculate positive historical VaR for one symbol group."""
        pnl = group["profit_loss"].values
        if len(pnl) == 0:
            return 0.0
        q = np.quantile(pnl, 1.0 - confidence)
        return float(max(0.0, -q))

    return data.groupby("symbol").apply(_calc_var)


def _portfolio_var_from_covariance_impl(
    returns_df: pd.DataFrame,
    weights: np.ndarray | None = None,
    confidence: float = 0.95,
) -> float:
    """Calculate Portfolio VaR using Variance-Covariance (Parametric) method.

    Purpose:
        Calculate Portfolio VaR using Variance-Covariance (Parametric) method.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        returns_df:
            Analytics input consumed by this function.
        weights:
            Analytics input consumed by this function.
        confidence:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")

    if returns_df.empty:
        return 0.0

    n_assets = returns_df.shape[1]
    if weights is None:
        weights = np.ones(n_assets) / n_assets
    else:
        if len(weights) != n_assets:
            raise ValueError(
                f"weights length ({len(weights)}) must match number of assets ({n_assets})"
            )
        # Normalize weights to sum to 1
        weights = weights / weights.sum()

    cov_matrix = returns_df.cov().values
    portfolio_std = np.sqrt(weights.T @ cov_matrix @ weights)
    portfolio_mean = returns_df.mean() @ weights

    from scipy.stats import norm

    z_score = norm.ppf(1.0 - confidence)

    var_return = portfolio_mean + z_score * portfolio_std
    return float(max(0.0, -var_return) * 100.0)


# =========================================================================
# Agent-Facing Function Tools
# =========================================================================


def _calculate_risk_metrics_impl(
    *,
    returns: list[float],
    alpha: float = 0.05,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Calculate VaR, CVaR, and volatility from returns.

    Purpose:
        Calculate VaR, CVaR, and volatility from returns.
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
        alpha:
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
    var = float(values.quantile(float(alpha))) if len(values) else 0.0
    tail = values[values <= var]
    data = {
        "var": var,
        "cvar": float(tail.mean()) if len(tail) else 0.0,
        "volatility": float(values.std()) if len(values) else 0.0,
    }
    return analytics_tool_result(
        "calculate_risk_metrics",
        data=data,
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def _volatility_impl(rets: pd.Series | np.ndarray) -> dict[str, Any]:
    """AI Tool wrapper for _volatility_impl."""
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

        res = _volatility_impl(**kwargs)
        logger.info("Executed volatility tool successfully.")

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

        return analytics_tool_result("volatility", data={"volatility": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _annualized_volatility_impl(
    rets: pd.Series | np.ndarray, periods_per_year: int = 252
) -> dict[str, Any]:
    """AI Tool wrapper for _annualized_volatility_impl."""
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

        res = _annualized_volatility_impl(**kwargs)
        logger.info("Executed annualized_volatility tool successfully.")

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
            "annualized_volatility", data={"annualized_volatility": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _downside_volatility_impl(
    rets: pd.Series | np.ndarray, target: float = 0.0
) -> dict[str, Any]:
    """AI Tool wrapper for _downside_volatility_impl."""
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

        res = _downside_volatility_impl(**kwargs)
        logger.info("Executed downside_volatility tool successfully.")

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
            "downside_volatility", data={"downside_volatility": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _value_at_risk_impl(
    rets: pd.Series | np.ndarray,
    confidence: float = 0.95,
    method: Literal["historical", "parametric"] = "historical",
) -> dict[str, Any]:
    """AI Tool wrapper for _value_at_risk_impl."""
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

        arg_confidence = confidence
        if "confidence" in ["trades", "open_trades"] and isinstance(
            arg_confidence, (list, dict)
        ):
            arg_confidence = pd.DataFrame(arg_confidence)
        elif "confidence" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_confidence, list):
            arg_confidence = pd.Series(arg_confidence)
        kwargs["confidence"] = arg_confidence

        arg_method = method
        if "method" in ["trades", "open_trades"] and isinstance(
            arg_method, (list, dict)
        ):
            arg_method = pd.DataFrame(arg_method)
        elif "method" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_method, list):
            arg_method = pd.Series(arg_method)
        kwargs["method"] = arg_method

        res = _value_at_risk_impl(**kwargs)
        logger.info("Executed value_at_risk tool successfully.")

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
            "value_at_risk", data={"value_at_risk": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _conditional_var_impl(
    rets: pd.Series | np.ndarray, confidence: float = 0.95
) -> dict[str, Any]:
    """AI Tool wrapper for _conditional_var_impl."""
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

        arg_confidence = confidence
        if "confidence" in ["trades", "open_trades"] and isinstance(
            arg_confidence, (list, dict)
        ):
            arg_confidence = pd.DataFrame(arg_confidence)
        elif "confidence" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_confidence, list):
            arg_confidence = pd.Series(arg_confidence)
        kwargs["confidence"] = arg_confidence

        res = _conditional_var_impl(**kwargs)
        logger.info("Executed conditional_var tool successfully.")

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
            "conditional_var", data={"conditional_var": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _expected_shortfall_impl(
    rets: pd.Series | np.ndarray, confidence: float = 0.95
) -> dict[str, Any]:
    """AI Tool wrapper for _expected_shortfall_impl."""
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

        arg_confidence = confidence
        if "confidence" in ["trades", "open_trades"] and isinstance(
            arg_confidence, (list, dict)
        ):
            arg_confidence = pd.DataFrame(arg_confidence)
        elif "confidence" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_confidence, list):
            arg_confidence = pd.Series(arg_confidence)
        kwargs["confidence"] = arg_confidence

        res = _expected_shortfall_impl(**kwargs)
        logger.info("Executed expected_shortfall tool successfully.")

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
            "expected_shortfall", data={"expected_shortfall": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _max_loss_probability_impl(
    trades: pd.DataFrame, loss_threshold_r: float = -1.0
) -> dict[str, Any]:
    """AI Tool wrapper for _max_loss_probability_impl."""
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

        arg_loss_threshold_r = loss_threshold_r
        if "loss_threshold_r" in ["trades", "open_trades"] and isinstance(
            arg_loss_threshold_r, (list, dict)
        ):
            arg_loss_threshold_r = pd.DataFrame(arg_loss_threshold_r)
        elif "loss_threshold_r" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_loss_threshold_r, list):
            arg_loss_threshold_r = pd.Series(arg_loss_threshold_r)
        kwargs["loss_threshold_r"] = arg_loss_threshold_r

        res = _max_loss_probability_impl(**kwargs)
        logger.info("Executed max_loss_probability tool successfully.")

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
            "max_loss_probability", data={"max_loss_probability": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _drawdown_probability_impl(
    returns_in: pd.Series | np.ndarray, threshold_pct: float
) -> dict[str, Any]:
    """AI Tool wrapper for _drawdown_probability_impl."""
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

        arg_threshold_pct = threshold_pct
        if "threshold_pct" in ["trades", "open_trades"] and isinstance(
            arg_threshold_pct, (list, dict)
        ):
            arg_threshold_pct = pd.DataFrame(arg_threshold_pct)
        elif "threshold_pct" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_threshold_pct, list):
            arg_threshold_pct = pd.Series(arg_threshold_pct)
        kwargs["threshold_pct"] = arg_threshold_pct

        res = _drawdown_probability_impl(**kwargs)
        logger.info("Executed drawdown_probability tool successfully.")

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
            "drawdown_probability", data={"drawdown_probability": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _risk_of_ruin_impl(
    trades: pd.DataFrame,
    risk_per_trade_pct: float | None = None,
    target_drawdown_pct: float = 50.0,
    num_simulations: int = 10000,
    **kwargs,
) -> dict[str, Any]:
    """AI Tool wrapper for _risk_of_ruin_impl."""
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

        arg_risk_per_trade_pct = risk_per_trade_pct
        if "risk_per_trade_pct" in ["trades", "open_trades"] and isinstance(
            arg_risk_per_trade_pct, (list, dict)
        ):
            arg_risk_per_trade_pct = pd.DataFrame(arg_risk_per_trade_pct)
        elif "risk_per_trade_pct" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_risk_per_trade_pct, list):
            arg_risk_per_trade_pct = pd.Series(arg_risk_per_trade_pct)
        kwargs["risk_per_trade_pct"] = arg_risk_per_trade_pct

        arg_target_drawdown_pct = target_drawdown_pct
        if "target_drawdown_pct" in ["trades", "open_trades"] and isinstance(
            arg_target_drawdown_pct, (list, dict)
        ):
            arg_target_drawdown_pct = pd.DataFrame(arg_target_drawdown_pct)
        elif "target_drawdown_pct" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_target_drawdown_pct, list):
            arg_target_drawdown_pct = pd.Series(arg_target_drawdown_pct)
        kwargs["target_drawdown_pct"] = arg_target_drawdown_pct

        arg_num_simulations = num_simulations
        if "num_simulations" in ["trades", "open_trades"] and isinstance(
            arg_num_simulations, (list, dict)
        ):
            arg_num_simulations = pd.DataFrame(arg_num_simulations)
        elif "num_simulations" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_num_simulations, list):
            arg_num_simulations = pd.Series(arg_num_simulations)
        kwargs["num_simulations"] = arg_num_simulations

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

        res = _risk_of_ruin_impl(**kwargs)
        logger.info("Executed risk_of_ruin tool successfully.")

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
            "risk_of_ruin", data={"risk_of_ruin": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _max_nominal_exposure_simple_impl(
    trades: pd.DataFrame, contract_size: float = 100000.0
) -> dict[str, Any]:
    """AI Tool wrapper for _max_nominal_exposure_simple_impl."""
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

        arg_contract_size = contract_size
        if "contract_size" in ["trades", "open_trades"] and isinstance(
            arg_contract_size, (list, dict)
        ):
            arg_contract_size = pd.DataFrame(arg_contract_size)
        elif "contract_size" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_contract_size, list):
            arg_contract_size = pd.Series(arg_contract_size)
        kwargs["contract_size"] = arg_contract_size

        res = _max_nominal_exposure_simple_impl(**kwargs)
        logger.info("Executed max_nominal_exposure_simple tool successfully.")

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
            "max_nominal_exposure_simple",
            data={"max_nominal_exposure_simple": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _max_gross_exposure_impl(
    trades: pd.DataFrame, contract_size: float = 100000.0
) -> dict[str, Any]:
    """AI Tool wrapper for _max_gross_exposure_impl."""
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

        arg_contract_size = contract_size
        if "contract_size" in ["trades", "open_trades"] and isinstance(
            arg_contract_size, (list, dict)
        ):
            arg_contract_size = pd.DataFrame(arg_contract_size)
        elif "contract_size" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_contract_size, list):
            arg_contract_size = pd.Series(arg_contract_size)
        kwargs["contract_size"] = arg_contract_size

        res = _max_gross_exposure_impl(**kwargs)
        logger.info("Executed max_gross_exposure tool successfully.")

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
            "max_gross_exposure", data={"max_gross_exposure": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _avg_trade_nominal_exposure_impl(
    trades: pd.DataFrame, contract_size: float = 100000.0
) -> dict[str, Any]:
    """AI Tool wrapper for _avg_trade_nominal_exposure_impl."""
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

        arg_contract_size = contract_size
        if "contract_size" in ["trades", "open_trades"] and isinstance(
            arg_contract_size, (list, dict)
        ):
            arg_contract_size = pd.DataFrame(arg_contract_size)
        elif "contract_size" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_contract_size, list):
            arg_contract_size = pd.Series(arg_contract_size)
        kwargs["contract_size"] = arg_contract_size

        res = _avg_trade_nominal_exposure_impl(**kwargs)
        logger.info("Executed avg_trade_nominal_exposure tool successfully.")

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
            "avg_trade_nominal_exposure",
            data={"avg_trade_nominal_exposure": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _exposure_time_ratio_impl(
    trades: pd.DataFrame,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _exposure_time_ratio_impl."""
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

        res = _exposure_time_ratio_impl(**kwargs)
        logger.info("Executed exposure_time_ratio tool successfully.")

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
            "exposure_time_ratio", data={"exposure_time_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _max_single_trade_margin_utilization_impl(
    trades: pd.DataFrame, account_equity: float
) -> dict[str, Any]:
    """AI Tool wrapper for _max_single_trade_margin_utilization_impl."""
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

        arg_account_equity = account_equity
        if "account_equity" in ["trades", "open_trades"] and isinstance(
            arg_account_equity, (list, dict)
        ):
            arg_account_equity = pd.DataFrame(arg_account_equity)
        elif "account_equity" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_account_equity, list):
            arg_account_equity = pd.Series(arg_account_equity)
        kwargs["account_equity"] = arg_account_equity

        res = _max_single_trade_margin_utilization_impl(**kwargs)
        logger.info("Executed max_single_trade_margin_utilization tool successfully.")

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
            "max_single_trade_margin_utilization",
            data={"max_single_trade_margin_utilization": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _avg_single_trade_margin_utilization_impl(
    trades: pd.DataFrame, account_equity: float
) -> dict[str, Any]:
    """AI Tool wrapper for _avg_single_trade_margin_utilization_impl."""
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

        arg_account_equity = account_equity
        if "account_equity" in ["trades", "open_trades"] and isinstance(
            arg_account_equity, (list, dict)
        ):
            arg_account_equity = pd.DataFrame(arg_account_equity)
        elif "account_equity" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_account_equity, list):
            arg_account_equity = pd.Series(arg_account_equity)
        kwargs["account_equity"] = arg_account_equity

        res = _avg_single_trade_margin_utilization_impl(**kwargs)
        logger.info("Executed avg_single_trade_margin_utilization tool successfully.")

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
            "avg_single_trade_margin_utilization",
            data={"avg_single_trade_margin_utilization": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _time_weighted_avg_exposure_impl(
    trades: pd.DataFrame,
    contract_size: float = 100000.0,
    end_time: pd.Timestamp | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _time_weighted_avg_exposure_impl."""
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

        arg_contract_size = contract_size
        if "contract_size" in ["trades", "open_trades"] and isinstance(
            arg_contract_size, (list, dict)
        ):
            arg_contract_size = pd.DataFrame(arg_contract_size)
        elif "contract_size" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_contract_size, list):
            arg_contract_size = pd.Series(arg_contract_size)
        kwargs["contract_size"] = arg_contract_size

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

        res = _time_weighted_avg_exposure_impl(**kwargs)
        logger.info("Executed time_weighted_avg_exposure tool successfully.")

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
            "time_weighted_avg_exposure",
            data={"time_weighted_avg_exposure": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _portfolio_margin_utilization_curve_impl(
    trades: pd.DataFrame, account_equity: float, end_time: pd.Timestamp | None = None
) -> dict[str, Any]:
    """AI Tool wrapper for _portfolio_margin_utilization_curve_impl."""
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

        arg_account_equity = account_equity
        if "account_equity" in ["trades", "open_trades"] and isinstance(
            arg_account_equity, (list, dict)
        ):
            arg_account_equity = pd.DataFrame(arg_account_equity)
        elif "account_equity" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_account_equity, list):
            arg_account_equity = pd.Series(arg_account_equity)
        kwargs["account_equity"] = arg_account_equity

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

        res = _portfolio_margin_utilization_curve_impl(**kwargs)
        logger.info("Executed portfolio_margin_utilization_curve tool successfully.")

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
            "portfolio_margin_utilization_curve",
            data={"portfolio_margin_utilization_curve": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _compounding_risk_of_ruin_impl(
    trades: pd.DataFrame,
    risk_fraction: float,
    target_drawdown_pct: float = 50.0,
    num_simulations: int = 10000,
) -> dict[str, Any]:
    """AI Tool wrapper for _compounding_risk_of_ruin_impl."""
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

        arg_risk_fraction = risk_fraction
        if "risk_fraction" in ["trades", "open_trades"] and isinstance(
            arg_risk_fraction, (list, dict)
        ):
            arg_risk_fraction = pd.DataFrame(arg_risk_fraction)
        elif "risk_fraction" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_risk_fraction, list):
            arg_risk_fraction = pd.Series(arg_risk_fraction)
        kwargs["risk_fraction"] = arg_risk_fraction

        arg_target_drawdown_pct = target_drawdown_pct
        if "target_drawdown_pct" in ["trades", "open_trades"] and isinstance(
            arg_target_drawdown_pct, (list, dict)
        ):
            arg_target_drawdown_pct = pd.DataFrame(arg_target_drawdown_pct)
        elif "target_drawdown_pct" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_target_drawdown_pct, list):
            arg_target_drawdown_pct = pd.Series(arg_target_drawdown_pct)
        kwargs["target_drawdown_pct"] = arg_target_drawdown_pct

        arg_num_simulations = num_simulations
        if "num_simulations" in ["trades", "open_trades"] and isinstance(
            arg_num_simulations, (list, dict)
        ):
            arg_num_simulations = pd.DataFrame(arg_num_simulations)
        elif "num_simulations" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_num_simulations, list):
            arg_num_simulations = pd.Series(arg_num_simulations)
        kwargs["num_simulations"] = arg_num_simulations

        res = _compounding_risk_of_ruin_impl(**kwargs)
        logger.info("Executed compounding_risk_of_ruin tool successfully.")

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
            "compounding_risk_of_ruin", data={"compounding_risk_of_ruin": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _risk_of_ruin_with_custom_horizon_impl(
    trades: pd.DataFrame,
    risk_per_trade_pct: float,
    horizon: int,
    target_drawdown_pct: float = 50.0,
    num_simulations: int = 10000,
) -> dict[str, Any]:
    """AI Tool wrapper for _risk_of_ruin_with_custom_horizon_impl."""
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

        arg_risk_per_trade_pct = risk_per_trade_pct
        if "risk_per_trade_pct" in ["trades", "open_trades"] and isinstance(
            arg_risk_per_trade_pct, (list, dict)
        ):
            arg_risk_per_trade_pct = pd.DataFrame(arg_risk_per_trade_pct)
        elif "risk_per_trade_pct" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_risk_per_trade_pct, list):
            arg_risk_per_trade_pct = pd.Series(arg_risk_per_trade_pct)
        kwargs["risk_per_trade_pct"] = arg_risk_per_trade_pct

        arg_horizon = horizon
        if "horizon" in ["trades", "open_trades"] and isinstance(
            arg_horizon, (list, dict)
        ):
            arg_horizon = pd.DataFrame(arg_horizon)
        elif "horizon" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_horizon, list):
            arg_horizon = pd.Series(arg_horizon)
        kwargs["horizon"] = arg_horizon

        arg_target_drawdown_pct = target_drawdown_pct
        if "target_drawdown_pct" in ["trades", "open_trades"] and isinstance(
            arg_target_drawdown_pct, (list, dict)
        ):
            arg_target_drawdown_pct = pd.DataFrame(arg_target_drawdown_pct)
        elif "target_drawdown_pct" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_target_drawdown_pct, list):
            arg_target_drawdown_pct = pd.Series(arg_target_drawdown_pct)
        kwargs["target_drawdown_pct"] = arg_target_drawdown_pct

        arg_num_simulations = num_simulations
        if "num_simulations" in ["trades", "open_trades"] and isinstance(
            arg_num_simulations, (list, dict)
        ):
            arg_num_simulations = pd.DataFrame(arg_num_simulations)
        elif "num_simulations" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_num_simulations, list):
            arg_num_simulations = pd.Series(arg_num_simulations)
        kwargs["num_simulations"] = arg_num_simulations

        res = _risk_of_ruin_with_custom_horizon_impl(**kwargs)
        logger.info("Executed risk_of_ruin_with_custom_horizon tool successfully.")

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
            "risk_of_ruin_with_custom_horizon",
            data={"risk_of_ruin_with_custom_horizon": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _historical_var_by_symbol_impl(
    trades: pd.DataFrame, confidence: float = 0.95
) -> dict[str, Any]:
    """AI Tool wrapper for _historical_var_by_symbol_impl."""
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

        arg_confidence = confidence
        if "confidence" in ["trades", "open_trades"] and isinstance(
            arg_confidence, (list, dict)
        ):
            arg_confidence = pd.DataFrame(arg_confidence)
        elif "confidence" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_confidence, list):
            arg_confidence = pd.Series(arg_confidence)
        kwargs["confidence"] = arg_confidence

        res = _historical_var_by_symbol_impl(**kwargs)
        logger.info("Executed historical_var_by_symbol tool successfully.")

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
            "historical_var_by_symbol", data={"historical_var_by_symbol": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _portfolio_var_from_covariance_impl(
    returns_df: pd.DataFrame,
    weights: np.ndarray | None = None,
    confidence: float = 0.95,
) -> dict[str, Any]:
    """AI Tool wrapper for _portfolio_var_from_covariance_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_returns_df = returns_df
        if "returns_df" in ["trades", "open_trades"] and isinstance(
            arg_returns_df, (list, dict)
        ):
            arg_returns_df = pd.DataFrame(arg_returns_df)
        elif "returns_df" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_returns_df, list):
            arg_returns_df = pd.Series(arg_returns_df)
        kwargs["returns_df"] = arg_returns_df

        arg_weights = weights
        if "weights" in ["trades", "open_trades"] and isinstance(
            arg_weights, (list, dict)
        ):
            arg_weights = pd.DataFrame(arg_weights)
        elif "weights" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_weights, list):
            arg_weights = pd.Series(arg_weights)
        kwargs["weights"] = arg_weights

        arg_confidence = confidence
        if "confidence" in ["trades", "open_trades"] and isinstance(
            arg_confidence, (list, dict)
        ):
            arg_confidence = pd.DataFrame(arg_confidence)
        elif "confidence" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_confidence, list):
            arg_confidence = pd.Series(arg_confidence)
        kwargs["confidence"] = arg_confidence

        res = _portfolio_var_from_covariance_impl(**kwargs)
        logger.info("Executed portfolio_var_from_covariance tool successfully.")

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
            "portfolio_var_from_covariance",
            data={"portfolio_var_from_covariance": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _calculate_risk_metrics_impl(
    *,
    returns: list[float],
    alpha: float = 0.05,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_risk_metrics_impl."""
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

        arg_alpha = alpha
        if "alpha" in ["trades", "open_trades"] and isinstance(arg_alpha, (list, dict)):
            arg_alpha = pd.DataFrame(arg_alpha)
        elif "alpha" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_alpha, list):
            arg_alpha = pd.Series(arg_alpha)
        kwargs["alpha"] = arg_alpha

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

        res = _calculate_risk_metrics_impl(**kwargs)
        logger.info("Executed calculate_risk_metrics tool successfully.")

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
            "calculate_risk_metrics", data={"calculate_risk_metrics": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def volatility(rets: pd.Series | np.ndarray) -> dict[str, Any]:
    """AI Tool wrapper for _volatility_impl."""
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

        res = _volatility_impl(**kwargs)
        logger.info("Executed volatility tool successfully.")

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

        return analytics_tool_result("volatility", data={"volatility": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def annualized_volatility(
    rets: pd.Series | np.ndarray, periods_per_year: int = 252
) -> dict[str, Any]:
    """AI Tool wrapper for _annualized_volatility_impl."""
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

        res = _annualized_volatility_impl(**kwargs)
        logger.info("Executed annualized_volatility tool successfully.")

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
            "annualized_volatility", data={"annualized_volatility": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def downside_volatility(
    rets: pd.Series | np.ndarray, target: float = 0.0
) -> dict[str, Any]:
    """AI Tool wrapper for _downside_volatility_impl."""
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

        res = _downside_volatility_impl(**kwargs)
        logger.info("Executed downside_volatility tool successfully.")

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
            "downside_volatility", data={"downside_volatility": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def value_at_risk(
    rets: pd.Series | np.ndarray,
    confidence: float = 0.95,
    method: Literal["historical", "parametric"] = "historical",
) -> dict[str, Any]:
    """AI Tool wrapper for _value_at_risk_impl."""
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

        arg_confidence = confidence
        if "confidence" in ["trades", "open_trades"] and isinstance(
            arg_confidence, (list, dict)
        ):
            arg_confidence = pd.DataFrame(arg_confidence)
        elif "confidence" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_confidence, list):
            arg_confidence = pd.Series(arg_confidence)
        kwargs["confidence"] = arg_confidence

        arg_method = method
        if "method" in ["trades", "open_trades"] and isinstance(
            arg_method, (list, dict)
        ):
            arg_method = pd.DataFrame(arg_method)
        elif "method" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_method, list):
            arg_method = pd.Series(arg_method)
        kwargs["method"] = arg_method

        res = _value_at_risk_impl(**kwargs)
        logger.info("Executed value_at_risk tool successfully.")

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
            "value_at_risk", data={"value_at_risk": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def conditional_var(
    rets: pd.Series | np.ndarray, confidence: float = 0.95
) -> dict[str, Any]:
    """AI Tool wrapper for _conditional_var_impl."""
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

        arg_confidence = confidence
        if "confidence" in ["trades", "open_trades"] and isinstance(
            arg_confidence, (list, dict)
        ):
            arg_confidence = pd.DataFrame(arg_confidence)
        elif "confidence" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_confidence, list):
            arg_confidence = pd.Series(arg_confidence)
        kwargs["confidence"] = arg_confidence

        res = _conditional_var_impl(**kwargs)
        logger.info("Executed conditional_var tool successfully.")

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
            "conditional_var", data={"conditional_var": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def expected_shortfall(
    rets: pd.Series | np.ndarray, confidence: float = 0.95
) -> dict[str, Any]:
    """AI Tool wrapper for _expected_shortfall_impl."""
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

        arg_confidence = confidence
        if "confidence" in ["trades", "open_trades"] and isinstance(
            arg_confidence, (list, dict)
        ):
            arg_confidence = pd.DataFrame(arg_confidence)
        elif "confidence" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_confidence, list):
            arg_confidence = pd.Series(arg_confidence)
        kwargs["confidence"] = arg_confidence

        res = _expected_shortfall_impl(**kwargs)
        logger.info("Executed expected_shortfall tool successfully.")

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
            "expected_shortfall", data={"expected_shortfall": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_loss_probability(
    trades: pd.DataFrame, loss_threshold_r: float = -1.0
) -> dict[str, Any]:
    """AI Tool wrapper for _max_loss_probability_impl."""
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

        arg_loss_threshold_r = loss_threshold_r
        if "loss_threshold_r" in ["trades", "open_trades"] and isinstance(
            arg_loss_threshold_r, (list, dict)
        ):
            arg_loss_threshold_r = pd.DataFrame(arg_loss_threshold_r)
        elif "loss_threshold_r" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_loss_threshold_r, list):
            arg_loss_threshold_r = pd.Series(arg_loss_threshold_r)
        kwargs["loss_threshold_r"] = arg_loss_threshold_r

        res = _max_loss_probability_impl(**kwargs)
        logger.info("Executed max_loss_probability tool successfully.")

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
            "max_loss_probability", data={"max_loss_probability": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def drawdown_probability(
    returns_in: pd.Series | np.ndarray, threshold_pct: float
) -> dict[str, Any]:
    """AI Tool wrapper for _drawdown_probability_impl."""
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

        arg_threshold_pct = threshold_pct
        if "threshold_pct" in ["trades", "open_trades"] and isinstance(
            arg_threshold_pct, (list, dict)
        ):
            arg_threshold_pct = pd.DataFrame(arg_threshold_pct)
        elif "threshold_pct" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_threshold_pct, list):
            arg_threshold_pct = pd.Series(arg_threshold_pct)
        kwargs["threshold_pct"] = arg_threshold_pct

        res = _drawdown_probability_impl(**kwargs)
        logger.info("Executed drawdown_probability tool successfully.")

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
            "drawdown_probability", data={"drawdown_probability": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def risk_of_ruin(
    trades: pd.DataFrame,
    risk_per_trade_pct: float | None = None,
    target_drawdown_pct: float = 50.0,
    num_simulations: int = 10000,
    **kwargs,
) -> dict[str, Any]:
    """AI Tool wrapper for _risk_of_ruin_impl."""
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

        arg_risk_per_trade_pct = risk_per_trade_pct
        if "risk_per_trade_pct" in ["trades", "open_trades"] and isinstance(
            arg_risk_per_trade_pct, (list, dict)
        ):
            arg_risk_per_trade_pct = pd.DataFrame(arg_risk_per_trade_pct)
        elif "risk_per_trade_pct" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_risk_per_trade_pct, list):
            arg_risk_per_trade_pct = pd.Series(arg_risk_per_trade_pct)
        kwargs["risk_per_trade_pct"] = arg_risk_per_trade_pct

        arg_target_drawdown_pct = target_drawdown_pct
        if "target_drawdown_pct" in ["trades", "open_trades"] and isinstance(
            arg_target_drawdown_pct, (list, dict)
        ):
            arg_target_drawdown_pct = pd.DataFrame(arg_target_drawdown_pct)
        elif "target_drawdown_pct" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_target_drawdown_pct, list):
            arg_target_drawdown_pct = pd.Series(arg_target_drawdown_pct)
        kwargs["target_drawdown_pct"] = arg_target_drawdown_pct

        arg_num_simulations = num_simulations
        if "num_simulations" in ["trades", "open_trades"] and isinstance(
            arg_num_simulations, (list, dict)
        ):
            arg_num_simulations = pd.DataFrame(arg_num_simulations)
        elif "num_simulations" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_num_simulations, list):
            arg_num_simulations = pd.Series(arg_num_simulations)
        kwargs["num_simulations"] = arg_num_simulations

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

        res = _risk_of_ruin_impl(**kwargs)
        logger.info("Executed risk_of_ruin tool successfully.")

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
            "risk_of_ruin", data={"risk_of_ruin": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_nominal_exposure_simple(
    trades: pd.DataFrame, contract_size: float = 100000.0
) -> dict[str, Any]:
    """AI Tool wrapper for _max_nominal_exposure_simple_impl."""
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

        arg_contract_size = contract_size
        if "contract_size" in ["trades", "open_trades"] and isinstance(
            arg_contract_size, (list, dict)
        ):
            arg_contract_size = pd.DataFrame(arg_contract_size)
        elif "contract_size" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_contract_size, list):
            arg_contract_size = pd.Series(arg_contract_size)
        kwargs["contract_size"] = arg_contract_size

        res = _max_nominal_exposure_simple_impl(**kwargs)
        logger.info("Executed max_nominal_exposure_simple tool successfully.")

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
            "max_nominal_exposure_simple",
            data={"max_nominal_exposure_simple": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_gross_exposure(
    trades: pd.DataFrame, contract_size: float = 100000.0
) -> dict[str, Any]:
    """AI Tool wrapper for _max_gross_exposure_impl."""
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

        arg_contract_size = contract_size
        if "contract_size" in ["trades", "open_trades"] and isinstance(
            arg_contract_size, (list, dict)
        ):
            arg_contract_size = pd.DataFrame(arg_contract_size)
        elif "contract_size" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_contract_size, list):
            arg_contract_size = pd.Series(arg_contract_size)
        kwargs["contract_size"] = arg_contract_size

        res = _max_gross_exposure_impl(**kwargs)
        logger.info("Executed max_gross_exposure tool successfully.")

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
            "max_gross_exposure", data={"max_gross_exposure": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def avg_trade_nominal_exposure(
    trades: pd.DataFrame, contract_size: float = 100000.0
) -> dict[str, Any]:
    """AI Tool wrapper for _avg_trade_nominal_exposure_impl."""
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

        arg_contract_size = contract_size
        if "contract_size" in ["trades", "open_trades"] and isinstance(
            arg_contract_size, (list, dict)
        ):
            arg_contract_size = pd.DataFrame(arg_contract_size)
        elif "contract_size" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_contract_size, list):
            arg_contract_size = pd.Series(arg_contract_size)
        kwargs["contract_size"] = arg_contract_size

        res = _avg_trade_nominal_exposure_impl(**kwargs)
        logger.info("Executed avg_trade_nominal_exposure tool successfully.")

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
            "avg_trade_nominal_exposure",
            data={"avg_trade_nominal_exposure": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def exposure_time_ratio(
    trades: pd.DataFrame,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _exposure_time_ratio_impl."""
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

        res = _exposure_time_ratio_impl(**kwargs)
        logger.info("Executed exposure_time_ratio tool successfully.")

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
            "exposure_time_ratio", data={"exposure_time_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_single_trade_margin_utilization(
    trades: pd.DataFrame, account_equity: float
) -> dict[str, Any]:
    """AI Tool wrapper for _max_single_trade_margin_utilization_impl."""
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

        arg_account_equity = account_equity
        if "account_equity" in ["trades", "open_trades"] and isinstance(
            arg_account_equity, (list, dict)
        ):
            arg_account_equity = pd.DataFrame(arg_account_equity)
        elif "account_equity" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_account_equity, list):
            arg_account_equity = pd.Series(arg_account_equity)
        kwargs["account_equity"] = arg_account_equity

        res = _max_single_trade_margin_utilization_impl(**kwargs)
        logger.info("Executed max_single_trade_margin_utilization tool successfully.")

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
            "max_single_trade_margin_utilization",
            data={"max_single_trade_margin_utilization": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def avg_single_trade_margin_utilization(
    trades: pd.DataFrame, account_equity: float
) -> dict[str, Any]:
    """AI Tool wrapper for _avg_single_trade_margin_utilization_impl."""
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

        arg_account_equity = account_equity
        if "account_equity" in ["trades", "open_trades"] and isinstance(
            arg_account_equity, (list, dict)
        ):
            arg_account_equity = pd.DataFrame(arg_account_equity)
        elif "account_equity" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_account_equity, list):
            arg_account_equity = pd.Series(arg_account_equity)
        kwargs["account_equity"] = arg_account_equity

        res = _avg_single_trade_margin_utilization_impl(**kwargs)
        logger.info("Executed avg_single_trade_margin_utilization tool successfully.")

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
            "avg_single_trade_margin_utilization",
            data={"avg_single_trade_margin_utilization": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def time_weighted_avg_exposure(
    trades: pd.DataFrame,
    contract_size: float = 100000.0,
    end_time: pd.Timestamp | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _time_weighted_avg_exposure_impl."""
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

        arg_contract_size = contract_size
        if "contract_size" in ["trades", "open_trades"] and isinstance(
            arg_contract_size, (list, dict)
        ):
            arg_contract_size = pd.DataFrame(arg_contract_size)
        elif "contract_size" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_contract_size, list):
            arg_contract_size = pd.Series(arg_contract_size)
        kwargs["contract_size"] = arg_contract_size

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

        res = _time_weighted_avg_exposure_impl(**kwargs)
        logger.info("Executed time_weighted_avg_exposure tool successfully.")

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
            "time_weighted_avg_exposure",
            data={"time_weighted_avg_exposure": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def portfolio_margin_utilization_curve(
    trades: pd.DataFrame, account_equity: float, end_time: pd.Timestamp | None = None
) -> dict[str, Any]:
    """AI Tool wrapper for _portfolio_margin_utilization_curve_impl."""
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

        arg_account_equity = account_equity
        if "account_equity" in ["trades", "open_trades"] and isinstance(
            arg_account_equity, (list, dict)
        ):
            arg_account_equity = pd.DataFrame(arg_account_equity)
        elif "account_equity" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_account_equity, list):
            arg_account_equity = pd.Series(arg_account_equity)
        kwargs["account_equity"] = arg_account_equity

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

        res = _portfolio_margin_utilization_curve_impl(**kwargs)
        logger.info("Executed portfolio_margin_utilization_curve tool successfully.")

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
            "portfolio_margin_utilization_curve",
            data={"portfolio_margin_utilization_curve": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def compounding_risk_of_ruin(
    trades: pd.DataFrame,
    risk_fraction: float,
    target_drawdown_pct: float = 50.0,
    num_simulations: int = 10000,
) -> dict[str, Any]:
    """AI Tool wrapper for _compounding_risk_of_ruin_impl."""
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

        arg_risk_fraction = risk_fraction
        if "risk_fraction" in ["trades", "open_trades"] and isinstance(
            arg_risk_fraction, (list, dict)
        ):
            arg_risk_fraction = pd.DataFrame(arg_risk_fraction)
        elif "risk_fraction" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_risk_fraction, list):
            arg_risk_fraction = pd.Series(arg_risk_fraction)
        kwargs["risk_fraction"] = arg_risk_fraction

        arg_target_drawdown_pct = target_drawdown_pct
        if "target_drawdown_pct" in ["trades", "open_trades"] and isinstance(
            arg_target_drawdown_pct, (list, dict)
        ):
            arg_target_drawdown_pct = pd.DataFrame(arg_target_drawdown_pct)
        elif "target_drawdown_pct" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_target_drawdown_pct, list):
            arg_target_drawdown_pct = pd.Series(arg_target_drawdown_pct)
        kwargs["target_drawdown_pct"] = arg_target_drawdown_pct

        arg_num_simulations = num_simulations
        if "num_simulations" in ["trades", "open_trades"] and isinstance(
            arg_num_simulations, (list, dict)
        ):
            arg_num_simulations = pd.DataFrame(arg_num_simulations)
        elif "num_simulations" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_num_simulations, list):
            arg_num_simulations = pd.Series(arg_num_simulations)
        kwargs["num_simulations"] = arg_num_simulations

        res = _compounding_risk_of_ruin_impl(**kwargs)
        logger.info("Executed compounding_risk_of_ruin tool successfully.")

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
            "compounding_risk_of_ruin", data={"compounding_risk_of_ruin": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def risk_of_ruin_with_custom_horizon(
    trades: pd.DataFrame,
    risk_per_trade_pct: float,
    horizon: int,
    target_drawdown_pct: float = 50.0,
    num_simulations: int = 10000,
) -> dict[str, Any]:
    """AI Tool wrapper for _risk_of_ruin_with_custom_horizon_impl."""
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

        arg_risk_per_trade_pct = risk_per_trade_pct
        if "risk_per_trade_pct" in ["trades", "open_trades"] and isinstance(
            arg_risk_per_trade_pct, (list, dict)
        ):
            arg_risk_per_trade_pct = pd.DataFrame(arg_risk_per_trade_pct)
        elif "risk_per_trade_pct" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_risk_per_trade_pct, list):
            arg_risk_per_trade_pct = pd.Series(arg_risk_per_trade_pct)
        kwargs["risk_per_trade_pct"] = arg_risk_per_trade_pct

        arg_horizon = horizon
        if "horizon" in ["trades", "open_trades"] and isinstance(
            arg_horizon, (list, dict)
        ):
            arg_horizon = pd.DataFrame(arg_horizon)
        elif "horizon" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_horizon, list):
            arg_horizon = pd.Series(arg_horizon)
        kwargs["horizon"] = arg_horizon

        arg_target_drawdown_pct = target_drawdown_pct
        if "target_drawdown_pct" in ["trades", "open_trades"] and isinstance(
            arg_target_drawdown_pct, (list, dict)
        ):
            arg_target_drawdown_pct = pd.DataFrame(arg_target_drawdown_pct)
        elif "target_drawdown_pct" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_target_drawdown_pct, list):
            arg_target_drawdown_pct = pd.Series(arg_target_drawdown_pct)
        kwargs["target_drawdown_pct"] = arg_target_drawdown_pct

        arg_num_simulations = num_simulations
        if "num_simulations" in ["trades", "open_trades"] and isinstance(
            arg_num_simulations, (list, dict)
        ):
            arg_num_simulations = pd.DataFrame(arg_num_simulations)
        elif "num_simulations" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_num_simulations, list):
            arg_num_simulations = pd.Series(arg_num_simulations)
        kwargs["num_simulations"] = arg_num_simulations

        res = _risk_of_ruin_with_custom_horizon_impl(**kwargs)
        logger.info("Executed risk_of_ruin_with_custom_horizon tool successfully.")

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
            "risk_of_ruin_with_custom_horizon",
            data={"risk_of_ruin_with_custom_horizon": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def historical_var_by_symbol(
    trades: pd.DataFrame, confidence: float = 0.95
) -> dict[str, Any]:
    """AI Tool wrapper for _historical_var_by_symbol_impl."""
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

        arg_confidence = confidence
        if "confidence" in ["trades", "open_trades"] and isinstance(
            arg_confidence, (list, dict)
        ):
            arg_confidence = pd.DataFrame(arg_confidence)
        elif "confidence" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_confidence, list):
            arg_confidence = pd.Series(arg_confidence)
        kwargs["confidence"] = arg_confidence

        res = _historical_var_by_symbol_impl(**kwargs)
        logger.info("Executed historical_var_by_symbol tool successfully.")

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
            "historical_var_by_symbol", data={"historical_var_by_symbol": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def portfolio_var_from_covariance(
    returns_df: pd.DataFrame,
    weights: np.ndarray | None = None,
    confidence: float = 0.95,
) -> dict[str, Any]:
    """AI Tool wrapper for _portfolio_var_from_covariance_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_returns_df = returns_df
        if "returns_df" in ["trades", "open_trades"] and isinstance(
            arg_returns_df, (list, dict)
        ):
            arg_returns_df = pd.DataFrame(arg_returns_df)
        elif "returns_df" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_returns_df, list):
            arg_returns_df = pd.Series(arg_returns_df)
        kwargs["returns_df"] = arg_returns_df

        arg_weights = weights
        if "weights" in ["trades", "open_trades"] and isinstance(
            arg_weights, (list, dict)
        ):
            arg_weights = pd.DataFrame(arg_weights)
        elif "weights" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_weights, list):
            arg_weights = pd.Series(arg_weights)
        kwargs["weights"] = arg_weights

        arg_confidence = confidence
        if "confidence" in ["trades", "open_trades"] and isinstance(
            arg_confidence, (list, dict)
        ):
            arg_confidence = pd.DataFrame(arg_confidence)
        elif "confidence" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_confidence, list):
            arg_confidence = pd.Series(arg_confidence)
        kwargs["confidence"] = arg_confidence

        res = _portfolio_var_from_covariance_impl(**kwargs)
        logger.info("Executed portfolio_var_from_covariance tool successfully.")

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
            "portfolio_var_from_covariance",
            data={"portfolio_var_from_covariance": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def calculate_risk_metrics(
    *,
    returns: list[float],
    alpha: float = 0.05,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_risk_metrics_impl."""
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

        arg_alpha = alpha
        if "alpha" in ["trades", "open_trades"] and isinstance(arg_alpha, (list, dict)):
            arg_alpha = pd.DataFrame(arg_alpha)
        elif "alpha" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_alpha, list):
            arg_alpha = pd.Series(arg_alpha)
        kwargs["alpha"] = arg_alpha

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

        res = _calculate_risk_metrics_impl(**kwargs)
        logger.info("Executed calculate_risk_metrics tool successfully.")

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
            "calculate_risk_metrics", data={"calculate_risk_metrics": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}
