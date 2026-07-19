"""Workflow integration evidence for portfolio allocation Analytics."""

# ruff: noqa: INP001

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.analytics import (
    build_portfolio_allocation_evidence as public_build_portfolio_allocation_evidence,
)
from app.services.analytics import (
    build_portfolio_rebalance_measurement as public_build_rebalance_measurement,
)
from app.services.analytics.reports.allocation import (
    build_portfolio_allocation_evidence,
    build_portfolio_rebalance_measurement,
)
from app.utils import logger
from tests.analytics.usage.test_usage_reports import _report


def test_allocation_evidence_builder_is_package_root_public() -> None:
    """Expose the registered allocation projector through Analytics' public port."""
    logger.info("Testing Analytics package-root allocation projector export")
    assert (
        public_build_portfolio_allocation_evidence
        is build_portfolio_allocation_evidence
    )


def test_rebalance_measurement_builder_is_package_root_public() -> None:
    """Expose post-trade measurement through Analytics' public domain port."""
    logger.info("Testing Analytics package-root rebalance measurement export")
    assert public_build_rebalance_measurement is build_portfolio_rebalance_measurement


_FIXTURE = Path("tests/analytics/fixtures/portfolio_simulation_result.json")
_GOLDEN_DIRECTORY = Path("tests/analytics/fixtures/golden")


def _portfolio_fixture() -> dict[str, object]:
    """Load and type the exact README-backed Simulation portfolio fixture.

    Returns:
        Portfolio result mapping with UTC datetime evidence.
    """
    logger.debug("Loading exact portfolio Simulation integration fixture")
    fixture = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    fixture["measurement_start"] = datetime.fromisoformat(fixture["measurement_start"])
    fixture["measurement_end"] = datetime.fromisoformat(fixture["measurement_end"])
    for row in fixture["component_return_series"]:
        for observation in row["observations"]:
            observation["timestamp"] = datetime.fromisoformat(observation["timestamp"])
    return fixture


def _golden(metric_key: str) -> dict[str, object]:
    """Load one allocation metric golden fixture.

    Args:
        metric_key: Catalog metric identity.

    Returns:
        Decoded expected metric evidence.
    """
    logger.debug("Loading Analytics allocation metric golden fixture")
    path = _GOLDEN_DIRECTORY / f"{metric_key}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_evidence_is_non_binding_and_fx_provenanced() -> None:
    """The complete workflow remains non-binding with explicit currency lineage."""
    logger.debug("Testing Analytics allocation-evidence workflow")
    first, config = _report(source_id="simulation-result-1")
    second, _ = _report(profit=Decimal(20), source_id="simulation-result-2")
    evidence = build_portfolio_allocation_evidence(
        (first, second),
        base_currency="USD",
        fx_evidence=None,
        config=config,
        portfolio_simulation_result=_portfolio_fixture(),
    )
    assert evidence.non_binding is True
    assert evidence.fx_lineage.source_contract == "identity_currency"
    for metric in (
        *evidence.dependence_evidence.metrics,
        *evidence.concentration_evidence.metrics,
    ):
        fixture = _golden(metric.metric_key)
        assert metric.status == fixture["expected_status"]
        assert float(metric.value) == pytest.approx(
            fixture["expected_value"],
            abs=fixture["absolute_tolerance"],
        )
