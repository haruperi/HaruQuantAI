"""Unit tests for isolated SQLite WAL persistence and HostPersistence CRUD operations.

Description:
    Exercises database connection lifecycle, WAL mode configuration, busy timeout
    handling, table schema creation across all 25 operational tables, canonical
    CRUD methods (create_record/create_entity, read_records/read_entity,
    update_record/update_entity, delete_record/delete_entity), and atomic batch
    transactions (apply_batch) on HostPersistence per the contributor constitution.
    Tests run strictly against isolated temporary stores, asserting non-silent
    structured logging for every functional requirement.

Purpose:
    FEAT-HOST-PERSISTENCE: Verify isolated SQLite WAL persistence and CRUD logic.

Key Capabilities:
    - FR-HOST-PERSISTENCE-CREATE: Verify parameterized insertions and entity creation.
      Associated: `test_canonical_crud_operations()`, `test_entity_lifecycle_and_optimistic_cas()`,
      `test_all_25_tables_crud_coverage()`
      Logging: caplog asserts `FR-HOST-PERSISTENCE-CREATE` events.
    - FR-HOST-PERSISTENCE-READ: Verify primary key lookups, filtering, and pagination.
      Associated: `test_canonical_crud_operations()`, `test_read_records_pagination_and_cursor()`
      Logging: caplog asserts `FR-HOST-PERSISTENCE-READ` events.
    - FR-HOST-PERSISTENCE-UPDATE: Verify atomic primary key updates and revision CAS.
      Associated: `test_canonical_crud_operations()`, `test_entity_lifecycle_and_optimistic_cas()`
      Logging: caplog asserts `FR-HOST-PERSISTENCE-UPDATE` events.
    - FR-HOST-PERSISTENCE-DELETE: Verify deletions and foreign key reference guards.
      Associated: `test_canonical_crud_operations()`, `test_foreign_key_guards_on_delete()`
      Logging: caplog asserts `FR-HOST-PERSISTENCE-DELETE` events.
    - FR-HOST-PERSISTENCE-BATCH: Verify atomic multi-row batch execution and rollback.
      Associated: `test_batch_transactions_operations()`, `test_batch_transactions_rollback()`
      Logging: caplog asserts `FR-HOST-PERSISTENCE-BATCH` events.

Python API Usage:
    ```python
    import pytest

    pytest.main(["tests/unit/test_persistence_crud.py", "--no-cov"])
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/test_persistence_crud.py --no-cov
    ```
"""

from __future__ import annotations

import inspect
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from typing import Any

import app.host.persistence as persistence_mod
import pytest
from app.host.persistence import (
    BATCH_FR,
    CREATE_FR,
    DELETE_FR,
    READ_FR,
    UPDATE_FR,
    HostPersistence,
    HostPersistenceCLI,
)

PersistenceError = HostPersistence.Error
RevisionConflictError = HostPersistence.RevisionConflictError


@pytest.fixture(autouse=True)
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect HostPersistence.DEFAULT_DB_PATH to an isolated temporary file."""
    db_file = tmp_path / "test_store.db"
    monkeypatch.setattr(HostPersistence, "DEFAULT_DB_PATH", db_file)
    return db_file


def test_connection_and_wal_mode(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify connection initialization, WAL mode, pragmas, and logging."""
    caplog.set_level(logging.DEBUG)
    conn = HostPersistence._get_connection()
    try:
        journal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        assert str(journal_mode).lower() == "wal"
        foreign_keys = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        assert foreign_keys == 1
        busy_timeout = conn.execute("PRAGMA busy_timeout;").fetchone()[0]
        assert busy_timeout in (5000, 30000)
    finally:
        conn.close()


