"""distributions.py - Analyze return and trade-result distributions, moments, tails, outliers, and fit quality.

This module provides tools to analyze the statistical properties of return streams and trade results,
including moments (skew/kurtosis), normality tests, distribution fitting, and outlier detection.

Classes:
    None.

Functions:
    _clean_series: Convert input to finite numeric pandas Series.
    _empty_distribution: Standardized empty distribution dictionary.
    _distribution_summary: Generate a standardized summary of a distribution's shape.
    return_distribution: Statistical summary of returns distribution (AI Tool).
    _return_distribution_impl: Core logic for return distribution.
    trade_pnl_distribution: Statistical summary of trade P&L (AI Tool).
    _trade_pnl_distribution_impl: Core logic for trade P&L distribution.
    r_multiple_distribution: Statistical summary of R-multiples (AI Tool).
    _r_multiple_distribution_impl: Core logic for R-multiple distribution.
    percentile_summary: Return selected percentile values (AI Tool).
    _percentile_summary_impl: Core logic for percentiles.
    upside_downside_summary: Summary of positive and negative outcomes (AI Tool).
    _upside_downside_summary_impl: Core logic for upside/downside analysis.
    skewness: Fisher-Pearson coefficient of skewness (AI Tool).
    _skewness_impl: Core logic for skewness.
    kurtosis: Excess kurtosis (AI Tool).
    _kurtosis_impl: Core logic for kurtosis.
    higher_moments: Detailed breakdown of skewness and kurtosis (AI Tool).
    _higher_moments_impl: Core logic for higher moments.
    fat_tail_score: Heuristic score of tail heaviness (AI Tool).
    _fat_tail_score_impl: Core logic for fat tail score.
    tail_ratio: Upper vs lower percentile ratio (AI Tool).
    _tail_ratio_impl: Core logic for tail ratio.
    jarque_bera_test: Jarque-Bera test for normality (AI Tool).
    _jarque_bera_test_impl: Core logic for Jarque-Bera.
    shapiro_wilk_test: Shapiro-Wilk test for normality (AI Tool).
    _shapiro_wilk_test_impl: Core logic for Shapiro-Wilk.
    qq_plot_data: Generate data for Q-Q plots (AI Tool).
    _qq_plot_data_impl: Core logic for Q-Q data.
    fit_distribution: Fit theoretical distribution parameters (AI Tool).
    _fit_distribution_impl: Core logic for distribution fitting.
    distribution_fit_quality: Metrics for fit quality (AI Tool).
    _distribution_fit_quality_impl: Core logic for fit quality.
    histogram_data: Generate data for histogram plots (AI Tool).
    _histogram_data_impl: Core logic for histogram.
    detect_outliers: Identify outliers in the data (AI Tool).
    _detect_outliers_impl: Core logic for outlier detection.
    outlier_ratio: Percentage of outliers (AI Tool).
    _outlier_ratio_impl: Core logic for outlier ratio.
    calculate_distribution_metrics: Combined skew and kurtosis (AI Tool).
    _calculate_distribution_metrics_impl: Core logic for combined distribution metrics.
"""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
import pandas as pd

try:
    from scipy import stats

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

from app.services.analytics.common import (
    analytics_tool_result,
    get_closed_trades,
    get_r_multiples,
)
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
# Shared Helpers & Cleaning
# =========================================================================


def _clean_series(data: pd.Series | np.ndarray | list[float]) -> pd.Series:
    """Convert input to finite numeric pandas Series.

    Args:
        data: Input data as Series, array, or list.

    Returns:
        Cleaned pandas Series of floats.
    """
    if isinstance(data, pd.Series):
        s = pd.to_numeric(data, errors="coerce")
    else:
        s = pd.Series(data, dtype="float64")

    s = s.replace([np.inf, -np.inf], np.nan).dropna()
    return s.astype(float)


def _empty_distribution() -> dict[str, float]:
    """Standardized empty distribution dictionary.

    Returns:
        Dictionary with zeroed statistical metrics.
    """
    return {
        "count": 0.0,
        "mean": 0.0,
        "median": 0.0,
        "std": 0.0,
        "skew": 0.0,
        "kurtosis": 0.0,
        "min": 0.0,
        "max": 0.0,
        "q25": 0.0,
        "q75": 0.0,
    }


def _distribution_summary(data: pd.Series) -> dict[str, float]:
    """Generate a standardized summary of a distribution's shape.

    Args:
        data: Cleaned pandas Series.

    Returns:
        Dictionary with count, mean, median, std, skew, kurtosis, etc.
    """
    s = _clean_series(data)
    if s.empty:
        return _empty_distribution()

    n = len(s)
    return {
        "count": float(n),
        "mean": float(s.mean()),
        "median": float(s.median()),
        "std": float(s.std(ddof=1)) if n >= 2 else 0.0,
        "skew": float(s.skew()) if n >= 3 else 0.0,
        "kurtosis": float(s.kurt()) if n >= 4 else 0.0,
        "min": float(s.min()),
        "max": float(s.max()),
        "q25": float(s.quantile(0.25)),
        "q75": float(s.quantile(0.75)),
    }


# =========================================================================
# Core Summary Statistics
# =========================================================================


def _return_distribution_impl(rets: pd.Series | np.ndarray) -> dict[str, float]:
    """Core logic for statistical summary of returns distribution.

    Args:
        rets: Series of returns.

    Returns:
        Standardized summary dictionary.
    """
    return _distribution_summary(rets)


