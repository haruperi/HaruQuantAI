"""Unit tests for closed-trade drawdown evidence."""

# ruff: noqa: INP001

import json
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.analytics.adapters.results import adapt_trading_result
from app.services.analytics.metrics.drawdowns import calculate_drawdown_evidence
from app.utils import logger
from tests.analytics.unit.test_results_adapter import _config, _source

GOLDEN = Path("tests/analytics/fixtures/golden/max_drawdown.json")


def test_drawdown_evidence_matches_golden_fixture() -> None:
    """Maximum closed-trade drawdown matches its cataloged formula fixture."""
    logger.debug("Testing Analytics drawdown golden formula")
    source = _source()
    row = dict(source["closed_trades"][0])
    row.update({"profit": Decimal(-100), "commission": Decimal(0)})
    source["closed_trades"] = (row,)
    result = adapt_trading_result(
        source,
        source_contract="simulation.result",
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=_config(),
    )
    section = calculate_drawdown_evidence(result)
    metric = next(item for item in section.metrics if item.metric_key == "max_drawdown")
    fixture = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert metric.metric_key == fixture["metric_key"]
    assert float(metric.value) == pytest.approx(
        fixture["expected_value"], abs=fixture["absolute_tolerance"]
    )
    assert metric.status == fixture["expected_status"]
    assert section.status == "degraded"
