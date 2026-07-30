"""Function-only construction and inspection boundary for Research values."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from typing import Any

from app.services.research.contracts import configurations as _configurations
from app.services.research.contracts import results as _results
from app.services.research.metrics import registry as _metrics
from app.services.research.seasonality import analysis as _seasonality

_MODULES = (_configurations, _results, _metrics, _seasonality)
_MAX_PROJECTED_FIELDS = 64


def _model(value_type: str) -> type[Any]:
    """Resolve one registered internal Research value type.

    Args:
        value_type: Exact internal type name.

    Returns:
        Registered internal model class.

    Raises:
        TypeError: If the type name is not registered.
    """
    for module in _MODULES:
        candidate = getattr(module, value_type, None)
        if isinstance(candidate, type):
            return candidate
    message = f"Unknown Research value type: {value_type}"
    raise TypeError(message)


def create_research_value(
    value_type: str, /, *args: object, **values: object
) -> object:
    """Construct one registered opaque Research value.

    Args:
        value_type: Exact internal Research value name.
        *args: Positional constructor values retained for concise numerical usage.
        **values: Named constructor values.

    Returns:
        Opaque validated Research value.

    Raises:
        TypeError: If the value type is unavailable.
    """
    return _model(value_type)(*args, **values)


def create_research_metric_registry(calculators: object) -> object:
    """Construct one isolated opaque metric registry.

    Args:
        calculators: Iterable of internal calculator protocol implementations.

    Returns:
        Opaque isolated metric registry.

    Raises:
        TypeError: If calculators is not iterable.
    """
    if not isinstance(calculators, tuple | list):
        raise TypeError("Research calculators must be a bounded sequence")
    return _metrics.MetricRegistry.from_calculators(calculators)


def execute_research_value_operation(
    value: object,
    operation: str,
    /,
    *args: object,
    **kwargs: object,
) -> object:
    """Execute one allowlisted operation on an opaque Research value.

    Returns:
        Operation result.

    Raises:
        TypeError: If the operation is private or unavailable.
    """
    if not operation or operation.startswith("_"):
        raise TypeError("Research value operation is unavailable")
    method = getattr(value, operation, None)
    if not callable(method):
        raise TypeError("Research value operation is unavailable")
    return method(*args, **kwargs)


def get_research_value_field(value: object, field: str) -> object:
    """Return one public field from an opaque Research value.

    Raises:
        ValueError: If the field is private or unavailable.
    """
    if not field or field.startswith("_") or not hasattr(value, field):
        raise ValueError("Research value does not expose the requested field")
    return getattr(value, field)


def is_research_metric_calculator(value: object) -> bool:
    """Return whether a value satisfies the Research calculator protocol."""
    return isinstance(value, _metrics.MetricCalculator)


def is_research_value(value: object, value_type: str) -> bool:
    """Return whether a value is one registered internal Research type."""
    try:
        model = _model(value_type)
    except TypeError:
        return False
    return isinstance(value, model)


def project_research_value(value: object) -> Mapping[str, object]:
    """Return a detached bounded mapping for one dataclass Research value.

    Raises:
        TypeError: If the value is not a registered dataclass contract.
        ValueError: If the detached projection is oversized.
    """
    if not is_dataclass(value) or isinstance(value, type):
        raise TypeError("Research value is not projectable")
    projected = asdict(value)
    if len(projected) > _MAX_PROJECTED_FIELDS:
        raise ValueError("Research value projection is too large")
    return projected


__all__ = (
    "create_research_metric_registry",
    "create_research_value",
    "execute_research_value_operation",
    "get_research_value_field",
    "is_research_metric_calculator",
    "is_research_value",
    "project_research_value",
)
