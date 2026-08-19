"""Component tests for the 011 market-reference migration."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.persistence.migrations import run_data_migrations
from app.utils import generate_id


def _unwrap(response):
    return unwrap_data_response(
        response,
        operation="data.persistence.test",
        request_id="req-00000000-0000-4000-8000-000000000000",
    )


def _configure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Configure one isolated database for migration runs."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///market_reference.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")
    return tmp_path / "market_reference.sqlite3"


def test_market_reference_step_replaces_reference_tables(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The step drops the 006 reference tables and creates the new set."""
    database = _configure(monkeypatch, tmp_path)

    _unwrap(run_data_migrations(generate_id("req")))

    with closing(sqlite3.connect(database)) as connection:
        names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    assert not {"data_symbols", "data_providers", "data_market_sessions"} & names
    assert {
        "data_instruments",
        "data_brokers",
        "data_sessions",
        "data_session_elements",
        "data_market_series",
        "data_broker_stocks",
        "data_stock_groups",
        "data_stock_members",
    } <= names


def test_market_reference_tables_are_strict_with_constraints(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The new tables enforce STRICT typing and boolean check constraints."""
    database = _configure(monkeypatch, tmp_path)

    _unwrap(run_data_migrations(generate_id("req")))

    with closing(sqlite3.connect(database)) as connection:
        instruments = connection.execute(
            "PRAGMA table_info(data_instruments)"
        ).fetchall()
        assert len(instruments) > 0
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO data_market_series (connection, symbol, instrument, "
                "remove_weekends) VALUES ('c', 's', 'i', 2)"
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO data_session_elements (session_id, day_from, time_from, "
                "day_to, time_to, eod) VALUES ('s', 1, 0, 5, 0, 3)"
            )
        # STRICT typing: a TEXT value cannot land in an INTEGER column.
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO data_broker_stocks (ticker, broker_id) "
                "VALUES ('T', 'not-an-integer')"
            )
