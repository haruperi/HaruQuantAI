"""Unit tests for the analytics metric definition catalog and validations."""

from __future__ import annotations

import pytest
from app.services.analytics.contracts.metric_catalog import (
    DECIMAL_PRECISION_POLICY,
    METRIC_DEFINITION_CATALOG,
    OFFICIAL_ANALYTICS_TOOL_CATALOG,
    SCHEMA_COMPATIBILITY_MATRIX,
    WARNING_SEVERITY_LEVELS,
    get_metric_definition,
    validate_metric_catalog,
)
from app.services.analytics.contracts.models import (
    MetricDefinition,
    MetricResult,
)
from app.services.analytics.errors import AnalyticsValidationError as ValidationError


def test_precision_and_severity_policies() -> None:
    """Test standard precision strings and severity levels are present."""
    assert len(DECIMAL_PRECISION_POLICY) > 0
    assert "derived_ratio_tolerance" in DECIMAL_PRECISION_POLICY
    assert "informational" in WARNING_SEVERITY_LEVELS
    assert "blocker" in WARNING_SEVERITY_LEVELS
    assert "1.3.1" in SCHEMA_COMPATIBILITY_MATRIX


def test_metric_result_generic_usage() -> None:
    """Test MetricResult type wraps values and supports custom attributes."""
    res_float = MetricResult[float](value=1.5, confidence="normal")
    assert res_float.value == 1.5
    assert res_float.confidence == "normal"
    assert res_float.warnings == ()

    res_none = MetricResult[str](
        value=None,
        confidence="degraded",
        warnings=({"code": "WARN"},),
    )
    assert res_none.value is None
    assert res_none.confidence == "degraded"
    assert len(res_none.warnings) == 1
    assert res_none.warnings[0]["code"] == "WARN"


def test_get_metric_definition_success() -> None:
    """Test retrieving valid metrics from the catalog."""
    definition = get_metric_definition("total_return")
    assert definition.name == "total_return"
    assert definition.units == "percent"
    assert "equity_curve" in definition.required_inputs
    assert definition.minimum_sample_size == 2


def test_get_metric_definition_failure() -> None:
    """Test retrieving invalid/unknown metrics raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        get_metric_definition("fabricated_nonexistent_metric")
    assert "Unknown or uncataloged metric" in str(exc_info.value)


def test_validate_official_catalog_passes() -> None:
    """Test that the main production catalog passes integrity validation checks."""
    result = validate_metric_catalog()
    assert result["status"] == "valid"
    assert result["metric_count"] == len(METRIC_DEFINITION_CATALOG)
    assert "total_return" in result["metrics"]


def test_validate_metric_catalog_edge_cases() -> None:
    """Test various validation failure states for catalog mappings."""
    # Test empty catalog
    with pytest.raises(ValidationError) as exc_info:
        validate_metric_catalog({})
    assert "must be non-empty" in str(exc_info.value)

    # Test wrong catalog type
    with pytest.raises(ValidationError) as exc_info:
        validate_metric_catalog([1, 2, 3])  # type: ignore[arg-type]
    assert "must be a Mapping or dictionary" in str(exc_info.value)

    # Test key mismatch
    bad_catalog = {
        "mismatched_key": MetricDefinition(
            name="different_name",
            formula="x + y",
            units="scalar",
            required_inputs=("x",),
        )
    }
    with pytest.raises(ValidationError) as exc_info:
        validate_metric_catalog(bad_catalog)
    assert "key mismatch" in str(exc_info.value)

    # Test empty formula
    empty_formula_catalog = {
        "metric_a": MetricDefinition(
            name="metric_a",
            formula="",
            units="scalar",
            required_inputs=("x",),
        )
    }
    with pytest.raises(ValidationError) as exc_info:
        validate_metric_catalog(empty_formula_catalog)
    assert "must define a formula" in str(exc_info.value)

    # Test empty required inputs
    empty_inputs_catalog = {
        "metric_a": MetricDefinition(
            name="metric_a",
            formula="x + 1",
            units="scalar",
            required_inputs=(),
        )
    }
    with pytest.raises(ValidationError) as exc_info:
        validate_metric_catalog(empty_inputs_catalog)
    assert "must define required inputs" in str(exc_info.value)

    # Test negative minimum sample size
    negative_sample_catalog = {
        "metric_a": MetricDefinition(
            name="metric_a",
            formula="x + 1",
            units="scalar",
            required_inputs=("x",),
            minimum_sample_size=-5,
        )
    }
    with pytest.raises(ValidationError) as exc_info:
        validate_metric_catalog(negative_sample_catalog)
    assert "must not use a negative minimum sample size" in str(exc_info.value)

    # Test non-MetricDefinition object
    invalid_object_catalog = {"metric_a": {"not": "a_metric_definition"}}
    with pytest.raises(ValidationError) as exc_info:
        validate_metric_catalog(invalid_object_catalog)  # type: ignore[arg-type]
    assert "is invalid" in str(exc_info.value)


def test_official_tools_catalog() -> None:
    """Test properties of the official tools catalog."""
    assert "build_analytics_report" in OFFICIAL_ANALYTICS_TOOL_CATALOG
    tool = OFFICIAL_ANALYTICS_TOOL_CATALOG["build_analytics_report"]
    assert tool.name == "build_analytics_report"
    assert tool.stability == "stable"
    assert tool.agent_api_safe is True
    assert "tests/analytics/unit/test_report.py" in tool.tests
