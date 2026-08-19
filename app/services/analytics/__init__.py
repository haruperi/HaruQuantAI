"""Public Analytics domain port.

All cross-domain consumers and standalone usage programs import Analytics
capabilities through this package root. Raw feature implementations remain
behind this stable response boundary.
"""

from __future__ import annotations

import typing
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal, cast

# Explicit imports keep type checking exact; runtime stays lazy.
if typing.TYPE_CHECKING:
    from app.services.analytics.contracts import (
        AnalyticsRunConfig,
        AnalyticsWarning,
        ClosedTrade,
        ClosedTradeLedger,
        DashboardPayload,
        PerformanceReport,
        PortfolioAllocationEvidence,
        PortfolioPerformanceReport,
        PortfolioRebalanceMeasurementEvidence,
        PortfolioRebalanceMeasurementRequest,
        QualityFlag,
        ReproducibilityHashes,
        SectionEvidence,
        TradingResult,
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
    from app.services.analytics.dashboards.snapshots import (
        get_analytics_dashboard_snapshot,
    )
    from app.services.analytics.migrations import (
        get_analytics_migrations,
        run_analytics_migrations,
    )
    from app.services.analytics.reports import WorstDayDistribution

# Public export name to the module and attribute that owns it. Wrapper
# functions below import their own collaborators on first call.
_EXPORTS: dict[str, tuple[str, str]] = {
    "ANALYTICS_SCHEMA_VERSION": (
        "app.services.analytics.contracts",
        "ANALYTICS_SCHEMA_VERSION",
    ),
    "ANNUALIZATION_POLICY": ("app.services.analytics.metrics", "ANNUALIZATION_POLICY"),
    "AnalyticsError": ("app.services.analytics.contracts", "AnalyticsError"),
    "AnalyticsRunConfig": ("app.services.analytics.contracts", "AnalyticsRunConfig"),
    "AnalyticsValidationError": (
        "app.services.analytics.contracts",
        "AnalyticsValidationError",
    ),
    "AnalyticsWarning": ("app.services.analytics.contracts", "AnalyticsWarning"),
    "BREAKEVEN_EPSILON": ("app.services.analytics.metrics", "BREAKEVEN_EPSILON"),
    "CONTRACT_COMPATIBILITY_MATRIX": (
        "app.services.analytics.contracts",
        "CONTRACT_COMPATIBILITY_MATRIX",
    ),
    "ClosedTrade": ("app.services.analytics.contracts", "ClosedTrade"),
    "ClosedTradeLedger": ("app.services.analytics.contracts", "ClosedTradeLedger"),
    "DashboardPayload": ("app.services.analytics.contracts", "DashboardPayload"),
    "EVIDENCE_CATALOG": ("app.services.analytics.contracts", "EVIDENCE_CATALOG"),
    "Lineage": ("app.services.analytics.contracts", "Lineage"),
    "METRIC_DEFINITION_CATALOG": (
        "app.services.analytics.contracts",
        "METRIC_DEFINITION_CATALOG",
    ),
    "MIN_METRIC_SAMPLES": ("app.services.analytics.metrics", "MIN_METRIC_SAMPLES"),
    "MetricEvidence": ("app.services.analytics.contracts", "MetricEvidence"),
    "PerformanceReport": ("app.services.analytics.contracts", "PerformanceReport"),
    "PortfolioAllocationEvidence": (
        "app.services.analytics.contracts",
        "PortfolioAllocationEvidence",
    ),
    "PortfolioPerformanceReport": (
        "app.services.analytics.contracts",
        "PortfolioPerformanceReport",
    ),
    "PortfolioRebalanceMeasurementEvidence": (
        "app.services.analytics.contracts",
        "PortfolioRebalanceMeasurementEvidence",
    ),
    "PortfolioRebalanceMeasurementRequest": (
        "app.services.analytics.contracts",
        "PortfolioRebalanceMeasurementRequest",
    ),
    "QualityFlag": ("app.services.analytics.contracts", "QualityFlag"),
    "ReportSection": ("app.services.analytics.contracts", "ReportSection"),
    "ReproducibilityHashes": (
        "app.services.analytics.contracts",
        "ReproducibilityHashes",
    ),
    "RiskFreeRateEvidence": (
        "app.services.analytics.contracts",
        "RiskFreeRateEvidence",
    ),
    "SectionEvidence": ("app.services.analytics.contracts", "SectionEvidence"),
    "StatisticalValidationConfig": (
        "app.services.analytics.contracts",
        "StatisticalValidationConfig",
    ),
    "TradingResult": ("app.services.analytics.contracts", "TradingResult"),
    "WorstDayDistribution": ("app.services.analytics.reports", "WorstDayDistribution"),
    "_adapt_trading_result": (
        "app.services.analytics.adapters",
        "adapt_trading_result",
    ),
    "_align_benchmark_series": (
        "app.services.analytics.metrics",
        "align_benchmark_series",
    ),
    "_analyze_emergency_response": (
        "app.services.analytics.emergency_response",
        "analyze_emergency_response",
    ),
    "_append_journal_entry": ("app.services.analytics.journal", "append_journal_entry"),
    "_assess_plan_adherence": (
        "app.services.analytics.behavior",
        "assess_plan_adherence",
    ),
    "_build_barrier_section": (
        "app.services.analytics.reports",
        "build_barrier_section",
    ),
    "_build_closed_trade_equity_curve": (
        "app.services.analytics.adapters",
        "build_closed_trade_equity_curve",
    ),
    "_build_dashboard_payload": (
        "app.services.analytics.dashboards",
        "build_dashboard_payload",
    ),
    "_build_performance_report": (
        "app.services.analytics.reports",
        "build_performance_report",
    ),
    "_build_period_tables": ("app.services.analytics.workbench", "build_period_tables"),
    "_build_portfolio_allocation_evidence": (
        "app.services.analytics.reports",
        "build_portfolio_allocation_evidence",
    ),
    "_build_portfolio_performance_report": (
        "app.services.analytics.reports",
        "build_portfolio_performance_report",
    ),
    "_build_portfolio_rebalance_measurement": (
        "app.services.analytics.reports",
        "build_portfolio_rebalance_measurement",
    ),
    "_build_process_score_mapping": (
        "app.services.analytics.scoring",
        "build_process_score_mapping",
    ),
    "_build_quality_flag": ("app.services.analytics.contracts", "build_quality_flag"),
    "_build_scoring_profile_mapping": (
        "app.services.analytics.scoring",
        "build_scoring_profile_mapping",
    ),
    "_build_session_score": ("app.services.analytics.scoring", "build_session_score"),
    "_build_warning": ("app.services.analytics.contracts", "build_warning"),
    "_build_workbench_payload": (
        "app.services.analytics.workbench",
        "build_workbench_payload",
    ),
    "_build_worst_day_distribution": (
        "app.services.analytics.reports",
        "build_worst_day_distribution",
    ),
    "_calculate_benchmark_evidence": (
        "app.services.analytics.metrics",
        "calculate_benchmark_evidence",
    ),
    "_calculate_cost_efficiency_evidence": (
        "app.services.analytics.metrics",
        "calculate_cost_efficiency_evidence",
    ),
    "_calculate_distribution_evidence": (
        "app.services.analytics.metrics",
        "calculate_distribution_evidence",
    ),
    "_calculate_drawdown_evidence": (
        "app.services.analytics.metrics",
        "calculate_drawdown_evidence",
    ),
    "_calculate_grouped_evidence": (
        "app.services.analytics.metrics",
        "calculate_grouped_evidence",
    ),
    "_calculate_ratio_evidence": (
        "app.services.analytics.metrics",
        "calculate_ratio_evidence",
    ),
    "_calculate_return_evidence": (
        "app.services.analytics.metrics",
        "calculate_return_evidence",
    ),
    "_calculate_risk_evidence": (
        "app.services.analytics.metrics",
        "calculate_risk_evidence",
    ),
    "_calculate_trade_evidence": (
        "app.services.analytics.metrics",
        "calculate_trade_evidence",
    ),
    "_compare_performance_reports": (
        "app.services.analytics.reports",
        "compare_performance_reports",
    ),
    "_compute_leaderboard_ranking": (
        "app.services.analytics.scoring",
        "compute_leaderboard_ranking",
    ),
    "_compute_reproducibility_hashes": (
        "app.services.analytics.reports",
        "compute_reproducibility_hashes",
    ),
    "_create_critical_failure_record": (
        "app.services.analytics.scoring",
        "create_critical_failure_record",
    ),
    "_create_process_scoring_profile": (
        "app.services.analytics.scoring",
        "create_process_scoring_profile",
    ),
    "_deserialize_performance_report": (
        "app.services.analytics.reports",
        "deserialize_performance_report",
    ),
    "_detect_behavior_patterns": (
        "app.services.analytics.behavior",
        "detect_behavior_patterns",
    ),
    "_evaluate_qualification": (
        "app.services.analytics.qualification",
        "evaluate_qualification",
    ),
    "_parse_process_score_mapping": (
        "app.services.analytics.scoring",
        "parse_process_score_mapping",
    ),
    "_parse_scoring_profile_mapping": (
        "app.services.analytics.scoring",
        "parse_scoring_profile_mapping",
    ),
    "_read_journal_entry": ("app.services.analytics.journal", "read_journal_entry"),
    "_run_statistical_validation": (
        "app.services.analytics.metrics",
        "run_statistical_validation",
    ),
    "_serialize_report": ("app.services.analytics.reports", "serialize_report"),
    "_to_analytics_error_payload": (
        "app.services.analytics.contracts",
        "to_analytics_error_payload",
    ),
    "_to_report_json_safe": ("app.services.analytics.contracts", "to_report_json_safe"),
    "_truncate_series": ("app.services.analytics.dashboards", "truncate_series"),
    "_validate_contract_version": (
        "app.services.analytics.contracts",
        "validate_contract_version",
    ),
    "_validate_metric_catalog": (
        "app.services.analytics.contracts",
        "validate_metric_catalog",
    ),
    "create_analytics_run_config": (
        "app.services.analytics.contracts.factories",
        "create_analytics_run_config",
    ),
    "create_analytics_value": (
        "app.services.analytics.contracts.factories",
        "create_analytics_value",
    ),
    "create_closed_trade_ledger": (
        "app.services.analytics.contracts.factories",
        "create_closed_trade_ledger",
    ),
    "create_portfolio_rebalance_measurement_request": (
        "app.services.analytics.contracts.factories",
        "create_portfolio_rebalance_measurement_request",
    ),
    "create_risk_free_rate_evidence": (
        "app.services.analytics.contracts.factories",
        "create_risk_free_rate_evidence",
    ),
    "create_statistical_validation_config": (
        "app.services.analytics.contracts.factories",
        "create_statistical_validation_config",
    ),
    "get_analytics_dashboard_snapshot": (
        "app.services.analytics.dashboards.snapshots",
        "get_analytics_dashboard_snapshot",
    ),
    "get_analytics_migrations": (
        "app.services.analytics.migrations",
        "get_analytics_migrations",
    ),
    "get_analytics_value_field": (
        "app.services.analytics.contracts.factories",
        "get_analytics_value_field",
    ),
    "is_analytics_value": (
        "app.services.analytics.contracts.factories",
        "is_analytics_value",
    ),
    "run_analytics_migrations": (
        "app.services.analytics.migrations",
        "run_analytics_migrations",
    ),
    "run_analytics_operation": (
        "app.services.analytics.contracts.responses",
        "run_analytics_operation",
    ),
}


def __getattr__(name: str) -> object:
    """Resolve one re-exported Analytics capability on first access.

    Args:
        name: Public export name.

    Returns:
        The resolved public function.

    Raises:
        AttributeError: If the name is not part of the public boundary.
    """
    target = _EXPORTS.get(name)
    if target is None:
        message = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(message)
    from importlib import import_module

    return getattr(import_module(target[0]), target[1])


type StandardResponse[T] = Any
RiskLevel = Literal["none", "low", "medium", "high", "critical"]

if typing.TYPE_CHECKING:
    MarketDataset = Any


def append_player_journal_entry(
    entry_id: str,
    *,
    session_id: str,
    plan_version: str,
    author_id: str,
    occurred_at: datetime,
    narrative: str,
    evidence_refs: Sequence[str] = (),
    replay_id: str | None = None,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[object]:
    """Append one immutable player journal entry.

    Args:
        entry_id: Unique journal entry identifier.
        session_id: Session id instance or value.
        plan_version: Plan version instance or value.
        author_id: Author id instance or value.
        occurred_at: Occurred at instance or value.
        narrative: Narrative instance or value.
        evidence_refs: Evidence refs instance or value.
        replay_id: Replay id instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing journal evidence.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.journal import (
        append_journal_entry as _append_journal_entry,
    )

    return run_analytics_operation(
        operation="analytics.journal.append",
        request_id=request_id,
        correlation_id=correlation_id,
        risk_level="none",
        raw=lambda: _append_journal_entry(
            entry_id,
            session_id=session_id,
            plan_version=plan_version,
            author_id=author_id,
            occurred_at=occurred_at,
            narrative=narrative,
            evidence_refs=evidence_refs,
            replay_id=replay_id,
        ),
    )


def read_player_journal_entry(
    entry_id: str, *, request_id: str | None = None, correlation_id: str | None = None
) -> StandardResponse[object]:
    """Read one player journal entry.

    Args:
        entry_id: Unique journal entry identifier.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing journal evidence or ``None``.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.journal import read_journal_entry as _read_journal_entry

    return run_analytics_operation(
        operation="analytics.journal.read",
        request_id=request_id,
        correlation_id=correlation_id,
        risk_level="none",
        raw=lambda: _read_journal_entry(entry_id),
    )


def assess_plan_adherence(
    planned_rules: Mapping[str, object],
    observed_actions: Sequence[Mapping[str, object]],
    *,
    plan_version: str,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[object]:
    """Assess evidence against an exact plan version.

    Args:
        planned_rules: Planned rules instance or value.
        observed_actions: Observed actions instance or value.
        plan_version: Plan version instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing adherence findings.
    """
    from app.services.analytics.behavior import (
        assess_plan_adherence as _assess_plan_adherence,
    )
    from app.services.analytics.contracts.responses import run_analytics_operation

    return run_analytics_operation(
        operation="analytics.behavior.adherence",
        request_id=request_id,
        correlation_id=correlation_id,
        risk_level="none",
        raw=lambda: _assess_plan_adherence(
            planned_rules, observed_actions, plan_version=plan_version
        ),
    )


def detect_behavior_patterns(
    actions: Sequence[Mapping[str, object]],
    *,
    threshold_version: str,
    thresholds: Mapping[str, int],
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[object]:
    """Run versioned evidence-only behavior detectors.

    Args:
        actions: Actions instance or value.
        threshold_version: Threshold version instance or value.
        thresholds: Thresholds instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing detector findings.
    """
    from app.services.analytics.behavior import (
        detect_behavior_patterns as _detect_behavior_patterns,
    )
    from app.services.analytics.contracts.responses import run_analytics_operation

    return run_analytics_operation(
        operation="analytics.behavior.detect",
        request_id=request_id,
        correlation_id=correlation_id,
        risk_level="none",
        raw=lambda: _detect_behavior_patterns(
            actions,
            threshold_version=threshold_version,
            thresholds=thresholds,
        ),
    )


def analyze_emergency_response(
    events: Sequence[Mapping[str, object]],
    *,
    required_sequence: Sequence[str],
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[object]:
    """Analyze Simulator emergency lifecycle evidence.

    Args:
        events: Events instance or value.
        required_sequence: Required sequence instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing emergency-response evidence.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.emergency_response import (
        analyze_emergency_response as _analyze_emergency_response,
    )

    return run_analytics_operation(
        operation="analytics.emergency.analyze",
        request_id=request_id,
        correlation_id=correlation_id,
        risk_level="none",
        raw=lambda: _analyze_emergency_response(
            events, required_sequence=required_sequence
        ),
    )


def evaluate_player_qualification(
    *,
    curriculum_version: str,
    completed_prerequisites: Sequence[str],
    required_prerequisites: Sequence[str],
    attempts: Sequence[Mapping[str, object]],
    valid_until: datetime,
    now: datetime,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[object]:
    """Evaluate player qualification and recurrent validity.

    Args:
        curriculum_version: Curriculum version instance or value.
        completed_prerequisites: Completed prerequisites instance or value.
        required_prerequisites: Required prerequisites instance or value.
        attempts: Attempts instance or value.
        valid_until: Valid until instance or value.
        now: Now instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing qualification evidence.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.qualification import (
        evaluate_qualification as _evaluate_qualification,
    )

    return run_analytics_operation(
        operation="analytics.qualification.evaluate",
        request_id=request_id,
        correlation_id=correlation_id,
        risk_level="none",
        raw=lambda: _evaluate_qualification(
            curriculum_version=curriculum_version,
            completed_prerequisites=completed_prerequisites,
            required_prerequisites=required_prerequisites,
            attempts=attempts,
            valid_until=valid_until,
            now=now,
        ),
    )


def get_analytics_schema_version() -> str:
    """Return the supported Analytics schema version."""
    from app.services.analytics.contracts import ANALYTICS_SCHEMA_VERSION

    return ANALYTICS_SCHEMA_VERSION


def get_annualization_policy() -> Mapping[str, object]:
    """Return the immutable annualization policy."""
    from app.services.analytics.metrics import ANNUALIZATION_POLICY

    return ANNUALIZATION_POLICY


def get_breakeven_epsilon() -> Decimal:
    """Return the Analytics breakeven comparison epsilon."""
    from app.services.analytics.metrics import BREAKEVEN_EPSILON

    return BREAKEVEN_EPSILON


def get_contract_compatibility_matrix() -> Mapping[str, object]:
    """Return the supported cross-domain contract versions."""
    from app.services.analytics.contracts import CONTRACT_COMPATIBILITY_MATRIX

    return CONTRACT_COMPATIBILITY_MATRIX


def get_evidence_catalog() -> Mapping[str, object]:
    """Return the immutable evidence catalogue."""
    from app.services.analytics.contracts import EVIDENCE_CATALOG

    return EVIDENCE_CATALOG


def get_metric_definition_catalog() -> Mapping[str, object]:
    """Return the immutable metric-definition catalogue."""
    from app.services.analytics.contracts import METRIC_DEFINITION_CATALOG

    return METRIC_DEFINITION_CATALOG


def get_min_metric_samples() -> Mapping[str, int]:
    """Return the minimum sample count for Analytics metrics."""
    from app.services.analytics.metrics import MIN_METRIC_SAMPLES

    return MIN_METRIC_SAMPLES


def validate_contract_version(
    contract: str,
    version: str,
    *,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[str]:
    """Validate one Analytics compatibility version.

    Args:
        contract: Contract instance or value.
        version: Version instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing the accepted compatibility status.
    """
    from app.services.analytics.contracts import (
        validate_contract_version as _validate_contract_version,
    )
    from app.services.analytics.contracts.responses import run_analytics_operation

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

    Args:
        catalog: Catalog instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response with ``data=None`` on successful validation.
    """
    from app.services.analytics.contracts import (
        validate_metric_catalog as _validate_metric_catalog,
    )
    from app.services.analytics.contracts.responses import run_analytics_operation

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

    Args:
        code: Code instance or value.
        section: Section instance or value.
        source_context: Source context instance or value.
        detail: Detail instance or value.
        max_detail_bytes: Max detail bytes instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing the quality flag in ``data``.
    """
    from app.services.analytics.contracts import (
        build_quality_flag as _build_quality_flag,
    )
    from app.services.analytics.contracts.responses import run_analytics_operation

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

    Args:
        code: Code instance or value.
        section: Section instance or value.
        source_context: Source context instance or value.
        detail: Detail instance or value.
        max_detail_bytes: Max detail bytes instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing the warning in ``data``.
    """
    from app.services.analytics.contracts import build_warning as _build_warning
    from app.services.analytics.contracts.responses import run_analytics_operation

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

    Args:
        error: Error instance or value.
        max_detail_bytes: Max detail bytes instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing the bounded error mapping in ``data``.
    """
    from app.services.analytics.contracts import (
        to_analytics_error_payload as _to_analytics_error_payload,
    )
    from app.services.analytics.contracts.responses import run_analytics_operation

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

    Args:
        value: Value instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing the JSON-safe value in ``data``.
    """
    from app.services.analytics.contracts import (
        to_report_json_safe as _to_report_json_safe,
    )
    from app.services.analytics.contracts.responses import run_analytics_operation

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

    Args:
        trades: Trades instance or value.
        initial_balance: Initial balance instance or value.
        config: Analytics configuration instance.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing the trade-indexed and daily curves in
        ``data``.
    """
    from app.services.analytics.adapters import (
        build_closed_trade_equity_curve as _build_closed_trade_equity_curve,
    )
    from app.services.analytics.contracts.responses import run_analytics_operation

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

    Args:
        source: Source instance or value.
        source_contract: Source contract instance or value.
        initial_balance: Initial balance instance or value.
        account_currency: Account currency instance or value.
        config: Analytics configuration instance.
        benchmark: Benchmark instance or value.
        fx_evidence: Fx evidence instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing the canonical TradingResult in ``data``.
    """
    from app.services.analytics.adapters import (
        adapt_trading_result as _adapt_trading_result,
    )
    from app.services.analytics.contracts.responses import run_analytics_operation

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

    Args:
        strategy: Strategy instance or value.
        benchmark: Benchmark instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing the aligned strategy and benchmark series.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.metrics import (
        align_benchmark_series as _align_benchmark_series,
    )

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

    Args:
        result: Source trading result or payload object.
        config: Analytics configuration instance.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing benchmark section evidence in ``data``.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.metrics import (
        calculate_benchmark_evidence as _calculate_benchmark_evidence,
    )

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

    Args:
        result: Source trading result or payload object.
        config: Analytics configuration instance.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing cost-efficiency evidence in ``data``.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.metrics import (
        calculate_cost_efficiency_evidence as _calculate_cost_efficiency_evidence,
    )

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

    Args:
        values: Values instance or value.
        config: Analytics configuration instance.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing distribution evidence in ``data``.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.metrics import (
        calculate_distribution_evidence as _calculate_distribution_evidence,
    )

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

    Args:
        result: Source trading result or payload object.
        config: Analytics configuration instance.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing drawdown evidence in ``data``.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.metrics import (
        calculate_drawdown_evidence as _calculate_drawdown_evidence,
    )

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

    Args:
        result: Source trading result or payload object.
        config: Analytics configuration instance.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing ordered section evidence in ``data``.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.metrics import (
        calculate_grouped_evidence as _calculate_grouped_evidence,
    )

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

    Args:
        result: Source trading result or payload object.
        returns: Returns instance or value.
        config: Analytics configuration instance.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing ratio evidence in ``data``.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.metrics import (
        calculate_ratio_evidence as _calculate_ratio_evidence,
    )

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

    Args:
        result: Source trading result or payload object.
        config: Analytics configuration instance.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing return evidence in ``data``.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.metrics import (
        calculate_return_evidence as _calculate_return_evidence,
    )

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

    Args:
        daily_returns: Daily returns instance or value.
        config: Analytics configuration instance.
        confidence: Confidence instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing risk evidence in ``data``.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.metrics import (
        calculate_risk_evidence as _calculate_risk_evidence,
    )

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

    Args:
        result: Source trading result or payload object.
        config: Analytics configuration instance.
        source_context: Source context instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing trade evidence in ``data``.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.metrics import (
        calculate_trade_evidence as _calculate_trade_evidence,
    )

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

    Args:
        values: Values instance or value.
        config: Analytics configuration instance.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing statistical evidence in ``data``.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.metrics import (
        run_statistical_validation as _run_statistical_validation,
    )

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

    Args:
        source: Source instance or value.
        source_contract: Source contract instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.
        created_at: Created at instance or value.
        initial_balance: Initial balance instance or value.
        account_currency: Account currency instance or value.
        config: Analytics configuration instance.
        benchmark: Benchmark instance or value.
        fx_evidence: Fx evidence instance or value.
        diagnostic_partial_mode: Diagnostic partial mode instance or value.

    Returns:
        Standard response containing the PerformanceReport in ``data``.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.reports import (
        build_performance_report as _build_performance_report,
    )

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

    Args:
        reports: Reports instance or value.
        base_currency: Base currency instance or value.
        fx_evidence: Fx evidence instance or value.
        config: Analytics configuration instance.
        portfolio_simulation_result: Portfolio simulation result instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing allocation evidence in ``data``.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.reports import (
        build_portfolio_allocation_evidence as _build_portfolio_allocation_evidence,
    )

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

    Args:
        reports: Reports instance or value.
        base_currency: Base currency instance or value.
        fx_evidence: Fx evidence instance or value.
        config: Analytics configuration instance.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing the portfolio report in ``data``.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.reports import (
        build_portfolio_performance_report as _build_portfolio_performance_report,
    )

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

    Args:
        request: Request instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing measurement evidence in ``data``.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.reports import (
        build_portfolio_rebalance_measurement as _build_portfolio_rebalance_measurement,
    )

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

    Args:
        reference: Reference instance or value.
        candidate: Candidate instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing comparison evidence in ``data``.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.reports import (
        compare_performance_reports as _compare_performance_reports,
    )

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

    Args:
        result: Source trading result or payload object.
        report: Performance report instance.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing reproducibility hashes in ``data``.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.reports import (
        compute_reproducibility_hashes as _compute_reproducibility_hashes,
    )

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

    Args:
        report: Performance report instance.
        format_name: Format name instance or value.
        config: Analytics configuration instance.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing the exact serialized string in ``data``.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.reports import serialize_report as _serialize_report

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

    Args:
        report: Performance report instance.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing the dashboard payload in ``data``.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.dashboards import (
        build_dashboard_payload as _build_dashboard_payload,
    )

    return run_analytics_operation(
        operation="analytics.dashboards.build_dashboard_payload",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _build_dashboard_payload(report),
    )


def build_analytics_workbench_payload(
    report: object,
    simulation_result: Mapping[str, object],
    *,
    max_points: int = 5_000,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[object]:
    """Project validated owner evidence into a finite workbench payload.

    Args:
        report: Validated Analytics PerformanceReport instance.
        simulation_result: Canonical Simulation result mapping.
        max_points: Maximum retained items per section.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing the workbench payload in ``data``.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.workbench import (
        build_workbench_payload as _build_workbench_payload,
    )

    return run_analytics_operation(
        operation="analytics.workbench.build_analytics_workbench_payload",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _build_workbench_payload(
            cast("PerformanceReport", report),
            simulation_result,
            max_points=max_points,
        ),
    )


def build_analytics_period_tables(
    report: object,
    simulation_result: Mapping[str, object],
    *,
    dimension: str = "month",
    context: str = "all",
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[object]:
    """Aggregate the canonical closed-trade ledger by one period dimension.

    Args:
        report: Validated Analytics PerformanceReport instance.
        simulation_result: Canonical Simulation result mapping.
        dimension: One of year, quarter, month, week, day, day_of_week,
            hour.
        context: ``all``, ``long``, or ``short`` source context.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing owner-safe period rows in ``data``.

    Raises:
        AnalyticsValidationError: If the report is not a PerformanceReport.
    """
    from app.services.analytics.contracts import (
        AnalyticsValidationError,
        PerformanceReport,
    )
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.workbench import (
        build_period_tables as _build_period_tables,
    )

    if not isinstance(report, PerformanceReport):
        raise AnalyticsValidationError("period table source must be PerformanceReport")
    return run_analytics_operation(
        operation="analytics.workbench.build_analytics_period_tables",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _build_period_tables(
            simulation_result, dimension=dimension, context=context
        ),
    )


def deserialize_analytics_performance_report(
    report_json: str,
    *,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[object]:
    """Rebuild one canonical report from its serialized JSON artifact.

    Args:
        report_json: Canonical JSON text produced by ``serialize_report``.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing the validated PerformanceReport in
        ``data``.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.reports import (
        deserialize_performance_report as _deserialize_performance_report,
    )

    return run_analytics_operation(
        operation="analytics.reports.deserialize_performance_report",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _deserialize_performance_report(report_json),
    )


def _truncate_transform(
    result: tuple[tuple[Mapping[str, object], ...], Mapping[str, object]],
) -> tuple[tuple[Mapping[str, object], ...], Mapping[str, object]]:
    """Place the truncated series in data and its evidence in extensions.

    Args:
        result: Source trading result or payload object.

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

    Args:
        ledger: Ledger instance or value.
        percentiles: Percentiles instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing the calculated distribution.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.reports import (
        build_worst_day_distribution as _build_worst_day_distribution,
    )

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

    Args:
        first_passage: First passage instance or value.
        joint: Joint instance or value.
        worst_day: Worst day instance or value.
        mandate_version: Mandate version instance or value.
        mode_sensitivity: Mode sensitivity instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing the barrier report section.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.reports import (
        build_barrier_section as _build_barrier_section,
    )

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

    Args:
        points: Points instance or value.
        max_points: Max points instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing the truncated series in ``data``.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.dashboards import truncate_series as _truncate_series

    return run_analytics_operation(
        operation="analytics.dashboards.truncate_series",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _truncate_series(points, max_points=max_points),
        transform=_truncate_transform,
    )


def create_process_scoring_profile(
    profile_version: str,
    dimension_weights: Mapping[str, float],
    *,
    critical_failure_policy: str = "invalidate",
    critical_failure_cap: float = 0.0,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[object]:
    """Create a validated process scoring profile.

    Args:
        profile_version: Profile version instance or value.
        dimension_weights: Dimension weights instance or value.
        critical_failure_policy: Critical failure policy instance or value.
        critical_failure_cap: Critical failure cap instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing the immutable scoring profile.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.scoring import (
        create_process_scoring_profile as _create_process_scoring_profile,
    )

    return run_analytics_operation(
        operation="analytics.scoring.create_process_scoring_profile",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _create_process_scoring_profile(
            profile_version,
            dimension_weights,
            critical_failure_policy=critical_failure_policy,
            critical_failure_cap=critical_failure_cap,
        ),
    )


def create_critical_failure_record(
    kind: str,
    severity: str,
    detail: str,
    *,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[object]:
    """Create one validated critical-failure observation record.

    Args:
        kind: Kind instance or value.
        severity: Severity instance or value.
        detail: Detail instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing the immutable failure record.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.scoring import (
        create_critical_failure_record as _create_critical_failure_record,
    )

    return run_analytics_operation(
        operation="analytics.scoring.create_critical_failure_record",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _create_critical_failure_record(kind, severity, detail),
    )


def build_session_score(
    profile: object,
    dimension_scores: Mapping[str, float],
    *,
    session_id: str,
    scored_at: datetime,
    critical_failures: Sequence[object] = (),
    no_trade: bool = False,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[object]:
    """Compute one deterministic process-first session score.

    Args:
        profile: Profile instance or value.
        dimension_scores: Dimension scores instance or value.
        session_id: Session id instance or value.
        scored_at: Scored at instance or value.
        critical_failures: Critical failures instance or value.
        no_trade: No trade instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing the immutable session score.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.scoring import (
        build_session_score as _build_session_score,
    )

    return run_analytics_operation(
        operation="analytics.scoring.build_session_score",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _build_session_score(
            cast("Any", profile),
            dimension_scores,
            session_id=session_id,
            scored_at=scored_at,
            critical_failures=cast("Any", critical_failures),
            no_trade=no_trade,
        ),
    )


def compute_leaderboard_ranking(
    scores: Sequence[object],
    profits: Mapping[str, str] | None = None,
    *,
    limit: int | None = None,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[object]:
    """Rank sessions deterministically with process score primary.

    Args:
        scores: Scores instance or value.
        profits: Profits instance or value.
        limit: Limit instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing ordered ranking rows.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.scoring import (
        compute_leaderboard_ranking as _compute_leaderboard_ranking,
    )

    return run_analytics_operation(
        operation="analytics.scoring.compute_leaderboard_ranking",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _compute_leaderboard_ranking(
            cast("Any", scores), profits, limit=limit
        ),
    )


def build_process_score_mapping(
    score: object,
    *,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[object]:
    """Serialize one session score to a JSON-safe v1 mapping.

    Args:
        score: Score instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing the validated JSON-safe mapping.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.scoring import (
        build_process_score_mapping as _build_process_score_mapping,
    )

    return run_analytics_operation(
        operation="analytics.scoring.build_process_score_mapping",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _build_process_score_mapping(cast("Any", score)),
    )


def parse_process_score_mapping(
    mapping: Mapping[str, object],
    *,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[object]:
    """Validate and denormalize a v1 process-score mapping.

    Args:
        mapping: Mapping instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing the immutable session score.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.scoring import (
        parse_process_score_mapping as _parse_process_score_mapping,
    )

    return run_analytics_operation(
        operation="analytics.scoring.parse_process_score_mapping",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _parse_process_score_mapping(mapping),
    )


def build_scoring_profile_mapping(
    profile: object,
    *,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[object]:
    """Serialize one scoring profile to a JSON-safe v1 mapping.

    Args:
        profile: Profile instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing the validated JSON-safe mapping.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.scoring import (
        build_scoring_profile_mapping as _build_scoring_profile_mapping,
    )

    return run_analytics_operation(
        operation="analytics.scoring.build_scoring_profile_mapping",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _build_scoring_profile_mapping(cast("Any", profile)),
    )


def parse_scoring_profile_mapping(
    mapping: Mapping[str, object],
    *,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StandardResponse[object]:
    """Validate and denormalize a v1 scoring-profile mapping.

    Args:
        mapping: Mapping instance or value.
        request_id: Optional request id.
        correlation_id: Optional correlation id.

    Returns:
        Standard response containing the immutable scoring profile.
    """
    from app.services.analytics.contracts.responses import run_analytics_operation
    from app.services.analytics.scoring import (
        parse_scoring_profile_mapping as _parse_scoring_profile_mapping,
    )

    return run_analytics_operation(
        operation="analytics.scoring.parse_scoring_profile_mapping",
        request_id=request_id,
        correlation_id=correlation_id,
        raw=lambda: _parse_scoring_profile_mapping(mapping),
    )


__all__: tuple[str, ...] = (
    "adapt_trading_result",
    "align_benchmark_series",
    "analyze_emergency_response",
    "append_player_journal_entry",
    "assess_plan_adherence",
    "build_analytics_period_tables",
    "build_analytics_workbench_payload",
    "build_barrier_section",
    "build_closed_trade_equity_curve",
    "build_dashboard_payload",
    "build_performance_report",
    "build_portfolio_allocation_evidence",
    "build_portfolio_performance_report",
    "build_portfolio_rebalance_measurement",
    "build_process_score_mapping",
    "build_quality_flag",
    "build_scoring_profile_mapping",
    "build_session_score",
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
    "compute_leaderboard_ranking",
    "compute_reproducibility_hashes",
    "create_analytics_run_config",
    "create_analytics_value",
    "create_closed_trade_ledger",
    "create_critical_failure_record",
    "create_portfolio_rebalance_measurement_request",
    "create_process_scoring_profile",
    "create_risk_free_rate_evidence",
    "create_statistical_validation_config",
    "deserialize_analytics_performance_report",
    "detect_behavior_patterns",
    "evaluate_player_qualification",
    "get_analytics_dashboard_snapshot",
    "get_analytics_migrations",
    "get_analytics_schema_version",
    "get_analytics_value_field",
    "get_annualization_policy",
    "get_breakeven_epsilon",
    "get_contract_compatibility_matrix",
    "get_evidence_catalog",
    "get_metric_definition_catalog",
    "get_min_metric_samples",
    "is_analytics_value",
    "parse_process_score_mapping",
    "parse_scoring_profile_mapping",
    "read_player_journal_entry",
    "run_analytics_migrations",
    "run_statistical_validation",
    "serialize_report",
    "to_analytics_error_payload",
    "to_report_json_safe",
    "truncate_series",
    "validate_contract_version",
    "validate_metric_catalog",
)
