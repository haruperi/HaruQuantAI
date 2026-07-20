"""statistical_tests.py - Validate strategy robustness with bootstrap, permutation, multiple-testing, and overfitting diagnostics.

Classes:
    BootstrapResult: Point estimate and confidence intervals for a metric.
    PermutationTestResult: Significance from random reshuffling.
    WhitesRealityCheckResult: Data snooping bias correction results.

Functions:
    _clean_returns: Normalize input to a finite 1D NumPy float array.
    _sharpe_ratio: Stable Sharpe calculation for internal bootstrap/permutations.
    _validate_probability: Ensure a probability value is within (0, 1).
    _safe_block_size: Ensure block size is at least 1.
    _safe_n: Ensure n is at least min_val.
    _bootstrap_kernel: General bootstrap kernel supporting IID (block_size=1) and circular block bootstrap.
    _sign_flip_kernel: Generate sign-flipped return series for order-insensitive metrics.
    whites_reality_check: White's Reality Check for data snooping bias.
    permutation_test: Significance test using random reshuffling or sign-flipping.
    bootstrap_confidence_intervals: Estimate metric uncertainty using non-parametric bootstrap.
    deflated_sharpe_ratio: Adjust Sharpe ratio for multiple testing and non-normality.
    probability_of_backtest_overfitting: Estimate Probability of Backtest Overfitting (PBO).
    walk_forward_degradation_score: Measures the performance decay from Train/IS to Test/OOS.
    bootstrap_probability_above_threshold: Probability that a bootstrapped metric exceeds a given threshold.
    bonferroni_correction: Strict Bonferroni correction for multiple hypothesis testing.
    benjamini_hochberg_correction: Benjamini-Hochberg False Discovery Rate (FDR) control.
    sample_size_warning: Audit metric reliability based on sample size.
    stability_score: Consistency of performance across walk-forward windows.
    _returns_from_backtest_result: Extract return array from a BacktestResult object.
    whites_reality_check_backtests: Wrapper for White's Reality Check taking BacktestResult objects.
    permutation_test_backtest: Wrapper for permutation test taking a BacktestResult object.
    bootstrap_confidence_intervals_backtest: Wrapper for bootstrap CIs taking a BacktestResult object.
    print_statistical_validation_report: Print comprehensive statistical validation report.

Nested functions and methods:
    BootstrapResult.__repr__: Return a compact confidence interval summary.
    PermutationTestResult.__repr__: Return a compact permutation-test significance summary.
    WhitesRealityCheckResult.__repr__: Return a compact White's Reality Check summary.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, cast

import numpy as np
import pandas as pd

try:
    from scipy import stats

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

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


def _clean_returns(data: np.ndarray | pd.Series) -> np.ndarray:
    """Normalize input to a finite 1D NumPy float array."""
    arr = cast("np.ndarray", np.asarray(data, dtype=float))
    return cast("np.ndarray", arr[np.isfinite(arr)])


def _sharpe_ratio(rets: np.ndarray, periods_per_year: int = 252) -> float:
    """Stable Sharpe calculation for internal bootstrap/permutations."""
    if len(rets) < 2:
        return 0.0
    mean, std = np.mean(rets), np.std(rets)
    if std < 1e-12:
        return 0.0
    return float((mean / std) * np.sqrt(periods_per_year))


def _validate_probability(value: float, name: str) -> None:
    """Ensure a probability value is within (0, 1)."""
    if not 0.0 < value < 1.0:
        raise ValueError(f"{name} must be between 0 and 1 (exclusive)")


def _safe_block_size(block_size: int) -> int:
    """Ensure block size is at least 1."""
    return max(1, int(block_size))


def _safe_n(n: int, min_val: int = 10) -> int:
    """Ensure n is at least min_val."""
    return max(min_val, int(n))


# =========================================================================
# Data Models
# =========================================================================


@dataclass
class BootstrapResult:
    """Point estimate and confidence intervals for a metric."""

    metric_name: str
    point_estimate: float
    mean: float
    median: float
    std: float
    ci_lower: float
    ci_upper: float
    confidence_level: float
    n_bootstrap: int

    def __repr__(self) -> str:
        """Return a compact confidence interval summary."""
        return (
            f"{self.metric_name}: {self.point_estimate:.4f} "
            f"[{self.ci_lower:.4f}, {self.ci_upper:.4f}] "
            f"({self.confidence_level * 100:.0f}% CI)"
        )


@dataclass
class PermutationTestResult:
    """Significance from random reshuffling."""

    metric_name: str
    observed_value: float
    p_value: float
    is_significant: bool
    significance_level: float
    n_permutations: int
    null_distribution_mean: float
    null_distribution_std: float

    def __repr__(self) -> str:
        """Return a compact permutation-test significance summary."""
        sig = "✓ Significant" if self.is_significant else "✗ Not significant"
        return (
            f"{self.metric_name}: {self.observed_value:.4f}, "
            f"p={self.p_value:.4f} ({sig} at α={self.significance_level})"
        )


@dataclass
class WhitesRealityCheckResult:
    """Data snooping bias correction results."""

    best_strategy_name: str
    best_performance: float
    p_value: float
    is_significant: bool
    significance_level: float
    n_strategies: int
    n_bootstrap: int

    def __repr__(self) -> str:
        """Return a compact White's Reality Check summary."""
        sig = "✓ Significant" if self.is_significant else "✗ Likely overfit"
        return (
            f"Best: {self.best_strategy_name} ({self.best_performance:.4f}), "
            f"p={self.p_value:.4f} ({sig})"
        )


if TYPE_CHECKING:
    BacktestResult = Any


try:
    from numba import njit
except ImportError:

    def njit(*_args: Any, **_kwargs: Any):
        """Return a no-op decorator when numba is unavailable."""

        def decorator(f):
            """Return the original function unchanged."""
            return f

        return decorator


# =========================================================================
# Utility & Kernel Helpers
# =========================================================================


@njit(cache=True)
def _bootstrap_kernel(
    returns: np.ndarray, n_bootstrap: int, block_size: int = 1
) -> np.ndarray:
    """
    General bootstrap kernel supporting IID (block_size=1) and circular block bootstrap.
    """
    n = len(returns)
    bootstrap_samples = np.zeros((n_bootstrap, n))

    for i in range(n_bootstrap):
        if block_size <= 1:
            indices = np.random.choice(n, size=n, replace=True)
            bootstrap_samples[i] = returns[indices]
        else:
            # Circular Block Bootstrap
            num_blocks = (n + block_size - 1) // block_size
            boot_idx: np.ndarray = np.zeros(n, dtype=np.int32)
            for j in range(num_blocks):
                start = np.random.randint(0, n)
                for k in range(block_size):
                    idx = (j * block_size) + k
                    if idx < n:
                        boot_idx[idx] = (start + k) % n
            bootstrap_samples[i] = returns[boot_idx]

    return bootstrap_samples


@njit(cache=True)
def _sign_flip_kernel(returns: np.ndarray, n_permutations: int) -> np.ndarray:
    """Generate sign-flipped return series for order-insensitive metrics."""
    n = len(returns)
    results = np.zeros((n_permutations, n))
    for i in range(n_permutations):
        signs = np.random.choice(np.array([-1.0, 1.0]), size=n)
        results[i] = returns * signs
    return results


# =========================================================================
# Core Validation Tests
# =========================================================================


