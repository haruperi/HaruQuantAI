"""Public Analytics domain port.

All cross-domain consumers and standalone usage programs import Analytics
capabilities through this package root. Raw feature implementations remain
behind this stable response boundary.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Literal, cast

from app.services.analytics.adapters import (
    adapt_trading_result as _adapt_trading_result,
)
from app.services.analytics.adapters import (
    build_closed_trade_equity_curve as _build_closed_trade_equity_curve,
)
from app.services.analytics.contracts import (
    ANALYTICS_SCHEMA_VERSION,
    CONTRACT_COMPATIBILITY_MATRIX,
    EVIDENCE_CATALOG,
    METRIC_DEFINITION_CATALOG,
    AnalyticsError,
    AnalyticsRunConfig,
    AnalyticsValidationError,
    AnalyticsWarning,
    ClosedTrade,
    ClosedTradeLedger,
    DashboardPayload,
    Lineage,
    MetricEvidence,
    PerformanceReport,
    PortfolioAllocationEvidence,
    PortfolioPerformanceReport,
    PortfolioRebalanceMeasurementEvidence,
    PortfolioRebalanceMeasurementRequest,
    QualityFlag,
    ReportSection,
    ReproducibilityHashes,
    RiskFreeRateEvidence,
    SectionEvidence,
    StatisticalValidationConfig,
    TradingResult,
)
from app.services.analytics.contracts import (
    build_quality_flag as _build_quality_flag,
)
from app.services.analytics.contracts import (
    build_warning as _build_warning,
)
from app.services.analytics.contracts import (
    to_analytics_error_payload as _to_analytics_error_payload,
)
from app.services.analytics.contracts import (
    to_report_json_safe as _to_report_json_safe,
)
from app.services.analytics.contracts import (
    validate_contract_version as _validate_contract_version,
)
from app.services.analytics.contracts import (
    validate_metric_catalog as _validate_metric_catalog,
)
from app.services.analytics.contracts.factories import (
    create_analytics_run_config,
    create_analytics_value,
    create_closed_trade_ledger,
    create_portfolio_rebalance_measurement_request,
    create_risk_free_rate_evidence,
    create_statistical_validation_config,
    get_analytics_value_field,
    is_analytics_value,
)
from app.services.analytics.contracts.responses import run_analytics_operation
from app.services.analytics.dashboards import (
    build_dashboard_payload as _build_dashboard_payload,
)
from app.services.analytics.dashboards import (
    truncate_series as _truncate_series,
)
from app.services.analytics.metrics import (
    ANNUALIZATION_POLICY,
    BREAKEVEN_EPSILON,
    MIN_METRIC_SAMPLES,
)
from app.services.analytics.metrics import (
    align_benchmark_series as _align_benchmark_series,
)
from app.services.analytics.metrics import (
    calculate_benchmark_evidence as _calculate_benchmark_evidence,
)
from app.services.analytics.metrics import (
    calculate_cost_efficiency_evidence as _calculate_cost_efficiency_evidence,
)
from app.services.analytics.metrics import (
    calculate_distribution_evidence as _calculate_distribution_evidence,
)
from app.services.analytics.metrics import (
    calculate_drawdown_evidence as _calculate_drawdown_evidence,
)
from app.services.analytics.metrics import (
    calculate_grouped_evidence as _calculate_grouped_evidence,
)
from app.services.analytics.metrics import (
    calculate_ratio_evidence as _calculate_ratio_evidence,
)
from app.services.analytics.metrics import (
    calculate_return_evidence as _calculate_return_evidence,
)
from app.services.analytics.metrics import (
    calculate_risk_evidence as _calculate_risk_evidence,
)
from app.services.analytics.metrics import (
    calculate_trade_evidence as _calculate_trade_evidence,
)
from app.services.analytics.metrics import (
    run_statistical_validation as _run_statistical_validation,
)
from app.services.analytics.reports import (
    WorstDayDistribution,
)
from app.services.analytics.reports import (
    build_barrier_section as _build_barrier_section,
)
from app.services.analytics.reports import (
    build_performance_report as _build_performance_report,
)
from app.services.analytics.reports import (
    build_portfolio_allocation_evidence as _build_portfolio_allocation_evidence,
)
from app.services.analytics.reports import (
    build_portfolio_performance_report as _build_portfolio_performance_report,
)
from app.services.analytics.reports import (
    build_portfolio_rebalance_measurement as _build_portfolio_rebalance_measurement,
)
from app.services.analytics.reports import (
    build_worst_day_distribution as _build_worst_day_distribution,
)
from app.services.analytics.reports import (
    compare_performance_reports as _compare_performance_reports,
)
from app.services.analytics.reports import (
    compute_reproducibility_hashes as _compute_reproducibility_hashes,
)
from app.services.analytics.reports import (
    serialize_report as _serialize_report,
)

type StandardResponse[T] = Any
RiskLevel = Literal["none", "low", "medium", "high", "critical"]

if TYPE_CHECKING:
    MarketDataset = Any


def get_analytics_schema_version() -> str:
    """Return the supported Analytics schema version."""
    return ANALYTICS_SCHEMA_VERSION


def get_annualization_policy() -> Mapping[str, object]:
    """Return the immutable annualization policy."""
    return ANNUALIZATION_POLICY


def get_breakeven_epsilon() -> Decimal:
    """Return the Analytics breakeven comparison epsilon."""
    return BREAKEVEN_EPSILON


def get_contract_compatibility_matrix() -> Mapping[str, object]:
    """Return the supported cross-domain contract versions."""
    return CONTRACT_COMPATIBILITY_MATRIX


def get_evidence_catalog() -> Mapping[str, object]:
    """Return the immutable evidence catalogue."""
    return EVIDENCE_CATALOG


def get_metric_definition_catalog() -> Mapping[str, object]:
    """Return the immutable metric-definition catalogue."""
    return METRIC_DEFINITION_CATALOG


def get_min_metric_samples() -> Mapping[str, int]:
    """Return the minimum sample count for Analytics metrics."""
    return MIN_METRIC_SAMPLES


def validate_contract_version(
    contract: str,
    version: str,
    *,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[str]:
    """Validate one Analytics compatibility version.

    Returns:
        Standard response containing the accepted compatibility status.
    """
    return run_analytics_operation(
        operation="analytics.contracts.validate_contract_version",
        request_id=request_id,
        correlation_id=correlation_id,
        risk_level="none",
        raw=lambda: _validate_contract_version(contract, version),
    )


def validate_metric_catalog(
    catalog: Mapping[str, Mapping[str, object]],
    *,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[None]:
    """Validate the immutable Analytics metric catalogue.

    Returns:
        Standard response with ``data=None`` on successful validation.
    """
    return run_analytics_operation(
        operation="analytics.contracts.validate_metric_catalog",
        request_id=request_id,
        correlation_id=correlation_id,
        risk_level="none",
        raw=lambda: _validate_metric_catalog(catalog),
    )


def build_quality_flag(
    code: str,
    *,
    section: str,
    source_context: str,
    detail: Mapping[str, object],
    max_detail_bytes: int,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[QualityFlag]:
    """Build one catalog-backed Analytics quality flag.

    Returns:
        Standard response containing the quality flag in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.contracts.build_quality_flag",
        request_id=request_id,
        correlation_id=correlation_id,
        risk_level="none",
        raw=lambda: _build_quality_flag(
            code,
            section=section,
            source_context=source_context,
            detail=detail,
            max_detail_bytes=max_detail_bytes,
        ),
    )


