"""Unit tests for app.host.persistence module.

Validates transactional SQLite database management, WAL journaling, connection pragmas,
schema migrations, narrow typed repositories, optimistic concurrency controls, cooperative
worker leases, startup recovery reconciliation, scoped persistence access facades,
FastAPI REST routes, and CLI diagnostics.
"""

from __future__ import annotations

import ast
import re
import sqlite3
import sys
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from app.host.bootstrap import HostRuntime, create_persistence_router
from app.host.bootstrap import main as bootstrap_main
from app.host.diagnostics import main
from app.host.jobs import LeaseManager
from app.host.persistence import (
    CorruptDataError,
    DatabaseManager,
    HostSessionStore,
    IncompatibleSchemaError,
    JobStore,
    LeaseExpiredError,
    PersistenceError,
    RevisionConflictError,
    SettingsStore,
    StorageBusyError,
    TypedRepository,
    ValidationError,
    canonical_json,
    validate_identifier,
    validate_json_depth,
)
from app.host.session import PersistenceAccess
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel


class SampleConfig(BaseModel):
    """Test entity model representing strategy configuration."""

    symbol: str
    timeframe: str
    allocation: float = 1.0


def _seed_obsolete_sessions(db: DatabaseManager) -> None:
    with db.transaction() as conn:
        conn.execute(
            "CREATE TABLE host_sessions (token_hash TEXT PRIMARY KEY, "
            "username TEXT NOT NULL, issued_at REAL NOT NULL, "
            "expires_at REAL NOT NULL, revoked INTEGER NOT NULL DEFAULT 0)"
        )
        conn.execute("INSERT INTO host_sessions VALUES ('synthetic', 'test', 1, 2, 0)")
        conn.execute("CREATE TABLE host_session (session_id TEXT PRIMARY KEY)")
        conn.execute("INSERT INTO host_session VALUES ('preserve')")


def test_obsolete_session_cleanup_preserves_singular_table(
    db_manager: DatabaseManager, caplog: pytest.LogCaptureFixture
) -> None:
    """Explicit guarded drop preserves singular records and is idempotent."""
    _seed_obsolete_sessions(db_manager)
    with caplog.at_level("INFO"):
        assert (
            db_manager.schema.drop_obsolete_sessions(expected_count=1, expires_before=3)
            == 1
        )
        assert (
            db_manager.schema.drop_obsolete_sessions(expected_count=1, expires_before=3)
            == 0
        )
    assert "Obsolete session table removed" in caplog.text
    assert "Obsolete session table already absent" in caplog.text
    with db_manager.connection(query_only=True) as conn:
        assert (
            conn.execute("SELECT session_id FROM host_session").fetchone()[0]
            == "preserve"
        )
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE name='host_sessions'"
            ).fetchone()[0]
            == 0
        )


@pytest.mark.parametrize("change", ["count", "expiry", "schema", "view", "foreign_key"])
def test_obsolete_session_cleanup_rejects_changed_targets(
    db_manager: DatabaseManager, change: str
) -> None:
    """Changed data, schema or dependencies abort without dropping records."""
    _seed_obsolete_sessions(db_manager)
    with db_manager.transaction() as conn:
        if change == "schema":
            conn.execute("ALTER TABLE host_sessions ADD COLUMN unexpected TEXT")
        elif change == "view":
            conn.execute("CREATE VIEW session_view AS SELECT * FROM host_sessions")
        elif change == "foreign_key":
            conn.execute(
                "CREATE TABLE dependent (token TEXT REFERENCES host_sessions(token_hash))"
            )
    with pytest.raises((RevisionConflictError, IncompatibleSchemaError)):
        db_manager.schema.drop_obsolete_sessions(
            expected_count=2 if change == "count" else 1,
            expires_before=1 if change == "expiry" else 3,
        )
    with db_manager.connection(query_only=True) as conn:
        assert conn.execute("SELECT COUNT(*) FROM host_sessions").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM host_session").fetchone()[0] == 1


@pytest.mark.parametrize("count,cutoff", [(-1, 3), (1, float("nan")), (1, 0)])
def test_obsolete_session_cleanup_rejects_invalid_predicates(
    db_manager: DatabaseManager, count: int, cutoff: float
) -> None:
    with pytest.raises(ValidationError):
        db_manager.schema.drop_obsolete_sessions(
            expected_count=count, expires_before=cutoff
        )


