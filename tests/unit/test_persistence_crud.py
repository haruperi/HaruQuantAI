"""Unit tests for isolated SQLite WAL persistence and CRUD operations.

Description:
    Exercises database connection lifecycle, WAL mode configuration, busy timeout
    handling, table schema creation across all 25 operational tables, and CRUD
    operations across host infrastructure, data manager, and transport domains.
    Tests run strictly against isolated temporary database stores or in-memory
    databases, asserting non-silent structured logging for every functional
    requirement.

Purpose:
    FEAT-HOST-PERSISTENCE: Verify isolated SQLite WAL persistence and CRUD logic.

Key Capabilities:
    - FR-HOST-PERSISTENCE-CONNECT: Verify WAL mode, timeout, and connection errors.
      Associated: `test_connection_and_wal_mode()`, `test_connection_error()`
      Logging: caplog asserts `FR-HOST-PERSISTENCE-CONNECT` events.
    - FR-HOST-PERSISTENCE-CREATE-SCHEMA: Verify creation of all 25 tables.
      Associated: `test_create_schema_all_25_tables()`, `test_schema_error()`
      Logging: caplog asserts `FR-HOST-PERSISTENCE-CREATE-SCHEMA` events.
    - FR-HOST-PERSISTENCE-INSERT: Verify parameterized insertions and validation.
      Associated: `test_crud_host_settings()`, `test_crud_host_session()`,
      `test_crud_host_jobs()`, `test_crud_datamgr_broker_and_dataset()`,
      `test_insert_validation_errors()`
      Logging: caplog asserts `FR-HOST-PERSISTENCE-INSERT` events.
    - FR-HOST-PERSISTENCE-READ-BY-PK: Verify primary key and composite lookups.
      Associated: `test_crud_host_settings()`, `test_read_by_pk_missing_columns()`
      Logging: caplog asserts `FR-HOST-PERSISTENCE-READ-BY-PK` events.
    - FR-HOST-PERSISTENCE-LIST: Verify filtering, ordering, pagination, and counts.
      Associated: `test_read_rows_filtering_and_pagination()`
      Logging: caplog asserts `FR-HOST-PERSISTENCE-LIST` events.
    - FR-HOST-PERSISTENCE-UPDATE-BY-PK: Verify atomic primary key updates.
      Associated: `test_crud_host_settings()`, `test_update_validation_errors()`
      Logging: caplog asserts `FR-HOST-PERSISTENCE-UPDATE-BY-PK` events.
    - FR-HOST-PERSISTENCE-DELETE-BY-PK: Verify primary key deletions.
      Associated: `test_crud_host_settings()`, `test_delete_by_pk_errors()`
      Logging: caplog asserts `FR-HOST-PERSISTENCE-DELETE-BY-PK` events.
    - FR-HOST-PERSISTENCE-DELETE-WHERE: Verify conditional multi-row deletions.
      Associated: `test_delete_rows_where()`
      Logging: caplog asserts `FR-HOST-PERSISTENCE-DELETE-WHERE` events.
    - FR-HOST-PERSISTENCE-BATCH-TRANSACTIONS: Verify atomic multi-row batch execution
      and all-or-nothing rollback semantics on failure.
      Associated: `test_batch_transactions_operations()`, `test_batch_transactions_rollback()`
      Logging: caplog asserts `FR-HOST-PERSISTENCE-BATCH-TRANSACTIONS` events.

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

import logging
import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest
from app.host.persistence import (
    BATCH_SETTINGS_REVISION_FR,
    BATCH_TRANSACTIONS_FR,
    CONNECT_FR,
    COUNT_FR,
    CREATE_SCHEMA_FR,
    DELETE_PK_FR,
    DELETE_WHERE_FR,
    INSERT_FR,
    LIST_FR,
    PERSISTENCE_TABLES,
    READ_PK_FR,
    SCHEMA_DDL,
    TABLE_DDL_MAP,
    TABLE_FOREIGN_KEY_GUARDS,
    TABLE_PRIMARY_KEYS,
    UPDATE_FR,
    BatchOperation,
    BatchResult,
    PersistenceError,
    RevisionConflictError,
    TransactionsCLI,
    apply_batch,
    batch_save_host_settings,
    count_rows,
    create_datamgr_broker,
    create_datamgr_broker_stock,
    create_datamgr_commodity,
    create_datamgr_crypto_catalog,
    create_datamgr_dataset,
    create_datamgr_instrument,
    create_datamgr_log,
    create_datamgr_operation_log,
    create_datamgr_quality_report,
    create_datamgr_session,
    create_datamgr_stock,
    create_datamgr_stock_group,
    create_datamgr_ticker,
    create_entity,
    create_host_entity,
    create_host_grid_lease,
    create_host_grid_node,
    create_host_job,
    create_host_job_attempt,
    create_host_job_event,
    create_host_lease,
    create_host_session,
    create_host_setting,
    create_mt5_command,
    create_mt5_event,
    create_record,
    create_schema,
    create_schema_migration,
    delete_datamgr_broker,
    delete_datamgr_broker_stock,
    delete_datamgr_commodity,
    delete_datamgr_crypto_catalog,
    delete_datamgr_dataset,
    delete_datamgr_instrument,
    delete_datamgr_log,
    delete_datamgr_operation_log,
    delete_datamgr_quality_report,
    delete_datamgr_session,
    delete_datamgr_stock,
    delete_datamgr_stock_group,
    delete_datamgr_ticker,
    delete_entity,
    delete_host_entity,
    delete_host_grid_lease,
    delete_host_grid_node,
    delete_host_job,
    delete_host_job_attempt,
    delete_host_job_event,
    delete_host_lease,
    delete_host_session,
    delete_host_setting,
    delete_mt5_command,
    delete_mt5_event,
    delete_record,
    delete_row_by_pk,
    delete_rows,
    delete_schema_migration,
    ensure_table_schema,
    get_connection,
    get_datamgr_broker,
    get_datamgr_broker_by_name,
    get_datamgr_broker_stock,
    get_datamgr_commodity,
    get_datamgr_crypto_catalog,
    get_datamgr_dataset,
    get_datamgr_instrument,
    get_datamgr_log,
    get_datamgr_operation_log,
    get_datamgr_quality_report,
    get_datamgr_session,
    get_datamgr_stock,
    get_datamgr_stock_group,
    get_datamgr_ticker,
    get_host_entity,
    get_host_grid_lease,
    get_host_grid_node,
    get_host_job,
    get_host_job_attempt,
    get_host_job_attempts,
    get_host_job_event,
    get_host_job_events,
    get_host_lease,
    get_host_session,
    get_host_session_by_token_hash,
    get_host_setting,
    get_mt5_command,
    get_mt5_event,
    get_schema_migration,
    get_schema_migrations,
    insert_row,
    list_datamgr_broker_stocks,
    list_datamgr_brokers,
    list_datamgr_commodities,
    list_datamgr_crypto_catalogs,
    list_datamgr_datasets,
    list_datamgr_instruments,
    list_datamgr_logs,
    list_datamgr_operation_logs,
    list_datamgr_quality_reports,
    list_datamgr_sessions,
    list_datamgr_stock_groups,
    list_datamgr_stocks,
    list_datamgr_tickers,
    list_host_entities,
    list_host_grid_leases,
    list_host_grid_nodes,
    list_host_job_attempts,
    list_host_job_events,
    list_host_jobs,
    list_host_leases,
    list_host_sessions,
    list_host_settings,
    list_mt5_commands,
    list_mt5_events,
    list_schema_migrations,
    read_entity,
    read_record,
    read_records,
    read_row_by_pk,
    read_rows,
    record_host_job_event,
    save_host_job,
    save_host_session,
    update_datamgr_broker,
    update_datamgr_broker_stock,
    update_datamgr_commodity,
    update_datamgr_crypto_catalog,
    update_datamgr_dataset,
    update_datamgr_instrument,
    update_datamgr_log,
    update_datamgr_operation_log,
    update_datamgr_quality_report,
    update_datamgr_session,
    update_datamgr_stock,
    update_datamgr_stock_group,
    update_datamgr_ticker,
    update_entity,
    update_host_entity,
    update_host_grid_lease,
    update_host_grid_node,
    update_host_grid_node_heartbeat,
    update_host_job,
    update_host_job_attempt,
    update_host_job_event,
    update_host_lease,
    update_host_session,
    update_host_session_status,
    update_host_setting,
    update_mt5_command,
    update_mt5_event,
    update_record,
    update_row_by_pk,
    update_schema_migration,
)


@pytest.fixture
def temp_db(tmp_path: Path) -> Generator[sqlite3.Connection]:
    """Provide an initialized SQLite connection to an isolated temporary store."""
    db_file = tmp_path / "test_store.db"
    conn = get_connection(db_file)
    create_schema(conn)
    try:
        yield conn
    finally:
        conn.close()


def test_connection_and_wal_mode(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify connection initialization, WAL mode, pragmas, and logging."""
    caplog.set_level(logging.DEBUG)
    db_file = tmp_path / "test_wal.db"
    conn = get_connection(db_file)
    try:
        journal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        assert str(journal_mode).lower() == "wal"
        foreign_keys = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        assert foreign_keys == 1
        busy_timeout = conn.execute("PRAGMA busy_timeout;").fetchone()[0]
        assert busy_timeout == 5000
    finally:
        conn.close()

    assert any(
        CONNECT_FR in record.message and getattr(record, "fr_id", None) == CONNECT_FR
        for record in caplog.records
    )


