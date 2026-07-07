"""Workload limits configuration and enforcement for Analytics boundaries.

All calculations are stateless pure functions.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.utils.errors import ValidationError


@dataclass(frozen=True, slots=True)
class AnalyticsLimits:
    """Configured limits for analytics payloads and calculation sizes.

    Attributes:
        max_trades: Maximum trades allowed in request.
        max_equity_points: Maximum equity curve points allowed.
        max_benchmark_points: Maximum benchmark curve points allowed.
        max_portfolio_components: Maximum components in portfolio report.
        max_dashboard_points: Maximum points before downsampling is triggered.
        max_statistical_observations: Maximum resamples or observations.
    """

    max_trades: int = 10000
    max_equity_points: int = 100000
    max_benchmark_points: int = 100000
    max_portfolio_components: int = 100
    max_dashboard_points: int = 1000
    max_statistical_observations: int = 500000


@dataclass(frozen=True, slots=True)
class WorkloadShape:
    """Describes the counts/sizes of the current workload elements.

    Attributes:
        trades_count: Number of trades.
        equity_points_count: Number of equity points.
        benchmark_points_count: Number of benchmark points.
        portfolio_components_count: Number of portfolio strategies.
        dashboard_points_count: Number of dashboard points.
        statistical_observations_count: Number of resampled observations.
    """

    trades_count: int = 0
    equity_points_count: int = 0
    benchmark_points_count: int = 0
    portfolio_components_count: int = 0
    dashboard_points_count: int = 0
    statistical_observations_count: int = 0


def enforce_limits(
    shape: WorkloadShape,
    limits: AnalyticsLimits,
) -> None:
    """Verify shape boundaries against the limits configurations.

    Raises:
        ValidationError: If any shape dimension exceeds the limit.
    """
    if shape.trades_count > limits.max_trades:
        msg = f"Trades count {shape.trades_count} exceeds limit {limits.max_trades}."
        raise ValidationError(msg)
    if shape.equity_points_count > limits.max_equity_points:
        msg = (
            f"Equity points count {shape.equity_points_count} "
            f"exceeds limit {limits.max_equity_points}."
        )
        raise ValidationError(msg)
    if shape.benchmark_points_count > limits.max_benchmark_points:
        msg = (
            f"Benchmark points count {shape.benchmark_points_count} "
            f"exceeds limit {limits.max_benchmark_points}."
        )
        raise ValidationError(msg)
    if shape.portfolio_components_count > limits.max_portfolio_components:
        msg = (
            f"Portfolio components count {shape.portfolio_components_count} "
            f"exceeds limit {limits.max_portfolio_components}."
        )
        raise ValidationError(msg)
    if shape.dashboard_points_count > limits.max_dashboard_points:
        msg = (
            f"Dashboard points count {shape.dashboard_points_count} "
            f"exceeds limit {limits.max_dashboard_points}."
        )
        raise ValidationError(msg)
    if shape.statistical_observations_count > limits.max_statistical_observations:
        msg = (
            f"Statistical observations count {shape.statistical_observations_count} "
            f"exceeds limit {limits.max_statistical_observations}."
        )
        raise ValidationError(msg)
