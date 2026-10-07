"""Unit tests for DataQualityInspector, SeriesTransformer, and data exports.

Description:
    Validates data quality metric auditing, gap detection, timeframe resampling
    (M1 to M5, H1), timezone conversions, session window filtering, and multi-format
    export to CSV, MT4, and MT5 formats (Phase 2 Task 2.4).

Purpose:
    FEAT-DATA-QUALITY: Quality diagnostics, resampling, transforms, and exports.

Key Capabilities:
    FR-DATA-QUALITY-METRICS: Health score calculation, gaps, and duplicates.
    FR-DATA-QUALITY-TRANSFORMS: Timeframe resampling and timezone shifting.
    FR-DATA-QUALITY-EXPORT: Multi-format exports (CSV, MT4, MT5).

Python API Usage:
    Run via pytest:
    `pytest tests/unit/v2/phase_02/test_quality.py -v --no-cov`
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
from app.plugins.data.ingestion import BarRecord
from app.plugins.data.quality import DataQualityInspector
from app.plugins.data.sessions import (
    SessionWindow,
    TradingHoliday,
    TradingSessionDefinition,
)
from app.plugins.data.transforms import SeriesTransformer


@pytest.fixture
def sample_m1_bars() -> list[BarRecord]:
    """Provide a contiguous sequence of 10 M1 bars spanning 09:30 to 09:39."""
    bars: list[BarRecord] = []
    base_price = 100.0
    for minute in range(30, 40):
        # 09:30 to 09:34 (bucket 1), 09:35 to 09:39 (bucket 2)
        bars.append(
            BarRecord(
                timestamp_utc=f"2026-10-07T09:{minute:02d}:00Z",
                open=base_price,
                high=base_price + 2.0,
                low=base_price - 1.0,
                close=base_price + 1.0,
                volume=50.0,
                open_interest=10.0,
            )
        )
        base_price += 1.0
    return bars


def test_quality_inspector_clean(caplog: pytest.LogCaptureFixture) -> None:
    """Validate quality audit on a perfectly contiguous clean series."""
    caplog.set_level(logging.DEBUG)
    inspector = DataQualityInspector()

    bars = [
        BarRecord(
            timestamp_utc=f"2026-10-07T09:{m:02d}:00Z",
            open=100.0,
            high=102.0,
            low=99.0,
            close=101.0,
            volume=10.0,
        )
        for m in range(5)
    ]
    report = inspector.inspect_series(bars, expected_interval_seconds=60)

    assert report.total_bars == 5
    assert report.valid_bars == 5
    assert report.bad_bars == 0
    assert report.duplicate_bars == 0
    assert report.gap_bars == 0
    assert report.quality_score == 1.0
    assert any("FR-DATA-QUALITY-METRICS" in rec.message for rec in caplog.records)


def test_quality_inspector_anomalies(caplog: pytest.LogCaptureFixture) -> None:
    """Validate quality audit detecting bad geometry, duplicates, and gaps."""
    caplog.set_level(logging.DEBUG)
    inspector = DataQualityInspector()

    bars = [
        # Bar 0: Valid
        BarRecord(
            timestamp_utc="2026-10-07T09:00:00Z",
            open=100.0,
            high=102.0,
            low=99.0,
            close=101.0,
            volume=10.0,
        ),
        # Bar 1: Duplicate timestamp
        BarRecord(
            timestamp_utc="2026-10-07T09:00:00Z",
            open=100.0,
            high=102.0,
            low=99.0,
            close=101.0,
            volume=10.0,
        ),
        # Bar 2: Bad geometry (high < open)
        BarRecord(
            timestamp_utc="2026-10-07T09:01:00Z",
            open=100.0,
            high=98.0,
            low=97.0,
            close=99.0,
            volume=10.0,
        ),
        # Bar 3: Large gap (10 minutes jump to 09:11:00)
        BarRecord(
            timestamp_utc="2026-10-07T09:11:00Z",
            open=101.0,
            high=103.0,
            low=100.0,
            close=102.0,
            volume=10.0,
        ),
    ]
    report = inspector.inspect_series(bars, expected_interval_seconds=60)

    assert report.total_bars == 4
    assert report.duplicate_bars == 1
    assert report.bad_bars == 1
    assert report.gap_bars > 0
    assert report.quality_score < 1.0
    assert len(report.issues) > 0


def test_quality_inspector_empty() -> None:
    """Validate handling of empty bar sequence."""
    inspector = DataQualityInspector()
    report = inspector.inspect_series([])
    assert report.total_bars == 0
    assert report.quality_score == 0.0


def test_resampling_m1_to_m5(
    sample_m1_bars: list[BarRecord], caplog: pytest.LogCaptureFixture
) -> None:
    """Validate M1 to M5 bar resampling aggregation math and bucket alignment."""
    caplog.set_level(logging.DEBUG)
    transformer = SeriesTransformer()

    m5_bars = transformer.resample(sample_m1_bars, target_timeframe="M5")

    # 10 M1 bars -> 2 M5 bars
    assert len(m5_bars) == 2

    # Bucket 1: 09:30 to 09:34
    b1 = m5_bars[0]
    assert b1.timestamp_utc.endswith("09:30:00") or "09:30:00" in b1.timestamp_utc
    assert b1.open == sample_m1_bars[0].open  # First open
    assert b1.close == sample_m1_bars[4].close  # Last close
    assert b1.high == max(b.high for b in sample_m1_bars[:5])
    assert b1.low == min(b.low for b in sample_m1_bars[:5])
    assert b1.volume == sum(b.volume for b in sample_m1_bars[:5])

    # Bucket 2: 09:35 to 09:39
    b2 = m5_bars[1]
    assert "09:35:00" in b2.timestamp_utc
    assert b2.open == sample_m1_bars[5].open
    assert b2.close == sample_m1_bars[9].close

    assert any("FR-DATA-QUALITY-TRANSFORMS" in rec.message for rec in caplog.records)


def test_resampling_unsupported_timeframe(
    sample_m1_bars: list[BarRecord],
) -> None:
    """Validate error on invalid timeframe specification."""
    transformer = SeriesTransformer()
    with pytest.raises(ValueError, match="Unsupported target timeframe"):
        transformer.resample(sample_m1_bars, target_timeframe="INVALID_TF")


def test_timezone_shifting(sample_m1_bars: list[BarRecord]) -> None:
    """Validate timezone conversion from UTC to America/New_York."""
    transformer = SeriesTransformer()
    shifted = transformer.shift_timezone(
        sample_m1_bars[:2], target_timezone="America/New_York"
    )

    assert len(shifted) == 2
    # In October, New York is EDT (UTC-4). 09:30:00 UTC -> 05:30:00 EDT
    assert "-04:00" in shifted[0].timestamp_utc
    assert "05:30:00" in shifted[0].timestamp_utc


def test_session_window_filtering() -> None:
    """Validate filtering bars outside active trading session or during holidays."""
    transformer = SeriesTransformer()

    # Session: 09:30 - 16:00 UTC, Mon-Fri (day_of_week 0-4)
    session = TradingSessionDefinition(
        name="TestRTH",
        timezone="UTC",
        windows=[
            SessionWindow(day_of_week=d, start_time="09:30", end_time="16:00")
            for d in range(5)
        ],
        holidays=[TradingHoliday(date_str="2026-10-09", description="Special Holiday")],
    )

    bars = [
        # In session (Wednesday 09:35 UTC)
        BarRecord(
            timestamp_utc="2026-10-07T09:35:00Z",
            open=100.0,
            high=102.0,
            low=99.0,
            close=101.0,
        ),
        # Pre-market out of session (Wednesday 08:00 UTC)
        BarRecord(
            timestamp_utc="2026-10-07T08:00:00Z",
            open=100.0,
            high=102.0,
            low=99.0,
            close=101.0,
        ),
        # Weekend (Saturday 12:00 UTC)
        BarRecord(
            timestamp_utc="2026-10-10T12:00:00Z",
            open=100.0,
            high=102.0,
            low=99.0,
            close=101.0,
        ),
        # Holiday (Friday 2026-10-09 10:00 UTC)
        BarRecord(
            timestamp_utc="2026-10-09T10:00:00Z",
            open=100.0,
            high=102.0,
            low=99.0,
            close=101.0,
        ),
    ]

    filtered = transformer.filter_by_session(bars, session)
    assert len(filtered) == 1
    assert filtered[0].timestamp_utc == "2026-10-07T09:35:00Z"


def test_export_formats(
    sample_m1_bars: list[BarRecord],
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Validate export to CSV, MT4, and MT5 formats."""
    caplog.set_level(logging.DEBUG)
    transformer = SeriesTransformer()

    # 1. CSV
    csv_file = tmp_path / "export.csv"
    transformer.export_csv(sample_m1_bars[:2], csv_file)
    assert csv_file.exists()
    csv_content = csv_file.read_text(encoding="utf-8")
    assert "Date,Time,Open,High,Low,Close,Volume" in csv_content
    assert "2026.10.07" in csv_content

    # 2. MT4
    mt4_file = tmp_path / "export_mt4.csv"
    transformer.export_mt4(sample_m1_bars[:2], mt4_file)
    assert mt4_file.exists()
    mt4_content = mt4_file.read_text(encoding="utf-8")
    assert "2026.10.07,09:30" in mt4_content

    # 3. MT5
    mt5_file = tmp_path / "export_mt5.txt"
    transformer.export_mt5(sample_m1_bars[:2], mt5_file)
    assert mt5_file.exists()
    mt5_content = mt5_file.read_text(encoding="utf-8")
    assert "<DATE>\t<TIME>" in mt5_content
    assert any("FR-DATA-QUALITY-EXPORT" in rec.message for rec in caplog.records)


