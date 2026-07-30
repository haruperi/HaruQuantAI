"""Focused branch evidence for the function-only Research boundary."""

from dataclasses import make_dataclass

import pytest
from app.services.research import (
    build_default_registry,
    create_research_metric_registry,
    create_research_value,
    execute_research_value_operation,
    get_research_value_field,
    is_research_metric_calculator,
    is_research_value,
    project_research_value,
)


def test_factory_rejects_unknown_types_and_invalid_sequences() -> None:
    """Reject unknown constructors and non-sequence calculator collections."""
    with pytest.raises(TypeError, match="Unknown Research value type"):
        create_research_value("NotRegistered")
    with pytest.raises(TypeError, match="bounded sequence"):
        create_research_metric_registry(object())
    assert is_research_value(object(), "NotRegistered") is False


def test_opaque_value_operations_and_inspection_are_allowlisted() -> None:
    """Exercise operation, field, protocol, and projection guards."""
    registry = build_default_registry()
    assert len(execute_research_value_operation(registry, "all")) == 7
    limits = create_research_value("ResearchResourceLimits", 100, 10.0, 1_024)
    assert get_research_value_field(limits, "max_rows") == 100
    assert is_research_metric_calculator(object()) is False
    assert is_research_value(registry, "MetricRegistry") is True

    with pytest.raises(TypeError, match="operation is unavailable"):
        execute_research_value_operation(registry, "_private")
    with pytest.raises(TypeError, match="operation is unavailable"):
        execute_research_value_operation(registry, "missing")
    with pytest.raises(ValueError, match="does not expose"):
        get_research_value_field(registry, "_private")
    with pytest.raises(TypeError, match="not projectable"):
        project_research_value(object())


def test_projection_is_detached_and_bounded() -> None:
    """Project dataclasses and reject oversized values."""
    value = create_research_value(
        "ResearchResourceLimits",
        100,
        10.0,
        1_024,
    )
    assert project_research_value(value)["max_rows"] == 100

    oversized_type = make_dataclass(
        "Oversized",
        [(f"field_{index}", int) for index in range(65)],
    )
    oversized = oversized_type(*range(65))
    with pytest.raises(ValueError, match="projection is too large"):
        project_research_value(oversized)
