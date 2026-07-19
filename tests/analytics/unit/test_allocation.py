"""Unit tests for complete Analytics allocation projection."""

# ruff: noqa: INP001

from decimal import Decimal

import pytest
from app.services.analytics.contracts import AnalyticsValidationError
from app.services.analytics.reports.allocation import (
    build_portfolio_allocation_evidence,
)
from app.utils import logger
from tests.analytics.usage.test_usage_reports import (
    _portfolio_simulation_result,
    _report,
)


def test_allocation_evidence_blocks_without_fx() -> None:
    """Mixed-currency allocation evidence fails with no Data-owned FX mapping."""
    logger.debug("Testing Analytics allocation FX blocker")
    usd, config = _report(source_id="simulation-result-1")
    eur, _ = _report(
        profit=Decimal(20),
        account_currency="EUR",
        source_id="simulation-result-2",
    )
    portfolio_result = _portfolio_simulation_result()
    portfolio_result["component_results"] = tuple(
        {
            **row,
            "account_currency": (
                "EUR" if row["simulation_result_id"] == "simulation-result-2" else "USD"
            ),
        }
        for row in portfolio_result["component_results"]
    )
    with pytest.raises(AnalyticsValidationError, match="FX"):
        build_portfolio_allocation_evidence(
            (usd, eur),
            base_currency="USD",
            fx_evidence=None,
            config=config,
            portfolio_simulation_result=portfolio_result,
        )


def test_allocation_evidence_calculates_dependence_and_concentration() -> None:
    """Complete same-currency evidence contains actual correlation and HHI."""
    logger.debug("Testing Analytics allocation metric projection")
    first, config = _report(source_id="simulation-result-1")
    second, _ = _report(profit=Decimal(20), source_id="simulation-result-2")
    evidence = build_portfolio_allocation_evidence(
        (first, second),
        base_currency="USD",
        fx_evidence=None,
        config=config,
        portfolio_simulation_result=_portfolio_simulation_result(),
    )
    assert evidence.dependence_evidence.metrics[0].metric_key == (
        "component_return_correlation"
    )
    assert evidence.concentration_evidence.metrics[0].value == pytest.approx(0.5)


def test_allocation_evidence_rejects_malformed_producer_hash() -> None:
    """A length-correct non-hex producer digest fails exact schema validation."""
    logger.debug("Testing Analytics allocation producer hash validation")
    first, config = _report(source_id="simulation-result-1")
    second, _ = _report(profit=Decimal(20), source_id="simulation-result-2")
    portfolio_result = _portfolio_simulation_result()
    portfolio_result["request_hash"] = "z" * 64
    with pytest.raises(AnalyticsValidationError, match="hash"):
        build_portfolio_allocation_evidence(
            (first, second),
            base_currency="USD",
            fx_evidence=None,
            config=config,
            portfolio_simulation_result=portfolio_result,
        )
