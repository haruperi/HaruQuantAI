"""Tests for the indicators domain registry."""

from __future__ import annotations

import tools.indicators as indicators


def test_registry_exports_expected_tools() -> None:
    expected = {
        "sma",
        "ema",
        "wma",
        "rsi",
        "atr",
        "adr",
        "bbands",
        "accumulation_distribution",
        "calculate_hurst",
        "hurst",
        "calculate_pair_strength",
        "calculate_currency_strength",
        "currency_strength_indicator",
        "get_top_pairs",
        "fvg",
        "swing_highs_lows",
        "bos_choch",
        "ob",
        "previous_high_low",
        "phl",
    }
    assert expected.issubset(set(indicators.__all__))


def test_all_exports_are_callable() -> None:
    for name in indicators.__all__:
        assert callable(getattr(indicators, name)), name