def _trade_pnl_distribution_impl(trades: pd.DataFrame) -> dict[str, float]:
    """Core logic for statistical summary of realized trade P&L.

    Args:
        trades: DataFrame of trades.

    Returns:
        Standardized summary dictionary.
    """
    res = get_closed_trades(trades)
    if res["status"] != "success":
        return _empty_distribution()

    closed = pd.DataFrame(res["data"]["closed_trades"])
    if closed.empty or "profit_loss" not in closed.columns:
        return _empty_distribution()
    return _distribution_summary(closed["profit_loss"])


def _r_multiple_distribution_impl(trades: pd.DataFrame) -> dict[str, float]:
    """Core logic for statistical summary of R-multiple distribution.

    Args:
        trades: DataFrame of trades.

    Returns:
        Standardized summary dictionary.
    """
    res = get_r_multiples(trades)
    if res["status"] != "success":
        return _empty_distribution()

    r_values = pd.Series(res["data"]["r_multiples"])
    if r_values.empty:
        return _empty_distribution()
    return _distribution_summary(r_values)


def _percentile_summary_impl(
    data: pd.Series | np.ndarray,
    percentiles: list[float] | None = None,
) -> dict[str, float]:
    """Core logic for calculating selected percentile values.

    Args:
        data: Input numeric data.
        percentiles: List of percentile values (0 to 1).

    Returns:
        Dictionary mapping percentile names to values.
    """
    s = _clean_series(data)
    if s.empty:
        return {}

    if percentiles is None:
        percentiles = [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]

    return {f"p{int(p * 100)}": float(s.quantile(p)) for p in percentiles}


def _upside_downside_summary_impl(data: pd.Series | np.ndarray) -> dict[str, float]:
    """Core logic for summary of positive and negative outcome distributions.

    Args:
        data: Input numeric data.

    Returns:
        Dictionary with upside and downside mean/std/count.
    """
    s = _clean_series(data)
    if s.empty:
        return {
            "upside_mean": 0.0,
            "downside_mean": 0.0,
            "upside_std": 0.0,
            "downside_std": 0.0,
            "upside_count": 0.0,
            "downside_count": 0.0,
        }

    upside = s[s > 0]
    downside = s[s < 0]

    return {
        "upside_mean": float(upside.mean()) if not upside.empty else 0.0,
        "downside_mean": float(downside.mean()) if not downside.empty else 0.0,
        "upside_std": float(upside.std(ddof=1)) if len(upside) >= 2 else 0.0,
        "downside_std": float(downside.std(ddof=1)) if len(downside) >= 2 else 0.0,
        "upside_count": float(len(upside)),
        "downside_count": float(len(downside)),
    }


# =========================================================================
# Higher Moments & Fat Tails
# =========================================================================


def _skewness_impl(data: pd.Series | np.ndarray) -> float:
    """Core logic for Fisher-Pearson coefficient of skewness.

    Args:
        data: Input numeric data.

    Returns:
        Skewness value (float).
    """
    s = _clean_series(data)
    if len(s) < 3:
        return 0.0
    return float(s.skew())


def _kurtosis_impl(data: pd.Series | np.ndarray) -> float:
    """Core logic for excess kurtosis (Fisher’s definition, Normal = 0).

    Args:
        data: Input numeric data.

    Returns:
        Excess kurtosis value (float).
    """
    s = _clean_series(data)
    if len(s) < 4:
        return 0.0
    return float(s.kurt())


def _higher_moments_impl(data: pd.Series | np.ndarray) -> dict[str, float]:
    """Core logic for detailed breakdown of skewness and kurtosis.

    Args:
        data: Input numeric data.

    Returns:
        Dictionary with skewness, excess kurtosis, and raw kurtosis.
    """
    s = _clean_series(data)
    ex_kurt = _kurtosis_impl(s)
    return {
        "skewness": _skewness_impl(s),
        "excess_kurtosis": ex_kurt,
        "kurtosis": ex_kurt + 3.0,
    }


def _fat_tail_score_impl(data: pd.Series | np.ndarray) -> float:
    """Core logic for heuristic score of tail heaviness relative to normal.

    Args:
        data: Input numeric data.

    Returns:
        Fat tail score (float).
    """
    k = _kurtosis_impl(data)
    ratio = _outlier_ratio_impl(data, method="iqr")
    # Heuristic: Kurtosis normalized by 3 + 2x outlier percentage
    return float(max(0.0, k / 3.0 + ratio / 5.0))


def _tail_ratio_impl(
    data: pd.Series | np.ndarray, upper_q: float = 0.95, lower_q: float = 0.05
) -> float:
    """Core logic for Tail Ratio calculation.

    Args:
        data: Input numeric data.
        upper_q: Upper quantile level.
        lower_q: Lower quantile level.

    Returns:
        Tail ratio (float).
    """
    if not (0 < lower_q < upper_q < 1):
        return 0.0

    s = _clean_series(data)
    if s.empty:
        return 0.0

    upper = s.quantile(upper_q)
    lower = s.quantile(lower_q)

    if abs(lower) <= 1e-12:
        return float("inf") if upper > 0 else 0.0

    return float(abs(upper) / abs(lower))


# =========================================================================
# Normality Tests
# =========================================================================


