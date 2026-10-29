"""Tests for canonical partition I/O and dynamic resampling."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]
import polars as pl
import pyarrow.parquet as pq
import pytest
from app.core.data.io import DataIO, timeframe_to_seconds
from app.core.data.market_storage import encode_frame
from app.core.enums import Timeframe
from app.core.lib.errors import DomainError


def test_timeframe_to_seconds_resolutions() -> None:
    """Verify standard enum, string, custom, and tick timeframe durations."""
    assert timeframe_to_seconds(Timeframe.PERIOD_M1) == 60
    assert timeframe_to_seconds(Timeframe.PERIOD_H1) == 3600
    assert timeframe_to_seconds("M1") == 60
    assert timeframe_to_seconds("M5") == 300
    assert timeframe_to_seconds("H1") == 3600
    assert timeframe_to_seconds("D1") == 86400
    assert timeframe_to_seconds("TICK") == 0
    assert timeframe_to_seconds("ticks") == 0
    assert timeframe_to_seconds("S15") == 15
    assert timeframe_to_seconds("M10") == 600

    with pytest.raises(DomainError) as exc_info:
        timeframe_to_seconds("INVALID_TF")
    assert exc_info.value.code == "INVALID_TIMEFRAME"


def test_empty_frame_schemas() -> None:
    """Verify empty frame schema for bars and ticks with decoded and integer prices."""
    m1_decoded = DataIO.empty_frame("M1", decode=True)
    assert m1_decoded.is_empty()
    assert m1_decoded.schema["Open"] == pl.Float64
    assert m1_decoded.schema["DateTime"] == pl.Datetime("us", "UTC")

    m1_raw = DataIO.empty_frame("M1", decode=False)
    assert m1_raw.schema["Open"] == pl.Int64

    tick_decoded = DataIO.empty_frame("TICK", decode=True)
    assert tick_decoded.schema["Bid"] == pl.Float64
    assert tick_decoded.schema["Ask"] == pl.Float64
    assert tick_decoded.schema["Flags"] == pl.UInt16

    tick_raw = DataIO.empty_frame("TICK", decode=False)
    assert tick_raw.schema["Bid"] == pl.Int64


def test_read_partitions_missing_file_raises_domain_error(tmp_path: Path) -> None:
    """Assert missing partition on disk raises CORRUPT_DATASET_STORAGE."""
    missing_file = tmp_path / "nonexistent.parquet"
    with pytest.raises(DomainError) as exc_info:
        DataIO.read_partitions([missing_file])
    assert exc_info.value.code == "CORRUPT_DATASET_STORAGE"
    assert "Partition file missing" in exc_info.value.message


def test_read_partitions_two_partitions_and_bounds(tmp_path: Path) -> None:
    """Fixture 1: Read across two partitions with unbounded and bounded time ranges."""
    tick_size = 0.0001
    part1_data = pd.DataFrame(
        {
            "DateTime": [
                datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
                datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
                datetime(2026, 1, 1, 0, 2, tzinfo=UTC),
            ],
            "Open": [1.1000, 1.1010, 1.1025],
            "High": [1.1020, 1.1030, 1.1040],
            "Low": [1.0990, 1.1005, 1.1020],
            "Close": [1.1010, 1.1025, 1.1035],
            "Volume": [100, 150, 200],
        }
    )
    part2_data = pd.DataFrame(
        {
            "DateTime": [
                datetime(2026, 1, 2, 0, 0, tzinfo=UTC),
                datetime(2026, 1, 2, 0, 1, tzinfo=UTC),
            ],
            "Open": [1.1050, 1.1060],
            "High": [1.1070, 1.1080],
            "Low": [1.1045, 1.1055],
            "Close": [1.1060, 1.1075],
            "Volume": [120, 180],
        }
    )

    p1 = tmp_path / "part1.parquet"
    p2 = tmp_path / "part2.parquet"
    pq.write_table(encode_frame(part1_data, "M1", tick_size), p1)
    pq.write_table(encode_frame(part2_data, "M1", tick_size), p2)

    # Unbounded read across both partitions
    full = DataIO.read_partitions([p1, p2], decode=True, tick_size=tick_size)
    assert len(full) == 5
    assert full["Close"].to_list() == [1.1010, 1.1025, 1.1035, 1.1060, 1.1075]

    # Bounded read spanning boundary: 2026-01-01 00:01:00 to 2026-01-02 00:00:00 (3 bars)
    bounded = DataIO.read_partitions(
        [p1, p2],
        start=datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
        end=datetime(2026, 1, 2, 0, 0, tzinfo=UTC),
        decode=True,
        tick_size=tick_size,
    )
    assert len(bounded) == 3
    assert bounded["DateTime"].to_list() == [
        datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
        datetime(2026, 1, 1, 0, 2, tzinfo=UTC),
        datetime(2026, 1, 2, 0, 0, tzinfo=UTC),
    ]

    # Raw integer price read (decode=False)
    raw = DataIO.read_partitions([p1], decode=False, tick_size=tick_size)
    assert raw["Close"].to_list() == [11010, 11025, 11035]


def test_resample_bars_dynamic_grouping() -> None:
    """Fixture 5: Resample five 1-minute bars into one 5-minute bar."""
    data = {
        "DateTime": [
            datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
            datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
            datetime(2026, 1, 1, 0, 2, tzinfo=UTC),
            datetime(2026, 1, 1, 0, 3, tzinfo=UTC),
            datetime(2026, 1, 1, 0, 4, tzinfo=UTC),
        ],
        "Open": [1.1000, 1.1010, 1.1025, 1.1030, 1.1040],
        "High": [1.1020, 1.1030, 1.1040, 1.1050, 1.1060],
        "Low": [1.0990, 1.1005, 1.1020, 1.1025, 1.1035],
        "Close": [1.1010, 1.1025, 1.1035, 1.1045, 1.1055],
        "Volume": [100, 150, 200, 120, 180],
    }
    df = pl.DataFrame(data)

    resampled = DataIO.resample_bars(df, target_timeframe="M5", source_timeframe="M1")
    assert len(resampled) == 1
    row = resampled.to_dicts()[0]
    assert row["DateTime"] == datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    assert row["Open"] == 1.1000
    assert row["High"] == 1.1060
    assert row["Low"] == 1.0990
    assert row["Close"] == 1.1055
    assert row["Volume"] == 750


def test_resample_bars_validation_errors() -> None:
    """Verify downsampling or tick resampling rejection."""
    df = pl.DataFrame(
        {
            "DateTime": [datetime(2026, 1, 1, 0, 0, tzinfo=UTC)],
            "Open": [1.1],
            "High": [1.2],
            "Low": [1.0],
            "Close": [1.15],
            "Volume": [10],
        }
    )
    with pytest.raises(DomainError) as exc_info:
        DataIO.resample_bars(df, target_timeframe="M1", source_timeframe="H1")
    assert exc_info.value.code == "UNSUPPORTED_RESAMPLING"

    with pytest.raises(DomainError) as exc_tick:
        DataIO.resample_bars(df, target_timeframe="M1", source_timeframe="TICK")
    assert exc_tick.value.code == "UNSUPPORTED_RESAMPLING"
