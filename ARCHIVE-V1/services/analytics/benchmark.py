"""benchmark.py - Calculate benchmark-relative analytics for strategy return streams.

This module provides tools to compare strategy performance against a benchmark,
including relative risk (beta), relative return (alpha), and capture ratios.

Classes:
    None.

Functions:
    _clean_series: Normalize numeric series, replace infinities, drop NaNs, and sort by index.
    _align_returns: Align two return series by their index, dropping missing periods.
    benchmark_returns: Generate a return series from benchmark equity (AI Tool).
    _benchmark_returns_impl: Core logic for generating benchmark returns.
    beta: Beta coefficient relative to the benchmark (AI Tool).
    _beta_impl: Core logic for calculating beta.
    alpha: Annualized Jensen's Alpha (AI Tool).
    _alpha_impl: Core logic for calculating alpha.
    r_squared: R-squared coefficient (AI Tool).
    _r_squared_impl: Core logic for calculating R-squared.
    tracking_error: Annualized Tracking Error (AI Tool).
    _tracking_error_impl: Core logic for calculating tracking error.
    information_ratio: Information Ratio (AI Tool).
    _information_ratio_impl: Core logic for calculating information ratio.
    relative_drawdown_series: Generate relative underperformance series (AI Tool).
    _relative_drawdown_series_impl: Core logic for relative drawdown.
    max_relative_drawdown_percent: Maximum relative underperformance (AI Tool).
    _max_relative_drawdown_percent_impl: Core logic for max relative drawdown.
    batting_average: Percentage of periods outperforming benchmark (AI Tool).
    _batting_average_impl: Core logic for batting average.
    up_down_capture: Calculate Up and Down Capture Ratios (AI Tool).
    _up_down_capture_impl: Core logic for capture ratios.
    calculate_benchmark_metrics: Comprehensive alpha and beta calculation (AI Tool).
    _calculate_benchmark_metrics_impl: Core logic for combined benchmark metrics.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from app.services.analytics.common import EPSILON, analytics_tool_result
from app.services.utils.logger import logger

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
# Shared Helpers & Alignment
# =========================================================================


def _clean_series(data: pd.Series) -> pd.Series:
    """Normalize numeric series, replace infinities, drop NaNs, and sort by index.

    Args:
        data: The input pandas Series.

    Returns:
        A cleaned pandas Series of floats.
    """
    s = pd.to_numeric(data, errors="coerce")
    s = s.replace([np.inf, -np.inf], np.nan).dropna()

    # Ensure index is datetime-like for resampling safety
    if not isinstance(s.index, pd.DatetimeIndex):
        try:
            s.index = pd.to_datetime(s.index)
        except (ValueError, TypeError):
            pass

    return s.astype(float).sort_index()


def _align_returns(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
) -> pd.DataFrame:
    """Align two return series by their index, dropping missing periods.

    Args:
        strategy_returns: Return series for the strategy.
        benchmark_returns: Return series for the benchmark.

    Returns:
        A aligned DataFrame with 'strategy' and 'benchmark' columns.
    """
    s = _clean_series(strategy_returns)
    b = _clean_series(benchmark_returns)

    aligned = pd.DataFrame({"strategy": s, "benchmark": b}).dropna()
    return aligned


# =========================================================================
# Benchmark Data Processing
# =========================================================================


def _benchmark_returns_impl(
    benchmark_equity: pd.Series, freq: str | None = None
) -> pd.Series:
    """Core logic for generating a return series from benchmark equity (prices).

    Args:
        benchmark_equity: Series of benchmark prices/equity.
        freq: Optional resampling frequency.

    Returns:
        A pandas Series of returns.
    """
    equity = _clean_series(benchmark_equity)
    if len(equity) < 2:
        return pd.Series(dtype=float)

    if freq is not None:
        equity = equity.resample(freq).last().ffill()

    rets = equity.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    return rets


# =========================================================================
# Relative Risk & Return
# =========================================================================


def _beta_impl(strategy_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Core logic for calculating Beta coefficient relative to the benchmark.

    Args:
        strategy_returns: Series of strategy returns.
        benchmark_returns: Series of benchmark returns.

    Returns:
        The beta coefficient (float).
    """
    aligned = _align_returns(strategy_returns, benchmark_returns)
    if len(aligned) < 2:
        return 0.0

    cov = aligned["strategy"].cov(aligned["benchmark"])
    var_bench = aligned["benchmark"].var()

    if pd.isna(cov) or pd.isna(var_bench) or var_bench < 1e-12:
        return 0.0

    return float(cov / var_bench)


