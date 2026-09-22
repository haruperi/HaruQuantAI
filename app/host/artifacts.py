"""Host artifacts owner: content-addressed storage with SHA-256 and quotas."""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import threading
import uuid
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol, override

from app.host.storage import (
    HOST_STORAGE,
    Storage,
    StorageDelete,
    StorageMutation,
    StorageRecord,
)
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


class ArtifactInUseError(ArtifactError):
    """Raised when deletion is refused because active references remain."""


class ArtifactCancelledError(ArtifactError):
    """Raised when a streaming artifact write is cancelled by the caller."""


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
    source_fingerprint: str = ""
    dependency_fingerprint: str = ""
    data_fingerprint: str = ""
    lineage: tuple[str, ...] = ()
    refcount: int = 0

    def __post_init__(self) -> None:
        """Validate metadata fields."""
        if not isinstance(self.ref, ArtifactRef):
            raise TypeError("ref must be an ArtifactRef")
        if not self.media_type or not isinstance(self.media_type, str):
            raise ValueError("media_type must be a non-empty string")
        if self.schema_version < 1:
            raise ValueError("schema_version must be >= 1")
        if self.refcount < 0:
            raise ValueError("refcount must be >= 0")


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
        source_fingerprint: str = "",
        dependency_fingerprint: str = "",
        data_fingerprint: str = "",
        lineage: Sequence[str] = (),
    ) -> ArtifactPutResult:
        """Store bytes content-addressed by SHA-256 and return reference."""
        ...

    def put_artifact_stream(
        self,
        chunks: Iterable[bytes],
        *,
        media_type: str = "application/octet-stream",
        provenance_hash: str = "",
        tags: Sequence[tuple[str, str]] = (),
        source_fingerprint: str = "",
        dependency_fingerprint: str = "",
        data_fingerprint: str = "",
        lineage: Sequence[str] = (),
        should_cancel: Callable[[], bool] | None = None,
    ) -> ArtifactPutResult:
        """Stream chunks into content-addressed storage, hashing while writing.

        The caller cancellation callback is checked before each chunk; a
        cancelled stream removes its temporary file and raises
        ArtifactCancelledError without publishing partial content.
        """
        ...

    def get_artifact_bytes(self, digest: str) -> bytes:
        """Read and verify artifact bytes by SHA-256 digest and size."""
        ...

    def get_metadata(self, digest: str) -> ArtifactMetadata | None:
        """Fetch metadata for an artifact by digest."""
        ...

    def request_deletion(self, digest: str) -> bool:
        """Mark an artifact's metadata for retention review (phase one)."""
        ...

    def acquire_reference(self, digest: str) -> None:
        """Increment the artifact's active reference count."""
        ...

    def release_reference(self, digest: str) -> None:
        """Decrement the artifact's active reference count."""
        ...

    def delete_artifact(self, digest: str) -> bool:
        """Delete a marked, unreferenced artifact and its metadata."""
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


