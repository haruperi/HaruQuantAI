"""Unit tests for deterministic Analytics metric composition."""

# ruff: noqa: INP001

import json
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.analytics.adapters.results import adapt_trading_result
from app.services.analytics.contracts import RiskFreeRateEvidence
from app.services.analytics.contracts.catalogs import METRIC_DEFINITION_CATALOG
from app.services.analytics.contracts.evidence import to_report_json_safe
from app.services.analytics.metrics.groups import calculate_grouped_evidence
from app.utils import logger
from tests.analytics.unit.test_results_adapter import _config, _source

_GOLDEN_DIRECTORY = Path("tests/analytics/fixtures/golden")


def _assert_golden_value(actual: object, expected: object, tolerance: float) -> None:
    """Compare nested JSON-safe evidence with numeric tolerance.

    Args:
        actual: Actual JSON-safe metric value.
        expected: Fixture-backed expected value.
        tolerance: Absolute numeric tolerance.
    """
    logger.debug("Comparing Analytics metric value with golden evidence")
    if isinstance(expected, dict):
        assert isinstance(actual, dict)
        assert set(actual) == set(expected)
        for key, value in expected.items():
            _assert_golden_value(actual[key], value, tolerance)
        return
    if isinstance(expected, list):
        assert isinstance(actual, (list, tuple))
        assert len(actual) == len(expected)
        for actual_item, expected_item in zip(actual, expected, strict=True):
            _assert_golden_value(actual_item, expected_item, tolerance)
        return
    if isinstance(expected, float):
        assert isinstance(actual, (int, float))
        assert float(actual) == pytest.approx(expected, abs=tolerance)
        return
    assert actual == expected


def test_grouped_evidence_order_is_deterministic() -> None:
    """Grouped evidence follows the documented stable report order."""
    logger.debug("Testing Analytics grouped evidence order")
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
    sections = calculate_grouped_evidence(result, config=config)
    assert tuple(section.section_key for section in sections) == (
        "trades",
        "pnl",
        "equity_returns",
        "drawdown",
        "risk",
        "ratios",
        "benchmark",
        "distribution",
        "cost_efficiency",
        "statistical",
    )


def test_metric_golden_fixtures_are_value_bearing() -> None:
    """Every catalog metric has a scenario, expected status, and expected value."""
    logger.debug("Testing Analytics metric golden fixture completeness")
    fixtures = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in _GOLDEN_DIRECTORY.glob("*.json")
    }
    assert set(fixtures) == set(METRIC_DEFINITION_CATALOG)
    for metric_key, fixture in fixtures.items():
        assert fixture["metric_key"] == metric_key
        assert fixture["fixture_case"]
        assert fixture["expected_status"] in {
            "calculated",
            "undefined",
            "skipped",
        }
        assert isinstance(fixture["absolute_tolerance"], float)
        assert "expected_value" in fixture


def test_canonical_metric_goldens_match_grouped_evidence() -> None:
    """Canonical-ledger fixtures match every emitted canonical metric value."""
    logger.debug("Testing Analytics grouped metrics against golden values")
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
    metrics = {
        metric.metric_key: metric
        for section in calculate_grouped_evidence(result, config=config)
        for metric in section.metrics
        if metric.source_context in {"all", "cost"}
    }
    for path in _GOLDEN_DIRECTORY.glob("*.json"):
        fixture = json.loads(path.read_text(encoding="utf-8"))
        if fixture["fixture_case"] != "canonical_ledger":
            continue
        metric = metrics[path.stem]
        assert metric.status == fixture["expected_status"]
        _assert_golden_value(
            to_report_json_safe(metric.value),
            fixture["expected_value"],
            fixture["absolute_tolerance"],
        )
