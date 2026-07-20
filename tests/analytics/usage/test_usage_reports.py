"""Runnable usage evidence for the implemented Analytics reporting operations."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256

from app.services.analytics.adapters.results import adapt_trading_result
from app.services.analytics.contracts import (
    AnalyticsRunConfig,
    PerformanceReport,
    PortfolioRebalanceMeasurementRequest,
    RiskFreeRateEvidence,
)
from app.services.analytics.reports.allocation import (
    build_portfolio_allocation_evidence,
    build_portfolio_rebalance_measurement,
)
from app.services.analytics.reports.builder import build_performance_report
from app.services.analytics.reports.comparison import compare_performance_reports
from app.services.analytics.reports.hashes import compute_reproducibility_hashes
from app.services.analytics.reports.portfolio import build_portfolio_performance_report
from app.services.analytics.reports.serialization import serialize_report
from app.utils import canonical_json, generate_id, logger
from tests.analytics.unit.test_results_adapter import _config, _source


def _configured() -> AnalyticsRunConfig:
    """Build fully source-backed reporting configuration.

    Returns:
        Bounded Analytics configuration.
    """
    logger.debug("Building Analytics report usage configuration")
    return replace(
        _config(),
        risk_free_rate=RiskFreeRateEvidence(
            rate=Decimal("0.02"),
            unit="annual_decimal",
            source="usage-fixture",
            as_of=datetime(2026, 7, 19, tzinfo=UTC),
        ),
    )


def _source_with_profit(profit: Decimal) -> dict[str, object]:
    """Build producer-neutral source evidence with controlled gross profit.

    Args:
        profit: Exact gross trade profit.

    Returns:
        Complete source mapping.
    """
    logger.debug("Building Analytics report usage source")
    source = _source()
    row = dict(source["closed_trades"][0])
    row["profit"] = profit
    source["closed_trades"] = (row,)
    return source


def _report(
    *,
    profit: Decimal = Decimal(10),
    account_currency: str = "USD",
    source_id: str = "simulation-result-1",
) -> tuple[PerformanceReport, AnalyticsRunConfig]:
    """Build one complete usage report.

    Args:
        profit: Controlled gross trade profit.
        account_currency: Report currency.
        source_id: Simulation result identity.

    Returns:
        Completed report and its configuration.
    """
    logger.debug("Building Analytics report usage fixture")
    config = _configured()
    source = _source_with_profit(profit)
    source["source_id"] = source_id
    report = build_performance_report(
        source,
        source_contract="simulation.result",
        request_id=generate_id("req"),
        initial_balance=Decimal(1000),
        account_currency=account_currency,
        config=config,
    )
    return report, config


def test_usage_hashes_compute_reproducibility_hashes() -> None:
    """Compute all canonical hashes from an adapted result."""
    logger.info("Running Analytics hash usage")
    config = _configured()
    result = adapt_trading_result(
        _source_with_profit(Decimal(10)),
        source_contract="simulation.result",
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=config,
    )
    assert len(compute_reproducibility_hashes(result).input_hash) == 64


def test_usage_serialization_serialize_report() -> None:
    """Serialize a report to canonical JSON and minimal text."""
    logger.info("Running Analytics serialization usage")
    report, config = _report()
    assert serialize_report(report, format_name="json", config=config).startswith("{")
    assert serialize_report(report, format_name="text", config=config).startswith(
        "PerformanceReport"
    )


def test_usage_portfolio_build_report() -> None:
    """Build an internal same-currency component portfolio report."""
    logger.info("Running Analytics portfolio-report usage")
    first, config = _report()
    second, _ = _report(profit=Decimal(20))
    portfolio = build_portfolio_performance_report(
        (first, second), base_currency="USD", fx_evidence=None, config=config
    )
    assert portfolio.base_currency == "USD"


def test_usage_comparison_compare_reports() -> None:
    """Compare actual common metrics from two compatible reports."""
    logger.info("Running Analytics report-comparison usage")
    reference, _ = _report()
    candidate, _ = _report(profit=Decimal(20))
    assert compare_performance_reports(reference, candidate).metrics


def test_usage_builder_build_performance_report() -> None:
    """Build a complete canonical PerformanceReport v1."""
    logger.info("Running Analytics report-builder usage")
    report, _ = _report()
    assert report.contract_version == "v1"
    assert report.hashes.report_hash is not None


def _portfolio_simulation_result() -> dict[str, object]:
    """Build the exact amended Simulation portfolio-result fixture.

    Returns:
        Complete producer-owned portfolio result mapping.
    """
    logger.debug("Building amended Simulation portfolio result usage fixture")
    start = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)
    end = datetime(2026, 7, 20, 8, 0, tzinfo=UTC)
    observations_one = tuple(
        {
            "timestamp": start + timedelta(minutes=30 * index),
            "return_value": index / 1000,
        }
        for index in range(30)
    )
    observations_two = tuple(
        {
            "timestamp": start + timedelta(minutes=30 * index),
            "return_value": ((index % 7) - 3) / 1000,
        }
        for index in range(30)
    )
    return {
        "contract_version": "v1",
        "schema_id": "simulation.portfolio_result.v1",
        "result_id": "portfolio-result-1",
        "run_id": "portfolio-run-1",
        "request_hash": "a" * 64,
        "config_hash": "b" * 64,
        "data_hash": "c" * 64,
        "result_hash": "d" * 64,
        "engine_version": "v1",
        "status": "completed",
        "portfolio_id": "portfolio-1",
        "construction_result_id": "construction-1",
        "construction_version": "v1",
        "measurement_start": start,
        "measurement_end": end,
        "base_currency": "USD",
        "component_results": (
            {
                "component_id": "component-1",
                "simulation_result_id": "simulation-result-1",
                "journal_ref": "journal-1",
                "metrics_ref": "metrics-1",
                "account_currency": "USD",
                "reconciled": True,
            },
            {
                "component_id": "component-2",
                "simulation_result_id": "simulation-result-2",
                "journal_ref": "journal-2",
                "metrics_ref": "metrics-2",
                "account_currency": "USD",
                "reconciled": True,
            },
        ),
        "component_return_series": (
            {
                "component_id": "component-1",
                "simulation_result_id": "simulation-result-1",
                "observations": observations_one,
            },
            {
                "component_id": "component-2",
                "simulation_result_id": "simulation-result-2",
                "observations": observations_two,
            },
        ),
        "aggregate_journal_ref": "journal-aggregate",
        "aggregate_metrics_ref": "metrics-aggregate",
        "risk_budget_history": (
            {
                "risk_decision_id": "risk-1",
                "component_id": "component-1",
                "effective_at": start,
                "expires_at": end,
                "approved_budget": Decimal(1000),
                "currency": "USD",
            },
        ),
        "fx_evidence_ids": ("identity-USD",),
        "artifact_manifest": {
            "artifacts": (),
            "created_at": end,
            "schema_version": "v1",
        },
    }


def test_usage_allocation_build_evidence() -> None:
    """Build complete non-binding allocation evidence from amended Simulation facts."""
    logger.info("Running Analytics allocation-evidence usage")
    first, config = _report(source_id="simulation-result-1")
    second, _ = _report(profit=Decimal(20), source_id="simulation-result-2")
    evidence = build_portfolio_allocation_evidence(
        (first, second),
        base_currency="USD",
        fx_evidence=None,
        config=config,
        portfolio_simulation_result=_portfolio_simulation_result(),
    )
    assert evidence.non_binding is True
    assert evidence.dependence_evidence.status == "completed"


def _measurement_request() -> PortfolioRebalanceMeasurementRequest:
    """Build one hash-bound request from redacted successful Trading facts.

    Returns:
        Valid deterministic measurement request.
    """
    logger.debug("Building Analytics rebalance measurement usage request")
    facts: dict[str, object] = {
        "status": "success",
        "data": {
            "plan_id": "plan-001",
            "outcomes": ({"action_id": "action-001", "status": "success", "data": {}},),
        },
        "errors": (),
        "warnings": (),
        "audit_metadata": {
            "operation": "execute_portfolio_rebalance",
            "request_id": "trading-request-001",
            "correlation_id": "correlation-001",
            "redaction_applied": True,
        },
    }
    return PortfolioRebalanceMeasurementRequest(
        contract_version="v1",
        schema_id="analytics.portfolio_rebalance_measurement_request.v1",
        request_id="analytics-request-001",
        workflow_id="workflow-001",
        correlation_id="correlation-001",
        portfolio_id="portfolio-001",
        allocation_version="allocation-v1",
        plan_id="plan-001",
        plan_version="v1",
        plan_hash="a" * 64,
        trading_request_id="trading-request-001",
        trading_execution_ref="trading-execution-001",
        trading_execution_hash=sha256(
            canonical_json(facts).encode("utf-8")
        ).hexdigest(),
        trading_facts=facts,
        requested_at=datetime(2026, 7, 19, 9, 0, tzinfo=UTC),
    )


def test_usage_allocation_build_rebalance_measurement() -> None:
    """Build deterministic read-only evidence from immutable Trading facts."""
    logger.info("Running Analytics rebalance measurement usage")
    evidence = build_portfolio_rebalance_measurement(_measurement_request())
    assert evidence.summary["successful_action_count"] == 1
    assert evidence.non_binding is True
