"""Focused tests for host artifacts owner: content addressing, quotas, and integrity."""

from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path

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