def test_connection_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify connection failure on invalid paths."""
    dir_path = tmp_path / "a_dir"
    dir_path.mkdir()
    monkeypatch.setattr(HostPersistence, "DEFAULT_DB_PATH", dir_path)
    with pytest.raises(PersistenceError):
        HostPersistence._get_connection()


def test_create_schema_all_25_tables() -> None:
    """Verify automatic creation of all 25 operational database tables."""
    HostPersistence.read_records("host_settings")
    conn = HostPersistence._get_connection()
    try:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        existing_tables = {row[0] for row in cursor.fetchall()}
    finally:
        conn.close()

    for table in HostPersistence.TABLE_PRIMARY_KEYS:
        assert table in existing_tables, f"Missing table: {table}"

    assert len(HostPersistence.TABLE_PRIMARY_KEYS) == 25
    assert len(HostPersistence.PERSISTENCE_TABLES) == 25


def test_canonical_crud_operations(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify canonical CRUD operations across tables with validations and logs."""
    caplog.set_level(logging.DEBUG)

    # 1. Canonical create_record (FR-HOST-PERSISTENCE-CREATE)
    created = HostPersistence.create_record(
        "host_settings",
        values={
            "scope": "canon",
            "key": "k1",
            "value_json": '{"v": 1}',
            "updated_at_utc": "2026-10-19T00:00:00Z",
        },
    )
    assert isinstance(created, dict)
    assert created["created"] is True
    assert created["key"] == ("canon", "k1")
    assert created["pk"] == {"scope": "canon", "key": "k1"}
    assert any(
        CREATE_FR in record.message and getattr(record, "fr_id", None) == CREATE_FR
        for record in caplog.records
    )

    # 2. Canonical read_records (FR-HOST-PERSISTENCE-READ)
    records = HostPersistence.read_records("host_settings", filters={"scope": "canon"})
    assert len(records) == 1
    assert records[0]["key"] == "k1"
    assert any(
        READ_FR in record.message and getattr(record, "fr_id", None) == READ_FR
        for record in caplog.records
    )

    # 3. Canonical update_record (FR-HOST-PERSISTENCE-UPDATE)
    upd = HostPersistence.update_record(
        "host_settings",
        key_columns={"scope": "canon", "key": "k1"},
        updates={"value_json": '{"v": 100}'},
    )
    assert isinstance(upd, dict)
    assert upd["updated"] == 1
    assert upd["affected"] == 1
    updated_rec = HostPersistence.read_records(
        "host_settings", {"scope": "canon", "key": "k1"}
    )
    assert len(updated_rec) == 1 and updated_rec[0]["value_json"] == '{"v": 100}'
    assert any(
        UPDATE_FR in record.message and getattr(record, "fr_id", None) == UPDATE_FR
        for record in caplog.records
    )

    # Upsert via update_record
    upd_upsert = HostPersistence.update_record(
        "host_settings",
        key_columns={"scope": "canon", "key": "k2"},
        updates={
            "scope": "canon",
            "key": "k2",
            "value_json": '{"v": 200}',
            "updated_at_utc": "2026-10-19T00:00:00Z",
        },
        upsert=True,
    )
    assert upd_upsert["upserted"] is True
    assert upd_upsert["affected"] == 1

    # Optimistic revision CAS on update_record
    upd_cas = HostPersistence.update_record(
        "host_settings",
        key_columns={"scope": "canon", "key": "k1"},
        updates={"value_json": '{"v": 101}', "schema_version": 2},
        expected_revision=1,
        revision_col="schema_version",
    )
    assert upd_cas["updated"] == 1

    with pytest.raises(RevisionConflictError):
        HostPersistence.update_record(
            "host_settings",
            key_columns={"scope": "canon", "key": "k1"},
            updates={"value_json": '{"v": 102}'},
            expected_revision=1,
            revision_col="schema_version",
        )

    # 4. Canonical delete_record (FR-HOST-PERSISTENCE-DELETE)
    del_res = HostPersistence.delete_record(
        "host_settings", key_columns={"scope": "canon", "key": "k1"}
    )
    assert isinstance(del_res, dict)
    assert del_res["deleted"] == 1
    del_where = HostPersistence.delete_record(
        "host_settings", key_columns={"scope": "canon"}
    )
    assert del_where["deleted"] == 1
    assert len(HostPersistence.read_records("host_settings", {"scope": "canon"})) == 0
    assert any(
        DELETE_FR in record.message and getattr(record, "fr_id", None) == DELETE_FR
        for record in caplog.records
    )


