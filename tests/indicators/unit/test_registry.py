"""Unit tests for the immutable official Indicators registry."""

import pytest
from app.services.indicators.core.errors import IndicatorError
from app.services.indicators.core.registry import (
    get_capability_matrix,
    get_indicator,
    list_indicators,
)

_EXPECTED_ORDER = (
    "adx",
    "adr",
    "atr",
    "bollinger_bands",
    "cmf",
    "doji",
    "ema",
    "engulfing",
    "hull_ma",
    "inside_bar",
    "mfi",
    "obv",
    "pinbar",
    "price_volume_distribution",
    "rolling_volatility",
    "rsi",
    "sma",
    "standard_deviation",
    "williams_r",
    "wma",
)


def test_get_indicator_rejects_unknown_id() -> None:
    """FR-INDI-011: an unknown ID raises IND_UNSUPPORTED_INDICATOR."""
    with pytest.raises(IndicatorError):
        get_indicator("macd")


def test_get_indicator_resolves_known_official_ids() -> None:
    """FR-INDI-011: every official ID resolves to its immutable spec."""
    for indicator_id in _EXPECTED_ORDER:
        spec = get_indicator(indicator_id)
        assert spec.indicator_id == indicator_id
        assert spec.tier == "core_mvp"
        assert spec.vectorized is True
        assert spec.multi_symbol is False
        assert spec.multi_timeframe is False


def test_list_indicators_is_stable_and_immutable() -> None:
    """FR-INDI-012: specs are listed in stable indicator-ID order."""
    specs = list_indicators()
    assert tuple(spec.indicator_id for spec in specs) == _EXPECTED_ORDER
    assert isinstance(specs, tuple)


def test_capability_matrix_matches_registry() -> None:
    """FR-INDI-013: the capability matrix mirrors registry order and shape."""
    matrix = get_capability_matrix()
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


def test_registry_period_schema_matches_indicator_requirements() -> None:
    """FR-INDI-011: required/default period metadata matches the registry."""
    ema_spec = get_indicator("ema")
    adx_spec = get_indicator("adx")
    assert ema_spec.parameter_schema["period"]["required"] is True
    assert ema_spec.parameter_schema["period"]["default"] is None
    assert adx_spec.parameter_schema["period"]["required"] is False
    assert adx_spec.parameter_schema["period"]["default"] == 14
    assert ema_spec.parameter_schema["period"]["minimum"] == 2
    assert ema_spec.parameter_schema["period"]["maximum"] == 1_000_000
