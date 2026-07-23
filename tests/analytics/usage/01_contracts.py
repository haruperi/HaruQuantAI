"""Executable Analytics contracts usage example.

Demonstrates versioned contracts, metric definition catalog, errors, warnings,
and JSON-safe serialization.
"""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.analytics.contracts import (
    METRIC_DEFINITION_CATALOG,
    AnalyticsValidationError,
    ClosedTrade,
    Lineage,
    MetricEvidence,
    PerformanceReport,
    ReproducibilityHashes,
    SectionEvidence,
    build_quality_flag,
    build_warning,
    to_analytics_error_payload,
    to_report_json_safe,
    validate_contract_version,
    validate_metric_catalog,
)

NOW = datetime(2026, 7, 19, tzinfo=UTC)
HASH = "0" * 64


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


def example_contracts() -> None:
    """Demonstrate Analytics contracts, validation, catalog, and serialization."""
    print("=" * 80)
    print("Analytics Example 1: Contracts and Serialization")
    print("=" * 80)

    # 1. Contract version validation
    status = validate_contract_version("simulation.result", "v1")
    print(f"Contract simulation.result v1 compatibility status: {status}")

    # 2. Metric definition catalog
    validate_metric_catalog(METRIC_DEFINITION_CATALOG)
    print(f"Catalog contains {len(METRIC_DEFINITION_CATALOG)} defined metric keys.")

    # 3. ClosedTrade PnL
    trade = _trade()
    print(f"ClosedTrade net PnL: {trade.net_trade_pnl}")

    # 4. Warnings and Quality Flags via build_warning and build_quality_flag
    warning = build_warning(
        "insufficient_samples",
        section="trades",
        source_context="usage",
        detail={"observed_count": 1, "required_count": 10},
        max_detail_bytes=1024,
    )
    qflag = build_quality_flag(
        "sample_below_threshold",
        section="trades",
        source_context="usage",
        detail={"observed_count": 1, "required_count": 10},
        max_detail_bytes=1024,
    )
    print(f"Built warning: {warning.code}, quality flag: {qflag.code}")

    # 5. Performance Report construction and serialization
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
        quality_flags=(qflag,),
        lineage=_lineage(),
        hashes=_hashes(),
        precision_metadata={"decimal_places": 8},
    )

    json_report = to_report_json_safe(report)
    print(
        f"PerformanceReport serialized to JSON-safe dict, keys: {list(json_report.keys())}"
    )

    # 6. Error conversion
    err_payload = to_analytics_error_payload(
        AnalyticsValidationError("Invalid input schema"), max_detail_bytes=128
    )
    print(f"Analytics error payload: {err_payload['code']} - {err_payload['message']}")


def main() -> None:
    """Run Analytics contracts usage example."""
    example_contracts()


if __name__ == "__main__":
    main()
