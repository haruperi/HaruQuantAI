"""Focused tests for host storage owner: SQLite records, migrations, and CAS."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from app.host.storage import (
    HOST_STORAGE,
    StorageClosedError,
    StorageConfig,
    StorageDelete,
    StorageMutation,
    StorageRecord,
    _SqliteStorage,
    _storage_feature,
)
from app.kernel.bootstrapper import Runtime


def test_storage_validation_and_records(tmp_path: Path) -> None:
    """Test field validation on storage dataclasses."""
    with pytest.raises(ValueError, match="namespace must be a non-empty string"):
        StorageRecord(
            namespace="",
            key="k",
            revision=1,
            schema_version=1,
            payload_bytes=b"{}",
            created_at_utc="now",
            updated_at_utc="now",
        )

    with pytest.raises(ValueError, match="revision must be >= 1"):
        StorageRecord(
            namespace="ns",
            key="k",
            revision=0,
            schema_version=1,
            payload_bytes=b"{}",
            created_at_utc="now",
            updated_at_utc="now",
        )

    with pytest.raises(TypeError, match="payload_bytes must be bytes"):
        StorageMutation(
            namespace="ns",
            key="k",
            schema_version=1,
            payload_bytes="not_bytes",  # type: ignore[arg-type]
        )


def test_storage_sqlite_crud_and_cas(tmp_path: Path) -> None:
    """Test CRUD operations, compare-and-swap revisions, and transaction atomicity."""
    db_file = tmp_path / "test_storage.db"
    config = StorageConfig(database_path=db_file)
    storage = _SqliteStorage(config)

    # Initially empty
    assert storage.get_record("users", "alice") is None

    # Insert Alice (expected_revision=0 or None)
    m1 = StorageMutation(
        namespace="users",
        key="alice",
        schema_version=1,
        payload_bytes=b'{"name":"Alice"}',
        expected_revision=0,
    )
    res = storage.commit_transaction([m1])
    assert res.committed is True
    assert len(res.records) == 1
    alice_rec = res.records[0]
    assert alice_rec.revision == 1
    assert alice_rec.payload_bytes == b'{"name":"Alice"}'

    # Fetch Alice
    fetched = storage.get_record("users", "alice")
    assert fetched is not None
    assert fetched.revision == 1
    assert fetched.payload_bytes == b'{"name":"Alice"}'

    # CAS Conflict: try to update expecting rev 0
    m_fail = StorageMutation(
        namespace="users",
        key="alice",
        schema_version=1,
        payload_bytes=b'{"name":"Alice Updated"}',
        expected_revision=0,
    )
    res_fail = storage.commit_transaction([m_fail])
    assert res_fail.committed is False
    assert len(res_fail.conflicts) == 1
    assert res_fail.conflicts[0].expected_revision == 0
    assert res_fail.conflicts[0].actual_revision == 1

    # Database was NOT modified on conflict
    assert storage.get_record("users", "alice") == fetched

    # Successful CAS update expecting rev 1 -> moves to rev 2
    m_ok = StorageMutation(
        namespace="users",
        key="alice",
        schema_version=1,
        payload_bytes=b'{"name":"Alice Updated"}',
        expected_revision=1,
    )
    res_ok = storage.commit_transaction([m_ok])
    assert res_ok.committed is True
    assert res_ok.records[0].revision == 2
    assert res_ok.records[0].payload_bytes == b'{"name":"Alice Updated"}'

    # Multi-operation atomic transaction: insert bob + update alice
    m_bob = StorageMutation(
        namespace="users",
        key="bob",
        schema_version=1,
        payload_bytes=b'{"name":"Bob"}',
        expected_revision=0,
    )
    m_alice3 = StorageMutation(
        namespace="users",
        key="alice",
        schema_version=1,
        payload_bytes=b'{"name":"Alice V3"}',
        expected_revision=2,
    )
    res_multi = storage.commit_transaction([m_bob, m_alice3])
    assert res_multi.committed is True
    assert len(res_multi.records) == 2

    assert storage.get_record("users", "bob") is not None
    alice_v3 = storage.get_record("users", "alice")
    assert alice_v3 is not None
    assert alice_v3.revision == 3

    # Delete Alice
    d_alice = StorageDelete(namespace="users", key="alice", expected_revision=3)
    res_del = storage.commit_transaction([d_alice])
    assert res_del.committed is True
    assert storage.get_record("users", "alice") is None

    # Deleting non-existent record with expected_revision fails
    d_fail = StorageDelete(namespace="users", key="alice", expected_revision=1)
    res_del_fail = storage.commit_transaction([d_fail])
    assert res_del_fail.committed is False

    storage.close()
    with pytest.raises(StorageClosedError):
        storage.get_record("users", "bob")


def test_storage_scan_pagination_and_deterministic_order(tmp_path: Path) -> None:
    """Test scan_records ordering, prefix filtering, and pagination."""
    config = StorageConfig(database_path=tmp_path / "scan.db", max_page_size=5)
    storage = _SqliteStorage(config)

    # Insert 10 items in reverse order
    mutations = [
        StorageMutation(
            namespace="items",
            key=f"item_{i:02d}",
            schema_version=1,
            payload_bytes=f'{{"idx":{i}}}'.encode(),
        )
        for i in reversed(range(10))
    ]
    res = storage.commit_transaction(mutations)
    assert res.committed is True

    # Scan page 1 (limit 3)
    page1 = storage.scan_records("items", limit=3)
    assert len(page1.records) == 3
    assert [r.key for r in page1.records] == ["item_00", "item_01", "item_02"]
    assert page1.next_token == "item_02"
    assert page1.total_count == 10

    # Scan page 2 using after_key
    page2 = storage.scan_records("items", limit=3, after_key=page1.next_token)
    assert len(page2.records) == 3
    assert [r.key for r in page2.records] == ["item_03", "item_04", "item_05"]
    assert page2.next_token == "item_05"

    # Scan with prefix
    page_prefix = storage.scan_records("items", prefix="item_0")
    assert page_prefix.total_count == 10

    storage.close()


def test_storage_feature_lifecycle(tmp_path: Path) -> None:
    """Test feature registration and context publication."""

    async def scenario() -> None:
        config = StorageConfig(database_path=tmp_path / "feature.db")
        feature = _storage_feature(config)

        runtime = Runtime(
            (lambda: feature,),
        )
        async with runtime:
            storage = runtime.require(HOST_STORAGE)
            res = storage.commit_transaction(
                [
                    StorageMutation(
                        namespace="test",
                        key="k1",
                        schema_version=1,
                        payload_bytes=b"ok",
                    )
                ]
            )
            assert res.committed is True
            assert storage.get_record("test", "k1") is not None

    import asyncio

    asyncio.run(scenario())


def test_migration_status_and_repeat_open_idempotent(tmp_path: Path) -> None:
    from app.host.storage import StorageStatus

    db = tmp_path / "storage.db"
    store = _SqliteStorage(StorageConfig(database_path=db))
    status = store.status()
    assert isinstance(status, StorageStatus)
    assert status.ready is True
    assert status.schema_version == 1
    assert status.applied_migrations == (1,)
    store.close()

    # Repeat open: no duplicate migration rows
    again = _SqliteStorage(StorageConfig(database_path=db))
    assert again.status().applied_migrations == (1,)
    again.close()


def test_upgrade_fixture_from_pre_migration_database(tmp_path: Path) -> None:
    """A pre-existing records table without schema_migrations is upgraded."""
    import sqlite3

    db = tmp_path / "legacy.db"
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE records (namespace TEXT, key TEXT, revision INTEGER,"
        " schema_version INTEGER, payload_bytes BLOB, created_at_utc TEXT,"
        " updated_at_utc TEXT, PRIMARY KEY (namespace, key));"
    )
    conn.commit()
    conn.close()

    store = _SqliteStorage(StorageConfig(database_path=db))
    assert store.status().schema_version == 1
    store.commit_transaction(
        [
            StorageMutation(
                namespace="legacy",
                key="k",
                schema_version=1,
                payload_bytes=b"{}",
                expected_revision=0,
            )
        ]
    )
    store.close()


def test_corrupt_database_fails_closed(tmp_path: Path) -> None:
    from app.host.storage import StorageError

    db = tmp_path / "corrupt.db"
    db.write_bytes(b"this is definitely not a sqlite database" * 100)
    with pytest.raises(StorageError, match="failed to open or migrate"):
        _SqliteStorage(StorageConfig(database_path=db))


def test_future_schema_version_fails_closed(tmp_path: Path) -> None:
    import sqlite3

    from app.host.storage import StorageMigrationError

    db = tmp_path / "future.db"
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY,"
        " name TEXT NOT NULL, applied_at_utc TEXT NOT NULL);"
    )
    conn.execute("INSERT INTO schema_migrations VALUES (999, 'future', '2026-01-01Z');")
    conn.commit()
    conn.close()

    with pytest.raises(StorageMigrationError, match="newer than supported"):
        _SqliteStorage(StorageConfig(database_path=db))


def test_migration_rollback_leaves_database_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failing migration rolls back and the next open succeeds."""
    import app.host.storage as storage_module
    from app.host.storage import StorageMigrationError

    db = tmp_path / "rollback.db"
    store = _SqliteStorage(StorageConfig(database_path=db))
    store.close()

    original_migrate = storage_module._SqliteStorage._migrate

    def failing_migrate(self: object) -> None:
        original_migrate(self)  # type: ignore[arg-type]
        raise StorageMigrationError("injected failure")

    monkeypatch.setattr(storage_module._SqliteStorage, "_migrate", failing_migrate)
    with pytest.raises(StorageMigrationError, match="injected failure"):
        _SqliteStorage(StorageConfig(database_path=db))
    monkeypatch.undo()

    reopened = _SqliteStorage(StorageConfig(database_path=db))
    assert reopened.status().schema_version == 1
    reopened.close()