def _jarque_bera_test_impl(data: pd.Series | np.ndarray) -> dict[str, float]:
    """Core logic for Jarque-Bera test for normality.

    Args:
        data: Input numeric data.

    Returns:
        Dictionary with test statistic and p-value.
    """
    if not HAS_SCIPY:
        return {"statistic": 0.0, "p_value": 0.0}

    s = _clean_series(data)
    if len(s) < 4:
        return {"statistic": 0.0, "p_value": 0.0}

    stat, p = stats.jarque_bera(s.to_numpy())
    return {"statistic": float(stat), "p_value": float(p)}


def _shapiro_wilk_test_impl(data: pd.Series | np.ndarray) -> dict[str, float]:
    """Core logic for Shapiro-Wilk test for normality.

    Args:
        data: Input numeric data.

    Returns:
        Dictionary with test statistic and p-value.
    """
    if not HAS_SCIPY:
        return {"statistic": 0.0, "p_value": 0.0}

    s = _clean_series(data)
    if len(s) < 3:
        return {"statistic": 0.0, "p_value": 0.0}

    arr = s.to_numpy()
    if len(arr) > 5000:
        arr = np.random.choice(arr, 5000, replace=False)

    stat, p = stats.shapiro(arr)
    return {"statistic": float(stat), "p_value": float(p)}


# =========================================================================
# Distribution Fitting & Q-Q Plots
# =========================================================================


