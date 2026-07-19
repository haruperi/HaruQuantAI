"""Runnable usage evidence for the Analytics contracts feature."""

from datetime import UTC, datetime
from decimal import Decimal

from app.services.analytics.contracts import (
    METRIC_DEFINITION_CATALOG,
    AnalyticsError,
    AnalyticsRunConfig,
    AnalyticsValidationError,
    AnalyticsWarning,
    ClosedTrade,
    DashboardPayload,
    Lineage,
    MetricEvidence,
    PerformanceReport,
    PortfolioAllocationEvidence,
    PortfolioPerformanceReport,
    QualityFlag,
    ReproducibilityHashes,
    RiskFreeRateEvidence,
    SectionEvidence,
    StatisticalValidationConfig,
    TradingResult,
    build_quality_flag,
    build_warning,
    to_analytics_error_payload,
    to_report_json_safe,
    validate_contract_version,
    validate_metric_catalog,
)
from app.utils import logger

NOW = datetime(2026, 7, 19, tzinfo=UTC)
HASH = "0" * 64


def _lineage() -> Lineage:
    """Build example Analytics lineage."""
    logger.debug("Building Analytics usage lineage")
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
    logger.debug("Building Analytics usage hashes")
    return ReproducibilityHashes(
        input_hash=HASH,
        configuration_hash=HASH,
        trade_ledger_hash=HASH,
        equity_curve_hash=HASH,
    )


def _trade() -> ClosedTrade:
    """Build one example closed trade."""
    logger.debug("Building Analytics usage trade")
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


def _metric() -> MetricEvidence:
    """Build one example metric."""
    logger.debug("Building Analytics usage metric")
    return MetricEvidence(
        metric_key="trade_count",
        status="calculated",
        value=1,
        unit="count",
    )


def _section() -> SectionEvidence:
    """Build one example report section."""
    logger.debug("Building Analytics usage section")
    return SectionEvidence(
        section_key="trades",
        criticality="required",
        metrics=(_metric(),),
        status="completed",
    )


def _report() -> PerformanceReport:
    """Build one example performance report."""
    logger.debug("Building Analytics usage report")
    return PerformanceReport(
        contract_version="v1",
        schema_id="analytics.performance_report.v1",
        report_id="report-1",
        request_id="req-00000000-0000-4000-8000-000000000001",
        created_at=NOW,
        account_currency="USD",
        sections=(_section(),),
        caveats=(),
        quality_flags=(),
        lineage=_lineage(),
        hashes=_hashes(),
        precision_metadata={"decimal_places": 8},
    )


def test_usage_errors_analytics_error() -> None:
    """Construct the Analytics base error."""
    logger.debug("Running Analytics base-error usage")
    assert str(AnalyticsError("failure")) == "failure"


def test_usage_errors_validation_error() -> None:
    """Construct a controlled validation error."""
    logger.debug("Running Analytics validation-error usage")
    assert isinstance(AnalyticsValidationError("invalid"), AnalyticsError)


def test_usage_errors_error_payload() -> None:
    """Convert a controlled error into a bounded payload."""
    logger.debug("Running Analytics error-payload usage")
    assert (
        to_analytics_error_payload(
            AnalyticsValidationError("invalid"), max_detail_bytes=128
        )["code"]
        == "ANALYTICS_VALIDATION_FAILED"
    )


def test_usage_models_closed_trade() -> None:
    """Construct the receiver-owned closed-trade row."""
    logger.debug("Running Analytics closed-trade usage")
    assert _trade().net_trade_pnl == Decimal(9)


def test_usage_models_trading_result() -> None:
    """Construct the canonical producer-neutral input."""
    logger.debug("Running Analytics trading-result usage")
    trade = _trade()
    result = TradingResult(
        contract_version="v1",
        schema_id="analytics.trading_result.v1",
        source_contract="simulation.result",
        source_contract_version="v1",
        source_schema_id="simulation.result.v1",
        source_id="run-1",
        phase="backtest",
        window_start=NOW,
        window_end=NOW,
        account_currency="USD",
        initial_balance=Decimal(1000),
        strategy_id="strategy-1",
        strategy_version="v1",
        symbols=("EURUSD",),
        timeframe="M1",
        trades=(trade,),
        equity_curve=({"timestamp": NOW, "equity": Decimal(1009)},),
        daily_equity_curve=({"timestamp": NOW, "equity": Decimal(1009)},),
        curve_basis="closed_trade",
        benchmark=None,
        fx_evidence=None,
        quality_metadata={},
        source_metadata={},
        lineage=_lineage(),
    )
    assert result.trades == (trade,)


def test_usage_models_metric_evidence() -> None:
    """Construct finite metric evidence."""
    logger.debug("Running Analytics metric usage")
    assert _metric().value == 1


def test_usage_models_section_evidence() -> None:
    """Construct ordered section evidence."""
    logger.debug("Running Analytics section usage")
    assert _section().status == "completed"


def test_usage_models_warning() -> None:
    """Construct bounded warning evidence."""
    logger.debug("Running Analytics warning-model usage")
    warning = AnalyticsWarning(
        code="stop_loss_absent",
        severity="warning",
        affected_section="trades",
        source_context="all",
        detail={"ticket": "ticket-1"},
    )
    assert warning.code == "stop_loss_absent"


def test_usage_models_quality_flag() -> None:
    """Construct non-governing quality evidence."""
    logger.debug("Running Analytics quality-model usage")
    flag = QualityFlag(
        code="sample_below_threshold",
        severity="warning",
        blocker=False,
        affected_sections=("trades",),
        source_context="all",
        detail={"observed_count": 1, "required_count": 30},
    )
    assert flag.blocker is False


