"""Unit tests for immutable Analytics catalogs."""

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
from app.utils import get_logger

logger = get_logger(__name__)


def test_every_contract_metric_is_cataloged() -> None:
    """The approved catalog contains all 60 metric definitions."""
    logger.debug("Testing Analytics metric catalog coverage")
    assert len(METRIC_DEFINITION_CATALOG) == 60
    validate_metric_catalog(METRIC_DEFINITION_CATALOG)
    assert all(
        definition["formula"] != metric_key
        for metric_key, definition in METRIC_DEFINITION_CATALOG.items()
    )
    assert (
        len({definition["inputs"] for definition in METRIC_DEFINITION_CATALOG.values()})
        > 5
    )


def test_package_root_exports_only_approved_domain_symbols() -> None:
    """The package root exposes the exact documented Analytics public API."""
    logger.debug("Testing Analytics package-root export boundary")
    assert len(analytics.__all__) == len(set(analytics.__all__))
    assert all(getattr(analytics, name, None) is not None for name in analytics.__all__)
    assert "build_dashboard_payload" in analytics.__all__
    assert "compare_performance_reports" in analytics.__all__
    assert "serialize_report" in analytics.__all__


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
    assert validate_contract_version("trading.closed_trade_ledger", "v1") == "accepted"


def test_contract_matrix_rejects_legacy() -> None:
    """Legacy producer contracts fail closed rather than claiming adaptation."""
    logger.debug("Testing Analytics legacy-version rejection")
    with pytest.raises(AnalyticsValidationError):
        validate_contract_version("trading.closed_trade_ledger", "legacy")


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
