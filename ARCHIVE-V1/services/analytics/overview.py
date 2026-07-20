"""overview.py - Orchestrate analytics modules into overview payloads, reports, dashboards, and cost-impact tools.

Classes:
    None.

Functions:
    _format_duration: Format duration into 'Xd Yh' format.
    _normalize_trades: Ensure trades are in a DataFrame with consistent column names.
    _extract_proxy_benchmark: Try to extract a proxy price series from trades if no benchmark is provided.
    _periods_to_timedelta: Convert a number of periods/bars to a Timedelta based on index frequency.
    calculate_analytics_for_subset: Calculate ALL analytics categories for a specific subset of trades.
    get_analytics_overview: Calculate comprehensive analytics across all categories in parallel subsets.
    format_summary_as_rows: Format raw summary data into display rows for reports.
    _get_dashboard_metrics: Extract a curated set of key performance indicators for the primary dashboard, with Long/Short support.
    build_overview_payload: Build the full analytics payload for the API including charts.
    _cost_impact: Calculate total cost and its ratio to gross profit.
    calculate_spread_cost_impact: Calculate spread cost drag.
    calculate_slippage_impact: Calculate slippage cost drag.
    calculate_commission_impact: Calculate commission cost drag.
    build_backtest_report: Build a structured backtest analytics report payload.

Nested functions and methods:
    get_analytics_overview._to_python_types: Convert pandas and NumPy values into JSON-safe Python primitives.
    format_summary_as_rows._fmt_num: Format a numeric value with a fixed decimal count.
    _get_dashboard_metrics.get_3way: Read an all/long/short metric triplet from analytics data.
    _get_dashboard_metrics.build_category: Build a dashboard category from configured analytics metrics.
    build_overview_payload._get_subset_curves: Build equity and drawdown percentage curves for a trade subset.
    build_overview_payload._merge_to_list: Merge all/long/short series into chart rows keyed by date.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from . import (
    benchmark,
    decision_scorecard,
    distributions,
    drawdowns,
    efficiency,
    metrics,
    ratios,
    returns,
    risks,
    statistical_tests,
)
from .common import analytics_business_payload, analytics_tool_result

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
# Utility & Normalization
# =========================================================================


def _format_duration(td_or_hours: Any) -> str:
    """Format duration into 'Xd Yh' format."""
    if pd.isna(td_or_hours):
        return "0h"

    if isinstance(td_or_hours, (pd.Timedelta, pd._libs.tslibs.timedeltas.Timedelta)):
        total_seconds = td_or_hours.total_seconds()
    elif isinstance(td_or_hours, (int, float, np.float64, np.int64)):
        total_seconds = float(td_or_hours) * 3600.0
    else:
        try:
            td = pd.to_timedelta(td_or_hours)
            total_seconds = td.total_seconds()
        except:
            return str(td_or_hours)

    hours = total_seconds / 3600.0
    if hours <= 0:
        return "0h"

    days = int(hours // 24)
    rem_hours = int(round(hours % 24))

    if rem_hours == 24:
        days += 1
        rem_hours = 0

    if days > 0:
        return f"{days}d {rem_hours}h"
    return f"{rem_hours}h"


def _normalize_trades(trades: Any) -> pd.DataFrame:
    """Ensure trades are in a DataFrame with consistent column names."""
    if isinstance(trades, pd.DataFrame):
        df = trades.copy()
    else:
        from dataclasses import asdict, is_dataclass

        rows = []
        for t in trades:
            if is_dataclass(t):
                rows.append(asdict(t))
            elif hasattr(t, "to_dict"):
                rows.append(t.to_dict())
            elif isinstance(t, dict):
                rows.append(dict(t))
            else:
                continue
        df = pd.DataFrame(rows)

    if df.empty:
        # Guarantee minimum columns for empty DF to avoid KeyErrors downstream
        # especially 'type' which is used for subset slicing
        for col in [
            "type",
            "profit_loss",
            "size",
            "time_in_trade",
            "r_multiple",
            "mfe_usd",
            "mae_usd",
            "open_time",
            "close_time",
        ]:
            if col not in df.columns:
                df[col] = pd.Series(dtype=object)
        return df

    # DEBUG: Check columns
    # import sys
    # print(f"DEBUG: _normalize_trades columns: {df.columns.tolist()}", file=sys.stderr)

    # Standardize column names safely to avoid duplicates
    standards = {
        "type": ["side", "direction"],
        "profit_loss": ["pnl", "profit", "final_profit"],
        "profit_pips": ["pips", "net_pips", "points"],
        "size": ["position_size", "quantity", "volume"],
        "time_in_trade": ["time_in_trade_seconds"],
        "r_multiple": ["rMultiple"],
        "mfe_usd": ["mfe_pips"],
        "mae_usd": ["mae_pips"],
    }

    for target, alternatives in standards.items():
        if target not in df.columns:
            for alt in alternatives:
                if alt in df.columns:
                    df = df.rename(columns={alt: target})
                    break

    for col in ["open_time", "close_time"]:
        if col in df.columns:
            # Handle potential seconds-since-epoch from MT5
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = pd.to_datetime(df[col], unit="s", errors="coerce")
            else:
                df[col] = pd.to_datetime(df[col], errors="coerce")

    if "type" not in df.columns and not df.empty:
        df["type"] = "buy"  # Default if missing

    return df


def _extract_proxy_benchmark(df: pd.DataFrame) -> pd.Series | None:
    """Try to extract a proxy price series from trades if no benchmark is provided."""
    if df.empty or "symbol" not in df.columns or "open_price" not in df.columns:
        return None

    # Take the most frequent symbol
    symbols = df["symbol"].dropna()
    if symbols.empty:
        return None
    symbol = symbols.mode()[0]
    symbol_df = df[df["symbol"] == symbol].sort_values("open_time")

    if symbol_df.empty:
        return None

    # Create a 2-point series as a minimal proxy for buy-and-hold
    # This isn't a full curve, but returns.buy_and_hold_return only needs iloc[0] and iloc[-1]
    # And returns.cagr uses the index to calculate duration.
    try:
        t0 = symbol_df["open_time"].iloc[0]
        t1 = symbol_df["close_time"].iloc[-1]
        p0 = symbol_df["open_price"].iloc[0]
        p1 = symbol_df["close_price"].iloc[-1]

        if pd.isna(t0) or pd.isna(t1) or p0 <= 0 or p1 <= 0:
            return None

        prices = pd.Series([p0, p1], index=[t0, t1])
        return prices
    except:
        return None


def _periods_to_timedelta(periods: float, index: pd.Index) -> pd.Timedelta:
    """Convert a number of periods/bars to a Timedelta based on index frequency."""
    if not len(index) or periods <= 0:
        return pd.Timedelta(0)
    if len(index) < 2:
        return pd.Timedelta(days=float(periods))

    # Estimate step from median difference between timestamps
    ts_series = pd.Series(index)
    diffs = ts_series.diff().dropna()
    diffs = diffs[diffs > pd.Timedelta(0)]
    step = diffs.median() if not diffs.empty else pd.Timedelta(days=1)
    return step * float(periods)


# =========================================================================
# Core Calculation Engines
# =========================================================================


def _calculate_analytics_for_subset_impl(
    trades: pd.DataFrame,
    initial_balance: float,
    start_time: pd.Timestamp | str | None = None,
    end_time: pd.Timestamp | str | None = None,
    benchmark_returns_series: pd.Series | None = None,
    benchmark_equity_series: pd.Series | None = None,
) -> dict[str, Any]:
    """Calculate ALL analytics categories for a specific subset of trades.

    Purpose:
        Calculate ALL analytics categories for a specific subset of trades.
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
        benchmark_returns_series:
            Analytics input consumed by this function.
        benchmark_equity_series:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    # Ensure timestamps are in pd.Timestamp format
    start_time = pd.Timestamp(start_time) if start_time else None
    end_time = pd.Timestamp(end_time) if end_time else None

    if trades.empty:
        return {
            "metrics": {},
            "returns": {},
            "ratios": {},
            "risks": {},
            "drawdowns": {},
            "distributions": {},
            "efficiency": {},
            "benchmark": {},
            "summary": {},
        }

    # Pre-calculate common derived data
    equity = returns.__equity_curve_impl_impl(
        trades, initial_balance, start_time=start_time, end_time=end_time
    )
    rets = returns.__returns_series_impl_impl(equity)

    # Resolve benchmark if missing
    if benchmark_returns_series is None:
        proxy_prices = _extract_proxy_benchmark(trades)
        if proxy_prices is not None and len(proxy_prices) >= 2:
            benchmark_returns_series = proxy_prices.pct_change().dropna()
            benchmark_equity_series = (
                1 + benchmark_returns_series
            ).cumprod() * initial_balance

    closed_trades = metrics.__get_closed_trades_impl_impl(trades)
    open_trades = trades[~trades.index.isin(closed_trades.index)]

    # 1. Metrics (Trade-based statistics)
    metrics_data = {
        "total_trades": metrics.__total_trades_impl_impl(closed_trades),
        "winning_trades": metrics.__winning_trades_impl_impl(closed_trades),
        "losing_trades": metrics.__losing_trades_impl_impl(closed_trades),
        "breakeven_trades": metrics.__breakeven_trades_impl_impl(closed_trades),
        "long_trades": metrics.__long_trades_impl_impl(closed_trades),
        "short_trades": metrics.__short_trades_impl_impl(closed_trades),
        "open_trades": len(open_trades),
        "open_pnl": metrics.__open_position_pnl_impl_impl(open_trades),
        "win_rate": metrics.__win_rate_impl_impl(closed_trades),
        "loss_rate": metrics.__loss_rate_impl_impl(closed_trades),
        "avg_win": metrics.__avg_win_impl_impl(closed_trades),
        "avg_loss": metrics.__avg_loss_impl_impl(closed_trades),
        "largest_win": metrics.__largest_win_impl_impl(closed_trades),
        "largest_loss": metrics.__largest_loss_impl_impl(closed_trades),
        "median_win": metrics.__median_win_impl_impl(closed_trades),
        "median_loss": metrics.__median_loss_impl_impl(closed_trades),
        "slippage_paid": metrics.__slippage_paid_impl_impl(closed_trades),
        "commission_paid": metrics.__commission_paid_impl_impl(closed_trades),
        "swap_paid": metrics.__swap_paid_impl_impl(closed_trades),
        "avg_r_multiple": metrics.__avg_r_multiple_impl_impl(closed_trades),
        "median_r_multiple": metrics.__median_r_multiple_impl_impl(closed_trades),
        "max_r_multiple": metrics.__max_r_multiple_impl_impl(closed_trades),
        "min_r_multiple": metrics.__min_r_multiple_impl_impl(closed_trades),
        "max_consecutive_wins": metrics.__max_consecutive_wins_impl_impl(closed_trades),
        "max_consecutive_losses": metrics.__max_consecutive_losses_impl_impl(
            closed_trades
        ),
        "avg_consecutive_wins": metrics.__avg_consecutive_wins_impl_impl(closed_trades),
        "avg_consecutive_losses": metrics.__avg_consecutive_losses_impl_impl(
            closed_trades
        ),
        "avg_time_in_trade": metrics.__avg_time_in_trade_impl_impl(closed_trades),
        "median_time_in_trade": metrics.__median_time_in_trade_impl_impl(closed_trades),
        "max_time_in_trade": metrics.__max_time_in_trade_impl_impl(closed_trades),
        "min_time_in_trade": metrics.__min_time_in_trade_impl_impl(closed_trades),
        "median_mae_r": metrics.__median_mae_r_impl_impl(closed_trades),
        "median_mfe_r": metrics.__median_mfe_r_impl_impl(closed_trades),
        "sqn": metrics.__sqn_impl_impl(closed_trades),
        "kelly_criterion": metrics.__kelly_criterion_impl_impl(closed_trades),
        "time_in_market_hours": metrics.__time_in_market_duration_impl_impl(
            closed_trades
        ).total_seconds()
        / 3600.0,
        "percent_time_in_market": metrics.__percent_time_in_market_impl_impl(
            closed_trades, start_time, end_time
        ),
        "longest_flat_period_hours": metrics.__longest_flat_period_duration_impl_impl(
            closed_trades, start_time, end_time
        ).total_seconds()
        / 3600.0,
        "max_size_held": metrics.__max_gross_size_held_impl_impl(
            closed_trades, end_time
        ),
        "max_net_size_held": metrics.__max_net_size_held_impl_impl(
            closed_trades, end_time
        ),
        "max_long_size_held": metrics.__max_long_size_held_impl_impl(closed_trades),
        "max_short_size_held": metrics.__max_short_size_held_impl_impl(closed_trades),
        "t_statistic": metrics.__t_statistic_impl_impl(closed_trades["profit_loss"])
        if not closed_trades.empty
        else 0.0,
        "trade_efficiency": metrics.__trade_efficiency_impl_impl(closed_trades),
        "r_signal_to_noise": metrics.__r_signal_to_noise_impl_impl(closed_trades),
        "expectancy_variance": metrics.__r_signal_to_noise_impl_impl(
            closed_trades
        ),  # Compatibility key
        "rolling_expectancy_stability": metrics.__rolling_expectancy_stability_impl_impl(
            closed_trades
        ),
        "runs_test_zscore": metrics.__runs_test_zscore_impl_impl(closed_trades),
        "win_after_win_probability": metrics.__win_after_win_probability_impl_impl(
            closed_trades
        ),
        "max_runup": returns.__max_runup_impl_impl(equity),
        "median_mae": metrics.__median_mae_r_impl_impl(closed_trades),
        "median_mfe": metrics.__median_mfe_r_impl_impl(closed_trades),
        "trade_outcome_entropy": metrics.__trade_outcome_entropy_impl_impl(
            closed_trades
        ),
        "trading_period_duration_days": metrics.__trading_period_duration_impl_impl(
            closed_trades, start_time, end_time
        ).total_seconds()
        / 86400.0,
        "expectancy": metrics.__expectancy_impl_impl(closed_trades),
        "expectancy_r": metrics.__expectancy_r_impl_impl(
            metrics.__get_r_multiples_impl_impl(closed_trades)
        ),
    }

    # 2. Returns
    returns_data = {
        "net_profit": returns.__net_profit_impl_impl(trades),
        "gross_profit": returns.__gross_profit_impl_impl(trades),
        "gross_loss": returns.__gross_loss_impl_impl(trades),
        "adjusted_net_profit": returns.__adjusted_net_profit_impl_impl(trades),
        "select_net_profit": returns.__select_net_profit_impl_impl(trades),
        "total_return": returns.__total_return_impl_impl(equity),
        "total_return_usd": returns.__total_return_usd_impl_impl(equity),
        "cagr": returns.__cagr_impl_impl(equity),
        "annualized_return": returns.__annualized_return_impl_impl(rets),
        "geometric_mean_return": returns.__geometric_mean_return_impl_impl(rets),
        "cmgr": returns.__compound_monthly_growth_rate_impl_impl(equity),
        "volatility": returns.__return_volatility_impl_impl(rets),
        "downside_volatility": returns.__downside_return_volatility_impl_impl(rets),
        "avg_monthly_return": returns.__avg_monthly_return_impl_impl(equity),
        "monthly_return_stddev": returns.__monthly_return_stddev_impl_impl(equity),
        "buy_and_hold_return": (
            returns.__buy_and_hold_return_impl_impl(benchmark_equity_series)
            if benchmark_equity_series is not None
            else returns.__buy_and_hold_return_impl_impl(
                _extract_proxy_benchmark(trades)
            )
        ),
        "buy_and_hold_cagr": (
            returns.__buy_and_hold_cagr_impl_impl(benchmark_equity_series)
            if benchmark_equity_series is not None
            else returns.__buy_and_hold_cagr_impl_impl(_extract_proxy_benchmark(trades))
        ),
        "adjusted_gross_profit": returns.__adjusted_gross_profit_impl_impl(trades),
        "adjusted_gross_loss": returns.__adjusted_gross_loss_impl_impl(trades),
        "select_gross_profit": returns.__select_gross_profit_impl_impl(trades),
        "select_gross_loss": returns.__select_gross_loss_impl_impl(trades),
        "return_skewness": returns.__return_skewness_impl_impl(rets),
        "return_kurtosis": returns.__return_kurtosis_impl_impl(rets),
        "daily_returns": returns.__daily_returns_impl_impl(equity).tolist(),
        "weekly_returns": returns.__weekly_returns_impl_impl(equity).tolist(),
        "monthly_returns": returns.__monthly_returns_impl_impl(equity).tolist(),
        "annual_returns": returns.__annual_returns_impl_impl(equity).tolist(),
        "log_returns": returns.__log_returns_series_impl_impl(equity).tolist(),
        "return_on_max_drawdown": returns.__return_on_max_strategy_drawdown_impl_impl(
            equity
        ),
        "return_on_max_c2c_drawdown": returns.__return_on_max_close_to_close_drawdown_impl_impl(
            trades
        ),
        "return_on_initial_capital": returns.__return_on_initial_capital_impl_impl(
            trades, initial_balance
        ),
        "max_runup": returns.__max_runup_impl_impl(equity),
        "max_runup_date": returns.__max_runup_date_impl_impl(equity),
        "best_return": returns.__best_return_impl_impl(rets),
        "worst_return": returns.__worst_return_impl_impl(rets),
    }

    # 3. Ratios
    ratios_data = {
        "sharpe_ratio": ratios.__sharpe_ratio_impl_impl(rets, annualize=True),
        "sortino_ratio": ratios.__sortino_ratio_impl_impl(rets, annualize=True),
        "calmar_ratio": ratios.__calmar_ratio_impl_impl(
            returns_data["cagr"],
            drawdowns.__max_strategy_drawdown_percent_impl_impl(equity),
        ),
        "omega_ratio": ratios.__omega_ratio_impl_impl(rets),
        "gain_to_pain_ratio": ratios.__gain_to_pain_ratio_impl_impl(rets),
        "profit_factor": ratios.__profit_factor_impl_impl(trades),
        "payoff_ratio": ratios.__payoff_ratio_impl_impl(trades),
        "expectancy": ratios.__expectancy_impl_impl(trades),
        "expectancy_r": ratios.__expectancy_r_impl_impl(
            metrics.__get_r_multiples_impl_impl(trades)
        ),
        "edge_ratio": ratios.__edge_ratio_impl_impl(trades),
        "rina_index": ratios.__rina_index_impl_impl(
            returns_data["select_net_profit"],
            drawdowns.__avg_drawdown_impl_impl(equity),
            metrics_data["percent_time_in_market"],
        ),
        "recovery_factor": drawdowns.__recovery_factor_impl_impl(equity),
        "information_ratio": ratios.__information_ratio_impl_impl(
            rets, benchmark_returns_series
        )
        if benchmark_returns_series is not None
        else 0.0,
        "sterling_ratio": ratios.__sterling_ratio_impl_impl(
            returns_data["cagr"], drawdowns.__avg_yearly_max_drawdown_impl_impl(equity)
        ),
        "profit_to_mae_ratio": ratios.__profit_to_mae_ratio_impl_impl(trades),
        "mfe_to_mae_ratio": ratios.__mfe_to_mae_ratio_impl_impl(trades),
        "fouse_ratio": ratios.__fouse_ratio_impl_impl(rets, risk_tolerance=2.0),
        "upside_potential_ratio": ratios.__upside_potential_ratio_impl_impl(rets),
        "kappa_ratio": ratios.__kappa_ratio_impl_impl(rets),
        "return_over_drawdown": ratios.__return_over_drawdown_impl_impl(trades),
        "expectancy_over_std": ratios.__expectancy_over_std_impl_impl(trades),
        "adjusted_profit_factor": ratios.__adjusted_profit_factor_impl_impl(trades),
        "select_profit_factor": ratios.__select_profit_factor_impl_impl(trades),
        "net_profit_to_max_dd": ratios.__net_profit_as_percent_of_max_strategy_drawdown_impl_impl(
            returns_data["net_profit"],
            drawdowns.__max_strategy_drawdown_impl_impl(equity),
        ),
    }

    # 4. Risks
    risks_data = {
        "volatility": risks.__volatility_impl_impl(rets),
        "annualized_volatility": risks.__annualized_volatility_impl_impl(rets),
        "value_at_risk_95": risks.__value_at_risk_impl_impl(rets, confidence=0.95),
        "expected_shortfall_95": risks.__expected_shortfall_impl_impl(
            rets, confidence=0.95
        ),
        "risk_of_ruin": risks.__risk_of_ruin_impl_impl(trades, risk_per_trade_pct=1.0),
        "max_exposure": risks.__max_nominal_exposure_simple_impl_impl(trades),
        "avg_exposure": risks.__avg_trade_nominal_exposure_impl_impl(trades),
        "downside_volatility_risk": risks.__downside_volatility_impl_impl(rets),
        "max_loss_probability": risks.__max_loss_probability_impl_impl(trades),
        "drawdown_probability_10pct": risks.__drawdown_probability_impl_impl(
            rets, threshold_pct=10.0
        ),
        "exposure_time_ratio": risks.__exposure_time_ratio_impl_impl(
            trades, start_time, end_time
        ),
        "max_gross_exposure": risks.__max_gross_exposure_impl_impl(trades),
    }

    # 5. Drawdowns
    max_dd_periods = int(drawdowns.__max_drawdown_duration_impl_impl(equity))
    avg_dd_periods = float(drawdowns.__avg_drawdown_duration_impl_impl(equity))

    drawdowns_data = {
        "max_drawdown_usd": drawdowns.__max_strategy_drawdown_impl_impl(equity),
        "max_drawdown_pct": drawdowns.__max_strategy_drawdown_percent_impl_impl(equity),
        "avg_drawdown_usd": drawdowns.__avg_drawdown_impl_impl(equity),
        "max_drawdown_duration": str(
            _periods_to_timedelta(max_dd_periods, equity.index)
        ),
        "avg_drawdown_duration": str(
            _periods_to_timedelta(avg_dd_periods, equity.index)
        ),
        "ulcer_index": drawdowns.__ulcer_index_impl_impl(equity),
        "pain_index": drawdowns.__pain_index_impl_impl(equity),
        "max_close_to_close_drawdown": drawdowns.__max_close_to_close_drawdown_impl_impl(
            trades
        ),
        "max_close_to_close_drawdown_pct": drawdowns.__max_close_to_close_drawdown_percent_impl_impl(
            trades, initial_balance
        ),
        "avg_yearly_max_drawdown": drawdowns.__avg_yearly_max_drawdown_impl_impl(
            equity
        ),
        "account_size_required": drawdowns.__account_size_required_impl_impl(trades),
        "pain_ratio": drawdowns.__pain_ratio_impl_impl(equity),
        "max_drawdown_date": drawdowns.__max_strategy_drawdown_date_impl_impl(
            equity
        ).isoformat()
        if not equity.empty
        and drawdowns.__max_strategy_drawdown_date_impl_impl(equity) is not None
        else None,
        "max_close_to_close_drawdown_date": drawdowns.__max_close_to_close_drawdown_date_impl_impl(
            trades
        ).isoformat()
        if not trades.empty
        and drawdowns.__max_close_to_close_drawdown_date_impl_impl(trades) is not None
        else None,
        "drawdown_distribution": drawdowns.__drawdown_distribution_impl_impl(equity),
        "time_to_recovery_periods": [
            str(_periods_to_timedelta(p, equity.index))
            for p in drawdowns.__time_to_recovery_impl_impl(equity)
        ],
        "avg_trade_drawdown": drawdowns.__avg_trade_drawdown_impl_impl(trades),
        "max_consecutive_drawdown_trades": drawdowns.__max_consecutive_drawdown_trades_impl_impl(
            trades
        ),
    }

    # 6. Distributions
    distributions_data = {
        "returns": distributions.__return_distribution_impl_impl(rets),
        "trades": distributions.__trade_pnl_distribution_impl_impl(trades),
        "r_multiples": distributions.__r_multiple_distribution_impl_impl(trades),
        "outlier_ratio": distributions.__outlier_ratio_impl_impl(rets),
        "skewness": distributions.__skewness_impl_impl(rets),
        "kurtosis": distributions.__kurtosis_impl_impl(rets),
        "jarque_bera": distributions.__jarque_bera_test_impl_impl(rets),
        "jarque_bera_p_value": distributions.__jarque_bera_test_impl_impl(rets).get(
            "p_value", 0.0
        ),
        "shapiro_wilk": distributions.__shapiro_wilk_test_impl_impl(rets),
        "shapiro_wilk_p_value": distributions.__shapiro_wilk_test_impl_impl(rets).get(
            "p_value", 0.0
        ),
        "is_normal_jb": distributions.__jarque_bera_test_impl_impl(rets).get(
            "p_value", 0.0
        )
        > 0.05,
        "is_normal_sw": distributions.__shapiro_wilk_test_impl_impl(rets).get(
            "p_value", 0.0
        )
        > 0.05,
        "fat_tail_score": distributions.__fat_tail_score_impl_impl(rets),
        "tail_ratio": distributions.__tail_ratio_impl_impl(rets),
        "higher_moments": distributions.__higher_moments_impl_impl(rets),
        "percentiles": distributions.__percentile_summary_impl_impl(rets),
        "upside_downside": distributions.__upside_downside_summary_impl_impl(rets),
        "histogram": distributions.__histogram_data_impl_impl(rets),
        "fit_quality": {
            "norm": distributions.__distribution_fit_quality_impl_impl(rets, "norm"),
            "t": distributions.__distribution_fit_quality_impl_impl(rets, "t"),
            "best_model": "Normal"
            if (
                distributions.__distribution_fit_quality_impl_impl(rets, "norm").get(
                    "aic", 0
                )
                < distributions.__distribution_fit_quality_impl_impl(rets, "t").get(
                    "aic", 0
                )
            )
            else "T-Distribution",
        },
    }

    # 7. Efficiency
    efficiency_data = {
        "capital_efficiency": efficiency.__capital_efficiency_impl_impl(trades),
        "avg_trade_notional_efficiency": efficiency.__avg_trade_notional_efficiency_impl_impl(
            trades
        ),
        "return_per_unit_mae": efficiency.__return_per_unit_mae_impl_impl(trades),
        "risk_adjusted_efficiency": efficiency.__risk_adjusted_efficiency_impl_impl(
            trades
        ),
        "avg_return_per_risk_unit": efficiency.__avg_return_per_risk_unit_impl_impl(
            trades
        ),
        "return_per_trade_hour": efficiency.__return_per_trade_hour_impl_impl(trades),
        "return_per_market_hour": efficiency.__return_per_market_hour_impl_impl(
            trades, end_time
        ),
        "return_per_calendar_day": efficiency.__return_per_calendar_day_impl_impl(
            trades, start_time, end_time
        ),
        "trades_per_day": efficiency.__trades_per_day_impl_impl(
            trades, start_time, end_time
        ),
        "profit_per_trade_per_day": efficiency.__profit_per_trade_per_day_impl_impl(
            trades, start_time, end_time
        ),
        "mfe_efficiency": efficiency.__mfe_efficiency_impl_impl(trades),
        "aggregate_mfe_capture_ratio": efficiency.__aggregate_mfe_capture_ratio_impl_impl(
            trades
        ),
        "mae_efficiency": efficiency.__mae_efficiency_impl_impl(trades),
        "exit_efficiency": efficiency.__exit_efficiency_impl_impl(trades),
        "loss_containment_efficiency": efficiency.__loss_containment_efficiency_impl_impl(
            trades
        ),
        "aggregate_loss_containment_efficiency": efficiency.__aggregate_loss_containment_efficiency_impl_impl(
            trades
        ),
        "position_size_efficiency": efficiency.__position_size_efficiency_impl_impl(
            trades
        ),
        "profit_per_pip_risk": efficiency.__profit_per_pip_risk_impl_impl(trades),
        # Backward compatibility aliases for UI
        "return_per_unit_risk": efficiency.__return_per_unit_mae_impl_impl(trades),
        "return_per_r_risk": efficiency.__avg_return_per_risk_unit_impl_impl(trades),
        "time_efficiency": efficiency.__return_per_trade_hour_impl_impl(trades),
        "return_per_unit_time": efficiency.__return_per_market_hour_impl_impl(
            trades, end_time
        ),
        "return_per_trade_opportunity": efficiency.__return_per_calendar_day_impl_impl(
            trades, start_time, end_time
        ),
        "return_per_trade": metrics_data.get("expectancy", 0.0),
        "win_efficiency": efficiency.__aggregate_mfe_capture_ratio_impl_impl(trades)
        * 100.0,  # Convert to % for UI
    }

    # 8. Benchmark
    benchmark_data = {}
    if benchmark_returns_series is not None:
        benchmark_data = {
            "beta": benchmark.__beta_impl_impl(rets, benchmark_returns_series),
            "alpha": benchmark.__alpha_impl_impl(rets, benchmark_returns_series),
            "r_squared": benchmark.__r_squared_impl_impl(
                rets, benchmark_returns_series
            ),
            "tracking_error": benchmark.__tracking_error_impl_impl(
                rets, benchmark_returns_series
            ),
            "batting_average": benchmark.__batting_average_impl_impl(
                rets, benchmark_returns_series
            ),
            "up_capture": benchmark.__up_down_capture_impl_impl(
                rets, benchmark_returns_series
            )[0],
            "down_capture": benchmark.__up_down_capture_impl_impl(
                rets, benchmark_returns_series
            )[1],
            "relative_drawdown": benchmark.__max_relative_drawdown_percent_impl_impl(
                equity, benchmark_equity_series
            ),
            "information_ratio": ratios.__information_ratio_impl_impl(
                rets, benchmark_returns_series
            ),
            "cagr": returns.__cagr_impl_impl(benchmark_equity_series),
            "total_return": returns.__buy_and_hold_return_impl_impl(
                benchmark_equity_series
            ),
        }

    # 9. Statistical Validation
    validation_data = {}
    if not closed_trades.empty:
        # P-values and DSR
        dsr_val, dsr_p = statistical_tests.__deflated_sharpe_ratio_impl_impl(
            observed_sharpe=ratios_data["sharpe_ratio"],
            n_trials=10,  # Conservative default
            n_observations=len(rets),
            skew=distributions_data["skewness"],
            kurt=distributions_data["kurtosis"] + 3.0,  # convert excess to normal
        )

        perm_test = statistical_tests.__permutation_test_impl_impl(
            rets, n_permutations=500
        )

        validation_data = {
            "deflated_sharpe_ratio": dsr_val,
            "dsr_p_value": dsr_p,
            "permutation_p_value": perm_test.p_value,
            "is_significant": perm_test.is_significant,
            "prob_sharpe_gt_0": statistical_tests.__bootstrap_probability_above_threshold_impl_impl(
                rets, lambda r: ratios.__sharpe_ratio_impl_impl(r), threshold=0.0
            ),
            "prob_return_gt_0": statistical_tests.__bootstrap_probability_above_threshold_impl_impl(
                rets, lambda r: np.sum(r), threshold=0.0
            ),
        }

    # 10. Summary (Overview table style)
    summary_data = {
        "start": start_time.isoformat() if start_time else None,
        "end": end_time.isoformat() if end_time else None,
        "duration_days": (end_time - start_time).total_seconds() / 86400.0
        if start_time and end_time
        else 0,
        "equity_final": float(equity.iloc[-1]) if not equity.empty else initial_balance,
        "equity_peak": float(equity.max()) if not equity.empty else initial_balance,
        "total_return": float(returns_data["total_return"]),
        "return_usd": float(returns_data["net_profit"]),
        "return_pct": float(returns_data["net_profit"] / initial_balance * 100.0)
        if initial_balance > 0
        else 0.0,
        "buy_hold_return_pct": float(returns_data["buy_and_hold_return"]),
        "num_trades": int(metrics_data["total_trades"]),
        "win_rate_pct": float(metrics_data["win_rate"]),
        "best_trade_pct": float((trades["profit_loss"] / initial_balance * 100.0).max())
        if not trades.empty and initial_balance > 0
        else 0.0,
        "worst_trade_pct": float(
            (trades["profit_loss"] / initial_balance * 100.0).min()
        )
        if not trades.empty and initial_balance > 0
        else 0.0,
        "avg_trade_pct": float((trades["profit_loss"] / initial_balance * 100.0).mean())
        if not trades.empty and initial_balance > 0
        else 0.0,
        "exposure_time_pct": float(metrics_data["percent_time_in_market"]),
        "time_in_market": _format_duration(metrics_data["time_in_market_hours"]),
        "longest_flat_period": _format_duration(
            metrics_data["longest_flat_period_hours"]
        ),
        "max_trade_duration": _format_duration(
            (
                pd.to_datetime(trades["close_time"])
                - pd.to_datetime(trades["open_time"])
            ).max()
        )
        if not trades.empty
        else "0h",
        "avg_trade_duration": _format_duration(
            (
                pd.to_datetime(trades["close_time"])
                - pd.to_datetime(trades["open_time"])
            ).mean()
        )
        if not trades.empty
        else "0h",
        "max_drawdown_pct": float(drawdowns_data["max_drawdown_pct"]),
        "avg_drawdown_pct": float(
            drawdowns.__avg_underwater_drawdown_percent_impl_impl(equity)
        ),
        "max_drawdown_duration": _format_duration(
            drawdowns_data["max_drawdown_duration"]
        ),
        "avg_drawdown_duration": _format_duration(
            drawdowns_data["avg_drawdown_duration"]
        ),
        "value_at_risk_95": float(risks_data["value_at_risk_95"]),
        "expectancy_pct": float(ratios_data["expectancy"] / initial_balance * 100.0)
        if initial_balance > 0
        else 0.0,
        "expectancy_r": float(ratios_data["expectancy_r"]),
        "profit_factor": float(ratios_data["profit_factor"]),
        "sharpe_ratio": float(ratios_data["sharpe_ratio"]),
        "sortino_ratio": float(ratios_data["sortino_ratio"]),
        "calmar_ratio": float(ratios_data["calmar_ratio"]),
        "alpha": float(benchmark_data.get("alpha", 0.0)),
        "beta": float(benchmark_data.get("beta", 0.0)),
        "cagr": float(returns_data["cagr"]),
        "annual_return": float(returns_data["annualized_return"]),
        "annual_volatility": float(returns_data["volatility"]),
        "risk_of_ruin": float(metrics_data.get("risk_of_ruin", 0.0)),
        "max_exposure": float(metrics_data.get("max_exposure", 0.0)),
        "ulcer_index": float(drawdowns_data.get("ulcer_index", 0.0)),
        "sqn": float(metrics_data.get("sqn", 0.0)),
        "kelly_criterion": float(metrics_data.get("kelly_criterion", 0.0)),
    }

    return {
        "summary": summary_data,
        "metrics": metrics_data,
        "returns": returns_data,
        "ratios": ratios_data,
        "risks": risks_data,
        "drawdowns": drawdowns_data,
        "distributions": distributions_data,
        "efficiency": efficiency_data,
        "benchmark": benchmark_data,
        "validation": validation_data,
    }


