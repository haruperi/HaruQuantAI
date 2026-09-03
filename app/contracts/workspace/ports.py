"""Public capability protocols (ports) for Workspace management."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pathlib import Path

    from app.contracts.workspace.errors import WorkspaceFailure
    from app.contracts.workspace.models import (
        DiagnosticBundleRef,
        DistributeWorkersRequest,
        DistributeWorkersSuccess,
        HostWorkspacesRequest,
        HostWorkspacesSuccess,
        JobKind,
        LocalSession,
        ManageWatchlistsRequest,
        ManageWatchlistsSuccess,
        RuntimeSupportProfile,
        ServerRuntimeSettings,
        ServerRuntimeValidation,
        StorageGuardDecision,
        StorageGuardLimits,
        SystemHealth,
        SystemReadiness,
        WorkspaceBackupManifest,
        WorkspaceRecoverySummary,
        WorkspaceRef,
        WorkspaceRestorePlan,
        WorkspaceSettings,
        WorkspaceSettingsVersion,
        WorkspaceVersion,
        WorkspaceWriterFence,
    )


@runtime_checkable
class ManageWorkspacesCapability(Protocol):
    """Capability protocol for workspace lifecycle operations."""

    def initialize_workspace(
        self,
        path: Path,
        name: str | None = None,
    ) -> WorkspaceRef:
        """Atomically initialize a new workspace at an explicit writable path.

        Creates directory tree (metadata, artifacts, logs, cache, exports, staging,
        backups) and initial SQLite database in WAL mode with base schema.

        Args:
            path: Target filesystem directory path.
            name: Optional human-readable workspace name.

        Returns:
            WorkspaceRef describing the initialized workspace.

        Raises:
            WorkspaceStorageError: If path cannot be created or is not writable.
            WorkspaceError: If workspace already exists or initialization fails.
        """
        ...

    def migrate_workspace_schema(
        self,
        workspace: Path | WorkspaceRef,
    ) -> WorkspaceVersion:
        """Apply ordered, transactional schema migrations to a workspace.

        Records applied migrations and version in the metadata database. Reopening
        an up-to-date database performs no mutations.

        Args:
            workspace: Workspace root path or WorkspaceRef.

        Returns:
            WorkspaceVersion with current schema version.

        Raises:
            WorkspaceNotFoundError: If workspace does not exist.
            WorkspaceMigrationError: If any migration step fails.
        """
        ...

    def fence_workspace_writers(
        self,
        workspace: Path | WorkspaceRef,
        *,
        read_only: bool = False,
    ) -> WorkspaceWriterFence:
        """Acquire an exclusive writer fence or read-only diagnostic lease.

        Args:
            workspace: Workspace root path or WorkspaceRef.
            read_only: True to open in diagnostic read-only mode without write lock.

        Returns:
            WorkspaceWriterFence containing lease and token details.

        Raises:
            WorkspaceNotFoundError: If workspace does not exist.
            WorkspaceAlreadyOpenError: If another active writer holds the fence.
        """
        ...

    def release_writer_fence(
        self,
        fence: WorkspaceWriterFence,
        workspace: Path | WorkspaceRef,
    ) -> None:
        """Release a held writer fence lock.

        Args:
            fence: The active WorkspaceWriterFence to release.
            workspace: Workspace root path or WorkspaceRef.
        """
        ...

    def recover_workspace_state(
        self,
        workspace: Path | WorkspaceRef,
    ) -> WorkspaceRecoverySummary:
        """Recover staged artifacts, expired leases, and nonterminal jobs.

        Args:
            workspace: Workspace root path or WorkspaceRef.

        Returns:
            WorkspaceRecoverySummary with recovery statistics and findings.

        Raises:
            WorkspaceNotFoundError: If workspace does not exist.
        """
        ...

    def backup_workspace(
        self,
        workspace: Path | WorkspaceRef,
        destination_dir: Path,
    ) -> WorkspaceBackupManifest:
        """Create a consistent backup snapshot of metadata and committed artifacts.

        Args:
            workspace: Workspace root path or WorkspaceRef.
            destination_dir: Directory where the backup snapshot/archive is created.

        Returns:
            WorkspaceBackupManifest with file inventory and checksums.

        Raises:
            WorkspaceNotFoundError: If workspace does not exist.
            WorkspaceStorageError: If destination is invalid or write fails.
        """
        ...

    def restore_workspace(
        self,
        plan: WorkspaceRestorePlan,
    ) -> WorkspaceRef:
        """Restore a workspace from a backup manifest into an empty target directory.

        Args:
            plan: WorkspaceRestorePlan describing manifest path and target.

        Returns:
            WorkspaceRef of the restored workspace.

        Raises:
            WorkspaceStorageError: If target path is non-empty or unwritable.
            WorkspaceCorruptionError: If checksum verification fails during restore.
        """
        ...


@runtime_checkable
class ConfigureRuntimeCapability(Protocol):
    """Capability protocol for workspace runtime configuration and admission."""

    def configure_workspace(
        self,
        workspace: Path | WorkspaceRef,
        settings: WorkspaceSettings,
    ) -> WorkspaceSettingsVersion:
        """Persist validated workspace settings as a new immutable version.

        Args:
            workspace: Workspace root path or WorkspaceRef.
            settings: Settings payload to validate and persist.

        Returns:
            WorkspaceSettingsVersion describing the persisted version.

        Raises:
            SettingsValidationError: If any field is invalid; the persisted
                version is not incremented.
            WorkspaceNotFoundError: If the workspace database is missing.
        """
        ...

    def get_workspace_settings(
        self,
        workspace: Path | WorkspaceRef,
    ) -> WorkspaceSettingsVersion | None:
        """Return the latest persisted settings version, if any.

        Args:
            workspace: Workspace root path or WorkspaceRef.

        Returns:
            Latest WorkspaceSettingsVersion or None when never configured.
        """
        ...

    def enforce_storage_guards(
        self,
        workspace: Path | WorkspaceRef,
        *,
        job_kind: JobKind,
        projected_artifact_mb: float,
        limits: StorageGuardLimits | None = None,
    ) -> StorageGuardDecision:
        """Evaluate workspace storage guards before admitting a job.

        Args:
            workspace: Workspace root path or WorkspaceRef.
            job_kind: Guarded job category.
            projected_artifact_mb: Projected artifact storage in MiB.
            limits: Optional guard limits; defaults apply when omitted.

        Returns:
            StorageGuardDecision; over-limit jobs are not admitted and report
            required versus available storage.
        """
        ...

    def configure_server_runtime(
        self,
        settings: ServerRuntimeSettings,
    ) -> ServerRuntimeValidation:
        """Validate launcher/server runtime settings before UI launch.

        Args:
            settings: Server runtime settings to validate.

        Returns:
            ServerRuntimeValidation; invalid or unavailable ports fail before
            launch and non-loopback bindings require explicit opt-in plus a
            non-loopback-capable authentication mode.
        """
        ...

    def publish_runtime_support(self) -> RuntimeSupportProfile:
        """Publish the versioned runtime support profile for this release.

        Returns:
            RuntimeSupportProfile naming supported platforms, resources,
            filesystems, browsers, and required compilers.

        Raises:
            UnsupportedRuntimeError: If the host platform is unsupported.
        """
        ...


@runtime_checkable
class SecureLocalAccessCapability(Protocol):
    """Capability protocol for local access security, health, and readiness."""

    def issue_local_session(
        self,
        *,
        client_id: str,
        is_launcher_connected: bool,
        client_host: str = "127.0.0.1",
        ttl_seconds: int | None = None,
    ) -> LocalSession:
        """Issue an ephemeral local-session token to a launcher client.

        Args:
            client_id: Identifier of the launcher client requesting the session.
            is_launcher_connected: True if caller is launcher-connected.
            client_host: Host IP of the client connection (loopback by default).
            ttl_seconds: Optional session lifetime in seconds.

        Returns:
            LocalSession with unique token and expiry timestamp.

        Raises:
            SessionDeniedError: If the client is not launcher-connected or
                source host is not loopback.
        """
        ...

    def verify_local_session(
        self,
        *,
        token: str,
        client_host: str = "127.0.0.1",
    ) -> LocalSession:
        """Verify an ephemeral local-session token and enforce loopback binding.

        Args:
            token: Session token to validate.
            client_host: Source host IP of the request.

        Returns:
            LocalSession if the token is valid, unexpired, and permitted.

        Raises:
            SessionDeniedError: If the token is unknown or revoked.
            SessionExpiredError: If the session TTL has elapsed.
            NonLoopbackAccessDeniedError: If a non-loopback source attempts access
                without nonlocal authorization.
        """
        ...

    def revoke_local_session(self, token: str) -> None:
        """Revoke a previously issued local session token.

        Args:
            token: Session token to invalidate immediately.
        """
        ...

    def check_system_health(self) -> SystemHealth:
        """Expose operational health status, functional before full readiness.

        Returns:
            SystemHealth describing runtime component health.
        """
        ...

    def report_system_readiness(
        self,
        workspace: Path | WorkspaceRef | None = None,
    ) -> SystemReadiness:
        """Expose system readiness without disclosing secrets or absolute user paths.

        Readiness becomes true only after migrations and job recovery succeed.

        Args:
            workspace: Optional workspace root or WorkspaceRef to verify.

        Returns:
            SystemReadiness describing readiness, schema, and worker status.
        """
        ...


@runtime_checkable
class BuildDiagnosticsCapability(Protocol):
    """Capability protocol for generating redacted diagnostic bundles."""

    def build_diagnostic_bundle(
        self,
        *,
        workspace: Path | WorkspaceRef | None = None,
        include_logs: bool = True,
        output_path: Path | None = None,
    ) -> DiagnosticBundleRef:
        """Produce a redacted diagnostic bundle for troubleshooting.

        Args:
            workspace: Optional workspace root or WorkspaceRef to inspect.
            include_logs: Whether to collect recent structured log entries.
            output_path: Optional destination directory or file path for the archive.

        Returns:
            DiagnosticBundleRef containing the archive path, checksum, and manifest.

        Raises:
            DiagnosticBundleError: If bundle construction or packaging fails.
        """
        ...


@runtime_checkable
class DistributeWorkersCapability(Protocol):
    """Capability protocol for distributed worker pool operations."""

    async def distribute_workers(
        self,
        request: DistributeWorkersRequest,
    ) -> DistributeWorkersSuccess | WorkspaceFailure:
        """Register, authenticate, lease, assign, and transfer worker work.

        Args:
            request: Operation-discriminated distributed worker pool
                request.

        Returns:
            The registration, lease, assignment envelope, or artifact
            manifest on success, otherwise a structured workspace failure.
        """
        ...


@runtime_checkable
class HostWorkspacesCapability(Protocol):
    """Capability protocol for hosted workspace boundary operations."""

    async def host_workspaces(
        self,
        request: HostWorkspacesRequest,
    ) -> HostWorkspacesSuccess | WorkspaceFailure:
        """Provision, describe, and authorize isolated hosted workspaces.

        Args:
            request: Operation-discriminated hosted workspace request.

        Returns:
            The isolation context or authorization decision (where ``DENY``
            is a typed success outcome) on success, otherwise a structured
            workspace failure.
        """
        ...


@runtime_checkable
class ManageWatchlistsCapability(Protocol):
    """Capability protocol for account watchlist operations."""

    async def manage_watchlists(
        self,
        request: ManageWatchlistsRequest,
    ) -> ManageWatchlistsSuccess | WorkspaceFailure:
        """List, create, update, and delete account-owned watchlists.

        Args:
            request: Operation-discriminated watchlist request.

        Returns:
            The watchlist page, mutation result, or deletion flag on
            success, otherwise a structured workspace failure.
        """
        ...