@dataclass(frozen=True, slots=True)
class _PutContext:
    """Bundle of caller-provided metadata for one artifact publication."""

    media_type: str = "application/octet-stream"
    provenance_hash: str = ""
    tags: tuple[tuple[str, str], ...] = ()
    source_fingerprint: str = ""
    dependency_fingerprint: str = ""
    data_fingerprint: str = ""
    lineage: tuple[str, ...] = ()


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

    def _write_stream_to_temp(
        self,
        chunks: Iterable[bytes],
        should_cancel: Callable[[], bool] | None,
    ) -> tuple[str, int, Path]:
        """Stream chunks into a temp file, hashing while writing.

        Enforces the per-artifact quota mid-stream and honors caller
        cancellation before each chunk. Returns (digest, size, temp_path).
        """
        hasher = hashlib.sha256()
        total = 0
        temp_path = self._tmp_dir / f"{uuid.uuid4().hex}.tmp"

        def accept_chunk(chunk: object, running_total: int) -> int:
            if should_cancel is not None and should_cancel():
                raise ArtifactCancelledError(
                    "Streaming artifact write cancelled by caller"
                )
            if not isinstance(chunk, (bytes, bytearray, memoryview)):
                raise TypeError("chunks must yield bytes")
            new_total = running_total + len(chunk)
            if new_total > self._config.max_artifact_bytes:
                raise ArtifactQuotaExceededError(
                    f"Artifact size exceeded {self._config.max_artifact_bytes} "
                    "bytes mid-stream"
                )
            return new_total

        try:
            with temp_path.open("wb") as f:
                for chunk in chunks:
                    total = accept_chunk(chunk, total)
                    hasher.update(chunk)
                    f.write(chunk)
                f.flush()
                os.fsync(f.fileno())
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise
        return hasher.hexdigest(), total, temp_path

    def _publish(
        self, digest: str, size: int, temp_path: Path, context: _PutContext
    ) -> ArtifactPutResult:
        """Atomically publish temp content and commit metadata via Storage."""
        ref = ArtifactRef(digest=digest, size_bytes=size)
        target_path = self._resolve_target_path(digest)

        with self._lock:
            if not target_path.exists():
                current_total = self._compute_total_bytes()
                if current_total + size > self._config.max_total_bytes:
                    temp_path.unlink(missing_ok=True)
                    raise ArtifactQuotaExceededError(
                        f"Total storage quota {self._config.max_total_bytes} exceeded"
                    )

            now_iso = _utc_now_iso()
            metadata = ArtifactMetadata(
                ref=ref,
                media_type=context.media_type,
                schema_version=1,
                created_at_utc=now_iso,
                provenance_hash=context.provenance_hash,
                retention_policy="standard",
                tags=tuple(context.tags),
                source_fingerprint=context.source_fingerprint,
                dependency_fingerprint=context.dependency_fingerprint,
                data_fingerprint=context.data_fingerprint,
                lineage=tuple(context.lineage),
                refcount=0,
            )

            # Deduplicate identical content without mutating existing files.
            if target_path.exists():
                existing_meta = self.get_metadata(digest)
                if existing_meta is not None:
                    temp_path.unlink(missing_ok=True)
                    return ArtifactPutResult(
                        ref=ref, metadata=existing_meta, deduplicated=True
                    )

            target_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                temp_path.replace(str(target_path))
            except Exception:
                # remove only the unreferenced new content owned by this op
                if not target_path.exists():
                    temp_path.unlink(missing_ok=True)
                raise

            meta_json = {
                "digest": digest,
                "size_bytes": size,
                "media_type": context.media_type,
                "schema_version": 1,
                "created_at_utc": now_iso,
                "provenance_hash": context.provenance_hash,
                "retention_policy": "standard",
                "tags": list(context.tags),
                "source_fingerprint": context.source_fingerprint,
                "dependency_fingerprint": context.dependency_fingerprint,
                "data_fingerprint": context.data_fingerprint,
                "lineage": list(context.lineage),
                "refcount": 0,
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
                # Commit metadata first failed: remove only the newly
                # published content owned by this operation.
                target_path.unlink(missing_ok=True)
                raise ArtifactError(
                    f"Failed to record artifact metadata in storage for {digest}"
                )

            return ArtifactPutResult(ref=ref, metadata=metadata, deduplicated=False)

    @override
    def put_artifact(
        self,
        data: bytes,
        *,
        media_type: str = "application/octet-stream",
        provenance_hash: str = "",
        tags: Sequence[tuple[str, str]] = (),
        source_fingerprint: str = "",
        dependency_fingerprint: str = "",
        data_fingerprint: str = "",
        lineage: Sequence[str] = (),
    ) -> ArtifactPutResult:
        """Store bytes atomically beneath root and record metadata."""
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        if len(data) > self._config.max_artifact_bytes:
            raise ArtifactQuotaExceededError(
                f"Artifact size {len(data)} exceeds max allowed "
                f"{self._config.max_artifact_bytes}"
            )
        digest, size, temp_path = self._write_stream_to_temp((data,), None)
        context = _PutContext(
            media_type=media_type,
            provenance_hash=provenance_hash,
            tags=tuple(tags),
            source_fingerprint=source_fingerprint,
            dependency_fingerprint=dependency_fingerprint,
            data_fingerprint=data_fingerprint,
            lineage=tuple(lineage),
        )
        return self._publish(digest, size, temp_path, context)

    @override
    def put_artifact_stream(
        self,
        chunks: Iterable[bytes],
        *,
        media_type: str = "application/octet-stream",
        provenance_hash: str = "",
        tags: Sequence[tuple[str, str]] = (),
        source_fingerprint: str = "",
        dependency_fingerprint: str = "",
        data_fingerprint: str = "",
        lineage: Sequence[str] = (),
        should_cancel: Callable[[], bool] | None = None,
    ) -> ArtifactPutResult:
        """Stream chunks into content-addressed storage, hashing while writing."""
        digest, size, temp_path = self._write_stream_to_temp(chunks, should_cancel)
        context = _PutContext(
            media_type=media_type,
            provenance_hash=provenance_hash,
            tags=tuple(tags),
            source_fingerprint=source_fingerprint,
            dependency_fingerprint=dependency_fingerprint,
            data_fingerprint=data_fingerprint,
            lineage=tuple(lineage),
        )
        return self._publish(digest, size, temp_path, context)

    @override
    def get_artifact_bytes(self, digest: str) -> bytes:
        """Retrieve artifact bytes and verify SHA-256 digest and size."""
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
            metadata = self.get_metadata(digest)
            if metadata is not None and metadata.ref.size_bytes != len(data):
                raise ArtifactCorruptionError(
                    f"Artifact size {len(data)} does not match metadata "
                    f"{metadata.ref.size_bytes}"
                )
            return data

    def _metadata_record(
        self, digest: str
    ) -> tuple[ArtifactMetadata, StorageRecord] | None:
        """Return parsed metadata plus its storage record, or None."""
        clean_digest = digest.strip().lower()
        rec = self._storage.get_record(ARTIFACTS_NAMESPACE, clean_digest)
        if rec is None:
            return None
        parsed = json.loads(rec.payload_bytes.decode("utf-8"))
        tags_raw = parsed.get("tags", [])
        metadata = ArtifactMetadata(
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
            source_fingerprint=parsed.get("source_fingerprint", ""),
            dependency_fingerprint=parsed.get("dependency_fingerprint", ""),
            data_fingerprint=parsed.get("data_fingerprint", ""),
            lineage=tuple(parsed.get("lineage", [])),
            refcount=int(parsed.get("refcount", 0)),
        )
        return metadata, rec

    def _rewrite_metadata(
        self, digest: str, metadata: ArtifactMetadata, rec: StorageRecord
    ) -> None:
        """Persist updated metadata via compare-and-swap on the record."""
        meta_json = {
            "digest": metadata.ref.digest,
            "size_bytes": metadata.ref.size_bytes,
            "media_type": metadata.media_type,
            "schema_version": metadata.schema_version,
            "created_at_utc": metadata.created_at_utc,
            "provenance_hash": metadata.provenance_hash,
            "retention_policy": metadata.retention_policy,
            "tags": [list(t) for t in metadata.tags],
            "source_fingerprint": metadata.source_fingerprint,
            "dependency_fingerprint": metadata.dependency_fingerprint,
            "data_fingerprint": metadata.data_fingerprint,
            "lineage": list(metadata.lineage),
            "refcount": metadata.refcount,
        }
        payload_bytes = json.dumps(
            meta_json, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        result = self._storage.commit_transaction(
            [
                StorageMutation(
                    namespace=ARTIFACTS_NAMESPACE,
                    key=digest.strip().lower(),
                    schema_version=metadata.schema_version,
                    payload_bytes=payload_bytes,
                    expected_revision=rec.revision,
                )
            ]
        )
        if not result.committed:
            raise ArtifactError(f"Metadata update conflict for artifact {digest}")

    @override
    def get_metadata(self, digest: str) -> ArtifactMetadata | None:
        """Fetch metadata for an artifact from Storage."""
        record = self._metadata_record(digest)
        return record[0] if record is not None else None

    @override
    def request_deletion(self, digest: str) -> bool:
        """Mark an artifact's metadata for retention review (phase one)."""
        with self._lock:
            record = self._metadata_record(digest)
            if record is None:
                return False
            metadata, rec = record
            if metadata.retention_policy == "retention_marked":
                return True
            marked = ArtifactMetadata(
                ref=metadata.ref,
                media_type=metadata.media_type,
                schema_version=metadata.schema_version,
                created_at_utc=metadata.created_at_utc,
                provenance_hash=metadata.provenance_hash,
                retention_policy="retention_marked",
                tags=metadata.tags,
                source_fingerprint=metadata.source_fingerprint,
                dependency_fingerprint=metadata.dependency_fingerprint,
                data_fingerprint=metadata.data_fingerprint,
                lineage=metadata.lineage,
                refcount=metadata.refcount,
            )
            self._rewrite_metadata(digest, marked, rec)
            return True

    @override
    def acquire_reference(self, digest: str) -> None:
        """Increment the artifact's active reference count."""
        with self._lock:
            record = self._metadata_record(digest)
            if record is None:
                raise ArtifactNotFoundError(f"Artifact {digest} not found")
            metadata, rec = record
            acquired = replace(metadata, refcount=metadata.refcount + 1)
            self._rewrite_metadata(digest, acquired, rec)

    @override
    def release_reference(self, digest: str) -> None:
        """Decrement the artifact's active reference count."""
        with self._lock:
            record = self._metadata_record(digest)
            if record is None:
                raise ArtifactNotFoundError(f"Artifact {digest} not found")
            metadata, rec = record
            released = replace(metadata, refcount=max(0, metadata.refcount - 1))
            self._rewrite_metadata(digest, released, rec)

    @override
    def delete_artifact(self, digest: str) -> bool:
        """Delete a marked, unreferenced artifact and its metadata.

        Retention protocol: mark metadata, prove no active reference needs
        the artifact, then remove content. An artifact with a nonzero
        reference count is refused with ArtifactInUseError.
        """
        target_path = self._resolve_target_path(digest)
        with self._lock:
            record = self._metadata_record(digest)
            if record is None and not target_path.exists():
                return False

            metadata: ArtifactMetadata | None = record[0] if record else None
            rec: StorageRecord | None = record[1] if record else None

            # Phase 1: mark metadata for deletion.
            if metadata is not None and rec is not None:
                if metadata.refcount > 0:
                    raise ArtifactInUseError(
                        f"Artifact {digest} still has {metadata.refcount} "
                        "active reference(s); deletion refused"
                    )
                if metadata.retention_policy != "retention_marked":
                    self.request_deletion(digest)

            # Phase 2: prove no active reference needs the artifact after
            # marking (re-read; marking bumped the record revision).
            if metadata is not None:
                fresh = self._metadata_record(digest)
                if fresh is not None:
                    if fresh[0].refcount > 0:
                        raise ArtifactInUseError(
                            f"Artifact {digest} gained a reference during "
                            "deletion; refused"
                        )
                    meta_tx = self._storage.commit_transaction(
                        [
                            StorageDelete(
                                namespace=ARTIFACTS_NAMESPACE,
                                key=digest.strip().lower(),
                                expected_revision=fresh[1].revision,
                            )
                        ]
                    )
                    if not meta_tx.committed:
                        # Metadata survived: keep content so the store never
                        # advertises a digest whose metadata still exists.
                        raise ArtifactError(
                            f"Metadata deletion conflict for {digest}; "
                            "content preserved"
                        )

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
    "ArtifactCancelledError",
    "ArtifactCorruptionError",
    "ArtifactError",
    "ArtifactInUseError",
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
