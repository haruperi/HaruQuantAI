"""Integration evidence for authoritative Analytics schema retirement."""

from pathlib import Path

import pytest
from app.kernel.identity import generate_id
from app.services.analytics import get_analytics_migrations, run_analytics_migrations
from app.services.data import (
    build_migration_request,
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
    run_domain_migrations,
    unwrap_data_response,
)

_TABLES = {
    "analytics_metric_definitions",
    "analytics_metric_values",
    "analytics_trade_analysis",
    "analytics_pnl_attribution",
    "analytics_equity_curves",
    "analytics_reports",
}


def _configure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Configure one isolated non-production database."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///analytics_migration_test.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")


def _table_names(request_id: str) -> set[str]:
    """Read current SQLite table names through Data's transaction boundary."""
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
        response, operation="analytics.migration.tables", request_id=request_id
    )
    return {row["name"] for row in result.rows}


def test_complete_manifest_retires_empty_tables_and_is_idempotent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Apply both immutable steps and leave no current Analytics tables."""
    _configure(monkeypatch, tmp_path)
    request_id = generate_id("req")
    response = run_analytics_migrations(request_id)
    assert str(response.status) == "success"
    assert _TABLES.isdisjoint(_table_names(request_id))
    assert str(run_analytics_migrations(generate_id("req")).status) == "success"


def test_nonempty_table_blocks_retirement_without_partial_drop(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Fail closed when historical derived data exists."""
    _configure(monkeypatch, tmp_path)
    request_id = generate_id("req")
    step_one = build_migration_request(
        domain="analytics",
        steps=(get_analytics_migrations()[0],),
        request_id=request_id,
        complete_manifest=False,
    )
    assert str(run_domain_migrations(step_one).status) == "success"
    execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(
                    "INSERT INTO analytics_metric_definitions "
                    "(metric_id, metric_code, version, category, formula_hash, "
                    "unit, definition_json, state, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ),
                parameter_sets=(
                    (
                        "metric-1",
                        "net_pnl",
                        "v1",
                        "returns",
                        "a" * 64,
                        "currency",
                        "{}",
                        "active",
                        "2026-08-07T00:00:00Z",
                        "2026-08-07T00:00:00Z",
                    ),
                ),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    response = run_analytics_migrations(generate_id("req"))
    assert str(response.status) == "error"
    assert _table_names(request_id) >= _TABLES
