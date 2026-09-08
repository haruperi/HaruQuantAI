"""Workspace management capability implementation.

Purpose:
    Open stable workspace identities, enforce one writer, create verified
    backups, restore through isolated staging, and reconcile interrupted
    publication records without deleting committed domain evidence.

Key capabilities:
    * Atomic initialize-or-open with exclusive writer fencing.
    * Checksummed, bounded backup and staged restore.
    * Idempotent recovery of pre- and post-promotion crash records.

Python API usage:
    service = ManageWorkspacesService()
    result = service.manage_workspaces(ManageWorkspacesRequest(...))

CLI usage:
    uv run python -m app.services.workspace.manage_workspaces._usage
"""

# Exception messages include local identifiers needed for operator diagnosis.
# ruff: noqa: EM102

from __future__ import annotations

import datetime as dt
import hashlib
import json
import shutil
import uuid
from pathlib import Path, PurePosixPath

from app.composition.logging import get_logger
from app.contracts.workspace.errors import (
    WorkspaceCorruptionError,
    WorkspaceError,
    WorkspaceStorageError,
)
from app.contracts.workspace.manage_workspaces import (
    ManageWorkspaceOperation,
    ManageWorkspacesRequest,
    ManageWorkspacesSuccess,
)
from app.contracts.workspace.models import (
    WorkspaceBackupManifest,
    WorkspaceRecoverySummary,
    WorkspaceRef,
    WorkspaceRestorePlan,
    WorkspaceVersion,
    WorkspaceWriterFence,
)
from app.services.workspace.manage_workspaces._backup import (
    create_backup,
    restore_backup,
    sha256_file,
)
from app.services.workspace.manage_workspaces._locking import (
    acquire_writer_fence,
    is_process_alive,
    release_writer_fence,
)
from app.services.workspace.manage_workspaces._persistence import (
    WorkspacePersistence,
)
from app.services.workspace.manage_workspaces.config import ManageWorkspacesConfig

SUBDIRECTORIES: tuple[str, ...] = (
    "database",
    "artifacts/objects",
    "staging",
    "logs",
    "cache",
    "exports",
    "backups",
)

logger = get_logger(__name__)


def _utc_now_iso() -> str:
    """Return a fixed-width UTC timestamp."""
    return dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _age_seconds(timestamp: str) -> float:
    """Return nonnegative age for an ISO-8601 UTC timestamp."""
    parsed = dt.datetime.fromisoformat(timestamp)
    return max(0.0, (dt.datetime.now(dt.UTC) - parsed).total_seconds())


def _db_path(root: Path) -> Path:
    """Return the canonical database path for the workspace."""
    if root.suffix == ".db":
        return root
    central_db = root / "database" / "haruquantai.db"
    if central_db.exists():
        return central_db
    if (root / "haruquantai.db").exists():
        return root / "haruquantai.db"
    if (root / "data" / "database" / "haruquantai.db").exists():
        return root / "data" / "database" / "haruquantai.db"
    return central_db


