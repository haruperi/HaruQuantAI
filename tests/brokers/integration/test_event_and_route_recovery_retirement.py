"""Integration evidence for guarded Broker event and route-recovery retirement."""

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
    """Configure one isolated non-production database.

    Args:
        monkeypatch: Test fixture for environment mutation.
        tmp_path: Isolated temporary filesystem directory.
    """
    monkeypatch.setenv(
        "DATABASE_URL", "sqlite:///brokers_event_route_retirement_test.sqlite3"
    )
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")


def _table_names(request_id: str) -> set[str]:
    """Read all current SQLite table names through Data.

    Args:
        request_id: Caller trace identifier.

    Returns:
        Set of table names present in the database.
    """
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


def test_complete_manifest_retires_empty_event_and_route_recovery_idempotently(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Apply immutable history and leave no event checkpoints or route recovery tables."""
    _configure(monkeypatch, tmp_path)
    request_id = generate_id("req")
    assert str(run_broker_migrations(request_id).status) == "success"
    tables = _table_names(request_id)
    assert "broker_event_checkpoints" not in tables
    assert "broker_route_recovery" not in tables
    assert "broker_health_history" in tables
    assert str(run_broker_migrations(generate_id("req")).status) == "success"


def test_nonempty_event_checkpoints_blocks_retirement_without_data_loss(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Fail closed and roll back when legacy event checkpoints need operator migration."""
    _configure(monkeypatch, tmp_path)
    request_id = generate_id("req")
    execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(
                    "CREATE TABLE broker_event_checkpoints ("
                    "checkpoint_id TEXT PRIMARY KEY, provider_code TEXT NOT NULL, "
                    "account_ref_digest TEXT NOT NULL, source_stream TEXT NOT NULL, "
                    "source_cursor TEXT NOT NULL, source_sequence INTEGER, "
                    "event_digest TEXT NOT NULL, request_id TEXT NOT NULL, "
                    "updated_at TEXT NOT NULL, "
                    "UNIQUE (provider_code, account_ref_digest, source_stream)) STRICT",
                    "INSERT INTO broker_event_checkpoints "
                    "(checkpoint_id, provider_code, account_ref_digest, source_stream, "
                    "source_cursor, source_sequence, event_digest, request_id, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ),
                parameter_sets=(
                    (),
                    (
                        "chk-1",
                        "mt5",
                        "digest-1",
                        "quotes",
                        "cur-1",
                        1,
                        "d-1",
                        "req-1",
                        _NOW,
                    ),
                ),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )

    assert str(run_broker_migrations(generate_id("req")).status) == "error"
    assert "broker_event_checkpoints" in _table_names(request_id)
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=("SELECT checkpoint_id FROM broker_event_checkpoints",),
                parameter_sets=((),),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    result = unwrap_data_response(
        response, operation="brokers.retirement.rows", request_id=request_id
    )
    assert [row["checkpoint_id"] for row in result.rows] == ["chk-1"]


def test_nonempty_route_recovery_blocks_retirement_without_data_loss(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Fail closed and roll back when legacy route recovery needs operator migration."""
    _configure(monkeypatch, tmp_path)
    request_id = generate_id("req")
    execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(
                    "CREATE TABLE broker_route_recovery ("
                    "route_ref TEXT PRIMARY KEY, provider_code TEXT NOT NULL, "
                    "account_ref_digest TEXT NOT NULL, environment TEXT NOT NULL, "
                    "recovery_cursor TEXT NOT NULL, uncertainty TEXT NOT NULL, "
                    "request_id TEXT NOT NULL, updated_at TEXT NOT NULL) STRICT",
                    "INSERT INTO broker_route_recovery "
                    "(route_ref, provider_code, account_ref_digest, environment, "
                    "recovery_cursor, uncertainty, request_id, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ),
                parameter_sets=(
                    (),
                    (
                        "route-1",
                        "mt5",
                        "digest-1",
                        "demo",
                        "cur-1",
                        "0.0",
                        "req-1",
                        _NOW,
                    ),
                ),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )

    assert str(run_broker_migrations(generate_id("req")).status) == "error"
    assert "broker_route_recovery" in _table_names(request_id)
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=("SELECT route_ref FROM broker_route_recovery",),
                parameter_sets=((),),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    result = unwrap_data_response(
        response, operation="brokers.retirement.rows", request_id=request_id
    )
    assert [row["route_ref"] for row in result.rows] == ["route-1"]
