"""Exact functional traceability evidence for FEAT-WS-MANAGE_ARTIFACTS.

Binds ``AT-WS-MANAGE_ARTIFACTS-001/002/003`` to named assertions against
the ``workspace.artifacts@1`` provider composed with the real
``workspace.persistence@1`` and ``orchestration.resource-admission@1``
providers (the admission provider uses synthetic host capacity so the
evidence is offline and deterministic).
"""

from __future__ import annotations

import hashlib
import sqlite3
import tempfile
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid7

import pytest
from app.contracts.workspace.artifacts import (
    AddReferenceRequest,
    ArtifactAccessDeniedError,
    ArtifactAdmissionUnavailableError,
    ArtifactGrantExpiredError,
    ArtifactIntegrityError,
    ArtifactNotFoundError,
    ArtifactPublication,
    ArtifactPublicationConflictError,
    ArtifactReference,
    ArtifactValidationError,
    AuthorizeDownloadRequest,
    DownloadGrant,
    InspectArtifactRequest,
    PublishArtifactRequest,
    ReconcileCustodyRequest,
    RemoveReferenceRequest,
    ResolveDownloadRequest,
    SetLegalHoldRequest,
)
from app.contracts.workspace.errors import RevisionConflictError
from app.services.orchestration.reserve_resources._persistence import (
    ResourceReservationStore,
)
from app.services.orchestration.reserve_resources.reserve_resources import (
    ReserveResourcesService,
)
from app.services.workspace.execute_persistence.execute_persistence import (
    ExecutePersistenceService,
)
from app.services.workspace.manage_artifacts._persistence import ArtifactCustodyStore
from app.services.workspace.manage_artifacts.config import ManageArtifactsConfig
from app.services.workspace.manage_artifacts.manage_artifacts import (
    ManageArtifactsService,
    _object_path,
    _publication_fingerprint,
    _staging_path,
)

_WORKSPACE = "trace-workspace"
_ACCOUNT = "trace-account"
_PRINCIPAL = "trace-principal"
_PAYLOAD = b"traceability artifact payload\n" * 6


def _hash(payload: bytes) -> str:
    """Return the canonical wire content hash for one payload."""
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _admission(*, free_disk_bytes: int = 50 * 1024**3) -> ReserveResourcesService:
    """Build the real admission provider with synthetic host capacity."""
    return ReserveResourcesService(
        store=ResourceReservationStore(),
        total_disk_bytes=100 * 1024**3,
        free_disk_bytes=free_disk_bytes,
    )


def _service(
    root: Path,
    *,
    admission: ReserveResourcesService | None = None,
) -> ManageArtifactsService:
    """Compose one artifact custody service over a temporary workspace."""
    return ManageArtifactsService(
        config=ManageArtifactsConfig(database_path=root),
        persistence=ExecutePersistenceService(),
        admission=admission,
    )


def _publication(
    artifact_id: str,
    *,
    payload: bytes = _PAYLOAD,
    idempotency_key: str | None = None,
) -> ArtifactPublication:
    """Build one publication declaration for evidence."""
    return ArtifactPublication(
        artifact_id=artifact_id,
        workspace_id=_WORKSPACE,
        account_id=_ACCOUNT,
        schema_declaration="application/octet-stream",
        byte_count=len(payload),
        content_hash=_hash(payload),
        idempotency_key=idempotency_key or f"key-{artifact_id}",
        source_reference="run-0001",
    )


def _publish(
    artifact_id: str,
    *,
    payload: bytes = _PAYLOAD,
    idempotency_key: str | None = None,
) -> PublishArtifactRequest:
    """Build one bounded publication request."""
    return PublishArtifactRequest(
        request_id=str(uuid7()),
        actor_id=_PRINCIPAL,
        publication=_publication(
            artifact_id,
            payload=payload,
            idempotency_key=idempotency_key,
        ),
        payload=payload,
    )


def _inspect(artifact_id: str) -> InspectArtifactRequest:
    """Build one bounded inspection request."""
    return InspectArtifactRequest(
        request_id=str(uuid7()),
        actor_id=_PRINCIPAL,
        artifact_id=artifact_id,
        workspace_id=_WORKSPACE,
        account_id=_ACCOUNT,
    )


def _past_iso(seconds: int) -> str:
    """Return one fixed-width ISO timestamp in the past."""
    return (datetime.now(UTC) - timedelta(seconds=seconds)).isoformat(
        timespec="microseconds"
    )


