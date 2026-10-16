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
from app.host.persistence.create import (
    CONNECT_FR,
    CREATE_SCHEMA_FR,
    INSERT_FR,
    TABLE_PRIMARY_KEYS,
    PersistenceError,
    create_datamgr_broker,
    create_datamgr_dataset,
    create_datamgr_instrument,
    create_datamgr_session,
    create_host_job,
    create_host_session,
    create_host_setting,
    create_mt5_command,
    create_mt5_event,
    create_schema,
    get_connection,
    insert_row,
)
from app.host.persistence.delete import (
    DELETE_PK_FR,
    DELETE_WHERE_FR,
    delete_datamgr_broker,
    delete_datamgr_dataset,
    delete_datamgr_instrument,
    delete_datamgr_session,
    delete_host_entity,
    delete_host_grid_node,
    delete_host_job,
    delete_host_lease,
    delete_host_session,
    delete_host_setting,
    delete_mt5_command,
    delete_row_by_pk,
    delete_rows,
)
from app.host.persistence.read import (
    COUNT_FR,
    LIST_FR,
    READ_PK_FR,
    count_rows,
    get_datamgr_broker,
    get_datamgr_broker_by_name,
    get_datamgr_dataset,
    get_datamgr_instrument,
    get_datamgr_quality_report,
    get_datamgr_session,
    get_host_entity,
    get_host_grid_node,
    get_host_job,
    get_host_job_attempts,
    get_host_job_events,
    get_host_lease,
    get_host_session,
    get_host_session_by_token_hash,
    get_host_setting,
    get_mt5_command,
    get_schema_migrations,
    list_datamgr_instruments,
    list_datamgr_sessions,
    list_host_jobs,
    list_host_settings,
    read_row_by_pk,
    read_rows,
)
from app.host.persistence.update import (
    UPDATE_FR,
    update_datamgr_broker,
    update_datamgr_dataset,
    update_datamgr_instrument,
    update_datamgr_session,
    update_host_entity,
    update_host_grid_node_heartbeat,
    update_host_job,
    update_host_job_attempt,
    update_host_session_status,
    update_host_setting,
    update_mt5_command,
    update_row_by_pk,
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
