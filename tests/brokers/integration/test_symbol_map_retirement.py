"""Integration evidence for guarded Broker symbol-map retirement."""

from pathlib import Path

import pytest
from app.kernel.identity import generate_id
from app.services.brokers import run_broker_migrations
from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
    unwrap_data_response,
)

_NOW = "2026-09-01T00:00:00Z"


def _configure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Configure one isolated non-production database."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///brokers_retirement_test.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")


def _table_names(request_id: str) -> set[str]:
    """Read all current SQLite table names through Data."""
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=("SELECT name FROM sqlite_master WHERE type='table'",),
                parameter_sets=((),),
                max_rows=100,
            ),
            request_id=request_id,
        )
    )
    result = unwrap_data_response(
        response, operation="brokers.retirement.tables", request_id=request_id
    )
    return {row["name"] for row in result.rows}


def test_complete_manifest_retires_empty_symbol_map_idempotently(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Apply immutable history and leave no current Broker symbol table."""
    _configure(monkeypatch, tmp_path)
    request_id = generate_id("req")
    assert str(run_broker_migrations(request_id).status) == "success"
    assert "broker_symbol_map" not in _table_names(request_id)
    assert str(run_broker_migrations(generate_id("req")).status) == "success"


def test_nonempty_symbol_map_blocks_retirement_without_data_loss(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Fail closed and roll back when legacy mappings need operator migration."""
    _configure(monkeypatch, tmp_path)
    request_id = generate_id("req")
    execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(
                    "CREATE TABLE broker_symbol_map ("
                    "map_id TEXT PRIMARY KEY, provider_code TEXT NOT NULL, "
                    "symbol_id TEXT NOT NULL, provider_symbol TEXT NOT NULL, "
                    "contract_size_decimal TEXT NOT NULL DEFAULT '1', "
                    "digits_override INTEGER, enabled INTEGER NOT NULL DEFAULT 1, "
                    "effective_from TEXT NOT NULL, effective_to TEXT, "
                    "request_id TEXT NOT NULL DEFAULT '', "
                    "correlation_id TEXT NOT NULL DEFAULT '', "
                    "created_at TEXT NOT NULL, updated_at TEXT NOT NULL, "
                    "UNIQUE (provider_code, provider_symbol, effective_from), "
                    "UNIQUE (provider_code, symbol_id, effective_from)) STRICT",
                    "INSERT INTO broker_symbol_map "
                    "(map_id, provider_code, symbol_id, provider_symbol, "
                    "effective_from, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                ),
                parameter_sets=(
                    (),
                    (
                        "map-1",
                        "mt5",
                        "EURUSD",
                        "EURUSD.r",
                        _NOW,
                        _NOW,
                        _NOW,
                    ),
                ),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )

    assert str(run_broker_migrations(generate_id("req")).status) == "error"
    assert "broker_symbol_map" in _table_names(request_id)
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=("SELECT map_id FROM broker_symbol_map",),
                parameter_sets=((),),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    result = unwrap_data_response(
        response, operation="brokers.retirement.rows", request_id=request_id
    )
    assert [row["map_id"] for row in result.rows] == ["map-1"]
