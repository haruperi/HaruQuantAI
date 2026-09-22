"""Focused tests for host artifacts owner: content addressing, quotas, and integrity."""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from app.host.artifacts import (
    HOST_ARTIFACTS,
    ArtifactCorruptionError,
    ArtifactNotFoundError,
    ArtifactQuotaExceededError,
    ArtifactRef,
    ArtifactsConfig,
    _artifacts_feature,
    _FilesystemArtifactStore,
)
from app.host.storage import StorageConfig, _SqliteStorage, _storage_feature
from app.kernel.bootstrapper import Runtime


def _build_store(
    tmp_path: Path, max_artifact_bytes: int = 50
) -> tuple[_FilesystemArtifactStore, _SqliteStorage]:
    """Build an artifact store over an isolated temporary SQLite database."""

    storage = _SqliteStorage(StorageConfig(database_path=tmp_path / "storage.db"))
    config = ArtifactsConfig(
        root_dir=tmp_path / "artifacts", max_artifact_bytes=max_artifact_bytes
    )
    return _FilesystemArtifactStore(config, storage), storage


def test_artifact_ref_validation() -> None:
    """Test ArtifactRef validation constraints."""
    valid_hex = "a" * 64
    ref = ArtifactRef(digest=valid_hex, size_bytes=10)
    assert ref.digest == valid_hex
    assert ref.size_bytes == 10

    with pytest.raises(ValueError, match="digest must be a 64-character hex string"):
        ArtifactRef(digest="short", size_bytes=10)

    with pytest.raises(ValueError, match="size_bytes must be >= 0"):
        ArtifactRef(digest=valid_hex, size_bytes=-1)


def test_artifacts_crud_and_deduplication(tmp_path: Path) -> None:
    """Test storing, fetching, deduplication, and deleting artifacts."""
    db_file = tmp_path / "storage.db"
    storage = _SqliteStorage(StorageConfig(database_path=db_file))
    artifacts_dir = tmp_path / "artifacts"
    config = ArtifactsConfig(root_dir=artifacts_dir)
    store = _FilesystemArtifactStore(config, storage)

    content = b"Hello, HaruQuantAI Quantitative Artifact!"
    expected_digest = hashlib.sha256(content).hexdigest()

    # Put artifact
    res1 = store.put_artifact(
        content,
        media_type="text/plain",
        provenance_hash="prov_123",
        tags=[("author", "test")],
    )
    assert res1.deduplicated is False
    assert res1.ref.digest == expected_digest
    assert res1.ref.size_bytes == len(content)
    assert res1.metadata.media_type == "text/plain"
    assert res1.metadata.provenance_hash == "prov_123"
    assert ("author", "test") in res1.metadata.tags

    # Read back and verify bytes
    retrieved = store.get_artifact_bytes(expected_digest)
    assert retrieved == content

    # Check has_artifact and get_metadata
    assert store.has_artifact(expected_digest) is True
    meta = store.get_metadata(expected_digest)
    assert meta is not None
    assert meta.ref.digest == expected_digest
    assert meta.ref.size_bytes == len(content)

    # Putting identical content should deduplicate
    res2 = store.put_artifact(content, media_type="text/plain")
    assert res2.deduplicated is True
    assert res2.ref.digest == expected_digest

    # Delete artifact
    deleted = store.delete_artifact(expected_digest)
    assert deleted is True
    assert store.has_artifact(expected_digest) is False
    assert store.get_metadata(expected_digest) is None

    # Getting deleted artifact raises NotFoundError
    with pytest.raises(ArtifactNotFoundError):
        store.get_artifact_bytes(expected_digest)

    storage.close()


