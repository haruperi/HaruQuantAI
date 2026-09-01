"""Unit tests for retained migration tombstones and state preservation.

Traces to: P8-T02, Gate G8
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from app.kernel.identity import generate_id
from app.services.data.contracts.errors import DataError
from app.services.data.persistence.contracts import (
    MigrationRequest,
    MigrationStep,
    MigrationTombstone,
)
from app.services.data.persistence.migrations import _run_domain_migrations_raw


def _configure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    db_file = tmp_path / "migrations.sqlite3"
    monkeypatch.setenv("DATABASE_URL", "sqlite:///migrations.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")
    return db_file


def _step(domain: str, migration_id: str, checksum: str, sql: str) -> MigrationStep:
    return MigrationStep(
        domain=domain,
        migration_id=migration_id,
        checksum=checksum,
        statements=(sql,),
    )


def test_migrations_succeed_when_all_owners_present(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify normal migration application when all steps are declared in request."""
    db_file = _configure(monkeypatch, tmp_path)

    step1 = _step(
        "test_dom",
        "0001_init",
        "chk_1",
        "CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT);",
    )
    req = MigrationRequest(
        domain="test_dom",
        steps=(step1,),
        request_id=generate_id("req"),
        complete_manifest=True,
    )

    result = _run_domain_migrations_raw(req)
    assert result.applied_ids == ("0001_init",)
    assert result.skipped_ids == ()

    # Verify table exists in SQLite
    conn = sqlite3.connect(db_file)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'"
        )
        assert cursor.fetchone() is not None
    finally:
        conn.close()


