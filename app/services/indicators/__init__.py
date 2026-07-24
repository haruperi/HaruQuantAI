"""Public Indicators domain port.

Re-exports the approved Core contracts/registry API plus the twenty-one official
built-in indicator convenience functions. This package root is the only
documented stable import surface; leaf modules are internal implementation
detail and are not part of the public contract.
"""

from importlib import import_module as _import_module
from typing import TYPE_CHECKING as _TYPE_CHECKING

from app.services.indicators.core import IndicatorError, IndicatorErrorCode

if _TYPE_CHECKING:
    from app.services.indicators.candles import doji, engulfing, inside_bar, pinbar
    from app.services.indicators.core import (
        IndicatorConfig,
        IndicatorManifest,
        IndicatorProtocol,
        IndicatorResult,
        IndicatorSpec,
        WarmupRequirement,
        get_capability_matrix,
        get_indicator,
        get_warmup_requirement,
        list_indicators,
        validate_indicator,
    )
    from app.services.indicators.momentum import rsi, williams_r
    from app.services.indicators.trend import (
        adx,
        bollinger_bands,
        ema,
        hull_ma,
        sma,
        wma,
        zigzag,
    )
    from app.services.indicators.volatility import (
        adr,
        atr,
        rolling_volatility,
        standard_deviation,
    )
    from app.services.indicators.volume import (
        cmf,
        mfi,
        obv,
        price_volume_distribution,
    )

_LAZY_EXPORTS = {
    "IndicatorConfig": "app.services.indicators.core",
    "IndicatorManifest": "app.services.indicators.core",
    "IndicatorProtocol": "app.services.indicators.core",
    "IndicatorResult": "app.services.indicators.core",
    "IndicatorSpec": "app.services.indicators.core",
    "WarmupRequirement": "app.services.indicators.core",
    "adr": "app.services.indicators.volatility",
    "adx": "app.services.indicators.trend",
    "atr": "app.services.indicators.volatility",
    "bollinger_bands": "app.services.indicators.trend",
    "cmf": "app.services.indicators.volume",
    "doji": "app.services.indicators.candles",
    "ema": "app.services.indicators.trend",
    "engulfing": "app.services.indicators.candles",
    "get_capability_matrix": "app.services.indicators.core",
    "get_indicator": "app.services.indicators.core",
    "get_warmup_requirement": "app.services.indicators.core",
    "hull_ma": "app.services.indicators.trend",
    "inside_bar": "app.services.indicators.candles",
    "list_indicators": "app.services.indicators.core",
    "mfi": "app.services.indicators.volume",
    "obv": "app.services.indicators.volume",
    "pinbar": "app.services.indicators.candles",
    "price_volume_distribution": "app.services.indicators.volume",
    "rolling_volatility": "app.services.indicators.volatility",
    "rsi": "app.services.indicators.momentum",
    "sma": "app.services.indicators.trend",
    "standard_deviation": "app.services.indicators.volatility",
    "validate_indicator": "app.services.indicators.core",
    "williams_r": "app.services.indicators.momentum",
    "wma": "app.services.indicators.trend",
    "zigzag": "app.services.indicators.trend",
}


def __getattr__(name: str) -> object:
    """Resolve and cache one explicitly registered Indicators public export.

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
    "adr",
    "adx",
    "atr",
    "bollinger_bands",
    "cmf",
    "doji",
    "ema",
    "engulfing",
    "get_capability_matrix",
    "get_indicator",
    "get_warmup_requirement",
    "hull_ma",
    "inside_bar",
    "list_indicators",
    "mfi",
    "obv",
    "pinbar",
    "price_volume_distribution",
    "rolling_volatility",
    "rsi",
    "sma",
    "standard_deviation",
    "validate_indicator",
    "williams_r",
    "wma",
    "zigzag",
)
