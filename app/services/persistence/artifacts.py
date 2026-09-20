"""Immutable content-addressed artifact catalog and packaging.

Feature:
    FEAT-PERSISTENCE-ARTIFACTS

Purpose:
    Provides immutable content-addressed artifact staging, promotion, retrieval,
    SHA-256 verification, lineage DAG tracking, and portable package bundling (.zip).
    Corresponds to StrategyQuant X strategy artifact and template storage.

Invariants:
    * Artifacts are immutable once promoted.
    * Staged artifacts are isolated until explicitly promoted.
    * Lineage parent references must exist in the catalog prior to promotion.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, override

from app.contracts.persistence import (
    ARTIFACT_STORE,
    DATABASE_SERVICE,
    ArtifactCorruptError,
    ArtifactIntegrityError,
    ArtifactMetadata,
    ArtifactNotFoundError,
    ArtifactRecord,
    DatabaseService,
)
from app.contracts.persistence import (
    ArtifactStore as IArtifactStore,
)
from app.kernel.context import FeatureContext
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger
from app.services.persistence.persistence import PersistenceDatabaseManager

logger = get_logger(__name__)


def _compute_sha256(payload: bytes) -> str:
    """Compute SHA-256 hex digest for given payload bytes.

    Args:
        payload: Raw binary content.

    Returns:
        Hex-encoded SHA-256 hash.
    """
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class ArtifactConfig:
    """Configuration for artifact and staging storage directories.

    Attributes:
        artifacts_dir: Directory for permanently promoted immutable artifacts.
        staging_dir: Directory for transient staging artifacts.
    """

    artifacts_dir: Path = Path("data/artifacts")
    staging_dir: Path = Path("data/staging")


class ArtifactServiceImpl(IArtifactStore):
    """Concrete implementation of ArtifactStore."""

    def __init__(
        self,
        db_service: DatabaseService,
        config: ArtifactConfig | None = None,
    ) -> None:
        """Initialize artifact service with database and directory config.

        Args:
            db_service: Database service provider.
            config: Optional artifact directory configuration.
        """
        self._db_service = db_service
        self._config = config or ArtifactConfig()
        self._config.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self._config.staging_dir.mkdir(parents=True, exist_ok=True)
        self._manager = PersistenceDatabaseManager(db_service.database_path)

    def _get_artifact_file_path(self, artifact_id: str) -> Path:
        """Return the filesystem path for a promoted artifact payload."""
        return self._config.artifacts_dir / f"{artifact_id}.bin"

    @override
    def stage_artifact(
        self,
        payload: bytes,
        media_type: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> str:
        """Stage an artifact payload in isolation and return staging token.

        Args:
            payload: Binary content to stage.
            media_type: MIME media type.
            metadata: Optional user-defined metadata dictionary.

        Returns:
            Unique staging token identifier.
        """
        staging_id = f"stage_{uuid.uuid4().hex}"
        bin_path = self._config.staging_dir / f"{staging_id}.bin"
        meta_path = self._config.staging_dir / f"{staging_id}.json"

        bin_path.write_bytes(payload)
        staged_metadata: dict[str, Any] = dict(metadata) if metadata else {}
        meta_dict: dict[str, Any] = {
            "media_type": media_type,
            "metadata": staged_metadata,
            "staged_at_utc": datetime.now(UTC).isoformat(),
        }
        meta_path.write_text(json.dumps(meta_dict), encoding="utf-8")

        logger.info(
            "artifact_staged",
            staging_id=staging_id,
            size_bytes=len(payload),
            media_type=media_type,
        )
        return staging_id

    @override
    def promote_artifact(
        self,
        staging_id: str,
        artifact_id: str | None = None,
        parent_ids: Sequence[str] = (),
    ) -> ArtifactRecord:
        """Validate, hash, promote, and catalog a staged artifact atomically.

        Args:
            staging_id: Staging token identifier.
            artifact_id: Optional explicit artifact ID. If omitted, SHA-256 is used.
            parent_ids: Sequence of parent artifact IDs for lineage tracking.

        Returns:
            Promoted ArtifactRecord catalog entry.

        Raises:
            ArtifactNotFoundError: If staging files do not exist.
            ArtifactIntegrityError: If parent artifacts are missing.
        """
        bin_path = self._config.staging_dir / f"{staging_id}.bin"
        meta_path = self._config.staging_dir / f"{staging_id}.json"

        if not bin_path.is_file() or not meta_path.is_file():
            msg = f"Staged artifact {staging_id} not found in staging area"
            raise ArtifactNotFoundError(msg)

        payload = bin_path.read_bytes()
        meta_raw = json.loads(meta_path.read_text(encoding="utf-8"))
        media_type = str(meta_raw.get("media_type", "application/octet-stream"))
        custom_meta = meta_raw.get("metadata", {})

        sha256_hash = _compute_sha256(payload)
        effective_id = artifact_id or sha256_hash

        # Fail-closed identity guard:
        # If explicit artifact_id already exists with different hash
        existing = self._manager.get_artifact(effective_id)
        if existing is not None and existing.sha256_hash != sha256_hash:
            msg = (
                f"Explicit artifact ID collision: {effective_id} already exists "
                f"with hash {existing.sha256_hash}, "
                f"but new payload has hash {sha256_hash}"
            )
            raise ArtifactIntegrityError(msg)

        # Verify parent artifacts exist
        for parent_id in parent_ids:
            if self._manager.get_artifact(parent_id) is None:
                msg = f"Parent artifact {parent_id} does not exist in catalog"
                raise ArtifactIntegrityError(msg)

        # Move staged binary payload into permanent artifacts storage
        target_path = self._get_artifact_file_path(effective_id)
        target_path.write_bytes(payload)

        # Cleanup staging files
        bin_path.unlink(missing_ok=True)
        meta_path.unlink(missing_ok=True)

        meta_obj = ArtifactMetadata(
            media_type=media_type,
            description=str(custom_meta.get("description", "")),
            author=str(custom_meta.get("author", "system")),
            tags=tuple(custom_meta.get("tags", ())),
            custom=custom_meta.get("custom", {}),
        )

        try:
            record = self._manager.insert_artifact(
                effective_id,
                sha256_hash,
                media_type,
                size_bytes=len(payload),
                metadata=meta_obj,
                created_at_utc=datetime.now(UTC),
                parent_ids=parent_ids,
            )
        except sqlite3.IntegrityError as exc:
            msg = (
                f"Database integrity violation while inserting artifact "
                f"{effective_id}: {exc}"
            )
            raise ArtifactIntegrityError(msg) from exc
        logger.info(
            "artifact_promoted",
            artifact_id=effective_id,
            sha256=sha256_hash,
            size_bytes=len(payload),
        )
        return record

    @override
    def store_artifact(
        self,
        payload: bytes,
        media_type: str,
        metadata: Mapping[str, Any] | None = None,
        parent_ids: Sequence[str] = (),
    ) -> ArtifactRecord:
        """Stage and promote an artifact atomically in a single operation.

        Args:
            payload: Binary payload content.
            media_type: MIME media type.
            metadata: Optional metadata dictionary.
            parent_ids: Sequence of parent artifact IDs.

        Returns:
            Promoted ArtifactRecord.
        """
        staging_id = self.stage_artifact(payload, media_type, metadata)
        return self.promote_artifact(staging_id, parent_ids=parent_ids)

    @override
    def get_artifact(self, artifact_id: str) -> ArtifactRecord | None:
        """Retrieve artifact receipt and metadata by unique ID.

        Args:
            artifact_id: Unique artifact ID.

        Returns:
            ArtifactRecord if found, None otherwise.
        """
        return self._manager.get_artifact(artifact_id)

    @override
    def read_artifact_bytes(self, artifact_id: str) -> bytes:
        """Read the raw immutable content bytes of an artifact.

        Args:
            artifact_id: Unique artifact ID.

        Returns:
            Raw bytes of artifact content.

        Raises:
            ArtifactNotFoundError: If artifact or payload file is missing.
        """
        record = self.get_artifact(artifact_id)
        if record is None:
            msg = f"Artifact {artifact_id} not found in catalog"
            raise ArtifactNotFoundError(msg)

        file_path = self._get_artifact_file_path(artifact_id)
        if not file_path.is_file():
            msg = f"Payload file for artifact {artifact_id} missing at {file_path}"
            raise ArtifactNotFoundError(msg)

        return file_path.read_bytes()

    @override
    def verify_checksum(self, artifact_id: str) -> bool:
        """Verify that stored file content matches its cataloged SHA-256 hash.

        Args:
            artifact_id: Unique artifact ID.

        Returns:
            True if content matches recorded hash, False otherwise.

        Raises:
            ArtifactNotFoundError: If artifact does not exist.
        """
        record = self.get_artifact(artifact_id)
        if record is None:
            msg = f"Artifact {artifact_id} not found in catalog"
            raise ArtifactNotFoundError(msg)

        file_path = self._get_artifact_file_path(artifact_id)
        if not file_path.is_file():
            return False

        payload = file_path.read_bytes()
        computed = _compute_sha256(payload)
        return computed == record.sha256_hash

    @override
    def get_lineage(self, artifact_id: str) -> list[str]:
        """Return list of parent artifact IDs.

        Args:
            artifact_id: Unique artifact ID.

        Returns:
            List of parent artifact IDs.

        Raises:
            ArtifactNotFoundError: If artifact does not exist.
        """
        record = self.get_artifact(artifact_id)
        if record is None:
            msg = f"Artifact {artifact_id} not found in catalog"
            raise ArtifactNotFoundError(msg)
        return self._manager.get_artifact_parents(artifact_id)

    @override
    def export_bundle(self, artifact_ids: Sequence[str], target_path: Path) -> Path:
        """Export artifacts and manifest into a portable .zip package bundle.

        Args:
            artifact_ids: Sequence of artifact IDs to bundle.
            target_path: Destination path for .zip bundle file.

        Returns:
            Target bundle Path.

        Raises:
            ArtifactNotFoundError: If any requested artifact is missing.
        """
        if not artifact_ids:
            msg = "Cannot export empty artifact bundle"
            raise ArtifactIntegrityError(msg)

        records: list[ArtifactRecord] = []
        for aid in artifact_ids:
            rec = self.get_artifact(aid)
            if rec is None:
                msg = f"Artifact {aid} not found in catalog for export"
                raise ArtifactNotFoundError(msg)
            records.append(rec)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_data = {
            "bundle_version": 1,
            "created_at_utc": datetime.now(UTC).isoformat(),
            "root_artifact_id": artifact_ids[0],
            "artifacts": [
                {
                    "artifact_id": r.artifact_id,
                    "sha256_hash": r.sha256_hash,
                    "media_type": r.media_type,
                    "size_bytes": r.size_bytes,
                    "created_at_utc": r.created_at_utc.isoformat(),
                    "metadata": {
                        "media_type": r.metadata.media_type,
                        "description": r.metadata.description,
                        "author": r.metadata.author,
                        "tags": list(r.metadata.tags),
                        "custom": dict(r.metadata.custom),
                    },
                    "parent_ids": list(r.parent_ids),
                }
                for r in records
            ],
        }

        with zipfile.ZipFile(target_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                "manifest.json",
                json.dumps(manifest_data, indent=2),
            )
            for rec in records:
                content = self.read_artifact_bytes(rec.artifact_id)
                zf.writestr(f"payloads/{rec.artifact_id}.bin", content)

        logger.info(
            "artifact_bundle_exported",
            target_path=str(target_path),
            count=len(records),
        )
        return target_path

    @override
    def import_bundle(self, bundle_path: Path) -> list[ArtifactRecord]:
        """Import, verify, and catalog artifacts from a portable package bundle.

        Args:
            bundle_path: Path to .zip bundle file.

        Returns:
            List of successfully imported ArtifactRecord objects.

        Raises:
            ArtifactIntegrityError: If bundle file or manifest is invalid.
            ArtifactCorruptError: If payload fails checksum verification.
        """
        if not bundle_path.is_file():
            msg = f"Bundle file {bundle_path} does not exist"
            raise ArtifactIntegrityError(msg)

        try:
            with zipfile.ZipFile(bundle_path, "r") as zf:
                manifest_text = zf.read("manifest.json").decode("utf-8")
                manifest_data = json.loads(manifest_text)
                imported_records: list[ArtifactRecord] = []

                for item in manifest_data.get("artifacts", []):
                    aid = str(item["artifact_id"])
                    expected_hash = str(item["sha256_hash"])
                    media_type = str(item.get("media_type", "application/octet-stream"))
                    payload_entry = f"payloads/{aid}.bin"
                    payload = zf.read(payload_entry)

                    actual_hash = _compute_sha256(payload)
                    if actual_hash != expected_hash:
                        msg = (
                            f"Corrupted payload for artifact {aid} in bundle: "
                            f"expected {expected_hash}, got {actual_hash}"
                        )
                        raise ArtifactCorruptError(msg)

                    meta_dict = item.get("metadata", {})
                    meta_obj = ArtifactMetadata(
                        media_type=meta_dict.get("media_type", media_type),
                        description=meta_dict.get("description", ""),
                        author=meta_dict.get("author", "system"),
                        tags=tuple(meta_dict.get("tags", ())),
                        custom=meta_dict.get("custom", {}),
                    )

                    # Save binary payload
                    target_file = self._get_artifact_file_path(aid)
                    target_file.write_bytes(payload)

                    # Catalog in database if not present
                    existing = self.get_artifact(aid)
                    if existing is None:
                        created_dt = datetime.fromisoformat(item["created_at_utc"])
                        parents = tuple(item.get("parent_ids", ()))
                        rec = self._manager.insert_artifact(
                            aid,
                            expected_hash,
                            media_type,
                            size_bytes=len(payload),
                            metadata=meta_obj,
                            created_at_utc=created_dt,
                            parent_ids=parents,
                        )
                        imported_records.append(rec)
                    else:
                        imported_records.append(existing)

                logger.info(
                    "artifact_bundle_imported",
                    bundle=str(bundle_path),
                    count=len(imported_records),
                )
                return imported_records
        except zipfile.BadZipFile as exc:
            msg = f"Invalid zip bundle at {bundle_path}: {exc}"
            raise ArtifactIntegrityError(msg) from exc


SPEC: FeatureSpec = FeatureSpec(
    name="persistence.artifacts",
    provides=frozenset({ARTIFACT_STORE}),
    requires=frozenset({DATABASE_SERVICE}),
    optional=frozenset(),
    description="Content-addressed immutable artifact catalog, staging, and bundles.",
)


class ArtifactFeature:
    """Wire immutable artifact store into kernel composition lifecycle."""

    def __init__(self, config: ArtifactConfig | None = None) -> None:
        """Initialize feature with optional configuration.

        Args:
            config: Optional artifact store configuration.
        """
        self._config = config or ArtifactConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Resolve database capability and register artifact store.

        Args:
            context: Kernel feature context.
        """
        db_service = context.require(DATABASE_SERVICE)
        service = ArtifactServiceImpl(db_service, self._config)
        context.provide(ARTIFACT_STORE, service)
        logger.info(
            "persistence_artifacts_feature_started",
            artifacts_dir=str(self._config.artifacts_dir),
        )


def feature() -> ArtifactFeature:
    """Return a zero-argument factory instance of ArtifactFeature."""
    return ArtifactFeature()
