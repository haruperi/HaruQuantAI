"""Approved public Core API: contracts, results, registry, and validation."""

from importlib import import_module as _import_module
from typing import TYPE_CHECKING as _TYPE_CHECKING

from app.services.indicators.core.errors import IndicatorError, IndicatorErrorCode

if _TYPE_CHECKING:
    from app.services.indicators.core.contracts import (
        IndicatorConfig,
        IndicatorProtocol,
        IndicatorSpec,
        WarmupRequirement,
    )
    from app.services.indicators.core.registry import (
        get_capability_matrix,
        get_indicator,
        list_indicators,
    )
    from app.services.indicators.core.results import IndicatorManifest, IndicatorResult
    from app.services.indicators.core.validation import (
        get_warmup_requirement,
        validate_indicator,
    )

_LAZY_EXPORTS = {
    "IndicatorConfig": "app.services.indicators.core.contracts",
    "IndicatorManifest": "app.services.indicators.core.results",
    "IndicatorProtocol": "app.services.indicators.core.contracts",
    "IndicatorResult": "app.services.indicators.core.results",
    "IndicatorSpec": "app.services.indicators.core.contracts",
    "WarmupRequirement": "app.services.indicators.core.contracts",
    "get_capability_matrix": "app.services.indicators.core.registry",
    "get_indicator": "app.services.indicators.core.registry",
    "get_warmup_requirement": "app.services.indicators.core.validation",
    "list_indicators": "app.services.indicators.core.registry",
    "validate_indicator": "app.services.indicators.core.validation",
}


def __getattr__(name: str) -> object:
    """Resolve and cache one explicitly registered Core public export.

    Args:
        name: Requested public attribute name.

    Returns:
        The registered public export.

    Raises:
        AttributeError: If the name is not registered.
    """
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        message = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(message)
    value = getattr(_import_module(module_name), name)
    globals()[name] = value
    return value


__all__ = (
    "IndicatorConfig",
    "IndicatorError",
    "IndicatorErrorCode",
    "IndicatorManifest",
    "IndicatorProtocol",
    "IndicatorResult",
    "IndicatorSpec",
    "WarmupRequirement",
    "get_capability_matrix",
    "get_indicator",
    "get_warmup_requirement",
    "list_indicators",
    "validate_indicator",
)