def build_warning(
    code: str,
    *,
    section: str,
    source_context: str,
    detail: Mapping[str, object],
    max_detail_bytes: int,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[AnalyticsWarning]:
    """Build one catalog-backed Analytics warning.

    Returns:
        Standard response containing the warning in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.contracts.build_warning",
        request_id=request_id,
        correlation_id=correlation_id,
        risk_level="none",
        raw=lambda: _build_warning(
            code,
            section=section,
            source_context=source_context,
            detail=detail,
            max_detail_bytes=max_detail_bytes,
        ),
    )


def to_analytics_error_payload(
    error: Exception,
    *,
    max_detail_bytes: int,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[dict[str, object]]:
    """Convert one Analytics exception to bounded public error data.

    Returns:
        Standard response containing the bounded error mapping in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.contracts.to_analytics_error_payload",
        request_id=request_id,
        correlation_id=correlation_id,
        risk_level="none",
        raw=lambda: _to_analytics_error_payload(
            error, max_detail_bytes=max_detail_bytes
        ),
    )


def to_report_json_safe(
    value: object,
    *,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[object]:
    """Normalize one report value through the Utils JSON-safety contract.

    Returns:
        Standard response containing the JSON-safe value in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.contracts.to_report_json_safe",
        request_id=request_id,
        correlation_id=correlation_id,
        risk_level="none",
        raw=lambda: _to_report_json_safe(value),
    )


def build_closed_trade_equity_curve(
    trades: Sequence[ClosedTrade],
    *,
    initial_balance: Decimal,
    config: AnalyticsRunConfig,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[
    tuple[tuple[Mapping[str, object], ...], tuple[Mapping[str, object], ...]]
]:
    """Build deterministic closed-trade equity curves.

    Returns:
        Standard response containing the trade-indexed and daily curves in
        ``data``.
    """
    return run_analytics_operation(
        operation="analytics.adapters.build_closed_trade_equity_curve",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _build_closed_trade_equity_curve(
            trades, initial_balance=initial_balance, config=config
        ),
    )


def adapt_trading_result(
    source: Mapping[str, object],
    *,
    source_contract: str,
    initial_balance: Decimal,
    account_currency: str,
    config: AnalyticsRunConfig,
    benchmark: MarketDataset | None = None,
    fx_evidence: Mapping[str, object] | None = None,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[TradingResult]:
    """Adapt a producer-neutral closed-trade ledger.

    Returns:
        Standard response containing the canonical TradingResult in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.adapters.adapt_trading_result",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _adapt_trading_result(
            source,
            source_contract=source_contract,
            initial_balance=initial_balance,
            account_currency=account_currency,
            config=config,
            benchmark=benchmark,
            fx_evidence=fx_evidence,
        ),
    )


