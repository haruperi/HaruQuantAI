"""Unit tests for complete Analytics allocation projection."""

from dataclasses import replace
from decimal import Decimal

import pytest
from app.composition.logging import get_logger
from app.services.analytics.contracts import AnalyticsValidationError
from app.services.analytics.reports.allocation import (
    _correlation,
    _require_mapping,
    _require_sequence,
    _validated_component_pairs,
    build_portfolio_allocation_evidence,
    build_portfolio_rebalance_measurement,
)

logger = get_logger(__name__)

from tests.analytics._support import (  # noqa: E402
    _measurement_request,
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


def test_rebalance_measurement_is_deterministic_and_hash_bound() -> None:
    """The same immutable Trading facts produce exactly the same evidence."""
    logger.debug("Testing deterministic Analytics rebalance measurement")
    request = _measurement_request()
    first = build_portfolio_rebalance_measurement(request)
    second = build_portfolio_rebalance_measurement(request)
    assert first == second
    assert first.trading_execution_hash == request.trading_execution_hash


def test_rebalance_measurement_rejects_tampered_execution_hash() -> None:
    """A digest that does not match Trading facts blocks measurement."""
    logger.debug("Testing Analytics rebalance measurement tamper detection")
    with pytest.raises(ValueError, match="hash does not match"):
        replace(_measurement_request(), trading_execution_hash="b" * 64)


def test_allocation_validators_fail_closed_on_malformed_shapes() -> None:
    """Reject non-collection inputs, duplicate components, and weak returns."""
    with pytest.raises(AnalyticsValidationError, match="sequence"):
        _require_sequence("not-a-sequence", "rows")
    with pytest.raises(AnalyticsValidationError, match="mapping"):
        _require_mapping([], "row")
    malformed = ({"component_id": "only-one-field"},)
    with pytest.raises(AnalyticsValidationError, match="component row"):
        _validated_component_pairs(malformed)
    with pytest.raises(AnalyticsValidationError, match="too short"):
        _correlation((1.0,), (1.0,))
    with pytest.raises(AnalyticsValidationError, match="variance"):
        _correlation((1.0,) * 30, (2.0,) * 30)
