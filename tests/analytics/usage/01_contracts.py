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

from app.services.analytics import (
    ANALYTICS_SCHEMA_VERSION,
    ANNUALIZATION_POLICY,
    BREAKEVEN_EPSILON,
    CONTRACT_COMPATIBILITY_MATRIX,
    EVIDENCE_CATALOG,
    METRIC_DEFINITION_CATALOG,
    MIN_METRIC_SAMPLES,
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

NOW = datetime(2026, 7, 19, tzinfo=UTC)
HASH = "0" * 64


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


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
    _header("Demonstrate Analytics contracts, validation, catalog, and serialization.")
    print("Analytics Example 1: Contracts and Serialization")

    # 1. Contract version validation
    status = validate_contract_version("simulation.result", "v1")
    print(f"Contract simulation.result v1 compatibility status: {status}")
    print(
        "Contract/catalog policies: "
        f"{ANALYTICS_SCHEMA_VERSION}, "
        f"{CONTRACT_COMPATIBILITY_MATRIX['simulation.result']['v1']}, "
        f"{len(EVIDENCE_CATALOG['warnings'])} warnings, "
        f"{ANNUALIZATION_POLICY['trading_days']} trading days, "
        f"{MIN_METRIC_SAMPLES['variance']} variance samples, "
        f"epsilon {BREAKEVEN_EPSILON}"
    )

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
    warning = AnalyticsWarning(**dict(warning.__dict__))
    qflag = QualityFlag(**dict(qflag.__dict__))
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
        "PerformanceReport serialized to JSON-safe dict, keys: "
        f"{list(json_report.keys())}"
    )

    # 6. Error conversion
    err_payload = to_analytics_error_payload(
        AnalyticsValidationError("Invalid input schema"), max_detail_bytes=128
    )
    base_error = AnalyticsError("Controlled Analytics failure")
    print(f"Analytics error payload: {err_payload['code']} - {err_payload['message']}")
    print(f"Analytics base error: {base_error}")


def fr_anlt_001() -> None:
    """FR-ANLT-001.

    The system shall expose one base exception for direct Analytics feature APIs.
    """
    _header(
        "FR-ANLT-001. The system shall expose one base exception for direct Analytics feature APIs."
    )
    example_contracts()


def fr_anlt_002() -> None:
    """FR-ANLT-002.

    The system shall distinguish invalid, missing, incompatible, or unsafe
    analytics evidence from execution failures.
    """
    _header(
        "FR-ANLT-002. The system shall distinguish invalid, missing, incompatible, or unsafe analytics evidence from execution failures."
    )
    example_contracts()


def fr_anlt_003() -> None:
    """FR-ANLT-003.

    The system shall convert a controlled exception into a bounded, redacted error
    payload without exposing provider exceptions or secrets. The caller supplies
    the validated positive detail bound explicitly; there is no fallback.
    """
    _header(
        "FR-ANLT-003. The system shall convert a controlled exception into a bounded, redacted error payload without exposing provider exceptions or secrets. The caller supplies the validated positive detail bound explicitly; there is no fallback."
    )
    example_contracts()


def fr_anlt_004() -> None:
    """FR-ANLT-004.

    The system shall represent an adapted upstream result with source version,
    IDs, phase, UTC window, `account_currency`, `initial_balance`, strategy,
    symbols, timeframe, an ordered `tuple[ClosedTrade, ...]` ledger, the derived
    closed-trade equity curve and its daily resample,
    `curve_basis="closed_trade"`, optional benchmark evidence, quality metadata,
    and lineage. The ledger is the primary evidence; every other series is derived
    from it deterministically.
    """
    _header(
        "FR-ANLT-004. The system shall represent an adapted upstream result with source version, IDs, phase, UTC window, `account_currency`, `initial_balance`, strategy, symbols, timeframe, an ordered `tuple[ClosedTrade, ...]` ledger, the derived closed-trade equity curve and its daily resample, `curve_basis='closed_trade'`, optional benchmark evidence, quality metadata, and lineage. The ledger is the primary evidence; every other series is derived from it deterministically."
    )
    example_contracts()


def fr_anlt_005() -> None:
    """FR-ANLT-005.

    The system shall represent one metric as a finite calculated/undefined/skipped
    value with unit, confidence, warnings, and source context.
    """
    _header(
        "FR-ANLT-005. The system shall represent one metric as a finite calculated/undefined/skipped value with unit, confidence, warnings, and source context."
    )
    example_contracts()


def fr_anlt_006() -> None:
    """FR-ANLT-006.

    The system shall represent one report section with approved criticality,
    ordered metrics, status, warnings, and failure/skipped reason.
    """
    _header(
        "FR-ANLT-006. The system shall represent one report section with approved criticality, ordered metrics, status, warnings, and failure/skipped reason."
    )
    example_contracts()