def _whites_reality_check_impl(
    strategy_returns: list[np.ndarray | pd.Series],
    benchmark_returns: np.ndarray | pd.Series,
    metric_func: Callable[[np.ndarray], float] | None = None,
    n_bootstrap: int = 1000,
    block_size: int = 1,
    significance_level: float = 0.05,
    seed: int | None = None,
) -> WhitesRealityCheckResult:
    """White's Reality Check for data snooping bias.

    Purpose:
        White's Reality Check for data snooping bias.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        strategy_returns:
            Analytics input consumed by this function.
        benchmark_returns:
            Analytics input consumed by this function.
        metric_func:
            Analytics input consumed by this function.
        n_bootstrap:
            Analytics input consumed by this function.
        block_size:
            Analytics input consumed by this function.
        significance_level:
            Analytics input consumed by this function.
        seed:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    _validate_probability(significance_level, "significance_level")
    n_bootstrap = _safe_n(n_bootstrap, min_val=10)
    block_size = _safe_block_size(block_size)

    if metric_func is None:
        metric_func = _sharpe_ratio

    _validate_probability(significance_level, "significance_level")
    if seed is not None:
        np.random.seed(seed)

    b_rets = _clean_returns(benchmark_returns)
    s_rets_raw = [_clean_returns(r) for r in strategy_returns]

    # Filter empty or insufficient strategies
    s_rets = [r for r in s_rets_raw if len(r) >= 3]
    if not s_rets or len(b_rets) < 3:
        return WhitesRealityCheckResult(
            "None",
            0.0,
            1.0,
            False,
            significance_level,
            len(strategy_returns),
            n_bootstrap,
        )

    # Align to minimum length
    min_len = min([len(r) for r in s_rets] + [len(b_rets)])

    b_aligned = b_rets[:min_len]
    s_aligned = np.stack([r[:min_len] for r in s_rets])

    # Observed performances
    n_strats = len(s_rets)
    obs_bench = metric_func(b_aligned)
    obs_strats = np.array([metric_func(s) for s in s_aligned])

    best_idx = np.argmax(obs_strats)
    best_outperf = obs_strats[best_idx] - obs_bench

    # Bootstrap centered differentials
    # V_i = Strategy_i - Benchmark
    # Null hypothesis: E[V_i] <= 0
    boot_samples = _bootstrap_kernel(np.arange(min_len), n_bootstrap, block_size)
    boot_max_outperfs = np.zeros(n_bootstrap)

    # Centering: Subtract observed mean performance so null mean is 0
    # For many metrics (like Sharpe), we bootstrap the returns and recalculate,
    # then subtract the original observed metric.
    for b in range(n_bootstrap):
        idx = boot_samples[b].astype(np.int32)
        boot_bench_rets = b_aligned[idx]
        boot_bench_perf = metric_func(boot_bench_rets)

        max_v = -1e18
        for s in range(n_strats):
            boot_strat_rets = s_aligned[s][idx]
            boot_strat_perf = metric_func(boot_strat_rets)

            # Centered outperformance
            v_centered = (boot_strat_perf - boot_bench_perf) - (
                obs_strats[s] - obs_bench
            )
            max_v = max(max_v, v_centered)

        boot_max_outperfs[b] = max_v

    p_val = np.mean(boot_max_outperfs >= best_outperf)

    logger.info(f"White's Reality Check: p={p_val:.4f} ({n_strats} strategies)")
    return WhitesRealityCheckResult(
        f"Strategy {best_idx}",
        float(obs_strats[best_idx]),
        float(p_val),
        bool(p_val < significance_level),
        significance_level,
        n_strats,
        n_bootstrap,
    )


def _permutation_test_impl(
    returns: np.ndarray | pd.Series,
    metric_func: Callable[[np.ndarray], float] | None = None,
    method: Literal["shuffle", "sign_flip"] = "sign_flip",
    n_permutations: int = 1000,
    significance_level: float = 0.05,
    seed: int | None = None,
) -> PermutationTestResult:
    """Significance test using random reshuffling or sign-flipping.

    Purpose:
        Significance test using random reshuffling or sign-flipping.
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
        metric_func:
            Analytics input consumed by this function.
        method:
            Analytics input consumed by this function.
        n_permutations:
            Analytics input consumed by this function.
        significance_level:
            Analytics input consumed by this function.
        seed:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    _validate_probability(significance_level, "significance_level")
    n_permutations = _safe_n(n_permutations, min_val=10)
    if seed is not None:
        np.random.seed(seed)
    if hasattr(returns, "get_equity_df"):
        rets = _returns_from_backtest_result(returns)
    else:
        rets = _clean_returns(returns)

    if metric_func is None:
        metric_func = _sharpe_ratio
        metric_name = "Sharpe Ratio"
    else:
        metric_name = getattr(metric_func, "__name__", "Custom Metric")

    if len(rets) < 2:
        return PermutationTestResult(
            metric_name,
            0.0,
            1.0,
            False,
            significance_level,
            n_permutations,
            0.0,
            0.0,
        )

    observed = metric_func(rets)

    if method == "shuffle":
        null_dist = np.array(
            [metric_func(np.random.permutation(rets)) for _ in range(n_permutations)]
        )
    else:
        # Sign-flip is better for Sharpe and order-insensitive metrics
        sign_flipped_samples = _sign_flip_kernel(rets, n_permutations)
        null_dist = np.array([metric_func(s) for s in sign_flipped_samples])

    p_val = np.mean(np.abs(null_dist) >= np.abs(observed))

    logger.info(f"Permutation test ({method}): p={p_val:.4f}")
    return PermutationTestResult(
        metric_name,
        float(observed),
        float(p_val),
        bool(p_val < significance_level),
        significance_level,
        n_permutations,
        float(null_dist.mean()),
        float(null_dist.std()),
    )


def _bootstrap_confidence_intervals_impl(
    returns: np.ndarray | pd.Series,
    metrics_dict: dict[str, Callable[[np.ndarray], float]] | None = None,
    n_bootstrap: int = 1000,
    block_size: int = 1,
    confidence_level: float = 0.95,
    periods_per_year: int = 252,
    seed: int | None = None,
) -> list[BootstrapResult]:
    """Estimate metric uncertainty using non-parametric bootstrap.

    Purpose:
        Estimate metric uncertainty using non-parametric bootstrap.
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
        metrics_dict:
            Analytics input consumed by this function.
        n_bootstrap:
            Analytics input consumed by this function.
        block_size:
            Analytics input consumed by this function.
        confidence_level:
            Analytics input consumed by this function.
        periods_per_year:
            Analytics input consumed by this function.
        seed:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    _validate_probability(confidence_level, "confidence_level")
    n_bootstrap = _safe_n(n_bootstrap, min_val=10)
    block_size = _safe_block_size(block_size)
    if seed is not None:
        np.random.seed(seed)
    rets = _clean_returns(returns)
    if len(rets) < 2:
        return []

    if metrics_dict is None:
        metrics_dict = {
            "Sharpe Ratio": lambda r: _sharpe_ratio(r, periods_per_year),
            "Total Return %": lambda r: (np.prod(1 + r) - 1) * 100,
            "Volatility %": lambda r: np.std(r) * np.sqrt(periods_per_year) * 100,
        }

    boot_samples = _bootstrap_kernel(rets, n_bootstrap, block_size)
    results = []

    for name, func in metrics_dict.items():
        point = func(rets)
        boot_vals = np.array([func(s) for s in boot_samples])

        # Guard against NaNs in bootstrap distribution
        boot_vals = boot_vals[np.isfinite(boot_vals)]
        if len(boot_vals) == 0:
            continue

        alpha = 1 - confidence_level
        results.append(
            BootstrapResult(
                name,
                float(point),
                float(boot_vals.mean()),
                float(np.median(boot_vals)),
                float(boot_vals.std()),
                float(np.percentile(boot_vals, alpha / 2 * 100)),
                float(np.percentile(boot_vals, (1 - alpha / 2) * 100)),
                float(confidence_level),
                n_bootstrap,
            )
        )

    logger.info(f"Bootstrap CIs complete ({'block' if block_size > 1 else 'iid'})")
    return results


def _deflated_sharpe_ratio_impl(
    observed_sharpe: float,
    n_trials: int,
    n_observations: int,
    expected_sharpe: float = 0.0,
    skew: float = 0.0,
    kurt: float = 3.0,
) -> tuple[float, float]:
    """Adjust Sharpe ratio for multiple testing and non-normality.

    Purpose:
        Adjust Sharpe ratio for multiple testing and non-normality.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        observed_sharpe:
            Analytics input consumed by this function.
        n_trials:
            Analytics input consumed by this function.
        n_observations:
            Analytics input consumed by this function.
        expected_sharpe:
            Analytics input consumed by this function.
        skew:
            Analytics input consumed by this function.
        kurt:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if not HAS_SCIPY:
        return 0.0, 1.0

    if n_trials < 1 or n_observations < 3:
        return 0.0, 1.0

    var_sr = (
        1.0
        + 0.5 * observed_sharpe**2
        - skew * observed_sharpe
        + ((kurt - 1.0) / 4.0) * observed_sharpe**2
    ) / (n_observations - 1)

    std_sr = np.sqrt(max(0.0, var_sr))

    if std_sr <= 1e-12:
        return 0.0, 1.0

    if n_trials > 1:
        gamma = 0.57721566490153286
        z_max = (1.0 - gamma) * stats.norm.ppf(
            1.0 - 1.0 / n_trials
        ) + gamma * stats.norm.ppf(1.0 - 1.0 / (n_trials * np.e))
        expected_max_sr = expected_sharpe + std_sr * z_max
    else:
        expected_max_sr = expected_sharpe

    z_stat = (observed_sharpe - expected_max_sr) / std_sr
    p_val = 1.0 - stats.norm.cdf(z_stat)

    logger.info(
        f"DSR: obs={observed_sharpe:.2f}, exp_max={expected_max_sr:.2f}, z={z_stat:.4f}, p={p_val:.4f}"
    )
    return float(z_stat), float(p_val)


# =========================================================================
# Advanced Robustness Metrics
# =========================================================================


def _probability_of_backtest_overfitting_impl(
    in_sample_scores: np.ndarray,
    out_of_sample_scores: np.ndarray,
) -> dict[str, float]:
    """Estimate Probability of Backtest Overfitting (PBO).

    Purpose:
        Estimate Probability of Backtest Overfitting (PBO).
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        in_sample_scores:
            Analytics input consumed by this function.
        out_of_sample_scores:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if in_sample_scores.shape != out_of_sample_scores.shape:
        raise ValueError(
            "in_sample_scores and out_of_sample_scores must have the same shape"
        )

    n_windows, n_strats = in_sample_scores.shape
    if n_windows < 2 or n_strats < 2:
        return {"pbo": 0.0, "rank_loss": 0.0}

    # Relative ranks in each window
    # For each window, find which strategy was best in-sample
    best_is_indices = np.argmax(in_sample_scores, axis=1)

    # Check the rank of these 'best' strategies in the out-of-sample period
    # Rank OOS scores: 1.0 = best, 0.0 = worst
    oos_ranks = np.zeros(n_windows)
    for i in range(n_windows):
        window_oos = out_of_sample_scores[i]
        # Percentile rank of the best IS strategy in OOS
        best_idx = best_is_indices[i]
        oos_ranks[i] = np.mean(window_oos <= window_oos[best_idx])

    # PBO is defined as the probability that the rank is below 0.5
    pbo = np.mean(oos_ranks < 0.5)

    return {
        "pbo": float(pbo),
        "mean_oos_rank": float(np.mean(oos_ranks)),
        "median_oos_rank": float(np.median(oos_ranks)),
        "rank_loss": float(1.0 - np.mean(oos_ranks)),
    }


def _walk_forward_degradation_score_impl(
    train_scores: np.ndarray | pd.Series,
    test_scores: np.ndarray | pd.Series,
) -> dict[str, float]:
    """Measures the performance decay from Train/IS to Test/OOS.

    Purpose:
        Measures the performance decay from Train/IS to Test/OOS.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        train_scores:
            Analytics input consumed by this function.
        test_scores:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    train = _clean_returns(train_scores)
    test = _clean_returns(test_scores)

    if len(train) == 0 or len(test) == 0:
        return {}

    mu_train, mu_test = train.mean(), test.mean()
    abs_degrad = mu_train - mu_test
    rel_degrad = (abs_degrad / abs(mu_train)) if mu_train != 0 else 0.0

    return {
        "train_mean": float(mu_train),
        "test_mean": float(mu_test),
        "absolute_degradation": float(abs_degrad),
        "relative_degradation_pct": float(rel_degrad * 100.0),
        "degradation_ratio": float(mu_test / mu_train if mu_train != 0 else 1.0),
    }


