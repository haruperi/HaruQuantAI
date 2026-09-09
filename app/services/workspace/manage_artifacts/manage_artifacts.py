"""Focused production domain logic for immutable artifact custody.

Purpose:
    Implement the ``workspace.artifacts@1`` capability: staged validation
    and atomic content-addressed publication, bounded authorized
    downloads, reference/legal-hold retention, and admitted custody
    maintenance with audit receipts.

Key capabilities:
    * Crash-safe publication through one custody root (staging directory
      plus content-addressed object store) using same-volume atomic
      rename.
    * Idempotent publication bound to a semantic fingerprint, not only a
      request id.
    * Authorization-bound downloads whose bytes always re-verify against
      the immutable stored checksum.
    * Reference-aware, admission-gated cleanup that never deletes
      referenced or legally held bytes.

Python API usage:
    service = ManageArtifactsService(config, persistence, admission)
    receipt = await service.publish_artifact(request)
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from app.composition.logging import get_logger
from app.contracts.orchestration.resources import (
    AdmissionStatus,
    FiniteResourceProfile,
    ResourceAdmissionPort,
    ResourceAdmissionRequest,
    WorkClass,
)
from app.contracts.workspace.artifacts import (
    AddReferenceRequest,
    ArtifactAccessDeniedError,
    ArtifactAdmissionUnavailableError,
    ArtifactCustodyState,
    ArtifactGrantExpiredError,
    ArtifactIntegrityError,
    ArtifactNotFoundError,
    ArtifactPublicationConflictError,
    ArtifactRecord,
    ArtifactReference,
    ArtifactValidationError,
    AuthorizeDownloadRequest,
    CustodyReceipt,
    CustodyReconciliationReport,
    DownloadGrant,
    InspectArtifactRequest,
    ManageArtifactsOperation,
    PublishArtifactRequest,
    ReconcileCustodyRequest,
    RemoveReferenceRequest,
    ResolvedDownload,
    ResolveDownloadRequest,
    SetLegalHoldRequest,
)
from app.contracts.workspace.errors import (
    RevisionConflictError,
    WorkspaceError,
)
from app.contracts.workspace.persistence import (
    EvidenceRecord,
    PersistenceCapability,
)
from app.services.workspace.manage_artifacts._persistence import (
    NAMESPACE,
    ArtifactCustodyStore,
)
from app.services.workspace.manage_artifacts.config import ManageArtifactsConfig

logger = get_logger(__name__)

# Payloads are written to staging in bounded slices so publication I/O
# stays chunked even though the accepted payload is memory-bounded by
# configuration.
_WRITE_CHUNK_BYTES = 1024 * 1024

# A fully applied finalize transaction touches exactly three rows: the
# publication insert, the retention seed, and the staging close.
_FINALIZE_APPLIED_ROWS = 3

# A fully applied reference removal touches exactly two rows: the fenced
# reference delete and the retention revision bump.
_REMOVE_REFERENCE_APPLIED_ROWS = 2

# Fixed finite maintenance profile for admitted reconciliation runs.
_RECONCILE_MEMORY_BYTES = 1024 * 1024
_RECONCILE_TEMP_DISK_BYTES = 16 * 1024 * 1024


def _utc_now_iso() -> str:
    """Return a fixed-width ISO 8601 UTC timestamp.

    Returns:
        Timestamp with always-present microsecond precision so
        lexicographic comparison matches chronological order.
    """
    return datetime.now(UTC).isoformat(timespec="microseconds")


def _hash_payload(payload: bytes) -> str:
    """Return the canonical wire content hash for one payload.

    Returns:
        ``sha256:``-prefixed lowercase hex SHA-256 digest.
    """
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _publication_fingerprint(
    artifact_id: str,
    workspace_id: str,
    account_id: str,
    schema_declaration: str,
    byte_count: int,
    content_hash: str,
    idempotency_key: str,
    source_reference: str,
) -> str:
    """Return the canonical idempotency fingerprint for a publication.

    The fingerprint covers every ratified logical-publication identity
    field so a replayed key with changed semantics is a typed conflict
    rather than an accidental second publication.

    Returns:
        Lowercase hex SHA-256 of the canonical JSON identity mapping.
    """
    canonical = json.dumps(
        {
            "account_id": account_id,
            "artifact_id": artifact_id,
            "byte_count": byte_count,
            "content_hash": content_hash,
            "idempotency_key": idempotency_key,
            "schema_declaration": schema_declaration,
            "source_reference": source_reference,
            "workspace_id": workspace_id,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _staging_path(custody_root: Path, staging_id: str) -> Path:
    """Return the staging file path for one staging identity."""
    return custody_root / "staging" / f"{staging_id}.bin"


def _object_path(custody_root: Path, content_hash: str) -> Path:
    """Return the content-addressed object path for one content hash.

    The path is derived exclusively from the validated hex digest, so no
    caller-supplied string ever reaches path construction.
    """
    digest = content_hash.removeprefix("sha256:")
    return custody_root / "objects" / digest[:2] / f"{digest}.bin"


def _write_staged_file(path: Path, payload: bytes) -> None:
    """Write one staged payload in bounded chunks and flush to disk.

    Args:
        path: Staging file path inside the custody root.
        payload: Bounded immutable payload bytes.

    Raises:
        WorkspaceError: If the staged write fails.
    """
    try:
        with path.open("wb") as handle:
            handle.writelines(
                payload[offset : offset + _WRITE_CHUNK_BYTES]
                for offset in range(0, len(payload), _WRITE_CHUNK_BYTES)
            )
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as error:
        message = f"staged artifact write failed: {error.errno}"
        raise WorkspaceError(
            message,
            error_code="ARTIFACT_STORAGE_ERROR",
        ) from error


def _verify_file(path: Path, artifact_id: str) -> tuple[int, str]:
    """Stream-verify one custody file's byte count and content hash.

    Args:
        path: Object or staging file inside the custody root.
        artifact_id: Owning artifact identity for typed failures.

    Returns:
        Tuple of exact byte count and canonical content hash.

    Raises:
        ArtifactIntegrityError: If the file cannot be read.
    """
    digest = hashlib.sha256()
    byte_count = 0
    try:
        with Path(path).open("rb") as handle:
            while chunk := handle.read(_WRITE_CHUNK_BYTES):
                digest.update(chunk)
                byte_count += len(chunk)
    except OSError as error:
        raise ArtifactIntegrityError(
            artifact_id,
            f"custody bytes unreadable (errno={error.errno})",
        ) from error
    return byte_count, f"sha256:{digest.hexdigest()}"


def _fsync_directory(path: Path) -> None:
    """Best-effort directory durability sync after an atomic rename.

    Directory fsync is a POSIX durability mechanism; on Windows it is
    unavailable (opening a directory raises), so this is deliberately
    tolerant and the residual crash window is closed by restart
    reconciliation rather than pretended away.
    """
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def _evidence_id(prefix: str) -> str:
    """Return one fresh bounded evidence identity."""
    return f"{prefix}:{uuid.uuid4().hex}"


class ManageArtifactsService:
    """Serve one ``workspace.artifacts@1`` provider over owned custody."""

    def __init__(
        self,
        config: ManageArtifactsConfig | None = None,
        persistence: PersistenceCapability | None = None,
        admission: ResourceAdmissionPort | None = None,
    ) -> None:
        """Initialize custody state, durable store, and custody root.

        Args:
            config: Strict feature configuration; defaults when None.
            persistence: Required bounded Workspace persistence provider.
            admission: Optional operation-gated resource admission port;
                heavy operations fail closed when it is absent.

        Raises:
            WorkspaceError: If the required persistence provider is
                absent or migrations cannot reach the declared schema.
        """
        if config is None:
            config = ManageArtifactsConfig()
        if persistence is None:
            raise WorkspaceError(
                "manage-artifacts requires the workspace.persistence provider",
                error_code="CAPABILITY_UNAVAILABLE",
            )
        self._config = config
        self._admission = admission
        self._persistence = persistence
        self._store = ArtifactCustodyStore(persistence, config.workspace_path)
        self._custody_root = config.effective_custody_root
        (self._custody_root / "staging").mkdir(parents=True, exist_ok=True)
        (self._custody_root / "objects").mkdir(parents=True, exist_ok=True)
        self._closed = False

    @property
    def store(self) -> ArtifactCustodyStore:
        """Return the feature-owned bounded persistence store."""
        return self._store

    @property
    def custody_root(self) -> Path:
        """Return the configured custody root (operational diagnostic)."""
        return self._custody_root

    def close(self) -> None:
        """Release runtime custody resources idempotently.

        Committed artifacts and durable metadata are retained; teardown
        never purges custody state.
        """
        if self._closed:
            return
        self._closed = True
        logger.info("artifact custody service closed", extra={"namespace": NAMESPACE})

    def _require_open(self) -> None:
        """Fail closed when the service is used after close.

        Raises:
            WorkspaceError: If the scope is already closed.
        """
        if self._closed:
            raise WorkspaceError(
                "artifact custody service is closed",
                error_code="ARTIFACT_SCOPE_CLOSED",
            )

    async def _admit(
        self,
        *,
        operation: ManageArtifactsOperation,
        request_id: str,
        memory_bytes: int,
        temp_disk_bytes: int,
    ) -> str:
        """Acquire one finite admission lease for a heavy operation.

        Args:
            operation: Heavy operation requesting admission.
            request_id: Calling request identity for lease derivation.
            memory_bytes: Finite memory requirement.
            temp_disk_bytes: Finite temporary disk requirement.

        Returns:
            The admitted lease identity for release.

        Raises:
            ArtifactAdmissionUnavailableError: When the port is absent or
                the decision is not ADMITTED.
        """
        if self._admission is None:
            raise ArtifactAdmissionUnavailableError(
                operation,
                "orchestration.resource-admission provider not mounted",
            )
        decision = await self._admission.admit(
            ResourceAdmissionRequest(
                request_id=f"{request_id}:admission",
                owner_id="FEAT-WS-MANAGE_ARTIFACTS",
                work_id=f"{operation.value.lower()}:{request_id}",
                idempotency_key=f"artifacts:{request_id}",
                profile=FiniteResourceProfile(
                    memory_bytes=memory_bytes,
                    temp_disk_bytes=temp_disk_bytes,
                ),
                work_class=WorkClass.BULK,
            )
        )
        if decision.status is not AdmissionStatus.ADMITTED or decision.lease is None:
            reason = decision.reason or decision.status.value
            raise ArtifactAdmissionUnavailableError(
                operation,
                f"admission decision not admitted: {reason}",
            )
        return decision.lease.lease_id

    async def _release(self, lease_id: str) -> None:
        """Release one admission lease, logging (not raising) failures."""
        if self._admission is None:
            return
        released = await self._admission.release(lease_id)
        if not released:
            logger.warning(
                "artifact custody lease release reported not-released",
                extra={"error_code": "ARTIFACT_LEASE_RELEASE_MISSED"},
            )

    def _append_evidence(
        self,
        *,
        workspace_id: str,
        payload: dict[str, Any],
    ) -> str:
        """Append one immutable custody evidence record.

        Args:
            workspace_id: Owning workspace scope, or the custody
                namespace scope for workspace-wide maintenance receipts.
            payload: Bounded secret-safe receipt mapping whose JSON is
                hashed into the record's content hash.

        Returns:
            The stored evidence identity.
        """
        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        record = EvidenceRecord(
            evidence_id=_evidence_id("artifact-custody"),
            workspace_id=workspace_id,
            namespace=NAMESPACE,
            content_hash=_hash_payload(payload_json.encode("utf-8")),
            payload_json=payload_json,
            created_at=_utc_now_iso(),
        )
        stored = self._persistence.append_evidence(
            workspace_path=self._config.workspace_path,
            namespace=NAMESPACE,
            evidence=record,
        )
        return stored.evidence_id

    def _receipt_from_row(self, row: dict[str, Any]) -> CustodyReceipt:
        """Build the immutable custody receipt for one publication row.

        Returns:
            Custody receipt carrying the row's frozen publication facts.
        """
        return CustodyReceipt(
            artifact_id=str(row["artifact_id"]),
            content_hash=str(row["content_hash"]),
            byte_count=int(row["byte_count"]),
            schema_declaration=str(row["schema_declaration"]),
            idempotency_key=str(row["idempotency_key"]),
            storage_revision=int(row["custody_revision"]),
            published_at=str(row["published_at"]),
        )

    def _verify_published_object(self, row: dict[str, Any]) -> None:
        """Fail closed unless the published object bytes verify.

        Raises:
            ArtifactIntegrityError: When the object is missing, is a
                symlink/reparse point, or fails checksum verification.
        """
        artifact_id = str(row["artifact_id"])
        object_path = _object_path(self._custody_root, str(row["content_hash"]))
        if object_path.is_symlink():
            raise ArtifactIntegrityError(artifact_id, "object path is a symlink")
        if not object_path.is_file():
            raise ArtifactIntegrityError(artifact_id, "object bytes absent")
        byte_count, content_hash = _verify_file(object_path, artifact_id)
        if byte_count != int(row["byte_count"]) or content_hash != str(
            row["content_hash"]
        ):
            raise ArtifactIntegrityError(artifact_id, "object checksum mismatch")

    async def publish_artifact(
        self,
        request: PublishArtifactRequest,
    ) -> CustodyReceipt:
        """Stage, validate, and atomically publish one artifact.

        Args:
            request: Validated publication request with bounded payload.

        Returns:
            The immutable custody receipt for the published artifact.

        Raises:
            ArtifactValidationError: When declared byte count, hash,
                schema, or size-cap validation fails.
            ArtifactPublicationConflictError: On identity or idempotency
                conflicts with immutable custody state.
            ArtifactIntegrityError: When staged or published bytes fail
                verification.
            ArtifactAdmissionUnavailableError: When admission is not
                available for the heavy publication.
            WorkspaceError: On durable storage failures.
        """
        self._require_open()
        publication = request.publication
        payload = request.payload
        if publication.byte_count != len(payload):
            raise ArtifactValidationError(
                "declared byte_count does not match payload length",
                field="byte_count",
            )
        if len(payload) > self._config.max_artifact_bytes:
            raise ArtifactValidationError(
                "payload exceeds the configured finite artifact size cap",
                field="payload",
            )
        actual_hash = _hash_payload(payload)
        if actual_hash != publication.content_hash:
            raise ArtifactValidationError(
                "declared content_hash does not match payload bytes",
                field="content_hash",
            )
        fingerprint = _publication_fingerprint(
            artifact_id=publication.artifact_id,
            workspace_id=publication.workspace_id,
            account_id=publication.account_id,
            schema_declaration=publication.schema_declaration,
            byte_count=publication.byte_count,
            content_hash=publication.content_hash,
            idempotency_key=publication.idempotency_key,
            source_reference=publication.source_reference,
        )

        existing = self._store.find_publication(
            request_id=request.request_id,
            workspace_id=publication.workspace_id,
            idempotency_key=publication.idempotency_key,
        )
        if existing is not None:
            if str(existing["idempotency_fingerprint"]) != fingerprint:
                raise ArtifactPublicationConflictError(
                    publication.artifact_id,
                    "idempotency key replayed with changed semantics",
                )
            self._verify_published_object(existing)
            return self._receipt_from_row(existing)
        by_identity = self._store.find_publication(
            request_id=request.request_id,
            workspace_id=publication.workspace_id,
            artifact_id=publication.artifact_id,
        )
        if by_identity is not None:
            if str(by_identity["content_hash"]) != publication.content_hash:
                raise ArtifactPublicationConflictError(
                    publication.artifact_id,
                    "artifact identity already published with different content",
                )
            self._verify_published_object(by_identity)
            return self._receipt_from_row(by_identity)

        lease_id = await self._admit(
            operation=ManageArtifactsOperation.PUBLISH_ARTIFACT,
            request_id=request.request_id,
            memory_bytes=max(len(payload), 1),
            temp_disk_bytes=2 * len(payload),
        )
        try:
            return await self._publish_under_lease(
                request=request,
                fingerprint=fingerprint,
            )
        finally:
            await self._release(lease_id)

    async def _publish_under_lease(
        self,
        *,
        request: PublishArtifactRequest,
        fingerprint: str,
    ) -> CustodyReceipt:
        """Execute the admitted staging/verification/finalization sequence.

        Returns:
            The durable custody receipt for the published artifact.

        Raises:
            ArtifactPublicationConflictError: On idempotency conflicts
                with durable staging state.
            ArtifactIntegrityError: When staged or published bytes fail
                verification.
            WorkspaceError: On durable storage failures.
        """
        publication = request.publication
        staging_row = self._store.find_staging(
            request_id=request.request_id,
            workspace_id=publication.workspace_id,
            idempotency_key=publication.idempotency_key,
        )
        if staging_row is not None and (
            str(staging_row["idempotency_fingerprint"]) != fingerprint
        ):
            raise ArtifactPublicationConflictError(
                publication.artifact_id,
                "staging idempotency key replayed with changed semantics",
            )
        if staging_row is None:
            staging_id = uuid.uuid4().hex
            now = _utc_now_iso()
            self._store.insert_staging(
                request_id=request.request_id,
                row={
                    "staging_id": staging_id,
                    "artifact_id": publication.artifact_id,
                    "workspace_id": publication.workspace_id,
                    "account_id": publication.account_id,
                    "schema_declaration": publication.schema_declaration,
                    "byte_count": publication.byte_count,
                    "content_hash": publication.content_hash,
                    "idempotency_key": publication.idempotency_key,
                    "idempotency_fingerprint": fingerprint,
                    "source_reference": publication.source_reference,
                    "created_at": now,
                },
            )
        else:
            staging_id = str(staging_row["staging_id"])

        staging_file = _staging_path(self._custody_root, staging_id)
        object_file = _object_path(self._custody_root, publication.content_hash)
        if staging_row is None or (
            str(staging_row["state"]) == ArtifactCustodyState.STAGING_INCOMPLETE
        ):
            _write_staged_file(staging_file, request.payload)
            staged_count, staged_hash = _verify_file(
                staging_file, publication.artifact_id
            )
            if (
                staged_count != publication.byte_count
                or staged_hash != publication.content_hash
            ):
                raise ArtifactIntegrityError(
                    publication.artifact_id,
                    "staged bytes failed re-read verification",
                )
            self._store.mark_staging_bytes_ready(
                request_id=request.request_id,
                staging_id=staging_id,
                updated_at=_utc_now_iso(),
            )

        if not object_file.exists():
            object_file.parent.mkdir(parents=True, exist_ok=True)
            # os.replace is the same-volume atomic rename on Windows;
            # the async pathlib variant is avoided deliberately here.
            os.replace(staging_file, object_file)  # noqa: PTH105
            _fsync_directory(object_file.parent)

        result = self._store.finalize_publication(
            request_id=request.request_id,
            staging_id=staging_id,
        )
        published = self._store.find_publication(
            request_id=request.request_id,
            workspace_id=publication.workspace_id,
            idempotency_key=publication.idempotency_key,
        )
        if published is None:
            raise ArtifactIntegrityError(
                publication.artifact_id,
                "durable publication metadata absent after finalization",
            )
        if result.rows_affected == _FINALIZE_APPLIED_ROWS:
            self._append_evidence(
                workspace_id=publication.workspace_id,
                payload={
                    "artifact_id": publication.artifact_id,
                    "byte_count": publication.byte_count,
                    "content_hash": publication.content_hash,
                    "custody_revision": int(published["custody_revision"]),
                    "event": "custody_receipt",
                    "idempotency_key": publication.idempotency_key,
                    "schema_declaration": publication.schema_declaration,
                },
            )
            logger.info(
                "artifact published",
                extra={
                    "artifact_id": publication.artifact_id,
                    "byte_count": publication.byte_count,
                    "error_code": "ARTIFACT_PUBLISHED",
                },
            )
        self._verify_published_object(published)
        return self._receipt_from_row(published)

    async def inspect_artifact(
        self,
        request: InspectArtifactRequest,
    ) -> ArtifactRecord:
        """Return one artifact's custody metadata.

        Args:
            request: Validated inspection request.

        Returns:
            The published artifact's custody metadata.

        Raises:
            ArtifactNotFoundError: When no published artifact exists in
                the requested scope.
        """
        self._require_open()
        row = self._store.find_publication(
            request_id=request.request_id,
            workspace_id=request.workspace_id,
            artifact_id=request.artifact_id,
        )
        if row is None or str(row["workspace_id"]) != request.workspace_id:
            raise ArtifactNotFoundError(request.artifact_id)
        retention = self._store.retention_state(
            request_id=request.request_id,
            workspace_id=request.workspace_id,
            artifact_id=request.artifact_id,
        )
        reference_count = self._store.reference_count(
            request_id=request.request_id,
            workspace_id=request.workspace_id,
            artifact_id=request.artifact_id,
        )
        return ArtifactRecord(
            artifact_id=request.artifact_id,
            workspace_id=str(row["workspace_id"]),
            account_id=str(row["account_id"]),
            schema_declaration=str(row["schema_declaration"]),
            byte_count=int(row["byte_count"]),
            content_hash=str(row["content_hash"]),
            state=ArtifactCustodyState(str(row["state"])),
            reference_count=reference_count,
            legal_hold=bool(retention["legal_hold"]) if retention else False,
            storage_revision=int(retention["revision"]) if retention else 1,
            published_at=str(row["published_at"]),
        )

    async def authorize_download(
        self,
        request: AuthorizeDownloadRequest,
    ) -> DownloadGrant:
        """Create one bounded durable download grant.

        Args:
            request: Validated grant authorization request.

        Returns:
            The durable bounded download grant.

        Raises:
            ArtifactNotFoundError: When the artifact is not published in
                the requested scope.
            ArtifactValidationError: When the TTL exceeds the configured
                bounded maximum.
        """
        self._require_open()
        if request.ttl_seconds > self._config.grant_max_ttl_seconds:
            raise ArtifactValidationError(
                "ttl_seconds exceeds the configured bounded maximum",
                field="ttl_seconds",
            )
        row = self._store.find_publication(
            request_id=request.request_id,
            workspace_id=request.workspace_id,
            artifact_id=request.artifact_id,
        )
        if row is None:
            raise ArtifactNotFoundError(request.artifact_id)
        retention = self._store.retention_state(
            request_id=request.request_id,
            workspace_id=request.workspace_id,
            artifact_id=request.artifact_id,
        )
        generation = int(retention["revision"]) if retention else 1
        grant_id = uuid.uuid4().hex
        expires_at = (
            datetime.now(UTC) + timedelta(seconds=request.ttl_seconds)
        ).isoformat(timespec="microseconds")
        self._store.insert_grant(
            request_id=request.request_id,
            row={
                "grant_id": grant_id,
                "workspace_id": request.workspace_id,
                "artifact_id": request.artifact_id,
                "account_id": request.account_id,
                "principal_id": request.principal_id,
                "action": "DOWNLOAD",
                "expires_at": expires_at,
                "generation": generation,
                "created_at": _utc_now_iso(),
            },
        )
        return DownloadGrant(
            grant_id=grant_id,
            artifact_id=request.artifact_id,
            workspace_id=request.workspace_id,
            account_id=request.account_id,
            principal_id=request.principal_id,
            action="DOWNLOAD",
            expires_at=expires_at,
            generation=generation,
        )

    async def resolve_download(
        self,
        request: ResolveDownloadRequest,
    ) -> ResolvedDownload:
        """Resolve one bounded grant into verified artifact bytes.

        Args:
            request: Validated resolution request carrying the grant.

        Returns:
            Authorized bytes whose payload hashes to the stored checksum.

        Raises:
            ArtifactAccessDeniedError: On scope, principal, generation,
                or durable-state denial.
            ArtifactGrantExpiredError: When the grant has expired.
            ArtifactNotFoundError: When the artifact identity is unknown.
            ArtifactIntegrityError: When custody bytes fail verification.
        """
        self._require_open()
        grant = request.grant
        row = self._store.find_grant(
            request_id=request.request_id,
            grant_id=grant.grant_id,
        )
        self._validate_grant_durable_state(request=request, row=row)
        publication = self._store.find_publication(
            request_id=request.request_id,
            workspace_id=grant.workspace_id,
            artifact_id=grant.artifact_id,
        )
        if publication is None:
            raise ArtifactNotFoundError(grant.artifact_id)
        retention = self._store.retention_state(
            request_id=request.request_id,
            workspace_id=grant.workspace_id,
            artifact_id=grant.artifact_id,
        )
        current_generation = int(retention["revision"]) if retention else 1
        if current_generation != grant.generation:
            raise ArtifactAccessDeniedError(
                grant.artifact_id,
                "authorization generation is stale for current retention state",
            )
        self._verify_published_object(publication)
        object_file = _object_path(self._custody_root, str(publication["content_hash"]))
        try:
            payload = object_file.read_bytes()
        except OSError as error:
            message = f"custody bytes unreadable (errno={error.errno})"
            raise ArtifactIntegrityError(
                grant.artifact_id,
                message,
            ) from error
        return ResolvedDownload(
            artifact_id=grant.artifact_id,
            content_hash=str(publication["content_hash"]),
            byte_count=int(publication["byte_count"]),
            schema_declaration=str(publication["schema_declaration"]),
            payload=payload,
        )

    def _validate_grant_durable_state(
        self,
        *,
        request: ResolveDownloadRequest,
        row: dict[str, Any] | None,
    ) -> None:
        """Fail closed unless the presented grant matches durable state.

        Args:
            request: Resolution request carrying the presented grant.
            row: Durable grant row for the presented grant identity.

        Raises:
            ArtifactAccessDeniedError: On unknown identity, field drift,
                revocation, scope mismatch, or generation drift.
            ArtifactGrantExpiredError: When the grant has expired.
        """
        grant = request.grant
        if row is None:
            raise ArtifactAccessDeniedError(
                grant.artifact_id,
                "grant identity has no durable authorization",
            )
        durable_fields = (
            "artifact_id",
            "workspace_id",
            "account_id",
            "principal_id",
            "action",
            "expires_at",
        )
        for field_name in durable_fields:
            if str(row[field_name]) != getattr(grant, field_name):
                raise ArtifactAccessDeniedError(
                    grant.artifact_id,
                    "presented grant does not match durable authorization",
                )
        if int(row["generation"]) != grant.generation:
            raise ArtifactAccessDeniedError(
                grant.artifact_id,
                "presented grant generation does not match durable state",
            )
        if int(row["revoked"]) != 0:
            raise ArtifactAccessDeniedError(grant.artifact_id, "grant revoked")
        if (
            request.workspace_id != grant.workspace_id
            or request.account_id != grant.account_id
            or request.principal_id != grant.principal_id
        ):
            raise ArtifactAccessDeniedError(
                grant.artifact_id,
                "resolution scope does not match grant scope",
            )
        expiry = datetime.fromisoformat(grant.expires_at)
        if datetime.now(UTC) >= expiry:
            raise ArtifactGrantExpiredError(grant.grant_id, grant.expires_at)

    async def add_reference(
        self,
        request: AddReferenceRequest,
    ) -> ArtifactReference:
        """Retain an artifact under one new semantic reference.

        Args:
            request: Validated add-reference request.

        Returns:
            The stored semantic reference.

        Raises:
            ArtifactNotFoundError: When the artifact is not published.
            WorkspaceError: When the reference already exists.
        """
        self._require_open()
        reference = request.reference
        publication = self._store.find_publication(
            request_id=request.request_id,
            workspace_id=request.workspace_id,
            artifact_id=reference.artifact_id,
        )
        if publication is None:
            raise ArtifactNotFoundError(reference.artifact_id)
        self._store.insert_reference(
            request_id=request.request_id,
            reference_id=reference.reference_id,
            workspace_id=request.workspace_id,
            artifact_id=reference.artifact_id,
            owner_namespace=reference.owner_namespace,
            owner_record_id=reference.owner_record_id,
            created_at=_utc_now_iso(),
        )
        return reference

    async def remove_reference(
        self,
        request: RemoveReferenceRequest,
    ) -> int:
        """Remove one semantic reference under a revision fence.

        Artifact bytes are never deleted by reference removal.

        Args:
            request: Validated remove-reference request.

        Returns:
            The artifact's storage revision after removal.

        Raises:
            ArtifactNotFoundError: When the reference is unknown.
            RevisionConflictError: When the expected revision is stale.
        """
        self._require_open()
        existing = self._store.find_reference(
            request_id=request.request_id,
            reference_id=request.reference_id,
        )
        if existing is None:
            raise ArtifactNotFoundError(request.reference_id)
        reference_workspace = str(existing["workspace_id"])
        reference_artifact = str(existing["artifact_id"])
        result = self._store.remove_reference(
            request_id=request.request_id,
            reference_id=request.reference_id,
            workspace_id=reference_workspace,
            artifact_id=reference_artifact,
            expected_revision=request.expected_revision,
            updated_at=_utc_now_iso(),
        )
        if result.rows_affected != _REMOVE_REFERENCE_APPLIED_ROWS:
            retention = self._store.retention_state(
                request_id=request.request_id,
                workspace_id=reference_workspace,
                artifact_id=reference_artifact,
            )
            raise RevisionConflictError(
                namespace=NAMESPACE,
                expected=request.expected_revision,
                actual=int(retention["revision"]) if retention else 1,
            )
        retention = self._store.retention_state(
            request_id=request.request_id,
            workspace_id=reference_workspace,
            artifact_id=reference_artifact,
        )
        return int(retention["revision"]) if retention else 1

    async def set_legal_hold(
        self,
        request: SetLegalHoldRequest,
    ) -> int:
        """Set or clear one artifact's legal hold under a revision fence.

        Args:
            request: Validated legal-hold request.

        Returns:
            The artifact's storage revision after the change.

        Raises:
            ArtifactNotFoundError: When the artifact is unknown.
            RevisionConflictError: When the expected revision is stale.
        """
        self._require_open()
        publication = self._store.find_publication(
            request_id=request.request_id,
            workspace_id=request.workspace_id,
            artifact_id=request.artifact_id,
        )
        if publication is None:
            raise ArtifactNotFoundError(request.artifact_id)
        result = self._store.set_legal_hold(
            request_id=request.request_id,
            workspace_id=request.workspace_id,
            artifact_id=request.artifact_id,
            hold=request.hold,
            expected_revision=request.expected_revision,
            updated_at=_utc_now_iso(),
        )
        if result.rows_affected != 1:
            retention = self._store.retention_state(
                request_id=request.request_id,
                workspace_id=request.workspace_id,
                artifact_id=request.artifact_id,
            )
            raise RevisionConflictError(
                namespace=NAMESPACE,
                expected=request.expected_revision,
                actual=int(retention["revision"]) if retention else 1,
            )
        retention = self._store.retention_state(
            request_id=request.request_id,
            workspace_id=request.workspace_id,
            artifact_id=request.artifact_id,
        )
        return int(retention["revision"]) if retention else 1

    async def reconcile_custody(
        self,
        request: ReconcileCustodyRequest,
    ) -> CustodyReconciliationReport:
        """Run admitted custody maintenance and eligible cleanup.

        Args:
            request: Validated reconciliation request.

        Returns:
            The bounded audit report for the reconciliation run.

        Raises:
            ArtifactAdmissionUnavailableError: When admission is not
                available for maintenance.
            WorkspaceError: On durable storage failures.
        """
        self._require_open()
        lease_id = await self._admit(
            operation=ManageArtifactsOperation.RECONCILE_CUSTODY,
            request_id=request.request_id,
            memory_bytes=_RECONCILE_MEMORY_BYTES,
            temp_disk_bytes=_RECONCILE_TEMP_DISK_BYTES,
        )
        try:
            return self._reconcile_under_lease(request)
        finally:
            await self._release(lease_id)

    def _reconcile_under_lease(
        self,
        request: ReconcileCustodyRequest,
    ) -> CustodyReconciliationReport:
        """Execute the admitted bounded reconciliation sequence.

        Returns:
            The audit report for this bounded reconciliation run.

        Raises:
            WorkspaceError: On durable storage or custody I/O failures.
        """
        limit = self._config.cleanup_batch_limit
        finalized: list[str] = []
        integrity_incidents: list[str] = []

        pending_rows = self._store.staging_scan(
            request_id=request.request_id,
            state=ArtifactCustodyState.BYTES_READY_METADATA_PENDING.value,
            limit=limit,
        )
        revision = 0
        for row in pending_rows:
            artifact_id = str(row["artifact_id"])
            object_file = _object_path(self._custody_root, str(row["content_hash"]))
            if not object_file.is_file() or object_file.is_symlink():
                integrity_incidents.append(artifact_id)
                continue
            byte_count, content_hash = _verify_file(object_file, artifact_id)
            if byte_count != int(row["byte_count"]) or content_hash != str(
                row["content_hash"]
            ):
                integrity_incidents.append(artifact_id)
                continue
            result = self._store.finalize_publication(
                request_id=request.request_id,
                staging_id=str(row["staging_id"]),
            )
            revision = max(revision, result.new_revision)
            if result.rows_affected == _FINALIZE_APPLIED_ROWS:
                finalized.append(artifact_id)
                logger.info(
                    "pending artifact publication finalized",
                    extra={
                        "artifact_id": artifact_id,
                        "error_code": "ARTIFACT_FINALIZED",
                    },
                )

        removed_staging, staging_revision = self._clean_expired_staging(
            request.request_id, limit
        )
        revision = max(revision, staging_revision)
        removed_orphans = self._remove_orphan_objects(request.request_id, limit)

        for row in self._store.publications_missing_objects(
            request_id=request.request_id,
            limit=limit,
        ):
            object_file = _object_path(self._custody_root, str(row["content_hash"]))
            if not object_file.is_file():
                integrity_incidents.append(str(row["artifact_id"]))
        if integrity_incidents:
            logger.warning(
                "artifact custody integrity incidents detected",
                extra={
                    "count": len(integrity_incidents),
                    "error_code": "ARTIFACT_INTEGRITY",
                },
            )

        finalized_ids = tuple(finalized)
        removed_staging_ids = tuple(removed_staging)
        removed_orphan_ids = tuple(removed_orphans)
        incident_ids = tuple(sorted(set(integrity_incidents)))
        retained_referenced = self._store.referenced_artifacts(
            request_id=request.request_id,
            limit=limit,
        )
        retained_legal_hold = self._store.held_artifacts(
            request_id=request.request_id,
            limit=limit,
        )
        receipt_evidence_id = self._append_evidence(
            workspace_id=NAMESPACE,
            payload={
                "event": "custody_reconciliation",
                "finalized": list(finalized_ids),
                "integrity_incidents": list(incident_ids),
                "removed_orphan_objects": list(removed_orphan_ids),
                "removed_staging": list(removed_staging_ids),
                "retained_legal_hold": list(retained_legal_hold),
                "retained_referenced": list(retained_referenced),
            },
        )
        return CustodyReconciliationReport(
            finalized=finalized_ids,
            removed_staging=removed_staging_ids,
            removed_orphan_objects=removed_orphan_ids,
            retained_referenced=retained_referenced,
            retained_legal_hold=retained_legal_hold,
            integrity_incidents=incident_ids,
            revision=revision,
            receipt_evidence_id=receipt_evidence_id,
        )

    def _clean_expired_staging(
        self, request_id: str, limit: int
    ) -> tuple[list[str], int]:
        """Remove expired incomplete staging rows and their files.

        Deletion is fenced on the staging state and age so a row that
        transitioned after the scan is never removed.

        Args:
            request_id: Fresh transaction identity prefix.
            limit: Bound on rows examined and removed.

        Returns:
            Tuple of removed staging identities and the latest durable
            namespace revision touched by the cleanup.

        Raises:
            WorkspaceError: When an expired staging file deletion fails.
        """
        cutoff = (
            datetime.now(UTC) - timedelta(seconds=self._config.staging_max_age_seconds)
        ).isoformat(timespec="microseconds")
        expired_rows = self._store.staging_scan(
            request_id=request_id,
            state=ArtifactCustodyState.STAGING_INCOMPLETE.value,
            created_before=cutoff,
            limit=limit,
        )
        removed: list[str] = []
        revision = 0
        for row in expired_rows:
            staging_id = str(row["staging_id"])
            drop_result = self._store.delete_staging_guarded(
                request_id=request_id,
                staging_id=staging_id,
                expected_state=ArtifactCustodyState.STAGING_INCOMPLETE.value,
                created_before=cutoff,
            )
            if drop_result.rows_affected != 1:
                continue
            staging_file = _staging_path(self._custody_root, staging_id)
            try:
                staging_file.unlink(missing_ok=True)
            except OSError as error:
                message = f"expired staging cleanup failed: {error.errno}"
                raise WorkspaceError(
                    message,
                    error_code="ARTIFACT_STORAGE_ERROR",
                ) from error
            removed.append(staging_id)
            revision = max(revision, drop_result.new_revision)
        return removed, revision

    def _scan_orphan_candidates(self, limit: int) -> list[tuple[str, Path]]:
        objects_root = self._custody_root / "objects"
        candidates: list[tuple[str, Path]] = []
        try:
            shard_dirs = sorted(objects_root.iterdir())
        except OSError:
            return []
        for shard in shard_dirs:
            if not shard.is_dir() or shard.is_symlink():
                continue
            for entry in sorted(shard.iterdir()):
                if (
                    entry.is_file()
                    and not entry.is_symlink()
                    and entry.suffix == ".bin"
                ):
                    candidates.append((entry.stem, entry))
                    if len(candidates) >= limit:
                        break
            if len(candidates) >= limit:
                break
        return candidates

    def _remove_orphan_objects(self, request_id: str, limit: int) -> list[str]:
        """Remove bounded object files with no durable publication or staging.

        A file is an orphan only when no catalog row and no staging row
        references its content hash; because publication always creates
        its staging row before producing the object file, a live
        publication can never lose its bytes to this scan.

        Args:
            request_id: Fresh read identity for catalog lookups.
            limit: Bound on files examined and removed.

        Returns:
            Removed content digests, in scan order.

        Raises:
            WorkspaceError: When an orphan deletion fails.
        """
        candidates = self._scan_orphan_candidates(limit)
        if not candidates:
            return []
        hashes = tuple(f"sha256:{name}" for name, _ in candidates)
        published = self._store.published_content_hashes(
            request_id=request_id,
            content_hashes=hashes,
        )
        staging = self._store.staging_content_hashes(
            request_id=request_id,
            content_hashes=hashes,
        )
        removed: list[str] = []
        for name, path in candidates:
            content_hash = f"sha256:{name}"
            if content_hash in published or content_hash in staging:
                continue
            try:
                path.unlink(missing_ok=True)
            except OSError as error:
                message = f"orphan object cleanup failed: {error.errno}"
                raise WorkspaceError(
                    message,
                    error_code="ARTIFACT_STORAGE_ERROR",
                ) from error
            removed.append(name)
        return removed
