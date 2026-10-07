"""Unit tests for CotService, COT catalog, index calculations, and bar alignment.

Description:
    Validates CFTC COT symbol catalog lookup, stochastic/trend index calculations
    for the 5 canonical fields (cpihedg, ctihedg, cpispec, ctispec, cpismall),
    weekly report synchronization, and forward-fill price bar alignment (Phase 2 Task 2.7).

Purpose:
    FEAT-DATA-COT: Ingest, compute, map, and align CFTC Commitments of Traders series.

Key Capabilities:
    FR-DATA-COT-CATALOG: Maintain symbol-to-CFTC contract mapping catalog.
    FR-DATA-COT-MAPPING: Compute 5 canonical COT indices and weekly bar alignment.
    FR-DATA-COT-UPDATES: Synchronize weekly CFTC reports and update indicators.

Python API Usage:
    Run via pytest:
    `pytest tests/unit/v2/phase_02/test_cot.py -v --no-cov`
"""

from __future__ import annotations

import logging
import math
from pathlib import Path

import pytest
from app.host.persistence import DatabaseManager
from app.workspace.data_manager.custom_data import CotService, CotSymbolMapping
from app.workspace.data_manager.data import BarRecord


@pytest.fixture
def cot_service(tmp_path: Path) -> CotService:
    """Fixture providing isolated CotService and database."""
    db = DatabaseManager(database_path=tmp_path / "test_cot.db")
    db.initialize()
    return CotService(db, storage_dir=tmp_path / "cot_storage")


def test_cot_catalog_mapping(
    cot_service: CotService, caplog: pytest.LogCaptureFixture
) -> None:
    """Validate default COT symbol mappings and custom mapping upsert."""
    caplog.set_level(logging.DEBUG)

    mappings = cot_service.list_mappings()
    assert len(mappings) >= 8

    symbols = {m.symbol for m in mappings}
    assert "EURUSD" in symbols
    assert "ES" in symbols
    assert "GC" in symbols

    eurusd_map = cot_service.get_mapping("EURUSD")
    assert eurusd_map is not None
    assert eurusd_map.cftc_code == "099741"
    assert "CHICAGO MERCANTILE EXCHANGE" in eurusd_map.cftc_name

    # Add custom mapping
    new_map = CotSymbolMapping(
        symbol="BTCUSD",
        cftc_code="133741",
        cftc_name="BITCOIN - CHICAGO MERCANTILE EXCHANGE",
        commodity_group="Crypto",
    )
    cot_service.save_mapping(new_map)

    retrieved = cot_service.get_mapping("BTCUSD")
    assert retrieved is not None
    assert retrieved.cftc_code == "133741"

    assert any("FR-DATA-COT-CATALOG" in rec.message for rec in caplog.records)


def test_cot_index_calculation(
    cot_service: CotService, caplog: pytest.LogCaptureFixture
) -> None:
    """Validate 5-index calculation logic and boundary values."""
    caplog.set_level(logging.DEBUG)

    # 10 weeks of mock raw data with monotonic changes
    raw_data = []
    for week in range(10):
        raw_data.append(
            {
                "report_date": f"2026-08-{week + 1:02d}",
                "release_date": f"2026-08-{week + 4:02d}",
                "comm_long": 10000.0 + week * 1000.0,
                "comm_short": 5000.0,
                "noncomm_long": 8000.0,
                "noncomm_short": 2000.0 + week * 500.0,
                "nonrep_long": 1000.0,
                "nonrep_short": 800.0,
                "open_interest": 50000.0,
            }
        )

    observations = cot_service.calculate_indices(raw_data, lookback_weeks=10)
    assert len(observations) == 10

    # Validate 5 fields exist on all observations
    for obs in observations:
        assert 0.0 <= obs.cpihedg <= 100.0
        assert 0.0 <= obs.ctihedg <= 100.0
        assert 0.0 <= obs.cpispec <= 100.0
        assert 0.0 <= obs.ctispec <= 100.0
        assert 0.0 <= obs.cpismall <= 100.0

    # Since commercial_long increases monotonically while short stays flat,
    # the last observation should be at the maximum (cpihedg == 100.0)
    assert observations[-1].cpihedg == 100.0

    assert any("FR-DATA-COT-MAPPING" in rec.message for rec in caplog.records)


