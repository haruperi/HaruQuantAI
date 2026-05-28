"""Unit tests for vectorized strategy execution."""

from __future__ import annotations

from tools.strategy import extract_strategy_signals, run_vectorized_strategy
from tools.strategy.examples.trend_following import TrendFollowingStrategy


def test_trend_following_does_not_mutate_input(ohlc_data) -> None:
    original_columns = list(ohlc_data.columns)
    strategy = TrendFollowingStrategy(
        {"symbol": "EURUSD", "fast_period": 5, "slow_period": 10, "filter_period": 20}
    )
    processed = strategy.on_bar(ohlc_data)
    assert list(ohlc_data.columns) == original_columns
    assert "entry_signal" in processed.columns
    assert "ema_5" in processed.columns


def test_run_vectorized_strategy_returns_schema_and_signals(ohlc_data) -> None:
    result = run_vectorized_strategy(
        "TrendFollowingStrategy",
        ohlc_data,
        params={
            "symbol": "EURUSD",
            "fast_period": 5,
            "slow_period": 10,
            "filter_period": 20,
        },
        request_id="unit-run-001",
    )
    assert result["status"] == "success"
    assert result["metadata"]["tool_name"] == "run_vectorized_strategy"
    assert result["data"]["rows"] == len(ohlc_data)
    assert isinstance(result["data"]["signals"], list)


def test_run_vectorized_strategy_invalid_strategy(ohlc_data) -> None:
    result = run_vectorized_strategy(
        "MissingStrategy", ohlc_data, request_id="unit-run-err"
    )
    assert result["status"] == "error"
    assert result["error"]["code"] == "DATA_NOT_FOUND"


def test_extract_strategy_signals_from_processed_data(ohlc_data) -> None:
    strategy = TrendFollowingStrategy(
        {"symbol": "EURUSD", "fast_period": 5, "slow_period": 10, "filter_period": 20}
    )
    processed = strategy.on_bar(ohlc_data)
    result = extract_strategy_signals(
        "TrendFollowingStrategy",
        processed,
        params={
            "symbol": "EURUSD",
            "fast_period": 5,
            "slow_period": 10,
            "filter_period": 20,
        },
        request_id="unit-extract-001",
    )
    assert result["status"] == "success"
    assert "signals" in result["data"]
