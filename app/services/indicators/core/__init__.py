"""Approved public Core API: contracts, results, registry, and validation."""

from app.services.indicators.core.contracts import (
    IndicatorConfig,
    IndicatorProtocol,
    IndicatorSpec,
    WarmupRequirement,
)
from app.services.indicators.core.errors import IndicatorError, IndicatorErrorCode
from app.services.indicators.core.registry import (
    get_capability_matrix,
    get_indicator,
    list_indicators,
)
from app.services.indicators.core.results import IndicatorManifest, IndicatorResult
from app.services.indicators.core.validation import validate_indicator

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
    "list_indicators",
    "validate_indicator",
)
