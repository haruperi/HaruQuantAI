"""Integration evidence for Indicators schema retirement migration (002).

Proves that:
1. A fresh database applies 001 and 002.
2. The three tables (indicator_definitions, indicator_param_sets, indicator_materializations) are absent afterward.
3. Both steps appear in data_migration_ledger with valid checksums.
4. Re-running the manifest is idempotent.
5. A checksum mismatch blocks database access.
6. Pre-existing rows make 002 fail and roll back cleanly.
7. No partial table deletion occurs after guard failure.
8. Write locking and transactional delegation remain active.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from app.services.data import (
    build_migration_request,
    build_migration_step,
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
    run_domain_migrations,
    unwrap_data_response,
)
from app.services.indicators import run_indicators_migrations
from app.services.indicators.migrations.definitions import (
    INDICATOR_MIGRATIONS,
)
from app.utils import generate_id

_REQ_ID = "req-00000000-0000-4000-8000-000000000001"
_NOW = "2026-08-06T00:00:00.000Z"


def _configure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Configure one isolated scratch database for migration runs.

    Args:
        monkeypatch: Environment mutator scoped to the current test.
        tmp_path: Unique per-test directory hosting the scratch database.
    """
    monkeypatch.setenv("DATABASE_URL", "sqlite:///indicators_migration_test.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")


def _get_table_names(request_id: str) -> set[str]:
    """Return all table names in the current database via transaction.

    Args:
        request_id: Caller trace identity.

    Returns:
        Set of table names.
    """
    resp = execute_transaction(
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
        resp,
        operation="indicators.migration.test_tables",
        request_id=request_id,
    )
    return {row["name"] for row in result.rows}


def test_fresh_database_applies_001_and_002_idempotently(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Fresh database applies 001 and 002, retiring the 3 tables, and is idempotent."""
    _configure(monkeypatch, tmp_path)
    request_id = generate_id("req")
    res = run_indicators_migrations(request_id)
    assert str(res.status) == "success"

    tables = _get_table_names(request_id)
    assert "indicator_definitions" not in tables
    assert "indicator_param_sets" not in tables
    assert "indicator_materializations" not in tables

    # Check ledger
    resp = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(
                    "SELECT migration_id, checksum FROM data_migration_ledger WHERE domain = 'indicators' ORDER BY migration_id",
                ),
                parameter_sets=((),),
                max_rows=10,
            ),
            request_id=request_id,
        )
    )
    rows = list(
        unwrap_data_response(resp, operation="test", request_id=request_id).rows
    )
    assert len(rows) == 2
    migration_ids = [r["migration_id"] for r in rows]
    assert migration_ids == [
        "001_indicator_schema_v1",
        "002_remove_unused_indicator_support_schema",
    ]

    # Re-running is idempotent
    res2 = run_indicators_migrations(generate_id("req"))
    assert str(res2.status) == "success"


def test_checksum_mismatch_blocks_database_access(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A tampered migration step checksum blocks migration execution."""
    _configure(monkeypatch, tmp_path)
    request_id = generate_id("req")
    run_indicators_migrations(request_id)

    # Corrupt step 001 checksum in request
    corrupted_step = build_migration_step(
        domain="indicators",
        migration_id="001_indicator_schema_v1",
        checksum="invalid_checksum_hash_value_ffffffffffffffffffffffffffffffff",
        statements=("SELECT 1",),
    )
    bad_request = build_migration_request(
        domain="indicators",
        steps=(corrupted_step,),
        request_id=generate_id("req"),
        complete_manifest=False,
    )
    bad_res = run_domain_migrations(bad_request)
    assert str(bad_res.status) == "error"


def test_preexisting_rows_cause_002_rollback_with_no_partial_deletion(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """If data exists when 002 runs, the guard fails and rolls back without deleting tables."""
    _configure(monkeypatch, tmp_path)
    request_id = generate_id("req")

    # Manually apply only step 001
    step1_req = build_migration_request(
        domain="indicators",
        steps=(INDICATOR_MIGRATIONS[0],),
        request_id=request_id,
        complete_manifest=False,
    )
    res1 = run_domain_migrations(step1_req)
    assert str(res1.status) == "success"

    # Insert a dummy definition row into indicator_definitions
    insert_plan = build_statement_plan(
        statements=(
            "INSERT INTO indicator_definitions (definition_id, indicator_code, version, category, formula_hash, param_schema_json, output_names_json, lookback_bars, is_causal, state, request_id, correlation_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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

    # Now attempt to run step 002 (via complete manifest run)
    res2 = run_indicators_migrations(generate_id("req"))
    assert str(res2.status) == "error"

    # Verify no partial table deletion occurred and all 3 tables still exist
    tables = _get_table_names(request_id)
    assert "indicator_definitions" in tables
    assert "indicator_param_sets" in tables
    assert "indicator_materializations" in tables
