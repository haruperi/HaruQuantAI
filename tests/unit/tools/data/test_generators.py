"""Unit tests for tools.data.generators."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[4]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from tools.data import generators as gen
from tools.data.generators import (
    BarAggregator,
    TicksGenerator,
    TimeframeManager,
    data_generate_ticks,
    gbm_data_generate,
)


def assert_standard_response(result: dict, tool_name: str) -> None:
    assert set(result) == {"status", "message", "data", "error", "metadata"}
    assert result["metadata"]["tool_name"] == tool_name
    assert result["metadata"]["tool_category"] == "data"
    assert result["metadata"]["tool_risk_level"] == "low"
    assert result["metadata"]["read_only"] is True
    assert result["metadata"]["writes_file"] is False
    assert result["metadata"]["modifies_database"] is False
    assert result["metadata"]["places_trade"] is False
    assert result["metadata"]["requires_network"] is False
    assert isinstance(result["metadata"]["execution_ms"], float)


def sample_bars() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": [1.0, 1.1, 1.2],
            "high": [1.2, 1.3, 1.4],
            "low": [0.9, 1.0, 1.1],
            "close": [1.1, 1.2, 1.3],
            "volume": [10, 20, 30],
            "spread": [2, 2, 3],
        },
        index=pd.date_range("2024-01-01", periods=3, freq="h", name="timestamp"),
    )


def sample_m1_bars() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": [1.00, 1.02, 1.04, 1.06],
            "high": [1.03, 1.05, 1.07, 1.09],
            "low": [0.99, 1.01, 1.03, 1.05],
            "close": [1.02, 1.04, 1.06, 1.08],
            "volume": [4, 5, 6, 7],
            "spread": [1, 2, 2, 3],
        },
        index=pd.date_range("2024-01-01", periods=4, freq="min", name="timestamp"),
    )


def sample_real_ticks() -> pd.DataFrame:
    return pd.DataFrame(
        {"Bid": [1.0, 1.01, 1.02], "Ask": [1.0002, 1.0102, 1.0202]},
        index=pd.date_range("2024-01-01", periods=3, freq="20s", name="timestamp"),
    )


def test_gbm_data_generate_success_single_symbol() -> None:
    result = gbm_data_generate("EURUSD", count=5, seed=42, request_id="test-001")
    assert result["status"] == "success"
    assert_standard_response(result, "gbm_data_generate")
    assert result["metadata"]["request_id"] == "test-001"
    assert result["data"]["rows"] == 5
    assert result["data"]["columns"] == ["open", "high", "low", "close", "volume"]


def test_gbm_data_generate_success_multiple_symbols() -> None:
    result = gbm_data_generate(["EURUSD", "GBPUSD"], count=3, seed=7)
    assert result["status"] == "success"
    assert result["data"]["columns"] == ["EURUSD", "GBPUSD"]


def test_gbm_data_generate_with_end_date_range() -> None:
    result = gbm_data_generate("EURUSD", start="2024-01-01", end="2024-01-03")
    assert result["status"] == "success"
    assert result["data"]["rows"] == 3


def test_gbm_data_generate_execution_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_serialize(_: pd.DataFrame) -> list[dict]:
        raise RuntimeError("serialization failed")

    monkeypatch.setattr(gen, "_serialize_frame_records", fail_serialize)
    result = gbm_data_generate("EURUSD", count=2)
    assert result["status"] == "error"
    assert result["error"]["code"] == "TOOL_EXECUTION_FAILED"


def test_gbm_data_generate_deterministic_with_same_seed() -> None:
    first = gbm_data_generate("EURUSD", count=5, seed=123)
    second = gbm_data_generate("EURUSD", count=5, seed=123)
    assert first["data"]["data"] == second["data"]["data"]


def test_gbm_data_generate_does_not_mutate_global_numpy_state() -> None:
    np.random.seed(999)
    before = np.random.random(3)
    np.random.seed(999)
    _ = gbm_data_generate("EURUSD", count=5, seed=123)
    after = np.random.random(3)
    assert np.allclose(before, after)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"symbols": ""},
        {"symbols": "EURUSD", "count": 0},
        {"symbols": "EURUSD", "sigma": -0.1},
        {"symbols": "EURUSD", "start_value": 0},
        {"symbols": "EURUSD", "start": "2024-02-01", "end": "2024-01-01"},
        {"symbols": "EURUSD", "interval": "BAD"},
    ],
)
def test_gbm_data_generate_invalid_input(kwargs: dict) -> None:
    result = gbm_data_generate(**kwargs)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_timeframe_manager_frequency_valid_invalid() -> None:
    assert TimeframeManager.timeframe_to_frequency("M5") == "5min"
    with pytest.raises(ValueError):
        TimeframeManager.timeframe_to_frequency("BAD")


def test_timeframe_manager_validation_and_resample_errors() -> None:
    manager = TimeframeManager()
    assert TimeframeManager.validate_timeframe("m1") is True
    assert TimeframeManager.validate_timeframe("") is False
    assert TimeframeManager.can_resample("M1", "H1") is True
    assert TimeframeManager.can_resample("H1", "M1") is False
    assert TimeframeManager.can_resample("bad", "M1") is False
    assert manager.resample(pd.DataFrame(), "H1").empty

    with pytest.raises(ValueError):
        TimeframeManager.timeframe_to_frequency("")
    with pytest.raises(ValueError):
        manager.resample("bad", "H1")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        manager.resample(sample_bars(), "M1", "H1")
    with pytest.raises(ValueError):
        manager.resample(sample_bars()[["open", "close"]], "H1")


def test_timeframe_manager_resample_lowercase_ohlcv() -> None:
    manager = TimeframeManager()
    result = manager.resample(sample_bars(), "H4", "H1")
    assert list(result.columns)[:5] == ["open", "high", "low", "close", "volume"]
    assert len(result) == 1


def test_timeframe_manager_resample_multi_timeframe_skips_invalid() -> None:
    result = TimeframeManager().resample_multi_timeframe(
        sample_bars(), "M1", ["M5", "BAD"]
    )
    assert list(result) == ["M5"]


def test_bar_aggregator_add_tick_and_flush() -> None:
    aggregator = BarAggregator("M1")
    assert (
        aggregator.add_tick(pd.Timestamp("2024-01-01T00:00:00").to_pydatetime(), 1.0)
        is None
    )
    completed = aggregator.add_tick(
        pd.Timestamp("2024-01-01T00:01:00").to_pydatetime(), 1.1
    )
    assert completed is not None
    assert completed["open"] == 1.0
    flushed = aggregator.flush()
    assert flushed is not None
    assert flushed["open"] == 1.1


def test_bar_aggregator_bar_paths_and_errors() -> None:
    aggregator = BarAggregator("M1")
    assert aggregator.get_current_bar() is None
    assert aggregator.flush() is None

    first = pd.Timestamp("2024-01-01T00:00:00").to_pydatetime()
    second = pd.Timestamp("2024-01-01T00:01:00").to_pydatetime()
    assert aggregator.add_bar(first, 1.0, 1.2, 0.9, 1.1, 10) is None
    assert aggregator.get_current_bar()["close"] == 1.1
    completed = aggregator.add_bar(second, 1.1, 1.3, 1.0, 1.2, 5)
    assert completed["timestamp"] == first
    assert aggregator.get_completed_bars() == [completed]

    with pytest.raises(ValueError):
        aggregator.add_tick("bad", 1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        aggregator.add_bar("bad", 1.0, 1.0, 1.0, 1.0)  # type: ignore[arg-type]

    empty = BarAggregator("M1")
    with pytest.raises(ValueError):
        empty._finalize_current_bar()


def test_data_generate_ticks_timeframe_success() -> None:
    result = data_generate_ticks(
        sample_bars(), model="timeframe_ticks", trading_timeframe="H1"
    )
    assert result["status"] == "success"
    assert_standard_response(result, "data_generate_ticks")
    assert result["data"]["rows"] == 12
    assert {"bid", "ask", "spread"}.issubset(set(result["data"]["columns"]))


def test_timeframe_ticks_with_timestamp_column_and_fixed_spread() -> None:
    bars = sample_bars().reset_index()
    bars.loc[1, "close"] = 0.95
    result = data_generate_ticks(
        bars,
        model="timeframe_ticks",
        trading_timeframe="H1",
        spread_model="fixed_spread",
        fixed_spread_points=4,
    )
    assert result["status"] == "success"
    assert {row["spread"] for row in result["data"]["data"]} == {4}


def test_data_generate_ticks_m1_real_and_synthetic_models() -> None:
    m1_result = data_generate_ticks(
        sample_bars(),
        model="m1_ticks",
        trading_timeframe="H1",
        m1_data=sample_m1_bars(),
        spread_model="variable_spread",
        min_spread_points=1,
        max_spread_points=2,
        random_seed=123,
    )
    assert m1_result["status"] == "success"
    assert m1_result["data"]["rows"] == 16

    real_result = data_generate_ticks(
        sample_bars(),
        model="real_ticks",
        trading_timeframe="H1",
        real_ticks=sample_real_ticks(),
    )
    assert real_result["status"] == "success"
    assert real_result["data"]["rows"] == 3

    synthetic_result = data_generate_ticks(
        sample_bars(),
        model="synthetic_ticks",
        trading_timeframe="H1",
        m1_data=sample_m1_bars(),
    )
    assert synthetic_result["status"] == "success"
    assert synthetic_result["data"]["rows"] == 22


def test_ticks_generator_helpers_and_validation_paths() -> None:
    assert TicksGenerator._find_col(pd.DataFrame({"Bid": [1]}), ["bid"]) == "Bid"
    assert TicksGenerator._find_col(pd.DataFrame({"Price": [1]}), ["bid"]) is None
    assert TicksGenerator._infer_bar_seconds(pd.DatetimeIndex(["2024-01-01"])) == 60
    assert list(TicksGenerator._empty_ticks().columns)[:4] == [
        "bid",
        "ask",
        "last",
        "spread",
    ]

    with pytest.raises(ValueError):
        TicksGenerator("bad", "H1")
    with pytest.raises(ValueError):
        TicksGenerator("timeframe_ticks", "BAD")
    with pytest.raises(ValueError):
        TicksGenerator("timeframe_ticks", "H1", point_value=0)
    with pytest.raises(ValueError):
        TicksGenerator("timeframe_ticks", "H1", spread_model="fixed_spread")
    with pytest.raises(ValueError):
        TicksGenerator(
            "timeframe_ticks",
            "H1",
            spread_model="fixed_spread",
            fixed_spread_points=-1,
        )
    with pytest.raises(ValueError):
        TicksGenerator("timeframe_ticks", "H1", spread_model="variable_spread")
    with pytest.raises(ValueError):
        TicksGenerator(
            "timeframe_ticks",
            "H1",
            spread_model="variable_spread",
            min_spread_points=3,
            max_spread_points=1,
        )


def test_internal_validation_helpers() -> None:
    records = gen._serialize_frame_records(
        pd.DataFrame(
            {"value": [np.nan, np.inf], "when": pd.date_range("2024-01-01", periods=2)}
        )
    )
    assert records[0]["value"] is None
    assert records[0]["when"].endswith("Z")

    with pytest.raises(gen.GeneratorValidationError):
        gen._serialize_frame_records(None)
    with pytest.raises(gen.GeneratorValidationError):
        gen._normalize_ohlcv_columns(None)
    with pytest.raises(gen.GeneratorValidationError):
        gen._ensure_datetime_index(pd.DataFrame({"open": [1]}))
    with pytest.raises(gen.GeneratorValidationError):
        gen._validate_symbols(123)
    with pytest.raises(gen.GeneratorValidationError):
        gen._validate_symbols(["EURUSD", ""])
    with pytest.raises(gen.GeneratorValidationError):
        gen._validate_numeric(True, "value")
    with pytest.raises(gen.GeneratorValidationError):
        gen._validate_numeric(np.inf, "value")
    with pytest.raises(gen.GeneratorValidationError):
        gen._validate_optional_positive_int(False, "count")
    with pytest.raises(gen.GeneratorValidationError):
        gen._parse_datetime("not-a-date", "start")
    with pytest.raises(gen.GeneratorValidationError):
        gen._validate_date_range("2024-01-01", None, count=None)
    with pytest.raises(gen.GeneratorValidationError):
        gen._validate_timeframe_interval("")
    with pytest.raises(gen.GeneratorValidationError):
        gen._validate_dataframe_not_empty([], "frame")
    with pytest.raises(gen.GeneratorValidationError):
        gen._validate_dataframe_not_empty(pd.DataFrame(), "frame")
    with pytest.raises(gen.GeneratorValidationError):
        gen._validate_max_output_rows(0)


def test_tick_output_and_path_helpers() -> None:
    assert gen._interpolate_path([1.0], 3) == [1.0, 1.0, 1.0]
    assert gen._interpolate_path([1.0, 2.0], 1) == [1.0]
    assert gen._timeframe_seconds("H4") == 14400
    assert gen._timeframe_seconds("unknown") == 60

    with pytest.raises(gen.GeneratorValidationError):
        gen._validate_tick_output("bad", 1)
    with pytest.raises(gen.GeneratorValidationError):
        gen._validate_tick_output(pd.DataFrame({"bid": [1]}), 10)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"model": "bad", "trading_timeframe": "H1"},
        {"model": "m1_ticks", "trading_timeframe": "H1"},
        {"model": "real_ticks", "trading_timeframe": "H1"},
        {"model": "timeframe_ticks", "trading_timeframe": "BAD"},
        {"model": "timeframe_ticks", "trading_timeframe": "H1", "spread_model": "bad"},
    ],
)
def test_data_generate_ticks_invalid_input(kwargs: dict) -> None:
    result = data_generate_ticks(sample_bars(), **kwargs)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_data_generate_ticks_max_output_guardrail() -> None:
    result = data_generate_ticks(
        sample_bars(),
        model="timeframe_ticks",
        trading_timeframe="H1",
        max_output_rows=2,
    )
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_data_generate_ticks_execution_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_generate(
        self: TicksGenerator, trading_tf_data: pd.DataFrame
    ) -> pd.DataFrame:
        raise RuntimeError("boom")

    monkeypatch.setattr(TicksGenerator, "generate", fail_generate)
    result = data_generate_ticks(
        sample_bars(), model="timeframe_ticks", trading_timeframe="H1"
    )
    assert result["status"] == "error"
    assert result["error"]["code"] == "TOOL_EXECUTION_FAILED"


def test_no_official_tool_returns_none() -> None:
    assert gbm_data_generate("EURUSD", count=2) is not None
    assert (
        data_generate_ticks(
            sample_bars(), model="timeframe_ticks", trading_timeframe="H1"
        )
        is not None
    )