def test_async_facade_uses_owned_writer_thread(tmp_path: Path) -> None:
    """Async operations run on the single owned writer thread, not the loop."""
    import threading

    async def scenario() -> None:
        db = tmp_path / "async.db"
        store = _SqliteStorage(StorageConfig(database_path=db))
        try:
            for i in range(20):
                result = await store.async_commit_transaction(
                    [
                        StorageMutation(
                            namespace="async",
                            key=f"k{i}",
                            schema_version=1,
                            payload_bytes=b"{}",
                            expected_revision=0,
                        )
                    ]
                )
                assert result.committed
                rec = await store.async_get_record("async", f"k{i}")
                assert rec is not None
            # all writes serialized through one named writer thread
            threads = store._writer._threads
            assert len(threads) == 1
            assert next(iter(threads)).name.startswith("haruquantai-storage")
            assert threading.current_thread().name.startswith("MainThread")
        finally:
            store.close()

    asyncio.run(scenario())


def test_concurrent_readers_single_writer(tmp_path: Path) -> None:
    """Multiple readers race one writer without corruption or busy errors."""
    import concurrent.futures

    db = tmp_path / "concurrent.db"
    writer = _SqliteStorage(StorageConfig(database_path=db))
    for i in range(10):
        writer.commit_transaction(
            [
                StorageMutation(
                    namespace="concurrent",
                    key=f"w{i}",
                    schema_version=1,
                    payload_bytes=b"{}",
                    expected_revision=0,
                )
            ]
        )

    def reader(i: int) -> int:
        store = _SqliteStorage(StorageConfig(database_path=db))
        try:
            page = store.scan_records("concurrent", limit=100)
            return len(page.records)
        finally:
            store.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        counts = list(pool.map(reader, range(8)))
    assert all(c == 10 for c in counts)
    writer.close()


