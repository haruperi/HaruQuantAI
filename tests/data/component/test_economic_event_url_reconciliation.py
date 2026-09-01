"""Component evidence for definition persistence and exact reconciliation."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from app.kernel.identity import generate_id
from app.services.data import run_data_migrations, sync_current_week_economic_calendar
from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.economic_calendar.event_urls import definition_parameters
from app.services.data.persistence import (
    reconcile_economic_event_definition_records,
    update_economic_event_definition_record,
)


def _unwrap(response):
    """Return successful Data response content."""
    return unwrap_data_response(
        response,
        operation="data.economic_calendar.definition_test",
        request_id=generate_id("req"),
    )


def _configure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Configure and migrate one isolated SQLite database."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///definitions.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")
    _unwrap(run_data_migrations(generate_id("req")))
    return tmp_path / "definitions.sqlite3"


def test_weekly_csv_persists_definition_and_permanent_url(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The official CSV shape retains its permanent event identity."""
    database = _configure(monkeypatch, tmp_path)
    _unwrap(
        sync_current_week_economic_calendar(
            environment="dev",
            rows=(
                {
                    "Title": "Unemployment Rate",
                    "Country": "USD",
                    "Date": "08-07-2026",
                    "Time": "8:30am",
                    "Impact": "High",
                    "Forecast": "4.2%",
                    "Previous": "4.2%",
                    "URL": (
                        "https://www.forexfactory.com/calendar/56-us-unemployment-rate"
                    ),
                },
            ),
        )
    )

    with closing(sqlite3.connect(database)) as connection:
        definition = connection.execute(
            "SELECT provider_definition_id, source_url "
            "FROM data_economic_event_definitions"
        ).fetchone()
        occurrence = connection.execute(
            "SELECT provider_definition_id, source_url FROM data_economic_events"
        ).fetchone()
    assert (
        definition
        == occurrence
        == (
            "56",
            "https://www.forexfactory.com/calendar/56-us-unemployment-rate",
        )
    )

    numeric = {
        "provider_definition_id": "56",
        "country": "USD",
        "title": "Unemployment Rate",
        "source_url": "https://www.forexfactory.com/calendar/56",
        "source_original": None,
        "source_latest": None,
        "measures": "Percentage unemployed",
        "effect": None,
        "frequency": None,
        "also_called": None,
        "event_type": "Employment",
    }
    request_id = generate_id("req")
    update_economic_event_definition_record(
        definition_parameters(numeric, request_id=request_id),
        request_id=request_id,
    )
    with closing(sqlite3.connect(database)) as connection:
        retained_url = connection.execute(
            "SELECT source_url FROM data_economic_event_definitions"
        ).fetchone()[0]
    assert retained_url.endswith("56-us-unemployment-rate")


def test_exact_unique_definition_reconciles_historical_occurrence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An exact unique title/country definition links an existing occurrence."""
    database = _configure(monkeypatch, tmp_path)
    request_id = generate_id("req")
    definition = {
        "provider_definition_id": "56",
        "country": "USD",
        "title": "Unemployment Rate",
        "source_url": "https://www.forexfactory.com/calendar/56-us-unemployment-rate",
        "source_original": "https://www.bls.gov/",
        "source_latest": None,
        "measures": "Percentage unemployed",
        "effect": None,
        "frequency": "Released monthly",
        "also_called": "Jobless Rate",
        "event_type": "Employment",
    }
    update_economic_event_definition_record(
        definition_parameters(definition, request_id=request_id),
        request_id=request_id,
    )
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(
            "INSERT INTO data_economic_events VALUES "
            "(?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, ?, NULL, ?, ?, ?, NULL)",
            (
                "local_csv:1",
                "Unemployment Rate",
                "USD",
                "2020-01-01T00:00:00+00:00",
                "2020-01-01T00:00:00+00:00",
                3,
                "local_csv",
                "2020-01-01T00:00:00+00:00",
                "2020-01-01T00:00:00+00:00",
                request_id,
            ),
        )
        connection.commit()

    result = reconcile_economic_event_definition_records(request_id=request_id)

    with closing(sqlite3.connect(database)) as connection:
        row = connection.execute(
            "SELECT provider_definition_id, source_url FROM data_economic_events"
        ).fetchone()
    assert result.affected_rows == 1
    assert row == (
        "56",
        "https://www.forexfactory.com/calendar/56-us-unemployment-rate",
    )
