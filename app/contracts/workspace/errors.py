"""Domain exceptions and errors for Workspace lifecycle capabilities."""

from __future__ import annotations


class WorkspaceError(RuntimeError):
    """Base exception for all workspace-related errors."""

    def __init__(self, message: str, error_code: str = "WORKSPACE_ERROR") -> None:
        """Initialize the workspace error.

        Args:
            message: Human-readable error description.
            error_code: Stable machine-readable error token.
        """
        self.error_code = error_code
        super().__init__(f"[{error_code}] {message}")


class WorkspaceAlreadyOpenError(WorkspaceError):
    """Raised when a workspace is already opened by another active writer."""

    def __init__(
        self,
        message: str = "Workspace is already opened by another writer process",
        holder_pid: int | None = None,
        lock_file: str | None = None,
    ) -> None:
        """Initialize the workspace already open error.

        Args:
            message: Error description.
            holder_pid: Process ID of the active lock holder if known.
            lock_file: Path to the active lock file.
        """
        self.holder_pid = holder_pid
        self.lock_file = lock_file
        details = []
        if holder_pid is not None:
            details.append(f"holder_pid={holder_pid}")
        if lock_file:
            details.append(f"lock_file={lock_file}")
        suffix = f" ({', '.join(details)})" if details else ""
        super().__init__(f"{message}{suffix}", error_code="WORKSPACE_ALREADY_OPEN")


class WorkspaceNotFoundError(WorkspaceError):
    """Raised when a workspace directory or database is missing."""

    def __init__(self, path: str) -> None:
        """Initialize the workspace not found error.

        Args:
            path: Missing workspace path.
        """
        super().__init__(
            f"Workspace not found at '{path}'", error_code="WORKSPACE_NOT_FOUND"
        )


class WorkspaceCorruptionError(WorkspaceError):
    """Raised when workspace metadata or artifacts fail integrity checks."""

    def __init__(self, message: str) -> None:
        """Initialize the corruption error.

        Args:
            message: Details of the corruption or failed checksum.
        """
        super().__init__(message, error_code="WORKSPACE_CORRUPTED")


class WorkspaceMigrationError(WorkspaceError):
    """Raised when database or workspace schema migration fails."""

    def __init__(self, message: str, version: int | None = None) -> None:
        """Initialize the migration error.

        Args:
            message: Details of the migration failure.
            version: Target migration version that failed.
        """
        self.version = version
        super().__init__(
            f"Migration failed at version {version}: {message}"
            if version is not None
            else message,
            error_code="WORKSPACE_MIGRATION_FAILED",
        )


class WorkspaceStorageError(WorkspaceError):
    """Raised when filesystem or I/O storage operations fail."""

    def __init__(self, message: str) -> None:
        """Initialize the storage error.

        Args:
            message: Error description.
        """
        super().__init__(message, error_code="WORKSPACE_STORAGE_ERROR")