def test_cot_bar_alignment_forward_fill(
    cot_service: CotService, caplog: pytest.LogCaptureFixture
) -> None:
    """Validate synchronizing weekly COT observations with daily price bars."""
    caplog.set_level(logging.DEBUG)

    # Weekly reports released on Friday 2026-10-02 and Friday 2026-10-09
    raw_reports = [
        {
            "report_date": "2026-09-29",
            "release_date": "2026-10-02",
            "comm_long": 50000.0,
            "comm_short": 30000.0,
            "noncomm_long": 20000.0,
            "noncomm_short": 15000.0,
            "nonrep_long": 5000.0,
            "nonrep_short": 4000.0,
        },
        {
            "report_date": "2026-10-06",
            "release_date": "2026-10-09",
            "comm_long": 55000.0,
            "comm_short": 28000.0,
            "noncomm_long": 22000.0,
            "noncomm_short": 14000.0,
            "nonrep_long": 5200.0,
            "nonrep_short": 3900.0,
        },
    ]
    cot_obs = cot_service.calculate_indices(raw_reports)
    assert len(cot_obs) == 2

    # Price bars: Thursday 10-01 (before first release), Monday 10-05, Friday 10-09
    bars = [
        BarRecord(
            timestamp_utc="2026-10-01T12:00:00Z",
            open=1.1000,
            high=1.1050,
            low=1.0980,
            close=1.1020,
        ),
        BarRecord(
            timestamp_utc="2026-10-05T12:00:00Z",
            open=1.1020,
            high=1.1060,
            low=1.1010,
            close=1.1040,
        ),
        BarRecord(
            timestamp_utc="2026-10-09T16:00:00Z",
            open=1.1040,
            high=1.1080,
            low=1.1030,
            close=1.1070,
        ),
    ]

    aligned = cot_service.align_cot_to_bars(bars, cot_obs)
    assert len(aligned) == 3

    # Bar 1 (10-01): Before release date 10-02 -> should have NaN for COT indices
    assert math.isnan(aligned[0]["cot_cpihedg"])

    # Bar 2 (10-05): After release date 10-02 -> should have report 1 values
    assert not math.isnan(aligned[1]["cot_cpihedg"])
    assert aligned[1]["cot_comm_net"] == 20000.0  # 50000 - 30000

    # Bar 3 (10-09): On release date 10-09 -> updated to report 2 values
    assert not math.isnan(aligned[2]["cot_cpihedg"])
    assert aligned[2]["cot_comm_net"] == 27000.0  # 55000 - 28000


def test_cot_report_update_flow(
    cot_service: CotService, caplog: pytest.LogCaptureFixture
) -> None:
    """Validate end-to-end CFTC report update and persistence."""
    caplog.set_level(logging.DEBUG)

    # Initial state
    assert cot_service.get_cot_data("EURUSD") == []

    # Run update
    count = cot_service.update_cftc_reports("EURUSD", synthetic_count=20)
    assert count == 20

    # Query persisted data
    persisted = cot_service.get_cot_data("EURUSD")
    assert len(persisted) == 20
    assert persisted[-1].cpihedg >= 0.0

    assert any("FR-DATA-COT-UPDATES" in rec.message for rec in caplog.records)


def test_cot_edge_cases(cot_service: CotService) -> None:
    """Validate empty bar alignment, missing observation handling, and invalid dates."""
    assert cot_service.align_cot_to_bars([], []) == []
    assert cot_service.get_cot_data("NONEXISTENT_SYMBOL") == []

    with pytest.raises(ValueError, match="No COT symbol mapping"):
        cot_service.update_cftc_reports("UNKNOWN_SYM")

    assert cot_service._estimate_release_date("invalid-date") == "invalid-date"