def test_entity_lifecycle_and_optimistic_cas(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify entity lifecycle, JSON payload handling, and optimistic concurrency."""
    caplog.set_level(logging.DEBUG)

    # Create entity
    created_ent = HostPersistence.create_entity(
        "agent_spec",
        values={
            "entity_id": "agent-01",
            "scope": "workspaces",
            "payload": '{"model": "test-v1"}',
            "revision": 1,
        },
    )
    assert isinstance(created_ent, dict)
    assert created_ent["entity"] == "agent_spec"
    assert created_ent["entity_id"] == "agent-01"
    assert created_ent["created"] is True

    # Read entity
    entities = HostPersistence.read_entity("agent_spec", "agent-01")
    assert isinstance(entities, list)
    assert len(entities) == 1
    entity = entities[0]
    assert entity["entity_id"] == "agent-01"
    assert entity["revision"] == 1
    assert entity["payload"] == '{"model": "test-v1"}'

    # Update entity with matching revision
    upd_ok = HostPersistence.update_entity(
        "agent_spec",
        "agent-01",
        updates={"payload": '{"model": "test-v2"}', "revision": 2},
        expected_revision=1,
    )
    assert isinstance(upd_ok, dict)
    assert upd_ok["updated"] == 1
    assert upd_ok["revision"] == 2
    updated = HostPersistence.read_entity("agent_spec", "agent-01")
    assert len(updated) == 1 and updated[0]["revision"] == 2

    # Update entity without expected_revision auto-increments revision
    upd_auto = HostPersistence.update_entity(
        "agent_spec",
        "agent-01",
        updates={"payload": '{"model": "test-v3"}', "scope": "global"},
    )
    assert upd_auto["updated"] == 1
    assert upd_auto["revision"] == 3
    updated_auto = HostPersistence.read_entity("agent_spec", "agent-01")
    assert len(updated_auto) == 1 and updated_auto[0]["revision"] == 3

    # Update entity with stale revision raises RevisionConflictError
    with pytest.raises(RevisionConflictError) as exc_info:
        HostPersistence.update_entity(
            "agent_spec",
            "agent-01",
            updates={"payload": '{"model": "conflict"}'},
            expected_revision=1,
        )
    assert exc_info.value.expected_revision == 1
    assert exc_info.value.current_revision == 3

    # Update non-existent entity returns updated=0
    missing_ent = HostPersistence.update_entity(
        "agent_spec", "missing-id", {"payload": "{}"}
    )
    assert missing_ent["updated"] == 0

    # Update non-existent record returns updated=0
    missing_rec = HostPersistence.update_record(
        "host_entities",
        {"entity_id": "missing-id", "entity_type": "agent_spec"},
        {"payload": "{}"},
        expected_revision=1,
    )
    assert missing_rec["updated"] == 0

    # Delete entity
    del_ok = HostPersistence.delete_entity("agent_spec", "agent-01")
    assert isinstance(del_ok, dict)
    assert del_ok["deleted"] == 1
    assert HostPersistence.read_entity("agent_spec", "agent-01") == []
    assert HostPersistence.delete_entity("agent_spec", "agent-01")["deleted"] == 0


def test_read_records_pagination_and_cursor() -> None:
    """Verify limit, offset, and keyset cursor pagination in read_records."""
    for i in range(10):
        HostPersistence.create_record(
            "datamgr_tickers",
            {"ticker": f"TICK{i:02d}", "name": f"Ticker {i}", "exchange": "NYSE"},
        )

    # Offset pagination
    page1 = HostPersistence.read_records(
        "datamgr_tickers", order_by="ticker ASC", limit=4, offset=0
    )
    assert len(page1) == 4
    assert page1[0]["ticker"] == "TICK00"
    assert page1[3]["ticker"] == "TICK03"

    page2 = HostPersistence.read_records(
        "datamgr_tickers", order_by="ticker ASC", limit=4, offset=4
    )
    assert len(page2) == 4
    assert page2[0]["ticker"] == "TICK04"

    # Keyset cursor pagination
    cursor_page = HostPersistence.read_records(
        "datamgr_tickers",
        cursor_col="ticker",
        after_cursor="TICK03",
        limit=3,
    )
    assert len(cursor_page) == 3
    assert cursor_page[0]["ticker"] == "TICK04"
    assert cursor_page[2]["ticker"] == "TICK06"

    # Invalid cursor column raises error
    with pytest.raises(PersistenceError):
        HostPersistence.read_records(
            "datamgr_tickers", cursor_col="invalid_col", after_cursor="abc"
        )
    with pytest.raises(PersistenceError):
        HostPersistence.read_records(
            "datamgr_tickers", cursor_col="malicious;drop", after_cursor="abc"
        )


def test_foreign_key_guards_on_delete() -> None:
    """Verify delete_record blocks cascade violations when parent is referenced."""
    b_res = HostPersistence.create_record(
        "datamgr_broker",
        {
            "name": "INTERACTIVE_BROKERS",
            "created_at_utc": "2026-10-19T00:00:00Z",
            "updated_at_utc": "2026-10-19T00:00:00Z",
        },
    )
    bid = b_res["key"]
    HostPersistence.create_record(
        "datamgr_broker_stock",
        {"TICKER": "SPY", "BROKER_ID": bid},
    )

    # Attempting to delete broker with check_references=True raises PersistenceError
    with pytest.raises(PersistenceError) as exc_info:
        HostPersistence.delete_record(
            "datamgr_broker",
            key_columns={"id": bid},
            check_references=True,
        )
    assert "dependent row(s) exist" in str(exc_info.value)

    # Deleting child row first allows parent deletion
    HostPersistence.delete_record(
        "datamgr_broker_stock",
        key_columns={"ID": 1},
    )
    assert (
        HostPersistence.delete_record("datamgr_broker", key_columns={"id": bid})[
            "deleted"
        ]
        == 1
    )


def test_batch_transactions_operations(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify atomic apply_batch transactions with create, update, delete, upsert."""
    caplog.set_level(logging.DEBUG)

    # Empty batch returns 0 operations
    empty_res = HostPersistence.apply_batch([])
    assert empty_res["total_operations"] == 0
    assert empty_res["affected_rows"] == 0

    ops: list[dict[str, Any]] = [
        {
            "op_type": "create",
            "table": "host_settings",
            "values": {
                "scope": "batch",
                "key": "b1",
                "value_json": '{"v": 1}',
                "updated_at_utc": "2026-10-19T00:00:00Z",
            },
        },
        {
            "op_type": "create",
            "table": "host_settings",
            "values": {
                "scope": "batch",
                "key": "b2",
                "value_json": '{"v": 2}',
                "updated_at_utc": "2026-10-19T00:00:00Z",
            },
        },
        {
            "op_type": "update",
            "table": "host_settings",
            "key_columns": {"scope": "batch", "key": "b1"},
            "values": {"value_json": '{"v": 10}'},
        },
        {
            "op_type": "upsert",
            "table": "host_settings",
            "key_columns": {"scope": "batch", "key": "b3"},
            "values": {
                "scope": "batch",
                "key": "b3",
                "value_json": '{"v": 30}',
                "updated_at_utc": "2026-10-19T00:00:00Z",
            },
        },
        {
            "op_type": "delete",
            "table": "host_settings",
            "key_columns": {"scope": "batch", "key": "b2"},
        },
    ]

    result = HostPersistence.apply_batch(ops)
    assert isinstance(result, dict)
    assert result["total_operations"] == 5
    assert result["affected_rows"] >= 4

    # Verify final DB state
    assert (
        HostPersistence.read_records("host_settings", {"scope": "batch", "key": "b1"})[
            0
        ]["value_json"]
        == '{"v": 10}'
    )
    assert (
        len(
            HostPersistence.read_records(
                "host_settings", {"scope": "batch", "key": "b2"}
            )
        )
        == 0
    )
    assert (
        len(
            HostPersistence.read_records(
                "host_settings", {"scope": "batch", "key": "b3"}
            )
        )
        == 1
    )

    assert any(
        BATCH_FR in record.message and getattr(record, "fr_id", None) == BATCH_FR
        for record in caplog.records
    )


def test_batch_transactions_rollback() -> None:
    """Verify all-or-nothing rollback when an operation inside apply_batch fails."""
    HostPersistence.create_record(
        "host_settings",
        {
            "scope": "rb",
            "key": "target",
            "value_json": '{"orig": true}',
            "updated_at_utc": "2026-10-19T00:00:00Z",
        },
    )

    failing_ops: list[dict[str, Any]] = [
        {
            "op_type": "update",
            "table": "host_settings",
            "key_columns": {"scope": "rb", "key": "target"},
            "values": {"value_json": '{"orig": false}'},
        },
        {
            "op_type": "create",
            "table": "unapproved_table_xyz",
            "values": {"foo": "bar"},
        },
    ]

    with pytest.raises(PersistenceError):
        HostPersistence.apply_batch(failing_ops)

    # Prior state preserved: update was rolled back
    row = HostPersistence.read_records(
        "host_settings", {"scope": "rb", "key": "target"}
    )[0]
    assert row["value_json"] == '{"orig": true}'


def test_all_25_tables_crud_coverage() -> None:
    """Verify parameterized create, read, update, delete across all 25 tables."""
    ordered_tables_and_samples: list[tuple[str, dict[str, Any]]] = [
        (
            "datamgr_broker",
            {
                "name": "ALPACA",
                "created_at_utc": "2026-10-19T00:00:00Z",
                "updated_at_utc": "2026-10-19T00:00:00Z",
            },
        ),
        (
            "datamgr_stock_group",
            {"NAME": "INDICES", "SYSTEM": 1},
        ),
        (
            "datamgr_datasets",
            {
                "id": "ds-test-01",
                "source": "import",
                "symbol": "BTCUSD",
                "underlying": "BTC",
                "instrument": "Crypto",
                "timeframe": "5m",
                "broker": "kraken",
                "broker_name": "Kraken Exchange",
                "timezone": "UTC",
                "category": "spot",
                "date_from": "2026-01-01",
                "date_to": "2026-01-02",
                "bars": 500,
                "created_at": "2026-10-19T00:00:00Z",
                "updated_at": "2026-10-19T00:00:00Z",
            },
        ),
        (
            "host_grid_nodes",
            {
                "node_id": "node-grid-01",
                "address": "10.0.0.10",
                "port": 8080,
                "cores": 8,
                "memory_mb": 4096,
                "state": "ONLINE",
                "last_heartbeat_utc": "2026-10-19T00:00:00Z",
            },
        ),
        (
            "host_jobs",
            {
                "job_id": "job-cov-01",
                "owner": "quant_dev",
                "kind": "optimization",
                "status": "RUNNING",
                "progress": 50.0,
                "message": "Optimizing hyperparameters",
                "attempt_id": 1,
                "submitted_at_utc": "2026-10-19T00:00:00Z",
            },
        ),
        ("datamgr_broker_stock", {"TICKER": "NVDA", "BROKER_ID": 1}),
        (
            "datamgr_commodities",
            {
                "code": "GC",
                "name": "Gold",
                "point_value": 100.0,
            },
        ),
        (
            "datamgr_crypto_catalog",
            {
                "exchange": "KRAKEN",
                "symbol": "BTCUSD",
                "point_value": 1.0,
                "tick_size": 0.1,
                "tick_step": 0.1,
                "updated_at": "2026-10-19T00:00:00Z",
            },
        ),
        (
            "datamgr_instruments",
            {
                "symbol": "GBPUSD",
                "created_at_utc": "2026-10-19T00:00:00Z",
                "updated_at_utc": "2026-10-19T00:00:00Z",
            },
        ),
        (
            "datamgr_logs",
            {
                "timestamp_utc": "2026-10-19T00:00:00Z",
                "action": "SYNC",
                "message": "sync ok",
            },
        ),
        (
            "datamgr_operation_log",
            {
                "timestamp_utc": "2026-10-19T00:00:00Z",
                "symbol": "EURUSD",
                "operation": "AUDIT",
                "status": "SUCCESS",
                "message": "OK",
            },
        ),
        (
            "datamgr_quality",
            {
                "report_id": "rep-test-01",
                "dataset_id": "ds-test-01",
                "quality_score": 1.0,
                "total_records": 500,
                "evaluated_at_utc": "2026-10-19T00:00:00Z",
            },
        ),
        (
            "datamgr_sessions",
            {
                "name": "AsianSession",
                "timezone": "UTC",
            },
        ),
        (
            "datamgr_stock",
            {
                "TICKER": "GOOGL",
                "BASKET_ID": 1,
                "DATE_FROM": 1500000000,
            },
        ),
        (
            "datamgr_tickers",
            {
                "ticker": "NQ",
                "name": "Nasdaq Future",
                "exchange": "CME",
            },
        ),
        (
            "host_entities",
            {
                "entity_id": "entity-cov-01",
                "entity_type": "plugin",
                "scope": "global",
                "payload": '{"enabled": true}',
                "revision": 1,
                "created_at_utc": "2026-10-19T00:00:00Z",
                "updated_at_utc": "2026-10-19T00:00:00Z",
            },
        ),
        (
            "host_grid_leases",
            {
                "lease_id": "lease-grid-01",
                "node_id": "node-grid-01",
                "job_id": "job-cov-01",
                "leased_at_utc": "2026-10-19T00:00:00Z",
                "expires_at_utc": "2026-10-19T01:00:00Z",
                "state": "GRANTED",
            },
        ),
        (
            "host_job_attempts",
            {
                "attempt_id": "attempt-cov-01",
                "job_id": "job-cov-01",
                "worker_id": "worker-1",
                "sequence": 1,
                "state": "RUNNING",
                "created_at_utc": "2026-10-19T00:00:00Z",
            },
        ),
        (
            "host_job_events",
            {
                "event_id": "event-cov-01",
                "job_id": "job-cov-01",
                "to_state": "RUNNING",
                "details_json": "{}",
                "created_at_utc": "2026-10-19T00:00:00Z",
            },
        ),
        (
            "host_leases",
            {
                "lease_key": "master-leader-lock",
                "holder_id": "host-instance-01",
                "scope": "global",
                "acquired_at_utc": "2026-10-19T00:00:00Z",
                "expires_at_utc": "2026-10-19T01:00:00Z",
                "metadata": "{}",
            },
        ),
        (
            "host_session",
            {
                "session_id": "sess-cov-01",
                "token_hash": "thash-cov-01",
                "username": "superadmin",
                "peer_id": "192.168.1.1",
                "created_at_utc": "2026-10-19T00:00:00Z",
                "expires_at_utc": "2026-10-20T00:00:00Z",
                "status": "ACTIVE",
            },
        ),
        (
            "host_settings",
            {
                "scope": "cov",
                "key": "audit_level",
                "value_json": '"high"',
                "schema_version": 1,
                "updated_at_utc": "2026-10-19T00:00:00Z",
            },
        ),
        (
            "mt5_commands",
            {
                "command_id": "cmd-cov-01",
                "object_id": "terminal",
                "class_name": "Account",
                "method_name": "Info",
                "args_json": "[]",
                "requires_arm": 0,
                "created_at": 1700000000.0,
                "status": "SUCCESS",
            },
        ),
        (
            "mt5_events",
            {
                "event_type": "CONNECT",
                "payload_json": '{"status": "ok"}',
                "received_at": 1700000000.0,
            },
        ),
        (
            "schema_migrations",
            {
                "version": 999,
                "name": "v999_coverage_migration",
                "applied_at_utc": "2026-10-19T00:00:00Z",
                "checksum": "sha256-dummy",
            },
        ),
    ]

    assert {t for t, _ in ordered_tables_and_samples} == set(
        HostPersistence.PERSISTENCE_TABLES
    )

    pk_dicts: dict[str, dict[str, Any]] = {}

    for table, sample in ordered_tables_and_samples:
        pk_cols = HostPersistence.TABLE_PRIMARY_KEYS[table]

        # 1. Create
        created_res = HostPersistence.create_record(table, sample)
        assert created_res["created"] is True
        pk_dict = created_res["pk"]
        pk_dicts[table] = pk_dict

        # 2. Read
        read_res = HostPersistence.read_records(table, pk_dict)
        assert len(read_res) == 1

        # 3. Update
        non_pk_cols = [
            c
            for c in sample
            if c not in pk_cols
            and c not in ("BROKER_ID", "BASKET_ID", "dataset_id", "node_id", "job_id")
        ]
        if non_pk_cols:
            upd_col = non_pk_cols[0]
            curr_val = sample[upd_col]
            new_val = f"{curr_val}_upd" if isinstance(curr_val, str) else curr_val
            upd_res = HostPersistence.update_record(table, pk_dict, {upd_col: new_val})
            assert upd_res["updated"] == 1

    # 4. Delete in reverse order (children before parents)
    for table, _ in reversed(ordered_tables_and_samples):
        deleted = HostPersistence.delete_record(
            table, pk_dicts[table], check_references=True
        )
        assert deleted["deleted"] == 1


def test_validation_and_unapproved_table_errors() -> None:
    """Verify error checking for unapproved tables and invalid arguments."""
    unapproved = "non_existent_unapproved_table"

    with pytest.raises(PersistenceError) as exc:
        HostPersistence.create_record(unapproved, {"a": 1})
    assert "not in approved table catalogue" in str(exc.value)

    with pytest.raises(PersistenceError):
        HostPersistence.read_records(unapproved)

    with pytest.raises(PersistenceError):
        HostPersistence.update_record(unapproved, {"id": 1}, {"a": 2})

    with pytest.raises(PersistenceError):
        HostPersistence.delete_record(unapproved, {"id": 1})

    # Empty values mapping on create_record
    with pytest.raises(PersistenceError):
        HostPersistence.create_record("host_settings", {})

    # Empty updates mapping
    with pytest.raises(PersistenceError):
        HostPersistence.update_record("host_settings", {"scope": "a", "key": "b"}, {})

    # Missing primary key columns
    with pytest.raises(PersistenceError):
        HostPersistence.update_record(
            "host_settings", {"scope": "a"}, {"value_json": "{}"}
        )

    # Empty delete criteria
    with pytest.raises(PersistenceError):
        HostPersistence.delete_record("host_settings", {})


def test_host_persistence_cli(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify HostPersistenceCLI formatting and execution exit codes."""
    res_dict = {
        "status": "success",
        "total_operations": 2,
        "affected_rows": 2,
        "details": [{"op": "create"}],
    }
    formatted = HostPersistenceCLI.format_output(res_dict)
    assert "total_operations: 2" in formatted
    assert "affected_rows: 2" in formatted

    exit_code = HostPersistenceCLI.run_cli([])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "total_operations: 2" in captured.out


def test_class_contract_and_clean_room() -> None:
    """Verify HostPersistence contract and exact checklist method signatures."""
    assert persistence_mod.__all__ == ["HostPersistence", "HostPersistenceCLI"]

    public_methods = [
        attr
        for attr in dir(HostPersistence)
        if not attr.startswith("_")
        and not isinstance(getattr(HostPersistence, attr), type)
        and callable(getattr(HostPersistence, attr))
    ]

    expected_canonical_methods = {
        "create_record",
        "create_entity",
        "read_records",
        "read_entity",
        "update_record",
        "update_entity",
        "delete_record",
        "delete_entity",
        "apply_batch",
    }

    assert set(public_methods) == expected_canonical_methods, (
        f"Unexpected public methods on HostPersistence: "
        f"{set(public_methods) - expected_canonical_methods}"
    )

    # Verify exact parameter names match blueprint specification
    assert list(inspect.signature(HostPersistence.create_record).parameters)[:2] == [
        "table",
        "values",
    ]
    assert list(inspect.signature(HostPersistence.create_entity).parameters)[:2] == [
        "entity",
        "values",
    ]
    assert list(inspect.signature(HostPersistence.read_records).parameters)[:5] == [
        "table",
        "filters",
        "limit",
        "offset",
        "order_by",
    ]
    assert list(inspect.signature(HostPersistence.read_entity).parameters)[:5] == [
        "entity",
        "entity_id",
        "filters",
        "limit",
        "offset",
    ]
    assert list(inspect.signature(HostPersistence.update_record).parameters)[:4] == [
        "table",
        "key_columns",
        "updates",
        "expected_revision",
    ]
    assert list(inspect.signature(HostPersistence.update_entity).parameters)[:4] == [
        "entity",
        "entity_id",
        "updates",
        "expected_revision",
    ]
    assert list(inspect.signature(HostPersistence.delete_record).parameters)[:2] == [
        "table",
        "key_columns",
    ]
    assert list(inspect.signature(HostPersistence.delete_entity).parameters)[:2] == [
        "entity",
        "entity_id",
    ]
    assert list(inspect.signature(HostPersistence.apply_batch).parameters)[:1] == [
        "operations"
    ]

    # Verify error classes are accessible and legacy BatchOperation/BatchResult shims are absent
    assert HostPersistence.Error is PersistenceError
    assert HostPersistence.RevisionConflictError is RevisionConflictError
    assert not hasattr(HostPersistence, "BatchOperation")
    assert not hasattr(HostPersistence, "BatchResult")


def test_settings_batch_compare_and_set_is_inside_transaction() -> None:
    """A stale batch cannot overwrite any record or session change."""
    HostPersistence.read_records("host_settings")
    barrier = Barrier(2)

    def write(value: str) -> str:
        operation = {
            "op_type": "upsert",
            "table": "host_settings",
            "key_columns": {"scope": "application", "key": "audit"},
            "values": {
                "scope": "application",
                "key": "audit",
                "value_json": value,
                "schema_version": 1,
                "updated_at_utc": "2026-10-20 00:00:00",
            },
        }
        barrier.wait(timeout=5)
        try:
            HostPersistence.apply_batch([operation], expected_settings_revision=0)
            return "committed"
        except HostPersistence.RevisionConflictError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(write, ['"one"', '"two"']))
    assert sorted(results) == ["committed", "conflict"]
    assert len(HostPersistence.read_records("host_settings")) == 1
