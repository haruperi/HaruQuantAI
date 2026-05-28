"""Unit tests for trend, momentum, and volatility indicator tools."""

from __future__ import annotations

import pandas as pd

from tools.indicators import adr, atr, bbands, ema, rsi, sma, wma
from tests.unit.tools.indicators.conftest import assert_standard_response


def test_sma_success_known_value_and_immutability(ohlcv: pd.DataFrame) -> None:
    original = ohlcv.copy(deep=True)
    response = sma(ohlcv, period=3, request_id="test-sma")
    assert_standard_response(response, "sma")
    assert response["status"] == "success"
    rows = response["data"]
    assert rows[2]["sma_3"] == 11.5
    pd.testing.assert_frame_equal(ohlcv, original)
    assert response["metadata"]["request_id"] == "test-sma"


def test_ema_wma_rsi_atr_adr_bbands_success(ohlcv: pd.DataFrame) -> None:
    cases = [
        (ema, "ema"),
        (wma, "wma"),
        (rsi, "rsi"),
        (atr, "atr"),
        (adr, "adr"),
        (bbands, "bbands"),
    ]
    for tool, name in cases:
        response = tool(ohlcv, period=3)
        assert_standard_response(response, name)
        assert response["status"] == "success"
        assert len(response["data"]) == len(ohlcv)


def test_invalid_period_returns_error(ohlcv: pd.DataFrame) -> None:
    response = sma(ohlcv, period=0)
    assert_standard_response(response, "sma")
    assert response["status"] == "error"
    assert response["error"]["code"] == "INVALID_INPUT"


def test_missing_column_returns_error(ohlcv: pd.DataFrame) -> None:
    response = rsi(ohlcv.drop(columns=["close"]), period=3)
    assert_standard_response(response, "rsi")
    assert response["status"] == "error"
    assert response["error"]["code"] == "INVALID_INPUT"


def test_warmup_nan_and_fill_policy(ohlcv: pd.DataFrame) -> None:
    nan_response = sma(ohlcv, period=3)
    assert nan_response["data"][0]["sma_3"] is None
    fill_response = sma(ohlcv, period=3, warmup_policy="fill", fill_value=0.0)
    assert fill_response["data"][0]["sma_3"] == 0.0


def test_index_alignment_is_preserved(ohlcv: pd.DataFrame) -> None:
    response = atr(ohlcv, period=3)
    returned_index = [row["index"] for row in response["data"]]
    assert returned_index[0] == ohlcv.index[0].isoformat()
    assert returned_index[-1] == ohlcv.index[-1].isoformat()
