"""Component evidence for application-triggered Data catalog transactions."""

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from app.kernel.identity import generate_id
from app.services.data import (
    get_verified_research_source,
    record_catalog_fetch,
    record_catalog_quality_event,
    run_data_migrations,
    sync_catalog_reference,
)
from app.services.data.persistence.update import update_verified_research_source_record


def _configure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Configure one disposable migrated Data store."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///catalog.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")
    result = run_data_migrations(generate_id("req"))
    assert result.status == "success"
    return tmp_path / "catalog.sqlite3"


def test_reference_fetch_quality_and_verified_source_are_reachable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Mutate and read every formerly orphaned non-artifact catalog table."""
    database = _configure(monkeypatch, tmp_path)
    request_id = generate_id("req")
    now = datetime(2026, 8, 5, tzinfo=UTC)
    sync_catalog_reference(
        provider_code="fixture",
        provider_kind="test",
        canonical_symbol="EURUSD",
        asset_class="fx",
        base_currency="EUR",
        quote_currency="USD",
        digits=5,
        tick_size=Decimal("0.00001"),
        min_volume=Decimal("0.01"),
        max_volume=Decimal(100),
        volume_step=Decimal("0.01"),
        sessions=(
            {
                "session_name": "weekday",
                "day_of_week": 0,
                "open_time_utc": "00:00:00",
                "close_time_utc": "23:59:59",
                "effective_from": "2026-01-01T00:00:00+00:00",
            },
        ),
        request_id=request_id,
        observed_at=now,
    )
    record_catalog_fetch(
        values=(
            "fetch-1",
            "provider-1",
            "symbol-1",
            "bars",
            "M1",
            1,
            2,
            1,
            0,
            None,
            "fixture",
            1,
            "success",
            None,
            request_id,
            "",
            now.isoformat(),
            now.isoformat(),
            now.isoformat(),
            now.isoformat(),
        ),
        request_id=request_id,
    )
    record_catalog_quality_event(
        values=(
            "quality-1",
            "symbol-1",
            None,
            None,
            "fetch-1",
            "gap",
            "warning",
            "inspect",
            1,
            2,
            1,
            "{}",
            now.isoformat(),
            request_id,
            "",
            now.isoformat(),
        ),
        request_id=request_id,
    )
    update_verified_research_source_record(
        ("sec", "v1", now.isoformat(), "record", "a" * 64, '["dev"]', "public"),
        request_id=request_id,
    )
    verified = get_verified_research_source("sec", "v1", request_id=request_id)
    assert verified is not None
    assert verified["source_id"] == "sec"

    with closing(sqlite3.connect(database)) as connection:
        counts = (
            connection.execute("SELECT COUNT(*) FROM data_instruments").fetchone()[0],
            connection.execute("SELECT COUNT(*) FROM data_brokers").fetchone()[0],
            connection.execute("SELECT COUNT(*) FROM data_sessions").fetchone()[0],
            connection.execute("SELECT COUNT(*) FROM data_fetch_log").fetchone()[0],
            connection.execute("SELECT COUNT(*) FROM data_quality_events").fetchone()[
                0
            ],
            connection.execute(
                "SELECT COUNT(*) FROM data_verified_research_sources"
            ).fetchone()[0],
        )
    assert all(count == 1 for count in counts)