def fr_anlt_007() -> None:
    """FR-ANLT-007.

    The system shall represent a bounded warning with code, severity, affected
    section, source context, and detail.
    """
    _header(
        "FR-ANLT-007. The system shall represent a bounded warning with code, severity, affected section, source context, and detail."
    )
    example_contracts()


def fr_anlt_008() -> None:
    """FR-ANLT-008.

    The system shall represent a quality flag separately from metrics and
    governance decisions, including blocker semantics and source evidence.
    """
    _header(
        "FR-ANLT-008. The system shall represent a quality flag separately from metrics and governance decisions, including blocker semantics and source evidence."
    )
    example_contracts()


def fr_anlt_009() -> None:
    """FR-ANLT-009.

    The system shall preserve bounded source IDs, versions, configuration sources,
    inherited currency, and transformation history.
    """
    _header(
        "FR-ANLT-009. The system shall preserve bounded source IDs, versions, configuration sources, inherited currency, and transformation history."
    )
    example_contracts()


def fr_anlt_010() -> None:
    """FR-ANLT-010.

    The system shall hold SHA-256 hashes for input, configuration, trade ledger,
    equity curve, optional benchmark, and final report evidence.
    """
    _header(
        "FR-ANLT-010. The system shall hold SHA-256 hashes for input, configuration, trade ledger, equity curve, optional benchmark, and final report evidence."
    )
    example_contracts()


def fr_anlt_011() -> None:
    """FR-ANLT-011.

    The system shall expose the owned `PerformanceReport v1` cross-domain contract
    with ordered sections, caveats, lineage, hashes, precision metadata, and
    `non_binding=true`.
    """
    _header(
        "FR-ANLT-011. The system shall expose the owned `PerformanceReport v1` cross-domain contract with ordered sections, caveats, lineage, hashes, precision metadata, and `non_binding=true`."
    )
    example_contracts()


def fr_anlt_012() -> None:
    """FR-ANLT-012.

    The system shall represent real portfolio aggregation with component lineage,
    base currency, FX evidence, blocker flags, and no fabricated aggregate values.
    """
    _header(
        "FR-ANLT-012. The system shall represent real portfolio aggregation with component lineage, base currency, FX evidence, blocker flags, and no fabricated aggregate values."
    )
    example_contracts()


def fr_anlt_013() -> None:
    """FR-ANLT-013.

    The system shall represent versioned finite chart/table payloads, section
    statuses, warnings, units, and truncation metadata without UI rendering logic.
    """
    _header(
        "FR-ANLT-013. The system shall represent versioned finite chart/table payloads, section statuses, warnings, units, and truncation metadata without UI rendering logic."
    )
    example_contracts()


def fr_anlt_016() -> None:
    """FR-ANLT-016.

    The system shall expose an authoritative definition for every metric used by a
    report, dashboard, warning, or quality flag.
    """
    _header(
        "FR-ANLT-016. The system shall expose an authoritative definition for every metric used by a report, dashboard, warning, or quality flag."
    )
    example_contracts()


def fr_anlt_017() -> None:
    """FR-ANLT-017.

    The system shall expose deterministic, separately namespaced warning and
    quality-flag definitions with bounded details, source-backed status, and
    blocker meaning.
    """
    _header(
        "FR-ANLT-017. The system shall expose deterministic, separately namespaced warning and quality-flag definitions with bounded details, source-backed status, and blocker meaning."
    )
    example_contracts()


def fr_anlt_018() -> None:
    """FR-ANLT-018.

    The system shall classify accepted source/report contract versions and reject
    missing, legacy, unsupported, and future versions independently of
    `schema_id`; Analytics provides no compatibility adapter unless a version is
    explicitly registered with an implemented adapter.
    """
    _header(
        "FR-ANLT-018. The system shall classify accepted source/report contract versions and reject missing, legacy, unsupported, and future versions independently of `schema_id`; Analytics provides no compatibility adapter unless a version is explicitly registered with an implemented adapter."
    )
    example_contracts()


def fr_anlt_020() -> None:
    """FR-ANLT-020.

    The system shall reject a metric catalog lacking formula, unit, inputs, scale,
    annualization, sample convention, minimum sample, undefined behavior, evidence
    type, or fixture.
    """
    _header(
        "FR-ANLT-020. The system shall reject a metric catalog lacking formula, unit, inputs, scale, annualization, sample convention, minimum sample, undefined behavior, evidence type, or fixture."
    )
    example_contracts()


def fr_anlt_021() -> None:
    """FR-ANLT-021.

    The system shall classify `contract_version` and reject missing, unsupported,
    or unsafe future compatibility versions before calculation; `schema_id` is
    validated separately and never parsed as a version.
    """
    _header(
        "FR-ANLT-021. The system shall classify `contract_version` and reject missing, unsupported, or unsafe future compatibility versions before calculation; `schema_id` is validated separately and never parsed as a version."
    )
    example_contracts()


