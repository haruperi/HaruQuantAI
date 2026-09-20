"""Tests for immutable artifact catalog feature (FEAT-PERSISTENCE-ARTIFACTS)."""

from __future__ import annotations

import asyncio
import zipfile
from pathlib import Path

import pytest
from app.contracts.persistence import (
    ARTIFACT_STORE,
    ArtifactCorruptError,
    ArtifactIntegrityError,
    ArtifactNotFoundError,
)
from app.kernel.bootstrapper import Runtime
from app.services.persistence.artifacts import (
    ArtifactConfig,
    ArtifactFeature,
    ArtifactServiceImpl,
    feature,
)
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseFeature,
    DatabaseServiceImpl,
)


def test_store_and_read_artifact(tmp_path: Path) -> None:
    """Test storing, reading, and verifying an immutable artifact."""
    db_file = tmp_path / "art_test.db"
    db_service = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    store = ArtifactServiceImpl(
        db_service,
        ArtifactConfig(
            artifacts_dir=tmp_path / "artifacts",
            staging_dir=tmp_path / "staging",
        ),
    )

    payload = b"strategy_code_v1_content_bytes"
    record = store.store_artifact(
        payload=payload,
        media_type="application/octet-stream",
        metadata={"author": "quant_researcher", "tags": ["mean_reversion", "eurusd"]},
    )

    assert record.size_bytes == len(payload)
    assert record.metadata.author == "quant_researcher"
    assert "mean_reversion" in record.metadata.tags

    read_bytes = store.read_artifact_bytes(record.artifact_id)
    assert read_bytes == payload
    assert store.verify_checksum(record.artifact_id) is True

    # Check retrieve
    fetched = store.get_artifact(record.artifact_id)
    assert fetched is not None
    assert fetched.artifact_id == record.artifact_id


def test_staging_promotion_and_lineage(tmp_path: Path) -> None:
    """Test multi-step staging, promotion, and lineage tracking."""
    db_file = tmp_path / "staging_test.db"
    db_service = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    store = ArtifactServiceImpl(
        db_service,
        ArtifactConfig(
            artifacts_dir=tmp_path / "artifacts",
            staging_dir=tmp_path / "staging",
        ),
    )

    parent_rec = store.store_artifact(b"parent_template", "text/plain")

    staging_id = store.stage_artifact(
        payload=b"child_strategy_bytes",
        media_type="application/octet-stream",
    )
    # File in staging exists
    assert (tmp_path / "staging" / f"{staging_id}.bin").exists()

    # Promote with parent lineage
    child_rec = store.promote_artifact(
        staging_id=staging_id,
        parent_ids=[parent_rec.artifact_id],
    )

    # Staging cleaned up
    assert not (tmp_path / "staging" / f"{staging_id}.bin").exists()
    assert child_rec.parent_ids == (parent_rec.artifact_id,)

    lineage = store.get_lineage(child_rec.artifact_id)
    assert lineage == [parent_rec.artifact_id]


def test_lineage_invalid_parent_fails(tmp_path: Path) -> None:
    """Test that promoting with non-existent parent fails closed."""
    db_file = tmp_path / "lineage_fail.db"
    db_service = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    store = ArtifactServiceImpl(
        db_service,
        ArtifactConfig(
            artifacts_dir=tmp_path / "artifacts",
            staging_dir=tmp_path / "staging",
        ),
    )

    staging_id = store.stage_artifact(b"test_payload", "text/plain")
    with pytest.raises(ArtifactIntegrityError, match="does not exist in catalog"):
        store.promote_artifact(staging_id, parent_ids=["non_existent_parent"])


def test_tampered_payload_checksum_fails(tmp_path: Path) -> None:
    """Test checksum verification when file on disk is altered."""
    db_file = tmp_path / "tamper.db"
    db_service = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    art_dir = tmp_path / "artifacts"
    store = ArtifactServiceImpl(
        db_service,
        ArtifactConfig(
            artifacts_dir=art_dir,
            staging_dir=tmp_path / "staging",
        ),
    )

    rec = store.store_artifact(b"clean_bytes", "text/plain")
    assert store.verify_checksum(rec.artifact_id) is True

    # Tamper with file
    (art_dir / f"{rec.artifact_id}.bin").write_bytes(b"tampered_bytes")
    assert store.verify_checksum(rec.artifact_id) is False


def test_export_and_import_bundle(tmp_path: Path) -> None:
    """Test exporting artifacts to a portable .zip bundle and importing them."""
    db1 = tmp_path / "db1.db"
    store1 = ArtifactServiceImpl(
        DatabaseServiceImpl(DatabaseConfig(database_path=db1)),
        ArtifactConfig(
            artifacts_dir=tmp_path / "art1",
            staging_dir=tmp_path / "staging1",
        ),
    )

    rec1 = store1.store_artifact(b"model_weights", "application/octet-stream")
    rec2 = store1.store_artifact(
        b"evaluation_report", "application/json", parent_ids=[rec1.artifact_id]
    )

    bundle_path = tmp_path / "exports" / "package.zip"
    exported = store1.export_bundle([rec1.artifact_id, rec2.artifact_id], bundle_path)
    assert exported.exists()
    assert zipfile.is_zipfile(exported)

    # Import into fresh store
    db2 = tmp_path / "db2.db"
    store2 = ArtifactServiceImpl(
        DatabaseServiceImpl(DatabaseConfig(database_path=db2)),
        ArtifactConfig(
            artifacts_dir=tmp_path / "art2",
            staging_dir=tmp_path / "staging2",
        ),
    )

    imported = store2.import_bundle(exported)
    assert len(imported) == 2
    assert store2.read_artifact_bytes(rec1.artifact_id) == b"model_weights"
    assert store2.read_artifact_bytes(rec2.artifact_id) == b"evaluation_report"
    assert store2.get_lineage(rec2.artifact_id) == [rec1.artifact_id]


