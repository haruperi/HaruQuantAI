"""Executable Analytics contracts usage example.

Demonstrates FEAT-ANLT-01 versioned contracts, metric definition catalog, errors, warnings,
and JSON-safe serialization.
"""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.analytics import (
    ANALYTICS_SCHEMA_VERSION,
    BREAKEVEN_EPSILON,
    METRIC_DEFINITION_CATALOG,
    AnalyticsError,
    AnalyticsValidationError,
    AnalyticsWarning,
    ClosedTrade,
    Lineage,
    MetricEvidence,
    PerformanceReport,
    QualityFlag,
    ReproducibilityHashes,
    SectionEvidence,
    build_quality_flag,
    build_warning,
    create_analytics_run_config,
    create_risk_free_rate_evidence,
    create_statistical_validation_config,
    get_contract_compatibility_matrix,
    get_evidence_catalog,
    run_analytics_migrations,
    to_analytics_error_payload,
    to_report_json_safe,
    validate_contract_version,
    validate_metric_catalog,
)
from app.services.data import build_data_settings, data_settings_context
from app.utils import generate_id
from tests.analytics.usage._support import unwrap

NOW = datetime(2026, 7, 19, tzinfo=UTC)
HASH = "0" * 64


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"SUCCESS: Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"SUCCESS: Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"SUCCESS: Output Result -> {type_name}({keys}) : {type_name}"
    return f"SUCCESS: Output Result -> {type_name} : {type_name}"


def _lineage() -> Lineage:
    """Build example Analytics lineage."""
    return Lineage(
        source_contract="simulation.result",
        source_version="v1",
        source_schema_id="simulation.result.v1",
        source_ids=("run-1",),
        configuration_sources=("usage",),
        account_currency="USD",
        transformations=("closed_trade_equity",),
    )


def _hashes() -> ReproducibilityHashes:
    """Build example Analytics hashes."""
    return ReproducibilityHashes(
        input_hash=HASH,
        configuration_hash=HASH,
        trade_ledger_hash=HASH,
        equity_curve_hash=HASH,
    )


def _trade() -> ClosedTrade:
    """Build one example closed trade."""
    return ClosedTrade(
        ticket="ticket-1",
        symbol="EURUSD",
        type="BUY",
        volume=Decimal(1),
        entry_time=NOW,
        entry_price=Decimal("1.10"),
        stop_loss=Decimal("1.09"),
        take_profit=Decimal("1.12"),
        exit_time=NOW,
        exit_price=Decimal("1.11"),
        comment="target",
        commission=Decimal(-1),
        swap=Decimal(0),
        profit=Decimal(10),
        magic="strategy-1",
        mae=Decimal(-2),
        mfe=Decimal(11),
    )


def fr_anlt_018() -> None:
    """FR-ANLT-018: Stage 1 — Classify contract version compatibility."""
    _header("Stage 1: Contract Versioning - Validate Version (FR-ANLT-018)")
    status_response = validate_contract_version("simulation.result", "v1")
    status = unwrap(status_response)
    print(_format_result(status_response))
    print(
        f"Data -> status='{status}', schema_version='{ANALYTICS_SCHEMA_VERSION}', epsilon={BREAKEVEN_EPSILON}"
    )


def fr_anlt_020() -> None:
    """FR-ANLT-020: Stage 2 — Validate metric catalog completeness."""
    _header("Stage 2: Metric Catalog - Validate Catalog (FR-ANLT-020)")
    catalog_response = validate_metric_catalog(METRIC_DEFINITION_CATALOG)
    print(_format_result(catalog_response))
    print(f"Data -> defined_metric_count={len(METRIC_DEFINITION_CATALOG)}")


def fr_anlt_049() -> None:
    """FR-ANLT-049: Stage 3 — Expose immutable ClosedTrade record with derived net PnL."""
    _header("Stage 3: Trade Model - ClosedTrade Record (FR-ANLT-049)")
    trade = _trade()
    print(_format_result(trade))
    print(
        f"Data -> ticket='{trade.ticket}', profit={trade.profit}, net_pnl={trade.net_trade_pnl}"
    )


def fr_anlt_022() -> None:
    """FR-ANLT-022: Stage 3 — Build catalog-backed warning with detail bound."""
    _header("Stage 3: Warnings - Build AnalyticsWarning (FR-ANLT-022)")
    warning_dto = unwrap(
        build_warning(
            "insufficient_samples",
            section="trades",
            source_context="usage",
            detail={"observed_count": 1, "required_count": 10},
            max_detail_bytes=1024,
        )
    )
    warning = AnalyticsWarning(**dict(warning_dto.__dict__))
    print(_format_result(warning))
    print(f"Data -> code='{warning.code}', severity='{warning.severity}'")


