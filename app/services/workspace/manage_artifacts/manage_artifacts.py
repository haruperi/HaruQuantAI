"""Immutable artifact custody implementation."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import uuid

from app.contracts.orchestration.resources import (
    AdmissionStatus,
    FiniteResourceProfile,
    ResourceAdmissionPort,
    ResourceAdmissionRequest,
)
from app.contracts.workspace.artifacts import (
    ArtifactDownload,
    ArtifactMutationReceipt,
    ArtifactRecord,
    ArtifactRequest,
    ArtifactResult,
    ChangeHoldRequest,
    ChangeReferenceRequest,
    CleanupArtifactsRequest,
    CleanupReceipt,
    CustodyReceipt,
    DownloadGrant,
    InspectArtifactRequest,
    IssueDownloadGrantRequest,
    PublishArtifactRequest,
    ResolveDownloadRequest,
)
from app.contracts.workspace.persistence import PersistenceCapability, PersistenceStatement
from app.services.workspace.manage_artifacts._persistence import ArtifactStore


def _custody_root(workspace_path: Path) -> Path:
    return workspace_path.resolve() / "artifacts"


def _safe_path(workspace_path: Path, relative_path: str) -> Path:
    root = _custody_root(workspace_path)
    candidate = (root / relative_path).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError("ARTIFACT_PATH_ESCAPE")
    return candidate


def _record(row: dict[str, object]) -> ArtifactRecord:
    return ArtifactRecord(
        artifact_id=str(row["artifact_id"]),
        account_id=str(row["account_id"]),
        owner_id=str(row["owner_id"]),
        content_hash=str(row["content_hash"]),
        byte_count=int(row["byte_count"]),
        schema_id=str(row["schema_id"]),
        published_at=datetime.fromisoformat(str(row["published_at"])),
        revision=int(row["revision"]),
    )


class ManageArtifactsService:
    """Own immutable bytes and custody metadata without exposing host paths."""

    def __init__(
        self,
        persistence: PersistenceCapability,
        resources: ResourceAdmissionPort,
    ) -> None:
        self._persistence = persistence
        self._resources = resources
        self._stores: dict[Path, ArtifactStore] = {}
        self._closed = False

    def _store(self, path: Path) -> ArtifactStore:
        resolved = path.resolve()
        store = self._stores.get(resolved)
        if store is None:
            store = ArtifactStore(self._persistence, resolved)
            self._stores[resolved] = store
        return store

    async def manage_artifact(self, request: ArtifactRequest) -> ArtifactResult:
        """Execute one artifact operation."""
        if self._closed:
            raise RuntimeError("manage-artifacts service is closed")
        if isinstance(request, PublishArtifactRequest):
            return await self._publish(request)
        if isinstance(request, InspectArtifactRequest):
            return self._inspect(request)
        if isinstance(request, IssueDownloadGrantRequest):
            return self._issue_grant(request)
        if isinstance(request, ResolveDownloadRequest):
            return self._resolve_download(request)
        if isinstance(request, ChangeReferenceRequest):
            return self._change_reference(request)
        if isinstance(request, ChangeHoldRequest):
            return self._change_hold(request)
        if isinstance(request, CleanupArtifactsRequest):
            return await self._cleanup(request)
        raise TypeError("unsupported artifact request")

    async def _publish(self, request: PublishArtifactRequest) -> CustodyReceipt:
        if request.declared_byte_count < 0 or request.declared_byte_count != len(request.content):
            raise ValueError("ARTIFACT_BYTE_COUNT_MISMATCH")
        digest = hashlib.sha256(request.content).hexdigest()
        if digest != request.declared_content_hash:
            raise ValueError("ARTIFACT_HASH_MISMATCH")
        store = self._store(request.workspace_path)
        existing = store.query(
            request.account_id,
            "SELECT * FROM workspace_artifacts WHERE idempotency_key = ?",
            (request.idempotency_key,),
        )
        if existing:
            record = _record(existing[0])
            if (
                record.content_hash != digest
                or record.byte_count != len(request.content)
                or record.account_id != request.account_id
                or record.owner_id != request.owner_id
                or record.schema_id != request.schema_id
            ):
                raise ValueError("ARTIFACT_IDEMPOTENCY_CONFLICT")
            return CustodyReceipt(record, request.idempotency_key, False)
        admission = await self._resources.admit(
            ResourceAdmissionRequest(
                request_id=f"artifact:{request.request_id}",
                owner_id="FEAT-WS-MANAGE_ARTIFACTS",
                work_id=request.idempotency_key,
                idempotency_key=f"artifact:{request.idempotency_key}",
                profile=FiniteResourceProfile(
                    memory_bytes=min(len(request.content), 64 * 1024 * 1024),
                    temp_disk_bytes=len(request.content),
                ),
            )
        )
        if admission.status is not AdmissionStatus.ADMITTED or admission.lease is None:
            raise RuntimeError(f"ARTIFACT_RESOURCE_{admission.status.value.upper()}")
        lease = admission.lease
        try:
            root = _custody_root(request.workspace_path)
            staging = root / ".staging"
            staging.mkdir(parents=True, exist_ok=True)
            artifact_id = f"art-{uuid.uuid4().hex}"
            relative = f"sha256/{digest[:2]}/{digest}"
            final = _safe_path(request.workspace_path, relative)
            final.parent.mkdir(parents=True, exist_ok=True)
            staged = staging / f"{artifact_id}.tmp"
            staged.write_bytes(request.content)
            if (
                staged.stat().st_size != request.declared_byte_count
                or hashlib.sha256(staged.read_bytes()).hexdigest() != digest
            ):
                staged.unlink(missing_ok=True)
                raise ValueError("ARTIFACT_STAGING_VALIDATION_FAILED")
            final_existed = final.exists()
            if final_existed:
                if hashlib.sha256(final.read_bytes()).hexdigest() != digest:
                    staged.unlink(missing_ok=True)
                    raise RuntimeError("ARTIFACT_CONTENT_ADDRESS_COLLISION")
                staged.unlink(missing_ok=True)
            else:
                staged.replace(final)
            published_at = datetime.now(timezone.utc)
            try:
                store.execute(
                    request.request_id,
                    request.actor_id,
                    request.account_id,
                    (
                        PersistenceStatement(
                            "INSERT INTO workspace_artifacts (artifact_id, account_id, owner_id, content_hash, byte_count, schema_id, relative_path, idempotency_key, published_at, revision) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)",
                            (
                                artifact_id,
                                request.account_id,
                                request.owner_id,
                                digest,
                                len(request.content),
                                request.schema_id,
                                relative,
                                request.idempotency_key,
                                published_at.isoformat(),
                            ),
                        ),
                    ),
                )
            except Exception:
                if not final_existed:
                    final.unlink(missing_ok=True)
                raise
            record = ArtifactRecord(
                artifact_id,
                request.account_id,
                request.owner_id,
                digest,
                len(request.content),
                request.schema_id,
                published_at,
            )
            return CustodyReceipt(record, request.idempotency_key, True)
        finally:
            await self._resources.release(lease.lease_id, lease.generation)

    def _inspect(self, request: InspectArtifactRequest) -> ArtifactRecord:
        rows = self._store(request.workspace_path).query(
            request.account_id,
            "SELECT * FROM workspace_artifacts WHERE artifact_id = ? AND account_id = ?",
            (request.artifact_id, request.account_id),
        )
        if not rows:
            raise KeyError("ARTIFACT_NOT_FOUND")
        return _record(rows[0])

    def _issue_grant(self, request: IssueDownloadGrantRequest) -> DownloadGrant:
        now = datetime.now(timezone.utc)
        if request.expires_at.tzinfo is None or request.expires_at <= now:
            raise ValueError("ARTIFACT_GRANT_EXPIRY_INVALID")
        store = self._store(request.workspace_path)
        rows = store.query(
            request.account_id,
            "SELECT * FROM workspace_artifacts WHERE artifact_id = ? AND account_id = ?",
            (request.artifact_id, request.account_id),
        )
        if not rows:
            raise KeyError("ARTIFACT_NOT_FOUND")
        record = _record(rows[0])
        grant = DownloadGrant(
            f"grant-{uuid.uuid4().hex}",
            record.artifact_id,
            request.account_id,
            request.principal_id,
            request.expires_at,
            record.content_hash,
        )
        store.execute(
            request.request_id,
            request.actor_id,
            request.account_id,
            (
                PersistenceStatement(
                    "INSERT INTO workspace_artifact_grants (grant_id, artifact_id, account_id, principal_id, expires_at, content_hash) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        grant.grant_id,
                        grant.artifact_id,
                        grant.account_id,
                        grant.principal_id,
                        grant.expires_at.isoformat(),
                        grant.content_hash,
                    ),
                ),
            ),
        )
        return grant

    def _resolve_download(self, request: ResolveDownloadRequest) -> ArtifactDownload:
        now = datetime.now(timezone.utc)
        grant = request.grant
        if grant.expires_at.tzinfo is None or now >= grant.expires_at:
            raise PermissionError("ARTIFACT_GRANT_EXPIRED")
        if grant.account_id != request.account_id or grant.principal_id != request.principal_id:
            raise PermissionError("ARTIFACT_GRANT_SCOPE_DENIED")
        store = self._store(request.workspace_path)
        grant_rows = store.query(
            request.account_id,
            "SELECT * FROM workspace_artifact_grants WHERE grant_id = ? AND artifact_id = ? AND account_id = ? AND principal_id = ?",
            (grant.grant_id, grant.artifact_id, request.account_id, request.principal_id),
        )
        if not grant_rows:
            raise PermissionError("ARTIFACT_GRANT_UNKNOWN")
        stored_grant = grant_rows[0]
        if (
            str(stored_grant["content_hash"]) != grant.content_hash
            or str(stored_grant["expires_at"]) != grant.expires_at.isoformat()
        ):
            raise PermissionError("ARTIFACT_GRANT_MUTATED")
        rows = store.query(
            request.account_id,
            "SELECT * FROM workspace_artifacts WHERE artifact_id = ? AND account_id = ?",
            (grant.artifact_id, request.account_id),
        )
        if not rows:
            raise KeyError("ARTIFACT_NOT_FOUND")
        record = _record(rows[0])
        if record.content_hash != grant.content_hash:
            raise PermissionError("ARTIFACT_GRANT_STALE")
        content = _safe_path(request.workspace_path, str(rows[0]["relative_path"])).read_bytes()
        if hashlib.sha256(content).hexdigest() != record.content_hash:
            raise RuntimeError("ARTIFACT_INTEGRITY_FAILURE")
        return ArtifactDownload(record, content)

    def _change_reference(self, request: ChangeReferenceRequest) -> ArtifactMutationReceipt:
        store = self._store(request.workspace_path)
        self._require_artifact(store, request.account_id, request.artifact_id)
        if request.add:
            statement = PersistenceStatement(
                "INSERT OR IGNORE INTO workspace_artifact_refs (artifact_id, reference_id, owner_id) VALUES (?, ?, ?)",
                (request.artifact_id, request.reference_id, request.owner_id),
            )
            action = "REFERENCE_ADDED"
        else:
            statement = PersistenceStatement(
                "DELETE FROM workspace_artifact_refs WHERE artifact_id = ? AND reference_id = ? AND owner_id = ?",
                (request.artifact_id, request.reference_id, request.owner_id),
            )
            action = "REFERENCE_REMOVED"
        store.execute(
            request.request_id,
            request.actor_id,
            request.account_id,
            (statement,),
        )
        return ArtifactMutationReceipt(request.artifact_id, True, action)

    def _change_hold(self, request: ChangeHoldRequest) -> ArtifactMutationReceipt:
        store = self._store(request.workspace_path)
        self._require_artifact(store, request.account_id, request.artifact_id)
        if request.add:
            statement = PersistenceStatement(
                "INSERT OR IGNORE INTO workspace_artifact_holds (artifact_id, hold_id, owner_id) VALUES (?, ?, ?)",
                (request.artifact_id, request.hold_id, request.owner_id),
            )
            action = "HOLD_ADDED"
        else:
            statement = PersistenceStatement(
                "DELETE FROM workspace_artifact_holds WHERE artifact_id = ? AND hold_id = ? AND owner_id = ?",
                (request.artifact_id, request.hold_id, request.owner_id),
            )
            action = "HOLD_RELEASED"
        store.execute(
            request.request_id,
            request.actor_id,
            request.account_id,
            (statement,),
        )
        return ArtifactMutationReceipt(request.artifact_id, True, action)

    async def _cleanup(self, request: CleanupArtifactsRequest) -> CleanupReceipt:
        if request.max_items < 1 or request.max_items > 1000:
            raise ValueError("cleanup max_items must be 1..1000")
        store = self._store(request.workspace_path)
        rows = store.query(
            request.account_id,
            "SELECT * FROM workspace_artifacts WHERE account_id = ? LIMIT ?",
            (request.account_id, request.max_items),
        )
        removed: list[str] = []
        for row in rows:
            artifact_id = str(row["artifact_id"])
            refs = store.query(
                request.account_id,
                "SELECT reference_id FROM workspace_artifact_refs WHERE artifact_id = ? LIMIT 1",
                (artifact_id,),
            )
            holds = store.query(
                request.account_id,
                "SELECT hold_id FROM workspace_artifact_holds WHERE artifact_id = ? LIMIT 1",
                (artifact_id,),
            )
            if refs or holds:
                continue
            relative_path = str(row["relative_path"])
            siblings = store.query(
                request.account_id,
                "SELECT artifact_id FROM workspace_artifacts WHERE relative_path = ? AND artifact_id <> ? LIMIT 1",
                (relative_path, artifact_id),
            )
            store.execute(
                f"{request.request_id}:{artifact_id}",
                request.actor_id,
                request.account_id,
                (
                    PersistenceStatement(
                        "DELETE FROM workspace_artifact_grants WHERE artifact_id = ?",
                        (artifact_id,),
                    ),
                    PersistenceStatement(
                        "DELETE FROM workspace_artifacts WHERE artifact_id = ? AND account_id = ?",
                        (artifact_id, request.account_id),
                    ),
                ),
            )
            if not siblings:
                _safe_path(request.workspace_path, relative_path).unlink(missing_ok=True)
            removed.append(artifact_id)
        return CleanupReceipt(tuple(removed), len(rows))

    def _require_artifact(
        self,
        store: ArtifactStore,
        account_id: str,
        artifact_id: str,
    ) -> None:
        if not store.query(
            account_id,
            "SELECT artifact_id FROM workspace_artifacts WHERE artifact_id = ? AND account_id = ?",
            (artifact_id, account_id),
        ):
            raise KeyError("ARTIFACT_NOT_FOUND")

    def close(self) -> None:
        """Release feature-local references while retaining committed custody state."""
        self._closed = True
        self._stores.clear()