def align_benchmark_series(
    strategy: Sequence[Mapping[str, object]],
    benchmark: Sequence[Mapping[str, object]],
    *,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[tuple[tuple[float, ...], tuple[float, ...]]]:
    """Align strategy and benchmark return observations.

    Returns:
        Standard response containing the aligned strategy and benchmark series.
    """
    return run_analytics_operation(
        operation="analytics.metrics.align_benchmark_series",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _align_benchmark_series(strategy, benchmark),
    )


def calculate_benchmark_evidence(
    result: TradingResult,
    *,
    config: AnalyticsRunConfig,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[SectionEvidence]:
    """Calculate catalog-approved benchmark evidence.

    Returns:
        Standard response containing benchmark section evidence in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.metrics.calculate_benchmark_evidence",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _calculate_benchmark_evidence(result, config=config),
    )


def calculate_cost_efficiency_evidence(
    result: TradingResult,
    *,
    config: AnalyticsRunConfig,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[SectionEvidence]:
    """Calculate catalog-approved cost and efficiency evidence.

    Returns:
        Standard response containing cost-efficiency evidence in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.metrics.calculate_cost_efficiency_evidence",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _calculate_cost_efficiency_evidence(result, config=config),
    )


def calculate_distribution_evidence(
    values: Sequence[float],
    *,
    config: AnalyticsRunConfig,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[SectionEvidence]:
    """Calculate catalog-approved distribution evidence.

    Returns:
        Standard response containing distribution evidence in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.metrics.calculate_distribution_evidence",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _calculate_distribution_evidence(values, config=config),
    )


def calculate_drawdown_evidence(
    result: TradingResult,
    *,
    config: AnalyticsRunConfig,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[SectionEvidence]:
    """Calculate closed-trade drawdown evidence.

    Returns:
        Standard response containing drawdown evidence in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.metrics.calculate_drawdown_evidence",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _calculate_drawdown_evidence(result, config=config),
    )


def calculate_grouped_evidence(
    result: TradingResult,
    *,
    config: AnalyticsRunConfig,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[tuple[SectionEvidence, ...]]:
    """Calculate all catalog-approved Analytics evidence groups.

    Returns:
        Standard response containing ordered section evidence in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.metrics.calculate_grouped_evidence",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _calculate_grouped_evidence(result, config=config),
    )


def calculate_ratio_evidence(
    result: TradingResult,
    returns: Sequence[float],
    *,
    config: AnalyticsRunConfig,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[SectionEvidence]:
    """Calculate catalog-approved ratio evidence.

    Returns:
        Standard response containing ratio evidence in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.metrics.calculate_ratio_evidence",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _calculate_ratio_evidence(result, returns, config=config),
    )


def calculate_return_evidence(
    result: TradingResult,
    *,
    config: AnalyticsRunConfig,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[SectionEvidence]:
    """Calculate catalog-approved return evidence.

    Returns:
        Standard response containing return evidence in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.metrics.calculate_return_evidence",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _calculate_return_evidence(result, config=config),
    )


def calculate_risk_evidence(
    daily_returns: Sequence[float],
    *,
    config: AnalyticsRunConfig,
    confidence: float = 0.95,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[SectionEvidence]:
    """Calculate catalog-approved risk evidence.

    Returns:
        Standard response containing risk evidence in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.metrics.calculate_risk_evidence",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _calculate_risk_evidence(
            daily_returns, config=config, confidence=confidence
        ),
    )


