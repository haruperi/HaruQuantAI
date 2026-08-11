"""Unit tests for the immutable official Indicators registry."""

from app.services.indicators import (
    get_capability_matrix,
    get_indicator,
    list_indicators,
)

from tests.indicators.helpers import assert_error, unwrap_response

_EXPECTED_ORDER = (
    "adx",
    "adr",
    "adx_dmi_regime",
    "aggressive_trade_imbalance",
    "amihud_illiquidity",
    "anchored_vwap",
    "aroon",
    "atr",
    "atr_percent",
    "bollinger_bands",
    "bollinger_bandwidth",
    "breakout_retest",
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
    "head_and_shoulders",
    "hull_ma",
    "hurst_regime",
    "inside_bar",
    "level_clustering",
    "linear_regression_trend",
    "macd",
    "market_event_arrival_rate",
    "mfi",
    "momentum_acceleration",
    "obv",
    "parkinson_volatility",
    "pinbar",
    "pivot_points",
    "pivots",
    "price_velocity",
    "price_volume_distribution",
    "rectangle",
    "rogers_satchell_volatility",
    "rolling_volatility",
    "rsi",
    "sma",
    "standard_deviation",
    "supertrend",
    "three_bar_reversal",
    "triangle",
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


def test_get_indicator_rejects_unknown_id() -> None:
    """FR-INDI-011: an unknown ID raises IND_UNSUPPORTED_INDICATOR."""
    assert_error(get_indicator("unknown_indicator"), "IND_UNSUPPORTED_INDICATOR")


def test_get_indicator_resolves_known_official_ids() -> None:
    """FR-INDI-011: every official ID resolves to its immutable spec."""
    for indicator_id in _EXPECTED_ORDER:
        spec = unwrap_response(get_indicator(indicator_id))
        assert spec.indicator_id == indicator_id
        assert spec.tier == "core_mvp"
        assert spec.vectorized is True
        assert spec.multi_symbol is False
        assert spec.multi_timeframe is False


def test_list_indicators_is_stable_and_immutable() -> None:
    """FR-INDI-012: specs are listed in stable indicator-ID order."""
    specs = unwrap_response(list_indicators())
    assert tuple(spec.indicator_id for spec in specs) == _EXPECTED_ORDER
    assert isinstance(specs, tuple)


def test_capability_matrix_matches_registry() -> None:
    """FR-INDI-013: the capability matrix mirrors registry order and shape."""
    matrix = unwrap_response(get_capability_matrix())
    assert tuple(record["indicator_id"] for record in matrix) == _EXPECTED_ORDER
    expected_keys = [
        "indicator_id",
        "indicator_version",
        "formula_version",
        "tier",
        "batch",
        "vectorized",
        "multi_symbol",
        "multi_timeframe",
        "unsupported_optional_modes",
        "dependencies",
        "unsupported_codes",
        "official_workflow_eligibility",
    ]
    for record in matrix:
        assert list(record.keys()) == expected_keys
        assert record["batch"] is True
        assert record["vectorized"] is True
        assert record["multi_symbol"] is False
        assert record["multi_timeframe"] is False
        assert record["unsupported_optional_modes"] == (
            "incremental",
            "streaming",
            "cache",
            "composition",
            "custom_registration",
            "out_of_core",
            "acceleration",
            "proprietary",
        )
        for mode in record["unsupported_optional_modes"]:
            assert record["unsupported_codes"][mode] == "IND_INVALID_CONFIG"

    # Every official calculator uses both NumPy and pandas for its vectorized
    # formula, so the capability matrix reports that dependency pair uniformly.
    for record in matrix:
        assert record["dependencies"] == ("numpy", "pandas")


def test_registry_new_volatility_indicators_declare_annualization_factor() -> None:
    """New volatility indicators declare a non-hardcoded annualization_factor."""
    for indicator_id in (
        "rolling_volatility",
        "ewma_volatility",
        "parkinson_volatility",
        "garman_klass_volatility",
        "rogers_satchell_volatility",
        "volatility_percentile",
    ):
        spec = unwrap_response(get_indicator(indicator_id))
        schema = spec.parameter_schema["annualization_factor"]
        assert schema["required"] is False
        assert schema["default"] == 252.0


def test_registry_atr_exposes_true_range_output_template() -> None:
    """ATR's registry entry declares both output columns per IND-VOL-01."""
    spec = unwrap_response(get_indicator("atr"))
    assert spec.output_templates == ("atr_{period}", "true_range")


def test_registry_period_schema_matches_indicator_requirements() -> None:
    """FR-INDI-011: required/default period metadata matches the registry."""
    ema_spec = unwrap_response(get_indicator("ema"))
    adx_spec = unwrap_response(get_indicator("adx"))
    assert ema_spec.parameter_schema["period"]["required"] is True
    assert ema_spec.parameter_schema["period"]["default"] is None
    assert adx_spec.parameter_schema["period"]["required"] is False
    assert adx_spec.parameter_schema["period"]["default"] == 14
    assert ema_spec.parameter_schema["period"]["minimum"] == 2
    assert ema_spec.parameter_schema["period"]["maximum"] == 1_000_000