def _fingerprint(request: ManageWorkspacesRequest) -> str:
    """Return a deterministic fingerprint excluding request identity."""
    payload = {
        "account_id": request.account_id,
        "actor_id": request.actor_id,
        "backup_manifest_path": (
            str(request.backup_manifest_path.resolve())
            if request.backup_manifest_path is not None
            else None
        ),
        "destination_path": (
            str(request.destination_path.resolve())
            if request.destination_path is not None
            else None
        ),
        "expected_revision": request.expected_revision,
        "name": request.name,
        "operation": request.operation.value,
        "read_only": request.read_only,
        "verify_checksums": request.verify_checksums,
        "workspace_id": request.workspace_id,
        "workspace_path": str(request.workspace_path.resolve()),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()


class ManageWorkspacesService:
    """Concrete workspace.manage-workspaces@1 provider."""

    def __init__(self, config: ManageWorkspacesConfig | None = None) -> None:
        """Create an effect-free service with bounded configuration."""
        self._config = config or ManageWorkspacesConfig()
        self._persistence = WorkspacePersistence(self._config.busy_timeout_seconds)
        self._owned_fences: dict[str, Path] = {}
        self._replays: dict[str, tuple[str, ManageWorkspacesSuccess]] = {}

    def _workspace(
        self,
        root: Path,
        *,
        account_id: str | None = None,
        workspace_id: str | None = None,
        expected_revision: int | None = None,
    ) -> tuple[WorkspaceRef, int]:
        reference, owner_account, revision = self._persistence.workspace(_db_path(root))
        if account_id is not None and account_id != owner_account:
            raise WorkspaceError(
                "Workspace belongs to a different account",
                error_code="WORKSPACE_SCOPE_DENIED",
            )
        if workspace_id is not None and workspace_id != reference.workspace_id:
            raise WorkspaceError(
                "Workspace identity does not match the request",
                error_code="WORKSPACE_SCOPE_DENIED",
            )
        if expected_revision is not None and expected_revision != revision:
            raise WorkspaceError(
                f"Expected workspace revision {expected_revision}, found {revision}",
                error_code="WORKSPACE_REVISION_CONFLICT",
            )
        return reference, revision

    def initialize_workspace(
        self,
        path: Path,
        name: str | None = None,
        *,
        account_id: str = "local",
    ) -> WorkspaceRef:
        """Initialize a workspace atomically, or reject an existing identity.

        Returns:
            The new stable workspace reference.

        Raises:
            WorkspaceError: If the workspace is already initialized.
            WorkspaceStorageError: If the target or filesystem operation is invalid.
        """
        root = path.resolve()
        if _db_path(root).exists():
            raise WorkspaceError(
                f"Workspace already initialized at '{root}'",
                error_code="WORKSPACE_ALREADY_EXISTS",
            )
        if root.exists() and (not root.is_dir() or any(root.iterdir())):
            raise WorkspaceStorageError(f"Workspace target must be empty: {root}")
        root.parent.mkdir(parents=True, exist_ok=True)
        staging = root.parent / f".{root.name}.initialize-{uuid.uuid4()}.staging"
        try:
            for subdirectory in SUBDIRECTORIES:
                (staging / subdirectory).mkdir(parents=True, exist_ok=True)
            reference = self._persistence.initialize(
                _db_path(staging),
                workspace_id=str(uuid.uuid4()),
                name=name or root.name,
                account_id=account_id,
                timestamp=_utc_now_iso(),
            )
            if root.exists():
                root.rmdir()
            Path(staging).replace(root)
            logger.info(
                "Workspace initialized",
                event="workspace.initialized",
                workspace_id=reference.workspace_id,
            )
            return WorkspaceRef(
                workspace_id=reference.workspace_id,
                name=reference.name,
                root_path=root,
                status=reference.status,
                created_at=reference.created_at,
            )
        except OSError as error:
            shutil.rmtree(staging, ignore_errors=True)
            raise WorkspaceStorageError(
                f"Failed to initialize workspace at '{root}': {error}"
            ) from error
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise

    def open_workspace(
        self,
        path: Path,
        *,
        name: str | None = None,
        account_id: str = "local",
        workspace_id: str | None = None,
        expected_revision: int | None = None,
        read_only: bool = False,
    ) -> tuple[WorkspaceRef, WorkspaceWriterFence, int]:
        """Initialize or reopen a stable workspace and acquire its session fence.

        Returns:
            Workspace reference, session fence, and current revision.
        """
        root = path.resolve()
        if not _db_path(root).exists():
            self.initialize_workspace(root, name, account_id=account_id)
        elif self._config.auto_migrate:
            self.migrate_workspace_schema(root)
        reference, revision = self._workspace(
            root,
            account_id=account_id,
            workspace_id=workspace_id,
            expected_revision=expected_revision,
        )
        fence = acquire_writer_fence(
            root,
            reference.workspace_id,
            _utc_now_iso(),
            read_only=read_only,
        )
        if fence.is_write_locked:
            self._owned_fences[fence.lock_token] = root
        logger.info(
            "Workspace opened",
            event="workspace.opened",
            workspace_id=reference.workspace_id,
            mode="read_only" if fence.is_read_only else "writer",
            revision=revision,
        )
        return reference, fence, revision

    def migrate_workspace_schema(
        self, workspace: Path | WorkspaceRef
    ) -> WorkspaceVersion:
        """Verify and apply ordered additive workspace migrations.

        Returns:
            The verified current workspace schema version.
        """
        root = (
            workspace.root_path if isinstance(workspace, WorkspaceRef) else workspace
        ).resolve()
        version = self._persistence.migrate(_db_path(root), _utc_now_iso())
        logger.info(
            "Workspace schema verified",
            event="workspace.schema.verified",
            schema_version=version.schema_version,
        )
        return version

    def fence_workspace_writers(
        self, workspace: Path | WorkspaceRef, *, read_only: bool = False
    ) -> WorkspaceWriterFence:
        """Acquire an exclusive writer or non-mutating read-only fence.

        Returns:
            The acquired writer or read-only fence.
        """
        root = (
            workspace.root_path if isinstance(workspace, WorkspaceRef) else workspace
        ).resolve()
        reference, _ = self._workspace(root)
        fence = acquire_writer_fence(
            root, reference.workspace_id, _utc_now_iso(), read_only=read_only
        )
        if fence.is_write_locked:
            self._owned_fences[fence.lock_token] = root
        logger.info(
            "Workspace fence acquired",
            event="workspace.fence.acquired",
            workspace_id=reference.workspace_id,
            mode="read_only" if fence.is_read_only else "writer",
        )
        return fence

    def release_writer_fence(
        self, fence: WorkspaceWriterFence, workspace: Path | WorkspaceRef
    ) -> None:
        """Release a writer fence only for the matching workspace and token."""
        root = (
            workspace.root_path if isinstance(workspace, WorkspaceRef) else workspace
        ).resolve()
        if fence.is_write_locked and release_writer_fence(root, fence.lock_token):
            self._owned_fences.pop(fence.lock_token, None)
            logger.info(
                "Workspace fence released",
                event="workspace.fence.released",
                workspace_id=fence.workspace_id,
            )

    def catalogue_artifact(self, workspace: Path | WorkspaceRef, path: Path) -> str:
        """Record one immutable artifact under artifacts/objects.

        Returns:
            The artifact content hash.

        Raises:
            WorkspaceStorageError: If the path is outside immutable custody.
        """
        root = (
            workspace.root_path if isinstance(workspace, WorkspaceRef) else workspace
        ).resolve()
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(root).as_posix()
        except ValueError as error:
            raise WorkspaceStorageError("Artifact is outside the workspace") from error
        if (
            not relative.startswith("artifacts/objects/")
            or resolved.is_symlink()
            or not resolved.is_file()
        ):
            raise WorkspaceStorageError("Artifact must be a regular immutable object")
        content_hash = sha256_file(resolved)
        self._persistence.catalogue_artifact(
            _db_path(root),
            content_hash=content_hash,
            relative_path=relative,
            size_bytes=resolved.stat().st_size,
            timestamp=_utc_now_iso(),
        )
        return content_hash

    def backup_workspace(
        self, workspace: Path | WorkspaceRef, destination_dir: Path
    ) -> WorkspaceBackupManifest:
        """Back up metadata and catalogued immutable artifacts atomically.

        Returns:
            The checksummed backup manifest.
        """
        root = (
            workspace.root_path if isinstance(workspace, WorkspaceRef) else workspace
        ).resolve()
        reference, _revision = self._workspace(root)
        version = self.migrate_workspace_schema(root)
        manifest = create_backup(
            root=root,
            workspace_id=reference.workspace_id,
            schema_version=version.schema_version,
            destination=destination_dir,
            artifacts=self._persistence.committed_artifacts(_db_path(root)),
            timestamp=_utc_now_iso(),
            config=self._config,
        )
        logger.info(
            "Workspace backup completed",
            event="workspace.backup.completed",
            workspace_id=reference.workspace_id,
            file_count=manifest.file_count,
            total_bytes=manifest.total_bytes,
        )
        return manifest

    def restore_workspace(self, plan: WorkspaceRestorePlan) -> WorkspaceRef:
        """Restore a complete verified backup through isolated staging.

        Returns:
            The restored workspace reference.
        """
        reference = restore_backup(
            manifest_path=plan.backup_manifest_path,
            target=plan.target_path,
            verify_checksums=plan.verify_checksums,
            config=self._config,
        )
        logger.info(
            "Workspace restore completed",
            event="workspace.restore.completed",
            workspace_id=reference.workspace_id,
        )
        return reference

    @staticmethod
    def _safe_workspace_member(root: Path, relative: str, prefix: str) -> Path:
        pure = PurePosixPath(relative)
        if (
            pure.is_absolute()
            or ".." in pure.parts
            or chr(92) in relative
            or ":" in relative
            or not relative.startswith(prefix)
        ):
            raise WorkspaceCorruptionError(f"Unsafe recovery path: {relative!r}")
        resolved = (root / pure).resolve()
        try:
            resolved.relative_to(root)
        except ValueError as error:
            raise WorkspaceCorruptionError(
                f"Recovery path escapes workspace: {relative!r}"
            ) from error
        return resolved

    def recover_workspace_state(
        self, workspace: Path | WorkspaceRef
    ) -> WorkspaceRecoverySummary:
        """Reconcile journalled crash states without deleting committed evidence.

        Returns:
            Counts and findings from deterministic reconciliation.

        Raises:
            WorkspaceCorruptionError: If committed references point to partial bytes.
        """
        root = (
            workspace.root_path if isinstance(workspace, WorkspaceRef) else workspace
        ).resolve()
        reference, _revision = self._workspace(root)
        findings: list[str] = []
        cleaned = 0
        for publication in self._persistence.publications(_db_path(root)):
            if (
                publication.state == "STAGED"
                and _age_seconds(publication.created_at)
                < self._config.staged_grace_period_seconds
            ):
                findings.append(
                    f"retained recent staged publication:{publication.publication_id}"
                )
                continue
            staged = self._safe_workspace_member(
                root, publication.staged_relative_path, "staging/"
            )
            final = self._safe_workspace_member(
                root, publication.final_relative_path, "artifacts/objects/"
            )
            if publication.state == "STAGED":
                if staged.is_file() and not staged.is_symlink():
                    staged.unlink()
                    cleaned += 1
                self._persistence.delete_publication(
                    _db_path(root), publication.publication_id
                )
                findings.append(
                    f"discarded pre-promotion publication:{publication.publication_id}"
                )
                continue
            committed = self._persistence.artifact_is_committed(
                _db_path(root), publication.content_hash
            )
            if committed:
                if (
                    not final.is_file()
                    or sha256_file(final) != publication.content_hash
                ):
                    raise WorkspaceCorruptionError(
                        "Committed artifact points at missing or partial bytes"
                    )
                self._persistence.delete_publication(
                    _db_path(root), publication.publication_id
                )
                findings.append(
                    f"confirmed catalogued publication:{publication.publication_id}"
                )
            else:
                self._persistence.set_publication_state(
                    _db_path(root), publication.publication_id, "ORPHANED"
                )
                findings.append(
                    "orphan custody retained:"
                    f"{publication.publication_id}:{publication.final_relative_path}"
                )
        lock_path = root / ".workspace.lock"
        if lock_path.is_file():
            try:
                holder = int(
                    json.loads(lock_path.read_text(encoding="utf-8"))["holder_pid"]
                )
            except OSError, ValueError, KeyError, json.JSONDecodeError:
                holder = 0
            if not is_process_alive(holder):
                lock_path.unlink(missing_ok=True)
                findings.append(f"cleared stale writer fence:{holder}")
        summary = WorkspaceRecoverySummary(
            workspace_id=reference.workspace_id,
            recovered_at=_utc_now_iso(),
            staged_artifacts_cleaned=cleaned,
            expired_leases_released=0,
            orphaned_jobs_reconciled=sum(
                finding.startswith("orphan custody retained:") for finding in findings
            ),
            findings=tuple(findings),
        )
        logger.info(
            "Workspace recovery completed",
            event="workspace.recovery.completed",
            workspace_id=reference.workspace_id,
            staged_cleaned=summary.staged_artifacts_cleaned,
            orphans_retained=summary.orphaned_jobs_reconciled,
            finding_count=len(summary.findings),
        )
        return summary

    def _require_owned_fence(self, root: Path, token: str | None) -> None:
        if token is None or self._owned_fences.get(token) != root:
            raise WorkspaceError(
                "A current writer fence is required",
                error_code="WORKSPACE_FENCE_REQUIRED",
            )

    def _execute_request(
        self, request: ManageWorkspacesRequest
    ) -> ManageWorkspacesSuccess:
        """Execute one admitted operation with replay protection.

        Returns:
            The versioned success receipt, or the exact earlier receipt on replay.

        Raises:
            ValueError: If a request ID is reused with different content.
            WorkspaceError: If scope, revision, fence, or operation policy fails.
        """
        fingerprint = _fingerprint(request)
        replay = self._replays.get(request.request_id)
        if replay is not None:
            if replay[0] != fingerprint:
                raise WorkspaceError(
                    "request_id was reused with different input",
                    error_code="WORKSPACE_REQUEST_CONFLICT",
                )
            logger.debug(
                "Workspace request replayed",
                event="workspace.request.replayed",
                operation=request.operation.value,
                request_id=request.request_id,
            )
            return replay[1]
        root = request.workspace_path.resolve()
        if request.operation is ManageWorkspaceOperation.OPEN:
            reference, fence, revision = self.open_workspace(
                root,
                name=request.name,
                account_id=request.account_id,
                workspace_id=request.workspace_id,
                expected_revision=request.expected_revision,
                read_only=request.read_only,
            )
            result = ManageWorkspacesSuccess(
                request_id=request.request_id,
                operation=request.operation,
                workspace=reference,
                fence=fence,
                workspace_revision=revision,
            )
        elif request.operation is ManageWorkspaceOperation.BACKUP:
            reference, revision = self._workspace(
                root,
                account_id=request.account_id,
                workspace_id=request.workspace_id,
                expected_revision=request.expected_revision,
            )
            self._require_owned_fence(root, request.fence_token)
            if request.destination_path is None:
                raise ValueError("BACKUP requires destination_path")
            result = ManageWorkspacesSuccess(
                request_id=request.request_id,
                operation=request.operation,
                workspace=reference,
                backup=self.backup_workspace(root, request.destination_path),
                workspace_revision=revision,
            )
        elif request.operation is ManageWorkspaceOperation.RESTORE:
            if request.backup_manifest_path is None:
                raise ValueError("RESTORE requires backup_manifest_path")
            restore_backup(
                manifest_path=request.backup_manifest_path,
                target=root,
                verify_checksums=request.verify_checksums,
                config=self._config,
                expected_workspace_id=request.workspace_id,
                expected_account_id=request.account_id,
            )
            reference, revision = self._workspace(
                root,
                account_id=request.account_id,
                workspace_id=request.workspace_id,
                expected_revision=request.expected_revision,
            )
            result = ManageWorkspacesSuccess(
                request_id=request.request_id,
                operation=request.operation,
                workspace=reference,
                workspace_revision=revision,
            )
        elif request.operation is ManageWorkspaceOperation.RECOVER:
            reference, revision = self._workspace(
                root,
                account_id=request.account_id,
                workspace_id=request.workspace_id,
                expected_revision=request.expected_revision,
            )
            self._require_owned_fence(root, request.fence_token)
            result = ManageWorkspacesSuccess(
                request_id=request.request_id,
                operation=request.operation,
                workspace=reference,
                recovery=self.recover_workspace_state(root),
                workspace_revision=revision,
            )
        else:
            reference, revision = self._workspace(
                root,
                account_id=request.account_id,
                workspace_id=request.workspace_id,
                expected_revision=request.expected_revision,
            )
            released = bool(
                request.fence_token and release_writer_fence(root, request.fence_token)
            )
            if request.fence_token:
                self._owned_fences.pop(request.fence_token, None)
            result = ManageWorkspacesSuccess(
                request_id=request.request_id,
                operation=request.operation,
                workspace=reference,
                released=released,
                workspace_revision=revision,
            )
        self._persistence.audit(
            _db_path(root),
            request_id=request.request_id,
            actor_id=request.actor_id,
            action=request.operation.value,
            workspace_id=(
                result.workspace.workspace_id if result.workspace else "unknown"
            ),
            outcome="SUCCESS",
            revision=result.workspace_revision,
            timestamp=_utc_now_iso(),
        )
        self._replays[request.request_id] = (fingerprint, result)
        return result

    def manage_workspaces(
        self, request: ManageWorkspacesRequest
    ) -> ManageWorkspacesSuccess:
        """Execute the versioned contract with safe operational logging.

        Returns:
            The versioned success receipt, or the exact earlier receipt on replay.

        Raises:
            WorkspaceError: If scope, revision, fence, or operation policy fails.
            Exception: If an unexpected implementation or storage failure occurs.
        """
        logger.debug(
            "Workspace request admitted",
            event="workspace.request.admitted",
            operation=request.operation.value,
            request_id=request.request_id,
        )
        try:
            result = self._execute_request(request)
        except WorkspaceError as error:
            logger.warning(
                "Workspace request failed",
                event="workspace.request.failed",
                operation=request.operation.value,
                request_id=request.request_id,
                error_code=error.error_code,
                error_type=type(error).__name__,
            )
            raise
        except Exception as error:
            logger.error(  # noqa: TRY400 - traceback may expose sensitive paths.
                "Workspace request failed",
                event="workspace.request.failed",
                operation=request.operation.value,
                request_id=request.request_id,
                error_type=type(error).__name__,
            )
            raise
        logger.info(
            "Workspace request completed",
            event="workspace.request.completed",
            operation=request.operation.value,
            request_id=request.request_id,
            revision=result.workspace_revision,
        )
        return result

    def close(self) -> None:
        """Release every writer fence owned by this service generation."""
        for token, root in tuple(self._owned_fences.items()):
            release_writer_fence(root, token)
            self._owned_fences.pop(token, None)


WorkspaceLifecycleService = ManageWorkspacesService
