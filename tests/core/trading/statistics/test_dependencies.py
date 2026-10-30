"""Tests for metric dependency graph ordering."""

import pytest
from app.core.lib.errors import DomainError
from app.core.trading.statistics.dependencies import MetricDependency, order_metrics


def test_stable_multi_pass_order() -> None:
    """Multi-pass scanning resolves dependencies in topological order."""
    b = MetricDependency("B", depends_on=("A",))
    c = MetricDependency("C")
    a = MetricDependency("A")

    result = order_metrics([b, c, a])
    assert result == (c, a, b)


def test_same_pass_dependencies() -> None:
    """Dependencies appended earlier in the same pass are immediately visible."""
    a = MetricDependency("A")
    b = MetricDependency("B", depends_on=("A",))
    c = MetricDependency("C", depends_on=("B",))

    result = order_metrics([a, b, c])
    assert result == (a, b, c)


def test_empty_registry() -> None:
    """Empty input yields an empty tuple."""
    assert order_metrics([]) == ()


def test_dependency_cycle() -> None:
    """Mutually dependent metrics raise unresolved error with pending IDs."""
    a = MetricDependency("A", depends_on=("B",))
    b = MetricDependency("B", depends_on=("A",))

    with pytest.raises(DomainError) as exc_info:
        order_metrics([a, b])

    err = exc_info.value
    assert err.code == "UNRESOLVED_METRIC_DEPENDENCY"
    assert err.message == "Metric dependencies cannot be resolved"
    assert err.details == {"pending_ids": ["A", "B"]}


def test_missing_dependency() -> None:
    """A missing dependency raises unresolved error with pending IDs."""
    b = MetricDependency("B", depends_on=("Missing",))

    with pytest.raises(DomainError) as exc_info:
        order_metrics([b])

    err = exc_info.value
    assert err.code == "UNRESOLVED_METRIC_DEPENDENCY"
    assert err.message == "Metric dependencies cannot be resolved"
    assert err.details == {"pending_ids": ["B"]}


def test_duplicate_id() -> None:
    """Duplicate metric identifiers raise invalid registry error."""
    a1 = MetricDependency("A")
    a2 = MetricDependency("A")

    with pytest.raises(DomainError) as exc_info:
        order_metrics([a1, a2])

    err = exc_info.value
    assert err.code == "INVALID_METRIC_REGISTRY"
    assert err.message == "Metric identifiers must be unique and non-empty"


def test_empty_id() -> None:
    """Empty metric identifier raises invalid registry error."""
    empty = MetricDependency("")

    with pytest.raises(DomainError) as exc_info:
        order_metrics([empty])

    err = exc_info.value
    assert err.code == "INVALID_METRIC_REGISTRY"
    assert err.message == "Metric identifiers must be unique and non-empty"


def test_unchanged_inputs() -> None:
    """Input sequence and objects are never mutated on success or failure."""
    b = MetricDependency("B", depends_on=("A",))
    c = MetricDependency("C")
    a = MetricDependency("A")
    success_input = [b, c, a]

    order_metrics(success_input)
    assert success_input == [b, c, a]

    cycle_a = MetricDependency("A", depends_on=("B",))
    cycle_b = MetricDependency("B", depends_on=("A",))
    failure_input = [cycle_a, cycle_b]

    with pytest.raises(DomainError):
        order_metrics(failure_input)

    assert failure_input == [cycle_a, cycle_b]
