"""Unit tests for immutable Analytics contracts."""

# ruff: noqa: INP001

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.analytics.contracts import (
    AnalyticsRunConfig,
    AnalyticsValidationError,
    ClosedTrade,
    DashboardPayload,
    Lineage,
    MetricEvidence,
    PerformanceReport,
    PortfolioAllocationEvidence,
    PortfolioPerformanceReport,
    ReproducibilityHashes,
    RiskFreeRateEvidence,
    SectionEvidence,
    StatisticalValidationConfig,
    TradingResult,
    build_quality_flag,
    build_warning,
)
from app.utils import logger
from pydantic import ValidationError as PydanticValidationError

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def _statistics() -> StatisticalValidationConfig:
    """Return deterministic test statistical settings."""
    logger.debug("Building Analytics test statistical settings")
    return StatisticalValidationConfig(
        seed=7,
        bootstrap_iterations=10,
        permutation_iterations=10,
        confidence=0.95,
        alpha=0.05,
    )


def _config() -> AnalyticsRunConfig:
    """Return complete bounded Analytics test configuration."""
    logger.debug("Building Analytics test runtime configuration")
    return AnalyticsRunConfig(
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
            source="owner-test",
            as_of=NOW,
        ),
        statistics=_statistics(),
    )


def _trade() -> ClosedTrade:
    """Return one canonical closed trade."""
    logger.debug("Building Analytics test closed trade")
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
        swap=Decimal("-0.5"),
        profit=Decimal(10),
        magic="strategy-1",
        mae=Decimal(-3),
        mfe=Decimal(12),
    )


def _lineage() -> Lineage:
    """Return source-backed test lineage."""
    logger.debug("Building Analytics test lineage")
    return Lineage(
        source_contract="simulation.result",
        source_version="v1",
        source_schema_id="simulation.result.v1",
        source_ids=("run-1",),
        configuration_sources=("unit-test",),
        account_currency="USD",
        transformations=("closed_trade_equity",),
    )


def _hashes() -> ReproducibilityHashes:
    """Return valid test reproducibility hashes."""
    logger.debug("Building Analytics test reproducibility hashes")
    return ReproducibilityHashes(
        input_hash="0" * 64,
        configuration_hash="0" * 64,
        trade_ledger_hash="0" * 64,
        equity_curve_hash="0" * 64,
    )


def _metric() -> MetricEvidence:
    """Return one calculated test metric."""
    logger.debug("Building Analytics test metric")
    return MetricEvidence(
        metric_key="trade_count",
        status="calculated",
        value=1,
        unit="count",
    )


def _section() -> SectionEvidence:
    """Return one completed test section."""
    logger.debug("Building Analytics test section")
    return SectionEvidence(
        section_key="trades",
        criticality="required",
        metrics=(_metric(),),
        status="completed",
    )


def _trading_result() -> TradingResult:
    """Return one valid canonical calculation input."""
    logger.debug("Building Analytics test trading result")
    trade = _trade()
    equity = ({"timestamp": NOW, "equity": Decimal("1008.5")},)
    return TradingResult(
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
        equity_curve=equity,
        daily_equity_curve=equity,
        curve_basis="closed_trade",
        benchmark=None,
        fx_evidence=None,
        quality_metadata={},
        source_metadata={},
        lineage=_lineage(),
    )


def _report() -> PerformanceReport:
    """Return one valid non-binding performance report."""
    logger.debug("Building Analytics test performance report")
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


def test_net_trade_pnl_adds_commission_and_swap() -> None:
    """ClosedTrade exposes the exact net PnL convention."""
    logger.debug("Testing Analytics net trade PnL")
    assert _trade().net_trade_pnl == Decimal("8.5")


def test_closed_trade_rejects_non_utc() -> None:
    """Ambiguous timestamps fail the canonical ledger contract."""
    logger.debug("Testing Analytics closed-trade UTC boundary")
    data = _trade().__dict__ | {"entry_time": NOW.replace(tzinfo=None)}
    with pytest.raises(
        (AnalyticsValidationError, PydanticValidationError), match="aware UTC"
    ):
        ClosedTrade(**data)


def test_trading_result_rejects_missing_identity() -> None:
    """Canonical results reject an empty producer identity."""
    logger.debug("Testing Analytics trading-result identity")
    data = _trading_result().__dict__ | {"source_id": ""}
    with pytest.raises(
        (AnalyticsValidationError, PydanticValidationError), match="source_id"
    ):
        TradingResult(**data)


def test_metric_evidence_rejects_infinity() -> None:
    """Calculated metric evidence rejects non-finite values."""
    logger.debug("Testing Analytics metric finite-value policy")
    with pytest.raises(
        (AnalyticsValidationError, PydanticValidationError), match="finite"
    ):
        MetricEvidence(
            metric_key="trade_count",
            status="calculated",
            value=float("inf"),
            unit="count",
        )