def test_connection_error(caplog: pytest.LogCaptureFixture) -> None:
    """Verify connection failure on invalid paths."""
    caplog.set_level(logging.DEBUG)
    invalid_path = Path("NUL:/nonexistent/invalid\0dir/db.sqlite")
    with pytest.raises(PersistenceError):
        get_connection(invalid_path)

    assert any(
        CONNECT_FR in record.message and record.levelno == logging.ERROR
        for record in caplog.records
    )


def test_create_schema_all_25_tables(
    temp_db: sqlite3.Connection,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify idempotent creation of all 25 operational database tables."""
    caplog.set_level(logging.INFO)
    cursor = temp_db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
    )
    existing_tables = {row[0] for row in cursor.fetchall()}

    for table in TABLE_PRIMARY_KEYS:
        assert table in existing_tables, f"Missing table: {table}"

    assert len(TABLE_PRIMARY_KEYS) == 25

    # Verify idempotency
    create_schema(temp_db)

    assert any(
        CREATE_SCHEMA_FR in record.message
        and getattr(record, "fr_id", None) == CREATE_SCHEMA_FR
        for record in caplog.records
    )


def test_crud_host_settings(
    temp_db: sqlite3.Connection,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify full CRUD lifecycle on host_settings with composite primary key."""
    caplog.set_level(logging.DEBUG)

    # 1. Create
    pk = create_host_setting(
        temp_db, "system", "general", '{"theme": "dark"}', schema_version=1
    )
    assert pk == ("system", "general")

    # 2. Read
    row = get_host_setting(temp_db, "system", "general")
    assert row is not None
    assert row["value_json"] == '{"theme": "dark"}'
    assert row["schema_version"] == 1

    # List
    all_settings = list_host_settings(temp_db, scope="system")
    assert len(all_settings) == 1
    assert all_settings[0]["key"] == "general"

    # 3. Update
    updated = update_host_setting(
        temp_db, "system", "general", '{"theme": "light"}', schema_version=2
    )
    assert updated is True
    row_updated = get_host_setting(temp_db, "system", "general")
    assert row_updated is not None
    assert row_updated["value_json"] == '{"theme": "light"}'
    assert row_updated["schema_version"] == 2

    # 4. Delete
    deleted = delete_host_setting(temp_db, "system", "general")
    assert deleted is True
    assert get_host_setting(temp_db, "system", "general") is None

    # Check logs
    assert any(getattr(r, "fr_id", None) == INSERT_FR for r in caplog.records)
    assert any(getattr(r, "fr_id", None) == READ_PK_FR for r in caplog.records)
    assert any(getattr(r, "fr_id", None) == UPDATE_FR for r in caplog.records)
    assert any(getattr(r, "fr_id", None) == DELETE_PK_FR for r in caplog.records)


def test_crud_host_session(temp_db: sqlite3.Connection) -> None:
    """Verify CRUD operations on host_session table."""
    sid = create_host_session(
        temp_db,
        "s-100",
        "hash-abc",
        "admin",
        "peer-1",
        created_at_utc="2026-10-14T00:00:00Z",
        expires_at_utc="2026-10-15T00:00:00Z",
        status="ACTIVE",
    )
    assert sid == "s-100"

    session = get_host_session(temp_db, "s-100")
    assert session is not None
    assert session["username"] == "admin"
    assert session["status"] == "ACTIVE"

    by_hash = get_host_session_by_token_hash(temp_db, "hash-abc")
    assert by_hash is not None
    assert by_hash["session_id"] == "s-100"

    assert get_host_session_by_token_hash(temp_db, "nonexistent") is None

    # Update
    updated = update_host_session_status(
        temp_db, "s-100", "REVOKED", revoked_at_utc="2026-10-14T01:00:00Z"
    )
    assert updated is True
    session_rev = get_host_session(temp_db, "s-100")
    assert session_rev is not None
    assert session_rev["status"] == "REVOKED"
    assert session_rev["revoked_at_utc"] == "2026-10-14T01:00:00Z"

    # Delete
    deleted = delete_host_session(temp_db, "s-100")
    assert deleted is True
    assert get_host_session(temp_db, "s-100") is None


def test_crud_host_jobs(temp_db: sqlite3.Connection) -> None:
    """Verify CRUD operations on host_jobs and related attempt/event tables."""
    jid = create_host_job(
        temp_db,
        "j-001",
        owner="test-user",
        kind="build",
        status="running",
        progress=0.5,
    )
    assert jid == "j-001"

    job = get_host_job(temp_db, "j-001")
    assert job is not None
    assert job["owner"] == "test-user"
    assert job["progress"] == 0.5

    # Insert attempt and event
    insert_row(
        temp_db,
        "host_job_attempts",
        {
            "attempt_id": "att-1",
            "job_id": "j-001",
            "worker_id": "w-1",
            "sequence": 1,
            "state": "running",
            "created_at_utc": "2026-10-14T00:00:00Z",
        },
    )
    insert_row(
        temp_db,
        "host_job_events",
        {
            "event_id": "ev-1",
            "job_id": "j-001",
            "attempt_id": "att-1",
            "to_state": "running",
            "details_json": "{}",
            "created_at_utc": "2026-10-14T00:00:00Z",
        },
    )

    attempts = get_host_job_attempts(temp_db, "j-001")
    assert len(attempts) == 1
    assert attempts[0]["attempt_id"] == "att-1"

    events = get_host_job_events(temp_db, "j-001")
    assert len(events) == 1
    assert events[0]["event_id"] == "ev-1"

    # Update attempt & job
    assert update_host_job_attempt(temp_db, "att-1", {"state": "completed"}) is True
    assert (
        update_host_job(temp_db, "j-001", {"status": "completed", "progress": 1.0})
        is True
    )

    job_done = get_host_job(temp_db, "j-001")
    assert job_done is not None
    assert job_done["status"] == "completed"
    assert job_done["progress"] == 1.0

    # List jobs
    jobs = list_host_jobs(temp_db, status="completed")
    assert len(jobs) == 1

    # Delete
    assert delete_row_by_pk(temp_db, "host_job_events", {"event_id": "ev-1"}) == 1
    assert delete_row_by_pk(temp_db, "host_job_attempts", {"attempt_id": "att-1"}) == 1
    assert delete_host_job(temp_db, "j-001") is True


def test_crud_host_entities_leases_and_grid(
    temp_db: sqlite3.Connection,
) -> None:
    """Verify operations on host_entities, host_leases, and host_grid_nodes."""
    # Entity
    insert_row(
        temp_db,
        "host_entities",
        {
            "entity_id": "e-1",
            "entity_type": "strategy",
            "scope": "workspace",
            "payload": '{"name": "Strat1"}',
            "revision": 1,
            "created_at_utc": "2026-10-14T00:00:00Z",
            "updated_at_utc": "2026-10-14T00:00:00Z",
        },
    )
    entity = get_host_entity(temp_db, "e-1", "strategy")
    assert entity is not None
    assert entity["payload"] == '{"name": "Strat1"}'

    assert (
        update_host_entity(
            temp_db, "e-1", "strategy", '{"name": "Strat1-mod"}', revision=2
        )
        is True
    )
    assert delete_host_entity(temp_db, "e-1", "strategy") is True

    # Lease
    insert_row(
        temp_db,
        "host_leases",
        {
            "lease_key": "lease-abc",
            "holder_id": "worker-1",
            "scope": "backtest",
            "acquired_at_utc": "2026-10-14T00:00:00Z",
            "expires_at_utc": "2026-10-14T01:00:00Z",
            "metadata": "{}",
        },
    )
    lease = get_host_lease(temp_db, "lease-abc")
    assert lease is not None
    assert lease["holder_id"] == "worker-1"
    assert delete_host_lease(temp_db, "lease-abc") is True

    # Grid node
    insert_row(
        temp_db,
        "host_grid_nodes",
        {
            "node_id": "node-1",
            "host": "127.0.0.1",
            "port": 9000,
            "cores": 8,
            "memory_mb": 16384,
            "state": "idle",
            "last_heartbeat_utc": "2026-10-14T00:00:00Z",
        },
    )
    node = get_host_grid_node(temp_db, "node-1")
    assert node is not None
    assert node["cores"] == 8

    assert (
        update_host_grid_node_heartbeat(
            temp_db, "node-1", "busy", "2026-10-14T00:05:00Z"
        )
        is True
    )
    assert delete_host_grid_node(temp_db, "node-1") is True


def test_crud_datamgr_broker_and_dataset(
    temp_db: sqlite3.Connection,
) -> None:
    """Verify operations on datamgr_broker and datamgr_datasets."""
    bid = create_datamgr_broker(
        temp_db,
        "Dukascopy",
        created_at_utc="2026-10-14T00:00:00Z",
        updated_at_utc="2026-10-14T00:00:00Z",
        description="Swiss Forex Broker",
    )
    assert bid > 0

    broker = get_datamgr_broker(temp_db, bid)
    assert broker is not None
    assert broker["name"] == "Dukascopy"

    by_name = get_datamgr_broker_by_name(temp_db, "Dukascopy")
    assert by_name is not None
    assert by_name["id"] == bid

    assert get_datamgr_broker_by_name(temp_db, "nonexistent") is None

    assert (
        update_datamgr_broker(temp_db, bid, {"description": "Updated Broker"}) is True
    )
    assert delete_datamgr_broker(temp_db, bid) is True

    # Datasets
    ds_id = create_datamgr_dataset(
        temp_db,
        "ds-eurusd-m1",
        source="dukascopy",
        symbol="EURUSD",
        underlying="EURUSD",
        instrument="Forex",
        timeframe="M1",
        broker="Dukascopy",
        broker_name="Dukascopy Europe",
        timezone_name="UTC",
        category="Forex",
        date_from="2020-01-01",
        date_to="2025-01-01",
        created_at="2026-10-14T00:00:00Z",
        updated_at="2026-10-14T00:00:00Z",
        bars=100000,
    )
    assert ds_id == "ds-eurusd-m1"

    dataset = get_datamgr_dataset(temp_db, "ds-eurusd-m1")
    assert dataset is not None
    assert dataset["bars"] == 100000

    assert update_datamgr_dataset(temp_db, "ds-eurusd-m1", {"bars": 120000}) is True
    assert delete_datamgr_dataset(temp_db, "ds-eurusd-m1") is True


def test_crud_datamgr_instrument_and_session(
    temp_db: sqlite3.Connection,
) -> None:
    """Verify operations on datamgr_instruments and datamgr_sessions."""
    iid = create_datamgr_instrument(
        temp_db,
        "GBPUSD",
        created_at_utc="2026-10-14T00:00:00Z",
        updated_at_utc="2026-10-14T00:00:00Z",
        broker_id=1,
        point_value=100000.0,
    )
    assert iid > 0

    inst = get_datamgr_instrument(temp_db, "GBPUSD")
    assert inst is not None
    assert inst["symbol"] == "GBPUSD"
    assert inst["broker_id"] == 1

    instruments = list_datamgr_instruments(temp_db, broker_id=1)
    assert len(instruments) == 1

    assert (
        update_datamgr_instrument(temp_db, "GBPUSD", {"point_value": 10000.0}) is True
    )
    assert (
        update_datamgr_instrument(temp_db, "NONEXISTENT", {"point_value": 1.0}) is False
    )

    assert delete_datamgr_instrument(temp_db, "GBPUSD") is True
    assert delete_datamgr_instrument(temp_db, "NONEXISTENT") is False

    # Sessions
    sid = create_datamgr_session(
        temp_db,
        "Forex 24/5",
        timezone_name="UTC",
        is_default=1,
    )
    assert sid > 0
    session = get_datamgr_session(temp_db, sid)
    assert session is not None
    assert session["name"] == "Forex 24/5"

    # Lookup by name
    session_by_name = get_datamgr_session(temp_db, "Forex 24/5")
    assert session_by_name is not None
    assert session_by_name["id"] == sid

    # List sessions
    sessions_list = list_datamgr_sessions(temp_db)
    assert len(sessions_list) == 1
    assert sessions_list[0]["name"] == "Forex 24/5"

    assert (
        update_datamgr_session(temp_db, "Forex 24/5", {"description": "Standard Forex"})
        is True
    )
    assert (
        update_datamgr_session(temp_db, "NONEXISTENT", {"description": "None"}) is False
    )

    assert delete_datamgr_session(temp_db, "Forex 24/5") is True
    assert delete_datamgr_session(temp_db, "NONEXISTENT") is False


def test_crud_mt5_commands_and_events(temp_db: sqlite3.Connection) -> None:
    """Verify operations on mt5_commands and mt5_events."""
    cid = create_mt5_command(
        temp_db,
        "cmd-1",
        object_id="obj-1",
        class_name="Terminal",
        method_name="account_info",
        args_json="[]",
        requires_arm=0,
        created_at=1700000000.0,
        status="QUEUED",
    )
    assert cid == "cmd-1"

    cmd = get_mt5_command(temp_db, "cmd-1")
    assert cmd is not None
    assert cmd["method_name"] == "account_info"

    assert (
        update_mt5_command(
            temp_db,
            "cmd-1",
            "RESOLVED",
            resolved_at=1700000001.0,
            value_json='{"login": 12345}',
        )
        is True
    )

    eid = create_mt5_event(
        temp_db,
        event_type="connected",
        payload_json='{"server": "Demo"}',
        received_at=1700000000.0,
        command_id="cmd-1",
    )
    assert eid > 0

    assert delete_mt5_command(temp_db, "cmd-1") is True


def test_read_rows_filtering_and_pagination(
    temp_db: sqlite3.Connection,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify filtering, ordering, pagination bounds, and count_rows."""
    caplog.set_level(logging.DEBUG)
    for i in range(10):
        create_host_setting(temp_db, "test_scope", f"key_{i:02d}", f'{{"idx": {i}}}')

    # Test count_rows
    total = count_rows(temp_db, "host_settings", where={"scope": "test_scope"})
    assert total == 10

    # Test pagination
    page1 = read_rows(
        temp_db,
        "host_settings",
        where={"scope": "test_scope"},
        order_by="key ASC",
        limit=3,
        offset=0,
    )
    assert len(page1) == 3
    assert page1[0]["key"] == "key_00"

    page2 = read_rows(
        temp_db,
        "host_settings",
        where={"scope": "test_scope"},
        order_by="key DESC",
        limit=3,
        offset=3,
    )
    assert len(page2) == 3
    assert page2[0]["key"] == "key_06"

    # Test where with NULL
    insert_row(
        temp_db,
        "host_jobs",
        {
            "job_id": "j-null",
            "owner": "usr",
            "kind": "compute",
            "status": "pending",
            "started_at_utc": None,
        },
    )
    null_jobs = read_rows(temp_db, "host_jobs", where={"started_at_utc": None})
    assert any(j["job_id"] == "j-null" for j in null_jobs)

    assert any(getattr(r, "fr_id", None) == LIST_FR for r in caplog.records)
    assert any(getattr(r, "fr_id", None) == COUNT_FR for r in caplog.records)


def test_delete_rows_where(
    temp_db: sqlite3.Connection,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify conditional multi-row deletion."""
    caplog.set_level(logging.DEBUG)
    for i in range(5):
        create_host_setting(temp_db, "bulk_del", f"key_{i}", f'{{"i": {i}}}')

    deleted_count = delete_rows(temp_db, "host_settings", {"scope": "bulk_del"})
    assert deleted_count == 5
    assert count_rows(temp_db, "host_settings", where={"scope": "bulk_del"}) == 0
    assert any(getattr(r, "fr_id", None) == DELETE_WHERE_FR for r in caplog.records)


def test_validation_and_error_handling(temp_db: sqlite3.Connection) -> None:
    """Verify defensive checks for table allowlists, empty data, and PKs."""
    # 1. Unapproved table
    with pytest.raises(PersistenceError, match="not in approved table"):
        insert_row(temp_db, "malicious_table", {"a": 1})

    with pytest.raises(PersistenceError, match="not in approved table"):
        read_row_by_pk(temp_db, "malicious_table", {"id": 1})

    with pytest.raises(PersistenceError, match="not in approved table"):
        read_rows(temp_db, "malicious_table")

    with pytest.raises(PersistenceError, match="not in approved table"):
        count_rows(temp_db, "malicious_table")

    with pytest.raises(PersistenceError, match="not in approved table"):
        update_row_by_pk(temp_db, "malicious_table", {"id": 1}, {"a": 2})

    with pytest.raises(PersistenceError, match="not in approved table"):
        delete_row_by_pk(temp_db, "malicious_table", {"id": 1})

    with pytest.raises(PersistenceError, match="not in approved table"):
        delete_rows(temp_db, "malicious_table", {"id": 1})

    # 2. Empty data
    with pytest.raises(PersistenceError, match="cannot be empty"):
        insert_row(temp_db, "host_settings", {})

    with pytest.raises(PersistenceError, match="cannot be empty"):
        update_row_by_pk(temp_db, "host_settings", {"scope": "s", "key": "k"}, {})

    with pytest.raises(PersistenceError, match="non-empty where filter"):
        delete_rows(temp_db, "host_settings", {})

    # 3. Missing primary key columns
    with pytest.raises(PersistenceError, match="Missing primary key"):
        read_row_by_pk(temp_db, "host_settings", {"scope": "only_scope"})

    with pytest.raises(PersistenceError, match="Missing primary key"):
        update_row_by_pk(
            temp_db, "host_settings", {"scope": "only_scope"}, {"value_json": "{}"}
        )

    with pytest.raises(PersistenceError, match="Missing primary key"):
        delete_row_by_pk(temp_db, "host_settings", {"scope": "only_scope"})

    # 4. Invalid order by or limits
    with pytest.raises(PersistenceError, match="Invalid order_by clause"):
        read_rows(temp_db, "host_settings", order_by="key ASC; DROP TABLE")

    with pytest.raises(PersistenceError, match="Limit must be a non-negative"):
        read_rows(temp_db, "host_settings", limit=-1)

    with pytest.raises(PersistenceError, match="Offset must be a non-negative"):
        read_rows(temp_db, "host_settings", limit=5, offset=-1)

    # 5. Non-existent row update/delete
    assert (
        update_row_by_pk(
            temp_db, "host_settings", {"scope": "nx", "key": "nx"}, {"value_json": "{}"}
        )
        == 0
    )

    assert delete_row_by_pk(temp_db, "host_settings", {"scope": "nx", "key": "nx"}) == 0

    assert (
        read_row_by_pk(temp_db, "host_settings", {"scope": "nx", "key": "nx"}) is None
    )


def test_remaining_table_coverage(temp_db: sqlite3.Connection) -> None:
    """Verify insert and read for remaining operational tables."""
    # datamgr_commodities
    insert_row(
        temp_db,
        "datamgr_commodities",
        {"id": 1, "code": "CL", "name": "Crude Oil", "point_value": 1000.0},
    )
    row = read_row_by_pk(temp_db, "datamgr_commodities", {"id": 1})
    assert row is not None and row["code"] == "CL"

    # datamgr_crypto_catalog
    insert_row(
        temp_db,
        "datamgr_crypto_catalog",
        {
            "exchange": "BINANCE",
            "symbol": "BTCUSDT",
            "point_value": 1.0,
            "tick_size": 0.01,
            "tick_step": 0.01,
            "default_spread": 0.0,
            "default_slippage": 0.0,
            "price_precision": 2,
            "updated_at": "2026-10-14T00:00:00Z",
        },
    )
    crypto = read_row_by_pk(
        temp_db,
        "datamgr_crypto_catalog",
        {"exchange": "BINANCE", "symbol": "BTCUSDT"},
    )
    assert crypto is not None and crypto["symbol"] == "BTCUSDT"

    # datamgr_stock_group and datamgr_stock
    gid = insert_row(
        temp_db,
        "datamgr_stock_group",
        {"NAME": "SP500", "SYSTEM": 1, "DESC": "S&P 500"},
    )
    insert_row(
        temp_db,
        "datamgr_stock",
        {
            "TICKER": "AAPL",
            "BASKET_ID": gid,
            "DATE_FROM": 1500000000,
            "DATE_TO": None,
        },
    )
    stock = read_rows(temp_db, "datamgr_stock", where={"TICKER": "AAPL"})
    assert len(stock) == 1

    # datamgr_broker_stock
    bid = create_datamgr_broker(
        temp_db,
        "IBKR",
        created_at_utc="2026-10-14T00:00:00Z",
        updated_at_utc="2026-10-14T00:00:00Z",
    )
    insert_row(
        temp_db,
        "datamgr_broker_stock",
        {"TICKER": "AAPL", "BROKER_ID": bid},
    )
    bstock = read_rows(temp_db, "datamgr_broker_stock", where={"BROKER_ID": bid})
    assert len(bstock) == 1

    # datamgr_tickers
    insert_row(
        temp_db,
        "datamgr_tickers",
        {"ticker": "ES", "name": "E-mini S&P", "exchange": "CME"},
    )
    ticker = read_rows(temp_db, "datamgr_tickers", where={"ticker": "ES"})
    assert len(ticker) == 1

    # datamgr_logs and datamgr_operation_log
    insert_row(
        temp_db,
        "datamgr_logs",
        {
            "timestamp_utc": "2026-10-14T00:00:00Z",
            "action": "IMPORT",
            "message": "Imported bars",
        },
    )
    insert_row(
        temp_db,
        "datamgr_operation_log",
        {
            "timestamp_utc": "2026-10-14T00:00:00Z",
            "symbol": "EURUSD",
            "operation": "DOWNLOAD",
            "status": "SUCCESS",
            "message": "Complete",
        },
    )
    assert count_rows(temp_db, "datamgr_logs") == 1
    assert count_rows(temp_db, "datamgr_operation_log") == 1

    # datamgr_quality
    insert_row(
        temp_db,
        "datamgr_quality",
        {
            "report_id": "rep-1",
            "dataset_id": "ds-1",
            "quality_score": 0.99,
            "total_records": 1000,
            "anomalies_json": "[]",
            "anomaly_counts_json": "{}",
            "evaluated_at_utc": "2026-10-14T00:00:00Z",
        },
    )
    qrep = get_datamgr_quality_report(temp_db, "rep-1")
    assert qrep is not None and qrep["quality_score"] == 0.99

    # host_grid_leases
    node_id = insert_row(
        temp_db,
        "host_grid_nodes",
        {
            "node_id": "gn-1",
            "host": "localhost",
            "port": 8000,
            "cores": 4,
            "memory_mb": 8192,
            "state": "active",
            "last_heartbeat_utc": "2026-10-14T00:00:00Z",
        },
    )
    job_id = create_host_job(temp_db, "job-grid-1")
    insert_row(
        temp_db,
        "host_grid_leases",
        {
            "lease_id": "gl-1",
            "node_id": node_id,
            "job_id": job_id,
            "leased_at_utc": "2026-10-14T00:00:00Z",
            "expires_at_utc": "2026-10-14T01:00:00Z",
            "state": "active",
        },
    )
    gl = read_row_by_pk(temp_db, "host_grid_leases", {"lease_id": "gl-1"})
    assert gl is not None and gl["state"] == "active"

    # schema_migrations
    insert_row(
        temp_db,
        "schema_migrations",
        {
            "version": 1,
            "name": "initial_schema",
            "applied_at_utc": "2026-10-14T00:00:00Z",
            "checksum": "abc123sha",
        },
    )
    migs = get_schema_migrations(temp_db)
    assert len(migs) == 1 and migs[0]["version"] == 1


def test_canonical_crud_operations(
    temp_db: sqlite3.Connection,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify canonical CRUD operations across tables with validations and FK guards."""
    caplog.set_level(logging.DEBUG)

    # 1. Canonical create_record
    pk = create_record(
        temp_db,
        "host_settings",
        {
            "scope": "canon",
            "key": "k1",
            "value_json": '{"v": 1}',
            "updated_at_utc": "2026-10-19T00:00:00Z",
        },
    )
    assert pk == ("canon", "k1")

    # 2. Canonical read_records
    records = read_records(temp_db, "host_settings", where={"scope": "canon"})
    assert len(records) == 1
    assert records[0]["key"] == "k1"

    # read_records pagination
    create_record(
        temp_db,
        "host_settings",
        {
            "scope": "canon",
            "key": "k2",
            "value_json": '{"v": 2}',
            "updated_at_utc": "2026-10-19T00:01:00Z",
        },
    )
    paged = read_records(
        temp_db,
        "host_settings",
        where={"scope": "canon"},
        order_by="key ASC",
        limit=1,
        offset=0,
    )
    assert len(paged) == 1 and paged[0]["key"] == "k1"

    cursor_paged = read_records(
        temp_db,
        "host_settings",
        where={"scope": "canon"},
        order_by="key ASC",
        cursor_col="key",
        after_cursor="k1",
    )
    assert len(cursor_paged) == 1 and cursor_paged[0]["key"] == "k2"

    # 3. Canonical read_record (alias to read_row_by_pk)
    rec = read_record(temp_db, "host_settings", {"scope": "canon", "key": "k1"})
    assert rec is not None and rec["key"] == "k1"

    # 4. Canonical update_record
    aff = update_record(
        temp_db,
        "host_settings",
        {"scope": "canon", "key": "k1"},
        {"value_json": '{"v": 100}'},
    )
    assert aff == 1
    updated_rec = read_record(temp_db, "host_settings", {"scope": "canon", "key": "k1"})
    assert updated_rec is not None and updated_rec["value_json"] == '{"v": 100}'

    # 5. Canonical delete_record
    del_count = delete_record(temp_db, "host_settings", {"scope": "canon", "key": "k1"})
    assert del_count == 1
    assert (
        read_record(temp_db, "host_settings", {"scope": "canon", "key": "k1"}) is None
    )

    # 6. Validations and errors for canonical operations
    with pytest.raises(PersistenceError, match="not in approved table"):
        create_record(temp_db, "forbidden_tbl", {"id": 1})

    with pytest.raises(PersistenceError, match="Missing required primary key"):
        create_record(temp_db, "host_settings", {"scope": "only_scope"})

    with pytest.raises(PersistenceError, match="Failed to create record"):
        create_record(
            temp_db,
            "host_settings",
            {
                "scope": "canon",
                "key": "k2",
                "value_json": '{"v": 2}',
                "updated_at_utc": "2026-10-19T00:01:00Z",
            },
        )

    with pytest.raises(PersistenceError, match="not in approved table"):
        read_records(temp_db, "forbidden_tbl")

    with pytest.raises(PersistenceError, match="Invalid cursor column"):
        read_records(
            temp_db, "host_settings", cursor_col="invalid_col", after_cursor="x"
        )

    with pytest.raises(PersistenceError, match="not in approved table"):
        update_record(temp_db, "forbidden_tbl", {"id": 1}, {"a": 2})

    with pytest.raises(PersistenceError, match="requires non-empty pk_values"):
        update_record(temp_db, "host_settings", {}, {"value_json": "{}"})

    with pytest.raises(PersistenceError, match="requires non-empty update_values"):
        update_record(temp_db, "host_settings", {"scope": "s", "key": "k"}, {})

    with pytest.raises(PersistenceError, match="not in approved table"):
        delete_record(temp_db, "forbidden_tbl", {"id": 1})

    with pytest.raises(PersistenceError, match="requires non-empty pk_values"):
        delete_record(temp_db, "host_settings", {})

    with pytest.raises(
        PersistenceError, match="is not an approved operational persistence table"
    ):
        ensure_table_schema(temp_db, "forbidden_tbl")

    batch_save_host_settings({"guard_scope": {"k_test": "v_test"}}, conn=temp_db)
    assert any(
        BATCH_SETTINGS_REVISION_FR in record.message for record in caplog.records
    )

    # 7. Foreign key reference guard checks
    bid = create_datamgr_broker(
        temp_db,
        "IBKR_GUARD",
        created_at_utc="2026-10-19T00:00:00Z",
        updated_at_utc="2026-10-19T00:00:00Z",
    )
    bs_id = create_datamgr_broker_stock(temp_db, "NVDA", bid)
    with pytest.raises(PersistenceError, match="Deletion blocked for 'datamgr_broker'"):
        delete_record(temp_db, "datamgr_broker", {"id": bid})

    with pytest.raises(PersistenceError, match="Deletion blocked for 'datamgr_broker'"):
        delete_row_by_pk(temp_db, "datamgr_broker", {"id": bid})

    delete_datamgr_broker_stock(temp_db, bs_id)
    assert delete_record(temp_db, "datamgr_broker", {"id": bid}) == 1

    # Guard check for datamgr_stock_group -> datamgr_stock
    gid = create_datamgr_stock_group(temp_db, "GUARD_GROUP", desc="Guard test")
    stk_id = create_datamgr_stock(temp_db, "NVDA", gid, 1500000000)
    with pytest.raises(
        PersistenceError, match="Deletion blocked for 'datamgr_stock_group'"
    ):
        delete_record(temp_db, "datamgr_stock_group", {"ID": gid})
    delete_datamgr_stock(temp_db, stk_id)
    assert delete_record(temp_db, "datamgr_stock_group", {"ID": gid}) == 1

    # Guard check for host_jobs -> host_job_attempts
    jid = create_host_job(temp_db, "job-guard-1")
    create_host_job_attempt(temp_db, "att-guard-1", jid, "worker-1", 1, state="running")
    with pytest.raises(PersistenceError, match="Deletion blocked for 'host_jobs'"):
        delete_record(temp_db, "host_jobs", {"job_id": jid})
    delete_host_job_attempt(temp_db, "att-guard-1")

    # Guard check for host_grid_nodes -> host_grid_leases
    gn_id = create_host_grid_node(
        temp_db,
        "gn-guard-1",
        "localhost",
        9000,
        cores=2,
        memory_mb=4096,
        state="active",
        last_heartbeat_utc="2026-10-19T00:00:00Z",
    )
    create_host_grid_lease(
        temp_db,
        "gl-guard-1",
        gn_id,
        jid,
        leased_at_utc="2026-10-19T00:00:00Z",
        expires_at_utc="2026-10-19T01:00:00Z",
    )
    with pytest.raises(PersistenceError, match="Deletion blocked for 'host_jobs'"):
        delete_record(temp_db, "host_jobs", {"job_id": jid})
    with pytest.raises(
        PersistenceError, match="Deletion blocked for 'host_grid_nodes'"
    ):
        delete_record(temp_db, "host_grid_nodes", {"node_id": gn_id})

    delete_host_grid_lease(temp_db, "gl-guard-1")
    assert delete_record(temp_db, "host_jobs", {"job_id": jid}) == 1
    assert delete_record(temp_db, "host_grid_nodes", {"node_id": gn_id}) == 1


def test_entity_lifecycle_and_optimistic_cas(temp_db: sqlite3.Connection) -> None:
    """Verify entity CRUD operations and compare-and-set revision concurrency."""
    ent_id = create_entity(
        temp_db,
        "ent-plan-1",
        "strategy_spec",
        "user_space",
        '{"symbol": "EURUSD", "timeframe": "M15"}',
    )
    assert ent_id == ("ent-plan-1", "strategy_spec")

    raw_ent_id = create_host_entity(
        temp_db,
        "ent-host-raw",
        "system_service",
        "system",
        '{"status": "ok"}',
    )
    assert raw_ent_id == ("ent-host-raw", "system_service")

    read_ent = read_entity(temp_db, "ent-plan-1", "strategy_spec")
    assert read_ent is not None
    assert read_ent["scope"] == "user_space"
    assert read_ent["revision"] == 1

    ents = list_host_entities(temp_db, entity_type="strategy_spec", scope="user_space")
    assert len(ents) == 1

    # Update with matching expected_revision -> revision increments to 2
    aff = update_entity(
        temp_db,
        "ent-plan-1",
        "strategy_spec",
        '{"symbol": "GBPUSD", "timeframe": "H1"}',
        expected_revision=1,
    )
    assert aff == 1
    read_ent_v2 = read_entity(temp_db, "ent-plan-1", "strategy_spec")
    assert read_ent_v2 is not None and read_ent_v2["revision"] == 2

    # Update with mismatched expected_revision raises RevisionConflictError
    with pytest.raises(RevisionConflictError) as exc_info:
        update_entity(
            temp_db,
            "ent-plan-1",
            "strategy_spec",
            '{"symbol": "USDJPY"}',
            expected_revision=1,
        )
    assert exc_info.value.expected == 1
    assert exc_info.value.current == 2

    # Update without expected_revision automatically increments revision
    update_entity(temp_db, "ent-plan-1", "strategy_spec", '{"symbol": "USDJPY"}')
    read_ent_v3 = read_entity(temp_db, "ent-plan-1", "strategy_spec")
    assert read_ent_v3 is not None and read_ent_v3["revision"] == 3

    # update_record on table without revision column raises error when expected_revision passed
    with pytest.raises(PersistenceError, match="does not contain revision column"):
        update_record(
            temp_db,
            "host_settings",
            {"scope": "s", "key": "k"},
            {"value_json": "{}"},
            expected_revision=1,
            revision_col="nonexistent_rev",
        )

    # Delete entity
    del_aff = delete_entity(temp_db, "ent-plan-1", "strategy_spec")
    assert del_aff == 1
    assert read_entity(temp_db, "ent-plan-1", "strategy_spec") is None
    assert read_entity(temp_db, "nonexistent", "strategy_spec") is None


def test_typed_crud_all_operational_tables(temp_db: sqlite3.Connection) -> None:
    """Verify all 25 tables have complete, functioning typed CRUD helper functions."""
    # 1. datamgr_broker
    bid = create_datamgr_broker(
        temp_db,
        "ALPACA",
        created_at_utc="2026-10-19T00:00:00Z",
        updated_at_utc="2026-10-19T00:00:00Z",
    )
    assert get_datamgr_broker(temp_db, bid) is not None
    assert get_datamgr_broker_by_name(temp_db, "ALPACA") is not None
    assert len(list_datamgr_brokers(temp_db)) >= 1
    update_datamgr_broker(temp_db, bid, {"name": "ALPACA_SEC"})
    assert get_datamgr_broker(temp_db, bid)["name"] == "ALPACA_SEC"  # type: ignore[index]

    # 2. datamgr_broker_stock
    bs_id = create_datamgr_broker_stock(temp_db, "TSLA", bid)
    bs = get_datamgr_broker_stock(temp_db, bs_id)
    assert bs is not None and bs["TICKER"] == "TSLA"
    assert len(list_datamgr_broker_stocks(temp_db, broker_id=bid)) == 1
    update_datamgr_broker_stock(temp_db, bs_id, {"TICKER": "TSLA"})
    assert delete_datamgr_broker_stock(temp_db, bs_id) == 1
    assert get_datamgr_broker_stock(temp_db, bs_id) is None
    delete_datamgr_broker(temp_db, bid)

    # 3. datamgr_commodity
    cid = create_datamgr_commodity(temp_db, "GC", name="Gold", point_value=100.0)
    com = get_datamgr_commodity(temp_db, cid)
    assert com is not None and com["code"] == "GC"
    assert len(list_datamgr_commodities(temp_db)) >= 1
    update_datamgr_commodity(temp_db, cid, {"name": "Gold Futures"})
    assert get_datamgr_commodity(temp_db, cid)["name"] == "Gold Futures"  # type: ignore[index]
    assert delete_datamgr_commodity(temp_db, cid) == 1

    # 4. datamgr_crypto_catalog
    create_datamgr_crypto_catalog(
        temp_db,
        "BINANCE",
        "ETHUSDT",
        point_value=1.0,
        tick_size=0.01,
        tick_step=0.01,
        default_spread=0.0,
        default_slippage=0.0,
        price_precision=2,
        updated_at="2026-10-19T00:00:00Z",
    )
    cry = get_datamgr_crypto_catalog(temp_db, "BINANCE", "ETHUSDT")
    assert cry is not None and cry["symbol"] == "ETHUSDT"
    assert len(list_datamgr_crypto_catalogs(temp_db, exchange="BINANCE")) >= 1
    update_datamgr_crypto_catalog(temp_db, "BINANCE", "ETHUSDT", {"tick_size": 0.05})
    assert delete_datamgr_crypto_catalog(temp_db, "BINANCE", "ETHUSDT") == 1

    # 5. datamgr_dataset
    ds_id = create_datamgr_dataset(
        temp_db,
        "SPY_M1",
        source="CSV",
        symbol="SPY",
        underlying="SPY",
        instrument="SPY",
        timeframe="minute",
        broker="default",
        broker_name="Default",
        timezone_name="UTC",
        category="equity",
        date_from="2026-01-01",
        date_to="2026-10-19",
        created_at="2026-10-19T00:00:00Z",
        updated_at="2026-10-19T00:00:00Z",
    )
    assert get_datamgr_dataset(temp_db, ds_id) is not None
    assert len(list_datamgr_datasets(temp_db)) >= 1
    update_datamgr_dataset(temp_db, ds_id, {"timeframe": "hour"})
    delete_datamgr_dataset(temp_db, ds_id)

    # 6. datamgr_instrument
    inst_id = create_datamgr_instrument(
        temp_db,
        symbol="MSFT",
        created_at_utc="2026-10-19T00:00:00Z",
        updated_at_utc="2026-10-19T00:00:00Z",
    )
    assert inst_id > 0
    assert get_datamgr_instrument(temp_db, "MSFT") is not None
    assert len(list_datamgr_instruments(temp_db)) >= 1
    update_datamgr_instrument(temp_db, "MSFT", {"description": "Microsoft Corp"})
    delete_datamgr_instrument(temp_db, "MSFT")

    # 7. datamgr_log
    log_id = create_datamgr_log(temp_db, "2026-10-19T00:00:00Z", "SYNC", "Synced bars")
    log_row = get_datamgr_log(temp_db, log_id)
    assert log_row is not None and log_row["action"] == "SYNC"
    assert len(list_datamgr_logs(temp_db)) >= 1
    update_datamgr_log(temp_db, log_id, {"message": "Synced bars ok"})
    assert delete_datamgr_log(temp_db, log_id) == 1

    # 8. datamgr_operation_log
    op_id = create_datamgr_operation_log(
        temp_db,
        "2026-10-19T00:00:00Z",
        "BTCUSDT",
        "FETCH",
        status="DONE",
        message="Success",
    )
    op_row = get_datamgr_operation_log(temp_db, op_id)
    assert op_row is not None and op_row["symbol"] == "BTCUSDT"
    assert len(list_datamgr_operation_logs(temp_db, symbol="BTCUSDT")) >= 1
    update_datamgr_operation_log(temp_db, op_id, {"status": "ARCHIVED"})
    assert delete_datamgr_operation_log(temp_db, op_id) == 1

    # 9. datamgr_quality
    create_datamgr_quality_report(
        temp_db,
        "rep-typed-1",
        "ds-typed-1",
        0.95,
        500,
        anomalies_json="[]",
        anomaly_counts_json="{}",
        evaluated_at_utc="2026-10-19T00:00:00Z",
    )
    q_rep = get_datamgr_quality_report(temp_db, "rep-typed-1")
    assert q_rep is not None and q_rep["quality_score"] == 0.95
    assert len(list_datamgr_quality_reports(temp_db, dataset_id="ds-typed-1")) == 1
    update_datamgr_quality_report(temp_db, "rep-typed-1", {"quality_score": 0.98})
    assert delete_datamgr_quality_report(temp_db, "rep-typed-1") == 1

    # 10. datamgr_session
    sid = create_datamgr_session(
        temp_db,
        name="session-typed-1",
    )
    assert get_datamgr_session(temp_db, sid) is not None
    assert len(list_datamgr_sessions(temp_db)) >= 1
    update_datamgr_session(temp_db, sid, {"description": "stopped"})
    delete_datamgr_session(temp_db, sid)

    # 11. datamgr_stock_group and datamgr_stock
    grp_id = create_datamgr_stock_group(
        temp_db, "TECH_TITANS", system=False, desc="Tech stocks"
    )
    grp = get_datamgr_stock_group(temp_db, grp_id)
    assert grp is not None and grp["NAME"] == "TECH_TITANS"
    assert len(list_datamgr_stock_groups(temp_db)) >= 1
    update_datamgr_stock_group(temp_db, grp_id, {"DESC": "Updated tech"})

    stk_id = create_datamgr_stock(temp_db, "GOOGL", grp_id, 1600000000)
    stk = get_datamgr_stock(temp_db, stk_id)
    assert stk is not None and stk["TICKER"] == "GOOGL"
    assert len(list_datamgr_stocks(temp_db, basket_id=grp_id)) == 1
    update_datamgr_stock(temp_db, stk_id, {"DATE_TO": 1700000000})
    assert delete_datamgr_stock(temp_db, stk_id) == 1
    delete_datamgr_stock_group(temp_db, grp_id)

    # 12. datamgr_ticker
    tick_id = create_datamgr_ticker(temp_db, "NQ", name="E-mini Nasdaq", exchange="CME")
    tick = get_datamgr_ticker(temp_db, tick_id)
    assert tick is not None and tick["exchange"] == "CME"
    assert len(list_datamgr_tickers(temp_db, exchange="CME")) >= 1
    update_datamgr_ticker(temp_db, tick_id, {"name": "Nasdaq 100 Futures"})
    assert delete_datamgr_ticker(temp_db, tick_id) == 1

    # 13. host_grid_nodes and host_grid_leases
    gnode_id = create_host_grid_node(
        temp_db,
        "gn-typed-1",
        "127.0.0.1",
        7000,
        cores=8,
        memory_mb=16384,
        state="active",
        last_heartbeat_utc="2026-10-19T00:00:00Z",
    )
    gnode = get_host_grid_node(temp_db, gnode_id)
    assert gnode is not None and gnode["cores"] == 8
    assert len(list_host_grid_nodes(temp_db, state="active")) >= 1
    update_host_grid_node(temp_db, gnode_id, {"cores": 16})
    update_host_grid_node_heartbeat(temp_db, gnode_id, "active", "2026-10-19T00:05:00Z")

    job_id = create_host_job(temp_db, "job-typed-1")
    save_host_job("job-typed-1", status="running", conn=temp_db)
    create_host_grid_lease(
        temp_db,
        "glease-typed-1",
        gnode_id,
        job_id,
        leased_at_utc="2026-10-19T00:00:00Z",
        expires_at_utc="2026-10-19T02:00:00Z",
        state="active",
    )
    glease = get_host_grid_lease(temp_db, "glease-typed-1")
    assert glease is not None and glease["state"] == "active"
    assert len(list_host_grid_leases(temp_db, node_id=gnode_id, state="active")) == 1
    update_host_grid_lease(temp_db, "glease-typed-1", {"state": "released"})
    assert delete_host_grid_lease(temp_db, "glease-typed-1") == 1
    delete_host_grid_node(temp_db, gnode_id)

    # 14. host_job_attempts and host_job_events
    att_id = create_host_job_attempt(
        temp_db,
        "att-typed-1",
        job_id,
        "worker-1",
        1,
        state="pending",
        created_at_utc="2026-10-19T00:00:00Z",
    )
    att = get_host_job_attempt(temp_db, att_id)
    assert att is not None and att["state"] == "pending"
    assert len(get_host_job_attempts(temp_db, job_id)) == 1
    assert len(list_host_job_attempts(temp_db, job_id=job_id)) == 1
    update_host_job_attempt(temp_db, att_id, {"state": "success"})
    assert delete_host_job_attempt(temp_db, att_id) == 1

    ev_id = create_host_job_event(
        temp_db,
        "ev-typed-1",
        job_id,
        "STARTED",
        details_json='{"worker": "w1"}',
        created_at_utc="2026-10-19T00:00:00Z",
    )
    ev = get_host_job_event(temp_db, ev_id)
    assert ev is not None and ev["to_state"] == "STARTED"
    assert len(get_host_job_events(temp_db, job_id)) >= 1
    assert len(list_host_job_events(temp_db, job_id=job_id)) >= 1
    update_host_job_event(temp_db, ev_id, {"details_json": '{"worker": "w2"}'})
    record_host_job_event(
        "ev-typed-2",
        job_id,
        "PROGRESS",
        details_json='{"pct": 50}',
        created_at_utc="2026-10-19T00:01:00Z",
        conn=temp_db,
    )
    assert delete_host_job_event(temp_db, ev_id) == 1
    delete_host_job(temp_db, job_id)

    # 15. host_leases
    create_host_lease(
        temp_db,
        "lease-typed-1",
        "holder-1",
        "cluster",
        acquired_at_utc="2026-10-19T00:00:00Z",
        expires_at_utc="2026-10-19T01:00:00Z",
    )
    lease = get_host_lease(temp_db, "lease-typed-1")
    assert lease is not None and lease["holder_id"] == "holder-1"
    assert len(list_host_leases(temp_db, scope="cluster")) == 1
    update_host_lease(temp_db, "lease-typed-1", {"metadata": '{"state": "expired"}'})
    assert delete_host_lease(temp_db, "lease-typed-1") == 1

    # 16. host_sessions
    sess_id = create_host_session(
        temp_db,
        "sess-typed-1",
        "sha256tokenhash",
        "user-typed-1",
        "peer-1",
        created_at_utc="2026-10-19T00:00:00Z",
        expires_at_utc="2026-10-20T00:00:00Z",
        status="active",
    )
    assert get_host_session(temp_db, sess_id) is not None
    assert get_host_session_by_token_hash(temp_db, "sha256tokenhash") is not None
    assert len(list_host_sessions(temp_db)) >= 1
    update_host_session(temp_db, sess_id, "revoked")
    update_host_session_status(temp_db, sess_id, "revoked")
    save_host_session(
        "sess-typed-1",
        "sha256tokenhash2",
        "user-typed-2",
        "peer-2",
        "2026-10-19T00:00:00Z",
        expires_at_utc="2026-10-21T00:00:00Z",
        status="active",
        conn=temp_db,
    )
    delete_host_session(temp_db, sess_id)

    # 17. mt5_commands and mt5_events
    cmd_id = create_mt5_command(
        temp_db,
        "cmd-typed-1",
        object_id="obj-1",
        class_name="MT5Client",
        method_name="connect",
        args_json="{}",
        requires_arm=0,
        created_at=1700000000.0,
        status="QUEUED",
    )
    assert get_mt5_command(temp_db, cmd_id) is not None
    assert len(list_mt5_commands(temp_db)) >= 1
    update_mt5_command(temp_db, cmd_id, "SUCCESS")

    m_ev_id = create_mt5_event(
        temp_db,
        "CONNECTED",
        '{"ping": 10}',
        1700000001.0,
        command_id=cmd_id,
    )
    assert get_mt5_event(temp_db, m_ev_id) is not None
    assert len(list_mt5_events(temp_db, command_id=cmd_id)) == 1
    update_mt5_event(temp_db, m_ev_id, {"payload_json": '{"ping": 5}'})
    assert delete_mt5_event(temp_db, m_ev_id) == 1
    delete_mt5_command(temp_db, cmd_id)

    # 18. schema_migrations
    create_schema_migration(
        temp_db,
        2,
        "test_mig_2",
        applied_at_utc="2026-10-19T00:00:00Z",
        checksum="checksum2",
    )
    mig = get_schema_migration(temp_db, 2)
    assert mig is not None and mig["name"] == "test_mig_2"
    assert len(list_schema_migrations(temp_db)) >= 1
    update_schema_migration(temp_db, 2, {"checksum": "checksum2_rev"})
    assert delete_schema_migration(temp_db, 2) == 1


def test_batch_transactions_operations(
    temp_db: sqlite3.Connection,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify atomic multi-row batch execution (create, update, upsert, delete)."""
    caplog.set_level(logging.DEBUG)

    # 1. Empty batch
    empty_res = apply_batch(temp_db, [])
    assert empty_res.total_operations == 0
    assert empty_res.affected_rows == 0
    assert empty_res.to_dict()["total_operations"] == 0

    # 2. Multi-operation batch
    ops = [
        BatchOperation(
            op_type="create",
            table="host_settings",
            data={
                "scope": "tx_test",
                "key": "op_create",
                "value_json": '{"v": 1}',
                "updated_at_utc": "2026-10-19T00:00:00Z",
            },
        ),
        BatchOperation(
            op_type="upsert",
            table="host_settings",
            data={
                "scope": "tx_test",
                "key": "op_upsert_new",
                "value_json": '{"v": 2}',
                "updated_at_utc": "2026-10-19T00:00:00Z",
            },
        ),
        BatchOperation(
            op_type="update",
            table="host_settings",
            pk_values={"scope": "tx_test", "key": "op_create"},
            data={"value_json": '{"v": 100}'},
        ),
        BatchOperation(
            op_type="upsert",
            table="host_settings",
            pk_values={"scope": "tx_test", "key": "op_upsert_new"},
            data={
                "scope": "tx_test",
                "key": "op_upsert_new",
                "value_json": '{"v": 200}',
                "updated_at_utc": "2026-10-19T00:01:00Z",
            },
        ),
        BatchOperation(
            op_type="delete",
            table="host_settings",
            pk_values={"scope": "tx_test", "key": "op_create"},
        ),
    ]

    res = apply_batch(temp_db, ops)
    assert isinstance(res, BatchResult)
    assert res.total_operations == 5
    assert res.affected_rows >= 4
    assert len(res.details) == 5

    # Verify state after transaction commit
    assert (
        read_record(temp_db, "host_settings", {"scope": "tx_test", "key": "op_create"})
        is None
    )
    upserted = read_record(
        temp_db, "host_settings", {"scope": "tx_test", "key": "op_upsert_new"}
    )
    assert upserted is not None and upserted["value_json"] == '{"v": 200}'

    # Check CLI formatting
    output = TransactionsCLI.format_output(res.to_dict())
    assert "total_operations: 5" in output

    assert any(
        BATCH_TRANSACTIONS_FR in record.message
        and getattr(record, "fr_id", None) == BATCH_TRANSACTIONS_FR
        for record in caplog.records
    )


def test_batch_transactions_rollback(
    temp_db: sqlite3.Connection,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify all-or-nothing rollback on constraint error and revision conflict."""
    caplog.set_level(logging.DEBUG)

    # 1. Rollback on RevisionConflictError
    create_entity(
        temp_db,
        "ent-tx-1",
        "strategy",
        "user",
        '{"name": "Initial"}',
        revision=1,
    )

    conflict_ops = [
        BatchOperation(
            op_type="create",
            table="host_settings",
            data={
                "scope": "tx_fail",
                "key": "should_rollback",
                "value_json": "{}",
                "updated_at_utc": "2026-10-19T00:00:00Z",
            },
        ),
        BatchOperation(
            op_type="update",
            table="host_entities",
            pk_values={"entity_id": "ent-tx-1", "entity_type": "strategy"},
            data={"payload_json": '{"name": "Conflict"}'},
            expected_revision=999,  # actual is 1!
            revision_col="revision",
        ),
    ]

    with pytest.raises(RevisionConflictError):
        apply_batch(temp_db, conflict_ops)

    # Verify that operation 1 was rolled back!
    assert (
        read_record(
            temp_db, "host_settings", {"scope": "tx_fail", "key": "should_rollback"}
        )
        is None
    )

    # 2. Rollback on SQLite IntegrityError (duplicate PK)
    duplicate_ops = [
        BatchOperation(
            op_type="create",
            table="host_settings",
            data={
                "scope": "tx_dup",
                "key": "dup_key",
                "value_json": "{}",
                "updated_at_utc": "2026-10-19T00:00:00Z",
            },
        ),
        BatchOperation(
            op_type="create",
            table="host_settings",
            data={
                "scope": "tx_dup",
                "key": "dup_key",  # Duplicate primary key!
                "value_json": "{}",
                "updated_at_utc": "2026-10-19T00:00:00Z",
            },
        ),
    ]

    with pytest.raises(PersistenceError, match="Batch transaction failed"):
        apply_batch(temp_db, duplicate_ops)

    # Verify row was NOT inserted due to rollback
    assert (
        read_record(temp_db, "host_settings", {"scope": "tx_dup", "key": "dup_key"})
        is None
    )

    # 3. Invalid operation type
    invalid_op = [BatchOperation(op_type="drop_table", table="host_settings")]
    with pytest.raises(PersistenceError, match="Unsupported batch operation"):
        apply_batch(temp_db, invalid_op)

    # 4. Unknown table
    unknown_tbl_op = [
        BatchOperation(op_type="create", table="unknown_table", data={"a": 1})
    ]
    with pytest.raises(PersistenceError, match="not in approved table set"):
        apply_batch(temp_db, unknown_tbl_op)

    # 5. Upsert validations
    upsert_empty = [BatchOperation(op_type="upsert", table="host_settings", data={})]
    with pytest.raises(PersistenceError, match="requires non-empty data"):
        apply_batch(temp_db, upsert_empty)

    upsert_missing_pk = [
        BatchOperation(
            op_type="upsert",
            table="host_settings",
            data={"value_json": "{}"},  # Missing scope and key!
        )
    ]
    with pytest.raises(PersistenceError, match="complete primary key"):
        apply_batch(temp_db, upsert_missing_pk)


def test_ddl_and_facade_constants() -> None:
    """Verify DDL map, schemas, and foreign key guard integrity."""
    assert len(PERSISTENCE_TABLES) == 25
    assert len(SCHEMA_DDL) == 25
    assert len(TABLE_DDL_MAP) == 25
    assert set(TABLE_DDL_MAP.keys()) == set(PERSISTENCE_TABLES)
    assert set(TABLE_PRIMARY_KEYS.keys()) == set(PERSISTENCE_TABLES)
    assert len(TABLE_FOREIGN_KEY_GUARDS) == 4
    for parent_table, child_specs in TABLE_FOREIGN_KEY_GUARDS.items():
        assert parent_table in PERSISTENCE_TABLES
        for child_table, _, _ in child_specs:
            assert child_table in PERSISTENCE_TABLES
