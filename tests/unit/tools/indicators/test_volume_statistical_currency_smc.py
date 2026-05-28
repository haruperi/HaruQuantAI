"""Unit tests for volume, statistical, currency strength, and SMC tools."""

from __future__ import annotations

import pandas as pd

from tools.indicators import (
    accumulation_distribution,
    bos_choch,
    calculate_currency_strength,
    calculate_hurst,
    calculate_pair_strength,
    fvg,
    get_top_pairs,
    hurst,
    ob,
    previous_high_low,
    swing_highs_lows,
)
from tests.unit.tools.indicators.conftest import assert_standard_response


def test_accumulation_distribution_success(ohlcv: pd.DataFrame) -> None:
    response = accumulation_distribution(ohlcv)
    assert_standard_response(response, "accumulation_distribution")
    assert response["status"] == "success"
    assert "adl" in response["data"][-1]


def test_hurst_tools_success(ohlcv: pd.DataFrame) -> None:
    scalar = calculate_hurst(ohlcv["close"].to_list(), min_length=5)
    assert_standard_response(scalar, "calculate_hurst")
    assert scalar["status"] == "success"
    rolling = hurst(ohlcv, period=6)
    assert_standard_response(rolling, "hurst")
    assert rolling["status"] == "success"


def test_currency_strength_tools_success(ohlcv: pd.DataFrame) -> None:
    eurusd = ohlcv.copy()
    gbpusd = ohlcv.copy()
    gbpusd["close"] = gbpusd["close"] * 1.02
    pair_data = {"EURUSD": eurusd, "GBPUSD": gbpusd}

    pair = calculate_pair_strength(eurusd, symbol="EURUSD", period=3)
    assert_standard_response(pair, "calculate_pair_strength")
    assert pair["status"] == "success"

    strength = calculate_currency_strength(pair_data, period=3)
    assert_standard_response(strength, "calculate_currency_strength")
    assert strength["status"] == "success"

    ranking = get_top_pairs(pair_data, period=3, top_n=1)
    assert_standard_response(ranking, "get_top_pairs")
    assert ranking["status"] == "success"


def test_smc_tools_success_and_no_lookahead_flags(ohlcv: pd.DataFrame) -> None:
    cases = [
        (fvg, "fvg"),
        (swing_highs_lows, "swing_highs_lows"),
        (bos_choch, "bos_choch"),
        (ob, "ob"),
        (previous_high_low, "previous_high_low"),
    ]
    for tool, name in cases:
        response = tool(ohlcv, request_id=f"test-{name}")
        assert_standard_response(response, name)
        assert response["status"] == "success"
        assert len(response["data"]) == len(ohlcv)


def test_invalid_currency_pair_returns_error(ohlcv: pd.DataFrame) -> None:
    response = calculate_pair_strength(ohlcv, symbol="EUR", period=3)
    assert_standard_response(response, "calculate_pair_strength")
    assert response["status"] == "error"
    assert response["error"]["code"] == "INVALID_INPUT"
