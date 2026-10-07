"""Unit tests for app.host.persistence module.

Validates transactional SQLite database management, WAL journaling, connection pragmas,
schema migrations, narrow typed repositories, optimistic concurrency controls, cooperative
worker leases, startup recovery reconciliation, scoped persistence access facades,
FastAPI REST routes, and CLI diagnostics.
"""

from __future__ import annotations

import sqlite3
import sys
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from app.host.persistence import (
    CorruptDataError,
    DatabaseManager,
    IncompatibleSchemaError,
    LeaseExpiredError,
    PersistenceAccess,
    PersistenceError,
    RevisionConflictError,
    StorageBusyError,
    TypedRepository,
    ValidationError,
    canonical_json,
    create_persistence_router,
    main,
    validate_identifier,
    validate_json_depth,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel


class SampleConfig(BaseModel):
    """Test entity model representing strategy configuration."""

    symbol: str
    timeframe: str
    allocation: float = 1.0


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
    router = create_persistence_router(db_manager)
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


def test_typed_repository_with_external_connection(
    sample_repo: TypedRepository[SampleConfig],
    db_manager: DatabaseManager,
) -> None:
    """Verify repository operations participate in external transaction context."""
    with db_manager.transaction() as conn:
        cfg = SampleConfig(symbol="AVAX/USD", timeframe="1h")
        sample_repo.save("avax_strat", cfg, connection=conn)
        record = sample_repo.get_record("avax_strat", connection=conn)
        assert record is not None
        assert record.revision == 1

    # Confirmed after commit
    assert sample_repo.get("avax_strat") is not None


# ============================================================================
# LeaseManager Tests
# ============================================================================


def test_lease_manager_acquire_and_release(db_manager: DatabaseManager) -> None:
    """Verify normal lease acquisition, list, and release."""
    leases = db_manager.leases

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
    leases = db_manager.leases
    leases.acquire("exclusive_job", "worker_1", ttl_seconds=60.0)

    # Worker 2 attempts acquisition while active
    with pytest.raises(StorageBusyError, match="actively held by worker 'worker_1'"):
        leases.acquire("exclusive_job", "worker_2", ttl_seconds=60.0)


def test_lease_manager_acquire_overwrites_same_holder(
    db_manager: DatabaseManager,
) -> None:
    """Verify same worker can re-acquire an existing lease."""
    leases = db_manager.leases
    rec1 = leases.acquire("re_acquire_job", "worker_1", ttl_seconds=10.0)
    rec2 = leases.acquire("re_acquire_job", "worker_1", ttl_seconds=60.0)
    assert rec2.expires_at_utc > rec1.expires_at_utc


def test_lease_manager_acquire_expired_lease_stealing(
    db_manager: DatabaseManager,
) -> None:
    """Verify worker can acquire a lease if previous holder's lease is expired."""
    leases = db_manager.leases
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
    leases = db_manager.leases
    rec1 = leases.acquire("heartbeat_lease", "worker_alpha", ttl_seconds=10.0)

    rec2 = leases.renew("heartbeat_lease", "worker_alpha", ttl_seconds=60.0)
    assert rec2.expires_at_utc > rec1.expires_at_utc


def test_lease_manager_renew_errors(db_manager: DatabaseManager) -> None:
    """Verify renewal errors on nonexistent, stolen, or expired leases."""
    leases = db_manager.leases

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
    leases = db_manager.leases
    leases.acquire("lock_a", "worker_1", ttl_seconds=60.0)

    # Mismatched holder
    assert leases.release("lock_a", "worker_wrong") is False

    # Nonexistent
    assert leases.release("lock_nonexistent", "worker_1") is False


def test_lease_manager_prune_expired(db_manager: DatabaseManager) -> None:
    """Verify prune_expired removes expired leases and keeps active ones."""
    leases = db_manager.leases
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

    report = db_manager.recovery.reconcile_on_startup()
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
            mgr.recovery.reconcile_on_startup()


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
    code = main()
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