def test_usage_models_lineage() -> None:
    """Construct source-backed lineage."""
    logger.debug("Running Analytics lineage usage")
    assert _lineage().source_version == "v1"


def test_usage_models_hashes() -> None:
    """Construct reproducibility hash evidence."""
    logger.debug("Running Analytics hash-model usage")
    assert _hashes().input_hash == HASH


def test_usage_models_performance_report() -> None:
    """Construct the cross-domain performance report."""
    logger.debug("Running Analytics report-model usage")
    assert _report().non_binding is True


def test_usage_models_portfolio_report() -> None:
    """Construct an internal portfolio aggregation report."""
    logger.debug("Running Analytics portfolio-report usage")
    report = PortfolioPerformanceReport(
        schema_id="analytics.portfolio_performance_report.v1",
        report_id="portfolio-report-1",
        component_report_ids=("report-1",),
        measurement_start=NOW,
        measurement_end=NOW,
        base_currency="USD",
        sections=(_section(),),
        caveats=(),
        quality_flags=(),
        fx_lineage=_lineage(),
        hashes=_hashes(),
    )
    assert report.base_currency == "USD"


def test_usage_models_dashboard_payload() -> None:
    """Construct a bounded dashboard contract."""
    logger.debug("Running Analytics dashboard-model usage")
    payload = DashboardPayload(
        contract_version="v1",
        schema_id="analytics.dashboard_payload.v1",
        payload_id="payload-1",
        report_id="report-1",
        generated_at=NOW,
        sections=({"section": "trades"},),
        warnings=(),
        quality_flags=(),
        units={"trade_count": "count"},
        truncation_metadata=(),
    )
    assert payload.non_binding is True


def test_usage_models_portfolio_allocation_evidence() -> None:
    """Construct non-binding allocation evidence."""
    logger.debug("Running Analytics allocation-model usage")
    evidence = PortfolioAllocationEvidence(
        contract_version="v1",
        schema_id="analytics.portfolio_allocation_evidence.v1",
        evidence_id="allocation-evidence-1",
        allocation_reference="allocation-1",
        result_references=("result-1",),
        measurement_start=NOW,
        measurement_end=NOW,
        base_currency="USD",
        component_metrics=({"component_id": "component-1"},),
        aggregate_metrics=(_metric(),),
        dependence_evidence=_section(),
        concentration_evidence=_section(),
        caveats=(),
        fx_lineage=_lineage(),
    )
    assert evidence.non_binding is True


def test_usage_models_analytics_run_config() -> None:
    """Construct caller-injected bounded runtime configuration."""
    logger.debug("Running Analytics runtime-config usage")
    statistics = StatisticalValidationConfig(
        seed=1,
        bootstrap_iterations=10,
        permutation_iterations=10,
        confidence=0.95,
        alpha=0.05,
    )
    config = AnalyticsRunConfig(
        max_warning_detail_bytes=1024,
        max_trades=100,
        max_equity_points=100,
        max_benchmark_points=100,
        max_statistical_observations=100,
        max_bootstrap_iterations=100,
        max_permutation_iterations=100,
        max_portfolio_components=10,
        max_response_bytes=100_000,
        risk_free_rate=RiskFreeRateEvidence(
            rate=Decimal("0.02"),
            unit="annual_decimal",
            source="owner",
            as_of=NOW,
        ),
        statistics=statistics,
    )
    assert config.max_trades == 100


def test_usage_catalogs_metrics() -> None:
    """Read the immutable metric catalog."""
    logger.debug("Running Analytics metric-catalog usage")
    assert "trade_count" in METRIC_DEFINITION_CATALOG


def test_usage_catalogs_warnings() -> None:
    """Build catalog-backed warning evidence."""
    logger.debug("Running Analytics warning-catalog usage")
    assert (
        build_warning(
            "stop_loss_absent",
            section="trades",
            source_context="all",
            detail={"ticket": "ticket-1"},
            max_detail_bytes=256,
        ).severity
        == "warning"
    )


def test_usage_catalogs_contract_compatibility() -> None:
    """Classify an accepted producer contract."""
    logger.debug("Running Analytics compatibility-catalog usage")
    assert validate_contract_version("simulation.result", "v1") == "accepted"


def test_usage_catalogs_validate_contract_version() -> None:
    """Invoke the compatibility validator as its public operation."""
    logger.debug("Running Analytics contract-version validation usage")
    assert validate_contract_version("trading.closed_trade_ledger", "v1") == "accepted"


def test_usage_catalogs_validate_metrics() -> None:
    """Validate the approved metric catalog."""
    logger.debug("Running Analytics catalog-validation usage")
    validate_metric_catalog(METRIC_DEFINITION_CATALOG)


def test_usage_evidence_build_warning() -> None:
    """Build warning evidence through the feature API."""
    logger.debug("Running Analytics warning-builder usage")
    assert (
        build_warning(
            "stop_loss_absent",
            section="trades",
            source_context="all",
            detail={"ticket": "ticket-1"},
            max_detail_bytes=256,
        ).affected_section
        == "trades"
    )


def test_usage_evidence_build_quality_flag() -> None:
    """Build quality evidence through the feature API."""
    logger.debug("Running Analytics quality-builder usage")
    assert (
        build_quality_flag(
            "initial_balance_required",
            section="report",
            source_context="adapter",
            detail={"source_contract": "simulation.result"},
            max_detail_bytes=256,
        ).blocker
        is True
    )


def test_usage_evidence_report_json_safe() -> None:
    """Convert report evidence through the Utils serialization boundary."""
    logger.debug("Running Analytics report-serialization usage")
    assert to_report_json_safe({"amount": Decimal("1.25")}) == {"amount": "1.25"}
