"""Component evidence for the Indicators retirement-migration guard."""

from pathlib import Path

import pytest
from app.kernel.identity import generate_id
from app.services.data import (
    build_migration_request,
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
    run_domain_migrations,
    unwrap_data_response,
)
from app.services.indicators import run_indicators_migrations
from app.services.indicators.migrations.definitions import INDICATOR_MIGRATIONS

_NOW = "2026-08-06T00:00:00.000Z"


def test_preexisting_rows_cause_002_rollback_with_no_partial_deletion(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify the retirement guard preserves every table when rows exist."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///indicators_guard_test.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")
    request_id = generate_id("req")
    step_one = build_migration_request(
        domain="indicators",
        steps=(INDICATOR_MIGRATIONS[0],),
        request_id=request_id,
        complete_manifest=False,
    )
    assert str(run_domain_migrations(step_one).status) == "success"

    insert_plan = build_statement_plan(
        statements=(
            "INSERT INTO indicator_definitions "
            "(definition_id, indicator_code, version, category, formula_hash, "
            "param_schema_json, output_names_json, lookback_bars, is_causal, "
            "state, request_id, correlation_id, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ),
        parameter_sets=(
            (
                "def-test-1",
                "SMA",
                "v1",
                "trend",
                "hash123",
                "{}",
                '["sma"]',
                14,
                1,
                "active",
                "req1",
                "corr1",
                _NOW,
                _NOW,
            ),
        ),
        max_rows=10,
    )
    execute_transaction(
        build_transaction_request(plan=insert_plan, request_id=request_id)
    )

    assert str(run_indicators_migrations(generate_id("req")).status) == "error"
    query = build_statement_plan(
        statements=("SELECT name FROM sqlite_master WHERE type='table'",),
        parameter_sets=((),),
        max_rows=100,
    )
    response = execute_transaction(
        build_transaction_request(plan=query, request_id=request_id)
    )
    result = unwrap_data_response(
        response,
        operation="indicators.migration.guard_tables",
        request_id=request_id,
    )
    names = {row["name"] for row in result.rows}
    assert {
        "indicator_definitions",
        "indicator_param_sets",
        "indicator_materializations",
    } <= names
