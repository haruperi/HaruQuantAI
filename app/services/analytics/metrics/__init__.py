"""Focused internal metric feature port for Analytics."""

from app.services.analytics.metrics.benchmarks import (
    align_benchmark_series,
    calculate_benchmark_evidence,
)
from app.services.analytics.metrics.cost_efficiency import (
    calculate_cost_efficiency_evidence,
)
from app.services.analytics.metrics.distributions import (
    calculate_distribution_evidence,
)
from app.services.analytics.metrics.drawdowns import calculate_drawdown_evidence
from app.services.analytics.metrics.groups import calculate_grouped_evidence
from app.services.analytics.metrics.ratios import calculate_ratio_evidence
from app.services.analytics.metrics.returns import calculate_return_evidence
from app.services.analytics.metrics.risk import calculate_risk_evidence
from app.services.analytics.metrics.statistics import run_statistical_validation
from app.services.analytics.metrics.trades import (
    ANNUALIZATION_POLICY,
    BREAKEVEN_EPSILON,
    MIN_METRIC_SAMPLES,
    calculate_trade_evidence,
)

__all__ = (
    "ANNUALIZATION_POLICY",
    "BREAKEVEN_EPSILON",
    "MIN_METRIC_SAMPLES",
    "align_benchmark_series",
    "calculate_benchmark_evidence",
    "calculate_cost_efficiency_evidence",
    "calculate_distribution_evidence",
    "calculate_drawdown_evidence",
    "calculate_grouped_evidence",
    "calculate_ratio_evidence",
    "calculate_return_evidence",
    "calculate_risk_evidence",
    "calculate_trade_evidence",
    "run_statistical_validation",
)
