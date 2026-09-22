"""Host artifacts owner: content-addressed storage with SHA-256 and quotas."""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import threading
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, override

from app.host.storage import HOST_STORAGE, Storage, StorageDelete, StorageMutation
from app.kernel.capability import Capability
from app.kernel.context import FeatureContext
from app.kernel.feature import FeatureSpec

_SHA256_HEX_LENGTH = 64


class ArtifactError(RuntimeError):
    """Base error for artifact storage failures."""


class ArtifactNotFoundError(ArtifactError):
    """Raised when an artifact digest is not found."""


class ArtifactQuotaExceededError(ArtifactError):
    """Raised when artifact size exceeds individual or total quota."""


class ArtifactPathEscapeError(ArtifactError):
    """Raised when an artifact digest results in a path escape attempt."""


class ArtifactCorruptionError(ArtifactError):
    """Raised when stored artifact content does not match its expected digest."""


@dataclass(frozen=True, slots=True)
class ArtifactRef:
    """Immutable reference to a content-addressed artifact."""

    digest: str
    size_bytes: int

    def __post_init__(self) -> None:
        """Validate artifact reference."""
        if not isinstance(self.digest, str) or len(self.digest) != _SHA256_HEX_LENGTH:
            raise ValueError("digest must be a 64-character hex string")
        int(self.digest, 16)  # Validate hex format
        if self.size_bytes < 0:
            raise ValueError("size_bytes must be >= 0")


@dataclass(frozen=True, slots=True)
class ArtifactMetadata:
    """Lineage and media metadata for an artifact."""

    ref: ArtifactRef
    media_type: str
    schema_version: int = 1
    created_at_utc: str = ""
    provenance_hash: str = ""
    retention_policy: str = "standard"
    tags: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        """Validate metadata fields."""
        if not isinstance(self.ref, ArtifactRef):
            raise TypeError("ref must be an ArtifactRef")
        if not self.media_type or not isinstance(self.media_type, str):
            raise ValueError("media_type must be a non-empty string")
        if self.schema_version < 1:
            raise ValueError("schema_version must be >= 1")


@dataclass(frozen=True, slots=True)
class ArtifactPutResult:
    """Outcome of storing an artifact."""

    ref: ArtifactRef
    metadata: ArtifactMetadata
    deduplicated: bool


@dataclass(frozen=True, slots=True)
class ArtifactsConfig:
    """Configuration for filesystem artifact store."""

    root_dir: Path | str
    max_artifact_bytes: int = 50_000_000  # 50 MB
    max_total_bytes: int = 1_000_000_000  # 1 GB

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.max_artifact_bytes <= 0:
            raise ValueError("max_artifact_bytes must be > 0")
        if self.max_total_bytes <= 0:
            raise ValueError("max_total_bytes must be > 0")


class ArtifactStore(Protocol):
    """Public capability protocol for content-addressed artifact storage."""

    def put_artifact(
        self,
        data: bytes,
        *,
        media_type: str = "application/octet-stream",
        provenance_hash: str = "",
        tags: Sequence[tuple[str, str]] = (),
    ) -> ArtifactPutResult:
        """Store bytes content-addressed by SHA-256 and return reference."""
        ...

    def get_artifact_bytes(self, digest: str) -> bytes:
        """Read and verify artifact bytes by SHA-256 digest."""
        ...

    def get_metadata(self, digest: str) -> ArtifactMetadata | None:
        """Fetch metadata for an artifact by digest."""
        ...

    def delete_artifact(self, digest: str) -> bool:
        """Delete an artifact and its metadata if present."""
        ...

    def has_artifact(self, digest: str) -> bool:
        """Return whether an artifact exists in the store."""
        ...


HOST_ARTIFACTS = Capability[ArtifactStore]("host.artifacts", 1)

ARTIFACTS_NAMESPACE = "artifacts"


