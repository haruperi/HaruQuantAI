# ruff: noqa: F401, F403, I001
"""Analytics service entry point.

Exposes the official AI tools, metric calculation kernels, and adapters
for the HaruQuantAI analytics service.
"""

from __future__ import annotations

# 1. Adapters
from app.services.analytics.adapters import (
    BacktestResult,
    LiveTradingResult,
    PaperTradingResult,
    TradingResult,
    TradingResultAdapter,
)

# 2. Benchmarks
from app.services.analytics.benchmarks import (
    alpha,
    batting_average,
    beta,
    calculate_benchmark_metrics,
    information_ratio,
    r_squared,
    tracking_error,
    up_down_capture,
)

# 3. Boundaries
from app.services.analytics.boundaries import (
    AnalyticsError,
    AnalyticsLimits,
    RedactionPolicy,
    WorkloadShape,
    enforce_limits,
    error_envelope,
    float64,
    redact,
    request_id,
    success_envelope,
    validate_request,
)

# 4. Contracts
from app.services.analytics.contracts import (
    METRIC_DEFINITION_CATALOG,
    OFFICIAL_ANALYTICS_TOOL_CATALOG,
    SCHEMA_COMPATIBILITY_MATRIX,
    AnalyticsConfig,
    AnalyticsMetadata,
    AnalyticsRequest,
    AnalyticsResult,
    MetricConfig,
    MetricDefinition,
    MetricDefinitionCatalog,
    MetricResult,
    ToolEnvelope,
    validate_metric_catalog,
)

# 5. Dashboards
from app.services.analytics.dashboards import (
    build_overview_payload,
    truncate_series,
)

# 6. Equity
# 6. Equity & Returns raw helpers (from metrics/equity.py)
from app.services.analytics.metrics.equity import (
    annual_returns,
    annualized_return,
    avg_monthly_return,
    benchmark_returns,
    best_return,
    buy_and_hold_return,
    calculate_equity_metrics,
    calculate_return_metrics,
    daily_returns,
    downside_return_volatility,
    geometric_mean_return,
    log_returns_series,
    monthly_return_stddev,
    monthly_returns,
    return_kurtosis,
    return_skewness,
    return_volatility,
    returns_series,
    total_return_usd,
    weekly_returns,
    worst_return,
)

# 7. Drawdown raw helpers (from metrics/drawdown.py)
from app.services.analytics.metrics.drawdown import (
    avg_underwater_drawdown_percent,
    calculate_drawdown_metrics,
    drawdown_duration_series,
    drawdown_series,
    max_drawdown_duration_from_equity,
    max_strategy_drawdown_date,
    relative_drawdown_series,
)

# 8. PnL raw helpers (from metrics/pnl.py)
from app.services.analytics.metrics.pnl import (
    buy_and_hold_cagr,
    cagr,
    compound_monthly_growth_rate,
    return_on_initial_capital as return_on_initial_capital,
    total_return as total_return,
)

# 9. Metrics (V2 Submodules wildcard)
from app.services.analytics.metrics import *

# Re-import overrides after wildcard to preserve V1 package-level signatures

# 8. Reports
from app.services.analytics.reports import (
    AnalyticsReport,
    PortfolioAnalyticsReport,
    build_analytics_report,
    build_backtest_report,
    build_portfolio_analytics_report,
    calculate_prop_firm_compliance,
    calculate_statistical_validation,
    compare_analytics_reports,
    format_summary_as_rows,
)

# 9. Scorecards
from app.services.analytics.scorecards import (
    ScorecardResult,
    ScorecardRule,
    evaluate_strategy_quality,
)

# 10. Statistics
from app.services.analytics.statistics import (
    benjamini_hochberg_correction,
    bonferroni_correction,
    bootstrap_confidence_intervals,
    bootstrap_confidence_intervals_backtest,
    bootstrap_probability_above_threshold,
    calculate_distribution_metrics,
    deflated_sharpe_ratio,
    detect_outliers,
    distribution_fit_quality,
    fit_distribution,
    higher_moments,
    histogram_data,
    outlier_ratio,
    qq_plot_data,
    r_multiple_distribution,
    sample_size_warning,
    shapiro_wilk_test,
    stability_score,
    whites_reality_check,
    whites_reality_check_backtests,
)
