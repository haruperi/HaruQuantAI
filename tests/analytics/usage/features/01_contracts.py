"""Executable Analytics contracts usage example.

Demonstrates FEAT-ANLT-01 versioned contracts, metric definition catalog, errors, warnings,
and JSON-safe serialization.
"""

from __future__ import annotations

import sys
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
    to_analytics_error_payload,
    to_report_json_safe,
    validate_contract_version,
    validate_metric_catalog,
)
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
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


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
    fr_anlt_018()

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
