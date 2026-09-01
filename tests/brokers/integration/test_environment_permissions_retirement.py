"""Integration evidence for guarded Broker environment-permissions retirement."""

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
    monkeypatch.setenv("DATABASE_URL", "sqlite:///brokers_env_retirement_test.sqlite3")
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


def test_complete_manifest_retires_empty_environment_permissions_idempotently(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Apply immutable history and leave no current Broker environment permissions table.

    Args:
        monkeypatch: Test fixture for environment isolation.
        tmp_path: Temporary test directory.
    """
    _configure(monkeypatch, tmp_path)
    request_id = generate_id("req")
    assert str(run_broker_migrations(request_id).status) == "success"
    assert "broker_environment_permissions" not in _table_names(request_id)
    assert str(run_broker_migrations(generate_id("req")).status) == "success"


def test_nonempty_environment_permissions_blocks_retirement_without_data_loss(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Fail closed and roll back when legacy environment permissions need operator migration.

    Args:
        monkeypatch: Test fixture for environment isolation.
        tmp_path: Temporary test directory.
    """
    _configure(monkeypatch, tmp_path)
    request_id = generate_id("req")
    execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(
                    "CREATE TABLE broker_environment_permissions ("
                    "permission_id TEXT PRIMARY KEY, provider_code TEXT NOT NULL, "
                    "account_ref_digest TEXT NOT NULL, environment TEXT NOT NULL, "
                    "allow_read INTEGER NOT NULL CHECK (allow_read IN (0, 1)), "
                    "allow_mutation INTEGER NOT NULL CHECK (allow_mutation IN (0, 1)), "
                    "enabled INTEGER NOT NULL CHECK (enabled IN (0, 1)), "
                    "effective_from TEXT NOT NULL, effective_to TEXT, "
                    "request_id TEXT NOT NULL, updated_at TEXT NOT NULL, "
                    "UNIQUE (provider_code, account_ref_digest, environment, effective_from)) STRICT",
                    "INSERT INTO broker_environment_permissions "
                    "(permission_id, provider_code, account_ref_digest, environment, "
                    "allow_read, allow_mutation, enabled, effective_from, request_id, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ),
                parameter_sets=(
                    (),
                    (
                        "perm-1",
                        "mt5",
                        "digest-1",
                        "demo",
                        1,
                        1,
                        1,
                        _NOW,
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
    assert "broker_environment_permissions" in _table_names(request_id)
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(
                    "SELECT permission_id FROM broker_environment_permissions",
                ),
                parameter_sets=((),),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    result = unwrap_data_response(
        response, operation="brokers.retirement.rows", request_id=request_id
    )
    assert [row["permission_id"] for row in result.rows] == ["perm-1"]
