"""Shared test support helpers for Analytics tests."""

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
    StatisticalValidationConfig,
    TradingResult,
)
from app.services.analytics.reports.builder import build_performance_report
from app.utils import canonical_json, generate_id, logger

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)


def _config() -> AnalyticsRunConfig:
    """Build default analytics run config."""
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
            source="usage-fixture",
            as_of=NOW,
        ),
        statistics=StatisticalValidationConfig(
            seed=1,
            bootstrap_iterations=10,
            permutation_iterations=10,
            confidence=0.95,
            alpha=0.05,
        ),
    )


def _configured() -> AnalyticsRunConfig:
    """Build fully source-backed reporting configuration."""
    return replace(
        _config(),
        risk_free_rate=RiskFreeRateEvidence(
            rate=Decimal("0.02"),
            unit="annual_decimal",
            source="usage-fixture",
            as_of=NOW,
        ),
    )


def _source_with_profit(profit: Decimal = Decimal(10)) -> dict[str, object]:
    """Build producer-neutral source evidence."""
    return {
        "contract_version": "v1",
        "schema_id": "simulation.result.v1",
        "source_id": "simulation-result-1",
        "phase": "backtest",
        "window_start": NOW,
        "window_end": NOW + timedelta(days=1),
        "strategy_id": "strategy-1",
        "strategy_version": "v1",
        "symbols": ("EURUSD",),
        "timeframe": "M1",
        "closed_trades": (
            {
                "ticket": "ticket-1",
                "symbol": "EURUSD",
                "type": "BUY",
                "volume": Decimal(1),
                "entry_time": NOW,
                "entry_price": Decimal("1.10"),
                "stop_loss": Decimal("1.09"),
                "take_profit": Decimal("1.12"),
                "exit_time": NOW,
                "exit_price": Decimal("1.11"),
                "comment": "closed",
                "commission": Decimal(-1),
                "swap": Decimal(0),
                "profit": profit,
                "magic": "strategy-1",
                "mae": Decimal(-2),
                "mfe": Decimal(12),
            },
        ),
        "quality_metadata": {},
        "source_metadata": {},
    }


def _source() -> dict[str, object]:
    """Build default producer-neutral source dict."""
    return _source_with_profit(Decimal(10))


def _report(
    *,
    profit: Decimal = Decimal(10),
    account_currency: str = "USD",
    source_id: str = "simulation-result-1",
    request_id: str | None = None,
) -> tuple[PerformanceReport, AnalyticsRunConfig]:
    """Build one complete usage/unit report."""
    config = _configured()
    source = _source_with_profit(profit)
    source["source_id"] = source_id
    report = build_performance_report(
        source,
        source_contract="simulation.result",
        request_id=request_id or generate_id("req"),
        initial_balance=Decimal(1000),
        account_currency=account_currency,
        config=config,
    )
    return report, config


def _configured_result(
    *, benchmark: bool = False
) -> tuple[TradingResult, AnalyticsRunConfig]:
    """Build a canonical result and fully source-backed metric configuration.

    Args:
        benchmark: Whether to include aligned benchmark evidence.

    Returns:
        Canonical result and Analytics run configuration.
    """
    logger.debug("Building Analytics metric usage evidence")
    config = replace(
        _config(),
        risk_free_rate=RiskFreeRateEvidence(
            rate=Decimal("0.02"),
            unit="annual_decimal",
            source="usage-fixture",
            as_of=NOW,
        ),
    )
    benchmark_evidence = (
        {
            "currency": "USD",
            "points": (
                {
                    "timestamp": NOW.replace(hour=0, minute=0, second=0, microsecond=0),
                    "value": 0.01,
                },
            ),
        }
        if benchmark
        else None
    )
    result = adapt_trading_result(
        _source(),
        source_contract="simulation.result",
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=config,
        benchmark=benchmark_evidence,
    )
    return result, config


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