def _alpha_impl(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    """Core logic for calculating annualized Jensen's Alpha (Percentage).

    Args:
        strategy_returns: Series of strategy returns.
        benchmark_returns: Series of benchmark returns.
        risk_free_rate: Annualized risk-free rate.
        periods_per_year: Number of periods in a year.

    Returns:
        The annualized alpha as a percentage.
    """
    aligned = _align_returns(strategy_returns, benchmark_returns)
    if len(aligned) < 2:
        return 0.0

    # Convert annual risk-free rate to period rate
    period_rf = risk_free_rate / periods_per_year

    s_avg = aligned["strategy"].mean()
    b_avg = aligned["benchmark"].mean()

    b_val = _beta_impl(aligned["strategy"], aligned["benchmark"])

    # Alpha per period
    alpha_period = (s_avg - period_rf) - b_val * (b_avg - period_rf)

    return float(alpha_period * periods_per_year * 100.0)


def _r_squared_impl(strategy_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Core logic for calculating R-squared (Coefficient of Determination).

    Args:
        strategy_returns: Series of strategy returns.
        benchmark_returns: Series of benchmark returns.

    Returns:
        R-squared value (0 to 1).
    """
    aligned = _align_returns(strategy_returns, benchmark_returns)
    if len(aligned) < 2:
        return 0.0

    corr = aligned["strategy"].corr(aligned["benchmark"])
    if pd.isna(corr):
        return 0.0

    return float(corr**2)


def _tracking_error_impl(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    periods_per_year: int = 252,
) -> float:
    """Core logic for calculating annualized Tracking Error (Percentage).

    Args:
        strategy_returns: Series of strategy returns.
        benchmark_returns: Series of benchmark returns.
        periods_per_year: Number of periods in a year.

    Returns:
        Annualized tracking error as a percentage.
    """
    aligned = _align_returns(strategy_returns, benchmark_returns)
    if len(aligned) < 2:
        return 0.0

    excess = aligned["strategy"] - aligned["benchmark"]
    te_period = excess.std(ddof=1)

    if pd.isna(te_period) or te_period < 1e-12:
        return 0.0

    return float(te_period * np.sqrt(periods_per_year) * 100.0)


def _information_ratio_impl(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    periods_per_year: int = 252,
) -> float:
    """Core logic for calculating Information Ratio.

    Args:
        strategy_returns: Series of strategy returns.
        benchmark_returns: Series of benchmark returns.
        periods_per_year: Number of periods in a year.

    Returns:
        The Information Ratio.
    """
    aligned = _align_returns(strategy_returns, benchmark_returns)
    if len(aligned) < 2:
        return 0.0

    excess_rets = aligned["strategy"] - aligned["benchmark"]
    avg_excess = excess_rets.mean()
    te_period = excess_rets.std(ddof=1)

    if pd.isna(te_period) or te_period < 1e-12:
        return 0.0

    return float((avg_excess / te_period) * np.sqrt(periods_per_year))


# =========================================================================
# Relative Drawdown & Underperformance
# =========================================================================


def _relative_drawdown_series_impl(
    strategy_equity: pd.Series, benchmark_equity: pd.Series
) -> pd.Series:
    """Core logic for generating a series of relative underperformance.

    Args:
        strategy_equity: Series of strategy equity/prices.
        benchmark_equity: Series of benchmark equity/prices.

    Returns:
        A pandas Series of relative drawdown values.
    """
    s = _clean_series(strategy_equity)
    b = _clean_series(benchmark_equity)

    aligned = pd.DataFrame({"strategy": s, "benchmark": b}).dropna()
    aligned = aligned[aligned["benchmark"].abs() > 1e-12]

    if aligned.empty:
        return pd.Series(dtype=float)

    rel_eq = aligned["strategy"] / aligned["benchmark"]
    rel_dd = (rel_eq / rel_eq.expanding().max()) - 1.0
    return rel_dd


def _max_relative_drawdown_percent_impl(
    strategy_equity: pd.Series, benchmark_equity: pd.Series
) -> float:
    """Core logic for calculating maximum relative underperformance percentage.

    Args:
        strategy_equity: Series of strategy equity/prices.
        benchmark_equity: Series of benchmark equity/prices.

    Returns:
        Max relative drawdown as a positive percentage.
    """
    dd_series = _relative_drawdown_series_impl(strategy_equity, benchmark_equity)
    if dd_series.empty:
        return 0.0
    return float(abs(dd_series.min()) * 100.0)


# =========================================================================
# Market Capture & Frequency
# =========================================================================


def _batting_average_impl(
    strategy_returns: pd.Series, benchmark_returns: pd.Series
) -> float:
    """Core logic for calculating percentage of periods where strategy outperformed benchmark.

    Args:
        strategy_returns: Series of strategy returns.
        benchmark_returns: Series of benchmark returns.

    Returns:
        The batting average percentage.
    """
    aligned = _align_returns(strategy_returns, benchmark_returns)
    if len(aligned) == 0:
        return 0.0

    better = (aligned["strategy"] > aligned["benchmark"]).sum()
    return float(better / len(aligned) * 100.0)


def _up_down_capture_impl(
    strategy_returns: pd.Series, benchmark_returns: pd.Series
) -> tuple[float, float]:
    """Core logic for calculating Up and Down Capture Ratios.

    Args:
        strategy_returns: Series of strategy returns.
        benchmark_returns: Series of benchmark returns.

    Returns:
        A tuple of (up_capture, down_capture) percentages.
    """
    aligned = _align_returns(strategy_returns, benchmark_returns)
    if len(aligned) == 0:
        return 0.0, 0.0

    up_market = aligned[aligned["benchmark"] > 0]
    down_market = aligned[aligned["benchmark"] < 0]

    up_cap = 0.0
    if not up_market.empty:
        up_bench_avg = up_market["benchmark"].mean()
        if up_bench_avg > EPSILON:
            up_cap = (up_market["strategy"].mean() / up_bench_avg) * 100.0

    down_cap = 0.0
    if not down_market.empty:
        down_bench_avg = down_market["benchmark"].mean()
        if abs(down_bench_avg) > EPSILON:
            down_cap = (down_market["strategy"].mean() / down_bench_avg) * 100.0

    return float(up_cap), float(down_cap)


def _calculate_benchmark_metrics_impl(
    returns: pd.Series,
    benchmark_returns: pd.Series,
) -> dict[str, float]:
    """Core logic for calculating combined benchmark metrics (alpha and beta).

    Args:
        returns: Series of strategy returns.
        benchmark_returns: Series of benchmark returns.

    Returns:
        A dictionary containing alpha and beta.
    """
    count = min(len(returns), len(benchmark_returns))
    if count < 2:
        return {"alpha": 0.0, "beta": 0.0}

    s = returns.iloc[:count]
    b = benchmark_returns.iloc[:count]

    benchmark_var = np.var(b)
    beta_val = (
        float(np.cov(s, b)[0, 1] / benchmark_var) if benchmark_var > 1e-12 else 0.0
    )
    alpha_val = float(s.mean() - beta_val * b.mean())

    return {"alpha": alpha_val, "beta": beta_val}


# =========================================================================
# AI Tool Wrappers (Rule 3)
# =========================================================================


def _benchmark_returns_impl(
    benchmark_equity: pd.Series | list[float], freq: str | None = None
) -> dict[str, Any]:
    """Generate a return series from benchmark equity (AI Tool).

    Args:
        benchmark_equity: Series or list of benchmark prices.
        freq: Optional resampling frequency.

    Returns:
        Standard tool result with returns data.
    """
    try:
        # Input Validation
        s = (
            pd.Series(benchmark_equity)
            if isinstance(benchmark_equity, list)
            else benchmark_equity
        )

        # Core Execution
        result = _benchmark_returns_impl(s, freq)

        # Structured Return
        logger.info("Executed benchmark_returns tool successfully.")
        return analytics_tool_result(
            "benchmark_returns", data={"returns": result.tolist()}
        )
    except Exception as e:
        logger.error(f"Error in benchmark_returns: {e!s}")
        return {"status": "error", "message": str(e)}


def _beta_impl(
    strategy_returns: pd.Series | list[float],
    benchmark_returns: pd.Series | list[float],
) -> dict[str, Any]:
    """Calculate beta coefficient relative to the benchmark (AI Tool).

    Args:
        strategy_returns: Series or list of strategy returns.
        benchmark_returns: Series or list of benchmark returns.

    Returns:
        Standard tool result with beta value.
    """
    try:
        s = (
            pd.Series(strategy_returns)
            if isinstance(strategy_returns, list)
            else strategy_returns
        )
        b = (
            pd.Series(benchmark_returns)
            if isinstance(benchmark_returns, list)
            else benchmark_returns
        )

        result = _beta_impl(s, b)

        logger.info("Executed beta tool successfully.")
        return analytics_tool_result("beta", data={"beta": result})
    except Exception as e:
        logger.error(f"Error in beta: {e!s}")
        return {"status": "error", "message": str(e)}


def _alpha_impl(
    strategy_returns: pd.Series | list[float],
    benchmark_returns: pd.Series | list[float],
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> dict[str, Any]:
    """Calculate annualized Jensen's Alpha (AI Tool).

    Args:
        strategy_returns: Series or list of strategy returns.
        benchmark_returns: Series or list of benchmark returns.
        risk_free_rate: Annualized risk-free rate.
        periods_per_year: Periods in a year.

    Returns:
        Standard tool result with alpha value.
    """
    try:
        s = (
            pd.Series(strategy_returns)
            if isinstance(strategy_returns, list)
            else strategy_returns
        )
        b = (
            pd.Series(benchmark_returns)
            if isinstance(benchmark_returns, list)
            else benchmark_returns
        )

        result = _alpha_impl(s, b, risk_free_rate, periods_per_year)

        logger.info("Executed alpha tool successfully.")
        return analytics_tool_result("alpha", data={"alpha": result})
    except Exception as e:
        logger.error(f"Error in alpha: {e!s}")
        return {"status": "error", "message": str(e)}


def _r_squared_impl(
    strategy_returns: pd.Series | list[float],
    benchmark_returns: pd.Series | list[float],
) -> dict[str, Any]:
    """Calculate R-squared coefficient (AI Tool).

    Args:
        strategy_returns: Series or list of strategy returns.
        benchmark_returns: Series or list of benchmark returns.

    Returns:
        Standard tool result with R-squared value.
    """
    try:
        s = (
            pd.Series(strategy_returns)
            if isinstance(strategy_returns, list)
            else strategy_returns
        )
        b = (
            pd.Series(benchmark_returns)
            if isinstance(benchmark_returns, list)
            else benchmark_returns
        )

        result = _r_squared_impl(s, b)

        logger.info("Executed r_squared tool successfully.")
        return analytics_tool_result("r_squared", data={"r_squared": result})
    except Exception as e:
        logger.error(f"Error in r_squared: {e!s}")
        return {"status": "error", "message": str(e)}


def _tracking_error_impl(
    strategy_returns: pd.Series | list[float],
    benchmark_returns: pd.Series | list[float],
    periods_per_year: int = 252,
) -> dict[str, Any]:
    """Calculate annualized Tracking Error (AI Tool).

    Args:
        strategy_returns: Series or list of strategy returns.
        benchmark_returns: Series or list of benchmark returns.
        periods_per_year: Periods in a year.

    Returns:
        Standard tool result with tracking error.
    """
    try:
        s = (
            pd.Series(strategy_returns)
            if isinstance(strategy_returns, list)
            else strategy_returns
        )
        b = (
            pd.Series(benchmark_returns)
            if isinstance(benchmark_returns, list)
            else benchmark_returns
        )

        result = _tracking_error_impl(s, b, periods_per_year)

        logger.info("Executed tracking_error tool successfully.")
        return analytics_tool_result("tracking_error", data={"tracking_error": result})
    except Exception as e:
        logger.error(f"Error in tracking_error: {e!s}")
        return {"status": "error", "message": str(e)}


def _information_ratio_impl(
    strategy_returns: pd.Series | list[float],
    benchmark_returns: pd.Series | list[float],
    periods_per_year: int = 252,
) -> dict[str, Any]:
    """Calculate Information Ratio (AI Tool).

    Args:
        strategy_returns: Series or list of strategy returns.
        benchmark_returns: Series or list of benchmark returns.
        periods_per_year: Periods in a year.

    Returns:
        Standard tool result with information ratio.
    """
    try:
        s = (
            pd.Series(strategy_returns)
            if isinstance(strategy_returns, list)
            else strategy_returns
        )
        b = (
            pd.Series(benchmark_returns)
            if isinstance(benchmark_returns, list)
            else benchmark_returns
        )

        result = _information_ratio_impl(s, b, periods_per_year)

        logger.info("Executed information_ratio tool successfully.")
        return analytics_tool_result(
            "information_ratio", data={"information_ratio": result}
        )
    except Exception as e:
        logger.error(f"Error in information_ratio: {e!s}")
        return {"status": "error", "message": str(e)}


def _relative_drawdown_series_impl(
    strategy_equity: pd.Series | list[float], benchmark_equity: pd.Series | list[float]
) -> dict[str, Any]:
    """Generate relative underperformance series (AI Tool).

    Args:
        strategy_equity: Series or list of strategy prices.
        benchmark_equity: Series or list of benchmark prices.

    Returns:
        Standard tool result with relative drawdown series.
    """
    try:
        s = (
            pd.Series(strategy_equity)
            if isinstance(strategy_equity, list)
            else strategy_equity
        )
        b = (
            pd.Series(benchmark_equity)
            if isinstance(benchmark_equity, list)
            else benchmark_equity
        )

        result = _relative_drawdown_series_impl(s, b)

        logger.info("Executed relative_drawdown_series tool successfully.")
        return analytics_tool_result(
            "relative_drawdown_series", data={"relative_drawdown": result.tolist()}
        )
    except Exception as e:
        logger.error(f"Error in relative_drawdown_series: {e!s}")
        return {"status": "error", "message": str(e)}


def _max_relative_drawdown_percent_impl(
    strategy_equity: pd.Series | list[float], benchmark_equity: pd.Series | list[float]
) -> dict[str, Any]:
    """Calculate maximum relative underperformance percentage (AI Tool).

    Args:
        strategy_equity: Series or list of strategy prices.
        benchmark_equity: Series or list of benchmark prices.

    Returns:
        Standard tool result with max relative drawdown value.
    """
    try:
        s = (
            pd.Series(strategy_equity)
            if isinstance(strategy_equity, list)
            else strategy_equity
        )
        b = (
            pd.Series(benchmark_equity)
            if isinstance(benchmark_equity, list)
            else benchmark_equity
        )

        result = _max_relative_drawdown_percent_impl(s, b)

        logger.info("Executed max_relative_drawdown_percent tool successfully.")
        return analytics_tool_result(
            "max_relative_drawdown_percent",
            data={"max_relative_drawdown_percent": result},
        )
    except Exception as e:
        logger.error(f"Error in max_relative_drawdown_percent: {e!s}")
        return {"status": "error", "message": str(e)}


def _batting_average_impl(
    strategy_returns: pd.Series | list[float],
    benchmark_returns: pd.Series | list[float],
) -> dict[str, Any]:
    """Calculate percentage of periods where strategy outperformed benchmark (AI Tool).

    Args:
        strategy_returns: Series or list of strategy returns.
        benchmark_returns: Series or list of benchmark returns.

    Returns:
        Standard tool result with batting average value.
    """
    try:
        s = (
            pd.Series(strategy_returns)
            if isinstance(strategy_returns, list)
            else strategy_returns
        )
        b = (
            pd.Series(benchmark_returns)
            if isinstance(benchmark_returns, list)
            else benchmark_returns
        )

        result = _batting_average_impl(s, b)

        logger.info("Executed batting_average tool successfully.")
        return analytics_tool_result(
            "batting_average", data={"batting_average": result}
        )
    except Exception as e:
        logger.error(f"Error in batting_average: {e!s}")
        return {"status": "error", "message": str(e)}


def _up_down_capture_impl(
    strategy_returns: pd.Series | list[float],
    benchmark_returns: pd.Series | list[float],
) -> dict[str, Any]:
    """Calculate Up and Down Capture Ratios (AI Tool).

    Args:
        strategy_returns: Series or list of strategy returns.
        benchmark_returns: Series or list of benchmark returns.

    Returns:
        Standard tool result with capture ratios.
    """
    try:
        s = (
            pd.Series(strategy_returns)
            if isinstance(strategy_returns, list)
            else strategy_returns
        )
        b = (
            pd.Series(benchmark_returns)
            if isinstance(benchmark_returns, list)
            else benchmark_returns
        )

        up, down = _up_down_capture_impl(s, b)

        logger.info("Executed up_down_capture tool successfully.")
        return analytics_tool_result(
            "up_down_capture", data={"up_capture": up, "down_capture": down}
        )
    except Exception as e:
        logger.error(f"Error in up_down_capture: {e!s}")
        return {"status": "error", "message": str(e)}


def _calculate_benchmark_metrics_impl(
    *,
    returns: list[float],
    benchmark_returns: list[float],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Comprehensive alpha and beta calculation (AI Tool).

    Args:
        returns: List of strategy returns.
        benchmark_returns: List of benchmark returns.
        request_id: Request identifier.
        agent_name: Agent name.
        environment: Execution environment.
        dry_run: Dry run flag.

    Returns:
        Standard tool result with alpha and beta values.
    """
    try:
        s = pd.Series(returns)
        b = pd.Series(benchmark_returns)

        metrics = _calculate_benchmark_metrics_impl(s, b)

        logger.info("Executed calculate_benchmark_metrics tool successfully.")
        return analytics_tool_result(
            "calculate_benchmark_metrics",
            data=metrics,
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )
    except Exception as e:
        logger.error(f"Error in calculate_benchmark_metrics: {e!s}")
        return {"status": "error", "message": str(e)}


def benchmark_returns(
    benchmark_equity: pd.Series, freq: str | None = None
) -> dict[str, Any]:
    """AI Tool wrapper for _benchmark_returns_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

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

        arg_freq = freq
        if "freq" in ["trades", "open_trades"] and isinstance(arg_freq, (list, dict)):
            arg_freq = pd.DataFrame(arg_freq)
        elif "freq" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_freq, list):
            arg_freq = pd.Series(arg_freq)
        kwargs["freq"] = arg_freq

        res = _benchmark_returns_impl(**kwargs)
        logger.info("Executed benchmark_returns tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "benchmark_returns", data={"benchmark_returns": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def beta(strategy_returns: pd.Series, benchmark_returns: pd.Series) -> dict[str, Any]:
    """AI Tool wrapper for _beta_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_strategy_returns = strategy_returns
        if "strategy_returns" in ["trades", "open_trades"] and isinstance(
            arg_strategy_returns, (list, dict)
        ):
            arg_strategy_returns = pd.DataFrame(arg_strategy_returns)
        elif "strategy_returns" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_strategy_returns, list):
            arg_strategy_returns = pd.Series(arg_strategy_returns)
        kwargs["strategy_returns"] = arg_strategy_returns

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

        res = _beta_impl(**kwargs)
        logger.info("Executed beta tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result("beta", data={"beta": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def alpha(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> dict[str, Any]:
    """AI Tool wrapper for _alpha_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_strategy_returns = strategy_returns
        if "strategy_returns" in ["trades", "open_trades"] and isinstance(
            arg_strategy_returns, (list, dict)
        ):
            arg_strategy_returns = pd.DataFrame(arg_strategy_returns)
        elif "strategy_returns" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_strategy_returns, list):
            arg_strategy_returns = pd.Series(arg_strategy_returns)
        kwargs["strategy_returns"] = arg_strategy_returns

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

        res = _alpha_impl(**kwargs)
        logger.info("Executed alpha tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result("alpha", data={"alpha": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def r_squared(
    strategy_returns: pd.Series, benchmark_returns: pd.Series
) -> dict[str, Any]:
    """AI Tool wrapper for _r_squared_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_strategy_returns = strategy_returns
        if "strategy_returns" in ["trades", "open_trades"] and isinstance(
            arg_strategy_returns, (list, dict)
        ):
            arg_strategy_returns = pd.DataFrame(arg_strategy_returns)
        elif "strategy_returns" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_strategy_returns, list):
            arg_strategy_returns = pd.Series(arg_strategy_returns)
        kwargs["strategy_returns"] = arg_strategy_returns

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

        res = _r_squared_impl(**kwargs)
        logger.info("Executed r_squared tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result("r_squared", data={"r_squared": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def tracking_error(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    periods_per_year: int = 252,
) -> dict[str, Any]:
    """AI Tool wrapper for _tracking_error_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_strategy_returns = strategy_returns
        if "strategy_returns" in ["trades", "open_trades"] and isinstance(
            arg_strategy_returns, (list, dict)
        ):
            arg_strategy_returns = pd.DataFrame(arg_strategy_returns)
        elif "strategy_returns" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_strategy_returns, list):
            arg_strategy_returns = pd.Series(arg_strategy_returns)
        kwargs["strategy_returns"] = arg_strategy_returns

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

        res = _tracking_error_impl(**kwargs)
        logger.info("Executed tracking_error tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "tracking_error", data={"tracking_error": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def information_ratio(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    periods_per_year: int = 252,
) -> dict[str, Any]:
    """AI Tool wrapper for _information_ratio_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_strategy_returns = strategy_returns
        if "strategy_returns" in ["trades", "open_trades"] and isinstance(
            arg_strategy_returns, (list, dict)
        ):
            arg_strategy_returns = pd.DataFrame(arg_strategy_returns)
        elif "strategy_returns" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_strategy_returns, list):
            arg_strategy_returns = pd.Series(arg_strategy_returns)
        kwargs["strategy_returns"] = arg_strategy_returns

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


