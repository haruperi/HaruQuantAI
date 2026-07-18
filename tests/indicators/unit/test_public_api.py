"""Import-contract tests for the Indicators public API surface."""

import types

import app.services.indicators as indicators_root
import app.services.indicators.candles as indicators_candles
import app.services.indicators.core as indicators_core
import app.services.indicators.momentum as indicators_momentum
import app.services.indicators.trend as indicators_trend
import app.services.indicators.volatility as indicators_volatility
import app.services.indicators.volume as indicators_volume

_EXPECTED_ROOT_ALL = (
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
_EXPECTED_CORE_ALL = (
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
_EXPECTED_TREND_ALL = ("adx", "bollinger_bands", "ema", "hull_ma", "sma", "wma")
_EXPECTED_VOLATILITY_ALL = (
    "adr",
    "atr",
    "rolling_volatility",
    "standard_deviation",
)
_EXPECTED_MOMENTUM_ALL = ("rsi", "williams_r")
_EXPECTED_VOLUME_ALL = ("cmf", "mfi", "obv", "price_volume_distribution")
_EXPECTED_CANDLES_ALL = ("doji", "engulfing", "inside_bar", "pinbar")

_RETIRED_BUNDLED_MODULE_NAMES = ("moving_averages", "oscillators", "ranges", "rolling")

_NAMESPACES = (
    (indicators_root, _EXPECTED_ROOT_ALL),
    (indicators_core, _EXPECTED_CORE_ALL),
    (indicators_trend, _EXPECTED_TREND_ALL),
    (indicators_volatility, _EXPECTED_VOLATILITY_ALL),
    (indicators_momentum, _EXPECTED_MOMENTUM_ALL),
    (indicators_volume, _EXPECTED_VOLUME_ALL),
    (indicators_candles, _EXPECTED_CANDLES_ALL),
)


def _public_non_module_attrs(module: types.ModuleType) -> set[str]:
    """Collect a module's non-underscore, non-submodule public attributes.

    Submodule references bound automatically by ``from x.y import z`` import
    machinery are excluded so leaf implementation modules are never mistaken
    for documented public symbols.

    Args:
        module: The module to inspect.

    Returns:
        The set of public, non-module attribute names.
    """
    return {
        name
        for name, value in vars(module).items()
        if not name.startswith("_") and not isinstance(value, types.ModuleType)
    }


def test_root_and_feature_exports_are_exact() -> None:
    """Root/feature ``__all__`` values are exact with no undocumented symbols."""
    for module, expected in _NAMESPACES:
        assert list(module.__all__) == list(expected)
        assert _public_non_module_attrs(module) == set(expected)
        for name in expected:
            assert hasattr(module, name)


def test_retired_bundled_modules_are_not_public_symbols() -> None:
    """Retired bundled implementation modules are absent from public exports."""
    for _module, expected in _NAMESPACES:
        assert not set(expected) & set(_RETIRED_BUNDLED_MODULE_NAMES)
