"""Component evidence for Economic Calendar database population."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.services.data import (
    import_economic_calendar_csv,
    run_data_migrations,
    sync_current_week_economic_calendar,
)
from app.services.data.contracts.responses import unwrap_data_response
from app.utils import generate_id


def _unwrap(response):
    """Return successful Data response content."""
    return unwrap_data_response(
        response,
        operation="data.economic_calendar.ingestion_test",
        request_id=generate_id("req"),
    )


def _configure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Configure and migrate one disposable SQLite database."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///calendar.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")
    _unwrap(run_data_migrations(generate_id("req")))
    return tmp_path / "calendar.sqlite3"


def test_csv_bootstrap_and_weekly_json_populate_reduced_schema(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Both approved source shapes persist events and explicit coverage."""
    database = _configure(monkeypatch, tmp_path)
    source = tmp_path / "scrape.csv"
    source.write_text(
        "id,datetime,currency,event,impact,actual,actual_unit,forecast,"
        "forecast_unit,previous,previous_unit,previous_revised\n"
        "1,2007-01-01 00:00:00,USD,CPI,High Impact Expected,2.0,"
        "unit_percentage,2.1,unit_percentage,1.9,unit_percentage,True\n"
        "2,2024-08-01 00:00:00,USD,Excluded,Low Impact Expected,,unit_none,"
        ",unit_none,,unit_none,False\n",
        encoding="utf-8",
    )

    imported = _unwrap(import_economic_calendar_csv(source, environment="dev"))
    weekly = _unwrap(
        sync_current_week_economic_calendar(
            environment="dev",
            observed_at=datetime(2026, 8, 3, tzinfo=UTC),
            rows=(
                {
                    "title": "Final Manufacturing PMI",
                    "country": "JPY",
                    "date": "2026-08-02T20:30:00-04:00",
                    "impact": "Low",
                    "forecast": "54.7",
                    "previous": "54.7",
                },
            ),
        )
    )

    assert imported == {"imported": 1, "rejected": 0}
    assert weekly == {"imported": 1, "rejected": 0}
    with closing(sqlite3.connect(database)) as connection:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(data_economic_events)")
        }
        event_count = connection.execute(
            "SELECT COUNT(*) FROM data_economic_events"
        ).fetchone()[0]
        coverage_count = connection.execute(
            "SELECT COUNT(*) FROM data_economic_calendar_coverage"
        ).fetchone()[0]
        weekly_end = connection.execute(
            "SELECT range_end FROM data_economic_calendar_coverage "
            "WHERE provider = 'forexfactory'"
        ).fetchone()[0]
    assert columns == {
        "event_id",
        "title",
        "country",
        "scheduled_at",
        "original_scheduled_at",
        "impact",
        "actual",
        "forecast",
        "previous",
        "revised_previous",
        "provider",
        "source_url",
        "first_seen_at",
        "updated_at",
        "request_id",
        "provider_definition_id",
    }
    assert event_count == 2
    assert coverage_count == 2
    assert weekly_end == "2026-08-09T04:00:00+00:00"
