"""Statistical analysis package for Analytics.

Exposes distributions profiling, multiple hypothesis testing corrections,
and seeded bootstrap/permutation tools.
"""

from __future__ import annotations

from app.services.analytics.statistics.distributions import (
    calculate_distribution_metrics,
    detect_outliers,
    distribution_fit_quality,
    fat_tail_score,
    fit_distribution,
    higher_moments,
    histogram_data,
    jarque_bera_test,
    kurtosis,
    outlier_ratio,
    percentile_summary,
    qq_plot_data,
    r_multiple_distribution,
    return_distribution,
    sample_size_warning,
    shapiro_wilk_test,
    skewness,
    tail_ratio,
    upside_downside_summary,
)
from app.services.analytics.statistics.multiple_testing import (
    benjamini_hochberg_correction,
    bonferroni_correction,
    deflated_sharpe_ratio,
    probability_of_backtest_overfitting,
    stability_score,
    walk_forward_degradation_score,
    whites_reality_check,
    whites_reality_check_backtests,
)
from app.services.analytics.statistics.resampling import (
    bootstrap_confidence_intervals,
    bootstrap_confidence_intervals_backtest,
    bootstrap_probability_above_threshold,
    permutation_test,
    permutation_test_backtest,
)

__all__ = [
    "benjamini_hochberg_correction",
    "bonferroni_correction",
    "bootstrap_confidence_intervals",
    "bootstrap_confidence_intervals_backtest",
    "bootstrap_probability_above_threshold",
    "calculate_distribution_metrics",
    "deflated_sharpe_ratio",
    "detect_outliers",
    "distribution_fit_quality",
    "fat_tail_score",
    "fit_distribution",
    "higher_moments",
    "histogram_data",
    "jarque_bera_test",
    "kurtosis",
    "outlier_ratio",
    "percentile_summary",
    "permutation_test",
    "permutation_test_backtest",
    "probability_of_backtest_overfitting",
    "qq_plot_data",
    "r_multiple_distribution",
    "return_distribution",
    "sample_size_warning",
    "shapiro_wilk_test",
    "skewness",
    "stability_score",
    "tail_ratio",
    "upside_downside_summary",
    "walk_forward_degradation_score",
    "whites_reality_check",
    "whites_reality_check_backtests",
]
