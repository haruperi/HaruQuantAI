"""Import-contract tests for the Indicators public API surface."""

import inspect
import types

import app.services.indicators as indicators_root
from app.services.indicators import (
    get_indicator,
    sma,
)

from tests.indicators.helpers import build_dataset

_EXPECTED_ROOT_ALL = (
    "adr",
    "adx",
    "adx_dmi_regime",
    "aggressive_trade_imbalance",
    "amihud_illiquidity",
    "anchored_vwap",
    "aroon",
    "assert_closed_input",
    "atr",
    "atr_percent",
    "bollinger_bands",
    "bollinger_bandwidth",
    "breakout_retest",
    "build_chart_pattern_evidence",
    "build_indicator_config",
    "build_indicator_snapshot",
    "build_liquidity_snapshot",
    "choppiness_regime",
    "cmf",
    "composite_market_speed_gauge",
    "cumulative_volume_delta",
    "doji",
    "donchian_breakout_regime",
    "donchian_channels",
    "double_top_bottom",
    "ema",
    "ema_slope",
    "engulfing",
    "ewma_volatility",
    "final_regime_resolver",
    "flag_pennant",
    "garman_klass_volatility",
    "gaps",
    "get_capability_matrix",
    "get_indicator",
    "get_indicator_result_metadata",
    "get_indicator_result_values",
    "get_warmup_requirement",
    "head_and_shoulders",
    "hull_ma",
    "hurst_regime",
    "inside_bar",
    "join_indicator_result",
    "level_clustering",
    "linear_regression_trend",
    "list_indicators",
    "macd",
    "market_event_arrival_rate",
    "measure_market_speed",
    "measure_order_flow",
    "measure_trend_strength",
    "measure_volatility_envelope",
    "mfi",
    "momentum_acceleration",
    "obv",
    "parkinson_volatility",
    "parse_indicator_snapshot",
    "parse_liquidity_snapshot",
    "pinbar",
    "pivot_points",
    "pivots",
    "price_velocity",
    "price_volume_distribution",
    "project_structural_levels",
    "rectangle",
    "rogers_satchell_volatility",
    "rolling_volatility",
    "rsi",
    "run_indicators_migrations",
    "sma",
    "standard_deviation",
    "supertrend",
    "three_bar_reversal",
    "triangle",
    "validate_indicator",
    "volatility_expansion_rate",
    "volatility_liquidity_stress_regime",
    "volatility_of_volatility",
    "volatility_percentile",
    "volume_acceleration",
    "volume_profile",
    "wedge",
    "williams_r",
    "wma",
    "zigzag",
)
_NAMESPACES = ((indicators_root, _EXPECTED_ROOT_ALL),)


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
        assert list(module.__all__) == sorted(expected)
        for name in expected:
            assert hasattr(module, name)
        assert _public_non_module_attrs(module) == set(expected)


def test_retired_bundled_modules_are_not_public_symbols() -> None:
    """Retired bundled implementation modules are absent from public exports."""
    retired = ("moving_averages", "oscillators", "ranges", "rolling")
    assert not set(_EXPECTED_ROOT_ALL) & set(retired)


def test_public_operations_return_the_exact_standard_response_shape() -> None:
    """Every migrated public operation exposes raw data in the five-field envelope."""
    response = get_indicator("sma")

    assert set(response.__class__.model_fields) == {
        "status",
        "message",
        "data",
        "error",
        "metadata",
    }
    assert response.status == "success"
    assert response.error is None
    assert response.data is not None
    assert response.data.indicator_id == "sma"
    assert response.data is get_indicator("sma").data
    assert response.metadata.domain == "indicators"
    assert response.metadata.read_only is True
    assert response.metadata.writes_file is False
    assert response.metadata.modifies_database is False
    assert response.metadata.places_trade is False
    assert response.metadata.requires_network is False
    assert "StandardResponse" in str(inspect.signature(sma).return_annotation)

    failure = sma(build_dataset([(1, 2, 0, 1, 10)]), period=1)
    assert failure.status == "error"
    assert failure.data is None
    assert failure.error is not None
    assert failure.error.code == "IND_INVALID_PARAMETER"
    assert '"status":"error"' in failure.model_dump_json()