def _db_value(root: Path, sql: str, parameters: tuple[object, ...]) -> object:
    """Run one read-only SQL scalar against the workspace database."""
    connection = sqlite3.connect(root / "database" / "haruquantai.db")
    try:
        return connection.execute(sql, parameters).fetchone()[0]
    finally:
        connection.close()


def _write_staging_file(
    service: ManageArtifactsService, staging_id: str, payload: bytes
) -> None:
    """Write one crash-fixture staging file inside the custody root."""
    staging_file = _staging_path(service.custody_root, staging_id)
    staging_file.parent.mkdir(parents=True, exist_ok=True)
    staging_file.write_bytes(payload)


def _raw_staging_row(
    service: ManageArtifactsService,
    *,
    state: str,
    created_at: str,
    staging_id: str,
    artifact_id: str,
    payload: bytes,
) -> None:
    """Insert one crash-fixture staging row through the feature store."""
    store: ArtifactCustodyStore = service.store
    idempotency_key = f"key-{artifact_id}"
    fingerprint = _publication_fingerprint(
        artifact_id=artifact_id,
        workspace_id=_WORKSPACE,
        account_id=_ACCOUNT,
        schema_declaration="application/octet-stream",
        byte_count=len(payload),
        content_hash=_hash(payload),
        idempotency_key=idempotency_key,
        source_reference="run-0001",
    )
    store.insert_staging(
        request_id=str(uuid7()),
        row={
            "staging_id": staging_id,
            "artifact_id": artifact_id,
            "workspace_id": _WORKSPACE,
            "account_id": _ACCOUNT,
            "schema_declaration": "application/octet-stream",
            "byte_count": len(payload),
            "content_hash": _hash(payload),
            "idempotency_key": idempotency_key,
            "idempotency_fingerprint": fingerprint,
            "source_reference": "run-0001",
            "created_at": created_at,
        },
    )
    if state == "BYTES_READY_METADATA_PENDING":
        assert store.mark_staging_bytes_ready(
            request_id=str(uuid7()),
            staging_id=staging_id,
            updated_at=created_at,
        )


def _symlink_supported() -> bool:
    """Probe once whether the host permits symlink creation."""
    with tempfile.TemporaryDirectory() as probe:
        target = Path(probe) / "target.bin"
        target.write_bytes(b"probe")
        link = Path(probe) / "link.bin"
        try:
            link.symlink_to(target)
        except OSError:
            return False
        return link.is_symlink()