def test_sync_operations_run_on_owned_writer_thread(tmp_path: Path) -> None:
    """Synchronous public calls serialize on the single owned writer thread."""
    import threading

    db = tmp_path / "sync.db"
    store = _SqliteStorage(StorageConfig(database_path=db))
    seen_threads: set[str] = set()
    original_commit = store._commit_transaction_impl
    original_get = store._get_record_impl

    def recording_commit(mutations: Any) -> Any:
        seen_threads.add(threading.current_thread().name)
        return original_commit(mutations)

    def recording_get(namespace: str, key: str) -> Any:
        seen_threads.add(threading.current_thread().name)
        return original_get(namespace, key)

    store._commit_transaction_impl = recording_commit  # type: ignore[method-assign]
    store._get_record_impl = recording_get  # type: ignore[method-assign]

    # synchronous write from the test (main) thread executes on the writer
    store.commit_transaction(
        [
            StorageMutation(
                namespace="sync",
                key="k1",
                schema_version=1,
                payload_bytes=b"{}",
                expected_revision=0,
            )
        ]
    )
    assert len(seen_threads) == 1
    assert next(iter(seen_threads)).startswith("haruquantai-storage")
    assert threading.current_thread().name != "haruquantai-storage"

    # synchronous read also serializes through the writer thread
    seen_threads.clear()
    assert store.get_record("sync", "k1") is not None
    assert len(seen_threads) == 1
    assert next(iter(seen_threads)).startswith("haruquantai-storage")
    store.close()


def test_artifacts_sync_writes_serialize_on_writer_thread(
    tmp_path: Path,
) -> None:
    """Artifact metadata commits from any caller thread hit the writer thread."""
    import threading

    from app.host.artifacts import ArtifactsConfig, _FilesystemArtifactStore

    storage = _SqliteStorage(StorageConfig(database_path=tmp_path / "a.db"))
    store = _FilesystemArtifactStore(
        ArtifactsConfig(root_dir=tmp_path / "artifacts"), storage
    )
    seen: set[str] = set()
    original_commit = storage._commit_transaction_impl

    def recording(mutations: Any) -> Any:
        seen.add(threading.current_thread().name)
        return original_commit(mutations)

    storage._commit_transaction_impl = recording  # type: ignore[method-assign]
    res = store.put_artifact(b"artifact bytes")
    assert store.get_metadata(res.ref.digest) is not None
    assert len(seen) == 1
    assert next(iter(seen)).startswith("haruquantai-storage")
