"""Unit tests for Analytics benchmark evidence."""

# ruff: noqa: INP001

import json
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from app.services.analytics.adapters.results import adapt_trading_result
from app.services.analytics.contracts import RiskFreeRateEvidence
from app.services.analytics.metrics.benchmarks import (
    align_benchmark_series,
    calculate_benchmark_evidence,
)
from app.utils import logger
from tests.analytics.unit.test_results_adapter import _config, _source

NOW = datetime(2026, 7, 19, tzinfo=UTC)
_GOLDEN_DIRECTORY = Path("tests/analytics/fixtures/golden")


def test_align_benchmark_series_uses_timestamp_intersection() -> None:
    """Only matching UTC timestamps enter benchmark calculations."""
    logger.debug("Testing Analytics benchmark timestamp intersection")
    strategy = (
        {"timestamp": NOW, "value": 0.1},
        {"timestamp": NOW.replace(day=20), "value": 0.2},
    )
    benchmark = ({"timestamp": NOW.replace(day=20), "value": 0.3},)
    assert align_benchmark_series(strategy, benchmark) == ((0.2,), (0.3,))


def test_benchmark_zero_variance_is_undefined() -> None:
    """A constant benchmark yields explicit undefined relative evidence."""
    logger.debug("Testing Analytics zero-variance benchmark")
    config = replace(
        _config(),
        risk_free_rate=RiskFreeRateEvidence(
            rate=Decimal(0),
            unit="annual_decimal",
            source="unit-test",
            as_of=NOW,
        ),
    )
    benchmark = {
        "currency": "USD",
        "points": ({"timestamp": NOW, "value": 0.01},),
    }
    result = adapt_trading_result(
        _source(),
        source_contract="simulation.result",
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=config,
        benchmark=benchmark,
    )
    section = calculate_benchmark_evidence(result, config=config)
    metrics = {item.metric_key: item for item in section.metrics}
    for metric_key, metric in metrics.items():
        fixture = json.loads(
            (_GOLDEN_DIRECTORY / f"{metric_key}.json").read_text(encoding="utf-8")
        )
        assert metric.status == fixture["expected_status"]
        assert metric.value == fixture["expected_value"]