def test_legacy_host_jobs_table_migrates_cleanly(tmp_path: Path) -> None:
    """Verify that a legacy host_jobs table with obsolete group_id NOT NULL constraint
    fails closed with IncompatibleSchemaError, preserving data and schema intact."""
    db_file = tmp_path / "legacy_jobs.db"
    conn = sqlite3.connect(db_file)
    conn.execute(
        """
        CREATE TABLE host_jobs (
            job_id TEXT PRIMARY KEY,
            group_id TEXT NOT NULL,
            operation TEXT NOT NULL,
            state TEXT NOT NULL,
            resource_class TEXT NOT NULL,
            config_hash TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at_utc TEXT NOT NULL
        );
        """
    )
    conn.execute(
        """
        INSERT INTO host_jobs (
            job_id, group_id, operation, state, resource_class,
            config_hash, payload_json, created_at_utc
        ) VALUES (
            'legacy-job-1', 'grp1', 'op1', 'RUNNING', 'res1',
            'hash1', '{"key": "value"}', '2025-01-01T00:00:00Z'
        );
        """
    )
    conn.commit()
    conn.close()

    db = DatabaseManager(database_path=db_file)
    with pytest.raises(IncompatibleSchemaError):
        db.initialize()

    # Verify table schema has preserved group_id and data is intact without lossy changes
    check_conn = sqlite3.connect(db_file)
    try:
        cols = [
            r[1] for r in check_conn.execute("PRAGMA table_info(host_jobs)").fetchall()
        ]
        assert "group_id" in cols
        row = check_conn.execute(
            "SELECT state, payload_json FROM host_jobs WHERE job_id = 'legacy-job-1'"
        ).fetchone()
        assert row is not None
        assert row[0] == "RUNNING"
        assert row[1] == '{"key": "value"}'
    finally:
        check_conn.close()


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Fixture providing an isolated temporary database path."""
    return tmp_path / "test_haruquantai.db"


@pytest.fixture
def db_manager(temp_db_path: Path) -> DatabaseManager:
    """Fixture providing an initialized DatabaseManager with migrated schema."""
    mgr = DatabaseManager(temp_db_path)
    mgr.initialize()
    return mgr


@pytest.fixture
def sample_repo(db_manager: DatabaseManager) -> TypedRepository[SampleConfig]:
    """Fixture providing a typed repository for SampleConfig."""
    return TypedRepository(
        db=db_manager,
        entity_type="sample_config",
        model_cls=SampleConfig,
        scope="test-tenant",
    )


@pytest.fixture
def client(db_manager: DatabaseManager) -> Generator[TestClient]:
    """Fixture providing a FastAPI TestClient mounted with persistence router."""
    app = FastAPI()
    router = create_persistence_router(
        db_manager, reconcile=lambda: HostRuntime.reconcile_persistence(db_manager)
    )
    app.include_router(router, prefix="/api/v2")
    with TestClient(app) as test_client:
        yield test_client


# ============================================================================
# Validation Primitives Tests
# ============================================================================


def test_validate_identifier_valid() -> None:
    """Test valid entity and lease identifiers."""
    validate_identifier("strategy-123", "id")
    validate_identifier("tenant.core:alpha_v2", "id")
    validate_identifier("ABC_123.456:789-0", "id")


def test_validate_identifier_empty() -> None:
    """Test empty identifier rejection."""
    with pytest.raises(ValidationError, match="id must not be empty"):
        validate_identifier("", "id")


def test_validate_identifier_too_long() -> None:
    """Test identifier exceeding maximum length."""
    long_id = "a" * 129
    with pytest.raises(ValidationError, match="exceeds maximum"):
        validate_identifier(long_id, "id")


def test_validate_identifier_invalid_chars() -> None:
    """Test rejection of illegal characters in identifier."""
    with pytest.raises(ValidationError, match="invalid characters"):
        validate_identifier("bad id with spaces", "id")
    with pytest.raises(ValidationError, match="invalid characters"):
        validate_identifier("bad/slash", "id")
    with pytest.raises(ValidationError, match="invalid characters"):
        validate_identifier("drop table;", "id")


def test_validate_json_depth() -> None:
    """Test JSON nesting depth enforcement."""
    shallow = {"a": {"b": {"c": 1}}}
    validate_json_depth(shallow)

    deep: dict[str, object] = {"val": 1}
    for _ in range(20):
        deep = {"nested": deep}
    with pytest.raises(ValidationError, match="exceeds maximum nesting depth"):
        validate_json_depth(deep)


def test_canonical_json() -> None:
    """Test canonical deterministic JSON serialization."""
    obj = {"b": 2, "a": 1}
    result = canonical_json(obj)
    assert result == '{"a":1,"b":2}'

    # Disallow NaN / inf
    with pytest.raises(ValidationError, match="not serializable to strict JSON"):
        canonical_json({"val": float("nan")})


def test_canonical_json_size_exceeded() -> None:
    """Test canonical JSON size limit rejection."""
    huge_obj = {"data": "x" * (2 * 1024 * 1024 + 10)}
    with pytest.raises(ValidationError, match="exceeds maximum limit"):
        canonical_json(huge_obj)


# ============================================================================
# DatabaseManager & Connection Tests
# ============================================================================


def test_database_manager_connection_pragmas(db_manager: DatabaseManager) -> None:
    """Verify SQLite connection pragmas (WAL, synchronous, foreign keys, timeout)."""
    with db_manager.connection() as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode;")
        journal = cur.fetchone()[0]
        assert journal.lower() == "wal"

        cur.execute("PRAGMA synchronous;")
        sync = cur.fetchone()[0]
        # NORMAL is typically 1 in SQLite
        assert sync in (1, "NORMAL", "normal")

        cur.execute("PRAGMA foreign_keys;")
        fk = cur.fetchone()[0]
        assert fk in (1, "ON", "on")


def test_database_manager_transaction_commit(db_manager: DatabaseManager) -> None:
    """Verify transaction commit under normal execution."""
    with db_manager.transaction() as conn:
        conn.execute(
            """
            INSERT INTO host_entities (
                entity_id, entity_type, scope, payload, revision,
                created_at_utc, updated_at_utc
            ) VALUES ('test-1', 'type-a', 'scope-a', '{}', 1, '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z');
            """
        )

    # Verify persisted in separate connection
    with db_manager.connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM host_entities WHERE entity_id = 'test-1';")
        assert cur.fetchone()[0] == 1


def test_database_manager_transaction_rollback(db_manager: DatabaseManager) -> None:
    """Verify transaction rollback when an exception occurs."""
    with pytest.raises(RuntimeError, match="Simulated crash"):
        with db_manager.transaction() as conn:
            conn.execute(
                """
                INSERT INTO host_entities (
                    entity_id, entity_type, scope, payload, revision,
                    created_at_utc, updated_at_utc
                ) VALUES ('rollback-1', 'type-a', 'scope-a', '{}', 1, '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z');
                """
            )
            raise RuntimeError("Simulated crash")

    # Verify not persisted
    with db_manager.connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM host_entities WHERE entity_id = 'rollback-1';"
        )
        assert cur.fetchone()[0] == 0


def test_database_manager_busy_timeout_translation(temp_db_path: Path) -> None:
    """Verify operational lock/busy errors are translated to StorageBusyError."""
    mgr = DatabaseManager(temp_db_path)
    mock_conn = MagicMock()
    mock_conn.execute.side_effect = sqlite3.OperationalError("database is locked")
    with patch.object(mgr, "connect", return_value=mock_conn):
        with pytest.raises(StorageBusyError, match="Database contention timeout"):
            with mgr.transaction():
                pass


def test_database_manager_operational_error(temp_db_path: Path) -> None:
    """Verify general operational errors raise PersistenceError."""
    mgr = DatabaseManager(temp_db_path)
    mock_conn = MagicMock()
    mock_conn.execute.side_effect = sqlite3.OperationalError("disk I/O error")
    with patch.object(mgr, "connect", return_value=mock_conn):
        with pytest.raises(PersistenceError, match="Database operational error"):
            with mgr.transaction():
                pass


def test_database_manager_status(db_manager: DatabaseManager) -> None:
    """Verify get_status returns accurate metadata."""
    stat = db_manager.get_status()
    assert stat.is_connected is True
    assert stat.journal_mode.lower() == "wal"
    assert stat.schema_version >= 1
    assert stat.table_count >= 3
    assert stat.integrity_status.lower() == "ok"


def test_database_manager_status_disconnected(tmp_path: Path) -> None:
    """Verify get_status gracefully handles uninitialized/invalid path."""
    mgr = DatabaseManager(tmp_path / "test.db")
    with patch.object(
        mgr,
        "connect",
        side_effect=sqlite3.OperationalError("unable to open database file"),
    ):
        stat = mgr.get_status()
        assert stat.is_connected is False
        assert stat.integrity_status == "disconnected"


def test_database_manager_check_integrity(db_manager: DatabaseManager) -> None:
    """Verify check_integrity returns 'ok' on healthy database."""
    assert db_manager.check_integrity() == "ok"


# ============================================================================
# SchemaManager Tests
# ============================================================================


def test_schema_manager_initialize_idempotent(db_manager: DatabaseManager) -> None:
    """Verify initialize is idempotent and does not duplicate migrations."""
    db_manager.schema.initialize()
    db_manager.schema.initialize()

    migrations = db_manager.schema.list_migrations()
    assert len(migrations) == 1
    assert migrations[0].version == 1
    assert migrations[0].name == "initial_host_control_tables"


def test_schema_manager_verify_schema_success(db_manager: DatabaseManager) -> None:
    """Verify schema passes validation on normal database."""
    assert db_manager.schema.verify_schema() is True


def test_schema_manager_verify_schema_missing_table(
    db_manager: DatabaseManager,
) -> None:
    """Verify IncompatibleSchemaError raised when a required table is missing."""
    with db_manager.connection() as conn:
        conn.execute("DROP TABLE host_leases;")

    with pytest.raises(IncompatibleSchemaError, match="missing required tables"):
        db_manager.schema.verify_schema()


def test_schema_manager_verify_schema_outdated_version(
    db_manager: DatabaseManager,
) -> None:
    """Verify IncompatibleSchemaError raised when applied version is behind expected."""
    with db_manager.connection() as conn:
        conn.execute("UPDATE schema_migrations SET version = 0;")

    with pytest.raises(IncompatibleSchemaError, match="Outdated database schema"):
        db_manager.schema.verify_schema()


# ============================================================================
# TypedRepository Tests
# ============================================================================


def test_typed_repository_crud(
    sample_repo: TypedRepository[SampleConfig],
) -> None:
    """Verify typed entity CRUD operations with revision tracking."""
    # 1. Save new entity (revision 1)
    cfg = SampleConfig(symbol="BTC/USD", timeframe="1h", allocation=0.5)
    rec1 = sample_repo.save("btc_strat", cfg)
    assert rec1.entity_id == "btc_strat"
    assert rec1.revision == 1
    assert rec1.scope == "test-tenant"
    assert rec1.payload["symbol"] == "BTC/USD"

    # 2. Get entity
    retrieved = sample_repo.get("btc_strat")
    assert retrieved is not None
    assert retrieved.symbol == "BTC/USD"
    assert retrieved.allocation == 0.5

    # 3. Get record envelope
    rec_env = sample_repo.get_record("btc_strat")
    assert rec_env is not None
    assert rec_env.revision == 1

    # 4. Update entity (revision 2)
    cfg2 = SampleConfig(symbol="BTC/USD", timeframe="4h", allocation=0.75)
    rec2 = sample_repo.save("btc_strat", cfg2, expected_revision=1)
    assert rec2.revision == 2
    assert rec2.payload["timeframe"] == "4h"

    # 5. Delete entity with expected revision
    deleted = sample_repo.delete("btc_strat", expected_revision=2)
    assert deleted is True

    # 6. Verify absent after delete
    assert sample_repo.get("btc_strat") is None
    assert sample_repo.get_record("btc_strat") is None


def test_typed_repository_optimistic_conflict_on_save(
    sample_repo: TypedRepository[SampleConfig],
) -> None:
    """Verify RevisionConflictError on save when expected_revision diverges."""
    cfg = SampleConfig(symbol="ETH/USD", timeframe="15m")
    sample_repo.save("eth_strat", cfg)

    # Attempt save with wrong expected_revision
    cfg_updated = SampleConfig(symbol="ETH/USD", timeframe="30m")
    with pytest.raises(RevisionConflictError, match="expected 99, but current is 1"):
        sample_repo.save("eth_strat", cfg_updated, expected_revision=99)


def test_typed_repository_optimistic_conflict_on_delete(
    sample_repo: TypedRepository[SampleConfig],
) -> None:
    """Verify RevisionConflictError on delete when expected_revision diverges."""
    cfg = SampleConfig(symbol="SOL/USD", timeframe="5m")
    sample_repo.save("sol_strat", cfg)

    with pytest.raises(RevisionConflictError, match="expected 42, current is 1"):
        sample_repo.delete("sol_strat", expected_revision=42)

    # Verify not deleted
    assert sample_repo.get("sol_strat") is not None


def test_typed_repository_delete_nonexistent(
    sample_repo: TypedRepository[SampleConfig],
) -> None:
    """Verify delete returns False when entity does not exist."""
    assert sample_repo.delete("nonexistent_strat") is False
    assert sample_repo.delete("nonexistent_strat", expected_revision=1) is False


def test_typed_repository_list_and_pagination(
    sample_repo: TypedRepository[SampleConfig],
) -> None:
    """Verify list method keyset pagination and ordering."""
    for i in range(5):
        sample_repo.save(
            f"strat_{i:02d}",
            SampleConfig(symbol=f"SYM_{i}", timeframe="1d", allocation=float(i)),
        )

    # Page 1: limit 2
    page1 = sample_repo.list(limit=2)
    assert len(page1.items) == 2
    assert page1.items[0].symbol == "SYM_0"
    assert page1.items[1].symbol == "SYM_1"
    assert page1.next_cursor == "strat_01"
    assert page1.total_count == 5

    # Page 2: with cursor
    page2 = sample_repo.list(cursor=page1.next_cursor, limit=2)
    assert len(page2.items) == 2
    assert page2.items[0].symbol == "SYM_2"
    assert page2.items[1].symbol == "SYM_3"
    assert page2.next_cursor == "strat_03"

    # Page 3: final item
    page3 = sample_repo.list(cursor=page2.next_cursor, limit=2)
    assert len(page3.items) == 1
    assert page3.items[0].symbol == "SYM_4"
    assert page3.next_cursor is None


def test_typed_repository_corrupt_payload(
    sample_repo: TypedRepository[SampleConfig],
    db_manager: DatabaseManager,
) -> None:
    """Verify CorruptDataError raised when persisted payload is invalid JSON or schema mismatch."""
    with db_manager.connection() as conn:
        conn.execute(
            """
            INSERT INTO host_entities (
                entity_id, entity_type, scope, payload, revision,
                created_at_utc, updated_at_utc
            ) VALUES ('corrupt_1', 'sample_config', 'test-tenant', '{"invalid_field": 123}', 1, '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z');
            """
        )

    with pytest.raises(CorruptDataError, match="Corrupt data encountered"):
        sample_repo.get("corrupt_1")


def test_typed_repository_corrupt_envelope(
    sample_repo: TypedRepository[SampleConfig],
    db_manager: DatabaseManager,
) -> None:
    """Verify CorruptDataError raised when envelope metadata is corrupt."""
    with db_manager.connection() as conn:
        conn.execute(
            """
            INSERT INTO host_entities (
                entity_id, entity_type, scope, payload, revision,
                created_at_utc, updated_at_utc
            ) VALUES ('corrupt_env', 'sample_config', 'test-tenant', 'not-valid-json', 1, 'not-a-date', 'not-a-date');
            """
        )

    with pytest.raises(CorruptDataError, match="Corrupt envelope"):
        sample_repo.get_record("corrupt_env")


def test_typed_repository_owns_transaction(
    sample_repo: TypedRepository[SampleConfig],
    db_manager: DatabaseManager,
) -> None:
    """Entity operations own their transaction and do not accept external handles."""
    import inspect

    for method in (
        sample_repo.get,
        sample_repo.get_record,
        sample_repo.save,
        sample_repo.delete,
    ):
        assert "connection" not in inspect.signature(method).parameters
    sample_repo.save("avax_strat", SampleConfig(symbol="AVAX/USD", timeframe="1h"))
    assert sample_repo.get("avax_strat") is not None


# ============================================================================
# LeaseManager Tests
# ============================================================================


def test_lease_manager_acquire_and_release(db_manager: DatabaseManager) -> None:
    """Verify normal lease acquisition, list, and release."""
    leases = LeaseManager(db_manager)

    # Acquire
    rec = leases.acquire("worker_lock_1", "worker_node_a", ttl_seconds=30.0)
    assert rec.lease_key == "worker_lock_1"
    assert rec.holder_id == "worker_node_a"
    assert rec.is_expired is False

    # List active
    active = leases.list_active()
    assert len(active) == 1
    assert active[0].lease_key == "worker_lock_1"

    # Release
    released = leases.release("worker_lock_1", "worker_node_a")
    assert released is True

    # Active now empty
    assert len(leases.list_active()) == 0


def test_lease_manager_acquire_busy_conflict(db_manager: DatabaseManager) -> None:
    """Verify StorageBusyError raised when lease is held by another active worker."""
    leases = LeaseManager(db_manager)
    leases.acquire("exclusive_job", "worker_1", ttl_seconds=60.0)

    # Worker 2 attempts acquisition while active
    with pytest.raises(StorageBusyError, match="actively held by worker 'worker_1'"):
        leases.acquire("exclusive_job", "worker_2", ttl_seconds=60.0)


def test_lease_manager_acquire_overwrites_same_holder(
    db_manager: DatabaseManager,
) -> None:
    """Verify same worker can re-acquire an existing lease."""
    leases = LeaseManager(db_manager)
    rec1 = leases.acquire("re_acquire_job", "worker_1", ttl_seconds=10.0)
    rec2 = leases.acquire("re_acquire_job", "worker_1", ttl_seconds=60.0)
    assert rec2.expires_at_utc > rec1.expires_at_utc


def test_lease_manager_acquire_expired_lease_stealing(
    db_manager: DatabaseManager,
) -> None:
    """Verify worker can acquire a lease if previous holder's lease is expired."""
    leases = LeaseManager(db_manager)
    expired_time = (datetime.now(UTC) - timedelta(seconds=10)).isoformat()
    now_str = datetime.now(UTC).isoformat()

    with db_manager.transaction() as conn:
        conn.execute(
            """
            INSERT INTO host_leases (
                lease_key, holder_id, scope, acquired_at_utc,
                expires_at_utc, metadata
            ) VALUES ('expired_job', 'dead_worker', 'default', ?, ?, '{}');
            """,
            (now_str, expired_time),
        )

    # New worker acquires successfully
    rec = leases.acquire("expired_job", "live_worker", ttl_seconds=30.0)
    assert rec.holder_id == "live_worker"