def test_owner_absent_applied_migration_succeeds_with_valid_tombstone(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify an applied migration whose owner is absent succeeds when a valid tombstone supplies the checksum."""
    _configure(monkeypatch, tmp_path)

    # 1. Apply initial migration
    step1 = _step(
        "test_dom",
        "0001_init",
        "chk_1",
        "CREATE TABLE orders (id INTEGER PRIMARY KEY, symbol TEXT);",
    )
    req1 = MigrationRequest(
        domain="test_dom",
        steps=(step1,),
        request_id=generate_id("req"),
        complete_manifest=True,
    )
    _run_domain_migrations_raw(req1)

    # 2. Simulate owner absence with a tombstone
    tombstone = MigrationTombstone(
        domain="test_dom",
        migration_id="0001_init",
        checksum="chk_1",
        owner_provider_id="trading.orders.provider",
        state_schema_id="trading_orders",
    )
    step2 = _step(
        "test_dom",
        "0002_other",
        "chk_2",
        "CREATE TABLE other_table (id INTEGER PRIMARY KEY);",
    )
    req2 = MigrationRequest(
        domain="test_dom",
        steps=(step2,),
        tombstones=(tombstone,),
        request_id=generate_id("req"),
        complete_manifest=True,
    )

    result2 = _run_domain_migrations_raw(req2)
    assert result2.applied_ids == ("0002_other",)


def test_owner_absent_applied_migration_fails_without_tombstone_when_complete_manifest(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify an applied migration absent from request without tombstone raises SCHEMA_MIGRATION_FAILED."""
    _configure(monkeypatch, tmp_path)

    step1 = _step(
        "test_dom",
        "0001_init",
        "chk_1",
        "CREATE TABLE orders (id INTEGER PRIMARY KEY);",
    )
    req1 = MigrationRequest(
        domain="test_dom",
        steps=(step1,),
        request_id=generate_id("req"),
        complete_manifest=True,
    )
    _run_domain_migrations_raw(req1)

    # Subsequent request omitting step1 without tombstone
    step2 = _step(
        "test_dom",
        "0002_other",
        "chk_2",
        "CREATE TABLE other (id INTEGER PRIMARY KEY);",
    )
    req2 = MigrationRequest(
        domain="test_dom",
        steps=(step2,),
        tombstones=(),
        request_id=generate_id("req"),
        complete_manifest=True,
    )

    with pytest.raises(DataError) as exc_info:
        _run_domain_migrations_raw(req2)
    assert exc_info.value.code == "SCHEMA_MIGRATION_FAILED"
    assert exc_info.value.safe_details.get("stage") == "manifest_validation"


def test_owner_absent_applied_migration_fails_with_checksum_mismatch_tombstone(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify tombstone with mismatched checksum raises checksum_validation error."""
    _configure(monkeypatch, tmp_path)

    step1 = _step(
        "test_dom",
        "0001_init",
        "chk_expected",
        "CREATE TABLE orders (id INTEGER PRIMARY KEY);",
    )
    req1 = MigrationRequest(
        domain="test_dom",
        steps=(step1,),
        request_id=generate_id("req"),
        complete_manifest=True,
    )
    _run_domain_migrations_raw(req1)

    tombstone = MigrationTombstone(
        domain="test_dom",
        migration_id="0001_init",
        checksum="chk_WRONG",
        owner_provider_id="trading.orders.provider",
        state_schema_id="trading_orders",
    )
    step2 = _step(
        "test_dom",
        "0002_other",
        "chk_2",
        "CREATE TABLE other (id INTEGER PRIMARY KEY);",
    )
    req2 = MigrationRequest(
        domain="test_dom",
        steps=(step2,),
        tombstones=(tombstone,),
        request_id=generate_id("req"),
        complete_manifest=True,
    )

    with pytest.raises(DataError) as exc_info:
        _run_domain_migrations_raw(req2)
    assert exc_info.value.code == "SCHEMA_MIGRATION_FAILED"
    assert exc_info.value.safe_details.get("stage") == "checksum_validation"


def test_tombstone_cannot_authorize_unapplied_new_migration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify tombstone for an unapplied migration does not create tables or apply SQL."""
    _configure(monkeypatch, tmp_path)

    tombstone = MigrationTombstone(
        domain="test_dom",
        migration_id="0001_unapplied",
        checksum="chk_1",
        owner_provider_id="test.provider",
        state_schema_id="test_schema",
    )
    step = _step(
        "test_dom",
        "0002_step",
        "chk_2",
        "CREATE TABLE valid_table (id INTEGER PRIMARY KEY);",
    )
    req = MigrationRequest(
        domain="test_dom",
        steps=(step,),
        tombstones=(tombstone,),
        request_id=generate_id("req"),
        complete_manifest=True,
    )

    result = _run_domain_migrations_raw(req)
    assert result.applied_ids == ("0002_step",)


def test_duplicate_step_and_tombstone_identifier_fails_request_validation() -> None:
    """Verify MigrationRequest rejects overlapping step and tombstone migration_id."""
    step = _step("test_dom", "0001_id", "chk_1", "CREATE TABLE a (id INT);")
    tombstone = MigrationTombstone(
        domain="test_dom",
        migration_id="0001_id",
        checksum="chk_1",
        owner_provider_id="prov",
        state_schema_id="schema",
    )

    with pytest.raises(DataError) as exc_info:
        MigrationRequest(
            domain="test_dom",
            steps=(step,),
            tombstones=(tombstone,),
            request_id=generate_id("req"),
        )
    assert exc_info.value.code == "INVALID_INPUT"


def test_database_tables_and_data_are_preserved_across_tombstoned_startup(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify table records are retained across uninstalled provider restarts with tombstones."""
    db_file = _configure(monkeypatch, tmp_path)

    # 1. Install & migrate
    step1 = _step(
        "test_dom",
        "0001_init",
        "chk_1",
        "CREATE TABLE records (id INTEGER PRIMARY KEY, val TEXT);",
    )
    req1 = MigrationRequest(
        domain="test_dom",
        steps=(step1,),
        request_id=generate_id("req"),
        complete_manifest=True,
    )
    _run_domain_migrations_raw(req1)

    # Insert data
    conn1 = sqlite3.connect(db_file)
    try:
        conn1.execute("INSERT INTO records (id, val) VALUES (1, 'retained_data')")
        conn1.commit()
    finally:
        conn1.close()

    # 2. Restart with tombstone
    tombstone = MigrationTombstone(
        domain="test_dom",
        migration_id="0001_init",
        checksum="chk_1",
        owner_provider_id="provider.records",
        state_schema_id="schema.records",
    )
    step2 = _step(
        "test_dom", "0002_step2", "chk_2", "CREATE TABLE temp (id INTEGER PRIMARY KEY);"
    )
    req2 = MigrationRequest(
        domain="test_dom",
        steps=(step2,),
        tombstones=(tombstone,),
        request_id=generate_id("req"),
        complete_manifest=True,
    )
    _run_domain_migrations_raw(req2)

    # Verify data is still intact
    conn2 = sqlite3.connect(db_file)
    try:
        cursor = conn2.cursor()
        cursor.execute("SELECT val FROM records WHERE id=1")
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "retained_data"
    finally:
        conn2.close()