def _utc_now_iso() -> str:
    """Return current UTC timestamp formatted as ISO-8601 string."""
    return (
        datetime.datetime.now(datetime.UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


class _FilesystemArtifactStore(ArtifactStore):
    """Filesystem-backed content-addressed artifact store with metadata in Storage."""

    def __init__(self, config: ArtifactsConfig, storage: Storage) -> None:
        """Initialize artifact store."""
        self._config = config
        self._storage = storage
        self._root_dir = Path(config.root_dir).resolve()
        self._objects_dir = self._root_dir / "objects"
        self._tmp_dir = self._root_dir / ".tmp"
        self._lock = threading.RLock()

        self._objects_dir.mkdir(parents=True, exist_ok=True)
        self._tmp_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_target_path(self, digest: str) -> Path:
        """Resolve sharded digest path and verify no path escape."""
        clean_digest = digest.strip().lower()
        if len(clean_digest) != _SHA256_HEX_LENGTH:
            raise ValueError("Digest must be 64 characters")
        int(clean_digest, 16)  # Validate hex format

        shard = clean_digest[:2]
        filename = clean_digest[2:]
        target = (self._objects_dir / shard / filename).resolve()

        # Strict containment check
        try:
            target.relative_to(self._objects_dir)
        except ValueError as err:
            raise ArtifactPathEscapeError(
                f"Path escape detected for digest {clean_digest}"
            ) from err

        return target

    def _compute_total_bytes(self) -> int:
        """Calculate total storage size of all stored objects."""
        total = 0
        for entry in self._objects_dir.rglob("*"):
            if entry.is_file():
                total += entry.stat().st_size
        return total

    @override
    def put_artifact(
        self,
        data: bytes,
        *,
        media_type: str = "application/octet-stream",
        provenance_hash: str = "",
        tags: Sequence[tuple[str, str]] = (),
    ) -> ArtifactPutResult:
        """Store bytes atomically beneath root and record metadata."""
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")

        size = len(data)
        if size > self._config.max_artifact_bytes:
            raise ArtifactQuotaExceededError(
                f"Artifact size {size} exceeds max allowed "
                f"{self._config.max_artifact_bytes}"
            )

        digest = hashlib.sha256(data).hexdigest()
        ref = ArtifactRef(digest=digest, size_bytes=size)
        target_path = self._resolve_target_path(digest)

        with self._lock:
            # Check total quota if writing new content
            if not target_path.exists():
                current_total = self._compute_total_bytes()
                if current_total + size > self._config.max_total_bytes:
                    raise ArtifactQuotaExceededError(
                        f"Total storage quota {self._config.max_total_bytes} exceeded"
                    )

            now_iso = _utc_now_iso()
            metadata = ArtifactMetadata(
                ref=ref,
                media_type=media_type,
                schema_version=1,
                created_at_utc=now_iso,
                provenance_hash=provenance_hash,
                retention_policy="standard",
                tags=tuple(tags),
            )

            # Check if file and metadata already exist (deduplication)
            if target_path.exists():
                existing_meta = self.get_metadata(digest)
                if existing_meta is not None:
                    return ArtifactPutResult(
                        ref=ref, metadata=existing_meta, deduplicated=True
                    )

            # Atomic file write: write to temp, fsync, move
            temp_path = self._tmp_dir / f"{uuid.uuid4().hex}.tmp"
            try:
                with Path(temp_path).open("wb") as f:
                    f.write(data)
                    f.flush()
                    os.fsync(f.fileno())

                target_path.parent.mkdir(parents=True, exist_ok=True)
                Path(str(temp_path)).replace(str(target_path))
            except Exception:
                if temp_path.exists():
                    temp_path.unlink(missing_ok=True)
                raise

            # Record metadata in Storage
            meta_json = {
                "digest": digest,
                "size_bytes": size,
                "media_type": media_type,
                "schema_version": 1,
                "created_at_utc": now_iso,
                "provenance_hash": provenance_hash,
                "retention_policy": "standard",
                "tags": list(tags),
            }
            payload_bytes = json.dumps(
                meta_json, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")

            mutation = StorageMutation(
                namespace=ARTIFACTS_NAMESPACE,
                key=digest,
                schema_version=1,
                payload_bytes=payload_bytes,
            )
            tx_res = self._storage.commit_transaction([mutation])
            if not tx_res.committed:
                # Cleanup newly written file if metadata commit failed
                target_path.unlink(missing_ok=True)
                raise ArtifactError(
                    f"Failed to record artifact metadata in storage for {digest}"
                )

            return ArtifactPutResult(ref=ref, metadata=metadata, deduplicated=False)

    @override
    def get_artifact_bytes(self, digest: str) -> bytes:
        """Retrieve artifact bytes and verify SHA-256 digest."""
        target_path = self._resolve_target_path(digest)
        with self._lock:
            if not target_path.exists():
                raise ArtifactNotFoundError(f"Artifact {digest} not found")

            data = target_path.read_bytes()
            computed = hashlib.sha256(data).hexdigest()
            if computed != digest.lower():
                raise ArtifactCorruptionError(
                    f"Artifact content hash {computed} does not match expected {digest}"
                )
            return data

    @override
    def get_metadata(self, digest: str) -> ArtifactMetadata | None:
        """Fetch metadata for an artifact from Storage."""
        clean_digest = digest.strip().lower()
        rec = self._storage.get_record(ARTIFACTS_NAMESPACE, clean_digest)
        if rec is None:
            return None
        parsed = json.loads(rec.payload_bytes.decode("utf-8"))
        tags_raw = parsed.get("tags", [])
        return ArtifactMetadata(
            ref=ArtifactRef(
                digest=parsed["digest"],
                size_bytes=parsed["size_bytes"],
            ),
            media_type=parsed["media_type"],
            schema_version=parsed.get("schema_version", 1),
            created_at_utc=parsed.get("created_at_utc", ""),
            provenance_hash=parsed.get("provenance_hash", ""),
            retention_policy=parsed.get("retention_policy", "standard"),
            tags=tuple((t[0], t[1]) for t in tags_raw),
        )

    @override
    def delete_artifact(self, digest: str) -> bool:
        """Delete an artifact and its metadata."""
        target_path = self._resolve_target_path(digest)
        with self._lock:
            rec = self._storage.get_record(ARTIFACTS_NAMESPACE, digest.lower())
            if rec is None and not target_path.exists():
                return False

            # Delete metadata first
            if rec is not None:
                self._storage.commit_transaction(
                    [
                        StorageDelete(
                            namespace=ARTIFACTS_NAMESPACE,
                            key=digest.lower(),
                            expected_revision=rec.revision,
                        )
                    ]
                )

            # Unlink file
            if target_path.exists():
                target_path.unlink()
            return True

    @override
    def has_artifact(self, digest: str) -> bool:
        """Return True if the artifact file and metadata exist."""
        try:
            target_path = self._resolve_target_path(digest)
        except ValueError:
            return False
        with self._lock:
            return target_path.exists() and (self.get_metadata(digest) is not None)


class _ArtifactsFeature:
    """Feature providing HOST_ARTIFACTS requiring HOST_STORAGE."""

    spec = FeatureSpec(
        "host.artifacts",
        provides=frozenset({HOST_ARTIFACTS}),
        requires=frozenset({HOST_STORAGE}),
        description="Content-addressed artifact store with SHA-256 and quotas",
    )

    def __init__(self, config: ArtifactsConfig) -> None:
        self._config = config
        self._service: _FilesystemArtifactStore | None = None

    async def start(self, context: FeatureContext) -> None:
        storage = context.require(HOST_STORAGE)
        self._service = _FilesystemArtifactStore(self._config, storage)
        context.provide(HOST_ARTIFACTS, self._service)


def _artifacts_feature(config: ArtifactsConfig) -> _ArtifactsFeature:
    """Construct the artifacts owner for the host composition root only."""
    return _ArtifactsFeature(config)


__all__ = (
    "ARTIFACTS_NAMESPACE",
    "HOST_ARTIFACTS",
    "ArtifactCorruptionError",
    "ArtifactError",
    "ArtifactMetadata",
    "ArtifactNotFoundError",
    "ArtifactPathEscapeError",
    "ArtifactPutResult",
    "ArtifactQuotaExceededError",
    "ArtifactRef",
    "ArtifactStore",
    "ArtifactsConfig",
    "_artifacts_feature",
)