def _qq_plot_data_impl(data: pd.Series | np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Core logic for generating theoretical vs actual quantiles for a Q-Q plot.

    Args:
        data: Input numeric data.

    Returns:
        Tuple of (theoretical_quantiles, actual_quantiles).
    """
    if not HAS_SCIPY:
        return np.array([]), np.array([])

    s = _clean_series(data)
    if len(s) < 2:
        return np.array([]), np.array([])

    std = s.std(ddof=1)
    if std == 0 or np.isnan(std):
        return np.array([]), np.array([])

    standardized = (s - s.mean()) / std

    osm, osr = stats.probplot(standardized, dist="norm", fit=False)
    return np.asarray(osm), np.asarray(osr)


def _fit_distribution_impl(
    data: pd.Series | np.ndarray,
    dist_name: Literal["norm", "t", "lognorm", "gamma"] = "norm",
) -> dict[str, float]:
    """Core logic for fitting a theoretical distribution.

    Args:
        data: Input numeric data.
        dist_name: Name of the distribution to fit.

    Returns:
        Dictionary of fitted parameters.
    """
    if not HAS_SCIPY:
        return {}

    s = _clean_series(data)
    arr = s.to_numpy()

    if dist_name in {"lognorm", "gamma"}:
        arr = arr[arr > 0]
        if len(arr) < 2:
            return {}

    if len(arr) < 2:
        return {}

    dist = getattr(stats, dist_name)
    params = dist.fit(arr)

    if dist_name == "norm":
        return {"mean": float(params[0]), "std": float(params[1])}
    if dist_name == "t":
        return {
            "df": float(params[0]),
            "loc": float(params[1]),
            "scale": float(params[2]),
        }
    if dist_name == "lognorm":
        return {
            "s": float(params[0]),
            "loc": float(params[1]),
            "scale": float(params[2]),
        }
    if dist_name == "gamma":
        return {
            "a": float(params[0]),
            "loc": float(params[1]),
            "scale": float(params[2]),
        }

    return {f"param_{i}": float(p) for i, p in enumerate(params)}


def _distribution_fit_quality_impl(
    data: pd.Series | np.ndarray,
    dist_name: Literal["norm", "t", "lognorm", "gamma"] = "norm",
) -> dict[str, float]:
    """Core logic for fit quality metrics (AIC, BIC, Log-Likelihood).

    Args:
        data: Input numeric data.
        dist_name: Name of the distribution.

    Returns:
        Dictionary with log_likelihood, aic, and bic.
    """
    if not HAS_SCIPY:
        return {}

    s = _clean_series(data)
    arr = s.to_numpy()

    if dist_name in {"lognorm", "gamma"}:
        arr = arr[arr > 0]

    if len(arr) < 3:
        return {}

    try:
        dist = getattr(stats, dist_name)
        params = dist.fit(arr)

        log_likelihood = float(np.sum(dist.logpdf(arr, *params)))
        k = len(params)
        n = len(arr)

        aic = 2 * k - 2 * log_likelihood
        bic = k * np.log(n) - 2 * log_likelihood

        return {
            "log_likelihood": log_likelihood,
            "aic": float(aic),
            "bic": float(bic),
        }
    except Exception:
        return {}


def _histogram_data_impl(
    data: pd.Series | np.ndarray,
    bins: int = 30,
) -> dict[str, list[float]]:
    """Core logic for generating histogram data.

    Args:
        data: Input numeric data.
        bins: Number of bins.

    Returns:
        Dictionary with bin_edges and counts.
    """
    if bins <= 0:
        bins = 30

    s = _clean_series(data)
    if s.empty:
        return {"bin_edges": [], "counts": []}

    counts, bin_edges = np.histogram(s.to_numpy(), bins=bins)

    return {
        "bin_edges": [float(x) for x in bin_edges],
        "counts": [float(x) for x in counts],
    }


# =========================================================================
# Outlier Detection
# =========================================================================


def _detect_outliers_impl(
    data: pd.Series | np.ndarray,
    method: Literal["zscore", "iqr"] = "zscore",
    threshold: float | None = None,
) -> pd.Series:
    """Core logic for identifying outliers.

    Args:
        data: Input numeric data.
        method: Method to use ('zscore' or 'iqr').
        threshold: Heuristic threshold.

    Returns:
        Boolean pandas Series where True indicates an outlier.
    """
    s = _clean_series(data)
    if s.empty:
        return pd.Series(dtype=bool)

    if method == "zscore":
        actual_threshold = threshold if threshold is not None else 3.0
        std = s.std(ddof=1)
        if std == 0 or np.isnan(std):
            return pd.Series(False, index=s.index)
        z = np.abs((s - s.mean()) / std)
        return z > actual_threshold

    if method == "iqr":
        actual_threshold = threshold if threshold is not None else 1.5
        q1 = s.quantile(0.25)
        q3 = s.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            return pd.Series(False, index=s.index)
        lower = q1 - (actual_threshold * iqr)
        upper = q3 + (actual_threshold * iqr)
        return (s < lower) | (s > upper)

    return pd.Series(False, index=s.index)


def _outlier_ratio_impl(
    data: pd.Series | np.ndarray,
    method: Literal["zscore", "iqr"] = "zscore",
    threshold: float | None = None,
) -> float:
    """Core logic for calculating outlier ratio.

    Args:
        data: Input numeric data.
        method: Method to use.
        threshold: Heuristic threshold.

    Returns:
        Outlier percentage (0-100).
    """
    mask = _detect_outliers_impl(data, method=method, threshold=threshold)
    if mask.empty:
        return 0.0
    return float(mask.sum() / len(mask) * 100.0)


# =========================================================================
# AI Tool Wrappers (Rule 3)
# =========================================================================


def _return_distribution_impl(rets: pd.Series | list[float]) -> dict[str, Any]:
    """Statistical summary of returns distribution (AI Tool).

    Args:
        rets: Series or list of strategy returns.

    Returns:
        Standardized tool result with distribution metrics.
    """
    try:
        s = _clean_series(rets)
        result = _return_distribution_impl(s)
        logger.info("Executed return_distribution tool successfully.")
        return analytics_tool_result("return_distribution", data=result)
    except Exception as e:
        logger.error(f"Error in return_distribution: {e!s}")
        return {"status": "error", "message": str(e)}


def _trade_pnl_distribution_impl(
    trades: pd.DataFrame | list[dict[str, Any]],
) -> dict[str, Any]:
    """Statistical summary of realized trade P&L (AI Tool).

    Args:
        trades: DataFrame or list of trades.

    Returns:
        Standardized tool result with trade P&L distribution.
    """
    try:
        df = pd.DataFrame(trades) if isinstance(trades, list) else trades
        result = _trade_pnl_distribution_impl(df)
        logger.info("Executed trade_pnl_distribution tool successfully.")
        return analytics_tool_result("trade_pnl_distribution", data=result)
    except Exception as e:
        logger.error(f"Error in trade_pnl_distribution: {e!s}")
        return {"status": "error", "message": str(e)}


def _r_multiple_distribution_impl(
    trades: pd.DataFrame | list[dict[str, Any]],
) -> dict[str, Any]:
    """Statistical summary of R-multiples (AI Tool).

    Args:
        trades: DataFrame or list of trades.

    Returns:
        Standardized tool result with R-multiple distribution.
    """
    try:
        df = pd.DataFrame(trades) if isinstance(trades, list) else trades
        result = _r_multiple_distribution_impl(df)
        logger.info("Executed r_multiple_distribution tool successfully.")
        return analytics_tool_result("r_multiple_distribution", data=result)
    except Exception as e:
        logger.error(f"Error in r_multiple_distribution: {e!s}")
        return {"status": "error", "message": str(e)}


def _percentile_summary_impl(
    data: pd.Series | list[float],
    percentiles: list[float] | None = None,
) -> dict[str, Any]:
    """Return selected percentile values (AI Tool).

    Args:
        data: Numeric data as Series or list.
        percentiles: Optional list of quantiles (0-1).

    Returns:
        Standardized tool result with percentile values.
    """
    try:
        s = _clean_series(data)
        result = _percentile_summary_impl(s, percentiles)
        logger.info("Executed percentile_summary tool successfully.")
        return analytics_tool_result("percentile_summary", data=result)
    except Exception as e:
        logger.error(f"Error in percentile_summary: {e!s}")
        return {"status": "error", "message": str(e)}


def _upside_downside_summary_impl(data: pd.Series | list[float]) -> dict[str, Any]:
    """Summary of positive and negative outcomes (AI Tool).

    Args:
        data: Numeric data as Series or list.

    Returns:
        Standardized tool result with upside/downside metrics.
    """
    try:
        s = _clean_series(data)
        result = _upside_downside_summary_impl(s)
        logger.info("Executed upside_downside_summary tool successfully.")
        return analytics_tool_result("upside_downside_summary", data=result)
    except Exception as e:
        logger.error(f"Error in upside_downside_summary: {e!s}")
        return {"status": "error", "message": str(e)}


def _skewness_impl(data: pd.Series | list[float]) -> dict[str, Any]:
    """Fisher-Pearson coefficient of skewness (AI Tool).

    Args:
        data: Numeric data as Series or list.

    Returns:
        Standardized tool result with skewness value.
    """
    try:
        s = _clean_series(data)
        result = _skewness_impl(s)
        logger.info("Executed skewness tool successfully.")
        return analytics_tool_result("skewness", data={"skewness": result})
    except Exception as e:
        logger.error(f"Error in skewness: {e!s}")
        return {"status": "error", "message": str(e)}


def _kurtosis_impl(data: pd.Series | list[float]) -> dict[str, Any]:
    """Excess kurtosis (Fisher’s definition, Normal = 0) (AI Tool).

    Args:
        data: Numeric data as Series or list.

    Returns:
        Standardized tool result with kurtosis value.
    """
    try:
        s = _clean_series(data)
        result = _kurtosis_impl(s)
        logger.info("Executed kurtosis tool successfully.")
        return analytics_tool_result("kurtosis", data={"kurtosis": result})
    except Exception as e:
        logger.error(f"Error in kurtosis: {e!s}")
        return {"status": "error", "message": str(e)}


def _higher_moments_impl(data: pd.Series | list[float]) -> dict[str, Any]:
    """Detailed breakdown of skewness and kurtosis (AI Tool).

    Args:
        data: Numeric data as Series or list.

    Returns:
        Standardized tool result with skew and kurtosis metrics.
    """
    try:
        s = _clean_series(data)
        result = _higher_moments_impl(s)
        logger.info("Executed higher_moments tool successfully.")
        return analytics_tool_result("higher_moments", data=result)
    except Exception as e:
        logger.error(f"Error in higher_moments: {e!s}")
        return {"status": "error", "message": str(e)}


def _fat_tail_score_impl(data: pd.Series | list[float]) -> dict[str, Any]:
    """Heuristic score of tail heaviness relative to normal (AI Tool).

    Args:
        data: Numeric data as Series or list.

    Returns:
        Standardized tool result with fat tail score.
    """
    try:
        s = _clean_series(data)
        result = _fat_tail_score_impl(s)
        logger.info("Executed fat_tail_score tool successfully.")
        return analytics_tool_result("fat_tail_score", data={"fat_tail_score": result})
    except Exception as e:
        logger.error(f"Error in fat_tail_score: {e!s}")
        return {"status": "error", "message": str(e)}


def _tail_ratio_impl(
    data: pd.Series | list[float], upper_q: float = 0.95, lower_q: float = 0.05
) -> dict[str, Any]:
    """Tail Ratio = |upper percentile| / |lower percentile| (AI Tool).

    Args:
        data: Numeric data.
        upper_q: Upper quantile.
        lower_q: Lower quantile.

    Returns:
        Standardized tool result with tail ratio.
    """
    try:
        s = _clean_series(data)
        result = _tail_ratio_impl(s, upper_q, lower_q)
        logger.info("Executed tail_ratio tool successfully.")
        return analytics_tool_result("tail_ratio", data={"tail_ratio": result})
    except Exception as e:
        logger.error(f"Error in tail_ratio: {e!s}")
        return {"status": "error", "message": str(e)}


def _jarque_bera_test_impl(data: pd.Series | list[float]) -> dict[str, Any]:
    """Jarque-Bera test for normality (AI Tool).

    Args:
        data: Numeric data.

    Returns:
        Standardized tool result with statistic and p-value.
    """
    try:
        s = _clean_series(data)
        result = _jarque_bera_test_impl(s)
        logger.info("Executed jarque_bera_test tool successfully.")
        return analytics_tool_result("jarque_bera_test", data=result)
    except Exception as e:
        logger.error(f"Error in jarque_bera_test: {e!s}")
        return {"status": "error", "message": str(e)}


def _shapiro_wilk_test_impl(data: pd.Series | list[float]) -> dict[str, Any]:
    """Shapiro-Wilk test for normality (AI Tool).

    Args:
        data: Numeric data.

    Returns:
        Standardized tool result with statistic and p-value.
    """
    try:
        s = _clean_series(data)
        result = _shapiro_wilk_test_impl(s)
        logger.info("Executed shapiro_wilk_test tool successfully.")
        return analytics_tool_result("shapiro_wilk_test", data=result)
    except Exception as e:
        logger.error(f"Error in shapiro_wilk_test: {e!s}")
        return {"status": "error", "message": str(e)}


def _qq_plot_data_impl(data: pd.Series | list[float]) -> dict[str, Any]:
    """Generate theoretical vs actual quantiles for a Q-Q plot (AI Tool).

    Args:
        data: Numeric data.

    Returns:
        Standardized tool result with Q-Q plot quantiles.
    """
    try:
        s = _clean_series(data)
        osm, osr = _qq_plot_data_impl(s)
        logger.info("Executed qq_plot_data tool successfully.")
        return analytics_tool_result(
            "qq_plot_data",
            data={
                "theoretical_quantiles": osm.tolist(),
                "actual_quantiles": osr.tolist(),
            },
        )
    except Exception as e:
        logger.error(f"Error in qq_plot_data: {e!s}")
        return {"status": "error", "message": str(e)}


def _fit_distribution_impl(
    data: pd.Series | list[float],
    dist_name: Literal["norm", "t", "lognorm", "gamma"] = "norm",
) -> dict[str, Any]:
    """Fit a theoretical distribution and return its parameters (AI Tool).

    Args:
        data: Numeric data.
        dist_name: Name of distribution.

    Returns:
        Standardized tool result with fitted parameters.
    """
    try:
        s = _clean_series(data)
        result = _fit_distribution_impl(s, dist_name)
        logger.info("Executed fit_distribution tool successfully.")
        return analytics_tool_result("fit_distribution", data=result)
    except Exception as e:
        logger.error(f"Error in fit_distribution: {e!s}")
        return {"status": "error", "message": str(e)}


def _distribution_fit_quality_impl(
    data: pd.Series | list[float],
    dist_name: Literal["norm", "t", "lognorm", "gamma"] = "norm",
) -> dict[str, Any]:
    """Fit a distribution and return log-likelihood, AIC, and BIC (AI Tool).

    Args:
        data: Numeric data.
        dist_name: Name of distribution.

    Returns:
        Standardized tool result with fit quality metrics.
    """
    try:
        s = _clean_series(data)
        result = _distribution_fit_quality_impl(s, dist_name)
        logger.info("Executed distribution_fit_quality tool successfully.")
        return analytics_tool_result("distribution_fit_quality", data=result)
    except Exception as e:
        logger.error(f"Error in distribution_fit_quality: {e!s}")
        return {"status": "error", "message": str(e)}


def _histogram_data_impl(
    data: pd.Series | list[float],
    bins: int = 30,
) -> dict[str, Any]:
    """Generate histogram data for UI plotting (AI Tool).

    Args:
        data: Numeric data.
        bins: Number of bins.

    Returns:
        Standardized tool result with histogram bins and counts.
    """
    try:
        s = _clean_series(data)
        result = _histogram_data_impl(s, bins)
        logger.info("Executed histogram_data tool successfully.")
        return analytics_tool_result("histogram_data", data=result)
    except Exception as e:
        logger.error(f"Error in histogram_data: {e!s}")
        return {"status": "error", "message": str(e)}


def _detect_outliers_impl(
    data: pd.Series | list[float],
    method: Literal["zscore", "iqr"] = "zscore",
    threshold: float | None = None,
) -> dict[str, Any]:
    """Return identification of outliers (AI Tool).

    Args:
        data: Numeric data.
        method: Outlier detection method.
        threshold: Heuristic threshold.

    Returns:
        Standardized tool result with boolean outlier mask.
    """
    try:
        s = _clean_series(data)
        mask = _detect_outliers_impl(s, method, threshold)
        logger.info("Executed detect_outliers tool successfully.")
        return analytics_tool_result(
            "detect_outliers", data={"outliers": mask.tolist()}
        )
    except Exception as e:
        logger.error(f"Error in detect_outliers: {e!s}")
        return {"status": "error", "message": str(e)}


def _outlier_ratio_impl(
    data: pd.Series | list[float],
    method: Literal["zscore", "iqr"] = "zscore",
    threshold: float | None = None,
) -> dict[str, Any]:
    """Percentage of data points identified as outliers (AI Tool).

    Args:
        data: Numeric data.
        method: Outlier detection method.
        threshold: Heuristic threshold.

    Returns:
        Standardized tool result with outlier percentage.
    """
    try:
        s = _clean_series(data)
        result = _outlier_ratio_impl(s, method, threshold)
        logger.info("Executed outlier_ratio tool successfully.")
        return analytics_tool_result("outlier_ratio", data={"outlier_ratio": result})
    except Exception as e:
        logger.error(f"Error in outlier_ratio: {e!s}")
        return {"status": "error", "message": str(e)}


def _calculate_distribution_metrics_impl(
    *,
    values: list[float],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Calculate skew and kurtosis for numeric values (AI Tool).

    Args:
        values: List of numeric values.
        request_id: Request identifier.
        agent_name: Agent name.
        environment: Execution environment.
        dry_run: Dry run flag.

    Returns:
        Standardized tool result with skew and kurtosis.
    """
    try:
        s = _clean_series(values)
        data = {
            "skew": float(s.skew()) if len(s) >= 3 else 0.0,
            "kurtosis": float(s.kurt()) if len(s) >= 4 else 0.0,
        }
        logger.info("Executed calculate_distribution_metrics tool successfully.")
        return analytics_tool_result(
            "calculate_distribution_metrics",
            data=data,
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )
    except Exception as e:
        logger.error(f"Error in calculate_distribution_metrics: {e!s}")
        return {"status": "error", "message": str(e)}


def return_distribution(rets: pd.Series | np.ndarray) -> dict[str, Any]:
    """AI Tool wrapper for _return_distribution_impl."""
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

        res = _return_distribution_impl(**kwargs)
        logger.info("Executed return_distribution tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "return_distribution", data={"return_distribution": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def trade_pnl_distribution(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _trade_pnl_distribution_impl."""
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

        res = _trade_pnl_distribution_impl(**kwargs)
        logger.info("Executed trade_pnl_distribution tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "trade_pnl_distribution", data={"trade_pnl_distribution": data_payload}
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


def percentile_summary(
    data: pd.Series | np.ndarray,
    percentiles: list[float] | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _percentile_summary_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_data = data
        if "data" in ["trades", "open_trades"] and isinstance(arg_data, (list, dict)):
            arg_data = pd.DataFrame(arg_data)
        elif "data" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_data, list):
            arg_data = pd.Series(arg_data)
        kwargs["data"] = arg_data

        arg_percentiles = percentiles
        if "percentiles" in ["trades", "open_trades"] and isinstance(
            arg_percentiles, (list, dict)
        ):
            arg_percentiles = pd.DataFrame(arg_percentiles)
        elif "percentiles" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_percentiles, list):
            arg_percentiles = pd.Series(arg_percentiles)
        kwargs["percentiles"] = arg_percentiles

        res = _percentile_summary_impl(**kwargs)
        logger.info("Executed percentile_summary tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "percentile_summary", data={"percentile_summary": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def upside_downside_summary(data: pd.Series | np.ndarray) -> dict[str, Any]:
    """AI Tool wrapper for _upside_downside_summary_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_data = data
        if "data" in ["trades", "open_trades"] and isinstance(arg_data, (list, dict)):
            arg_data = pd.DataFrame(arg_data)
        elif "data" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_data, list):
            arg_data = pd.Series(arg_data)
        kwargs["data"] = arg_data

        res = _upside_downside_summary_impl(**kwargs)
        logger.info("Executed upside_downside_summary tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "upside_downside_summary", data={"upside_downside_summary": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def skewness(data: pd.Series | np.ndarray) -> dict[str, Any]:
    """AI Tool wrapper for _skewness_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_data = data
        if "data" in ["trades", "open_trades"] and isinstance(arg_data, (list, dict)):
            arg_data = pd.DataFrame(arg_data)
        elif "data" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_data, list):
            arg_data = pd.Series(arg_data)
        kwargs["data"] = arg_data

        res = _skewness_impl(**kwargs)
        logger.info("Executed skewness tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result("skewness", data={"skewness": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def kurtosis(data: pd.Series | np.ndarray) -> dict[str, Any]:
    """AI Tool wrapper for _kurtosis_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_data = data
        if "data" in ["trades", "open_trades"] and isinstance(arg_data, (list, dict)):
            arg_data = pd.DataFrame(arg_data)
        elif "data" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_data, list):
            arg_data = pd.Series(arg_data)
        kwargs["data"] = arg_data

        res = _kurtosis_impl(**kwargs)
        logger.info("Executed kurtosis tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result("kurtosis", data={"kurtosis": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def higher_moments(data: pd.Series | np.ndarray) -> dict[str, Any]:
    """AI Tool wrapper for _higher_moments_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_data = data
        if "data" in ["trades", "open_trades"] and isinstance(arg_data, (list, dict)):
            arg_data = pd.DataFrame(arg_data)
        elif "data" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_data, list):
            arg_data = pd.Series(arg_data)
        kwargs["data"] = arg_data

        res = _higher_moments_impl(**kwargs)
        logger.info("Executed higher_moments tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "higher_moments", data={"higher_moments": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def fat_tail_score(data: pd.Series | np.ndarray) -> dict[str, Any]:
    """AI Tool wrapper for _fat_tail_score_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_data = data
        if "data" in ["trades", "open_trades"] and isinstance(arg_data, (list, dict)):
            arg_data = pd.DataFrame(arg_data)
        elif "data" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_data, list):
            arg_data = pd.Series(arg_data)
        kwargs["data"] = arg_data

        res = _fat_tail_score_impl(**kwargs)
        logger.info("Executed fat_tail_score tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "fat_tail_score", data={"fat_tail_score": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def tail_ratio(
    data: pd.Series | np.ndarray, upper_q: float = 0.95, lower_q: float = 0.05
) -> dict[str, Any]:
    """AI Tool wrapper for _tail_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_data = data
        if "data" in ["trades", "open_trades"] and isinstance(arg_data, (list, dict)):
            arg_data = pd.DataFrame(arg_data)
        elif "data" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_data, list):
            arg_data = pd.Series(arg_data)
        kwargs["data"] = arg_data

        arg_upper_q = upper_q
        if "upper_q" in ["trades", "open_trades"] and isinstance(
            arg_upper_q, (list, dict)
        ):
            arg_upper_q = pd.DataFrame(arg_upper_q)
        elif "upper_q" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_upper_q, list):
            arg_upper_q = pd.Series(arg_upper_q)
        kwargs["upper_q"] = arg_upper_q

        arg_lower_q = lower_q
        if "lower_q" in ["trades", "open_trades"] and isinstance(
            arg_lower_q, (list, dict)
        ):
            arg_lower_q = pd.DataFrame(arg_lower_q)
        elif "lower_q" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_lower_q, list):
            arg_lower_q = pd.Series(arg_lower_q)
        kwargs["lower_q"] = arg_lower_q

        res = _tail_ratio_impl(**kwargs)
        logger.info("Executed tail_ratio tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result("tail_ratio", data={"tail_ratio": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def jarque_bera_test(data: pd.Series | np.ndarray) -> dict[str, Any]:
    """AI Tool wrapper for _jarque_bera_test_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_data = data
        if "data" in ["trades", "open_trades"] and isinstance(arg_data, (list, dict)):
            arg_data = pd.DataFrame(arg_data)
        elif "data" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_data, list):
            arg_data = pd.Series(arg_data)
        kwargs["data"] = arg_data

        res = _jarque_bera_test_impl(**kwargs)
        logger.info("Executed jarque_bera_test tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "jarque_bera_test", data={"jarque_bera_test": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def shapiro_wilk_test(data: pd.Series | np.ndarray) -> dict[str, Any]:
    """AI Tool wrapper for _shapiro_wilk_test_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_data = data
        if "data" in ["trades", "open_trades"] and isinstance(arg_data, (list, dict)):
            arg_data = pd.DataFrame(arg_data)
        elif "data" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_data, list):
            arg_data = pd.Series(arg_data)
        kwargs["data"] = arg_data

        res = _shapiro_wilk_test_impl(**kwargs)
        logger.info("Executed shapiro_wilk_test tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "shapiro_wilk_test", data={"shapiro_wilk_test": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def qq_plot_data(data: pd.Series | np.ndarray) -> dict[str, Any]:
    """AI Tool wrapper for _qq_plot_data_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_data = data
        if "data" in ["trades", "open_trades"] and isinstance(arg_data, (list, dict)):
            arg_data = pd.DataFrame(arg_data)
        elif "data" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_data, list):
            arg_data = pd.Series(arg_data)
        kwargs["data"] = arg_data

        res = _qq_plot_data_impl(**kwargs)
        logger.info("Executed qq_plot_data tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "qq_plot_data", data={"qq_plot_data": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def fit_distribution(
    data: pd.Series | np.ndarray,
    dist_name: Literal["norm", "t", "lognorm", "gamma"] = "norm",
) -> dict[str, Any]:
    """AI Tool wrapper for _fit_distribution_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_data = data
        if "data" in ["trades", "open_trades"] and isinstance(arg_data, (list, dict)):
            arg_data = pd.DataFrame(arg_data)
        elif "data" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_data, list):
            arg_data = pd.Series(arg_data)
        kwargs["data"] = arg_data

        arg_dist_name = dist_name
        if "dist_name" in ["trades", "open_trades"] and isinstance(
            arg_dist_name, (list, dict)
        ):
            arg_dist_name = pd.DataFrame(arg_dist_name)
        elif "dist_name" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_dist_name, list):
            arg_dist_name = pd.Series(arg_dist_name)
        kwargs["dist_name"] = arg_dist_name

        res = _fit_distribution_impl(**kwargs)
        logger.info("Executed fit_distribution tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "fit_distribution", data={"fit_distribution": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def distribution_fit_quality(
    data: pd.Series | np.ndarray,
    dist_name: Literal["norm", "t", "lognorm", "gamma"] = "norm",
) -> dict[str, Any]:
    """AI Tool wrapper for _distribution_fit_quality_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_data = data
        if "data" in ["trades", "open_trades"] and isinstance(arg_data, (list, dict)):
            arg_data = pd.DataFrame(arg_data)
        elif "data" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_data, list):
            arg_data = pd.Series(arg_data)
        kwargs["data"] = arg_data

        arg_dist_name = dist_name
        if "dist_name" in ["trades", "open_trades"] and isinstance(
            arg_dist_name, (list, dict)
        ):
            arg_dist_name = pd.DataFrame(arg_dist_name)
        elif "dist_name" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_dist_name, list):
            arg_dist_name = pd.Series(arg_dist_name)
        kwargs["dist_name"] = arg_dist_name

        res = _distribution_fit_quality_impl(**kwargs)
        logger.info("Executed distribution_fit_quality tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "distribution_fit_quality", data={"distribution_fit_quality": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def histogram_data(
    data: pd.Series | np.ndarray,
    bins: int = 30,
) -> dict[str, Any]:
    """AI Tool wrapper for _histogram_data_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_data = data
        if "data" in ["trades", "open_trades"] and isinstance(arg_data, (list, dict)):
            arg_data = pd.DataFrame(arg_data)
        elif "data" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_data, list):
            arg_data = pd.Series(arg_data)
        kwargs["data"] = arg_data

        arg_bins = bins
        if "bins" in ["trades", "open_trades"] and isinstance(arg_bins, (list, dict)):
            arg_bins = pd.DataFrame(arg_bins)
        elif "bins" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_bins, list):
            arg_bins = pd.Series(arg_bins)
        kwargs["bins"] = arg_bins

        res = _histogram_data_impl(**kwargs)
        logger.info("Executed histogram_data tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "histogram_data", data={"histogram_data": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def detect_outliers(
    data: pd.Series | np.ndarray,
    method: Literal["zscore", "iqr"] = "zscore",
    threshold: float | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _detect_outliers_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_data = data
        if "data" in ["trades", "open_trades"] and isinstance(arg_data, (list, dict)):
            arg_data = pd.DataFrame(arg_data)
        elif "data" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_data, list):
            arg_data = pd.Series(arg_data)
        kwargs["data"] = arg_data

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

        res = _detect_outliers_impl(**kwargs)
        logger.info("Executed detect_outliers tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "detect_outliers", data={"detect_outliers": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def outlier_ratio(
    data: pd.Series | np.ndarray,
    method: Literal["zscore", "iqr"] = "zscore",
    threshold: float | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _outlier_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_data = data
        if "data" in ["trades", "open_trades"] and isinstance(arg_data, (list, dict)):
            arg_data = pd.DataFrame(arg_data)
        elif "data" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_data, list):
            arg_data = pd.Series(arg_data)
        kwargs["data"] = arg_data

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

        res = _outlier_ratio_impl(**kwargs)
        logger.info("Executed outlier_ratio tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "outlier_ratio", data={"outlier_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def calculate_distribution_metrics(
    *,
    values: list[float],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_distribution_metrics_impl."""
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

        res = _calculate_distribution_metrics_impl(**kwargs)
        logger.info("Executed calculate_distribution_metrics tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "calculate_distribution_metrics",
            data={"calculate_distribution_metrics": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}