@pytest.mark.asyncio
async def test_at_ws_manage_artifacts_001_publication_validation_and_idempotency(
    tmp_path: Path,
) -> None:
    """AT-001: validation failures publish nothing; retries are idempotent."""
    root = tmp_path / "workspace"
    root.mkdir()
    service = _service(root, admission=_admission())

    receipt = await service.publish_artifact(_publish("artifact-a"))
    assert receipt.content_hash == _hash(_PAYLOAD)
    assert receipt.byte_count == len(_PAYLOAD)
    assert receipt.storage_revision == 1
    object_file = _object_path(service.custody_root, receipt.content_hash)
    assert object_file.is_file()
    assert not object_file.is_symlink()
    record = await service.inspect_artifact(_inspect("artifact-a"))
    assert record.state.value == "PUBLISHED_VALID"

    bad_hash_request = _publish("artifact-bad-hash")
    bad_hash_request = PublishArtifactRequest(
        request_id=bad_hash_request.request_id,
        actor_id=_PRINCIPAL,
        publication=ArtifactPublication(
            artifact_id="artifact-bad-hash",
            workspace_id=_WORKSPACE,
            account_id=_ACCOUNT,
            schema_declaration="application/octet-stream",
            byte_count=len(_PAYLOAD),
            content_hash=f"sha256:{'0' * 64}",
            idempotency_key="key-artifact-bad-hash",
            source_reference="run-0001",
        ),
        payload=_PAYLOAD,
    )
    with pytest.raises(ArtifactValidationError):
        await service.publish_artifact(bad_hash_request)
    with pytest.raises(ArtifactNotFoundError):
        await service.inspect_artifact(_inspect("artifact-bad-hash"))

    truncated = PublishArtifactRequest(
        request_id=str(uuid7()),
        actor_id=_PRINCIPAL,
        publication=ArtifactPublication(
            artifact_id="artifact-truncated",
            workspace_id=_WORKSPACE,
            account_id=_ACCOUNT,
            schema_declaration="application/octet-stream",
            byte_count=len(_PAYLOAD) + 10,
            content_hash=_hash(_PAYLOAD),
            idempotency_key="key-artifact-truncated",
            source_reference="run-0001",
        ),
        payload=_PAYLOAD,
    )
    with pytest.raises(ArtifactValidationError):
        await service.publish_artifact(truncated)

    with pytest.raises(ArtifactValidationError):
        ArtifactPublication(
            artifact_id="artifact-schema",
            workspace_id=_WORKSPACE,
            account_id=_ACCOUNT,
            schema_declaration="not a media type",
            byte_count=len(_PAYLOAD),
            content_hash=_hash(_PAYLOAD),
            idempotency_key="key-artifact-schema",
            source_reference="run-0001",
        )

    replay = await service.publish_artifact(_publish("artifact-a"))
    assert (replay.artifact_id, replay.content_hash, replay.idempotency_key) == (
        receipt.artifact_id,
        receipt.content_hash,
        receipt.idempotency_key,
    )
    assert (
        _db_value(
            root,
            "SELECT COUNT(*) FROM artifact_publications WHERE artifact_id = ?",
            ("artifact-a",),
        )
        == 1
    )

    changed = _publish(
        "artifact-a",
        payload=b"different bytes entirely",
        idempotency_key="key-artifact-a",
    )
    with pytest.raises(ArtifactPublicationConflictError):
        await service.publish_artifact(changed)

    crash_staging_id = "crashbeforepublication01"
    _raw_staging_row(
        service,
        state="STAGING_INCOMPLETE",
        created_at=_past_iso(7200),
        staging_id=crash_staging_id,
        artifact_id="artifact-crashed",
        payload=_PAYLOAD,
    )
    _write_staging_file(service, crash_staging_id, _PAYLOAD)
    with pytest.raises(ArtifactNotFoundError):
        await service.inspect_artifact(_inspect("artifact-crashed"))

    pending_id = "bytesreadymetadatapending01"
    pending_payload = b"pending finalization payload"
    _raw_staging_row(
        service,
        state="BYTES_READY_METADATA_PENDING",
        created_at=_past_iso(60),
        staging_id=pending_id,
        artifact_id="artifact-pending",
        payload=pending_payload,
    )
    pending_object = _object_path(service.custody_root, _hash(pending_payload))
    pending_object.parent.mkdir(parents=True, exist_ok=True)
    pending_object.write_bytes(pending_payload)
    recovered = await service.publish_artifact(
        _publish("artifact-pending", payload=pending_payload)
    )
    assert recovered.content_hash == _hash(pending_payload)

    restarted = _service(root, admission=_admission())
    retained = await restarted.inspect_artifact(_inspect("artifact-a"))
    assert retained.content_hash == _hash(_PAYLOAD)
    report = await restarted.reconcile_custody(
        ReconcileCustodyRequest(request_id=str(uuid7()), actor_id=_PRINCIPAL)
    )
    assert "artifact-a" not in report.integrity_incidents
    assert crash_staging_id in report.removed_staging
    assert not _staging_path(restarted.custody_root, crash_staging_id).exists()


def _authorize(
    artifact_id: str = "artifact-dl",
    ttl: int = 60,
) -> AuthorizeDownloadRequest:
    """Build one bounded grant-authorization request."""
    return AuthorizeDownloadRequest(
        request_id=str(uuid7()),
        actor_id=_PRINCIPAL,
        artifact_id=artifact_id,
        workspace_id=_WORKSPACE,
        account_id=_ACCOUNT,
        principal_id=_PRINCIPAL,
        ttl_seconds=ttl,
    )


def _resolve(grant: DownloadGrant, **scope: str) -> ResolveDownloadRequest:
    """Build one bounded grant-resolution request."""
    return ResolveDownloadRequest(
        request_id=str(uuid7()),
        grant=grant,
        workspace_id=scope.get("workspace_id", _WORKSPACE),
        account_id=scope.get("account_id", _ACCOUNT),
        principal_id=scope.get("principal_id", _PRINCIPAL),
    )