def _get_analytics_overview_impl(
    trades: Any,
    initial_balance: float,
    start_time: Any = None,
    end_time: Any = None,
    benchmark_equity: pd.Series | None = None,
) -> dict[str, Any]:
    """Calculate comprehensive analytics across all categories in parallel subsets.

    Purpose:
        Calculate comprehensive analytics across all categories in parallel subsets.
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
        benchmark_equity:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    df = _normalize_trades(trades)
    t_start = pd.Timestamp(start_time) if start_time else None
    t_end = pd.Timestamp(end_time) if end_time else None

    benchmark_rets = (
        benchmark_equity.pct_change().dropna()
        if benchmark_equity is not None and len(benchmark_equity) >= 2
        else None
    )

    with ThreadPoolExecutor(max_workers=3) as executor:
        f_all = executor.submit(
            calculate_analytics_for_subset,
            df,
            initial_balance,
            t_start,
            t_end,
            benchmark_rets,
            benchmark_equity,
        )
        f_long = executor.submit(
            calculate_analytics_for_subset,
            df[df["type"] == "buy"],
            initial_balance,
            t_start,
            t_end,
            benchmark_rets,
            benchmark_equity,
        )
        f_short = executor.submit(
            calculate_analytics_for_subset,
            df[df["type"] == "sell"],
            initial_balance,
            t_start,
            t_end,
            benchmark_rets,
            benchmark_equity,
        )

        results_all = f_all.result()
        results_long = f_long.result()
        results_short = f_short.result()

    final_output = {}
    categories = [
        "metrics",
        "returns",
        "ratios",
        "risks",
        "drawdowns",
        "distributions",
        "efficiency",
        "benchmark",
        "validation",
        "summary",
    ]
    for cat in categories:
        final_output[cat] = {
            "all": results_all.get(cat, {}),
            "long": results_long.get(cat, {}),
            "short": results_short.get(cat, {}),
        }

    def _to_python_types(obj, key=None):
        """Convert pandas and NumPy values into JSON-safe Python primitives."""
        if isinstance(obj, dict):
            return {k: _to_python_types(v, k) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [_to_python_types(x, key) for x in obj]

        # Datetime & Timedelta
        if isinstance(obj, (pd.Timestamp, datetime)):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(obj, (pd.Timedelta, pd._libs.tslibs.timedeltas.Timedelta)):
            return str(obj)

        # Float rounding
        if isinstance(obj, (float, np.float64, np.float32)):
            val = float(obj)
            if not np.isfinite(val):
                return 0.0
            if key and any(
                s in key.lower()
                for s in [
                    "_usd",
                    "_final",
                    "_peak",
                    "pnl",
                    "_profit",
                    "_loss",
                    "balance",
                    "equity",
                ]
            ):
                return round(val, 2)
            return round(val, 5)

        if isinstance(obj, (np.int64, np.int32)):
            return int(obj)
        return None if pd.isna(obj) else obj

    return _to_python_types(final_output)


# =========================================================================
# Reporting & Payload Construction
# =========================================================================


def _format_summary_as_rows_impl(summary_data: dict[str, Any]) -> list[tuple[str, str]]:
    """Format raw summary data into display rows for reports.

    Purpose:
        Format raw summary data into display rows for reports.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        summary_data:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """

    def _fmt_num(val, decimals=2):
        """Format a numeric value with a fixed decimal count."""
        if val is None or not np.isfinite(float(val)):
            return "nan"
        return f"{float(val):.{decimals}f}"

    return [
        ("Start", str(summary_data.get("start", ""))),
        ("End", str(summary_data.get("end", ""))),
        ("Duration", f"{summary_data.get('duration_days', 0):.2f} days"),
        ("Equity Final [$]", _fmt_num(summary_data.get("equity_final"), 2)),
        ("Equity Peak [$]", _fmt_num(summary_data.get("equity_peak"), 2)),
        ("Return [$]", _fmt_num(summary_data.get("return_usd"), 2)),
        ("Return [%]", _fmt_num(summary_data.get("return_pct"), 5)),
        ("Buy & Hold Return [%]", _fmt_num(summary_data.get("buy_hold_return_pct"), 5)),
        ("Num of Trades", str(summary_data.get("num_trades", 0))),
        ("Num of Ticks", str(summary_data.get("processed_ticks", 0))),
        ("Win Rate [%]", _fmt_num(summary_data.get("win_rate_pct"), 5)),
        ("Best Trade [%]", _fmt_num(summary_data.get("best_trade_pct"), 5)),
        ("Worst Trade [%]", _fmt_num(summary_data.get("worst_trade_pct"), 5)),
        ("Avg. Trade [%]", _fmt_num(summary_data.get("avg_trade_pct"), 5)),
        ("Exposure Time [%]", _fmt_num(summary_data.get("exposure_time_pct"), 5)),
        ("Time in Market", str(summary_data.get("time_in_market", "0h"))),
        ("Longest Flat Period", str(summary_data.get("longest_flat_period", "0h"))),
        ("Max. Trade Duration", str(summary_data.get("max_trade_duration", ""))),
        ("Avg. Trade Duration", str(summary_data.get("avg_trade_duration", ""))),
        ("Max. Drawdown [%]", _fmt_num(summary_data.get("max_drawdown_pct"), 5)),
        ("Avg. Drawdown [%]", _fmt_num(summary_data.get("avg_drawdown_pct"), 5)),
        ("Max. Drawdown Duration", str(summary_data.get("max_drawdown_duration", ""))),
        ("Avg. Drawdown Duration", str(summary_data.get("avg_drawdown_duration", ""))),
        ("Value at Risk (95%)", _fmt_num(summary_data.get("value_at_risk_95"), 5)),
        ("Expectancy [%]", _fmt_num(summary_data.get("expectancy_pct"), 5)),
        ("R-Expectancy", _fmt_num(summary_data.get("expectancy_r"), 5)),
        ("Profit Factor", _fmt_num(summary_data.get("profit_factor"), 5)),
        ("Sharpe Ratio", _fmt_num(summary_data.get("sharpe_ratio"), 5)),
        ("Sortino Ratio", _fmt_num(summary_data.get("sortino_ratio"), 5)),
        ("Calmar Ratio", _fmt_num(summary_data.get("calmar_ratio"), 5)),
        ("Alpha [%]", _fmt_num(summary_data.get("alpha"), 5)),
        ("Beta", _fmt_num(summary_data.get("beta"), 5)),
        ("CAGR [%]", _fmt_num(summary_data.get("cagr"), 5)),
        ("Return (Ann.) [%]", _fmt_num(summary_data.get("annual_return"), 5)),
        ("Volatility (Ann.) [%]", _fmt_num(summary_data.get("annual_volatility"), 5)),
        ("Risk of Ruin [%]", _fmt_num(summary_data.get("risk_of_ruin", 0) * 100, 2)),
        ("Max Exposure [$]", _fmt_num(summary_data.get("max_exposure"), 2)),
        ("Ulcer Index", _fmt_num(summary_data.get("ulcer_index"), 5)),
        ("SQN", _fmt_num(summary_data.get("sqn"), 5)),
        ("Kelly Criterion [%]", _fmt_num(summary_data.get("kelly_criterion"), 5)),
    ]


def _get_dashboard_metrics(analytics: dict[str, Any]) -> dict[str, Any]:
    """Extract a curated set of key performance indicators for the primary dashboard, with Long/Short support."""

    def get_3way(cat, key, default=0.0):
        """Read an all/long/short metric triplet from analytics data."""
        category_data = analytics.get(cat, {})
        return {
            "all": category_data.get("all", {}).get(key, default),
            "long": category_data.get("long", {}).get(key, default),
            "short": category_data.get("short", {}).get(key, default),
        }

    # Helper to merge multiple 3-way metrics into a category object
    def build_category(cat_configs):
        """Build a dashboard category from configured analytics metrics."""
        # cat_configs is list of (dashboard_key, cat_name, metric_key)
        out = {"all": {}, "long": {}, "short": {}}
        for dashboard_key, cat_name, metric_key in cat_configs:
            m3 = get_3way(cat_name, metric_key)
            out["all"][dashboard_key] = m3["all"]
            out["long"][dashboard_key] = m3["long"]
            out["short"][dashboard_key] = m3["short"]
        return out

    return {
        "profitability": build_category(
            [
                ("net_profit", "returns", "net_profit"),
                ("total_return", "returns", "total_return"),
                ("cagr", "returns", "cagr"),
                ("profit_factor", "ratios", "profit_factor"),
                ("expectancy_r", "ratios", "expectancy_r"),
            ]
        ),
        "risk": build_category(
            [
                ("max_drawdown_pct", "drawdowns", "max_drawdown_pct"),
                ("max_drawdown_duration", "drawdowns", "max_drawdown_duration"),
                ("value_at_risk_95", "risks", "value_at_risk_95"),
                ("expected_shortfall_95", "risks", "expected_shortfall_95"),
                ("ulcer_index", "drawdowns", "ulcer_index"),
                ("risk_of_ruin", "risks", "risk_of_ruin"),
            ]
        ),
        "quality": build_category(
            [
                ("sharpe_ratio", "ratios", "sharpe_ratio"),
                ("sortino_ratio", "ratios", "sortino_ratio"),
                ("calmar_ratio", "ratios", "calmar_ratio"),
                ("sqn", "metrics", "sqn"),
                ("kelly_criterion", "metrics", "kelly_criterion"),
                ("win_rate", "metrics", "win_rate"),
            ]
        ),
        "robustness": build_category(
            [
                ("deflated_sharpe_ratio", "validation", "deflated_sharpe_ratio"),
                ("dsr_p_value", "validation", "dsr_p_value"),
                ("prob_sharpe_gt_0", "validation", "prob_sharpe_gt_0"),
            ]
        ),
        "efficiency": build_category(
            [
                (
                    "aggregate_mfe_capture_ratio",
                    "efficiency",
                    "aggregate_mfe_capture_ratio",
                ),
                (
                    "aggregate_loss_containment_efficiency",
                    "efficiency",
                    "aggregate_loss_containment_efficiency",
                ),
                ("percent_time_in_market", "metrics", "percent_time_in_market"),
                ("capital_efficiency", "efficiency", "capital_efficiency"),
            ]
        ),
        "benchmark": build_category(
            [
                ("alpha", "benchmark", "alpha"),
                ("beta", "benchmark", "beta"),
                ("information_ratio", "ratios", "information_ratio"),
                ("up_capture", "benchmark", "up_capture"),
                ("down_capture", "benchmark", "down_capture"),
            ]
        ),
    }


def _build_overview_payload_core(
    trades: Any,
    initial_balance: float,
    start_time: Any = None,
    end_time: Any = None,
    equity_curve_records: list[Any] | None = None,
    summary_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the full analytics payload for the API including charts.

    Purpose:
        Build the full analytics payload for the API including charts.
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
        equity_curve_records:
            Analytics input consumed by this function.
        summary_overrides:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    df = _normalize_trades(trades)

    # 1. Calculate base analytics (get_analytics_overview already handles All/Long/Short)
    analytics = _get_analytics_overview_impl(df, initial_balance, start_time, end_time)

    # 2. Extract structured summary
    summary = analytics.get("summary", {"all": {}, "long": {}, "short": {}})

    # 3. Apply overrides (e.g. processed_ticks) specifically to the 'all' category
    if summary_overrides:
        summary["all"].update(summary_overrides)

    # 4. Prepare metric categories for the payload (already structured by get_analytics_overview)
    categories = [
        "metrics",
        "returns",
        "ratios",
        "risks",
        "drawdowns",
        "distributions",
        "efficiency",
        "benchmark",
        "validation",
    ]
    payload_categories = {cat: analytics.get(cat, {}) for cat in categories}

    # Generate Curves for Charts
    def _get_subset_curves(subset_df):
        """Build equity and drawdown percentage curves for a trade subset."""
        if subset_df.empty:
            return pd.Series(dtype=float), pd.Series(dtype=float)
        time_col = "close_time" if "close_time" in subset_df.columns else None
        if time_col:
            index = pd.to_datetime(subset_df[time_col], errors="coerce")
        else:
            index = pd.to_datetime(subset_df.index, errors="coerce")
        pnl = pd.to_numeric(subset_df.get("profit_loss", 0.0), errors="coerce").fillna(
            0.0
        )
        equity = pd.Series(initial_balance + pnl.cumsum().to_numpy(), index=index)
        equity = equity[~equity.index.isna()].sort_index()
        equity = equity.groupby(level=0).last()
        raw_dd = equity - equity.cummax()

        # Calculate absolute percentage drawdown (0 to 100%)
        # peak = equity - raw_dd (since raw_dd is negative)
        peak = equity - raw_dd
        dd_pct = (abs(raw_dd) / peak.replace(0, 1e-9)) * 100

        return equity, dd_pct

    eq_all, dd_all = _get_subset_curves(df)
    eq_long, dd_long = _get_subset_curves(df[df["type"] == "buy"])
    eq_short, dd_short = _get_subset_curves(df[df["type"] == "sell"])

    # Merge into 3-way format for unified charts
    def _merge_to_list(all_s, long_s, short_s, val_key):
        """Merge all/long/short series into chart rows keyed by date."""
        all_indices = sorted(set(all_s.index) | set(long_s.index) | set(short_s.index))
        if not all_indices:
            return []
        a = (
            all_s.reindex(all_indices)
            .ffill()
            .fillna(initial_balance if "equity" in val_key else 0)
        )
        l = (
            long_s.reindex(all_indices)
            .ffill()
            .fillna(initial_balance if "equity" in val_key else 0)
        )
        s = (
            short_s.reindex(all_indices)
            .ffill()
            .fillna(initial_balance if "equity" in val_key else 0)
        )
        return [
            {
                "date": ts.isoformat(),
                "all": float(a.loc[ts]),
                "long": float(l.loc[ts]),
                "short": float(s.loc[ts]),
            }
            for ts in all_indices
        ]

    equity_chart = _merge_to_list(eq_all, eq_long, eq_short, "equity")
    drawdown_chart = _merge_to_list(dd_all, dd_long, dd_short, "drawdown")

    # 5. Generate Decision Scorecard
    scorecard = {
        "all": decision_scorecard.__evaluate_strategy_quality_impl_impl(
            {
                "summary": summary,
                "metrics": payload_categories["metrics"],
                "ratios": payload_categories["ratios"],
                "drawdowns": payload_categories["drawdowns"],
                "validation": payload_categories["validation"],
            }
        )
    }

    # 6. Extract Dashboard Metrics
    dashboard = _get_dashboard_metrics(analytics)

    return {
        "summary": summary,
        "dashboard": dashboard,
        **payload_categories,
        "scorecard": scorecard,
        "equity_curves": {
            "all": [
                {"date": ts.isoformat(), "equity": float(v)} for ts, v in eq_all.items()
            ],
            "long": [
                {"date": ts.isoformat(), "equity": float(v)}
                for ts, v in eq_long.items()
            ],
            "short": [
                {"date": ts.isoformat(), "equity": float(v)}
                for ts, v in eq_short.items()
            ],
        },
        "charts": {"equity_curve": equity_chart, "drawdown_curve": drawdown_chart},
    }


# =========================================================================
# Agent-Facing Function Tools
# =========================================================================


def _cost_impact(
    tool_name: str,
    field: str,
    costs: list[float],
    gross_profit: float,
    request_id: str | None,
    agent_name: str | None,
    environment: str,
    dry_run: bool,
) -> dict[str, Any]:
    """Calculate total cost and its ratio to gross profit."""
    series = pd.to_numeric(pd.Series(costs), errors="coerce").dropna()
    total = float(series.sum()) if len(series) else 0.0
    return analytics_tool_result(
        tool_name,
        data={
            field: costs,
            "total_cost": total,
            "cost_to_gross_ratio": total / gross_profit if gross_profit else 0.0,
        },
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def _calculate_spread_cost_impact_impl(
    *,
    spread_costs: list[float],
    gross_profit: float,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Calculate spread cost drag.

    Purpose:
        Calculate spread cost drag.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        spread_costs:
            Analytics input consumed by this function.
        gross_profit:
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
    return _cost_impact(
        "calculate_spread_cost_impact",
        "spread_costs",
        spread_costs,
        float(gross_profit),
        request_id,
        agent_name,
        environment,
        dry_run,
    )


def _calculate_slippage_impact_impl(
    *,
    slippage_costs: list[float],
    gross_profit: float,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Calculate slippage cost drag.

    Purpose:
        Calculate slippage cost drag.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        slippage_costs:
            Analytics input consumed by this function.
        gross_profit:
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
    return _cost_impact(
        "calculate_slippage_impact",
        "slippage_costs",
        slippage_costs,
        float(gross_profit),
        request_id,
        agent_name,
        environment,
        dry_run,
    )


def _calculate_commission_impact_impl(
    *,
    commission_costs: list[float],
    gross_profit: float,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Calculate commission cost drag.

    Purpose:
        Calculate commission cost drag.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        commission_costs:
            Analytics input consumed by this function.
        gross_profit:
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
    return _cost_impact(
        "calculate_commission_impact",
        "commission_costs",
        commission_costs,
        float(gross_profit),
        request_id,
        agent_name,
        environment,
        dry_run,
    )


def _build_backtest_report_impl(
    *,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
    **report_sections: Any,
) -> dict[str, Any]:
    """Build a structured backtest analytics report payload.

    Purpose:
        Build a structured backtest analytics report payload.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        request_id:
            Analytics input consumed by this function.
        agent_name:
            Analytics input consumed by this function.
        environment:
            Analytics input consumed by this function.
        dry_run:
            Analytics input consumed by this function.
        **report_sections:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    return analytics_tool_result(
        "build_backtest_report",
        data={"backtest_report": analytics_business_payload(report_sections)},
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def _calculate_analytics_for_subset_impl(
    trades: pd.DataFrame,
    initial_balance: float,
    start_time: pd.Timestamp | str | None = None,
    end_time: pd.Timestamp | str | None = None,
    benchmark_returns_series: pd.Series | None = None,
    benchmark_equity_series: pd.Series | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_analytics_for_subset_impl."""
    try:
        import pandas as pd
        from app.services.utils.logger import logger

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

        arg_benchmark_returns_series = benchmark_returns_series
        if "benchmark_returns_series" in ["trades", "open_trades"] and isinstance(
            arg_benchmark_returns_series, (list, dict)
        ):
            arg_benchmark_returns_series = pd.DataFrame(arg_benchmark_returns_series)
        elif "benchmark_returns_series" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_benchmark_returns_series, list):
            arg_benchmark_returns_series = pd.Series(arg_benchmark_returns_series)
        kwargs["benchmark_returns_series"] = arg_benchmark_returns_series

        arg_benchmark_equity_series = benchmark_equity_series
        if "benchmark_equity_series" in ["trades", "open_trades"] and isinstance(
            arg_benchmark_equity_series, (list, dict)
        ):
            arg_benchmark_equity_series = pd.DataFrame(arg_benchmark_equity_series)
        elif "benchmark_equity_series" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_benchmark_equity_series, list):
            arg_benchmark_equity_series = pd.Series(arg_benchmark_equity_series)
        kwargs["benchmark_equity_series"] = arg_benchmark_equity_series

        res = _calculate_analytics_for_subset_impl(**kwargs)
        logger.info("Executed calculate_analytics_for_subset tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
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
            "calculate_analytics_for_subset",
            data={"calculate_analytics_for_subset": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _get_analytics_overview_impl(
    trades: Any,
    initial_balance: float,
    start_time: Any = None,
    end_time: Any = None,
    benchmark_equity: pd.Series | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _get_analytics_overview_impl."""
    try:
        import pandas as pd
        from app.services.utils.logger import logger

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

        arg_benchmark_equity = benchmark_equity
        if "benchmark_equity" in ["trades", "open_trades"] and isinstance(
            arg_benchmark_equity, (list, dict)
        ):
            arg_benchmark_equity = pd.DataFrame(arg_benchmark_equity)
        elif "benchmark_equity" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_benchmark_equity, list):
            arg_benchmark_equity = pd.Series(arg_benchmark_equity)
        kwargs["benchmark_equity"] = arg_benchmark_equity

        res = _get_analytics_overview_impl(**kwargs)
        logger.info("Executed get_analytics_overview tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
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
            "get_analytics_overview", data={"get_analytics_overview": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _format_summary_as_rows_impl(summary_data: dict[str, Any]) -> dict[str, Any]:
    """AI Tool wrapper for _format_summary_as_rows_impl."""
    try:
        import pandas as pd
        from app.services.utils.logger import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_summary_data = summary_data
        if "summary_data" in ["trades", "open_trades"] and isinstance(
            arg_summary_data, (list, dict)
        ):
            arg_summary_data = pd.DataFrame(arg_summary_data)
        elif "summary_data" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_summary_data, list):
            arg_summary_data = pd.Series(arg_summary_data)
        kwargs["summary_data"] = arg_summary_data

        res = _format_summary_as_rows_impl(**kwargs)
        logger.info("Executed format_summary_as_rows tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
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
            "format_summary_as_rows", data={"format_summary_as_rows": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _build_overview_payload_impl(
    trades: Any,
    initial_balance: float,
    start_time: Any = None,
    end_time: Any = None,
    equity_curve_records: list[Any] | None = None,
    summary_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _build_overview_payload_impl."""
    try:
        import pandas as pd
        from app.services.utils.logger import logger

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

        arg_equity_curve_records = equity_curve_records
        if "equity_curve_records" in ["trades", "open_trades"] and isinstance(
            arg_equity_curve_records, (list, dict)
        ):
            arg_equity_curve_records = pd.DataFrame(arg_equity_curve_records)
        elif "equity_curve_records" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_equity_curve_records, list):
            arg_equity_curve_records = pd.Series(arg_equity_curve_records)
        kwargs["equity_curve_records"] = arg_equity_curve_records

        arg_summary_overrides = summary_overrides
        if "summary_overrides" in ["trades", "open_trades"] and isinstance(
            arg_summary_overrides, (list, dict)
        ):
            arg_summary_overrides = pd.DataFrame(arg_summary_overrides)
        elif "summary_overrides" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_summary_overrides, list):
            arg_summary_overrides = pd.Series(arg_summary_overrides)
        kwargs["summary_overrides"] = arg_summary_overrides

        res = _build_overview_payload_core(**kwargs)
        logger.info("Executed build_overview_payload tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
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
            "build_overview_payload", data={"build_overview_payload": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _calculate_spread_cost_impact_impl(
    *,
    spread_costs: list[float],
    gross_profit: float,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_spread_cost_impact_impl."""
    try:
        import pandas as pd
        from app.services.utils.logger import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_spread_costs = spread_costs
        if "spread_costs" in ["trades", "open_trades"] and isinstance(
            arg_spread_costs, (list, dict)
        ):
            arg_spread_costs = pd.DataFrame(arg_spread_costs)
        elif "spread_costs" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_spread_costs, list):
            arg_spread_costs = pd.Series(arg_spread_costs)
        kwargs["spread_costs"] = arg_spread_costs

        arg_gross_profit = gross_profit
        if "gross_profit" in ["trades", "open_trades"] and isinstance(
            arg_gross_profit, (list, dict)
        ):
            arg_gross_profit = pd.DataFrame(arg_gross_profit)
        elif "gross_profit" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_gross_profit, list):
            arg_gross_profit = pd.Series(arg_gross_profit)
        kwargs["gross_profit"] = arg_gross_profit

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

        res = _calculate_spread_cost_impact_impl(**kwargs)
        logger.info("Executed calculate_spread_cost_impact tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
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
            "calculate_spread_cost_impact",
            data={"calculate_spread_cost_impact": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _calculate_slippage_impact_impl(
    *,
    slippage_costs: list[float],
    gross_profit: float,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_slippage_impact_impl."""
    try:
        import pandas as pd
        from app.services.utils.logger import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_slippage_costs = slippage_costs
        if "slippage_costs" in ["trades", "open_trades"] and isinstance(
            arg_slippage_costs, (list, dict)
        ):
            arg_slippage_costs = pd.DataFrame(arg_slippage_costs)
        elif "slippage_costs" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_slippage_costs, list):
            arg_slippage_costs = pd.Series(arg_slippage_costs)
        kwargs["slippage_costs"] = arg_slippage_costs

        arg_gross_profit = gross_profit
        if "gross_profit" in ["trades", "open_trades"] and isinstance(
            arg_gross_profit, (list, dict)
        ):
            arg_gross_profit = pd.DataFrame(arg_gross_profit)
        elif "gross_profit" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_gross_profit, list):
            arg_gross_profit = pd.Series(arg_gross_profit)
        kwargs["gross_profit"] = arg_gross_profit

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

        res = _calculate_slippage_impact_impl(**kwargs)
        logger.info("Executed calculate_slippage_impact tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
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
            "calculate_slippage_impact",
            data={"calculate_slippage_impact": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _calculate_commission_impact_impl(
    *,
    commission_costs: list[float],
    gross_profit: float,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_commission_impact_impl."""
    try:
        import pandas as pd
        from app.services.utils.logger import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_commission_costs = commission_costs
        if "commission_costs" in ["trades", "open_trades"] and isinstance(
            arg_commission_costs, (list, dict)
        ):
            arg_commission_costs = pd.DataFrame(arg_commission_costs)
        elif "commission_costs" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_commission_costs, list):
            arg_commission_costs = pd.Series(arg_commission_costs)
        kwargs["commission_costs"] = arg_commission_costs

        arg_gross_profit = gross_profit
        if "gross_profit" in ["trades", "open_trades"] and isinstance(
            arg_gross_profit, (list, dict)
        ):
            arg_gross_profit = pd.DataFrame(arg_gross_profit)
        elif "gross_profit" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_gross_profit, list):
            arg_gross_profit = pd.Series(arg_gross_profit)
        kwargs["gross_profit"] = arg_gross_profit

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

        res = _calculate_commission_impact_impl(**kwargs)
        logger.info("Executed calculate_commission_impact tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
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
            "calculate_commission_impact",
            data={"calculate_commission_impact": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _build_backtest_report_impl(
    *,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
    **report_sections: Any,
) -> dict[str, Any]:
    """AI Tool wrapper for _build_backtest_report_impl."""
    try:
        import pandas as pd
        from app.services.utils.logger import logger

        from .common import analytics_tool_result

        kwargs = {}

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

        arg_report_sections = report_sections
        if "report_sections" in ["trades", "open_trades"] and isinstance(
            arg_report_sections, (list, dict)
        ):
            arg_report_sections = pd.DataFrame(arg_report_sections)
        elif "report_sections" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_report_sections, list):
            arg_report_sections = pd.Series(arg_report_sections)
        kwargs["report_sections"] = arg_report_sections

        res = _build_backtest_report_impl(**kwargs)
        logger.info("Executed build_backtest_report tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
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
            "build_backtest_report", data={"build_backtest_report": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def calculate_analytics_for_subset(
    trades: pd.DataFrame,
    initial_balance: float,
    start_time: pd.Timestamp | str | None = None,
    end_time: pd.Timestamp | str | None = None,
    benchmark_returns_series: pd.Series | None = None,
    benchmark_equity_series: pd.Series | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_analytics_for_subset_impl."""
    try:
        import pandas as pd
        from app.services.utils.logger import logger

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

        arg_benchmark_returns_series = benchmark_returns_series
        if "benchmark_returns_series" in ["trades", "open_trades"] and isinstance(
            arg_benchmark_returns_series, (list, dict)
        ):
            arg_benchmark_returns_series = pd.DataFrame(arg_benchmark_returns_series)
        elif "benchmark_returns_series" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_benchmark_returns_series, list):
            arg_benchmark_returns_series = pd.Series(arg_benchmark_returns_series)
        kwargs["benchmark_returns_series"] = arg_benchmark_returns_series

        arg_benchmark_equity_series = benchmark_equity_series
        if "benchmark_equity_series" in ["trades", "open_trades"] and isinstance(
            arg_benchmark_equity_series, (list, dict)
        ):
            arg_benchmark_equity_series = pd.DataFrame(arg_benchmark_equity_series)
        elif "benchmark_equity_series" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_benchmark_equity_series, list):
            arg_benchmark_equity_series = pd.Series(arg_benchmark_equity_series)
        kwargs["benchmark_equity_series"] = arg_benchmark_equity_series

        res = _calculate_analytics_for_subset_impl(**kwargs)
        logger.info("Executed calculate_analytics_for_subset tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
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
            "calculate_analytics_for_subset",
            data={"calculate_analytics_for_subset": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def get_analytics_overview(
    trades: Any,
    initial_balance: float,
    start_time: Any = None,
    end_time: Any = None,
    benchmark_equity: pd.Series | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _get_analytics_overview_impl."""
    try:
        import pandas as pd
        from app.services.utils.logger import logger

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

        arg_benchmark_equity = benchmark_equity
        if "benchmark_equity" in ["trades", "open_trades"] and isinstance(
            arg_benchmark_equity, (list, dict)
        ):
            arg_benchmark_equity = pd.DataFrame(arg_benchmark_equity)
        elif "benchmark_equity" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_benchmark_equity, list):
            arg_benchmark_equity = pd.Series(arg_benchmark_equity)
        kwargs["benchmark_equity"] = arg_benchmark_equity

        res = _get_analytics_overview_impl(**kwargs)
        logger.info("Executed get_analytics_overview tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
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
            "get_analytics_overview", data={"get_analytics_overview": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def format_summary_as_rows(summary_data: dict[str, Any]) -> dict[str, Any]:
    """AI Tool wrapper for _format_summary_as_rows_impl."""
    try:
        import pandas as pd
        from app.services.utils.logger import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_summary_data = summary_data
        if "summary_data" in ["trades", "open_trades"] and isinstance(
            arg_summary_data, (list, dict)
        ):
            arg_summary_data = pd.DataFrame(arg_summary_data)
        elif "summary_data" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_summary_data, list):
            arg_summary_data = pd.Series(arg_summary_data)
        kwargs["summary_data"] = arg_summary_data

        res = _format_summary_as_rows_impl(**kwargs)
        logger.info("Executed format_summary_as_rows tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
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
            "format_summary_as_rows", data={"format_summary_as_rows": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def build_overview_payload(
    trades: Any,
    initial_balance: float,
    start_time: Any = None,
    end_time: Any = None,
    equity_curve_records: list[Any] | None = None,
    summary_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _build_overview_payload_impl."""
    try:
        import pandas as pd
        from app.services.utils.logger import logger

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

        arg_equity_curve_records = equity_curve_records
        if "equity_curve_records" in ["trades", "open_trades"] and isinstance(
            arg_equity_curve_records, (list, dict)
        ):
            arg_equity_curve_records = pd.DataFrame(arg_equity_curve_records)
        elif "equity_curve_records" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_equity_curve_records, list):
            arg_equity_curve_records = pd.Series(arg_equity_curve_records)
        kwargs["equity_curve_records"] = arg_equity_curve_records

        arg_summary_overrides = summary_overrides
        if "summary_overrides" in ["trades", "open_trades"] and isinstance(
            arg_summary_overrides, (list, dict)
        ):
            arg_summary_overrides = pd.DataFrame(arg_summary_overrides)
        elif "summary_overrides" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_summary_overrides, list):
            arg_summary_overrides = pd.Series(arg_summary_overrides)
        kwargs["summary_overrides"] = arg_summary_overrides

        res = _build_overview_payload_core(**kwargs)
        logger.info("Executed build_overview_payload tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
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
            "build_overview_payload", data={"build_overview_payload": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def calculate_spread_cost_impact(
    *,
    spread_costs: list[float],
    gross_profit: float,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_spread_cost_impact_impl."""
    try:
        import pandas as pd
        from app.services.utils.logger import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_spread_costs = spread_costs
        if "spread_costs" in ["trades", "open_trades"] and isinstance(
            arg_spread_costs, (list, dict)
        ):
            arg_spread_costs = pd.DataFrame(arg_spread_costs)
        elif "spread_costs" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_spread_costs, list):
            arg_spread_costs = pd.Series(arg_spread_costs)
        kwargs["spread_costs"] = arg_spread_costs

        arg_gross_profit = gross_profit
        if "gross_profit" in ["trades", "open_trades"] and isinstance(
            arg_gross_profit, (list, dict)
        ):
            arg_gross_profit = pd.DataFrame(arg_gross_profit)
        elif "gross_profit" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_gross_profit, list):
            arg_gross_profit = pd.Series(arg_gross_profit)
        kwargs["gross_profit"] = arg_gross_profit

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

        res = _calculate_spread_cost_impact_impl(**kwargs)
        logger.info("Executed calculate_spread_cost_impact tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
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
            "calculate_spread_cost_impact",
            data={"calculate_spread_cost_impact": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def calculate_slippage_impact(
    *,
    slippage_costs: list[float],
    gross_profit: float,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_slippage_impact_impl."""
    try:
        import pandas as pd
        from app.services.utils.logger import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_slippage_costs = slippage_costs
        if "slippage_costs" in ["trades", "open_trades"] and isinstance(
            arg_slippage_costs, (list, dict)
        ):
            arg_slippage_costs = pd.DataFrame(arg_slippage_costs)
        elif "slippage_costs" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_slippage_costs, list):
            arg_slippage_costs = pd.Series(arg_slippage_costs)
        kwargs["slippage_costs"] = arg_slippage_costs

        arg_gross_profit = gross_profit
        if "gross_profit" in ["trades", "open_trades"] and isinstance(
            arg_gross_profit, (list, dict)
        ):
            arg_gross_profit = pd.DataFrame(arg_gross_profit)
        elif "gross_profit" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_gross_profit, list):
            arg_gross_profit = pd.Series(arg_gross_profit)
        kwargs["gross_profit"] = arg_gross_profit

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

        res = _calculate_slippage_impact_impl(**kwargs)
        logger.info("Executed calculate_slippage_impact tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
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
            "calculate_slippage_impact",
            data={"calculate_slippage_impact": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def calculate_commission_impact(
    *,
    commission_costs: list[float],
    gross_profit: float,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_commission_impact_impl."""
    try:
        import pandas as pd
        from app.services.utils.logger import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_commission_costs = commission_costs
        if "commission_costs" in ["trades", "open_trades"] and isinstance(
            arg_commission_costs, (list, dict)
        ):
            arg_commission_costs = pd.DataFrame(arg_commission_costs)
        elif "commission_costs" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_commission_costs, list):
            arg_commission_costs = pd.Series(arg_commission_costs)
        kwargs["commission_costs"] = arg_commission_costs

        arg_gross_profit = gross_profit
        if "gross_profit" in ["trades", "open_trades"] and isinstance(
            arg_gross_profit, (list, dict)
        ):
            arg_gross_profit = pd.DataFrame(arg_gross_profit)
        elif "gross_profit" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_gross_profit, list):
            arg_gross_profit = pd.Series(arg_gross_profit)
        kwargs["gross_profit"] = arg_gross_profit

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

        res = _calculate_commission_impact_impl(**kwargs)
        logger.info("Executed calculate_commission_impact tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
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
            "calculate_commission_impact",
            data={"calculate_commission_impact": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def build_backtest_report(
    *,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
    **report_sections: Any,
) -> dict[str, Any]:
    """AI Tool wrapper for _build_backtest_report_impl."""
    try:
        import pandas as pd
        from app.services.utils.logger import logger

        from .common import analytics_tool_result

        kwargs = {}

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

        arg_report_sections = report_sections
        if "report_sections" in ["trades", "open_trades"] and isinstance(
            arg_report_sections, (list, dict)
        ):
            arg_report_sections = pd.DataFrame(arg_report_sections)
        elif "report_sections" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_report_sections, list):
            arg_report_sections = pd.Series(arg_report_sections)
        kwargs["report_sections"] = arg_report_sections

        res = _build_backtest_report_impl(**kwargs)
        logger.info("Executed build_backtest_report tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
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
            "build_backtest_report", data={"build_backtest_report": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}
