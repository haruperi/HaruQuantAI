"""Focused tests for host storage owner: SQLite records, migrations, and CAS."""

from __future__ import annotations

from pathlib import Path

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