def test_section_evidence_requires_reason_when_skipped() -> None:
    """Skipped sections carry an explicit evidence reason."""
    logger.debug("Testing Analytics skipped-section reason")
    with pytest.raises(
        (AnalyticsValidationError, PydanticValidationError), match="requires a reason"
    ):
        SectionEvidence(
            section_key="benchmark",
            criticality="optional",
            metrics=(),
            status="skipped",
        )


def test_warning_uses_cataloged_severity() -> None:
    """Warning construction derives severity from the evidence catalog."""
    logger.debug("Testing Analytics warning catalog severity")
    warning = build_warning(
        "stop_loss_absent",
        section="trades",
        source_context="all",
        detail={"ticket": "ticket-1"},
        max_detail_bytes=256,
    )
    assert warning.severity == "warning"


def test_quality_flag_cannot_claim_governance_decision() -> None:
    """Quality evidence exposes blocker truth but no decision field."""
    logger.debug("Testing Analytics quality governance boundary")
    flag = build_quality_flag(
        "sample_below_threshold",
        section="trades",
        source_context="all",
        detail={"observed_count": 1, "required_count": 30},
        max_detail_bytes=256,
    )
    assert flag.blocker is False
    assert not hasattr(flag, "approved")


def test_lineage_preserves_source_versions() -> None:
    """Lineage retains independent contract and schema identities."""
    logger.debug("Testing Analytics lineage version preservation")
    lineage = _lineage()
    assert lineage.source_version == "v1"
    assert lineage.source_schema_id == "simulation.result.v1"


def test_performance_report_matches_v1_contract() -> None:
    """Performance reports expose the approved v1 non-binding identity."""
    logger.debug("Testing Analytics performance-report v1 contract")
    report = _report()
    assert report.contract_version == "v1"
    assert report.schema_id == "analytics.performance_report.v1"
    assert report.non_binding is True


def test_portfolio_report_requires_fx_lineage() -> None:
    """Portfolio reports cannot omit their FX provenance contract."""
    logger.debug("Testing Analytics portfolio FX lineage requirement")
    with pytest.raises((TypeError, PydanticValidationError)):
        PortfolioPerformanceReport(
            schema_id="analytics.portfolio_performance_report.v1",
            report_id="portfolio-report-1",
            component_report_ids=("report-1",),
            measurement_start=NOW,
            measurement_end=NOW,
            base_currency="USD",
            sections=(_section(),),
            caveats=(),
            quality_flags=(),
            hashes=_hashes(),
        )


def test_dashboard_payload_is_json_safe() -> None:
    """Dashboard contracts reject non-finite nested payload values."""
    logger.debug("Testing Analytics dashboard finite-output boundary")
    with pytest.raises(
        (AnalyticsValidationError, PydanticValidationError), match="finite"
    ):
        DashboardPayload(
            contract_version="v1",
            schema_id="analytics.dashboard_payload.v1",
            payload_id="payload-1",
            report_id="report-1",
            generated_at=NOW,
            sections=({"value": float("inf")},),
            warnings=(),
            quality_flags=(),
            units={},
            truncation_metadata=(),
        )


def test_allocation_evidence_is_non_binding_and_fx_provenanced() -> None:
    """Allocation evidence retains non-binding and FX-lineage truth."""
    logger.debug("Testing Analytics allocation evidence boundary")
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
    assert evidence.fx_lineage.source_contract == "simulation.result"


def test_reproducibility_hashes_require_sha256() -> None:
    """Malformed evidence digests are rejected."""
    logger.debug("Testing Analytics SHA-256 validation")
    with pytest.raises(
        (AnalyticsValidationError, PydanticValidationError), match="SHA-256"
    ):
        ReproducibilityHashes(
            input_hash="bad",
            configuration_hash="0" * 64,
            trade_ledger_hash="0" * 64,
            equity_curve_hash="0" * 64,
        )


def test_runtime_config_requires_every_positive_limit() -> None:
    """Runtime configuration has no missing or non-positive fallback."""
    logger.debug("Testing Analytics required runtime limits")
    data = _config().__dict__ | {"max_trades": 0}
    with pytest.raises(
        (AnalyticsValidationError, PydanticValidationError), match="positive"
    ):
        AnalyticsRunConfig(**data)


def test_runtime_config_bounds_iterations() -> None:
    """Requested statistical iterations cannot exceed activation bounds."""
    logger.debug("Testing Analytics statistical iteration bounds")
    data = _config().__dict__ | {"max_bootstrap_iterations": 5}
    with pytest.raises(
        (AnalyticsValidationError, PydanticValidationError), match="exceed"
    ):
        AnalyticsRunConfig(**data)
