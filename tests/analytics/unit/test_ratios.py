"""Unit tests for core Analytics ratios."""

# ruff: noqa: INP001

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

from app.services.analytics.adapters.results import adapt_trading_result
from app.services.analytics.contracts import RiskFreeRateEvidence
from app.services.analytics.metrics.ratios import calculate_ratio_evidence
from app.utils import logger
from tests.analytics.unit.test_results_adapter import _config, _source


def test_ratio_evidence_never_returns_infinity() -> None:
    """Zero denominators produce undefined evidence and never infinity."""
    logger.debug("Testing Analytics ratio zero denominators")
    config = replace(
        _config(),
        risk_free_rate=RiskFreeRateEvidence(
            rate=Decimal(0),
            unit="annual_decimal",
            source="unit-test",
            as_of=datetime(2026, 7, 19, tzinfo=UTC),
        ),
    )
    result = adapt_trading_result(
        _source(),
        source_contract="simulation.result",
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=config,
    )
    section = calculate_ratio_evidence(result, (0.01, 0.01), config=config)
    metrics = {item.metric_key: item for item in section.metrics}
    assert metrics["sharpe_ratio"].status == "undefined"
    assert metrics["profit_factor"].status == "undefined"
    assert metrics["expectancy"].value == 9.0