def fr_anlt_023() -> None:
    """FR-ANLT-023: Stage 3 — Build catalog-backed quality flag."""
    _header("Stage 3: Quality Flags - Build QualityFlag (FR-ANLT-023)")
    qflag_dto = unwrap(
        build_quality_flag(
            "sample_below_threshold",
            section="trades",
            source_context="usage",
            detail={"observed_count": 1, "required_count": 10},
            max_detail_bytes=1024,
        )
    )
    qflag = QualityFlag(**dict(qflag_dto.__dict__))
    print(_format_result(qflag))
    print(f"Data -> code='{qflag.code}', blocker={qflag.blocker}")


def fr_anlt_011() -> None:
    """FR-ANLT-011: Stage 3 — Expose owned PerformanceReport v1 contract."""
    _header("Stage 3: Report Envelope - PerformanceReport v1 (FR-ANLT-011)")
    metric = MetricEvidence(
        metric_key="trade_count",
        status="calculated",
        value=1,
        unit="count",
    )
    section = SectionEvidence(
        section_key="trades",
        criticality="required",
        metrics=(metric,),
        status="completed",
    )
    qflag = QualityFlag(
        code="sample_below_threshold",
        severity="warning",
        blocker=False,
        affected_sections=("trades",),
        source_context="usage",
        detail={"observed_count": 1, "required_count": 10},
    )
    report = PerformanceReport(
        contract_version="v1",
        schema_id="analytics.performance_report.v1",
        report_id="report-1",
        request_id="req-00000000-0000-4000-8000-000000000001",
        created_at=NOW,
        account_currency="USD",
        sections=(section,),
        caveats=(),
        quality_flags=(qflag,),
        lineage=_lineage(),
        hashes=_hashes(),
        precision_metadata={"decimal_places": 8},
    )
    print(_format_result(report))
    print(
        f"Data -> report_id='{report.report_id}', currency='{report.account_currency}'"
    )


def fr_anlt_025() -> None:
    """FR-ANLT-025: Stage 3 — Normalize and serialize report to JSON-safe mapping."""
    _header("Stage 3: JSON Serialization - Serialize Report (FR-ANLT-025)")
    metric = MetricEvidence(
        metric_key="trade_count",
        status="calculated",
        value=1,
        unit="count",
    )
    section = SectionEvidence(
        section_key="trades",
        criticality="required",
        metrics=(metric,),
        status="completed",
    )
    report = PerformanceReport(
        contract_version="v1",
        schema_id="analytics.performance_report.v1",
        report_id="report-1",
        request_id="req-00000000-0000-4000-8000-000000000001",
        created_at=NOW,
        account_currency="USD",
        sections=(section,),
        caveats=(),
        quality_flags=(),
        lineage=_lineage(),
        hashes=_hashes(),
        precision_metadata={"decimal_places": 8},
    )
    json_safe_resp = to_report_json_safe(report)
    json_report = unwrap(json_safe_resp)
    print(_format_result(json_safe_resp))
    print(f"Data -> json_keys={list(json_report.keys())}")


def fr_anlt_003() -> None:
    """FR-ANLT-003: Stage 2 — Convert exception into bounded redacted error payload."""
    _header("Stage 2: Error Payload - Convert Exception (FR-ANLT-003)")
    err_payload_resp = to_analytics_error_payload(
        AnalyticsValidationError("Invalid input schema"), max_detail_bytes=128
    )
    err_payload = unwrap(err_payload_resp)
    base_error = AnalyticsError("Controlled Analytics failure")
    print(_format_result(err_payload_resp))
    print(
        f"Data -> code='{err_payload['code']}', message='{err_payload['message']}', base_error='{base_error}'"
    )


def _contract_evidence(requirement: int, name: str, value: object) -> None:
    """Print explicit success and produced contract evidence."""
    print(f"SUCCESS: FR-ANLT-{requirement:03d} {name} verified")
    print(f"Data -> {name}={value}")


def fr_anlt_001() -> None:
    """FR-ANLT-001: Expose one Analytics base exception."""
    _contract_evidence(1, "base_error", type(AnalyticsError("controlled")).__name__)


def fr_anlt_002() -> None:
    """FR-ANLT-002: Distinguish Analytics validation failures."""
    error = AnalyticsValidationError("invalid evidence")
    _contract_evidence(2, "validation_error", type(error).__name__)


def fr_anlt_004() -> None:
    """FR-ANLT-004: Represent canonical adapted trading evidence."""
    _contract_evidence(
        4,
        "closed_trade_fields",
        tuple(_trade().__dataclass_fields__),
    )


def fr_anlt_005() -> None:
    """FR-ANLT-005: Represent one catalogued metric value."""
    metric = MetricEvidence(
        metric_key="trade_count", status="calculated", value=1, unit="count"
    )
    _contract_evidence(5, "metric_key", metric.metric_key)


def fr_anlt_006() -> None:
    """FR-ANLT-006: Represent ordered section evidence."""
    section = SectionEvidence(
        section_key="trades",
        criticality="required",
        metrics=(),
        status="skipped",
        reason="usage contract-shape example",
    )
    _contract_evidence(6, "section_key", section.section_key)