def calculate_trade_evidence(
    result: TradingResult,
    *,
    config: AnalyticsRunConfig,
    source_context: str = "all",
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[SectionEvidence]:
    """Calculate catalog-approved closed-trade evidence.

    Returns:
        Standard response containing trade evidence in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.metrics.calculate_trade_evidence",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _calculate_trade_evidence(
            result, config=config, source_context=source_context
        ),
    )


def run_statistical_validation(
    values: Sequence[float],
    *,
    config: AnalyticsRunConfig,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[SectionEvidence]:
    """Run bounded seeded statistical validation.

    Returns:
        Standard response containing statistical evidence in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.metrics.run_statistical_validation",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _run_statistical_validation(values, config=config),
    )


def build_performance_report(
    source: Mapping[str, object],
    *,
    source_contract: str,
    request_id: str,
    correlation_id: str,
    created_at: datetime,
    initial_balance: Decimal,
    account_currency: str,
    config: AnalyticsRunConfig,
    benchmark: MarketDataset | None = None,
    fx_evidence: Mapping[str, object] | None = None,
    diagnostic_partial_mode: bool = False,
) -> StandardResponse[PerformanceReport]:
    """Build one canonical Analytics performance report.

    Returns:
        Standard response containing the PerformanceReport in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.reports.build_performance_report",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _build_performance_report(
            source,
            source_contract=source_contract,
            request_id=request_id,
            correlation_id=correlation_id,
            created_at=created_at,
            initial_balance=initial_balance,
            account_currency=account_currency,
            config=config,
            benchmark=benchmark,
            fx_evidence=fx_evidence,
            diagnostic_partial_mode=diagnostic_partial_mode,
        ),
    )


def build_portfolio_allocation_evidence(
    reports: Sequence[PerformanceReport],
    *,
    base_currency: str,
    fx_evidence: Mapping[str, object] | None,
    config: AnalyticsRunConfig,
    portfolio_simulation_result: Mapping[str, object],
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[PortfolioAllocationEvidence]:
    """Build non-binding portfolio allocation evidence.

    Returns:
        Standard response containing allocation evidence in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.reports.build_portfolio_allocation_evidence",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _build_portfolio_allocation_evidence(
            reports,
            base_currency=base_currency,
            fx_evidence=fx_evidence,
            config=config,
            portfolio_simulation_result=portfolio_simulation_result,
        ),
    )


def build_portfolio_performance_report(
    reports: Sequence[PerformanceReport],
    *,
    base_currency: str,
    fx_evidence: Mapping[str, object] | None,
    config: AnalyticsRunConfig,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[PortfolioPerformanceReport]:
    """Build a currency-safe internal portfolio performance report.

    Returns:
        Standard response containing the portfolio report in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.reports.build_portfolio_performance_report",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _build_portfolio_performance_report(
            reports,
            base_currency=base_currency,
            fx_evidence=fx_evidence,
            config=config,
        ),
    )


def build_portfolio_rebalance_measurement(
    request: PortfolioRebalanceMeasurementRequest,
    *,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[PortfolioRebalanceMeasurementEvidence]:
    """Measure reconciled portfolio rebalance facts without execution authority.

    Returns:
        Standard response containing measurement evidence in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.reports.build_portfolio_rebalance_measurement",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _build_portfolio_rebalance_measurement(request),
    )


def compare_performance_reports(
    reference: PerformanceReport,
    candidate: PerformanceReport,
    *,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[SectionEvidence]:
    """Compare compatible reports using actual common metrics.

    Returns:
        Standard response containing comparison evidence in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.reports.compare_performance_reports",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _compare_performance_reports(reference, candidate),
    )


def compute_reproducibility_hashes(
    result: TradingResult,
    report: PerformanceReport | None = None,
    *,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[ReproducibilityHashes]:
    """Compute deterministic Analytics reproducibility hashes.

    Returns:
        Standard response containing reproducibility hashes in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.reports.compute_reproducibility_hashes",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _compute_reproducibility_hashes(result, report),
    )