@pytest.mark.asyncio
async def test_at_ws_manage_artifacts_002_download_authorization(
    tmp_path: Path,
) -> None:
    """AT-002: grants authorize scope; path identities and forgeries fail."""
    root = tmp_path / "workspace"
    root.mkdir()
    service = _service(root, admission=_admission())
    receipt = await service.publish_artifact(_publish("artifact-dl"))

    grant = await service.authorize_download(_authorize())
    resolved = await service.resolve_download(_resolve(grant))
    assert resolved.payload == _PAYLOAD
    assert (
        f"sha256:{hashlib.sha256(resolved.payload).hexdigest()}"
        == receipt.content_hash
        == resolved.content_hash
    )

    past = _past_iso(1)
    expired = replace(grant, expires_at=past)
    connection = sqlite3.connect(root / "database" / "haruquantai.db")
    try:
        connection.execute(
            "UPDATE artifact_grants SET expires_at = ? WHERE grant_id = ?",
            (past, grant.grant_id),
        )
        connection.commit()
    finally:
        connection.close()
    with pytest.raises(ArtifactGrantExpiredError):
        await service.resolve_download(_resolve(expired))

    with pytest.raises(ArtifactAccessDeniedError):
        await service.resolve_download(_resolve(grant, principal_id="other-principal"))
    with pytest.raises(ArtifactAccessDeniedError):
        await service.resolve_download(_resolve(grant, account_id="other-account"))
    with pytest.raises(ArtifactAccessDeniedError):
        await service.resolve_download(_resolve(grant, workspace_id="other-workspace"))

    for path_like in ("../../secret", "C:\\Windows\\system32", "\\\\server\\share\\x"):
        with pytest.raises(ArtifactValidationError):
            AuthorizeDownloadRequest(
                request_id=str(uuid7()),
                actor_id=_PRINCIPAL,
                artifact_id=path_like,
                workspace_id=_WORKSPACE,
                account_id=_ACCOUNT,
                principal_id=_PRINCIPAL,
                ttl_seconds=60,
            )

    forged = replace(grant, generation=grant.generation + 1)
    with pytest.raises(ArtifactAccessDeniedError):
        await service.resolve_download(_resolve(forged))

    unknown = replace(grant, grant_id="0" * 32)
    with pytest.raises(ArtifactAccessDeniedError):
        await service.resolve_download(_resolve(unknown))

    await service.add_reference(
        AddReferenceRequest(
            request_id=str(uuid7()),
            actor_id=_PRINCIPAL,
            workspace_id=_WORKSPACE,
            reference=ArtifactReference(
                reference_id="dl-ref-1",
                artifact_id="artifact-dl",
                owner_namespace="simulation.result",
                owner_record_id="run-0001",
                created_at="",
            ),
        )
    )
    with pytest.raises(ArtifactAccessDeniedError):
        await service.resolve_download(_resolve(grant))


@pytest.mark.skipif(
    not _symlink_supported(), reason="host platform cannot create symlinks"
)
@pytest.mark.asyncio
async def test_at_ws_manage_artifacts_002_symlink_escape_fails_closed(
    tmp_path: Path,
) -> None:
    """AT-002: a symlinked object path never resolves as valid bytes."""
    root = tmp_path / "workspace"
    root.mkdir()
    service = _service(root, admission=_admission())
    receipt = await service.publish_artifact(_publish("artifact-link"))
    object_file = _object_path(service.custody_root, receipt.content_hash)
    outside = root / "outside.bin"
    outside.write_bytes(b"outside custody root")
    object_file.unlink()
    object_file.symlink_to(outside)
    grant = await service.authorize_download(_authorize("artifact-link"))
    with pytest.raises(ArtifactIntegrityError):
        await service.resolve_download(_resolve(grant))