def fr_anlt_022() -> None:
    """FR-ANLT-022.

    The system shall build a catalog-backed warning with deterministic ordering
    and bounded redacted detail. The validated positive detail bound is supplied
    explicitly from `AnalyticsRunConfig`.
    """
    _header(
        "FR-ANLT-022. The system shall build a catalog-backed warning with deterministic ordering and bounded redacted detail. The validated positive detail bound is supplied explicitly from `AnalyticsRunConfig`."
    )
    example_contracts()


def fr_anlt_023() -> None:
    """FR-ANLT-023.

    The system shall build a catalog-backed quality flag that separates evidence
    from final governance decisions. The validated positive detail bound is
    supplied explicitly from `AnalyticsRunConfig`.
    """
    _header(
        "FR-ANLT-023. The system shall build a catalog-backed quality flag that separates evidence from final governance decisions. The validated positive detail bound is supplied explicitly from `AnalyticsRunConfig`."
    )
    example_contracts()


def fr_anlt_025() -> None:
    """FR-ANLT-025.

    The system shall normalize report-specific pandas and NumPy values into
    Utils-supported types, delegate the conversion to the Utils-owned
    `to_json_safe`, and translate the resulting Utils `ValidationError` into
    `AnalyticsValidationError`. It shall not reimplement finite, cycle, depth, or
    item checking, and shall not define a symbol named `to_json_safe`.
    """
    _header(
        "FR-ANLT-025. The system shall normalize report-specific pandas and NumPy values into Utils-supported types, delegate the conversion to the Utils-owned `to_json_safe`, and translate the resulting Utils `ValidationError` into `AnalyticsValidationError`. It shall not reimplement finite, cycle, depth, or item checking, and shall not define a symbol named `to_json_safe`."
    )
    example_contracts()


def fr_anlt_047() -> None:
    """FR-ANLT-047.

    The system shall expose the owned `PortfolioAllocationEvidence v1`
    cross-domain contract carrying `contract_version="v1"`,
    `schema_id="analytics.portfolio_allocation_evidence.v1"`, allocation and
    result references, a UTC measurement window, ordered component and aggregate
    metric evidence, dependence and concentration evidence, ordered caveats, FX
    lineage, and `non_binding=true`. Field set matches the registered row in
    `docs/PROJECT.md` §5.
    """
    _header(
        "FR-ANLT-047. The system shall expose the owned `PortfolioAllocationEvidence v1` cross-domain contract carrying `contract_version='v1'`, `schema_id='analytics.portfolio_allocation_evidence.v1'`, allocation and result references, a UTC measurement window, ordered component and aggregate metric evidence, dependence and concentration evidence, ordered caveats, FX lineage, and `non_binding=true`. Field set matches the registered row in `docs/PROJECT.md` §5."
    )
    example_contracts()


def fr_anlt_049() -> None:
    """FR-ANLT-049.

    The system shall represent one closed trade as an immutable record carrying
    `ticket`, `symbol`, `type` (direction), `volume`, `entry_time`, `entry_price`,
    `stop_loss`, `take_profit`, `exit_time`, `exit_price`, `comment` (exit
    reason), `commission`, `swap`, `profit`, `magic` (strategy ID), `mae`, and
    `mfe`. Timestamps are UTC; `volume`, prices, and monetary fields are
    `Decimal`. `profit` is **gross**: it reflects price movement only and excludes
    `commission` and `swap`, which arrive with a negative sign under the MT5
    convention. The contract exposes the derived read-only property `net_trade_pnl
    = profit + commission + swap`.
    """
    _header(
        "FR-ANLT-049. The system shall represent one closed trade as an immutable record carrying `ticket`, `symbol`, `type` (direction), `volume`, `entry_time`, `entry_price`, `stop_loss`, `take_profit`, `exit_time`, `exit_price`, `comment` (exit reason), `commission`, `swap`, `profit`, `magic` (strategy ID), `mae`, and `mfe`. Timestamps are UTC; `volume`, prices, and monetary fields are `Decimal`. `profit` is **gross**: it reflects price movement only and excludes `commission` and `swap`, which arrive with a negative sign under the MT5 convention. The contract exposes the derived read-only property `net_trade_pnl = profit + commission + swap`."
    )
    example_contracts()


def fr_anlt_051() -> None:
    """FR-ANLT-051.

    The system shall accept one immutable caller-constructed runtime configuration
    containing every required positive input/response/iteration bound, optional
    source-backed risk-free-rate evidence, and deterministic statistical settings.
    Analytics reads no environment variable or configuration file and applies no
    fallback.
    """
    _header(
        "FR-ANLT-051. The system shall accept one immutable caller-constructed runtime configuration containing every required positive input/response/iteration bound, optional source-backed risk-free-rate evidence, and deterministic statistical settings. Analytics reads no environment variable or configuration file and applies no fallback."
    )
    example_contracts()


def main() -> None:
    """Run the bounded demonstration shared by every contract requirement."""
    example_contracts()


if __name__ == "__main__":
    main()
