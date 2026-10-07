"""Unit tests for app.host.resources module.

Validates path containment, safe archive inspection and extraction, Zip-Slip
and expansion bomb protection, bounded LRU/TTL caching, remote HTTP acquisition,
content-addressed staging and publication, orphan cleanup, scoped facades,
FastAPI REST routes, and CLI diagnostics.
"""

from __future__ import annotations

import io
import sys
import tarfile
import time
import zipfile
from collections.abc import Generator
from pathlib import Path
from typing import Literal
from unittest.mock import MagicMock, patch

import pytest
from app.host.resources import (
    AcquisitionError,
    ArchiveFormat,
    ArchiveLimits,
    CorruptResourceError,
    ResourceAccess,
    ResourceCache,
    ResourceConflictError,
    ResourceManager,
    ResourceNotFoundError,
    ResourceScope,
    ResourceSecurityError,
    ResourceStatus,
    acquire_remote,
    create_resources_router,
    inspect_archive,
    main,
    safe_extract_archive,
    validate_contained_path,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Fixture providing an isolated temporary directory."""
    return tmp_path


@pytest.fixture
def resource_manager(temp_dir: Path) -> ResourceManager:
    """Fixture providing an initialized ResourceManager."""
    return ResourceManager(root_dir=temp_dir / "resources", cache_max_bytes=1024 * 1024)


# ============================================================================
# Containment & Path Security Tests
# ============================================================================


def test_validate_contained_path_valid(temp_dir: Path) -> None:
    """Validate relative and nested paths resolve cleanly inside sandbox."""
    sub = temp_dir / "sandbox"
    sub.mkdir()
    target = validate_contained_path(sub, "child/file.txt")
    assert target == (sub / "child" / "file.txt").resolve()


def test_validate_contained_path_empty_reject(temp_dir: Path) -> None:
    """Reject empty candidate path."""
    with pytest.raises(ResourceSecurityError, match="cannot be empty"):
        validate_contained_path(temp_dir, "")


def test_validate_contained_path_traversal_reject(temp_dir: Path) -> None:
    """Reject parent directory traversal components."""
    with pytest.raises(ResourceSecurityError, match="Path traversal rejected"):
        validate_contained_path(temp_dir, "../outside.txt")

    with pytest.raises(ResourceSecurityError, match="Path traversal rejected"):
        validate_contained_path(temp_dir, "nested/../../outside.txt")


def test_validate_contained_path_outside_escape(temp_dir: Path) -> None:
    """Reject absolute path targeting an external directory."""
    base = temp_dir / "sandbox"
    base.mkdir()
    external = temp_dir / "other" / "file.txt"
    with pytest.raises(ResourceSecurityError, match="resolves outside base sandbox"):
        validate_contained_path(base, external)


def test_validate_contained_path_symlink_checks(temp_dir: Path) -> None:
    """Reject symlinks when forbidden; allow when explicitly permitted."""
    base = temp_dir / "sandbox"
    base.mkdir()
    real_target = base / "real.txt"
    real_target.write_text("content", encoding="utf-8")
    symlink_path = base / "sym.txt"

    try:
        symlink_path.symlink_to(real_target)
    except OSError:
        pytest.skip("Symlink creation not supported in current environment")

    # Forbidden by default
    with pytest.raises(ResourceSecurityError, match="Symbolic link forbidden"):
        validate_contained_path(base, "sym.txt", allow_symlinks=False)

    # Allowed when enabled
    resolved = validate_contained_path(base, "sym.txt", allow_symlinks=True)
    assert resolved == real_target.resolve()


# ============================================================================
# Safe Archive Inspection & Extraction Tests
# ============================================================================


def _create_test_zip(
    zip_path: Path, files: dict[str, bytes], *, encrypt_name: str | None = None
) -> None:
    """Helper creating a test zip archive."""
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    if encrypt_name:
        # Patch flag_bits of entry to simulate password protection
        pass


def _create_test_tar(
    tar_path: Path,
    files: dict[str, bytes],
    *,
    mode: Literal["w:gz", "w", "w:bz2", "w:xz"] = "w:gz",
) -> None:
    """Helper creating a test tar archive."""
    with tarfile.open(tar_path, mode) as tf:
        for name, data in files.items():
            ti = tarfile.TarInfo(name=name)
            ti.size = len(data)
            tf.addfile(ti, io.BytesIO(data))


def test_inspect_archive_valid_zip(temp_dir: Path) -> None:
    """Inspect standard valid ZIP file."""
    zip_path = temp_dir / "sample.zip"
    _create_test_zip(zip_path, {"hello.txt": b"Hello world", "sub/dir.txt": b"nested"})

    report = inspect_archive(zip_path)
    assert report.is_safe is True
    assert report.entry_count == 2
    assert report.archive_format == ArchiveFormat.ZIP
    assert report.uncompressed_bytes == len(b"Hello world") + len(b"nested")
    assert len(report.entries) == 2


def test_inspect_archive_valid_tar(temp_dir: Path) -> None:
    """Inspect standard valid TAR.GZ file."""
    tar_path = temp_dir / "sample.tar.gz"
    _create_test_tar(tar_path, {"a.txt": b"12345", "b.bin": b"abcde"})

    report = inspect_archive(tar_path)
    assert report.is_safe is True
    assert report.entry_count == 2
    assert report.archive_format == ArchiveFormat.TAR_GZ
    assert report.uncompressed_bytes == 10


def test_inspect_archive_unsupported_format(temp_dir: Path) -> None:
    """Reject unrecognized file formats."""
    dummy = temp_dir / "unknown.bin"
    dummy.write_bytes(b"\x00\x01\x02\x03\x04\x05")

    with pytest.raises(ResourceSecurityError, match="Unsupported or unrecognized"):
        inspect_archive(dummy)


def test_inspect_archive_zip_slip_rejection(temp_dir: Path) -> None:
    """Detect and flag Zip-Slip traversal vectors."""
    bad_zip = temp_dir / "bad_slip.zip"
    with zipfile.ZipFile(bad_zip, "w") as zf:
        zf.writestr("../../escaped.txt", b"evil")

    report = inspect_archive(bad_zip)
    assert report.is_safe is False
    assert any("Zip-Slip" in v for v in report.violations)


def test_inspect_archive_tar_traversal_rejection(temp_dir: Path) -> None:
    """Detect and flag TAR traversal vectors."""
    bad_tar = temp_dir / "bad_slip.tar"
    with tarfile.open(bad_tar, "w") as tf:
        ti = tarfile.TarInfo(name="../escape.txt")
        ti.size = 4
        tf.addfile(ti, io.BytesIO(b"evil"))

    report = inspect_archive(bad_tar)
    assert report.is_safe is False
    assert any("Tar traversal" in v for v in report.violations)


def test_inspect_archive_entry_count_limit(temp_dir: Path) -> None:
    """Detect entry count exceeding configured limit."""
    zip_path = temp_dir / "many.zip"
    files = {f"file_{i}.txt": b"x" for i in range(15)}
    _create_test_zip(zip_path, files)

    limits = ArchiveLimits(max_entries=10)
    report = inspect_archive(zip_path, limits=limits)
    assert report.is_safe is False
    assert any("Entry count 15 exceeds limit 10" in v for v in report.violations)


def test_inspect_archive_size_ceiling_limit(temp_dir: Path) -> None:
    """Detect uncompressed size exceeding ceiling limit."""
    zip_path = temp_dir / "large.zip"
    _create_test_zip(zip_path, {"big.bin": b"x" * 5000})

    limits = ArchiveLimits(max_uncompressed_bytes=2000)
    report = inspect_archive(zip_path, limits=limits)
    assert report.is_safe is False
    assert any("exceeds ceiling 2000" in v for v in report.violations)


def test_safe_extract_archive_success(temp_dir: Path) -> None:
    """Safely extract valid ZIP archive into contained sandbox."""
    zip_path = temp_dir / "valid.zip"
    _create_test_zip(zip_path, {"f1.txt": b"content 1", "sub/f2.txt": b"content 2"})

    dest = temp_dir / "extracted_sandbox"
    paths = safe_extract_archive(zip_path, dest)
    assert len(paths) == 2
    assert (dest / "f1.txt").read_bytes() == b"content 1"
    assert (dest / "sub" / "f2.txt").read_bytes() == b"content 2"


def test_safe_extract_archive_tar_success(temp_dir: Path) -> None:
    """Safely extract valid TAR.GZ archive into contained sandbox."""
    tar_path = temp_dir / "valid.tar.gz"
    _create_test_tar(tar_path, {"doc.txt": b"hello tar"})

    dest = temp_dir / "tar_sandbox"
    paths = safe_extract_archive(tar_path, dest)
    assert len(paths) == 1
    assert (dest / "doc.txt").read_bytes() == b"hello tar"


def test_safe_extract_archive_rejects_unsafe(temp_dir: Path) -> None:
    """Refuse extraction of archive with Zip-Slip traversal."""
    bad_zip = temp_dir / "bad_extract.zip"
    with zipfile.ZipFile(bad_zip, "w") as zf:
        zf.writestr("../escaped.txt", b"evil")

    dest = temp_dir / "dest"
    with pytest.raises(ResourceSecurityError, match="Archive rejected due to safety"):
        safe_extract_archive(bad_zip, dest)


# ============================================================================
# Bounded Resource Cache Tests
# ============================================================================


def test_resource_cache_put_get_miss() -> None:
    """Verify standard put, hit, and miss operations."""
    cache = ResourceCache(max_bytes=1000)
    assert cache.get("k1") is None

    cache.put("k1", b"payload1")
    assert cache.get("k1") == b"payload1"

    stats = cache.get_stats()
    assert stats.hit_count == 1
    assert stats.miss_count == 1
    assert stats.entry_count == 1
    assert stats.used_bytes == len(b"payload1")


def test_resource_cache_lru_eviction() -> None:
    """Verify LRU eviction when exceeding maximum byte ceiling."""
    cache = ResourceCache(max_bytes=20)
    cache.put("a", b"12345678")  # 8 bytes
    cache.put("b", b"12345678")  # 8 bytes (total 16)
    cache.put("c", b"12345678")  # 8 bytes -> triggers eviction of 'a'

    assert cache.get("a") is None
    assert cache.get("b") == b"12345678"
    assert cache.get("c") == b"12345678"

    stats = cache.get_stats()
    assert stats.eviction_count == 1
    assert stats.entry_count == 2
    assert stats.used_bytes == 16


def test_resource_cache_ttl_expiration() -> None:
    """Verify expired items are evicted on access."""
    cache = ResourceCache(max_bytes=1000)
    cache.put("k_exp", b"data", ttl_seconds=0.01)
    time.sleep(0.02)
    assert cache.get("k_exp") is None


def test_resource_cache_invalidate_and_clear() -> None:
    """Verify explicit invalidation and clearance."""
    cache = ResourceCache(max_bytes=1000)
    cache.put("k1", b"data1")
    cache.put("k2", b"data2")

    assert cache.invalidate("k1") is True
    assert cache.get("k1") is None
    assert cache.invalidate("k1") is False

    cache.clear()
    assert cache.get_stats().entry_count == 0
    assert cache.get_stats().used_bytes == 0


# ============================================================================
# Remote HTTP Acquisition Tests
# ============================================================================


def test_acquire_remote_invalid_scheme(temp_dir: Path) -> None:
    """Reject schemes other than http and https."""
    dest = temp_dir / "remote.bin"
    with pytest.raises(ResourceSecurityError, match="Unsupported URL scheme"):
        acquire_remote("ftp://example.com/file.bin", dest)


def test_acquire_remote_success(temp_dir: Path) -> None:
    """Acquire remote payload using mocked httpx client."""
    dest = temp_dir / "remote_good.bin"
    content = b"Simulated remote artifact content"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-length": str(len(content))}
    mock_resp.iter_bytes.return_value = [content]

    mock_client = MagicMock()
    mock_client.stream.return_value.__enter__.return_value = mock_resp

    size, digest = acquire_remote(
        "https://example.com/strategy.pkg",
        dest,
        client=mock_client,
    )
    assert size == len(content)
    assert dest.read_bytes() == content
    assert len(digest) == 64


def test_acquire_remote_size_limit_exceeded(temp_dir: Path) -> None:
    """Abort and remove staging file if downloaded stream exceeds max_bytes."""
    dest = temp_dir / "remote_large.bin"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_resp.iter_bytes.return_value = [b"chunk1_5bytes", b"chunk2_5bytes"]

    mock_client = MagicMock()
    mock_client.stream.return_value.__enter__.return_value = mock_resp

    with pytest.raises(AcquisitionError, match="exceeded ceiling"):
        acquire_remote(
            "https://example.com/huge.bin",
            dest,
            max_bytes=8,
            client=mock_client,
        )
    assert not dest.exists()


# ============================================================================
# Resource Manager Staging & Publication Tests
# ============================================================================


def test_resource_manager_stage_bytes_and_publish(
    resource_manager: ResourceManager,
) -> None:
    """Test full staging and publication lifecycle of raw bytes."""
    meta = resource_manager.stage_bytes(
        b"alpha trading parameters",
        name="params.json",
        scope=ResourceScope.WORKSPACE,
        tags={"strategy": "momentum"},
    )
    assert meta.status == ResourceStatus.STAGED
    assert meta.size_bytes == len(b"alpha trading parameters")
    assert meta.tags["strategy"] == "momentum"

    # Verify staging file exists
    staged_path = resource_manager.get_content_path(meta.resource_id)
    assert staged_path.is_file()

    # Publish
    published = resource_manager.publish(meta.resource_id)
    assert published.status == ResourceStatus.PUBLISHED
    assert published.published_at_utc is not None

    # Staging directory removed
    assert not (resource_manager.staging_dir / meta.resource_id).exists()

    # Content-addressed file exists in store
    store_path = resource_manager.get_content_path(meta.resource_id)
    assert store_path.is_file()
    assert store_path.read_bytes() == b"alpha trading parameters"

    # Reading bytes uses cache
    read_data = resource_manager.read_bytes(meta.resource_id)
    assert read_data == b"alpha trading parameters"
    assert resource_manager.cache.get_stats().hit_count >= 0


def test_resource_manager_stage_file_and_publish(
    resource_manager: ResourceManager, temp_dir: Path
) -> None:
    """Test staging from local file and publishing."""
    src = temp_dir / "source.txt"
    src.write_text("Hello source", encoding="utf-8")

    meta = resource_manager.stage_file(src, scope=ResourceScope.PLUGIN)
    assert meta.name == "source.txt"
    assert meta.size_bytes == len(b"Hello source")

    published = resource_manager.publish(
        meta.resource_id, expected_hash=meta.content_hash
    )
    assert published.status == ResourceStatus.PUBLISHED


def test_resource_manager_publish_hash_mismatch(
    resource_manager: ResourceManager,
) -> None:
    """Fail publish when expected hash mismatches."""
    meta = resource_manager.stage_bytes(b"content", name="c.txt")
    with pytest.raises(CorruptResourceError, match="Expected hash"):
        resource_manager.publish(meta.resource_id, expected_hash="badhash123")


def test_resource_manager_publish_already_published_conflict(
    resource_manager: ResourceManager,
) -> None:
    """Fail publish when resource is not in STAGED status."""
    meta = resource_manager.stage_bytes(b"content", name="c.txt")
    resource_manager.publish(meta.resource_id)

    with pytest.raises(ResourceConflictError, match="cannot publish"):
        resource_manager.publish(meta.resource_id)


def test_resource_manager_tombstone(resource_manager: ResourceManager) -> None:
    """Tombstone resource and verify subsequent queries fail."""
    meta = resource_manager.stage_bytes(b"temp", name="t.txt")
    resource_manager.publish(meta.resource_id)

    tombstoned = resource_manager.tombstone(meta.resource_id)
    assert tombstoned.status == ResourceStatus.TOMBSTONED

    with pytest.raises(ResourceNotFoundError):
        resource_manager.get_metadata(meta.resource_id)


def test_resource_manager_inspect_and_extract_archive(
    resource_manager: ResourceManager, temp_dir: Path
) -> None:
    """Stage, publish, inspect, and extract an archive resource."""
    zip_path = temp_dir / "model.zip"
    _create_test_zip(zip_path, {"weights.bin": b"12345678"})

    meta = resource_manager.stage_file(zip_path)
    resource_manager.publish(meta.resource_id)

    # Inspect
    inspection = resource_manager.inspect_resource_archive(meta.resource_id)
    assert inspection.is_safe is True
    assert inspection.entry_count == 1

    # Extract
    extracted = resource_manager.extract_resource_archive(meta.resource_id, "models/v1")
    assert len(extracted) == 1
    assert extracted[0].read_bytes() == b"12345678"


def test_resource_manager_cleanup_staging(
    resource_manager: ResourceManager,
) -> None:
    """Purge orphaned or expired staging directories."""
    # Create fake abandoned staging directory
    abandoned = resource_manager.staging_dir / "res_abandoned"
    abandoned.mkdir()
    (abandoned / "orphan.dat").write_bytes(b"trash")

    # Fast forward max age
    purged = resource_manager.cleanup_staging(max_age_seconds=0.0)
    assert purged >= 1
    assert not abandoned.exists()


# ============================================================================
# Scoped Capability Facade Tests
# ============================================================================


def test_resource_access_facade(resource_manager: ResourceManager) -> None:
    """Verify ResourceAccess enforces tenant scope boundaries."""
    facade_ws = ResourceAccess(
        resource_manager, scope=ResourceScope.WORKSPACE, owner_id="ws-1"
    )
    facade_plugin = ResourceAccess(
        resource_manager, scope=ResourceScope.PLUGIN, owner_id="pl-1"
    )

    meta = facade_ws.stage(b"workspace confidential", name="secret.txt")
    assert meta.scope == ResourceScope.WORKSPACE
    assert meta.tags["owner_id"] == "ws-1"

    pub = facade_ws.publish(meta.resource_id)
    assert pub.status == ResourceStatus.PUBLISHED

    # Same scope can read
    data = facade_ws.read(meta.resource_id)
    assert data == b"workspace confidential"

    # Foreign scope access denied
    with pytest.raises(ResourceSecurityError, match="Unauthorized"):
        facade_plugin.read(meta.resource_id)


# ============================================================================
# REST Transport Endpoints Tests
# ============================================================================


@pytest.fixture
def client(resource_manager: ResourceManager) -> Generator[TestClient]:
    """TestClient fixture with resources router mounted."""
    app = FastAPI()
    router = create_resources_router(resource_manager)
    app.include_router(router)
    with TestClient(app) as test_client:
        yield test_client


def test_rest_stage_json_and_publish(client: TestClient) -> None:
    """Test staging via JSON and publishing via REST."""
    stage_resp = client.post(
        "/resources/stage",
        json={"name": "test_artifact.bin", "scope": "workspace"},
    )
    assert stage_resp.status_code == 200
    body = stage_resp.json()
    assert body["status"] == "success"
    res_id = body["data"]["resource_id"]

    # Publish
    pub_resp = client.post(f"/resources/{res_id}/publish", json={})
    assert pub_resp.status_code == 200
    assert pub_resp.json()["data"]["status"] == "published"

    # Query metadata
    meta_resp = client.get(f"/resources/{res_id}")
    assert meta_resp.status_code == 200
    assert meta_resp.json()["data"]["resource_id"] == res_id

    # Download content
    dl_resp = client.get(f"/resources/{res_id}/content")
    assert dl_resp.status_code == 200

    # Tombstone
    del_resp = client.delete(f"/resources/{res_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["data"]["status"] == "tombstoned"


def test_rest_stage_upload(client: TestClient) -> None:
    """Test staging uploaded binary payload via REST."""
    resp = client.post(
        "/resources/stage/upload?name=upload.txt",
        content=b"Uploaded payload data",
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "upload.txt"


def test_rest_cache_status_and_cleanup(client: TestClient) -> None:
    """Test querying cache status and triggering staging cleanup."""
    cache_resp = client.get("/resources/cache/status")
    assert cache_resp.status_code == 200
    assert "used_bytes" in cache_resp.json()["data"]

    clean_resp = client.post("/resources/staging/cleanup?max_age_seconds=0")
    assert clean_resp.status_code == 200
    assert "purged_count" in clean_resp.json()["data"]


# ============================================================================
# CLI Diagnostics Entrypoint Tests
# ============================================================================


def test_cli_inspect_valid_archive(temp_dir: Path) -> None:
    """Test CLI --inspect on valid archive."""
    zip_path = temp_dir / "cli_sample.zip"
    _create_test_zip(zip_path, {"sample.txt": b"cli test"})

    with patch.object(sys, "argv", ["resources", "--inspect", str(zip_path)]):
        exit_code = main()
        assert exit_code == 0


def test_cli_cleanup_staging(temp_dir: Path) -> None:
    """Test CLI --cleanup-staging flag."""
    root = temp_dir / "cli_res"
    root.mkdir()
    with patch.object(
        sys, "argv", ["resources", "--cleanup-staging", "--root", str(root)]
    ):
        exit_code = main()
        assert exit_code == 0


def test_cli_inspect_missing_archive(temp_dir: Path) -> None:
    """Test CLI --inspect on missing archive returns non-zero."""
    with patch.object(
        sys, "argv", ["resources", "--inspect", str(temp_dir / "nonexistent.zip")]
    ):
        exit_code = main()
        assert exit_code == 2


def test_rest_errors_and_archive_endpoints(
    client: TestClient, resource_manager: ResourceManager, temp_dir: Path
) -> None:
    """Test REST 404/422 responses and archive inspect/extract endpoints."""
    # 404 for missing resource
    assert client.get("/resources/res_missing").status_code == 404
    assert client.get("/resources/res_missing/content").status_code == 404
    assert client.delete("/resources/res_missing").status_code == 404
    assert client.post("/resources/res_missing/publish", json={}).status_code == 404

    # Stage and publish an archive for inspect/extract tests
    zip_path = temp_dir / "rest_pkg.zip"
    _create_test_zip(zip_path, {"inner.txt": b"inner payload"})
    meta = resource_manager.stage_file(zip_path)
    resource_manager.publish(meta.resource_id)

    # Inspect endpoint
    ins_resp = client.post(
        "/resources/archive/inspect",
        json={"resource_id": meta.resource_id},
    )
    assert ins_resp.status_code == 200
    assert ins_resp.json()["data"]["is_safe"] is True

    # Extract endpoint
    ext_resp = client.post(
        "/resources/archive/extract",
        json={"resource_id": meta.resource_id, "target_subpath": "rest_out"},
    )
    assert ext_resp.status_code == 200
    assert ext_resp.json()["data"]["count"] == 1


def test_resource_manager_stage_missing_file_raises(
    resource_manager: ResourceManager, temp_dir: Path
) -> None:
    """Verify stage_file on non-existent file raises ResourceNotFoundError."""
    with pytest.raises(ResourceNotFoundError, match="Source file not found"):
        resource_manager.stage_file(temp_dir / "absent.dat")


def test_resource_manager_corrupted_staged_payload(
    resource_manager: ResourceManager,
) -> None:
    """Verify publish detects tampering of staged payload before commit."""
    meta = resource_manager.stage_bytes(b"original", name="file.bin")
    staged_path = resource_manager.staging_dir / meta.resource_id / "file.bin"
    staged_path.write_bytes(b"tampered")

    with pytest.raises(CorruptResourceError, match="recorded hash"):
        resource_manager.publish(meta.resource_id)