@pytest.mark.asyncio
async def test_at_ws_manage_artifacts_003_retention_and_admitted_cleanup(
    tmp_path: Path,
) -> None:
    """AT-003: references and holds retain; admitted cleanup is audited."""
    root = tmp_path / "workspace"
    root.mkdir()
    service = _service(root, admission=_admission())
    receipt = await service.publish_artifact(_publish("artifact-keep"))

    def _reference(reference_id: str, namespace: str) -> ArtifactReference:
        return ArtifactReference(
            reference_id=reference_id,
            artifact_id="artifact-keep",
            owner_namespace=namespace,
            owner_record_id="record-0001",
            created_at="",
        )

    for reference_id, namespace in (
        ("ref-databank", "databank.membership"),
        ("ref-result", "simulation.result"),
    ):
        await service.add_reference(
            AddReferenceRequest(
                request_id=str(uuid7()),
                actor_id=_PRINCIPAL,
                workspace_id=_WORKSPACE,
                reference=_reference(reference_id, namespace),
            )
        )
    inspected = await service.inspect_artifact(_inspect("artifact-keep"))
    await service.remove_reference(
        RemoveReferenceRequest(
            request_id=str(uuid7()),
            actor_id=_PRINCIPAL,
            reference_id="ref-databank",
            expected_revision=inspected.storage_revision,
        )
    )
    remaining = await service.inspect_artifact(_inspect("artifact-keep"))
    assert remaining.reference_count == 1
    assert _object_path(service.custody_root, receipt.content_hash).is_file()

    with pytest.raises(RevisionConflictError):
        await service.remove_reference(
            RemoveReferenceRequest(
                request_id=str(uuid7()),
                actor_id=_PRINCIPAL,
                reference_id="ref-result",
                expected_revision=inspected.storage_revision,
            )
        )
    await service.set_legal_hold(
        SetLegalHoldRequest(
            request_id=str(uuid7()),
            actor_id=_PRINCIPAL,
            workspace_id=_WORKSPACE,
            artifact_id="artifact-keep",
            hold=True,
            expected_revision=remaining.storage_revision,
        )
    )

    expired_id = "expiredstaging0000000001"
    _raw_staging_row(
        service,
        state="STAGING_INCOMPLETE",
        created_at=_past_iso(7200),
        staging_id=expired_id,
        artifact_id="artifact-expired",
        payload=_PAYLOAD,
    )
    _write_staging_file(service, expired_id, _PAYLOAD)

    uncertain_id = "uncertainpublication00001"
    _raw_staging_row(
        service,
        state="BYTES_READY_METADATA_PENDING",
        created_at=_past_iso(7200),
        staging_id=uncertain_id,
        artifact_id="artifact-uncertain",
        payload=b"uncertain object payload",
    )

    orphan_digest = "ab" + "0" * 62
    orphan_file = service.custody_root / "objects" / "ab" / f"{orphan_digest}.bin"
    orphan_file.parent.mkdir(parents=True, exist_ok=True)
    orphan_file.write_bytes(b"orphan bytes")

    report = await service.reconcile_custody(
        ReconcileCustodyRequest(request_id=str(uuid7()), actor_id=_PRINCIPAL)
    )
    assert expired_id in report.removed_staging
    assert not _staging_path(service.custody_root, expired_id).exists()
    assert orphan_digest in report.removed_orphan_objects
    assert not orphan_file.exists()
    assert "artifact-keep" in report.retained_referenced
    assert "artifact-keep" in report.retained_legal_hold
    assert "artifact-uncertain" in report.integrity_incidents
    assert (
        _db_value(
            root,
            "SELECT COUNT(*) FROM artifact_staging WHERE staging_id = ?",
            (uncertain_id,),
        )
        == 1
    )
    assert report.receipt_evidence_id
    assert _object_path(service.custody_root, receipt.content_hash).is_file()

    refusing = _service(root, admission=_admission(free_disk_bytes=1 * 1024**3))
    with pytest.raises(ArtifactAdmissionUnavailableError):
        await refusing.reconcile_custody(
            ReconcileCustodyRequest(request_id=str(uuid7()), actor_id=_PRINCIPAL)
        )
    with pytest.raises(ArtifactAdmissionUnavailableError):
        await refusing.publish_artifact(_publish("artifact-refused"))

    unadmitted = _service(root)
    with pytest.raises(ArtifactAdmissionUnavailableError):
        await unadmitted.publish_artifact(_publish("artifact-unadmitted"))
    with pytest.raises(ArtifactAdmissionUnavailableError):
        await unadmitted.reconcile_custody(
            ReconcileCustodyRequest(request_id=str(uuid7()), actor_id=_PRINCIPAL)
        )
    assert (
        _db_value(
            root,
            "SELECT COUNT(*) FROM artifact_publications WHERE artifact_id = ?",
            ("artifact-unadmitted",),
        )
        == 0
    )


def test_identity_patterns_reject_path_characters() -> None:
    """Path-like identities fail DTO validation before any effect."""
    for path_like in ("../../secret", "C:\\Windows\\system32", "\\\\server\\share\\x"):
        with pytest.raises(ArtifactValidationError):
            ArtifactPublication(
                artifact_id=path_like,
                workspace_id=_WORKSPACE,
                account_id=_ACCOUNT,
                schema_declaration="application/octet-stream",
                byte_count=len(_PAYLOAD),
                content_hash=_hash(_PAYLOAD),
                idempotency_key="key-path",
                source_reference="run-0001",
            )
    with pytest.raises(ArtifactValidationError):
        ArtifactPublication(
            artifact_id="ok-artifact",
            workspace_id=_WORKSPACE,
            account_id=_ACCOUNT,
            schema_declaration="application/octet-stream",
            byte_count=len(_PAYLOAD),
            content_hash="md5:0123",
            idempotency_key="key-hash",
            source_reference="run-0001",
        )