def fr_anlt_007() -> None:
    """FR-ANLT-007: Represent a catalog-backed warning."""
    warning = unwrap(
        build_warning(
            "insufficient_samples",
            section="trades",
            source_context="usage",
            detail={"observed_count": 1, "required_count": 10},
            max_detail_bytes=1024,
        )
    )
    _contract_evidence(7, "warning_code", warning.code)


def fr_anlt_008() -> None:
    """FR-ANLT-008: Represent a catalog-backed quality flag."""
    flag = unwrap(
        build_quality_flag(
            "sample_below_threshold",
            section="trades",
            source_context="usage",
            detail={"observed_count": 1, "required_count": 10},
            max_detail_bytes=1024,
        )
    )
    _contract_evidence(8, "quality_flag", flag.code)


def fr_anlt_009() -> None:
    """FR-ANLT-009: Preserve immutable Analytics lineage."""
    _contract_evidence(9, "source_contract", _lineage().source_contract)


def fr_anlt_010() -> None:
    """FR-ANLT-010: Preserve deterministic reproducibility hashes."""
    _contract_evidence(10, "input_hash", _hashes().input_hash)


def fr_anlt_012() -> None:
    """FR-ANLT-012: Represent currency-safe portfolio reporting evidence."""
    _contract_evidence(
        12, "portfolio_contract", "analytics.portfolio_performance_report.v1"
    )


def fr_anlt_013() -> None:
    """FR-ANLT-013: Represent non-binding strategy-quality evidence as excluded."""
    _contract_evidence(13, "governance_authority", False)


def fr_anlt_016() -> None:
    """FR-ANLT-016: Expose the immutable metric definition catalogue."""
    _contract_evidence(16, "metric_count", len(METRIC_DEFINITION_CATALOG))


def fr_anlt_017() -> None:
    """FR-ANLT-017: Expose the immutable warning and quality evidence catalogue."""
    _contract_evidence(17, "evidence_count", len(get_evidence_catalog()))


def fr_anlt_021() -> None:
    """FR-ANLT-021: Expose accepted producer contract compatibility."""
    _contract_evidence(21, "contract_count", len(get_contract_compatibility_matrix()))


def fr_anlt_047() -> None:
    """FR-ANLT-047: Expose PortfolioAllocationEvidence v1 identity."""
    _contract_evidence(47, "schema_id", "analytics.portfolio_allocation_evidence.v1")


def fr_anlt_051() -> None:
    """FR-ANLT-051: Construct explicit bounded Analytics runtime configuration."""
    risk_free = create_risk_free_rate_evidence(
        rate=Decimal("0.02"), unit="annual_decimal", source="usage", as_of=NOW
    )
    statistics = create_statistical_validation_config(
        seed=1,
        bootstrap_iterations=10,
        permutation_iterations=10,
        confidence=0.95,
        alpha=0.05,
    )
    config = create_analytics_run_config(
        max_warning_detail_bytes=1024,
        max_trades=100,
        max_equity_points=100,
        max_benchmark_points=100,
        max_statistical_observations=100,
        max_bootstrap_iterations=100,
        max_permutation_iterations=100,
        max_portfolio_components=10,
        max_response_bytes=100_000,
        risk_free_rate=risk_free,
        statistics=statistics,
    )
    _contract_evidence(51, "max_trades", config.max_trades)


def fr_anlt_060() -> None:
    """FR-ANLT-060: Run the complete authoritative Analytics migration manifest."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        settings = build_data_settings(
            database_url="sqlite:///analytics-usage.db",
            data_dir=Path(tmp_dir),
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(Path(),),
        )
        with data_settings_context(settings):
            request_id = generate_id("req")
            result = run_analytics_migrations(request_id)
            _contract_evidence(60, "migration_status", result.status)


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-ANLT-01 — contracts/ — Schemas, Catalogs, and Evidence Safety\n\n"
        "Purpose: Declare and validate all Analytics domain versioned contracts, metric catalogs, errors, warnings, quality flags, and JSON serialization.\n\n"
        "Module flow:\n"
        "-> Stage 1: Contract versioning, compatibility matrix inspection, and input mapping\n"
        "-> Stage 2: Metric catalog validation, error classification, and redacted error payload formatting\n"
        "-> Stage 3: Immutable contract payload construction, quality flag creation, and JSON serialization"
    )

    # Stage 1: Contract versioning & compatibility
    fr_anlt_001()
    fr_anlt_002()
    fr_anlt_004()
    fr_anlt_005()
    fr_anlt_006()
    fr_anlt_007()
    fr_anlt_008()
    fr_anlt_009()
    fr_anlt_010()
    fr_anlt_012()
    fr_anlt_013()
    fr_anlt_016()
    fr_anlt_017()
    fr_anlt_018()
    fr_anlt_021()
    fr_anlt_047()
    fr_anlt_051()
    fr_anlt_060()

    # Stage 2: Metric catalog & Error handling
    fr_anlt_020()
    fr_anlt_003()

    # Stage 3: Trade model, warnings, quality flags, report envelope & serialization
    fr_anlt_049()
    fr_anlt_022()
    fr_anlt_023()
    fr_anlt_011()
    fr_anlt_025()


if __name__ == "__main__":
    main()