def test_lease_manager_renew_success(db_manager: DatabaseManager) -> None:
    """Verify renewal extends expiration time."""
    leases = LeaseManager(db_manager)
    rec1 = leases.acquire("heartbeat_lease", "worker_alpha", ttl_seconds=10.0)

    rec2 = leases.renew("heartbeat_lease", "worker_alpha", ttl_seconds=60.0)
    assert rec2.expires_at_utc > rec1.expires_at_utc


def test_lease_manager_renew_errors(db_manager: DatabaseManager) -> None:
    """Verify renewal errors on nonexistent, stolen, or expired leases."""
    leases = LeaseManager(db_manager)

    # Nonexistent
    with pytest.raises(LeaseExpiredError, match="does not exist"):
        leases.renew("nonexistent_lease", "worker_1")

    # Stolen / different holder
    leases.acquire("shared_lease", "worker_1", ttl_seconds=60.0)
    with pytest.raises(LeaseExpiredError, match="held by 'worker_1', not 'worker_2'"):
        leases.renew("shared_lease", "worker_2")

    # Expired
    expired_time = (datetime.now(UTC) - timedelta(seconds=5)).isoformat()
    with db_manager.transaction() as conn:
        conn.execute(
            "UPDATE host_leases SET expires_at_utc = ? WHERE lease_key = 'shared_lease';",
            (expired_time,),
        )
    with pytest.raises(LeaseExpiredError, match="has already expired"):
        leases.renew("shared_lease", "worker_1")


def test_lease_manager_release_failures(db_manager: DatabaseManager) -> None:
    """Verify release returns False on nonexistent or mismatched holder."""
    leases = LeaseManager(db_manager)
    leases.acquire("lock_a", "worker_1", ttl_seconds=60.0)

    # Mismatched holder
    assert leases.release("lock_a", "worker_wrong") is False

    # Nonexistent
    assert leases.release("lock_nonexistent", "worker_1") is False


def test_lease_manager_prune_expired(db_manager: DatabaseManager) -> None:
    """Verify prune_expired removes expired leases and keeps active ones."""
    leases = LeaseManager(db_manager)
    # Active lease
    leases.acquire("active_lock", "live_node", ttl_seconds=60.0)

    # Two expired leases
    past_time = (datetime.now(UTC) - timedelta(seconds=20)).isoformat()
    with db_manager.transaction() as conn:
        conn.execute(
            """
            INSERT INTO host_leases (lease_key, holder_id, scope, acquired_at_utc, expires_at_utc, metadata)
            VALUES ('dead_1', 'dead_node', 'default', ?, ?, '{}'),
                   ('dead_2', 'dead_node', 'default', ?, ?, '{}');
            """,
            (past_time, past_time, past_time, past_time),
        )

    pruned = leases.prune_expired()
    assert pruned == 2

    active = leases.list_active()
    assert len(active) == 1
    assert active[0].lease_key == "active_lock"


# ============================================================================
# RecoveryManager & Scoped Facade Tests
# ============================================================================


def test_recovery_manager_reconcile_on_startup(db_manager: DatabaseManager) -> None:
    """Verify startup recovery reconciles leases, validates schema, and reports status."""
    # Seed an expired lease
    past_time = (datetime.now(UTC) - timedelta(seconds=10)).isoformat()
    with db_manager.transaction() as conn:
        conn.execute(
            """
            INSERT INTO host_leases (lease_key, holder_id, scope, acquired_at_utc, expires_at_utc, metadata)
            VALUES ('orphaned_lease', 'dead_pid', 'default', ?, ?, '{}');
            """,
            (past_time, past_time),
        )

    report = HostRuntime.reconcile_persistence(db_manager)
    assert report["status"] == "reconciled"
    assert report["integrity"].lower() == "ok"
    assert report["pruned_expired_leases"] >= 1


def test_recovery_manager_integrity_failure(temp_db_path: Path) -> None:
    """Verify IncompatibleSchemaError raised when database integrity check fails."""
    mgr = DatabaseManager(temp_db_path)
    mgr.initialize()

    with patch.object(mgr, "check_integrity", return_value="corruption detected"):
        with pytest.raises(
            IncompatibleSchemaError, match="Database integrity check failed"
        ):
            HostRuntime.reconcile_persistence(mgr)


def test_persistence_access_isolation(db_manager: DatabaseManager) -> None:
    """Verify tenant isolation through PersistenceAccess capability facade."""
    access_a = PersistenceAccess(db_manager, scope="tenant-a", owner_id="owner-a")
    access_b = PersistenceAccess(db_manager, scope="tenant-b", owner_id="owner-b")

    repo_a = access_a.get_repository("config", SampleConfig)
    repo_b = access_b.get_repository("config", SampleConfig)

    # Save under tenant A
    repo_a.save("cfg_1", SampleConfig(symbol="BTC", timeframe="1h"))

    # Tenant A sees it
    assert repo_a.get("cfg_1") is not None

    # Tenant B does not see it
    assert repo_b.get("cfg_1") is None
    assert len(repo_b.list().items) == 0


# ============================================================================
# FastAPI Persistence Router Tests
# ============================================================================