def serialize_report(
    report: PerformanceReport,
    *,
    format_name: str,
    config: AnalyticsRunConfig,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[str]:
    """Serialize a validated report without writing a file.

    Returns:
        Standard response containing the exact serialized string in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.reports.serialize_report",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _serialize_report(report, format_name=format_name, config=config),
    )


def build_dashboard_payload(
    report: PerformanceReport,
    *,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[DashboardPayload]:
    """Project a validated report into a bounded dashboard payload.

    Returns:
        Standard response containing the dashboard payload in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.dashboards.build_dashboard_payload",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _build_dashboard_payload(report),
    )


def _truncate_transform(
    result: tuple[tuple[Mapping[str, object], ...], Mapping[str, object]],
) -> tuple[tuple[Mapping[str, object], ...], Mapping[str, object]]:
    """Place the truncated series in data and its evidence in extensions.

    Returns:
        The series and its response-extension metadata.
    """
    points, metadata = result
    return points, {"truncation": metadata}


def build_worst_day_distribution(
    ledger: ClosedTradeLedger | TradingResult,
    *,
    percentiles: Sequence[Decimal],
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[object]:
    """Build worst-day distribution evidence from an Analytics ledger.

    Returns:
        Standard response containing the calculated distribution.
    """
    return run_analytics_operation(
        operation="analytics.reports.build_worst_day_distribution",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _build_worst_day_distribution(ledger, percentiles=percentiles),
    )


def build_barrier_section(
    first_passage: object | None,
    joint: object | None,
    worst_day: WorstDayDistribution | None,
    *,
    mandate_version: str,
    mode_sensitivity: Mapping[object, object] | None = None,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[object]:
    """Build barrier evidence when verified first-passage inputs are supplied.

    Returns:
        Standard response containing the barrier report section.
    """
    return run_analytics_operation(
        operation="analytics.reports.build_barrier_section",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _build_barrier_section(
            cast("Any", first_passage),
            cast("Any", joint),
            worst_day,
            mandate_version=mandate_version,
            mode_sensitivity=cast("Any", mode_sensitivity),
        ),
    )


def truncate_series(
    points: Sequence[Mapping[str, object]],
    *,
    max_points: int,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[tuple[Mapping[str, object], ...]]:
    """Deterministically bound a dashboard series.

    Returns:
        Standard response containing the truncated series in ``data``.
    """
    return run_analytics_operation(
        operation="analytics.dashboards.truncate_series",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _truncate_series(points, max_points=max_points),
        transform=_truncate_transform,
    )


__all__: tuple[str, ...] = (
    "AnalyticsError",
    "AnalyticsValidationError",
    "Lineage",
    "MetricEvidence",
    "ReportSection",
    "RiskFreeRateEvidence",
    "StatisticalValidationConfig",
    "adapt_trading_result",
    "align_benchmark_series",
    "build_barrier_section",
    "build_closed_trade_equity_curve",
    "build_dashboard_payload",
    "build_performance_report",
    "build_portfolio_allocation_evidence",
    "build_portfolio_performance_report",
    "build_portfolio_rebalance_measurement",
    "build_quality_flag",
    "build_warning",
    "build_worst_day_distribution",
    "calculate_benchmark_evidence",
    "calculate_cost_efficiency_evidence",
    "calculate_distribution_evidence",
    "calculate_drawdown_evidence",
    "calculate_grouped_evidence",
    "calculate_ratio_evidence",
    "calculate_return_evidence",
    "calculate_risk_evidence",
    "calculate_trade_evidence",
    "compare_performance_reports",
    "compute_reproducibility_hashes",
    "create_analytics_run_config",
    "create_analytics_value",
    "create_closed_trade_ledger",
    "create_portfolio_rebalance_measurement_request",
    "create_risk_free_rate_evidence",
    "create_statistical_validation_config",
    "get_analytics_schema_version",
    "get_analytics_value_field",
    "get_annualization_policy",
    "get_breakeven_epsilon",
    "get_contract_compatibility_matrix",
    "get_evidence_catalog",
    "get_metric_definition_catalog",
    "get_min_metric_samples",
    "is_analytics_value",
    "run_statistical_validation",
    "serialize_report",
    "to_analytics_error_payload",
    "to_report_json_safe",
    "truncate_series",
    "validate_contract_version",
    "validate_metric_catalog",
)