def test_quality_inspector_inversion_and_bad_timestamps() -> None:
    """Validate quality inspector handling of inverted chronological order and bad timestamps."""
    inspector = DataQualityInspector()
    bars = [
        BarRecord(
            timestamp_utc="2026-10-07T09:35:00Z",
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=10.0,
        ),
        # Inverted timestamp: earlier than previous
        BarRecord(
            timestamp_utc="2026-10-07T09:30:00Z",
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=10.0,
        ),
        # Invalid isoformat timestamp string
        BarRecord(
            timestamp_utc="not-a-timestamp",
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=10.0,
        ),
        # Bad geometry: high is lower than open
        BarRecord(
            timestamp_utc="2026-10-07T09:40:00Z",
            open=100.0,
            high=95.0,
            low=90.0,
            close=92.0,
            volume=10.0,
        ),
    ]
    report = inspector.inspect_series(bars)
    assert report.total_bars == 4
    assert report.bad_bars >= 2
    assert any("Chronological inversion" in issue for issue in report.issues)


def test_transforms_edge_cases(sample_m1_bars: list[BarRecord]) -> None:
    """Validate empty bar handling, H1/D1 bucket resolution."""
    transformer = SeriesTransformer()
    # Empty resampling
    assert transformer.resample([], "M5") == []

    # Higher timeframe resampling
    h1_bars = transformer.resample(sample_m1_bars, "H1")
    assert len(h1_bars) == 1

    d1_bars = transformer.resample(sample_m1_bars, "D1")
    assert len(d1_bars) == 1


def test_quality_score_zero_denominator() -> None:
    """Validate compute score fallback when denominator is non-positive."""
    assert DataQualityInspector._compute_score(0, 0, 0, 0) == 1.0
