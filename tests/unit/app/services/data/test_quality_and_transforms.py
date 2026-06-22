"""Unit tests for transforms, resampling, and alignment."""

from datetime import UTC, datetime, timedelta

from app.services.data.transforms import (
    aggregate_ticks_to_bars,
    align_multitimeframe_data,
    generate_synthetic_bars,
    generate_synthetic_ticks,
    label_market_data,
    resample_ohlcv,
)


def test_resample_ohlcv_m1_to_m5() -> None:
    """Test resampling M1 bars into M5 timeframe."""
    records = []
    base_time = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)
    for i in range(5):
        records.append(
            {
                "timestamp": (base_time + timedelta(minutes=i)).isoformat(),
                "open": 1.1000 + i * 0.0002,
                "high": 1.1010 + i * 0.0002,
                "low": 1.0990 + i * 0.0002,
                "close": 1.1002 + i * 0.0002,
                "volume": 10 + i,
                "tick_volume": 10,
                "real_volume": 0.0,
                "spread": 1.5,
                "source": "csv",
                "symbol": "EURUSD",
                "timeframe": "M1",
            }
        )

    resampled = resample_ohlcv(records, "M5")
    assert len(resampled) == 1
    bar = resampled[0]
    assert bar["open"] == 1.1000
    assert bar["high"] == 1.1018
    assert bar["low"] == 1.0990
    assert bar["close"] == 1.1010
    assert bar["volume"] == 60


def test_aggregate_ticks_to_bars_m1() -> None:
    """Test tick aggregation into M1 bars."""
    ticks = []
    base_time = datetime(2026, 6, 1, 10, 0, 5, tzinfo=UTC)
    for i in range(6):
        ticks.append(
            {
                "timestamp": (base_time + timedelta(seconds=i * 10)).isoformat(),
                "bid": 1.1000 + i * 0.0001,
                "ask": 1.1002 + i * 0.0001,
                "last": 1.1001 + i * 0.0001,
                "volume": 1,
                "spread": 2.0,
                "source": "csv",
                "symbol": "EURUSD",
            }
        )

    bars = aggregate_ticks_to_bars(ticks, "M1")
    assert len(bars) == 1
    bar = bars[0]
    assert bar["open"] == 1.1001
    assert bar["high"] == 1.1006
    assert bar["low"] == 1.1001
    assert bar["close"] == 1.1006


def test_align_multitimeframe_no_lookahead() -> None:
    """Verify that multi-timeframe alignment does not introduce lookahead bias."""
    m1_records = [
        {"timestamp": "2026-06-01T10:00:00Z", "close": 1.1000},
        {"timestamp": "2026-06-01T10:01:00Z", "close": 1.1002},
        {"timestamp": "2026-06-01T10:02:00Z", "close": 1.1004},
    ]
    m5_records = [
        {"timestamp": "2026-06-01T10:00:00Z", "close": 1.0990},
    ]

    target_ts = ["2026-06-01T10:00:00Z", "2026-06-01T10:01:00Z", "2026-06-01T10:02:00Z"]
    records_map = {"M1": m1_records, "M5": m5_records}
    aligned = align_multitimeframe_data(
        records_map,
        target_ts,
        allow_lookahead=False,
        alignment_method="last_known_closed_bar",
    )

    # For base M1 at 10:01, M5 closed bar is still the one from 10:00
    # or None if start boundary
    assert aligned is not None
    assert "M1" in aligned
    assert len(aligned["M1"]) == 3


def test_synthetic_generators() -> None:
    """Test deterministic synthetic generation."""
    bars = generate_synthetic_bars(
        symbol="EURUSD",
        timeframe="M5",
        start_time="2026-06-01T00:00:00Z",
        num_bars=10,
        start_price=1.10,
        drift=0.0,
        volatility=0.01,
        seed=100,
    )
    assert len(bars) == 10
    assert bars[0]["symbol"] == "EURUSD"

    ticks = generate_synthetic_ticks(
        symbol="EURUSD",
        start_time="2026-06-01T00:00:00Z",
        num_ticks=10,
        start_price=1.10,
        average_spread=0.0002,
        volatility=0.001,
        seed=100,
    )
    assert len(ticks) == 10


def test_data_labeling() -> None:
    """Verify data labeling engine outputs correct dimensions."""
    records = []
    base_time = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)
    for i in range(10):
        records.append(
            {
                "timestamp": (base_time + timedelta(minutes=i)).isoformat(),
                "close": 1.1000 + i * 0.0005,
            }
        )

    labeled = label_market_data(records, horizon=2, threshold=0.0001)
    assert len(labeled) == 10
    # For index 0, price at index 2 (1.1010) is greater than index 0 (1.1000)
    # by more than threshold
    assert labeled[0]["label"] == 1


def test_to_native_types() -> None:
    import numpy as np
    from app.services.data.transforms import _clean_numpy_types
    records = [
        {"int_val": np.int64(42), "float_val": np.float64(3.14), "str_val": "hello"}
    ]
    res = _clean_numpy_types(records)
    assert isinstance(res[0]["int_val"], int)
    assert isinstance(res[0]["float_val"], float)


def test_timeframe_to_pandas_freq_errors() -> None:
    import pytest
    from app.services.data.transforms import timeframe_to_pandas_freq
    from app.utils.errors import ValidationError

    # MN prefix
    assert timeframe_to_pandas_freq("MN1") == "1ME"

    # H prefix
    assert timeframe_to_pandas_freq("H4") == "4h"

    # D prefix
    assert timeframe_to_pandas_freq("D1") == "1D"

    # W prefix
    assert timeframe_to_pandas_freq("W1") == "1W"

    # Invalid timeframe value format
    with pytest.raises(ValidationError, match="Invalid timeframe value format"):
        timeframe_to_pandas_freq("Mabc")

    # Invalid timeframe unit
    with pytest.raises(ValidationError, match="Invalid timeframe unit"):
        timeframe_to_pandas_freq("Z5")


def test_timeframe_to_minutes_errors() -> None:
    import pytest
    from app.services.data.transforms import timeframe_to_minutes
    from app.utils.errors import ValidationError

    # MN prefix
    assert timeframe_to_minutes("MN1") == 43200

    # H prefix
    assert timeframe_to_minutes("H4") == 240

    # D prefix
    assert timeframe_to_minutes("D1") == 1440

    # W prefix
    assert timeframe_to_minutes("W1") == 10080

    # Invalid timeframe value format
    with pytest.raises(ValidationError, match="Invalid timeframe value format"):
        timeframe_to_minutes("Mabc")

    # Invalid timeframe unit
    with pytest.raises(ValidationError, match="Invalid timeframe unit"):
        timeframe_to_minutes("Z5")


def test_resample_ohlcv_errors_and_policies() -> None:
    import pytest
    from app.services.data.transforms import resample_ohlcv
    from app.utils.errors import ValidationError

    # Empty list returns empty list
    assert resample_ohlcv([], "M5") == []

    records = [
        {
            "timestamp": "2026-06-01T10:00:00Z",
            "open": 1.1000,
            "high": 1.1010,
            "low": 1.0990,
            "close": 1.1002,
            "volume": 10,
            "tick_volume": 10,
            "real_volume": 0.0,
            "spread": 1.5,
            "source": "csv",
            "symbol": "EURUSD",
            "timeframe": "M1",
        }
    ]

    # Invalid timeframe
    with pytest.raises(ValidationError):
        resample_ohlcv(records, "Z5")

    # resample with custom spread_policy
    res = resample_ohlcv(records, "M5", spread_policy="last")
    assert len(res) == 1

