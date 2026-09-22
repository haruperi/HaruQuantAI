"""Host artifacts owner: content-addressed storage with SHA-256 and quotas.

This file is the single owner of the ``host.artifacts@1`` capability:
immutable binary artifacts stored beneath a configured root, addressed
by the SHA-256 digest of their content, with metadata records kept in
``host.storage``. Per the one-file-owner rule, all artifact layout and
publication details for this capability live here.

It does not own raw record persistence (delegated to ``Storage``), job
lifecycle semantics, or UI state.

Persistence and filesystem safety:
- Tests use isolated temporary stores and roots only.
- Callers see digests, refs, and metadata documents, never SQL,
  connections, or storage paths beyond the configured root directory.
- Content publication is atomic (temp file + fsync + rename) and
  metadata is committed via Storage only after content exists; a
  failed metadata commit removes only the content this operation
  just wrote.
- Identical content deduplicates without mutating existing files.
- Reads verify both the recomputed digest and the recorded size, and
  traversal or escape digests are rejected.
- ARCH-019: this module and ``app/host/storage.py`` are the only
  filesystem mutators in the host.
"""

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
    """Raised when an artifact digest is not found.

    Surfaced by reads and reference operations whose metadata record
    does not exist.
    """


class ArtifactQuotaExceededError(ArtifactError):
    """Raised when artifact size exceeds individual or total quota.

    The per-artifact quota is enforced up front and again mid-stream;
    the total-store quota is enforced at publication time.
    """


class ArtifactPathEscapeError(ArtifactError):
    """Raised when an artifact digest results in a path escape attempt."""


class ArtifactCorruptionError(ArtifactError):
    """Raised when stored content does not match its expected metadata.

    Covers both digest mismatches and sizes that disagree with the
    recorded metadata.
    """


class ArtifactInUseError(ArtifactError):
    """Raised when deletion is refused because active references remain."""


class ArtifactCancelledError(ArtifactError):
    """Raised when a streaming artifact write is cancelled by the caller."""


@dataclass(frozen=True, slots=True)
class ArtifactRef:
    """Immutable reference to a content-addressed artifact.

    Attributes:
        digest: SHA-256 digest as exactly 64 hex characters, naming
            the artifact content.
        size_bytes: Exact content length in bytes (>= 0).
    """

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
    """Lineage and media metadata for an artifact.

    Immutable; updates happen by constructing a replacement and
    compare-and-swap rewriting the storage record.

    Attributes:
        ref: Content digest and size this metadata describes.
        media_type: Media type of the content.
        schema_version: Metadata document schema version (>= 1).
        created_at_utc: ISO-8601 UTC stamp of first publication.
        provenance_hash: Opaque producer-defined provenance identity.
        retention_policy: Retention state; ``"standard"`` until a
            deletion request marks it ``"retention_marked"``.
        tags: Ordered key/value pairs for lookup and display.
        source_fingerprint: Fingerprint of the producing source.
        dependency_fingerprint: Fingerprint of the dependency set.
        data_fingerprint: Fingerprint of the consumed input data.
        lineage: Digests of upstream artifacts this one derives from.
        refcount: Number of active references protecting deletion.
    """

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
    """Outcome of storing an artifact.

    Attributes:
        ref: Reference (digest and size) of the stored content.
        metadata: Metadata as committed; the pre-existing metadata
            when the put deduplicated.
        deduplicated: True when identical content already existed and
            nothing new was written.
    """

    ref: ArtifactRef
    metadata: ArtifactMetadata
    deduplicated: bool


