"""Public Indicators domain port.

Re-exports the approved Core contracts/registry API plus the twenty official
built-in indicator convenience functions. This package root is the only
documented stable import surface; leaf modules are internal implementation
detail and are not part of the public contract.
"""

from app.services.indicators.candles import doji, engulfing, inside_bar, pinbar
from app.services.indicators.core import (
    IndicatorConfig,
    IndicatorError,
    IndicatorErrorCode,
    IndicatorManifest,
    IndicatorProtocol,
    IndicatorResult,
    IndicatorSpec,
    WarmupRequirement,
    get_capability_matrix,
    get_indicator,
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
)
from app.services.indicators.volatility import (
    adr,
    atr,
    rolling_volatility,
    standard_deviation,
)
from app.services.indicators.volume import cmf, mfi, obv, price_volume_distribution

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
)