def relative_drawdown_series(
    strategy_equity: pd.Series, benchmark_equity: pd.Series
) -> dict[str, Any]:
    """AI Tool wrapper for _relative_drawdown_series_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_strategy_equity = strategy_equity
        if "strategy_equity" in ["trades", "open_trades"] and isinstance(
            arg_strategy_equity, (list, dict)
        ):
            arg_strategy_equity = pd.DataFrame(arg_strategy_equity)
        elif "strategy_equity" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_strategy_equity, list):
            arg_strategy_equity = pd.Series(arg_strategy_equity)
        kwargs["strategy_equity"] = arg_strategy_equity

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

        res = _relative_drawdown_series_impl(**kwargs)
        logger.info("Executed relative_drawdown_series tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "relative_drawdown_series", data={"relative_drawdown_series": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_relative_drawdown_percent(
    strategy_equity: pd.Series, benchmark_equity: pd.Series
) -> dict[str, Any]:
    """AI Tool wrapper for _max_relative_drawdown_percent_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_strategy_equity = strategy_equity
        if "strategy_equity" in ["trades", "open_trades"] and isinstance(
            arg_strategy_equity, (list, dict)
        ):
            arg_strategy_equity = pd.DataFrame(arg_strategy_equity)
        elif "strategy_equity" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_strategy_equity, list):
            arg_strategy_equity = pd.Series(arg_strategy_equity)
        kwargs["strategy_equity"] = arg_strategy_equity

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

        res = _max_relative_drawdown_percent_impl(**kwargs)
        logger.info("Executed max_relative_drawdown_percent tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "max_relative_drawdown_percent",
            data={"max_relative_drawdown_percent": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def batting_average(
    strategy_returns: pd.Series, benchmark_returns: pd.Series
) -> dict[str, Any]:
    """AI Tool wrapper for _batting_average_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_strategy_returns = strategy_returns
        if "strategy_returns" in ["trades", "open_trades"] and isinstance(
            arg_strategy_returns, (list, dict)
        ):
            arg_strategy_returns = pd.DataFrame(arg_strategy_returns)
        elif "strategy_returns" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_strategy_returns, list):
            arg_strategy_returns = pd.Series(arg_strategy_returns)
        kwargs["strategy_returns"] = arg_strategy_returns

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

        res = _batting_average_impl(**kwargs)
        logger.info("Executed batting_average tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "batting_average", data={"batting_average": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def up_down_capture(
    strategy_returns: pd.Series, benchmark_returns: pd.Series
) -> dict[str, Any]:
    """AI Tool wrapper for _up_down_capture_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_strategy_returns = strategy_returns
        if "strategy_returns" in ["trades", "open_trades"] and isinstance(
            arg_strategy_returns, (list, dict)
        ):
            arg_strategy_returns = pd.DataFrame(arg_strategy_returns)
        elif "strategy_returns" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_strategy_returns, list):
            arg_strategy_returns = pd.Series(arg_strategy_returns)
        kwargs["strategy_returns"] = arg_strategy_returns

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

        res = _up_down_capture_impl(**kwargs)
        logger.info("Executed up_down_capture tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "up_down_capture", data={"up_down_capture": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def calculate_benchmark_metrics(
    returns: pd.Series,
    benchmark_returns: pd.Series,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_benchmark_metrics_impl."""
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

        res = _calculate_benchmark_metrics_impl(**kwargs)
        logger.info("Executed calculate_benchmark_metrics tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "calculate_benchmark_metrics",
            data={"calculate_benchmark_metrics": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}