def test_artifacts_quota_enforcement(tmp_path: Path) -> None:
    """Test per-artifact and total storage quota enforcement."""
    db_file = tmp_path / "storage.db"
    storage = _SqliteStorage(StorageConfig(database_path=db_file))
    artifacts_dir = tmp_path / "artifacts"
    config = ArtifactsConfig(
        root_dir=artifacts_dir,
        max_artifact_bytes=50,
        max_total_bytes=80,
    )
    store = _FilesystemArtifactStore(config, storage)

    # 1. Per-artifact quota exceeded
    large_data = b"x" * 60
    with pytest.raises(ArtifactQuotaExceededError, match="exceeds max allowed"):
        store.put_artifact(large_data)

    # 2. Total storage quota exceeded
    data1 = b"a" * 45
    store.put_artifact(data1)

    data2 = b"b" * 45
    with pytest.raises(ArtifactQuotaExceededError, match="Total storage quota"):
        store.put_artifact(data2)

    storage.close()


def test_artifacts_path_escape_and_corruption(tmp_path: Path) -> None:
    """Test rejection of path escape and corrupted artifact detection."""
    db_file = tmp_path / "storage.db"
    storage = _SqliteStorage(StorageConfig(database_path=db_file))
    artifacts_dir = tmp_path / "artifacts"
    config = ArtifactsConfig(root_dir=artifacts_dir)
    store = _FilesystemArtifactStore(config, storage)

    # Invalid digest length
    with pytest.raises(ValueError, match="Digest must be 64 characters"):
        store.get_artifact_bytes("invalid_digest")

    # Store valid artifact
    content = b"valid content"
    digest = hashlib.sha256(content).hexdigest()
    store.put_artifact(content)

    # Intentionally corrupt the file on disk
    target = artifacts_dir / "objects" / digest[:2] / digest[2:]
    target.write_bytes(b"corrupted content!")

    # Reading should fail digest verification
    with pytest.raises(ArtifactCorruptionError, match="does not match expected"):
        store.get_artifact_bytes(digest)

    storage.close()


def test_artifacts_feature_composition(tmp_path: Path) -> None:
    """Test Runtime composition with HOST_STORAGE and HOST_ARTIFACTS."""

    async def scenario() -> None:
        storage_feature = _storage_feature(
            StorageConfig(database_path=tmp_path / "storage.db")
        )
        artifacts_feature = _artifacts_feature(
            ArtifactsConfig(root_dir=tmp_path / "artifacts")
        )

        runtime = Runtime(
            (lambda: storage_feature, lambda: artifacts_feature),
        )
        async with runtime:
            artifacts = runtime.require(HOST_ARTIFACTS)
            res = artifacts.put_artifact(b"test data", media_type="text/plain")
            assert res.ref.size_bytes == 9
            assert artifacts.get_artifact_bytes(res.ref.digest) == b"test data"

    asyncio.run(scenario())


def test_streaming_put_matches_bytes_and_metadata(tmp_path: Path) -> None:
    store, _storage = _build_store(tmp_path)
    chunks = [b"hello ", b"streaming ", b"world"]
    res = store.put_artifact_stream(
        chunks,
        media_type="text/plain",
        source_fingerprint="src_fp",
        dependency_fingerprint="dep_fp",
        data_fingerprint="data_fp",
        lineage=("job_1", "job_2"),
    )
    assert res.deduplicated is False
    assert store.get_artifact_bytes(res.ref.digest) == b"hello streaming world"
    meta = store.get_metadata(res.ref.digest)
    assert meta is not None
    assert meta.source_fingerprint == "src_fp"
    assert meta.dependency_fingerprint == "dep_fp"
    assert meta.data_fingerprint == "data_fp"
    assert meta.lineage == ("job_1", "job_2")
    assert meta.refcount == 0

    # identical content dedups without mutation
    again = store.put_artifact_stream([b"hello streaming world"])
    assert again.deduplicated is True
    assert again.ref == res.ref


