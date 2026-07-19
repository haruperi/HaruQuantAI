"""Unit tests for immutable Analytics catalogs."""

# ruff: noqa: INP001

from types import MappingProxyType

import pytest
from app.services import analytics
from app.services.analytics.contracts import (
    EVIDENCE_CATALOG,
    METRIC_DEFINITION_CATALOG,
    AnalyticsValidationError,
    validate_contract_version,
    validate_metric_catalog,
)
from app.utils import logger


def test_every_contract_metric_is_cataloged() -> None:
    """The approved catalog contains all 60 metric definitions."""
    logger.debug("Testing Analytics metric catalog coverage")
    assert len(METRIC_DEFINITION_CATALOG) == 60
    validate_metric_catalog(METRIC_DEFINITION_CATALOG)


def test_package_root_exports_only_approved_domain_symbols() -> None:
    """The package root exposes owned contracts and one high-level operation."""
    logger.debug("Testing Analytics package-root export boundary")
    assert analytics.__all__ == (
        "AnalyticsRunConfig",
        "DashboardPayload",
        "PerformanceReport",
        "PortfolioAllocationEvidence",
        "RiskFreeRateEvidence",
        "StatisticalValidationConfig",
        "build_performance_report",
    )


def test_warning_and_flag_codes_are_unique() -> None:
    """Warning and quality namespaces never collide."""
    logger.debug("Testing Analytics evidence namespaces")
    assert set(EVIDENCE_CATALOG["warnings"]).isdisjoint(
        EVIDENCE_CATALOG["quality_flags"]
    )


def test_contract_matrix_covers_each_counterparty() -> None:
    """Supported Trading and Simulation versions classify independently."""
    logger.debug("Testing Analytics compatibility catalog")
    assert validate_contract_version("simulation.result", "v1") == "accepted"
    assert (
        validate_contract_version("trading.closed_trade_ledger", "legacy")
        == "legacy-adapted"
    )


def test_validate_metric_catalog_requires_formula_policy() -> None:
    """Incomplete metric definitions fail closed."""
    logger.debug("Testing Analytics metric definition completeness")
    with pytest.raises(AnalyticsValidationError):
        validate_metric_catalog(MappingProxyType({"broken": MappingProxyType({})}))


def test_validate_contract_version_rejects_future() -> None:
    """Unknown future versions are not guessed compatible."""
    logger.debug("Testing Analytics future-version rejection")
    with pytest.raises(AnalyticsValidationError):
        validate_contract_version("simulation.result", "v2")
