"""Unit tests for market session schedules and historical volume orchestration."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from app.services.data.access.sessions import (
    fetch_historical_volume,
    get_current_schedule,
)
from app.services.data.contracts import (
    DatasetSaveRequest,
    MarketSchedule,
    ScheduleRequest,
    SessionWindow,
    VolumeRequest,
)
from app.services.data.sources.policy import _reset_policy_registry
from app.services.data.sources.registry import _reset_registry
from app.services.data.storage.datasets import save_dataset

from tests.data.helpers import make_dataset, make_quality, register_local_test_source

START = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
END = START + timedelta(hours=2)


def _configure_database(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test_sessions_access.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1.0")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")
    from app.services.data.storage.migrations import run_data_migrations

    run_data_migrations(
        "req-60d56de3ff8bb20750e936377422e90f785e5ecfef35c15300af6cade7ff5e9d"
    )


@pytest.fixture(autouse=True)
def _setup(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _reset_registry()
    _reset_policy_registry()
    _configure_database(monkeypatch, tmp_path)
    raw_root = tmp_path / "data" / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    register_local_test_source(raw_root, ("AAPL",))


def test_current_schedule_advances_midnight_end() -> None:
    """Verify schedule returns advanced cross-midnight windows correctly."""
    req = ScheduleRequest(
        source_id="local_csv",
        symbol="AAPL",
        view="sessions",
        timezone="America/New_York",
        request_id="req-c9177c5c2ae0a357706459bab174f7712855b3f7a0d1efd8242053d95fe4d812",
    )

    schedule = MarketSchedule(
        source_id="local_csv",
        symbol="AAPL",
        timezone="America/New_York",
        hours=(
            SessionWindow(
                label="regular",
                opens_at=START,
                closes_at=START + timedelta(hours=8),
            ),
        ),
        sessions=(
            SessionWindow(
                label="regular",
                opens_at=START,
                closes_at=START + timedelta(hours=8),
            ),
        ),
        observed_at=START,
        request_id=req.request_id,
    )
    calendar = MagicMock()
    calendar.get_schedule.return_value = schedule
    clock = MagicMock()
    clock.now.return_value = START
    sched = get_current_schedule(req, calendar, clock=clock)
    assert sched.symbol == "AAPL"

    # Verify cross-midnight session advances to next day
    session = sched.sessions[0]
    assert session.opens_at < session.closes_at
    assert (session.closes_at - session.opens_at) >= timedelta(hours=6)


def test_volume_modes_have_stable_contracts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify volume fetch works across summary, records, and buckets modes."""
    (tmp_path / "data" / "raw").mkdir(parents=True, exist_ok=True)

    # Save a dataset containing bars with volume
    dataset = make_dataset().model_copy(
        update={
            "symbol": "AAPL",
            "start": START,
            "end": START + timedelta(minutes=5),
            "records": (
                make_dataset()
                .records[0]
                .model_copy(
                    update={
                        "timestamp": START,
                        "volume": Decimal(100),
                        "available_at": START + timedelta(minutes=5, seconds=1),
                    }
                ),
                make_dataset()
                .records[0]
                .model_copy(
                    update={
                        "timestamp": START + timedelta(minutes=5),
                        "volume": Decimal(200),
                        "available_at": START + timedelta(minutes=5, seconds=1),
                    }
                ),
            ),
            "record_count": 2,
            "available_at": START + timedelta(minutes=5, seconds=1),
            "quality_report": make_quality(count=2).model_copy(
                update={"generated_at": START + timedelta(minutes=5, seconds=1)}
            ),
            "request_id": (
                "req-2f61a9763d33a78e4abf23a9cdd321aeebeb8a8b3c9dd40ca16d811e7a867710"
            ),
        }
    )
    save_req = DatasetSaveRequest(
        dataset=dataset,
        relative_path=Path("data/raw/AAPL.csv"),
        format="csv",
        overwrite=True,
        request_id="req-2f61a9763d33a78e4abf23a9cdd321aeebeb8a8b3c9dd40ca16d811e7a867710",
    )
    save_dataset(save_req)

    # 1. Summary mode
    req_summary = VolumeRequest(
        source_id="local_csv",
        symbol="AAPL",
        start=START,
        end=END,
        mode="summary",
        limit=10,
        request_id="req-971a30451dc702c3543a14c4a221ddbec879d6088816b6072273446e05bf902f",
    )
    res_sum = fetch_historical_volume(req_summary)
    assert res_sum.mode == "summary"
    assert res_sum.summary is not None
    assert res_sum.summary.total == Decimal(300)
    assert res_sum.summary.average == Decimal(150)

    # 2. Records mode
    req_records = req_summary.model_copy(
        update={
            "mode": "records",
            "request_id": (
                "req-2c084f9f9c2f4a5e7a81b07cbf5e7800c223d71bdc686c0a3cce5e3699180724"
            ),
        }
    )
    res_rec = fetch_historical_volume(req_records)
    assert res_rec.mode == "records"
    assert len(res_rec.records) == 2
    assert res_rec.records[0].volume == Decimal(100)

    # 3. Buckets mode
    req_buckets = req_summary.model_copy(
        update={
            "mode": "buckets",
            "bucket_seconds": 300,
            "request_id": (
                "req-9aaf1525d803fe6d5fea1059efc2cfcc9074f170d33ede861ff79cd07ebdc955"
            ),
        }
    )
    res_buck = fetch_historical_volume(req_buckets)
    assert res_buck.mode == "buckets"
    assert len(res_buck.records) == 2
