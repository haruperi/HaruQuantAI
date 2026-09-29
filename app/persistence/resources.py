"""Host Custody of Quantitative Resources, Revision Envelopes, and Artifacts.

Description:
    Provides durable, host-owned custody for immutable quantitative resource
    revisions and artifacts independently of producer runtime code.

    External relations and workflows:
    - Host capabilities: Injected into workspace plugins via ResourceAccess
      capability slots (app.host.capabilities) allowing plugins to publish
      models, backtest results, and datasets under strict custody.
    - Isolation boundary: Revisions survive plugin removal; readers verify
      declarative JSON schemas without importing or executing producer code.

    Internal coordination:
    - ResourceRef: Defines immutable identity, semantic revision, content digest,
      media type, and provenance metadata.
    - ResourceRecord: Bounded JSON envelope encapsulating raw payload (base64)
      and explicit reader authorization lists.
    - ResourceStore: Enforces exclusive filesystem lock serialization, atomic
      fsync-tempfile-rename writes, and SHA-256 integrity validation.

Purpose:
    FEAT-PERSIST-RESOURCES: Durable custody, publication, and retrieval of
    immutable quantitative artifacts with cryptographic integrity verification.

Key Capabilities:
    - FR-PERSIST-RESOURCES-PUBLISH: Atomically publishes an immutable resource
      revision envelope with schema validation, digest verification, and
      exclusive writer locking via ResourceStore.publish().
      * Verified via: logger.info("ResourceStore committed revision %d for "
        "resource %s (producer=%s)")
    - FR-PERSIST-RESOURCES-READ: Reads and validates stored payload bytes against
      SHA-256 digest and access control grants via ResourceStore.read().
      * Verified via: logger.info("ResourceStore read resource %s revision %d "
        "(principal=%s)")
    - FR-PERSIST-RESOURCES-LIST: Discovers resource revisions visible to a
      requesting principal or published globally via ResourceStore.list().
      * Verified via: logger.info("ResourceStore listed %d resources for "
        "principal %s")

Python API Usage:
    ```python
    from pathlib import Path

    from app.persistence.resources import ResourceStore

    store = ResourceStore(Path("data/resources"))
    ref = store.publish(
        producer_id="plugin.strategy.builder",
        producer_version="1.0.0",
        content=b"strategy_weights_payload",
        schema_id="schema.weights",
        schema_version="1.0.0",
        schema_json='{"type": "object"}',
        media_type="application/octet-stream",
        readers=("operator",),
    )
    data, schema = store.read(principal="operator", reference=ref)
    ```

CLI Usage:
    ```bash
    # Verified through host resource tests:
    uv run python -m pytest tests/host/test_resource_store.py
    ```
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from pydantic import Field

from app.host.contracts import Document
from app.host.logging import get_logger

logger = get_logger(__name__)

MAX_RESOURCE_BYTES = 16 * 1024 * 1024
MAX_RESOURCE_RECORDS = 4096
MAX_SCHEMA_BYTES = 65536


class ResourceRef(Document):
    """Immutable identity, revision, schema, digest and producer provenance."""

    id: str = Field(pattern=r"^[a-f0-9]{32}$")
    revision: int = Field(ge=1)
    schema_id: str = Field(min_length=1, max_length=200)
    schema_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    media_type: str = Field(min_length=1, max_length=100)
    producer_id: str = Field(min_length=1, max_length=200)
    producer_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")


class ResourceRecord(Document):
    """One bounded JSON envelope; declarative schema and access grants survive code."""

    reference: ResourceRef
    readers: tuple[str, ...]
    schema_document: str
    content_base64: str


class ResourceStore:
    """Custody rooted in an explicitly injected directory; construction has no I/O."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def _directory(self) -> Path:
        """Check the explicitly configured storage boundary without following links."""
        if any(
            p.is_symlink() or p.is_junction() for p in (self.root, *self.root.parents)
        ):
            raise ValueError("Linked resource store is not permitted")
        return self.root.resolve()

    def _records(self) -> tuple[ResourceRecord, ...]:
        """Read a bounded inventory of inert resource records."""
        root = self._directory()
        if not root.exists():
            return ()
        files = sorted(root.glob("*.json"))
        if len(files) > MAX_RESOURCE_RECORDS:
            raise ValueError("Resource inventory limit")
        return tuple(self._record(path) for path in files)

    def _record(self, path: Path) -> ResourceRecord:
        """Decode a bounded envelope, rejecting linked or corrupted records."""
        if path.is_symlink() or path.is_junction():
            raise ValueError("Linked resource record")
        with path.open("rb") as stream:
            data = stream.read(MAX_RESOURCE_BYTES * 2 + 1)
        if len(data) > MAX_RESOURCE_BYTES * 2:
            raise ValueError("Resource envelope limit")
        return ResourceRecord.model_validate_json(data)

    def list(self, principal: str) -> tuple[ResourceRef, ...]:
        """Return only revisions explicitly readable by the caller or published."""
        results = tuple(
            record.reference
            for record in self._records()
            if principal in record.readers or "*" in record.readers
        )
        logger.info(
            "ResourceStore listed %d resources for principal %s",
            len(results),
            principal,
        )
        return results

    def read(self, principal: str, reference: ResourceRef) -> tuple[bytes, str]:
        """Read verified bytes and declarative schema without producer presence.

        Raises:
            PermissionError: Caller lacks the revision's read grant.
            ValueError: Identity, content or envelope is corrupt.
            OSError: The reference is unavailable in this store.
        """
        path = self._directory() / f"{reference.id}.{reference.revision}.json"
        record = self._record(path)
        if principal not in record.readers and "*" not in record.readers:
            raise PermissionError("Resource read denied")
        if record.reference != reference:
            raise ValueError("Resource reference mismatch")
        content = base64.b64decode(record.content_base64, validate=True)
        if len(content) > MAX_RESOURCE_BYTES:
            raise ValueError("Resource content limit")
        if hashlib.sha256(content).hexdigest() != reference.digest:
            raise ValueError("Resource checksum mismatch")
        logger.info(
            "ResourceStore read resource %s revision %d (principal=%s)",
            reference.id,
            reference.revision,
            principal,
        )
        return content, record.schema_document

    def publish(
        self,
        producer_id: str,
        producer_version: str,
        content: bytes,
        *,
        schema_id: str,
        schema_version: str,
        schema_json: str,
        media_type: str,
        readers: tuple[str, ...] = (),
        previous: ResourceRef | None = None,
    ) -> ResourceRef:
        """Publish one revision atomically with explicit grants and optimistic lineage.

        A previous reference permits only its original producer to append a revision.
        Published revisions and read grants never change. New consumers may read
        public resources, but cannot overwrite the producer's private authority.

        Raises:
            ValueError: Bounds/schema/lineage fail validation.
            FileExistsError: Another writer or abandoned lock requires reconciliation.
            PermissionError: Producer does not own the prior reference.
        """
        if (
            len(content) > MAX_RESOURCE_BYTES
            or len(schema_json.encode()) > MAX_SCHEMA_BYTES
        ):
            raise ValueError("Resource publication limit")
        if not isinstance(json.loads(schema_json), dict):
            raise TypeError("Resource schema must be a JSON object")
        if previous is not None and previous.producer_id != producer_id:
            raise PermissionError("Resource write denied")
        root = self._directory()
        root.mkdir(parents=True, exist_ok=True)
        lock = root / ".publication.lock"
        lock.open("x", encoding="utf-8").close()
        try:
            return self._publish_locked(
                ResourceRecord(
                    reference=ResourceRef(
                        id=previous.id if previous else uuid4().hex,
                        revision=previous.revision + 1 if previous else 1,
                        schema_id=schema_id,
                        schema_version=schema_version,
                        digest=hashlib.sha256(content).hexdigest(),
                        media_type=media_type,
                        producer_id=producer_id,
                        producer_version=producer_version,
                    ),
                    readers=tuple(sorted({producer_id, *readers})),
                    schema_document=schema_json,
                    content_base64=base64.b64encode(content).decode("ascii"),
                ),
                previous,
            )
        finally:
            lock.unlink()

    def _publish_locked(
        self, record: ResourceRecord, previous: ResourceRef | None
    ) -> ResourceRef:
        """Check lineage under the writer lock and atomically install an envelope."""
        records = self._records()
        if len(records) >= MAX_RESOURCE_RECORDS:
            raise ValueError("Resource inventory limit")
        if previous is not None:
            revisions = [r.reference for r in records if r.reference.id == previous.id]
            if not revisions or max(revisions, key=lambda r: r.revision) != previous:
                raise ValueError("Stale resource revision")
        root = self._directory()
        target = root / f"{record.reference.id}.{record.reference.revision}.json"
        with NamedTemporaryFile(dir=root, suffix=".pending", delete=False) as stream:
            temporary = Path(stream.name)
            try:
                stream.write(record.model_dump_json().encode())
                stream.flush()
                os.fsync(stream.fileno())
            except BaseException:
                stream.close()
                temporary.unlink()
                raise
        try:
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        logger.info(
            "ResourceStore committed revision %d for resource %s (producer=%s)",
            record.reference.revision,
            record.reference.id,
            record.reference.producer_id,
        )
        return record.reference