def _bootstrap_probability_above_threshold_impl(
    returns: np.ndarray | pd.Series,
    metric_func: Callable[[np.ndarray], float],
    threshold: float,
    n_bootstrap: int = 1000,
    block_size: int = 1,
    seed: int | None = None,
) -> float:
    """Probability that a bootstrapped metric exceeds a given threshold.

    Purpose:
        Probability that a bootstrapped metric exceeds a given threshold.
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
        metric_func:
            Analytics input consumed by this function.
        threshold:
            Analytics input consumed by this function.
        n_bootstrap:
            Analytics input consumed by this function.
        block_size:
            Analytics input consumed by this function.
        seed:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if seed is not None:
        np.random.seed(seed)
    rets = _clean_returns(returns)
    if len(rets) < 5:
        return 0.0

    n_bootstrap = _safe_n(n_bootstrap)
    block_size = _safe_block_size(block_size)

    boot_samples = _bootstrap_kernel(rets, n_bootstrap, block_size)
    boot_metrics = np.array([metric_func(s) for s in boot_samples])

    prob = np.mean(boot_metrics > threshold)
    return float(prob)


# =========================================================================
# Multiple Testing Corrections
# =========================================================================


def _bonferroni_correction_impl(
    p_values: np.ndarray | list[float],
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Strict Bonferroni correction for multiple hypothesis testing.

    Purpose:
        Strict Bonferroni correction for multiple hypothesis testing.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        p_values:
            Analytics input consumed by this function.
        alpha:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    _validate_probability(alpha, "alpha")
    p_vals = np.asarray(p_values)
    n = len(p_vals)
    adj_alpha = alpha / n if n > 0 else alpha

    return {
        "alpha": alpha,
        "adjusted_alpha": adj_alpha,
        "significant_count": int(np.sum(p_vals < adj_alpha)),
        "is_significant": p_vals < adj_alpha,
    }


def _benjamini_hochberg_correction_impl(
    p_values: np.ndarray | list[float],
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Benjamini-Hochberg False Discovery Rate (FDR) control.

    Purpose:
        Benjamini-Hochberg False Discovery Rate (FDR) control.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        p_values:
            Analytics input consumed by this function.
        alpha:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    _validate_probability(alpha, "alpha")
    p_vals = np.asarray(p_values)
    n = len(p_vals)
    if n == 0:
        return {}

    # Sort p-values
    sorted_idx = np.argsort(p_vals)
    sorted_p = p_vals[sorted_idx]

    # BH critical values: (i/n) * alpha
    crit_vals = (np.arange(1, n + 1) / n) * alpha

    # Find the largest k such that p(k) <= crit_val(k)
    significant = sorted_p <= crit_vals
    if not np.any(significant):
        k = 0
    else:
        k = np.max(np.where(significant)[0]) + 1

    # All p-values up to rank k are considered significant
    reject: np.ndarray = np.zeros(n, dtype=bool)
    if k > 0:
        reject[sorted_idx[:k]] = True

    return {"alpha": alpha, "k_limit": k, "significant_count": k, "reject": reject}


def _sample_size_warning_impl(
    n_observations: int, min_recommended: int = 100
) -> dict[str, Any]:
    """Audit metric reliability based on sample size.

    Purpose:
        Audit metric reliability based on sample size.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        n_observations:
            Analytics input consumed by this function.
        min_recommended:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    return {
        "n_observations": n_observations,
        "min_recommended": min_recommended,
        "is_sufficient": n_observations >= min_recommended,
        "reliability_score": min(1.0, n_observations / min_recommended),
    }


def _stability_score_impl(
    walk_forward_results: list[dict[str, Any]], metric_key: str = "sharpe_ratio"
) -> dict[str, float]:
    """Consistency of performance across walk-forward windows.

    Purpose:
        Consistency of performance across walk-forward windows.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        walk_forward_results:
            Analytics input consumed by this function.
        metric_key:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    if not walk_forward_results:
        return {
            "test_mean": 0.0,
            "test_std": 0.0,
            "stability_ratio": 0.0,
            "degradation": 1.0,
            "consistency": 0.0,
        }

    t_key, v_key = f"train_{metric_key}", f"test_{metric_key}"
    train_m = np.array([w[t_key] for w in walk_forward_results if t_key in w])
    test_m = np.array([w[v_key] for w in walk_forward_results if v_key in w])

    if len(test_m) == 0:
        return {
            "test_mean": 0.0,
            "test_std": 0.0,
            "stability_ratio": 0.0,
            "degradation": 1.0,
            "consistency": 0.0,
        }

    mu, sigma = test_m.mean(), test_m.std()
    train_mu = train_m.mean() if len(train_m) > 0 else 0.0

    stability = {
        "test_mean": float(mu),
        "test_std": float(sigma),
        "test_min": float(test_m.min()),
        "test_max": float(test_m.max()),
        "stability_ratio": float(mu / sigma if sigma > 0 else 0.0),
        "degradation": float((train_mu - mu) / abs(train_mu) if train_mu != 0 else 0.0),
        "consistency": float(np.mean(test_m > 0) * 100),
    }
    logger.info(f"Stability: mean={mu:.4f}, degradation={stability['degradation']:.2%}")
    return stability


# =========================================================================
# BacktestResult Wrappers
# =========================================================================


def _returns_from_backtest_result(result: "BacktestResult") -> np.ndarray:
    """Extract return array from a BacktestResult object."""
    try:
        eq = result.get_equity_df()
        if eq is None or len(eq) < 2:
            return np.array([], dtype=float)
        returns = eq["equity"].pct_change().dropna()
        return cast("np.ndarray", _clean_returns(returns))
    except (AttributeError, KeyError, TypeError, ValueError):
        return np.array([], dtype=float)


def _whites_reality_check_backtests_impl(
    strategy_results: list["BacktestResult"],
    benchmark_result: "BacktestResult",
    metric_func: Callable[[np.ndarray], float] | None = None,
    **kwargs,
) -> WhitesRealityCheckResult:
    """Wrapper for White's Reality Check taking BacktestResult objects.

    Purpose:
        Wrapper for White's Reality Check taking BacktestResult objects.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        strategy_results:
            Analytics input consumed by this function.
        benchmark_result:
            Analytics input consumed by this function.
        metric_func:
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
    valid_data = [
        (r.strategy_name, _returns_from_backtest_result(r)) for r in strategy_results
    ]

    # Filter for sufficient length
    valid_data = [(name, rets) for name, rets in valid_data if len(rets) >= 3]

    if not valid_data:
        return WhitesRealityCheckResult(
            "None",
            0.0,
            1.0,
            False,
            kwargs.get("significance_level", 0.05),
            len(strategy_results),
            kwargs.get("n_bootstrap", 1000),
        )

    names = [x[0] for x in valid_data]
    s_rets = [x[1] for x in valid_data]
    b_rets = _returns_from_backtest_result(benchmark_result)

    if metric_func is None:
        metric_func = _sharpe_ratio

    result = _whites_reality_check_impl(
        s_rets, b_rets, metric_func=metric_func, **kwargs
    )

    # Map the relative "Strategy X" name back to the original strategy name.
    try:
        best_idx_str = result.best_strategy_name.split()[-1]
        if best_idx_str.isdigit():
            best_idx = int(best_idx_str)
            result.best_strategy_name = names[best_idx]
    except (IndexError, ValueError):
        pass

    return result


def _permutation_test_backtest_impl(
    strategy_result: "BacktestResult", **kwargs
) -> PermutationTestResult:
    """Wrapper for permutation test taking a BacktestResult object.

    Purpose:
        Wrapper for permutation test taking a BacktestResult object.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        strategy_result:
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
    rets = _returns_from_backtest_result(strategy_result)
    return _permutation_test_impl(rets, **kwargs)


def _bootstrap_confidence_intervals_backtest_impl(
    strategy_result: "BacktestResult", **kwargs
) -> list[BootstrapResult]:
    """Wrapper for bootstrap CIs taking a BacktestResult object.

    Purpose:
        Wrapper for bootstrap CIs taking a BacktestResult object.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        strategy_result:
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
    rets = _returns_from_backtest_result(strategy_result)
    return _bootstrap_confidence_intervals_impl(rets, **kwargs)


# =========================================================================
# Reporting Utilities
# =========================================================================


def _print_statistical_validation_report_impl(
    permutation_result: PermutationTestResult | None = None,
    bootstrap_results: list[BootstrapResult] | None = None,
    deflated_sharpe_result: tuple[float, float] | None = None,
    stability_result: dict[str, float] | None = None,
    whites_result: WhitesRealityCheckResult | None = None,
) -> None:
    """Print comprehensive statistical validation report.

    Purpose:
        Print comprehensive statistical validation report.
    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        permutation_result:
            Analytics input consumed by this function.
        bootstrap_results:
            Analytics input consumed by this function.
        deflated_sharpe_result:
            Analytics input consumed by this function.
        stability_result:
            Analytics input consumed by this function.
        whites_result:
            Analytics input consumed by this function.

    Returns:
        Analytics result produced by this function. Agent-facing wrapper tools return
        the standard HaruQuant tool result dictionary; scalar and series helpers
        return their documented analytics value.

    Raises:
        Raises only for invalid caller inputs or unexpected computation errors.
    """
    print("\n" + "=" * 70 + "\nSTATISTICAL VALIDATION REPORT\n" + "=" * 70)

    if permutation_result:
        print("\n" + "-" * 70 + "\nPERMUTATION TEST\n" + "-" * 70)
        print(
            f"  Metric: {permutation_result.metric_name}\n  Observed: {permutation_result.observed_value:>10.4f}"
        )
        print(
            f"  P-value:  {permutation_result.p_value:>10.4f}\n  Result:   {'✓ Significant' if permutation_result.is_significant else '✗ Not Significant'}"
        )

    if bootstrap_results:
        print("\n" + "-" * 70 + "\nBOOTSTRAP CONFIDENCE INTERVALS\n" + "-" * 70)
        for br in bootstrap_results:
            print(
                f"  {br.metric_name}: {br.point_estimate:.4f} [{br.ci_lower:.4f}, {br.ci_upper:.4f}]"
            )

    if deflated_sharpe_result:
        dsr, p = deflated_sharpe_result
        print("\n" + "-" * 70 + "\nDEFLATED SHARPE RATIO\n" + "-" * 70)
        print(f"  DSR:      {dsr:>10.4f}\n  P-value:  {p:>10.4f}")

    if stability_result:
        print("\n" + "-" * 70 + "\nWALK-FORWARD STABILITY\n" + "-" * 70)
        print(
            f"  Test Mean: {stability_result['test_mean']:>10.4f}\n  Ratio:     {stability_result['stability_ratio']:>10.4f}"
        )
        print(
            f"  Degrad:    {stability_result['degradation']:>10.2%}\n  Consist:   {stability_result['consistency']:>10.1f}%"
        )

    if whites_result:
        print("\n" + "-" * 70 + "\nWHITE'S REALITY CHECK\n" + "-" * 70)
        print(
            f"  Best:     {whites_result.best_strategy_name}\n  P-value:  {whites_result.p_value:>10.4f}"
        )
        print(
            f"  Result:   {'✓ Significant' if whites_result.is_significant else '✗ Likely Overfit'}"
        )
    print("\n" + "=" * 70 + "\n")