def test_rest_status_endpoint(client: TestClient) -> None:
    """Test GET /api/v2/persistence/status."""
    resp = client.get("/api/v2/persistence/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["data"]["is_connected"] is True
    assert data["data"]["journal_mode"].lower() == "wal"


def test_rest_migrations_endpoint(client: TestClient) -> None:
    """Test GET /api/v2/persistence/schema/migrations."""
    resp = client.get("/api/v2/persistence/schema/migrations")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert len(data["data"]) >= 1
    assert data["data"][0]["name"] == "initial_host_control_tables"


def test_rest_integrity_check_endpoint(client: TestClient) -> None:
    """Test POST /api/v2/persistence/integrity-check."""
    resp = client.post("/api/v2/persistence/integrity-check")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["data"]["integrity"] == "ok"


def test_rest_leases_lifecycle(client: TestClient) -> None:
    """Test REST API lease acquire, list, renew, and release endpoints."""
    # 1. Acquire lease
    acq_payload = {
        "lease_key": "api_lease_1",
        "holder_id": "api_worker_a",
        "scope": "default",
        "ttl_seconds": 30.0,
        "metadata": {"task": "backtest"},
    }
    resp1 = client.post("/api/v2/persistence/leases/acquire", json=acq_payload)
    assert resp1.status_code == 200
    assert resp1.json()["data"]["lease_key"] == "api_lease_1"

    # 2. Acquire conflict (busy)
    conflict_payload = {
        "lease_key": "api_lease_1",
        "holder_id": "api_worker_b",
        "scope": "default",
        "ttl_seconds": 30.0,
    }
    resp_conflict = client.post(
        "/api/v2/persistence/leases/acquire", json=conflict_payload
    )
    assert resp_conflict.status_code == 409

    # 3. List active leases
    resp_list = client.get("/api/v2/persistence/leases")
    assert resp_list.status_code == 200
    assert len(resp_list.json()["data"]) >= 1

    # 4. Renew lease
    renew_payload = {
        "lease_key": "api_lease_1",
        "holder_id": "api_worker_a",
        "ttl_seconds": 60.0,
    }
    resp_renew = client.post("/api/v2/persistence/leases/renew", json=renew_payload)
    assert resp_renew.status_code == 200

    # 5. Renew conflict / invalid holder
    bad_renew = {
        "lease_key": "api_lease_1",
        "holder_id": "api_worker_intruder",
        "ttl_seconds": 60.0,
    }
    resp_bad_renew = client.post("/api/v2/persistence/leases/renew", json=bad_renew)
    assert resp_bad_renew.status_code == 404

    # 6. Release lease
    release_payload = {
        "lease_key": "api_lease_1",
        "holder_id": "api_worker_a",
    }
    resp_release = client.post(
        "/api/v2/persistence/leases/release", json=release_payload
    )
    assert resp_release.status_code == 200
    assert resp_release.json()["data"]["released"] is True


def test_rest_recovery_reconcile_endpoint(client: TestClient) -> None:
    """Test POST /api/v2/persistence/recovery/reconcile."""
    resp = client.post("/api/v2/persistence/recovery/reconcile")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["data"]["status"] == "reconciled"


# ============================================================================
# CLI Diagnostics Tests
# ============================================================================


def test_cli_main_status(temp_db_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test CLI main() with --status flag."""
    mgr = DatabaseManager(temp_db_path)
    mgr.initialize()

    monkeypatch.setattr(
        sys,
        "argv",
        ["persistence.py", "--status", "--db", str(temp_db_path)],
    )
    code = main()
    assert code == 0


def test_cli_main_integrity_check(
    temp_db_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test CLI main() with --integrity-check flag."""
    mgr = DatabaseManager(temp_db_path)
    mgr.initialize()

    monkeypatch.setattr(
        sys,
        "argv",
        ["persistence.py", "--integrity-check", "--db", str(temp_db_path)],
    )
    code = main()
    assert code == 0


def test_cli_main_reconcile(
    temp_db_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test CLI main() with --reconcile flag."""
    mgr = DatabaseManager(temp_db_path)
    mgr.initialize()

    monkeypatch.setattr(
        sys,
        "argv",
        ["persistence.py", "--reconcile", "--db", str(temp_db_path)],
    )
    code = bootstrap_main()
    assert code == 0


def test_cli_main_help_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test CLI main() without action flags prints help and returns 0."""
    monkeypatch.setattr(sys, "argv", ["persistence.py"])
    code = main()
    assert code == 0


def test_cli_main_exception(
    temp_db_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test CLI main() returns 2 when an exception occurs."""
    monkeypatch.setattr(
        sys,
        "argv",
        ["persistence.py", "--status", "--db", str(temp_db_path)],
    )
    with patch.object(
        DatabaseManager, "get_status", side_effect=RuntimeError("disk err")
    ):
        code = main()
        assert code == 2


# ==============================================================================
# Architectural Isolation & Store Integration Tests
# ==============================================================================


def test_sqlite3_import_isolation() -> None:
    """Assert that sqlite3 is imported ONLY within app/host/persistence across app/."""
    app_root = Path(__file__).resolve().parents[4] / "app"
    assert app_root.is_dir(), f"Expected app directory at {app_root}"

    violating_imports: list[str] = []

    for py_file in app_root.rglob("*.py"):
        rel_path = py_file.relative_to(app_root.parent).as_posix()
        # app/host/persistence is the sole authorized SQLite package/module
        if rel_path == "app/host/persistence.py" or rel_path.startswith(
            "app/host/persistence/"
        ):
            continue

        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "sqlite3" or alias.name.startswith("sqlite3."):
                        violating_imports.append(
                            f"{rel_path}:{node.lineno} ('import {alias.name}')"
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module and (
                    node.module == "sqlite3" or node.module.startswith("sqlite3.")
                ):
                    violating_imports.append(
                        f"{rel_path}:{node.lineno} ('from {node.module} import ...')"
                    )

    assert not violating_imports, (
        "Architectural violation: sqlite3 must ONLY be imported within "
        "app/host/persistence. Found unauthorized imports in: "
        f"{violating_imports}"
    )


def test_persistence_settings_store_crud(temp_db_path: Path) -> None:
    """Settings storage returns records and revisions without host snapshots."""
    store = SettingsStore(db_path=temp_db_path)
    store.initialize()
    assert store.read_all() == (1, [])
    revision, rows = store.update_batch(
        {"workspace_paths": {"data_dir": "data"}}, expected_revision=1
    )
    assert revision == 2
    assert rows[0].value == "data"
    assert (
        store.read_settings("workspace_paths", key="data_dir").items[0].value == "data"
    )
    revision, rows = store.update_batch(
        {"workspace_paths": {"data_dir": "custom_data"}}, expected_revision=2
    )
    assert revision == 3
    assert rows[0].value == "custom_data"
    assert (
        store.update_batch(
            {"workspace_paths": {"data_dir": "custom_data"}}, expected_revision=3
        )[0]
        == 3
    )


def test_persistence_job_store_crud(temp_db_path: Path) -> None:
    """Job storage persists explicit fields without job lifecycle interpretation."""
    store = JobStore(db_path=temp_db_path)
    record = {
        "job_id": "job-test-001",
        "owner": "worker-1",
        "kind": "compute",
        "status": "running",
        "progress": 25.0,
        "accepted": 10,
        "rejected": 0,
        "message": "Processing batch 1",
        "attempt_id": 1,
        "max_retries": 3,
        "retry_count": 0,
        "dedup_key": "dedup-batch-1",
        "parent_job_id": None,
        "child_job_ids_json": "[]",
        "budget_json": "{}",
        "submitted_at_utc": "2026-10-07T12:00:00Z",
        "started_at_utc": None,
        "finished_at_utc": None,
        "error_message": None,
        "error_location": None,
    }
    store.upsert_job(record)
    assert store.get_job("job-test-001") == record
    assert store.list_jobs(owner="worker-1")[0]["status"] == "running"
    assert (
        store.update_statuses(
            ("running",),
            status="caller-selected-state",
            finished_at_utc="2026-10-08T12:00:00Z",
            error_message="caller-selected-message",
        )
        == 1
    )
    assert store.get_job("job-test-001")["status"] == "caller-selected-state"


def _database_boundary_violations(source: str) -> list[str]:  # noqa: C901 - bounded AST cases
    """Detect application database imports, SQL and handle access without execution."""
    violations = []
    drivers = {"sqlite3", "aiosqlite", "duckdb", "sqlalchemy", "psycopg", "pymysql"}
    sql = re.compile(
        r"^\s*(?:SELECT\b[\s\S]*\bFROM\b|INSERT\s+(?:OR\s+\w+\s+)?INTO\b|"
        r"UPDATE\s+\w+\s+SET\b|DELETE\s+FROM\b|CREATE\s+(?:TABLE|INDEX)\b|PRAGMA\b)",
        re.IGNORECASE,
    )
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] in drivers for alias in node.names):
                violations.append("database driver import")
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in drivers:
                violations.append("database driver import")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if sql.search(node.value):
                violations.append("SQL statement")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr in {
                "connection",
                "transaction",
                "cursor",
                "executescript",
                "executemany",
            }:
                violations.append("database handle operation")
            if isinstance(node.func, ast.Attribute) and node.func.attr in {
                "connect",
                "execute",
                "fetchone",
                "fetchall",
            }:
                receiver = node.func.value
                receiver_names = {
                    child.id
                    for child in ast.walk(receiver)
                    if isinstance(child, ast.Name)
                } | {
                    child.attr
                    for child in ast.walk(receiver)
                    if isinstance(child, ast.Attribute)
                }
                if receiver_names & {"db", "_db", "db_manager", "conn", "cursor"}:
                    violations.append("database handle operation")
            if node.args and isinstance(node.args[0], ast.Constant):
                value = node.args[0].value
                if isinstance(value, str) and value.split(".")[0] in drivers:
                    if (
                        isinstance(node.func, ast.Name) and node.func.id == "__import__"
                    ) or (
                        isinstance(node.func, ast.Attribute)
                        and node.func.attr == "import_module"
                    ):
                        violations.append("dynamic database driver import")
    return violations


@pytest.mark.parametrize(
    "source",
    [
        "import sqlite3 as driver\ndriver.connect(':memory:')",
        "from sqlite3 import connect as open_db",
        "with manager.connection() as borrowed:\n    borrowed.execute(query)",
        "with manager.transaction() as borrowed:\n    pass",
        "cursor = borrowed.cursor()",
        "db.connect()",
        "conn.execute(query)",
        "query = 'SELECT name FROM records'\nrunner.execute(query)",
        "__import__('sqlite3')",
        "importlib.import_module('duckdb')",
    ],
)
def test_database_boundary_rejects_bypasses(source: str) -> None:
    """Guard catches imports, dynamic imports, borrowed handles and SQL constants."""
    assert _database_boundary_violations(source)


def test_database_boundary_allows_service_calls() -> None:
    """Unrelated execution methods and storage result APIs are permitted."""
    assert not _database_boundary_violations(
        "from app.host.persistence import DatabaseManager\n"
        "rows = db.datasets.list_datasets()\nresult = worker.execute(task)"
    )


def test_application_database_boundary() -> None:
    """Every application SQL/driver/handle operation belongs to persistence."""
    root = Path(__file__).resolve().parents[4]
    violations = {}
    for path in (root / "app").rglob("*.py"):
        if path == root / "app/host/persistence.py" or (
            path.is_relative_to(root / "app/host/persistence")
        ):
            continue
        found = _database_boundary_violations(path.read_text(encoding="utf-8"))
        if found:
            violations[str(path.relative_to(root))] = found
    assert not violations
    persistence_dir = root / "app/host/persistence"
    persistence_files = (
        list(persistence_dir.rglob("*.py"))
        if persistence_dir.is_dir()
        else [root / "app/host/persistence.py"]
    )
    forbidden = {
        "fastapi",
        "argparse",
        "app.host.jobs",
        "app.host.settings",
        "app.host.bootstrap",
        "app.host.session",
        "app.host.diagnostics",
    }
    for p_file in persistence_files:
        source = p_file.read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(source)):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            assert not any(
                module == prefix or module.startswith(prefix + ".")
                for module in modules
                for prefix in forbidden | {"app.workspace"}
            )


def test_storage_initialization_has_no_domain_seeds(
    db_manager: DatabaseManager,
) -> None:
    """Creating tables must never decide which instruments, sessions, baskets, or brokers exist."""
    assert db_manager.instruments.count() == 0
    assert db_manager.sessions.count() == 0
    assert db_manager.baskets.count() == 0
    assert db_manager.brokers.count() == 0


def test_basket_replacement_rolls_back(db_manager: DatabaseManager) -> None:
    """A membership write failure cannot destroy the previous group or members."""
    store = db_manager.baskets
    store.save(
        "group", "original", [{"ticker": "AAPL", "date_from": "1900-01-01"}], system=0
    )
    before = store.get("group")
    with pytest.raises(KeyError):
        store.save("group", "replacement", [{"ticker": "MSFT"}], system=0)
    assert store.get("group") == before


def test_lease_acquisition_is_atomic(temp_db_path: Path) -> None:
    """Independent managers racing for a lease produce exactly one winner."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    first = DatabaseManager(temp_db_path)
    first.initialize()
    second = DatabaseManager(temp_db_path)
    barrier = Barrier(2)

    def acquire(db: DatabaseManager, holder: str) -> bool:
        barrier.wait(timeout=5)
        try:
            LeaseManager(db).acquire("race", holder, ttl_seconds=60)
        except StorageBusyError:
            return False
        return True

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(acquire, first, "one"),
            pool.submit(acquire, second, "two"),
        ]
        assert sum(future.result(timeout=10) for future in futures) == 1


def test_session_upsert_reuses_id(db_manager: DatabaseManager) -> None:
    """Session upsert updates supplied fields while preserving its identity."""
    first = db_manager.sessions.upsert({"name": "session", "description": "first"})
    second = db_manager.sessions.upsert({"name": "session", "description": "second"})
    assert first == second
    assert db_manager.sessions.get_by_name("session")["description"] == "second"


def test_corrupt_lease_renewal_rolls_back(db_manager: DatabaseManager) -> None:
    """Corrupt metadata must abort the expiry update rather than commit it."""
    import json

    leases = LeaseManager(db_manager)
    before = leases.acquire("corrupt", "holder", ttl_seconds=60)
    with db_manager.transaction() as conn:
        conn.execute(
            "UPDATE host_leases SET metadata = 'invalid-json' WHERE lease_key = 'corrupt'"
        )
    with pytest.raises(json.JSONDecodeError):
        leases.renew("corrupt", "holder", ttl_seconds=120)
    with db_manager.connection(query_only=True) as conn:
        row = conn.execute(
            "SELECT expires_at_utc FROM host_leases WHERE lease_key = 'corrupt'"
        ).fetchone()
    assert datetime.fromisoformat(row[0]) == before.expires_at_utc


def test_storage_column_allowlists(db_manager: DatabaseManager) -> None:
    """Unknown column expressions are rejected before SQL construction."""
    with pytest.raises(ValidationError):
        db_manager.sessions.upsert({"name": "session", "unknown": "value"})
    with pytest.raises(ValidationError):
        db_manager.instruments.update("symbol", {"unknown": "value"})


def test_storage_logs_do_not_include_setting_values(
    db_manager: DatabaseManager,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Storage records its operations without logging arbitrary stored payloads."""
    import logging

    caplog.set_level(logging.DEBUG)
    store = SettingsStore(db=db_manager)
    store.initialize()
    store.update_batch({"scope": {"token": "sensitive-test-value"}})
    store.read_all()
    assert any(
        getattr(record, "fr_id", "") == "FR-HOST-PERSISTENCE-SETTINGS"
        for record in caplog.records
    )
    assert "sensitive-test-value" not in caplog.text


@pytest.fixture
def explicit_dataset_row() -> dict[str, object]:
    """A complete storage row with intentionally non-default metadata."""
    return {
        "id": "explicit-id",
        "source": "source",
        "symbol": "SYMBOL",
        "underlying": "",
        "instrument": "",
        "timeframe": "D1",
        "broker": "broker",
        "broker_name": "Broker",
        "timezone": "UTC",
        "category": "Custom",
        "date_from": "first",
        "date_to": "last",
        "bars": 7,
        "created_at": "caller-created",
        "updated_at": "caller-updated",
        "path": "path",
        "data_kind": "ticks",
        "quality_score": 0.25,
        "lineage_json": "{}",
        "schema_version": 9,
    }


def test_dataset_crud_uses_explicit_fields_and_update_selection(
    db_manager: DatabaseManager, explicit_dataset_row: dict[str, object]
) -> None:
    """CRUD preserves supplied metadata and only updates selected columns."""
    store = db_manager.datasets
    store.save(explicit_dataset_row, update_columns=("source",))
    assert store.get_by_id("explicit-id") == explicit_dataset_row
    revised = dict(explicit_dataset_row, source="changed", bars=99, updated_at="new")
    store.save(revised, update_columns=("source",))
    assert store.get_by_id("explicit-id") == dict(
        explicit_dataset_row, source="changed"
    )
    store.save(revised, update_columns=())
    assert store.get_by_id("explicit-id") == dict(
        explicit_dataset_row, source="changed"
    )
    with pytest.raises(ValidationError, match="Unsupported storage column"):
        store.save(revised, update_columns=("source = 'unsafe'",))
    assert store.get_by_id("explicit-id") == dict(
        explicit_dataset_row, source="changed"
    )


@pytest.mark.parametrize("store_name", ["instruments", "sessions", "datasets"])
def test_incomplete_creation_does_not_invent_domain_defaults(
    db_manager: DatabaseManager, store_name: str
) -> None:
    """Incomplete raw creation fails before writing any business rows."""
    with pytest.raises(ValidationError, match="Incomplete storage record"):
        if store_name == "instruments":
            db_manager.instruments.create({"symbol": "incomplete"})
        elif store_name == "sessions":
            db_manager.sessions.create({"name": "incomplete"})
        else:
            db_manager.datasets.save({"id": "incomplete"}, update_columns=())
    assert db_manager.instruments.count() == 0
    assert db_manager.sessions.count() == 0
    assert db_manager.datasets.count() == 0


def test_raw_session_create_preserves_supplied_fields(
    db_manager: DatabaseManager,
) -> None:
    """The store persists explicit session values without choosing defaults."""
    row = {
        "name": "explicit",
        "broker_id": 42,
        "description": "",
        "timezone": "caller-zone",
        "windows_json": "caller-windows",
        "holidays_json": "caller-holidays",
        "is_default": 1,
    }
    session_id = db_manager.sessions.create(row)
    assert db_manager.sessions.get_by_name("explicit") == dict(row, id=session_id)


def test_settings_access_and_update_boundary() -> None:
    """Settings composes storage directly and excludes filesystem diagnostics."""
    root = Path(__file__).resolve().parents[4]
    tree = ast.parse((root / "app/host/settings.py").read_text(encoding="utf-8"))
    assert not any(
        isinstance(node, ast.ClassDef) and node.name == "SettingsStore"
        for node in ast.walk(tree)
    )
    imported_stores = {
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == "app.host.persistence"
        for alias in node.names
        if alias.name == "SettingsStore"
    }
    assert imported_stores
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in imported_stores
        for node in ast.walk(tree)
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"exists", "is_dir", "is_file", "stat"}
    singleton = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "settings"
            for target in node.targets
        )
    )
    assert isinstance(singleton.value, ast.Call)
    assert isinstance(singleton.value.func, ast.Name)
    assert singleton.value.func.id == "HostSettings"
    assert not singleton.value.args and not singleton.value.keywords


def test_capability_adapter_ownership() -> None:
    """HTTP access stays with its business owner; diagnostics only observes."""
    from app.host import bootstrap, diagnostics, jobs
    from app.host import settings as settings_module

    assert settings_module.create_settings_router.__module__ == "app.host.settings"
    assert jobs.create_leases_router.__module__ == "app.host.jobs"
    assert bootstrap.create_recovery_router.__module__ == "app.host.bootstrap"
    assert bootstrap.create_persistence_router.__module__ == "app.host.bootstrap"
    assert not hasattr(diagnostics, "create_settings_router")
    assert not hasattr(diagnostics, "AcquireLeaseRequest")
    assert not hasattr(diagnostics, "create_persistence_router")


def test_settings_atomic_delete_conflict_and_backup(tmp_path: Path) -> None:
    """Update/delete share one revision; backup preserves data without overwrite."""
    store = SettingsStore(tmp_path / "source.db")
    store.initialize()
    revision, _ = store.update_batch(
        {
            "application": {"config_global": {"unknown": "keep"}},
            "config.global": {"sounds_off": True},
        }
    )
    before = store.read_all()
    with pytest.raises(RevisionConflictError):
        store.update_batch(
            {"application": {"config_global": {"sounds_off": True}}},
            deletions=(("config.global", "sounds_off"),),
            expected_revision=revision - 1,
        )
    assert store.read_all() == before
    backup = tmp_path / "backups" / "backup.db"
    store.backup_to(backup)
    assert SettingsStore(backup).read_all() == before
    with pytest.raises(ValidationError):
        store.backup_to(backup)
    with pytest.raises(ValidationError):
        store.backup_to(store.db_path)
    for deletions in (
        (("_system", "revision"),),
        (("config.global", "sounds_off"), ("config.global", "sounds_off")),
    ):
        with pytest.raises(ValidationError):
            store.update_batch({}, deletions=deletions)
    final, rows = store.update_batch(
        {"application": {"config_global": {"sounds_off": True, "unknown": "keep"}}},
        deletions=(("config.global", "sounds_off"),),
        expected_revision=revision,
    )
    assert final == revision + 1
    assert [(r.scope, r.key) for r in rows] == [("application", "config_global")]
    assert SettingsStore(backup).read_all() == before


def test_host_session_crud_preserves_history_and_filters_issuer(
    db_manager: DatabaseManager, caplog: pytest.LogCaptureFixture
) -> None:
    from app.host.persistence import HostSessionRecord, HostSessionStore

    store = HostSessionStore(db_manager)

    def row(name: str, peer: str) -> HostSessionRecord:
        return HostSessionRecord(
            session_id=name,
            token_hash="hash-" + name,
            username="test",
            peer_id=peer,
            created_at_utc="2026-10-09T00:00:00+00:00",
            expires_at_utc="2026-10-10T00:00:00+00:00",
            status="ACTIVE",
        )

    with caplog.at_level("INFO"):
        store.create(row("one", "peer-one"))
        store.create(row("two", "peer-two"))
        assert (
            store.update_status(
                peer_id="peer-one",
                expected_status="ACTIVE",
                status="REVOKED",
                revoked_at_utc="2026-10-09T01:00:00+00:00",
                token_hash="hash-one",
                username="test",
            )
            == 1
        )
        assert (
            store.update_status(
                peer_id="peer-one",
                expected_status="ACTIVE",
                status="EXPIRED",
                revoked_at_utc=None,
            )
            == 0
        )
    assert "hash-one" not in caplog.text
    assert "Host session record inserted" in caplog.text
    assert "Host session records updated" in caplog.text
    assert store.list_records(peer_id="peer-one")[0].status == "REVOKED"
    assert store.list_records(peer_id="peer-two")[0].status == "ACTIVE"
    store.initialize()
    assert len(store.list_records(peer_id="peer-one")) == 1
    with pytest.raises(sqlite3.IntegrityError):
        store.create(row("one", "peer-one"))
    assert len(store.list_records(peer_id="peer-one")) == 1
    with db_manager.connection(query_only=True) as conn:
        assert (
            conn.execute(
                "SELECT name FROM sqlite_master WHERE name='host_sessions'"
            ).fetchone()
            is None
        )
    with pytest.raises(ValidationError):
        store.list_records(peer_id="peer-one", limit=0)


def test_host_session_store_rejects_incompatible_schema(
    db_manager: DatabaseManager,
) -> None:
    from app.host.persistence import HostSessionStore

    with db_manager.transaction() as conn:
        conn.execute("CREATE TABLE host_session (unexpected TEXT)")
    with pytest.raises(IncompatibleSchemaError):
        HostSessionStore(db_manager).initialize()
    with db_manager.connection(query_only=True) as conn:
        assert (
            conn.execute("PRAGMA table_info(host_session)").fetchone()["name"]
            == "unexpected"
        )


def test_dataset_delete_legacy_foreign_key_tolerance(
    db_manager: DatabaseManager,
) -> None:
    """Deleting a dataset cleans up legacy referencing tables without FK errors,
    and legacy tables remain preserved intact without automatic startup purge."""
    dataset_record = {
        "id": "ds_legacy_fk_test",
        "source": "MT5",
        "symbol": "NZDJPY_test",
        "underlying": "NZDJPY",
        "instrument": "NZDJPY",
        "timeframe": "M1",
        "broker": "6",
        "broker_name": "Pepperstone",
        "timezone": "UTC",
        "category": "Forex",
        "date_from": "2024-01-01",
        "date_to": "2024-01-02",
        "bars": 100,
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
        "path": "",
        "data_kind": "bars",
        "quality_score": 1.0,
        "lineage_json": "{}",
        "schema_version": 1,
    }
    db_manager.datasets.save(dataset_record, update_columns=())
    assert db_manager.datasets.get_by_id("ds_legacy_fk_test") is not None

    # Simulate legacy tables referencing datamgr_datasets
    with db_manager.transaction() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS source_datasets (
                id TEXT PRIMARY KEY REFERENCES datamgr_datasets(id),
                owner TEXT NOT NULL,
                identity_json TEXT NOT NULL,
                options_json TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS source_partitions (
                dataset_id TEXT NOT NULL REFERENCES source_datasets(id),
                period TEXT NOT NULL,
                revision INTEGER NOT NULL,
                relative_path TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                first_ms INTEGER NOT NULL,
                last_ms INTEGER NOT NULL,
                schema_json TEXT NOT NULL,
                committed_at TEXT NOT NULL,
                PRIMARY KEY (dataset_id, period, revision)
            );
            """
        )
        conn.execute(
            "INSERT INTO source_datasets VALUES (?, 'plugin.data_manager.meta_trader', '[]', '{}')",
            ("ds_legacy_fk_test",),
        )
        conn.execute(
            "INSERT INTO source_partitions VALUES (?, '2024', 1, 'rel.parquet', 'sha', 10, 0, 100, '{}', 'now')",
            ("ds_legacy_fk_test",),
        )

    # Deletion must succeed despite existing foreign key referencing rows
    assert db_manager.datasets.delete("ds_legacy_fk_test") is True
    assert db_manager.datasets.get_by_id("ds_legacy_fk_test") is None

    # Verify legacy tables are preserved intact without automatic deletion
    with db_manager.connection(query_only=True) as conn:
        remaining = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE name IN ('source_datasets', 'source_partitions')"
            ).fetchall()
        ]
        assert "source_datasets" in remaining
        assert "source_partitions" in remaining


def test_schema_verification_rejects_future_version(tmp_path: Path) -> None:
    """Verify that verify_schema() and initialize() reject version 999."""
    db_file = tmp_path / "future_ver.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()

    with db.transaction() as conn:
        conn.execute(
            "INSERT INTO schema_migrations (version, name, applied_at_utc, checksum) "
            "VALUES (999, 'future_migration', '2026-10-12T00:00:00Z', 'hash999');"
        )

    db2 = DatabaseManager(database_path=db_file)
    with pytest.raises(
        IncompatibleSchemaError,
        match="Unsupported future database schema version 999",
    ):
        db2.schema.verify_schema()

    with pytest.raises(
        IncompatibleSchemaError,
        match="Unsupported future database schema version 999",
    ):
        db2.initialize()


def test_schema_verification_rejects_missing_core_table(tmp_path: Path) -> None:
    """Verify that dropping a core table causes verify_schema() and initialize() to fail closed."""
    db_file = tmp_path / "missing_core.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()

    with db.transaction() as conn:
        conn.execute("DROP TABLE datamgr_datasets;")

    db2 = DatabaseManager(database_path=db_file)
    with pytest.raises(IncompatibleSchemaError, match="missing required tables"):
        db2.schema.verify_schema()

    with pytest.raises(IncompatibleSchemaError, match="missing required tables"):
        db2.initialize()


def test_schema_initialization_rejects_unversioned_core_tables(
    tmp_path: Path,
) -> None:
    """Verify that an unversioned database with core tables is rejected."""
    db_file = tmp_path / "unversioned.db"
    conn = sqlite3.connect(db_file)
    conn.execute(
        """
        CREATE TABLE host_entities (
            entity_id TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL,
            scope TEXT NOT NULL,
            payload TEXT NOT NULL,
            revision INTEGER NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()

    db = DatabaseManager(database_path=db_file)
    with pytest.raises(
        IncompatibleSchemaError, match="without schema_migrations ledger"
    ):
        db.initialize()


def test_settings_and_session_stores_initialize_in_isolation(
    tmp_path: Path,
) -> None:
    """Verify SettingsStore and HostSessionStore initialize standalone."""
    # SettingsStore in isolation
    s_db_file = tmp_path / "settings_only.db"
    s_store = SettingsStore(db_path=s_db_file)
    s_store.initialize()

    conn1 = sqlite3.connect(s_db_file)
    try:
        tables = {
            r[0]
            for r in conn1.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert tables == {"host_settings"}
        assert "schema_migrations" not in tables
        assert "host_jobs" not in tables
        assert "datamgr_datasets" not in tables
    finally:
        conn1.close()

    # HostSessionStore in isolation
    sess_db_file = tmp_path / "session_only.db"
    sess_db = DatabaseManager(database_path=sess_db_file)
    sess_store = HostSessionStore(sess_db)
    sess_store.initialize()

    conn2 = sqlite3.connect(sess_db_file)
    try:
        tables = {
            r[0]
            for r in conn2.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert tables == {"host_session"}
        assert "schema_migrations" not in tables
        assert "host_jobs" not in tables
    finally:
        conn2.close()

    # Now verify that SchemaManager can adopt these existing tables during full initialization
    full_db = DatabaseManager(database_path=s_db_file)
    full_db.initialize()
    conn3 = sqlite3.connect(s_db_file)
    try:
        tables = {
            r[0]
            for r in conn3.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert "schema_migrations" in tables
        assert "host_settings" in tables
        assert "host_jobs" in tables
    finally:
        conn3.close()


def test_schema_verification_rejects_missing_dataset_path_column(
    tmp_path: Path,
) -> None:
    """Verify that removing datamgr_datasets.path causes verify_schema() to fail closed."""
    db_file = tmp_path / "missing_dataset_path.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()

    with db.transaction() as conn:
        conn.execute("ALTER TABLE datamgr_datasets DROP COLUMN path;")

    db2 = DatabaseManager(database_path=db_file)
    with pytest.raises(
        IncompatibleSchemaError,
        match="Missing required column in datamgr_datasets: path",
    ):
        db2.schema.verify_schema()


def test_schema_verification_rejects_malformed_settings_constraints(
    tmp_path: Path,
) -> None:
    """Verify that host_settings with wrong column types or missing PK fails closed."""
    db_file = tmp_path / "malformed_settings.db"
    conn = sqlite3.connect(db_file)
    try:
        conn.execute(
            """
            CREATE TABLE host_settings (
                scope TEXT,
                key TEXT,
                value_json TEXT,
                schema_version TEXT,
                updated_at_utc TEXT
            );
            """
        )
        conn.commit()
    finally:
        conn.close()

    db = DatabaseManager(database_path=db_file)
    with pytest.raises(IncompatibleSchemaError):
        db.schema.verify_schema()

    s_store = SettingsStore(db_path=db_file)
    with pytest.raises(IncompatibleSchemaError):
        s_store.initialize()


def test_schema_verification_rejects_missing_job_or_entity_columns(
    tmp_path: Path,
) -> None:
    """Verify that host_jobs and host_entities missing operational columns fail closed."""
    db_file = tmp_path / "missing_job_col.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()

    with db.transaction() as conn:
        conn.execute("DROP INDEX IF EXISTS idx_host_jobs_status;")
        conn.execute("ALTER TABLE host_jobs DROP COLUMN status;")

    db2 = DatabaseManager(database_path=db_file)
    with pytest.raises(
        IncompatibleSchemaError,
        match="Missing required column in host_jobs: status",
    ):
        db2.schema.verify_schema()


def test_session_schema_rejects_partial_unique_index_and_preserves_data(
    tmp_path: Path,
) -> None:
    """Verify that a partial unique index on token_hash is rejected and preserves data."""
    db_file = tmp_path / "partial_session.db"
    conn = sqlite3.connect(db_file)
    try:
        conn.execute(
            """
            CREATE TABLE host_session (
                session_id TEXT PRIMARY KEY,
                token_hash TEXT NOT NULL,
                username TEXT NOT NULL,
                peer_id TEXT NOT NULL,
                created_at_utc TEXT NOT NULL,
                expires_at_utc TEXT NOT NULL,
                revoked_at_utc TEXT,
                status TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX idx_host_session_token_hash
            ON host_session(token_hash) WHERE status = 'ACTIVE';
            """
        )
        conn.execute(
            """
            INSERT INTO host_session VALUES
            ('s1', 'shared_hash', 'user1', 'peer1', '2026-01-01T00:00:00Z', '2026-01-02T00:00:00Z', '2026-01-01T12:00:00Z', 'REVOKED'),
            ('s2', 'shared_hash', 'user2', 'peer2', '2026-01-01T00:00:00Z', '2026-01-02T00:00:00Z', '2026-01-01T12:00:00Z', 'REVOKED');
            """
        )
        conn.commit()
    finally:
        conn.close()

    db = DatabaseManager(database_path=db_file)
    sess_store = HostSessionStore(db)

    with pytest.raises(
        IncompatibleSchemaError,
        match="partial unique index on token_hash is not permitted",
    ):
        sess_store.initialize()

    conn2 = sqlite3.connect(db_file)
    try:
        rows = conn2.execute(
            "SELECT session_id, token_hash, status FROM host_session ORDER BY session_id"
        ).fetchall()
        assert len(rows) == 2
        assert rows[0] == ("s1", "shared_hash", "REVOKED")
        assert rows[1] == ("s2", "shared_hash", "REVOKED")
    finally:
        conn2.close()


def test_schema_initialization_fault_injection_rolls_back_and_remains_retryable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that if core DDL is faulty, initialize() rolls back and does not cache success."""
    import app.host.persistence.schema as schema_mod

    db_file = tmp_path / "fault_injection.db"
    db = DatabaseManager(database_path=db_file)

    monkeypatch.setattr(
        schema_mod,
        "DATAMGR_DATASETS_DDL",
        "CREATE TABLE datamgr_datasets (id TEXT);",
    )

    with pytest.raises(IncompatibleSchemaError):
        db.initialize()

    assert db.schema._initialized is False

    conn = sqlite3.connect(db_file)
    try:
        tables = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert (
            "schema_migrations" not in tables
            or conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 0
        )
    finally:
        conn.close()

    monkeypatch.undo()
    db.initialize()
    assert db.schema._initialized is True
    assert db.schema.verify_schema() is True


@pytest.mark.parametrize(
    ("table_name", "col_to_drop"),
    [
        ("datamgr_sessions", "windows_json"),
        ("datamgr_sessions", "holidays_json"),
        ("datamgr_sessions", "is_default"),
        ("datamgr_instruments", "order_size_multiplier"),
        ("datamgr_instruments", "min_distance"),
        ("datamgr_instruments", "cot"),
        ("datamgr_broker", "stockpicker_use"),
        ("datamgr_broker", "mt_use"),
        ("datamgr_broker", "server_timezone"),
        ("datamgr_stock", "date_to"),
        ("datamgr_datasets", "path"),
        ("datamgr_datasets", "lineage_json"),
        ("host_jobs", "error_location"),
        ("host_jobs", "child_job_ids_json"),
        ("host_leases", "metadata"),
        ("host_entities", "payload"),
        ("datamgr_logs", "details"),
    ],
)
def test_schema_verify_rejects_missing_operational_columns(
    tmp_path: Path, table_name: str, col_to_drop: str
) -> None:
    """Verify that dropping any operational column fails verify_schema with IncompatibleSchemaError."""
    db_file = tmp_path / f"missing_col_{table_name}_{col_to_drop}.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()
    assert db.schema.verify_schema() is True

    with db.transaction() as conn:
        conn.execute(f"ALTER TABLE {table_name} DROP COLUMN {col_to_drop};")

    with pytest.raises(
        IncompatibleSchemaError,
        match=f"Missing required column in {table_name}: {col_to_drop}",
    ):
        db.schema.verify_schema()


@pytest.mark.parametrize(
    ("table_name", "ddl_recreate", "expected_err_match"),
    [
        (
            "datamgr_datasets",
            """
            CREATE TABLE datamgr_datasets (
                id TEXT,
                source TEXT NOT NULL,
                symbol TEXT NOT NULL,
                underlying TEXT NOT NULL,
                instrument TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                broker TEXT NOT NULL,
                broker_name TEXT NOT NULL,
                timezone TEXT NOT NULL,
                category TEXT NOT NULL,
                date_from TEXT NOT NULL,
                date_to TEXT NOT NULL,
                bars INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                path TEXT NOT NULL DEFAULT '',
                data_kind TEXT NOT NULL DEFAULT 'bars',
                quality_score REAL NOT NULL DEFAULT 1.0,
                lineage_json TEXT NOT NULL DEFAULT '{}',
                schema_version INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (id, source)
            );
            """,
            r"primary key mismatch: expected \('id',\), got \('id', 'source'\)",
        ),
        (
            "host_jobs",
            """
            CREATE TABLE host_jobs (
                job_id TEXT,
                owner TEXT NOT NULL,
                kind TEXT NOT NULL,
                status TEXT NOT NULL,
                progress REAL NOT NULL DEFAULT 0.0,
                accepted INTEGER NOT NULL DEFAULT 0,
                rejected INTEGER NOT NULL DEFAULT 0,
                message TEXT,
                attempt_id TEXT,
                max_retries INTEGER NOT NULL DEFAULT 0,
                retry_count INTEGER NOT NULL DEFAULT 0,
                dedup_key TEXT,
                parent_job_id TEXT,
                child_job_ids_json TEXT NOT NULL DEFAULT '[]',
                budget_json TEXT NOT NULL DEFAULT '{}',
                submitted_at_utc TEXT NOT NULL DEFAULT '',
                started_at_utc TEXT,
                finished_at_utc TEXT,
                error_message TEXT,
                error_location TEXT,
                PRIMARY KEY (job_id, owner)
            );
            """,
            r"primary key mismatch: expected \('job_id',\), got \('job_id', 'owner'\)",
        ),
        (
            "host_entities",
            """
            CREATE TABLE host_entities (
                entity_id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                scope TEXT NOT NULL,
                payload TEXT NOT NULL,
                revision INTEGER NOT NULL DEFAULT 1,
                created_at_utc TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL
            );
            """,
            r"primary key mismatch: expected \('entity_id', 'entity_type'\), got \('entity_id',\)",
        ),
        (
            "host_leases",
            """
            CREATE TABLE host_leases (
                lease_key TEXT,
                holder_id TEXT NOT NULL,
                scope TEXT NOT NULL,
                acquired_at_utc TEXT NOT NULL,
                expires_at_utc TEXT NOT NULL,
                metadata TEXT NOT NULL,
                PRIMARY KEY (lease_key, holder_id)
            );
            """,
            r"primary key mismatch: expected \('lease_key',\), got \('lease_key', 'holder_id'\)",
        ),
    ],
)
def test_schema_verify_rejects_primary_key_mismatches(
    tmp_path: Path, table_name: str, ddl_recreate: str, expected_err_match: str
) -> None:
    """Verify that non-matching composite or partial primary keys are rejected."""
    db_file = tmp_path / f"pk_mismatch_{table_name}.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()

    with db.transaction() as conn:
        conn.execute(f"DROP TABLE {table_name};")
        conn.execute(ddl_recreate)

    with pytest.raises(IncompatibleSchemaError, match=expected_err_match):
        db.schema.verify_schema()


@pytest.mark.parametrize(
    ("table_name", "ddl_recreate", "expected_err_match"),
    [
        (
            "datamgr_instruments",
            """
            CREATE TABLE datamgr_instruments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                connection TEXT DEFAULT '',
                broker_id INTEGER DEFAULT -1,
                description TEXT DEFAULT '',
                tick_size REAL NOT NULL DEFAULT 0.00001,
                tick_step REAL NOT NULL DEFAULT 0.00001,
                tick_value_in_money REAL NOT NULL DEFAULT 10.0,
                point_value REAL NOT NULL DEFAULT 100000.0,
                decimals INTEGER NOT NULL DEFAULT 5,
                default_spread REAL NOT NULL DEFAULT 0.0001,
                default_slippage REAL NOT NULL DEFAULT 0.0,
                min_volume REAL NOT NULL DEFAULT 0.01,
                max_volume REAL NOT NULL DEFAULT 100.0,
                lot_step REAL NOT NULL DEFAULT 0.01,
                margin_rate REAL NOT NULL DEFAULT 0.05,
                swap_long REAL NOT NULL DEFAULT 0.0,
                swap_short REAL NOT NULL DEFAULT 0.0,
                swap_3day_day INTEGER NOT NULL DEFAULT 3,
                commissions TEXT DEFAULT '0.0',
                data_type TEXT DEFAULT 'Forex',
                alias TEXT DEFAULT '',
                exchange TEXT DEFAULT '',
                country TEXT DEFAULT '',
                sector TEXT DEFAULT '',
                min_distance REAL NOT NULL DEFAULT 0.0,
                order_size_multiplier REAL NOT NULL DEFAULT 1.0,
                order_size_step REAL NOT NULL DEFAULT 0.0,
                cot TEXT DEFAULT NULL,
                created_at_utc TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL
            );
            """,
            r"missing non-partial UNIQUE constraint or index on \('symbol',\)",
        ),
        (
            "datamgr_sessions",
            """
            CREATE TABLE datamgr_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                broker_id INTEGER NOT NULL DEFAULT -1,
                description TEXT DEFAULT '',
                timezone TEXT NOT NULL DEFAULT 'UTC',
                windows_json TEXT NOT NULL DEFAULT '[]',
                holidays_json TEXT NOT NULL DEFAULT '[]',
                is_default INTEGER NOT NULL DEFAULT 0
            );
            """,
            r"missing non-partial UNIQUE constraint or index on \('name',\)",
        ),
        (
            "datamgr_sessions",
            """
            CREATE TABLE datamgr_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                broker_id INTEGER NOT NULL DEFAULT -1,
                description TEXT DEFAULT '',
                timezone TEXT NOT NULL DEFAULT 'UTC',
                windows_json TEXT NOT NULL DEFAULT '[]',
                holidays_json TEXT NOT NULL DEFAULT '[]',
                is_default INTEGER NOT NULL DEFAULT 0
            );
            CREATE UNIQUE INDEX idx_sess_partial ON datamgr_sessions(name) WHERE is_default = 1;
            """,
            r"missing non-partial UNIQUE constraint or index on \('name',\)",
        ),
        (
            "datamgr_broker",
            """
            CREATE TABLE datamgr_broker (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                is_system INTEGER NOT NULL DEFAULT 0,
                description TEXT DEFAULT '',
                server_timezone TEXT DEFAULT 'UTC',
                postfix TEXT DEFAULT '',
                enabled INTEGER NOT NULL DEFAULT 1,
                mt_use INTEGER NOT NULL DEFAULT 0,
                stockpicker_use INTEGER NOT NULL DEFAULT 0,
                created_at_utc TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL
            );
            """,
            r"missing non-partial UNIQUE constraint or index on \('name',\)",
        ),
        (
            "datamgr_stock_group",
            """
            CREATE TABLE datamgr_stock_group (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                system INTEGER NOT NULL DEFAULT 0,
                description TEXT DEFAULT ''
            );
            """,
            r"missing non-partial UNIQUE constraint or index on \('name',\)",
        ),
    ],
)
def test_schema_verify_rejects_missing_or_partial_unique_targets(
    tmp_path: Path, table_name: str, ddl_recreate: str, expected_err_match: str
) -> None:
    """Verify that tables missing required non-partial UNIQUE constraints fail verify_schema."""
    db_file = tmp_path / f"unique_target_{table_name}.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()

    with db.transaction() as conn:
        conn.execute(f"DROP TABLE {table_name};")
        conn.executescript(ddl_recreate)

    with pytest.raises(IncompatibleSchemaError, match=expected_err_match):
        db.schema.verify_schema()


def test_schema_verify_rejects_foreign_key_target_mismatch(tmp_path: Path) -> None:
    """Verify that datamgr_stock referencing datamgr_broker is rejected."""
    db_file = tmp_path / "fk_mismatch.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()

    with db.transaction() as conn:
        conn.execute("DROP TABLE datamgr_stock;")
        conn.execute(
            """
            CREATE TABLE datamgr_stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                basket_id INTEGER NOT NULL,
                date_from TEXT NOT NULL,
                date_to TEXT,
                FOREIGN KEY(basket_id) REFERENCES datamgr_broker(id)
            );
            """
        )

    with pytest.raises(
        IncompatibleSchemaError,
        match=r"missing foreign key basket_id -> datamgr_stock_group\(id\)",
    ):
        db.schema.verify_schema()


@pytest.mark.parametrize(
    ("table_name", "ddl_recreate", "expected_err_match"),
    [
        (
            "datamgr_datasets",
            """
            CREATE TABLE datamgr_datasets (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                symbol TEXT NOT NULL,
                underlying TEXT NOT NULL,
                instrument TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                broker TEXT NOT NULL,
                broker_name TEXT NOT NULL,
                timezone TEXT NOT NULL,
                category TEXT NOT NULL,
                date_from TEXT NOT NULL,
                date_to TEXT NOT NULL,
                bars BLOB,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                path TEXT NOT NULL DEFAULT '',
                data_kind TEXT NOT NULL DEFAULT 'bars',
                quality_score REAL NOT NULL DEFAULT 1.0,
                lineage_json TEXT NOT NULL DEFAULT '{}',
                schema_version INTEGER NOT NULL DEFAULT 1
            );
            """,
            r"Column datamgr_datasets\.bars type 'BLOB' has affinity 'BLOB', expected one of \('INTEGER',\)",
        ),
        (
            "datamgr_datasets",
            """
            CREATE TABLE datamgr_datasets (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                symbol TEXT NOT NULL,
                underlying TEXT NOT NULL,
                instrument TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                broker TEXT NOT NULL,
                broker_name TEXT NOT NULL,
                timezone TEXT NOT NULL,
                category TEXT NOT NULL,
                date_from TEXT NOT NULL,
                date_to TEXT NOT NULL,
                bars INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                path TEXT NOT NULL DEFAULT '',
                data_kind TEXT NOT NULL DEFAULT 'bars',
                quality_score REAL NOT NULL DEFAULT 1.0,
                lineage_json TEXT NOT NULL DEFAULT '{}',
                schema_version INTEGER NOT NULL DEFAULT 1
            );
            """,
            r"Column datamgr_datasets\.bars must be NOT NULL",
        ),
        (
            "datamgr_broker_stock",
            """
            CREATE TABLE datamgr_broker_stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                broker_id INTEGER NOT NULL,
                FOREIGN KEY(broker_id) REFERENCES datamgr_stock_group(id)
            );
            """,
            r"missing foreign key broker_id -> datamgr_broker\(id\)",
        ),
    ],
)
def test_schema_verify_rejects_type_affinity_and_nullability_mismatches(
    tmp_path: Path, table_name: str, ddl_recreate: str, expected_err_match: str
) -> None:
    """Verify that type affinity and nullability mismatches fail verify_schema."""
    db_file = tmp_path / f"type_mismatch_{table_name}.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()

    with db.transaction() as conn:
        conn.execute(f"DROP TABLE {table_name};")
        conn.execute(ddl_recreate)

    with pytest.raises(IncompatibleSchemaError, match=expected_err_match):
        db.schema.verify_schema()


def test_live_database_schema_passes_readonly_preflight() -> None:
    """Verify the existing operational database schema passes read-only shape verification."""
    from app.host.persistence.schema import _verify_core_shapes

    db_path = Path("data/database/haruquantai.db")
    if not db_path.exists():
        pytest.skip("Live database not found at data/database/haruquantai.db")

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only = ON;")
        _verify_core_shapes(conn)
    finally:
        conn.close()