@dataclass(frozen=True, slots=True)
class ArtifactsConfig:
    """Configuration for filesystem artifact store.

    Attributes:
        root_dir: Root directory for object storage; the ``objects``
            and ``.tmp`` subdirectories are created on construction.
        max_artifact_bytes: Per-artifact quota enforced before and
            during streaming writes.
        max_total_bytes: Total quota across all stored objects,
            enforced at publication time.
    """

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
    """Public capability protocol for content-addressed artifact storage.

    Contract: content-addressed SHA-256 storage beneath a configured
    root; streaming puts hash while writing, check a per-chunk caller
    cancellation callback, and enforce the mid-stream quota;
    publication is atomic and metadata is committed via Storage only
    after the content exists; identical content deduplicates without
    mutating existing files; reads verify the digest and the recorded
    size; deletion follows a two-phase retention protocol
    (``request_deletion`` marks, ``delete_artifact`` proves the
    refcount is zero) with reference counting protection.
    """

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
        """Store bytes content-addressed by SHA-256 and return a result.

        Args:
            data: Complete artifact content.
            media_type: Media type recorded in metadata.
            provenance_hash: Producer provenance identity.
            tags: Key/value pairs recorded in metadata.
            source_fingerprint: Producing-source fingerprint.
            dependency_fingerprint: Dependency-set fingerprint.
            data_fingerprint: Consumed-input fingerprint.
            lineage: Digests of upstream artifacts.

        Returns:
            The stored reference, committed metadata, and whether the
            content was deduplicated against an existing artifact.

        Raises:
            TypeError: If ``data`` is not bytes.
            ArtifactQuotaExceededError: If the bytes exceed the
                per-artifact quota or the total store quota.
            ArtifactPathEscapeError: If the digest escapes the root.
            ArtifactError: If the metadata commit fails (the newly
                written content is then removed).
        """
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

        The digest is computed incrementally as chunks are written to a
        temporary file. The caller cancellation callback is checked
        before each chunk; a cancelled stream removes its temporary
        file and raises ArtifactCancelledError without publishing
        partial content. The per-artifact quota is enforced mid-stream.

        Args:
            chunks: Iterable of content chunks.
            media_type: Media type recorded in metadata.
            provenance_hash: Producer provenance identity.
            tags: Key/value pairs recorded in metadata.
            source_fingerprint: Producing-source fingerprint.
            dependency_fingerprint: Dependency-set fingerprint.
            data_fingerprint: Consumed-input fingerprint.
            lineage: Digests of upstream artifacts.
            should_cancel: Optional callback polled before each chunk;
                returning True aborts the write.

        Returns:
            The stored reference, committed metadata, and whether the
            content was deduplicated against an existing artifact.

        Raises:
            ArtifactCancelledError: If the caller cancels mid-stream.
            ArtifactQuotaExceededError: If the stream exceeds the
                per-artifact quota mid-stream or the total quota at
                publication.
            TypeError: If a chunk is not bytes-like.
            ArtifactPathEscapeError: If the digest escapes the root.
            ArtifactError: If the metadata commit fails.
        """
        ...

    def get_artifact_bytes(self, digest: str) -> bytes:
        """Read and verify artifact bytes by SHA-256 digest.

        Verifies the recomputed digest and, when metadata exists, the
        recorded size before returning content.

        Args:
            digest: SHA-256 hex digest of the artifact.

        Returns:
            The verified artifact bytes.

        Raises:
            ArtifactNotFoundError: If no content exists for the digest.
            ArtifactCorruptionError: If content fails digest or size
                verification against metadata.
            ArtifactPathEscapeError: If the digest escapes the root.
        """
        ...

    def get_metadata(self, digest: str) -> ArtifactMetadata | None:
        """Fetch metadata for an artifact by digest.

        Args:
            digest: SHA-256 hex digest of the artifact.

        Returns:
            The parsed metadata, or ``None`` when no record exists.
        """
        ...

    def request_deletion(self, digest: str) -> bool:
        """Mark an artifact's metadata for retention review (phase one).

        Sets ``retention_policy`` to ``"retention_marked"``; content is
        not touched until ``delete_artifact`` succeeds.

        Args:
            digest: SHA-256 hex digest of the artifact.

        Returns:
            True if the artifact exists (or was already marked);
            False when no metadata record exists.
        """
        ...

    def acquire_reference(self, digest: str) -> None:
        """Increment the artifact's active reference count.

        Args:
            digest: SHA-256 hex digest of the artifact.

        Raises:
            ArtifactNotFoundError: If no metadata record exists.
        """
        ...

    def release_reference(self, digest: str) -> None:
        """Decrement the artifact's active reference count.

        The count floors at zero; releasing below zero is not an error.

        Args:
            digest: SHA-256 hex digest of the artifact.

        Raises:
            ArtifactNotFoundError: If no metadata record exists.
        """
        ...

    def delete_artifact(self, digest: str) -> bool:
        """Delete a marked, unreferenced artifact and its metadata.

        Retention protocol: mark metadata (phase one), prove no active
        reference needs the artifact, then delete metadata first and
        content second. An artifact with a nonzero reference count is
        refused with ArtifactInUseError. The metadata deletion is
        compare-and-swap checked: if it conflicts, content is
        preserved so the store never loses data whose metadata still
        exists.

        Args:
            digest: SHA-256 hex digest of the artifact.

        Returns:
            True if content or metadata existed and were removed;
            False when neither exists.

        Raises:
            ArtifactInUseError: If any active reference remains.
            ArtifactError: If the metadata CAS delete conflicts;
                content is preserved.
        """
        ...

    def has_artifact(self, digest: str) -> bool:
        """Return whether an artifact exists in the store.

        Args:
            digest: SHA-256 hex digest of the artifact.

        Returns:
            True only when both the object file and its metadata
            record exist; malformed digests also return False.
        """
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
    """Filesystem-backed content-addressed artifact store.

    Layout: published content lives at
    ``<root>/objects/<first-2-hex>/<remaining-62-hex>`` and in-flight
    writes at ``<root>/.tmp``, guarded by an RLock. Metadata documents
    live in Storage under the ``artifacts`` namespace; published
    content is never mutated afterwards.
    """

    def __init__(self, config: ArtifactsConfig, storage: Storage) -> None:
        """Initialize artifact store, creating the root layout.

        Args:
            config: Root directory and quota configuration.
            storage: Durable store used for metadata records.
        """
        self._config = config
        self._storage = storage
        self._root_dir = Path(config.root_dir).resolve()
        self._objects_dir = self._root_dir / "objects"
        self._tmp_dir = self._root_dir / ".tmp"
        self._lock = threading.RLock()

        self._objects_dir.mkdir(parents=True, exist_ok=True)
        self._tmp_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_target_path(self, digest: str) -> Path:
        """Resolve sharded digest path and verify no path escape.

        Normalizes the digest to lowercase, shards by the first two hex
        characters, and raises ArtifactPathEscapeError unless the
        resolved path stays strictly inside the objects directory.
        """
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
        cancellation before each chunk. The completed file is flushed
        and fsynced, and any failure removes it. Returns
        (digest, size, temp_path).
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
        """Atomically publish temp content and commit metadata via Storage.

        Order of operations: enforce the total quota (only for content
        not already present), deduplicate against existing content
        without mutating it, rename the fsynced temp file into place,
        then commit the metadata record. A failed metadata commit
        removes only the content published by this operation.
        """
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
        """Store bytes atomically beneath root and record metadata.

        Enforces the per-artifact quota up front, then delegates to the
        streaming writer and the atomic publisher.

        Args:
            data: Complete artifact content.
            media_type: Media type recorded in metadata.
            provenance_hash: Producer provenance identity.
            tags: Key/value pairs recorded in metadata.
            source_fingerprint: Producing-source fingerprint.
            dependency_fingerprint: Dependency-set fingerprint.
            data_fingerprint: Consumed-input fingerprint.
            lineage: Digests of upstream artifacts.

        Returns:
            The stored reference, committed metadata, and whether the
            content was deduplicated.

        Raises:
            TypeError: If ``data`` is not bytes.
            ArtifactQuotaExceededError: If a quota is exceeded.
            ArtifactError: If the metadata commit fails.
        """
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
        """Stream chunks into content-addressed storage, hashing while writing.

        Args:
            chunks: Iterable of content chunks.
            media_type: Media type recorded in metadata.
            provenance_hash: Producer provenance identity.
            tags: Key/value pairs recorded in metadata.
            source_fingerprint: Producing-source fingerprint.
            dependency_fingerprint: Dependency-set fingerprint.
            data_fingerprint: Consumed-input fingerprint.
            lineage: Digests of upstream artifacts.
            should_cancel: Optional callback polled before each chunk.

        Returns:
            The stored reference, committed metadata, and whether the
            content was deduplicated.

        Raises:
            ArtifactCancelledError: If cancelled by the callback.
            ArtifactQuotaExceededError: If a quota is exceeded.
        """
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
        """Retrieve artifact bytes and verify SHA-256 digest and size.

        Args:
            digest: SHA-256 hex digest of the artifact.

        Returns:
            The verified artifact bytes.

        Raises:
            ArtifactNotFoundError: If the content file is absent.
            ArtifactCorruptionError: If the recomputed digest differs
                or the size disagrees with metadata.
        """
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
        """Persist updated metadata via compare-and-swap on the record.

        Args:
            digest: Digest whose metadata record is rewritten.
            metadata: The replacement metadata document.
            rec: The storage record the CAS revision is taken from.

        Raises:
            ArtifactError: If the CAS write conflicts with a
                concurrent metadata update.
        """
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
        """Fetch metadata for an artifact from Storage.

        Args:
            digest: SHA-256 hex digest of the artifact.

        Returns:
            The parsed metadata, or ``None`` when absent.
        """
        record = self._metadata_record(digest)
        return record[0] if record is not None else None

    @override
    def request_deletion(self, digest: str) -> bool:
        """Mark metadata ``retention_marked`` (phase one of retention).

        Args:
            digest: SHA-256 hex digest of the artifact.

        Returns:
            True when the record exists or was already marked; False
            when no metadata record exists.
        """
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
        """Increment the artifact's active reference count.

        Args:
            digest: SHA-256 hex digest of the artifact.

        Raises:
            ArtifactNotFoundError: If no metadata record exists.
        """
        with self._lock:
            record = self._metadata_record(digest)
            if record is None:
                raise ArtifactNotFoundError(f"Artifact {digest} not found")
            metadata, rec = record
            acquired = replace(metadata, refcount=metadata.refcount + 1)
            self._rewrite_metadata(digest, acquired, rec)

    @override
    def release_reference(self, digest: str) -> None:
        """Decrement the artifact's active reference count.

        The count floors at zero; over-releasing is not an error.

        Args:
            digest: SHA-256 hex digest of the artifact.

        Raises:
            ArtifactNotFoundError: If no metadata record exists.
        """
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

        Retention protocol: mark metadata (phase one), prove no active
        reference needs the artifact, then remove metadata first and
        content second. The metadata deletion result is checked: on a
        CAS conflict content is preserved because metadata still
        exists. ArtifactInUseError protects any nonzero refcount
        observed before or after marking.

        Args:
            digest: SHA-256 hex digest of the artifact.

        Returns:
            True if metadata or content existed and were removed;
            False when neither exists.

        Raises:
            ArtifactInUseError: If active references remain.
            ArtifactError: If the metadata CAS delete conflicts;
                content is preserved.
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
        """Return True only when both content and metadata exist."""
        try:
            target_path = self._resolve_target_path(digest)
        except ValueError:
            return False
        with self._lock:
            return target_path.exists() and (self.get_metadata(digest) is not None)


class _ArtifactsFeature:
    """Feature providing HOST_ARTIFACTS requiring HOST_STORAGE.

    The artifact store is constructed at startup against the storage
    capability resolved from the runtime context.
    """

    spec = FeatureSpec(
        "host.artifacts",
        provides=frozenset({HOST_ARTIFACTS}),
        requires=frozenset({HOST_STORAGE}),
        description="Content-addressed artifact store with SHA-256 and quotas",
    )

    def __init__(self, config: ArtifactsConfig) -> None:
        """Store the configuration until storage is available."""
        self._config = config
        self._service: _FilesystemArtifactStore | None = None

    async def start(self, context: FeatureContext) -> None:
        """Build the store over HOST_STORAGE and provide HOST_ARTIFACTS."""
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
