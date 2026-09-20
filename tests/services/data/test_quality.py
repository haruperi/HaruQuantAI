"""Tests for FEAT-DATA-QUALITY (app/services/data/quality.py)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.contracts.data import (
    BarRecord,
    QualityAnomalyType,
    RepairPolicy,
    SessionDefinition,
    SessionWindow,
    TickRecord,
)
from app.services.data.quality import (
    QualityConfig,
    QualityServiceImpl,
)
from app.services.data.sessions import (
    SessionConfig,
    SessionServiceImpl,
)
from app.services.persistence.data import (
    DataPersistenceConfig,
    DataPersistenceServiceImpl,
)
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseServiceImpl,
)


def _setup_quality(tmp_path: Path) -> QualityServiceImpl:
    db_file = tmp_path / "test_quality.db"
    db = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    persist = DataPersistenceServiceImpl(
        db, DataPersistenceConfig(preseed_defaults=True)
    )
    sess_svc = SessionServiceImpl(persist, SessionConfig())
    return QualityServiceImpl(
        persistence=persist,
        session_service=sess_svc,
        config=QualityConfig(),
    )


def test_anomaly_detection_ohlc_inversions_and_spikes(tmp_path: Path) -> None:
    """Verify detection of high/low errors, crossed bars, and price spikes."""
    svc = _setup_quality(tmp_path)
    base_time = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)

    # 1. Normal baseline bars
    bars = [
        BarRecord(
            timestamp=base_time + timedelta(minutes=i),
            open=1.0500,
            high=1.0510,
            low=1.0490,
            close=1.0505,
            volume=100.0,
        )
        for i in range(10)
    ]

    # 2. Add an inverted bar (crossed quote: Low > High)
    bars.append(
        BarRecord(
            timestamp=base_time + timedelta(minutes=10),
            open=1.0500,
            high=1.0480,
            low=1.0520,
            close=1.0500,
            volume=100.0,
        )
    )

    # 3. Add a spike bar
    bars.append(
        BarRecord(
            timestamp=base_time + timedelta(minutes=11),
            open=1.0500,
            high=1.1000,  # 500 pip spike vs 20 pip baseline
            low=1.0490,
            close=1.0505,
            volume=100.0,
        )
    )

    report = svc.evaluate_quality(bars, timeframe="M1")
    assert report.total_records == 12
    assert report.quality_score < 1.0

    anomaly_types = {a.anomaly_type for a in report.anomalies}
    assert QualityAnomalyType.CROSSED_QUOTE in anomaly_types
    assert QualityAnomalyType.SPIKE in anomaly_types


def test_gap_and_sequence_detection(tmp_path: Path) -> None:
    """Verify detection of non-monotonicity, duplicates, and gaps."""
    svc = _setup_quality(tmp_path)
    base_time = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)

    bars = [
        BarRecord(timestamp=base_time, open=1.05, high=1.06, low=1.04, close=1.05),
        # Duplicate timestamp
        BarRecord(timestamp=base_time, open=1.05, high=1.06, low=1.04, close=1.05),
        # Gap: 10 minutes later (600s vs 60s M1 threshold)
        BarRecord(
            timestamp=base_time + timedelta(minutes=10),
            open=1.05,
            high=1.06,
            low=1.04,
            close=1.05,
        ),
        # Non-monotonic: earlier timestamp
        BarRecord(
            timestamp=base_time + timedelta(minutes=5),
            open=1.05,
            high=1.06,
            low=1.04,
            close=1.05,
        ),
    ]

    report = svc.evaluate_quality(bars, timeframe="M1")
    anomaly_types = {a.anomaly_type for a in report.anomalies}
    assert QualityAnomalyType.DUPLICATE in anomaly_types
    assert QualityAnomalyType.GAP in anomaly_types
    assert QualityAnomalyType.NON_MONOTONIC in anomaly_types


def test_out_of_session_detection(tmp_path: Path) -> None:
    """Verify session-aware out-of-session anomaly flagging."""
    svc = _setup_quality(tmp_path)

    session = SessionDefinition(
        name="Test Window",
        timezone="UTC",
        windows=[
            SessionWindow(day_of_week=0, open_time="09:00:00", close_time="17:00:00")
        ],
    )

    # Monday at 08:00 UTC (Pre-market)
    pre_mkt_bar = BarRecord(
        timestamp=datetime(2026, 6, 1, 8, 0, 0, tzinfo=UTC),
        open=1.05,
        high=1.06,
        low=1.04,
        close=1.05,
    )
    report = svc.evaluate_quality([pre_mkt_bar], session=session)
    assert len(report.anomalies) == 1
    assert report.anomalies[0].anomaly_type == QualityAnomalyType.OUT_OF_SESSION


def test_data_repair_policy(tmp_path: Path) -> None:
    """Verify dropping invalid OHLC bars and deduplicating timestamps."""
    svc = _setup_quality(tmp_path)
    base_time = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)

    bars = [
        BarRecord(timestamp=base_time, open=1.05, high=1.06, low=1.04, close=1.05),
        # Duplicate
        BarRecord(timestamp=base_time, open=1.05, high=1.06, low=1.04, close=1.05),
        # Invalid OHLC (Low > High)
        BarRecord(
            timestamp=base_time + timedelta(minutes=1),
            open=1.05,
            high=1.03,
            low=1.07,
            close=1.05,
        ),
        # Valid bar
        BarRecord(
            timestamp=base_time + timedelta(minutes=2),
            open=1.05,
            high=1.06,
            low=1.04,
            close=1.05,
        ),
    ]

    policy = RepairPolicy(drop_invalid_ohlc=True)
    repaired, audit = svc.repair_data(bars, policy)

    assert len(repaired) == 2  # Duplicate dropped, invalid dropped
    assert audit.original_count == 4
    assert audit.repaired_count == 2
    assert audit.modifications_count == 2
    assert len(audit.repairs_applied) == 2


def test_tick_quality_evaluation(tmp_path: Path) -> None:
    """Verify tick crossed quotes, duplicates, and non-monotonic timing."""
    svc = _setup_quality(tmp_path)
    base_time = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)

    ticks = [
        # Normal tick
        TickRecord(timestamp=base_time, sequence=1, bid=1.0500, ask=1.0502),
        # Crossed quote: bid > ask
        TickRecord(
            timestamp=base_time + timedelta(seconds=1),
            sequence=2,
            bid=1.0510,
            ask=1.0508,
        ),
        # Duplicate timestamp and sequence
        TickRecord(
            timestamp=base_time + timedelta(seconds=1),
            sequence=2,
            bid=1.0510,
            ask=1.0512,
        ),
        # Non-monotonic timing
        TickRecord(
            timestamp=base_time - timedelta(seconds=10),
            sequence=3,
            bid=1.0500,
            ask=1.0502,
        ),
    ]

    report = svc.evaluate_tick_quality(ticks)
    assert report.total_records == 4
    assert report.quality_score < 1.0

    anomaly_types = {a.anomaly_type for a in report.anomalies}
    assert QualityAnomalyType.CROSSED_QUOTE in anomaly_types
    assert QualityAnomalyType.DUPLICATE in anomaly_types
    assert QualityAnomalyType.NON_MONOTONIC in anomaly_types


def test_repair_clamp_spikes_and_fill_gaps(tmp_path: Path) -> None:
    """Verify spike clamping and small gap interpolation in repair_data."""
    svc = _setup_quality(tmp_path)
    base_time = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)

    # 15 baseline bars so ATR is computed over 14 bars
    bars = [
        BarRecord(
            timestamp=base_time + timedelta(minutes=i),
            open=1.0500,
            high=1.0510,
            low=1.0490,
            close=1.0500,
            volume=100.0,
        )
        for i in range(15)
    ]
    # Add a 1-bar gap between minute 14 and minute 16
    # And add a spike on minute 16
    bars.append(
        BarRecord(
            timestamp=base_time + timedelta(minutes=16),
            open=1.0500,
            high=1.0900,  # 400 pip spike vs 20 pip ATR
            low=1.0490,
            close=1.0500,
            volume=100.0,
        )
    )

    policy = RepairPolicy(
        drop_invalid_ohlc=True,
        clamp_spikes=True,
        fill_small_gaps=True,
        max_fill_gap_bars=2,
    )
    repaired, audit = svc.repair_data(bars, policy)

    # Original: 16 bars. 1 gap filled at minute 15 -> 17 bars total.
    assert len(repaired) == 17
    assert audit.original_count == 16
    assert audit.repaired_count == 17
    assert audit.modifications_count >= 2  # 1 gap filled + 1 spike clamped

    # The minute-16 bar (now index 16) should have clamped range
    clamped_bar = repaired[16]
    assert clamped_bar.high < 1.0900