def test_streaming_cancel_removes_temp_and_publishes_nothing(
    tmp_path: Path,
) -> None:
    from app.host.artifacts import ArtifactCancelledError

    store, _storage = _build_store(tmp_path)
    emitted: list[bytes] = []

    def gen() -> Any:
        for chunk in (b"part1-", b"part2-", b"part3-"):
            emitted.append(chunk)
            yield chunk

    with pytest.raises(ArtifactCancelledError, match="cancelled"):
        store.put_artifact_stream(gen(), should_cancel=lambda: len(emitted) >= 2)
    # no partial file reported as complete
    tmp_files = list((tmp_path / "artifacts" / ".tmp").iterdir())
    assert tmp_files == []
    objects = [
        p for p in (tmp_path / "artifacts" / "objects").rglob("*") if p.is_file()
    ]
    assert objects == []


def test_streaming_quota_enforced_mid_stream(tmp_path: Path) -> None:
    store, _storage = _build_store(tmp_path)

    with pytest.raises(ArtifactQuotaExceededError, match="mid-stream"):
        store.put_artifact_stream(
            [b"x" * 30, b"y" * 30],
            # default max_artifact_bytes=50 in _build_store config
        )


def test_retention_active_reference_protection(tmp_path: Path) -> None:
    from app.host.artifacts import ArtifactInUseError

    store, _storage = _build_store(tmp_path)
    res = store.put_artifact(b"retained content")
    digest = res.ref.digest

    store.acquire_reference(digest)
    store.acquire_reference(digest)
    assert store.get_metadata(digest) is not None
    assert store.get_metadata(digest).refcount == 2  # type: ignore[union-attr]

    store.request_deletion(digest)
    marked = store.get_metadata(digest)
    assert marked is not None
    assert marked.retention_policy == "retention_marked"

    with pytest.raises(ArtifactInUseError, match="active reference"):
        store.delete_artifact(digest)

    store.release_reference(digest)
    store.release_reference(digest)
    assert store.delete_artifact(digest) is True
    assert store.has_artifact(digest) is False


def test_read_verifies_size_against_metadata(tmp_path: Path) -> None:
    from app.host.artifacts import ARTIFACTS_NAMESPACE, ArtifactCorruptionError
    from app.host.storage import StorageMutation, StorageRecord

    store, storage = _build_store(tmp_path)
    res = store.put_artifact(b"sized-content")
    digest = res.ref.digest

    # tamper the recorded size in metadata storage
    rec: StorageRecord | None = storage.get_record(ARTIFACTS_NAMESPACE, digest)
    assert rec is not None
    tampered = json.loads(rec.payload_bytes.decode("utf-8"))
    tampered["size_bytes"] = 999
    bad_bytes = json.dumps(tampered, sort_keys=True, separators=(",", ":")).encode()
    storage.commit_transaction(
        [
            StorageMutation(
                namespace=ARTIFACTS_NAMESPACE,
                key=digest,
                schema_version=1,
                payload_bytes=bad_bytes,
                expected_revision=rec.revision,
            )
        ]
    )

    with pytest.raises(ArtifactCorruptionError, match="size"):
        store.get_artifact_bytes(digest)


def test_metadata_delete_failure_preserves_content(tmp_path: Path) -> None:
    """A CAS failure during metadata deletion never removes the content."""
    from app.host.artifacts import ArtifactError
    from app.host.storage import StorageTransactionResult

    store, storage = _build_store(tmp_path)
    res = store.put_artifact(b"precious content")

    original = storage.commit_transaction

    def failing_delete(mutations: Any) -> Any:
        if any(type(m).__name__ == "StorageDelete" for m in mutations):
            return StorageTransactionResult(committed=False)
        return original(mutations)

    storage.commit_transaction = failing_delete  # type: ignore[method-assign]

    with pytest.raises(ArtifactError, match="Metadata deletion conflict"):
        store.delete_artifact(res.ref.digest)

    # content and metadata both survive the failed deletion
    assert store.get_artifact_bytes(res.ref.digest) == b"precious content"
    assert store.get_metadata(res.ref.digest) is not None