def test_import_corrupt_bundle(tmp_path: Path) -> None:
    """Test importing a bundle with corrupted payload raises error."""
    db_file = tmp_path / "corrupt_import.db"
    store = ArtifactServiceImpl(
        DatabaseServiceImpl(DatabaseConfig(database_path=db_file)),
        ArtifactConfig(
            artifacts_dir=tmp_path / "art",
            staging_dir=tmp_path / "staging",
        ),
    )

    rec = store.store_artifact(b"original", "text/plain")
    bundle_path = tmp_path / "tampered.zip"
    store.export_bundle([rec.artifact_id], bundle_path)

    # Tamper payload inside zip
    with zipfile.ZipFile(bundle_path, "r") as zin:
        manifest = zin.read("manifest.json")

    with zipfile.ZipFile(bundle_path, "w") as zout:
        zout.writestr("manifest.json", manifest)
        zout.writestr(f"payloads/{rec.artifact_id}.bin", b"corrupted_content")

    # Import should fail with ArtifactCorruptError
    with pytest.raises(ArtifactCorruptError, match="Corrupted payload"):
        store.import_bundle(bundle_path)


def test_missing_artifact_errors(tmp_path: Path) -> None:
    """Test error handling when requesting non-existent artifacts."""
    db_file = tmp_path / "missing.db"
    store = ArtifactServiceImpl(
        DatabaseServiceImpl(DatabaseConfig(database_path=db_file)),
        ArtifactConfig(
            artifacts_dir=tmp_path / "art",
            staging_dir=tmp_path / "staging",
        ),
    )

    with pytest.raises(ArtifactNotFoundError):
        store.read_artifact_bytes("missing_id")

    with pytest.raises(ArtifactNotFoundError):
        store.verify_checksum("missing_id")

    with pytest.raises(ArtifactNotFoundError):
        store.get_lineage("missing_id")


def test_artifact_feature_lifecycle(tmp_path: Path) -> None:
    """Test runtime composition of ArtifactFeature."""

    async def _test() -> None:
        db_file = tmp_path / "runtime_art.db"
        art_dir = tmp_path / "runtime_artifacts"
        runtime = Runtime(
            [
                lambda: DatabaseFeature(DatabaseConfig(database_path=db_file)),
                lambda: ArtifactFeature(ArtifactConfig(artifacts_dir=art_dir)),
            ]
        )
        async with runtime:
            service = runtime.require(ARTIFACT_STORE)
            rec = service.store_artifact(b"test_runtime_content", "text/plain")
            assert bool(rec.artifact_id)
            assert (
                service.read_artifact_bytes(rec.artifact_id) == b"test_runtime_content"
            )

    asyncio.run(_test())


def test_artifact_factory() -> None:
    """Test zero-argument factory returns ArtifactFeature."""
    f = feature()
    assert isinstance(f, ArtifactFeature)
    assert f.spec.name == "persistence.artifacts"


def test_store_artifact_idempotent_by_content_identity(tmp_path: Path) -> None:
    """Test that storing identical payload content multiple times is idempotent."""
    db_file = tmp_path / "idempotent.db"
    db_service = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    store = ArtifactServiceImpl(
        db_service,
        ArtifactConfig(
            artifacts_dir=tmp_path / "artifacts",
            staging_dir=tmp_path / "staging",
        ),
    )

    payload = b"deterministic strategy source code payload"
    # First store
    rec1 = store.store_artifact(payload, "text/plain")
    # Second store with same content
    rec2 = store.store_artifact(payload, "text/plain")

    assert rec1.artifact_id == rec2.artifact_id
    assert rec1.sha256_hash == rec2.sha256_hash

    # Assert exactly 1 row exists in database catalog
    count_rows = db_service.execute_query(
        "SELECT count(*) as cnt FROM persistence_artifacts WHERE artifact_id = ?;",
        (rec1.artifact_id,),
    )
    assert count_rows[0]["cnt"] == 1

    # Assert content is readable and matches
    assert store.read_artifact_bytes(rec1.artifact_id) == payload


def test_promote_explicit_id_conflict_fails_closed(tmp_path: Path) -> None:
    """Test that explicit artifact_id collision with differing payload fails closed."""
    db_file = tmp_path / "conflict.db"
    store = ArtifactServiceImpl(
        DatabaseServiceImpl(DatabaseConfig(database_path=db_file)),
        ArtifactConfig(
            artifacts_dir=tmp_path / "artifacts",
            staging_dir=tmp_path / "staging",
        ),
    )

    explicit_id = "custom_strategy_v1"
    stage1 = store.stage_artifact(b"content_alpha", "text/plain")
    store.promote_artifact(stage1, artifact_id=explicit_id)

    stage2 = store.stage_artifact(b"different_content_beta", "text/plain")
    with pytest.raises(ArtifactIntegrityError, match="Explicit artifact ID collision"):
        store.promote_artifact(stage2, artifact_id=explicit_id)