def _whites_reality_check_impl(
    strategy_returns: list[np.ndarray | pd.Series],
    benchmark_returns: np.ndarray | pd.Series,
    metric_func: Callable[[np.ndarray], float] | None = None,
    n_bootstrap: int = 1000,
    block_size: int = 1,
    significance_level: float = 0.05,
    seed: int | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _whites_reality_check_impl."""
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

        arg_metric_func = metric_func
        if "metric_func" in ["trades", "open_trades"] and isinstance(
            arg_metric_func, (list, dict)
        ):
            arg_metric_func = pd.DataFrame(arg_metric_func)
        elif "metric_func" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_metric_func, list):
            arg_metric_func = pd.Series(arg_metric_func)
        kwargs["metric_func"] = arg_metric_func

        arg_n_bootstrap = n_bootstrap
        if "n_bootstrap" in ["trades", "open_trades"] and isinstance(
            arg_n_bootstrap, (list, dict)
        ):
            arg_n_bootstrap = pd.DataFrame(arg_n_bootstrap)
        elif "n_bootstrap" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_n_bootstrap, list):
            arg_n_bootstrap = pd.Series(arg_n_bootstrap)
        kwargs["n_bootstrap"] = arg_n_bootstrap

        arg_block_size = block_size
        if "block_size" in ["trades", "open_trades"] and isinstance(
            arg_block_size, (list, dict)
        ):
            arg_block_size = pd.DataFrame(arg_block_size)
        elif "block_size" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_block_size, list):
            arg_block_size = pd.Series(arg_block_size)
        kwargs["block_size"] = arg_block_size

        arg_significance_level = significance_level
        if "significance_level" in ["trades", "open_trades"] and isinstance(
            arg_significance_level, (list, dict)
        ):
            arg_significance_level = pd.DataFrame(arg_significance_level)
        elif "significance_level" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_significance_level, list):
            arg_significance_level = pd.Series(arg_significance_level)
        kwargs["significance_level"] = arg_significance_level

        arg_seed = seed
        if "seed" in ["trades", "open_trades"] and isinstance(arg_seed, (list, dict)):
            arg_seed = pd.DataFrame(arg_seed)
        elif "seed" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_seed, list):
            arg_seed = pd.Series(arg_seed)
        kwargs["seed"] = arg_seed

        res = _whites_reality_check_impl(**kwargs)
        logger.info("Executed whites_reality_check tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "whites_reality_check", data={"whites_reality_check": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _permutation_test_impl(
    returns: np.ndarray | pd.Series,
    metric_func: Callable[[np.ndarray], float] | None = None,
    method: Literal["shuffle", "sign_flip"] = "sign_flip",
    n_permutations: int = 1000,
    significance_level: float = 0.05,
    seed: int | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _permutation_test_impl."""
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

        arg_metric_func = metric_func
        if "metric_func" in ["trades", "open_trades"] and isinstance(
            arg_metric_func, (list, dict)
        ):
            arg_metric_func = pd.DataFrame(arg_metric_func)
        elif "metric_func" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_metric_func, list):
            arg_metric_func = pd.Series(arg_metric_func)
        kwargs["metric_func"] = arg_metric_func

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

        arg_n_permutations = n_permutations
        if "n_permutations" in ["trades", "open_trades"] and isinstance(
            arg_n_permutations, (list, dict)
        ):
            arg_n_permutations = pd.DataFrame(arg_n_permutations)
        elif "n_permutations" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_n_permutations, list):
            arg_n_permutations = pd.Series(arg_n_permutations)
        kwargs["n_permutations"] = arg_n_permutations

        arg_significance_level = significance_level
        if "significance_level" in ["trades", "open_trades"] and isinstance(
            arg_significance_level, (list, dict)
        ):
            arg_significance_level = pd.DataFrame(arg_significance_level)
        elif "significance_level" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_significance_level, list):
            arg_significance_level = pd.Series(arg_significance_level)
        kwargs["significance_level"] = arg_significance_level

        arg_seed = seed
        if "seed" in ["trades", "open_trades"] and isinstance(arg_seed, (list, dict)):
            arg_seed = pd.DataFrame(arg_seed)
        elif "seed" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_seed, list):
            arg_seed = pd.Series(arg_seed)
        kwargs["seed"] = arg_seed

        res = _permutation_test_impl(**kwargs)
        logger.info("Executed permutation_test tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "permutation_test", data={"permutation_test": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _bootstrap_confidence_intervals_impl(
    returns: np.ndarray | pd.Series,
    metrics_dict: dict[str, Callable[[np.ndarray], float]] | None = None,
    n_bootstrap: int = 1000,
    block_size: int = 1,
    confidence_level: float = 0.95,
    periods_per_year: int = 252,
    seed: int | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _bootstrap_confidence_intervals_impl."""
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

        arg_metrics_dict = metrics_dict
        if "metrics_dict" in ["trades", "open_trades"] and isinstance(
            arg_metrics_dict, (list, dict)
        ):
            arg_metrics_dict = pd.DataFrame(arg_metrics_dict)
        elif "metrics_dict" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_metrics_dict, list):
            arg_metrics_dict = pd.Series(arg_metrics_dict)
        kwargs["metrics_dict"] = arg_metrics_dict

        arg_n_bootstrap = n_bootstrap
        if "n_bootstrap" in ["trades", "open_trades"] and isinstance(
            arg_n_bootstrap, (list, dict)
        ):
            arg_n_bootstrap = pd.DataFrame(arg_n_bootstrap)
        elif "n_bootstrap" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_n_bootstrap, list):
            arg_n_bootstrap = pd.Series(arg_n_bootstrap)
        kwargs["n_bootstrap"] = arg_n_bootstrap

        arg_block_size = block_size
        if "block_size" in ["trades", "open_trades"] and isinstance(
            arg_block_size, (list, dict)
        ):
            arg_block_size = pd.DataFrame(arg_block_size)
        elif "block_size" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_block_size, list):
            arg_block_size = pd.Series(arg_block_size)
        kwargs["block_size"] = arg_block_size

        arg_confidence_level = confidence_level
        if "confidence_level" in ["trades", "open_trades"] and isinstance(
            arg_confidence_level, (list, dict)
        ):
            arg_confidence_level = pd.DataFrame(arg_confidence_level)
        elif "confidence_level" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_confidence_level, list):
            arg_confidence_level = pd.Series(arg_confidence_level)
        kwargs["confidence_level"] = arg_confidence_level

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

        arg_seed = seed
        if "seed" in ["trades", "open_trades"] and isinstance(arg_seed, (list, dict)):
            arg_seed = pd.DataFrame(arg_seed)
        elif "seed" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_seed, list):
            arg_seed = pd.Series(arg_seed)
        kwargs["seed"] = arg_seed

        res = _bootstrap_confidence_intervals_impl(**kwargs)
        logger.info("Executed bootstrap_confidence_intervals tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "bootstrap_confidence_intervals",
            data={"bootstrap_confidence_intervals": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _deflated_sharpe_ratio_impl(
    observed_sharpe: float,
    n_trials: int,
    n_observations: int,
    expected_sharpe: float = 0.0,
    skew: float = 0.0,
    kurt: float = 3.0,
) -> dict[str, Any]:
    """AI Tool wrapper for _deflated_sharpe_ratio_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_observed_sharpe = observed_sharpe
        if "observed_sharpe" in ["trades", "open_trades"] and isinstance(
            arg_observed_sharpe, (list, dict)
        ):
            arg_observed_sharpe = pd.DataFrame(arg_observed_sharpe)
        elif "observed_sharpe" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_observed_sharpe, list):
            arg_observed_sharpe = pd.Series(arg_observed_sharpe)
        kwargs["observed_sharpe"] = arg_observed_sharpe

        arg_n_trials = n_trials
        if "n_trials" in ["trades", "open_trades"] and isinstance(
            arg_n_trials, (list, dict)
        ):
            arg_n_trials = pd.DataFrame(arg_n_trials)
        elif "n_trials" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_n_trials, list):
            arg_n_trials = pd.Series(arg_n_trials)
        kwargs["n_trials"] = arg_n_trials

        arg_n_observations = n_observations
        if "n_observations" in ["trades", "open_trades"] and isinstance(
            arg_n_observations, (list, dict)
        ):
            arg_n_observations = pd.DataFrame(arg_n_observations)
        elif "n_observations" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_n_observations, list):
            arg_n_observations = pd.Series(arg_n_observations)
        kwargs["n_observations"] = arg_n_observations

        arg_expected_sharpe = expected_sharpe
        if "expected_sharpe" in ["trades", "open_trades"] and isinstance(
            arg_expected_sharpe, (list, dict)
        ):
            arg_expected_sharpe = pd.DataFrame(arg_expected_sharpe)
        elif "expected_sharpe" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_expected_sharpe, list):
            arg_expected_sharpe = pd.Series(arg_expected_sharpe)
        kwargs["expected_sharpe"] = arg_expected_sharpe

        arg_skew = skew
        if "skew" in ["trades", "open_trades"] and isinstance(arg_skew, (list, dict)):
            arg_skew = pd.DataFrame(arg_skew)
        elif "skew" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_skew, list):
            arg_skew = pd.Series(arg_skew)
        kwargs["skew"] = arg_skew

        arg_kurt = kurt
        if "kurt" in ["trades", "open_trades"] and isinstance(arg_kurt, (list, dict)):
            arg_kurt = pd.DataFrame(arg_kurt)
        elif "kurt" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_kurt, list):
            arg_kurt = pd.Series(arg_kurt)
        kwargs["kurt"] = arg_kurt

        res = _deflated_sharpe_ratio_impl(**kwargs)
        logger.info("Executed deflated_sharpe_ratio tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "deflated_sharpe_ratio", data={"deflated_sharpe_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _probability_of_backtest_overfitting_impl(
    in_sample_scores: np.ndarray,
    out_of_sample_scores: np.ndarray,
) -> dict[str, Any]:
    """AI Tool wrapper for _probability_of_backtest_overfitting_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_in_sample_scores = in_sample_scores
        if "in_sample_scores" in ["trades", "open_trades"] and isinstance(
            arg_in_sample_scores, (list, dict)
        ):
            arg_in_sample_scores = pd.DataFrame(arg_in_sample_scores)
        elif "in_sample_scores" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_in_sample_scores, list):
            arg_in_sample_scores = pd.Series(arg_in_sample_scores)
        kwargs["in_sample_scores"] = arg_in_sample_scores

        arg_out_of_sample_scores = out_of_sample_scores
        if "out_of_sample_scores" in ["trades", "open_trades"] and isinstance(
            arg_out_of_sample_scores, (list, dict)
        ):
            arg_out_of_sample_scores = pd.DataFrame(arg_out_of_sample_scores)
        elif "out_of_sample_scores" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_out_of_sample_scores, list):
            arg_out_of_sample_scores = pd.Series(arg_out_of_sample_scores)
        kwargs["out_of_sample_scores"] = arg_out_of_sample_scores

        res = _probability_of_backtest_overfitting_impl(**kwargs)
        logger.info("Executed probability_of_backtest_overfitting tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "probability_of_backtest_overfitting",
            data={"probability_of_backtest_overfitting": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _walk_forward_degradation_score_impl(
    train_scores: np.ndarray | pd.Series,
    test_scores: np.ndarray | pd.Series,
) -> dict[str, Any]:
    """AI Tool wrapper for _walk_forward_degradation_score_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_train_scores = train_scores
        if "train_scores" in ["trades", "open_trades"] and isinstance(
            arg_train_scores, (list, dict)
        ):
            arg_train_scores = pd.DataFrame(arg_train_scores)
        elif "train_scores" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_train_scores, list):
            arg_train_scores = pd.Series(arg_train_scores)
        kwargs["train_scores"] = arg_train_scores

        arg_test_scores = test_scores
        if "test_scores" in ["trades", "open_trades"] and isinstance(
            arg_test_scores, (list, dict)
        ):
            arg_test_scores = pd.DataFrame(arg_test_scores)
        elif "test_scores" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_test_scores, list):
            arg_test_scores = pd.Series(arg_test_scores)
        kwargs["test_scores"] = arg_test_scores

        res = _walk_forward_degradation_score_impl(**kwargs)
        logger.info("Executed walk_forward_degradation_score tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "walk_forward_degradation_score",
            data={"walk_forward_degradation_score": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _bootstrap_probability_above_threshold_impl(
    returns: np.ndarray | pd.Series,
    metric_func: Callable[[np.ndarray], float],
    threshold: float,
    n_bootstrap: int = 1000,
    block_size: int = 1,
    seed: int | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _bootstrap_probability_above_threshold_impl."""
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

        arg_metric_func = metric_func
        if "metric_func" in ["trades", "open_trades"] and isinstance(
            arg_metric_func, (list, dict)
        ):
            arg_metric_func = pd.DataFrame(arg_metric_func)
        elif "metric_func" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_metric_func, list):
            arg_metric_func = pd.Series(arg_metric_func)
        kwargs["metric_func"] = arg_metric_func

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

        arg_n_bootstrap = n_bootstrap
        if "n_bootstrap" in ["trades", "open_trades"] and isinstance(
            arg_n_bootstrap, (list, dict)
        ):
            arg_n_bootstrap = pd.DataFrame(arg_n_bootstrap)
        elif "n_bootstrap" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_n_bootstrap, list):
            arg_n_bootstrap = pd.Series(arg_n_bootstrap)
        kwargs["n_bootstrap"] = arg_n_bootstrap

        arg_block_size = block_size
        if "block_size" in ["trades", "open_trades"] and isinstance(
            arg_block_size, (list, dict)
        ):
            arg_block_size = pd.DataFrame(arg_block_size)
        elif "block_size" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_block_size, list):
            arg_block_size = pd.Series(arg_block_size)
        kwargs["block_size"] = arg_block_size

        arg_seed = seed
        if "seed" in ["trades", "open_trades"] and isinstance(arg_seed, (list, dict)):
            arg_seed = pd.DataFrame(arg_seed)
        elif "seed" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_seed, list):
            arg_seed = pd.Series(arg_seed)
        kwargs["seed"] = arg_seed

        res = _bootstrap_probability_above_threshold_impl(**kwargs)
        logger.info("Executed bootstrap_probability_above_threshold tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "bootstrap_probability_above_threshold",
            data={"bootstrap_probability_above_threshold": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _bonferroni_correction_impl(
    p_values: np.ndarray | list[float],
    alpha: float = 0.05,
) -> dict[str, Any]:
    """AI Tool wrapper for _bonferroni_correction_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_p_values = p_values
        if "p_values" in ["trades", "open_trades"] and isinstance(
            arg_p_values, (list, dict)
        ):
            arg_p_values = pd.DataFrame(arg_p_values)
        elif "p_values" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_p_values, list):
            arg_p_values = pd.Series(arg_p_values)
        kwargs["p_values"] = arg_p_values

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

        res = _bonferroni_correction_impl(**kwargs)
        logger.info("Executed bonferroni_correction tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "bonferroni_correction", data={"bonferroni_correction": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _benjamini_hochberg_correction_impl(
    p_values: np.ndarray | list[float],
    alpha: float = 0.05,
) -> dict[str, Any]:
    """AI Tool wrapper for _benjamini_hochberg_correction_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_p_values = p_values
        if "p_values" in ["trades", "open_trades"] and isinstance(
            arg_p_values, (list, dict)
        ):
            arg_p_values = pd.DataFrame(arg_p_values)
        elif "p_values" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_p_values, list):
            arg_p_values = pd.Series(arg_p_values)
        kwargs["p_values"] = arg_p_values

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

        res = _benjamini_hochberg_correction_impl(**kwargs)
        logger.info("Executed benjamini_hochberg_correction tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "benjamini_hochberg_correction",
            data={"benjamini_hochberg_correction": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _sample_size_warning_impl(
    n_observations: int, min_recommended: int = 100
) -> dict[str, Any]:
    """AI Tool wrapper for _sample_size_warning_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_n_observations = n_observations
        if "n_observations" in ["trades", "open_trades"] and isinstance(
            arg_n_observations, (list, dict)
        ):
            arg_n_observations = pd.DataFrame(arg_n_observations)
        elif "n_observations" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_n_observations, list):
            arg_n_observations = pd.Series(arg_n_observations)
        kwargs["n_observations"] = arg_n_observations

        arg_min_recommended = min_recommended
        if "min_recommended" in ["trades", "open_trades"] and isinstance(
            arg_min_recommended, (list, dict)
        ):
            arg_min_recommended = pd.DataFrame(arg_min_recommended)
        elif "min_recommended" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_min_recommended, list):
            arg_min_recommended = pd.Series(arg_min_recommended)
        kwargs["min_recommended"] = arg_min_recommended

        res = _sample_size_warning_impl(**kwargs)
        logger.info("Executed sample_size_warning tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "sample_size_warning", data={"sample_size_warning": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _stability_score_impl(
    walk_forward_results: list[dict[str, Any]], metric_key: str = "sharpe_ratio"
) -> dict[str, Any]:
    """AI Tool wrapper for _stability_score_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_walk_forward_results = walk_forward_results
        if "walk_forward_results" in ["trades", "open_trades"] and isinstance(
            arg_walk_forward_results, (list, dict)
        ):
            arg_walk_forward_results = pd.DataFrame(arg_walk_forward_results)
        elif "walk_forward_results" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_walk_forward_results, list):
            arg_walk_forward_results = pd.Series(arg_walk_forward_results)
        kwargs["walk_forward_results"] = arg_walk_forward_results

        arg_metric_key = metric_key
        if "metric_key" in ["trades", "open_trades"] and isinstance(
            arg_metric_key, (list, dict)
        ):
            arg_metric_key = pd.DataFrame(arg_metric_key)
        elif "metric_key" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_metric_key, list):
            arg_metric_key = pd.Series(arg_metric_key)
        kwargs["metric_key"] = arg_metric_key

        res = _stability_score_impl(**kwargs)
        logger.info("Executed stability_score tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "stability_score", data={"stability_score": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _whites_reality_check_backtests_impl(
    strategy_results: list["BacktestResult"],
    benchmark_result: "BacktestResult",
    metric_func: Callable[[np.ndarray], float] | None = None,
    **kwargs,
) -> dict[str, Any]:
    """AI Tool wrapper for _whites_reality_check_backtests_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_strategy_results = strategy_results
        if "strategy_results" in ["trades", "open_trades"] and isinstance(
            arg_strategy_results, (list, dict)
        ):
            arg_strategy_results = pd.DataFrame(arg_strategy_results)
        elif "strategy_results" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_strategy_results, list):
            arg_strategy_results = pd.Series(arg_strategy_results)
        kwargs["strategy_results"] = arg_strategy_results

        arg_benchmark_result = benchmark_result
        if "benchmark_result" in ["trades", "open_trades"] and isinstance(
            arg_benchmark_result, (list, dict)
        ):
            arg_benchmark_result = pd.DataFrame(arg_benchmark_result)
        elif "benchmark_result" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_benchmark_result, list):
            arg_benchmark_result = pd.Series(arg_benchmark_result)
        kwargs["benchmark_result"] = arg_benchmark_result

        arg_metric_func = metric_func
        if "metric_func" in ["trades", "open_trades"] and isinstance(
            arg_metric_func, (list, dict)
        ):
            arg_metric_func = pd.DataFrame(arg_metric_func)
        elif "metric_func" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_metric_func, list):
            arg_metric_func = pd.Series(arg_metric_func)
        kwargs["metric_func"] = arg_metric_func

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

        res = _whites_reality_check_backtests_impl(**kwargs)
        logger.info("Executed whites_reality_check_backtests tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "whites_reality_check_backtests",
            data={"whites_reality_check_backtests": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _permutation_test_backtest_impl(
    strategy_result: "BacktestResult", **kwargs
) -> dict[str, Any]:
    """AI Tool wrapper for _permutation_test_backtest_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_strategy_result = strategy_result
        if "strategy_result" in ["trades", "open_trades"] and isinstance(
            arg_strategy_result, (list, dict)
        ):
            arg_strategy_result = pd.DataFrame(arg_strategy_result)
        elif "strategy_result" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_strategy_result, list):
            arg_strategy_result = pd.Series(arg_strategy_result)
        kwargs["strategy_result"] = arg_strategy_result

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

        res = _permutation_test_backtest_impl(**kwargs)
        logger.info("Executed permutation_test_backtest tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "permutation_test_backtest",
            data={"permutation_test_backtest": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _bootstrap_confidence_intervals_backtest_impl(
    strategy_result: "BacktestResult", **kwargs
) -> dict[str, Any]:
    """AI Tool wrapper for _bootstrap_confidence_intervals_backtest_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_strategy_result = strategy_result
        if "strategy_result" in ["trades", "open_trades"] and isinstance(
            arg_strategy_result, (list, dict)
        ):
            arg_strategy_result = pd.DataFrame(arg_strategy_result)
        elif "strategy_result" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_strategy_result, list):
            arg_strategy_result = pd.Series(arg_strategy_result)
        kwargs["strategy_result"] = arg_strategy_result

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

        res = _bootstrap_confidence_intervals_backtest_impl(**kwargs)
        logger.info(
            "Executed bootstrap_confidence_intervals_backtest tool successfully."
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
            "bootstrap_confidence_intervals_backtest",
            data={"bootstrap_confidence_intervals_backtest": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _print_statistical_validation_report_impl(
    permutation_result: PermutationTestResult | None = None,
    bootstrap_results: list[BootstrapResult] | None = None,
    deflated_sharpe_result: tuple[float, float] | None = None,
    stability_result: dict[str, float] | None = None,
    whites_result: WhitesRealityCheckResult | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _print_statistical_validation_report_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_permutation_result = permutation_result
        if "permutation_result" in ["trades", "open_trades"] and isinstance(
            arg_permutation_result, (list, dict)
        ):
            arg_permutation_result = pd.DataFrame(arg_permutation_result)
        elif "permutation_result" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_permutation_result, list):
            arg_permutation_result = pd.Series(arg_permutation_result)
        kwargs["permutation_result"] = arg_permutation_result

        arg_bootstrap_results = bootstrap_results
        if "bootstrap_results" in ["trades", "open_trades"] and isinstance(
            arg_bootstrap_results, (list, dict)
        ):
            arg_bootstrap_results = pd.DataFrame(arg_bootstrap_results)
        elif "bootstrap_results" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_bootstrap_results, list):
            arg_bootstrap_results = pd.Series(arg_bootstrap_results)
        kwargs["bootstrap_results"] = arg_bootstrap_results

        arg_deflated_sharpe_result = deflated_sharpe_result
        if "deflated_sharpe_result" in ["trades", "open_trades"] and isinstance(
            arg_deflated_sharpe_result, (list, dict)
        ):
            arg_deflated_sharpe_result = pd.DataFrame(arg_deflated_sharpe_result)
        elif "deflated_sharpe_result" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_deflated_sharpe_result, list):
            arg_deflated_sharpe_result = pd.Series(arg_deflated_sharpe_result)
        kwargs["deflated_sharpe_result"] = arg_deflated_sharpe_result

        arg_stability_result = stability_result
        if "stability_result" in ["trades", "open_trades"] and isinstance(
            arg_stability_result, (list, dict)
        ):
            arg_stability_result = pd.DataFrame(arg_stability_result)
        elif "stability_result" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_stability_result, list):
            arg_stability_result = pd.Series(arg_stability_result)
        kwargs["stability_result"] = arg_stability_result

        arg_whites_result = whites_result
        if "whites_result" in ["trades", "open_trades"] and isinstance(
            arg_whites_result, (list, dict)
        ):
            arg_whites_result = pd.DataFrame(arg_whites_result)
        elif "whites_result" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_whites_result, list):
            arg_whites_result = pd.Series(arg_whites_result)
        kwargs["whites_result"] = arg_whites_result

        res = _print_statistical_validation_report_impl(**kwargs)
        logger.info("Executed print_statistical_validation_report tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "print_statistical_validation_report",
            data={"print_statistical_validation_report": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def whites_reality_check(
    strategy_returns: list[np.ndarray | pd.Series],
    benchmark_returns: np.ndarray | pd.Series,
    metric_func: Callable[[np.ndarray], float] | None = None,
    n_bootstrap: int = 1000,
    block_size: int = 1,
    significance_level: float = 0.05,
    seed: int | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _whites_reality_check_impl."""
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

        arg_metric_func = metric_func
        if "metric_func" in ["trades", "open_trades"] and isinstance(
            arg_metric_func, (list, dict)
        ):
            arg_metric_func = pd.DataFrame(arg_metric_func)
        elif "metric_func" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_metric_func, list):
            arg_metric_func = pd.Series(arg_metric_func)
        kwargs["metric_func"] = arg_metric_func

        arg_n_bootstrap = n_bootstrap
        if "n_bootstrap" in ["trades", "open_trades"] and isinstance(
            arg_n_bootstrap, (list, dict)
        ):
            arg_n_bootstrap = pd.DataFrame(arg_n_bootstrap)
        elif "n_bootstrap" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_n_bootstrap, list):
            arg_n_bootstrap = pd.Series(arg_n_bootstrap)
        kwargs["n_bootstrap"] = arg_n_bootstrap

        arg_block_size = block_size
        if "block_size" in ["trades", "open_trades"] and isinstance(
            arg_block_size, (list, dict)
        ):
            arg_block_size = pd.DataFrame(arg_block_size)
        elif "block_size" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_block_size, list):
            arg_block_size = pd.Series(arg_block_size)
        kwargs["block_size"] = arg_block_size

        arg_significance_level = significance_level
        if "significance_level" in ["trades", "open_trades"] and isinstance(
            arg_significance_level, (list, dict)
        ):
            arg_significance_level = pd.DataFrame(arg_significance_level)
        elif "significance_level" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_significance_level, list):
            arg_significance_level = pd.Series(arg_significance_level)
        kwargs["significance_level"] = arg_significance_level

        arg_seed = seed
        if "seed" in ["trades", "open_trades"] and isinstance(arg_seed, (list, dict)):
            arg_seed = pd.DataFrame(arg_seed)
        elif "seed" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_seed, list):
            arg_seed = pd.Series(arg_seed)
        kwargs["seed"] = arg_seed

        res = _whites_reality_check_impl(**kwargs)
        logger.info("Executed whites_reality_check tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "whites_reality_check", data={"whites_reality_check": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def permutation_test(
    returns: np.ndarray | pd.Series,
    metric_func: Callable[[np.ndarray], float] | None = None,
    method: Literal["shuffle", "sign_flip"] = "sign_flip",
    n_permutations: int = 1000,
    significance_level: float = 0.05,
    seed: int | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _permutation_test_impl."""
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

        arg_metric_func = metric_func
        if "metric_func" in ["trades", "open_trades"] and isinstance(
            arg_metric_func, (list, dict)
        ):
            arg_metric_func = pd.DataFrame(arg_metric_func)
        elif "metric_func" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_metric_func, list):
            arg_metric_func = pd.Series(arg_metric_func)
        kwargs["metric_func"] = arg_metric_func

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

        arg_n_permutations = n_permutations
        if "n_permutations" in ["trades", "open_trades"] and isinstance(
            arg_n_permutations, (list, dict)
        ):
            arg_n_permutations = pd.DataFrame(arg_n_permutations)
        elif "n_permutations" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_n_permutations, list):
            arg_n_permutations = pd.Series(arg_n_permutations)
        kwargs["n_permutations"] = arg_n_permutations

        arg_significance_level = significance_level
        if "significance_level" in ["trades", "open_trades"] and isinstance(
            arg_significance_level, (list, dict)
        ):
            arg_significance_level = pd.DataFrame(arg_significance_level)
        elif "significance_level" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_significance_level, list):
            arg_significance_level = pd.Series(arg_significance_level)
        kwargs["significance_level"] = arg_significance_level

        arg_seed = seed
        if "seed" in ["trades", "open_trades"] and isinstance(arg_seed, (list, dict)):
            arg_seed = pd.DataFrame(arg_seed)
        elif "seed" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_seed, list):
            arg_seed = pd.Series(arg_seed)
        kwargs["seed"] = arg_seed

        res = _permutation_test_impl(**kwargs)
        logger.info("Executed permutation_test tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "permutation_test", data={"permutation_test": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def bootstrap_confidence_intervals(
    returns: np.ndarray | pd.Series,
    metrics_dict: dict[str, Callable[[np.ndarray], float]] | None = None,
    n_bootstrap: int = 1000,
    block_size: int = 1,
    confidence_level: float = 0.95,
    periods_per_year: int = 252,
    seed: int | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _bootstrap_confidence_intervals_impl."""
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

        arg_metrics_dict = metrics_dict
        if "metrics_dict" in ["trades", "open_trades"] and isinstance(
            arg_metrics_dict, (list, dict)
        ):
            arg_metrics_dict = pd.DataFrame(arg_metrics_dict)
        elif "metrics_dict" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_metrics_dict, list):
            arg_metrics_dict = pd.Series(arg_metrics_dict)
        kwargs["metrics_dict"] = arg_metrics_dict

        arg_n_bootstrap = n_bootstrap
        if "n_bootstrap" in ["trades", "open_trades"] and isinstance(
            arg_n_bootstrap, (list, dict)
        ):
            arg_n_bootstrap = pd.DataFrame(arg_n_bootstrap)
        elif "n_bootstrap" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_n_bootstrap, list):
            arg_n_bootstrap = pd.Series(arg_n_bootstrap)
        kwargs["n_bootstrap"] = arg_n_bootstrap

        arg_block_size = block_size
        if "block_size" in ["trades", "open_trades"] and isinstance(
            arg_block_size, (list, dict)
        ):
            arg_block_size = pd.DataFrame(arg_block_size)
        elif "block_size" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_block_size, list):
            arg_block_size = pd.Series(arg_block_size)
        kwargs["block_size"] = arg_block_size

        arg_confidence_level = confidence_level
        if "confidence_level" in ["trades", "open_trades"] and isinstance(
            arg_confidence_level, (list, dict)
        ):
            arg_confidence_level = pd.DataFrame(arg_confidence_level)
        elif "confidence_level" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_confidence_level, list):
            arg_confidence_level = pd.Series(arg_confidence_level)
        kwargs["confidence_level"] = arg_confidence_level

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

        arg_seed = seed
        if "seed" in ["trades", "open_trades"] and isinstance(arg_seed, (list, dict)):
            arg_seed = pd.DataFrame(arg_seed)
        elif "seed" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_seed, list):
            arg_seed = pd.Series(arg_seed)
        kwargs["seed"] = arg_seed

        res = _bootstrap_confidence_intervals_impl(**kwargs)
        logger.info("Executed bootstrap_confidence_intervals tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "bootstrap_confidence_intervals",
            data={"bootstrap_confidence_intervals": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def deflated_sharpe_ratio(
    observed_sharpe: float,
    n_trials: int,
    n_observations: int,
    expected_sharpe: float = 0.0,
    skew: float = 0.0,
    kurt: float = 3.0,
) -> dict[str, Any]:
    """AI Tool wrapper for _deflated_sharpe_ratio_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_observed_sharpe = observed_sharpe
        if "observed_sharpe" in ["trades", "open_trades"] and isinstance(
            arg_observed_sharpe, (list, dict)
        ):
            arg_observed_sharpe = pd.DataFrame(arg_observed_sharpe)
        elif "observed_sharpe" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_observed_sharpe, list):
            arg_observed_sharpe = pd.Series(arg_observed_sharpe)
        kwargs["observed_sharpe"] = arg_observed_sharpe

        arg_n_trials = n_trials
        if "n_trials" in ["trades", "open_trades"] and isinstance(
            arg_n_trials, (list, dict)
        ):
            arg_n_trials = pd.DataFrame(arg_n_trials)
        elif "n_trials" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_n_trials, list):
            arg_n_trials = pd.Series(arg_n_trials)
        kwargs["n_trials"] = arg_n_trials

        arg_n_observations = n_observations
        if "n_observations" in ["trades", "open_trades"] and isinstance(
            arg_n_observations, (list, dict)
        ):
            arg_n_observations = pd.DataFrame(arg_n_observations)
        elif "n_observations" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_n_observations, list):
            arg_n_observations = pd.Series(arg_n_observations)
        kwargs["n_observations"] = arg_n_observations

        arg_expected_sharpe = expected_sharpe
        if "expected_sharpe" in ["trades", "open_trades"] and isinstance(
            arg_expected_sharpe, (list, dict)
        ):
            arg_expected_sharpe = pd.DataFrame(arg_expected_sharpe)
        elif "expected_sharpe" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_expected_sharpe, list):
            arg_expected_sharpe = pd.Series(arg_expected_sharpe)
        kwargs["expected_sharpe"] = arg_expected_sharpe

        arg_skew = skew
        if "skew" in ["trades", "open_trades"] and isinstance(arg_skew, (list, dict)):
            arg_skew = pd.DataFrame(arg_skew)
        elif "skew" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_skew, list):
            arg_skew = pd.Series(arg_skew)
        kwargs["skew"] = arg_skew

        arg_kurt = kurt
        if "kurt" in ["trades", "open_trades"] and isinstance(arg_kurt, (list, dict)):
            arg_kurt = pd.DataFrame(arg_kurt)
        elif "kurt" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_kurt, list):
            arg_kurt = pd.Series(arg_kurt)
        kwargs["kurt"] = arg_kurt

        res = _deflated_sharpe_ratio_impl(**kwargs)
        logger.info("Executed deflated_sharpe_ratio tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "deflated_sharpe_ratio", data={"deflated_sharpe_ratio": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def probability_of_backtest_overfitting(
    in_sample_scores: np.ndarray,
    out_of_sample_scores: np.ndarray,
) -> dict[str, Any]:
    """AI Tool wrapper for _probability_of_backtest_overfitting_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_in_sample_scores = in_sample_scores
        if "in_sample_scores" in ["trades", "open_trades"] and isinstance(
            arg_in_sample_scores, (list, dict)
        ):
            arg_in_sample_scores = pd.DataFrame(arg_in_sample_scores)
        elif "in_sample_scores" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_in_sample_scores, list):
            arg_in_sample_scores = pd.Series(arg_in_sample_scores)
        kwargs["in_sample_scores"] = arg_in_sample_scores

        arg_out_of_sample_scores = out_of_sample_scores
        if "out_of_sample_scores" in ["trades", "open_trades"] and isinstance(
            arg_out_of_sample_scores, (list, dict)
        ):
            arg_out_of_sample_scores = pd.DataFrame(arg_out_of_sample_scores)
        elif "out_of_sample_scores" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_out_of_sample_scores, list):
            arg_out_of_sample_scores = pd.Series(arg_out_of_sample_scores)
        kwargs["out_of_sample_scores"] = arg_out_of_sample_scores

        res = _probability_of_backtest_overfitting_impl(**kwargs)
        logger.info("Executed probability_of_backtest_overfitting tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "probability_of_backtest_overfitting",
            data={"probability_of_backtest_overfitting": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def walk_forward_degradation_score(
    train_scores: np.ndarray | pd.Series,
    test_scores: np.ndarray | pd.Series,
) -> dict[str, Any]:
    """AI Tool wrapper for _walk_forward_degradation_score_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_train_scores = train_scores
        if "train_scores" in ["trades", "open_trades"] and isinstance(
            arg_train_scores, (list, dict)
        ):
            arg_train_scores = pd.DataFrame(arg_train_scores)
        elif "train_scores" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_train_scores, list):
            arg_train_scores = pd.Series(arg_train_scores)
        kwargs["train_scores"] = arg_train_scores

        arg_test_scores = test_scores
        if "test_scores" in ["trades", "open_trades"] and isinstance(
            arg_test_scores, (list, dict)
        ):
            arg_test_scores = pd.DataFrame(arg_test_scores)
        elif "test_scores" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_test_scores, list):
            arg_test_scores = pd.Series(arg_test_scores)
        kwargs["test_scores"] = arg_test_scores

        res = _walk_forward_degradation_score_impl(**kwargs)
        logger.info("Executed walk_forward_degradation_score tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "walk_forward_degradation_score",
            data={"walk_forward_degradation_score": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def bootstrap_probability_above_threshold(
    returns: np.ndarray | pd.Series,
    metric_func: Callable[[np.ndarray], float],
    threshold: float,
    n_bootstrap: int = 1000,
    block_size: int = 1,
    seed: int | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _bootstrap_probability_above_threshold_impl."""
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

        arg_metric_func = metric_func
        if "metric_func" in ["trades", "open_trades"] and isinstance(
            arg_metric_func, (list, dict)
        ):
            arg_metric_func = pd.DataFrame(arg_metric_func)
        elif "metric_func" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_metric_func, list):
            arg_metric_func = pd.Series(arg_metric_func)
        kwargs["metric_func"] = arg_metric_func

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

        arg_n_bootstrap = n_bootstrap
        if "n_bootstrap" in ["trades", "open_trades"] and isinstance(
            arg_n_bootstrap, (list, dict)
        ):
            arg_n_bootstrap = pd.DataFrame(arg_n_bootstrap)
        elif "n_bootstrap" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_n_bootstrap, list):
            arg_n_bootstrap = pd.Series(arg_n_bootstrap)
        kwargs["n_bootstrap"] = arg_n_bootstrap

        arg_block_size = block_size
        if "block_size" in ["trades", "open_trades"] and isinstance(
            arg_block_size, (list, dict)
        ):
            arg_block_size = pd.DataFrame(arg_block_size)
        elif "block_size" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_block_size, list):
            arg_block_size = pd.Series(arg_block_size)
        kwargs["block_size"] = arg_block_size

        arg_seed = seed
        if "seed" in ["trades", "open_trades"] and isinstance(arg_seed, (list, dict)):
            arg_seed = pd.DataFrame(arg_seed)
        elif "seed" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_seed, list):
            arg_seed = pd.Series(arg_seed)
        kwargs["seed"] = arg_seed

        res = _bootstrap_probability_above_threshold_impl(**kwargs)
        logger.info("Executed bootstrap_probability_above_threshold tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "bootstrap_probability_above_threshold",
            data={"bootstrap_probability_above_threshold": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def bonferroni_correction(
    p_values: np.ndarray | list[float],
    alpha: float = 0.05,
) -> dict[str, Any]:
    """AI Tool wrapper for _bonferroni_correction_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_p_values = p_values
        if "p_values" in ["trades", "open_trades"] and isinstance(
            arg_p_values, (list, dict)
        ):
            arg_p_values = pd.DataFrame(arg_p_values)
        elif "p_values" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_p_values, list):
            arg_p_values = pd.Series(arg_p_values)
        kwargs["p_values"] = arg_p_values

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

        res = _bonferroni_correction_impl(**kwargs)
        logger.info("Executed bonferroni_correction tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "bonferroni_correction", data={"bonferroni_correction": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def benjamini_hochberg_correction(
    p_values: np.ndarray | list[float],
    alpha: float = 0.05,
) -> dict[str, Any]:
    """AI Tool wrapper for _benjamini_hochberg_correction_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_p_values = p_values
        if "p_values" in ["trades", "open_trades"] and isinstance(
            arg_p_values, (list, dict)
        ):
            arg_p_values = pd.DataFrame(arg_p_values)
        elif "p_values" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_p_values, list):
            arg_p_values = pd.Series(arg_p_values)
        kwargs["p_values"] = arg_p_values

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

        res = _benjamini_hochberg_correction_impl(**kwargs)
        logger.info("Executed benjamini_hochberg_correction tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "benjamini_hochberg_correction",
            data={"benjamini_hochberg_correction": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def sample_size_warning(
    n_observations: int, min_recommended: int = 100
) -> dict[str, Any]:
    """AI Tool wrapper for _sample_size_warning_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_n_observations = n_observations
        if "n_observations" in ["trades", "open_trades"] and isinstance(
            arg_n_observations, (list, dict)
        ):
            arg_n_observations = pd.DataFrame(arg_n_observations)
        elif "n_observations" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_n_observations, list):
            arg_n_observations = pd.Series(arg_n_observations)
        kwargs["n_observations"] = arg_n_observations

        arg_min_recommended = min_recommended
        if "min_recommended" in ["trades", "open_trades"] and isinstance(
            arg_min_recommended, (list, dict)
        ):
            arg_min_recommended = pd.DataFrame(arg_min_recommended)
        elif "min_recommended" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_min_recommended, list):
            arg_min_recommended = pd.Series(arg_min_recommended)
        kwargs["min_recommended"] = arg_min_recommended

        res = _sample_size_warning_impl(**kwargs)
        logger.info("Executed sample_size_warning tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "sample_size_warning", data={"sample_size_warning": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def stability_score(
    walk_forward_results: list[dict[str, Any]], metric_key: str = "sharpe_ratio"
) -> dict[str, Any]:
    """AI Tool wrapper for _stability_score_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_walk_forward_results = walk_forward_results
        if "walk_forward_results" in ["trades", "open_trades"] and isinstance(
            arg_walk_forward_results, (list, dict)
        ):
            arg_walk_forward_results = pd.DataFrame(arg_walk_forward_results)
        elif "walk_forward_results" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_walk_forward_results, list):
            arg_walk_forward_results = pd.Series(arg_walk_forward_results)
        kwargs["walk_forward_results"] = arg_walk_forward_results

        arg_metric_key = metric_key
        if "metric_key" in ["trades", "open_trades"] and isinstance(
            arg_metric_key, (list, dict)
        ):
            arg_metric_key = pd.DataFrame(arg_metric_key)
        elif "metric_key" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_metric_key, list):
            arg_metric_key = pd.Series(arg_metric_key)
        kwargs["metric_key"] = arg_metric_key

        res = _stability_score_impl(**kwargs)
        logger.info("Executed stability_score tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "stability_score", data={"stability_score": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def whites_reality_check_backtests(
    strategy_results: list["BacktestResult"],
    benchmark_result: "BacktestResult",
    metric_func: Callable[[np.ndarray], float] | None = None,
    **kwargs,
) -> dict[str, Any]:
    """AI Tool wrapper for _whites_reality_check_backtests_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_strategy_results = strategy_results
        if "strategy_results" in ["trades", "open_trades"] and isinstance(
            arg_strategy_results, (list, dict)
        ):
            arg_strategy_results = pd.DataFrame(arg_strategy_results)
        elif "strategy_results" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_strategy_results, list):
            arg_strategy_results = pd.Series(arg_strategy_results)
        kwargs["strategy_results"] = arg_strategy_results

        arg_benchmark_result = benchmark_result
        if "benchmark_result" in ["trades", "open_trades"] and isinstance(
            arg_benchmark_result, (list, dict)
        ):
            arg_benchmark_result = pd.DataFrame(arg_benchmark_result)
        elif "benchmark_result" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_benchmark_result, list):
            arg_benchmark_result = pd.Series(arg_benchmark_result)
        kwargs["benchmark_result"] = arg_benchmark_result

        arg_metric_func = metric_func
        if "metric_func" in ["trades", "open_trades"] and isinstance(
            arg_metric_func, (list, dict)
        ):
            arg_metric_func = pd.DataFrame(arg_metric_func)
        elif "metric_func" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_metric_func, list):
            arg_metric_func = pd.Series(arg_metric_func)
        kwargs["metric_func"] = arg_metric_func

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

        res = _whites_reality_check_backtests_impl(**kwargs)
        logger.info("Executed whites_reality_check_backtests tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "whites_reality_check_backtests",
            data={"whites_reality_check_backtests": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def permutation_test_backtest(
    strategy_result: "BacktestResult", **kwargs
) -> dict[str, Any]:
    """AI Tool wrapper for _permutation_test_backtest_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_strategy_result = strategy_result
        if "strategy_result" in ["trades", "open_trades"] and isinstance(
            arg_strategy_result, (list, dict)
        ):
            arg_strategy_result = pd.DataFrame(arg_strategy_result)
        elif "strategy_result" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_strategy_result, list):
            arg_strategy_result = pd.Series(arg_strategy_result)
        kwargs["strategy_result"] = arg_strategy_result

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

        res = _permutation_test_backtest_impl(**kwargs)
        logger.info("Executed permutation_test_backtest tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "permutation_test_backtest",
            data={"permutation_test_backtest": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def bootstrap_confidence_intervals_backtest(
    strategy_result: "BacktestResult", **kwargs
) -> dict[str, Any]:
    """AI Tool wrapper for _bootstrap_confidence_intervals_backtest_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_strategy_result = strategy_result
        if "strategy_result" in ["trades", "open_trades"] and isinstance(
            arg_strategy_result, (list, dict)
        ):
            arg_strategy_result = pd.DataFrame(arg_strategy_result)
        elif "strategy_result" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_strategy_result, list):
            arg_strategy_result = pd.Series(arg_strategy_result)
        kwargs["strategy_result"] = arg_strategy_result

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

        res = _bootstrap_confidence_intervals_backtest_impl(**kwargs)
        logger.info(
            "Executed bootstrap_confidence_intervals_backtest tool successfully."
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
            "bootstrap_confidence_intervals_backtest",
            data={"bootstrap_confidence_intervals_backtest": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def print_statistical_validation_report(
    permutation_result: PermutationTestResult | None = None,
    bootstrap_results: list[BootstrapResult] | None = None,
    deflated_sharpe_result: tuple[float, float] | None = None,
    stability_result: dict[str, float] | None = None,
    whites_result: WhitesRealityCheckResult | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _print_statistical_validation_report_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_permutation_result = permutation_result
        if "permutation_result" in ["trades", "open_trades"] and isinstance(
            arg_permutation_result, (list, dict)
        ):
            arg_permutation_result = pd.DataFrame(arg_permutation_result)
        elif "permutation_result" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_permutation_result, list):
            arg_permutation_result = pd.Series(arg_permutation_result)
        kwargs["permutation_result"] = arg_permutation_result

        arg_bootstrap_results = bootstrap_results
        if "bootstrap_results" in ["trades", "open_trades"] and isinstance(
            arg_bootstrap_results, (list, dict)
        ):
            arg_bootstrap_results = pd.DataFrame(arg_bootstrap_results)
        elif "bootstrap_results" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_bootstrap_results, list):
            arg_bootstrap_results = pd.Series(arg_bootstrap_results)
        kwargs["bootstrap_results"] = arg_bootstrap_results

        arg_deflated_sharpe_result = deflated_sharpe_result
        if "deflated_sharpe_result" in ["trades", "open_trades"] and isinstance(
            arg_deflated_sharpe_result, (list, dict)
        ):
            arg_deflated_sharpe_result = pd.DataFrame(arg_deflated_sharpe_result)
        elif "deflated_sharpe_result" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_deflated_sharpe_result, list):
            arg_deflated_sharpe_result = pd.Series(arg_deflated_sharpe_result)
        kwargs["deflated_sharpe_result"] = arg_deflated_sharpe_result

        arg_stability_result = stability_result
        if "stability_result" in ["trades", "open_trades"] and isinstance(
            arg_stability_result, (list, dict)
        ):
            arg_stability_result = pd.DataFrame(arg_stability_result)
        elif "stability_result" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_stability_result, list):
            arg_stability_result = pd.Series(arg_stability_result)
        kwargs["stability_result"] = arg_stability_result

        arg_whites_result = whites_result
        if "whites_result" in ["trades", "open_trades"] and isinstance(
            arg_whites_result, (list, dict)
        ):
            arg_whites_result = pd.DataFrame(arg_whites_result)
        elif "whites_result" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_whites_result, list):
            arg_whites_result = pd.Series(arg_whites_result)
        kwargs["whites_result"] = arg_whites_result

        res = _print_statistical_validation_report_impl(**kwargs)
        logger.info("Executed print_statistical_validation_report tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "print_statistical_validation_report",
            data={"print_statistical_validation_report": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}
