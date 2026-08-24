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


class SettingsValidationError(WorkspaceError):
    """Raised when workspace settings fail field validation.

    Attributes:
        field_errors: Mapping of settings field name to error description.
    """

    def __init__(self, field_errors: dict[str, str]) -> None:
        """Initialize the settings validation error.

        Args:
            field_errors: Mapping of invalid field name to error description.
        """
        self.field_errors = field_errors
        detail = "; ".join(f"{k}: {v}" for k, v in sorted(field_errors.items()))
        super().__init__(
            f"Workspace settings validation failed: {detail}",
            error_code="SETTINGS_VALIDATION_FAILED",
        )


class ServerRuntimeValidationError(WorkspaceError):
    """Raised when launcher/server runtime settings are invalid.

    Attributes:
        errors: Tuple of field-level validation error descriptions.
    """

    def __init__(self, errors: tuple[str, ...]) -> None:
        """Initialize the server runtime validation error.

        Args:
            errors: Validation error descriptions.
        """
        self.errors = errors
        super().__init__(
            f"Server runtime settings invalid: {'; '.join(errors)}",
            error_code="SERVER_RUNTIME_INVALID",
        )


class UnsupportedRuntimeError(WorkspaceError):
    """Raised when the host platform violates the runtime support profile."""

    def __init__(self, message: str) -> None:
        """Initialize the unsupported runtime error.

        Args:
            message: Details of the unsupported architecture or filesystem.
        """
        super().__init__(message, error_code="RUNTIME_UNSUPPORTED")


class LocalSessionError(WorkspaceError):
    """Base exception for local session and access authentication failures."""

    def __init__(self, message: str, error_code: str = "SESSION_ERROR") -> None:
        """Initialize the local session error.

        Args:
            message: Error description.
            error_code: Stable machine-readable error token.
        """
        super().__init__(message, error_code=error_code)


class SessionDeniedError(LocalSessionError):
    """Raised when session issuance or verification is denied."""

    def __init__(
        self,
        message: str = "Session access denied",
        reason: str | None = None,
    ) -> None:
        """Initialize the session denied error.

        Args:
            message: Error description.
            reason: Optional failure reason detail.
        """
        detail = f": {reason}" if reason else ""
        super().__init__(f"{message}{detail}", error_code="SESSION_DENIED")


class SessionExpiredError(LocalSessionError):
    """Raised when a local session token has expired."""

    def __init__(
        self,
        message: str = "Local session has expired",
        expired_at: str | None = None,
    ) -> None:
        """Initialize the session expired error.

        Args:
            message: Error description.
            expired_at: Optional ISO 8601 UTC timestamp of expiry.
        """
        detail = f" at {expired_at}" if expired_at else ""
        super().__init__(f"{message}{detail}", error_code="SESSION_EXPIRED")


class NonLoopbackAccessDeniedError(LocalSessionError):
    """Raised when access from a non-loopback address is denied."""

    def __init__(
        self,
        client_host: str,
        message: str = "Access denied for non-loopback client without authorization",
    ) -> None:
        """Initialize the non-loopback access denied error.

        Args:
            client_host: Client host IP address that was rejected.
            message: Error description.
        """
        self.client_host = client_host
        super().__init__(
            f"{message} (client_host={client_host})",
            error_code="NON_LOOPBACK_ACCESS_DENIED",
        )


class SystemNotReadyError(WorkspaceError):
    """Raised when an operation requires full readiness but the system is degraded."""

    def __init__(self, reasons: tuple[str, ...]) -> None:
        """Initialize the system not ready error.

        Args:
            reasons: Tuple of reasons why the system is not ready.
        """
        self.reasons = reasons
        super().__init__(
            f"System is not ready: {'; '.join(reasons)}",
            error_code="SYSTEM_NOT_READY",
        )


class DiagnosticBundleError(WorkspaceError):
    """Raised when diagnostic bundle generation, redaction, or packaging fails."""

    def __init__(
        self, message: str, error_code: str = "DIAGNOSTIC_BUNDLE_FAILED"
    ) -> None:
        """Initialize the diagnostic bundle error.

        Args:
            message: Error description.
            error_code: Stable machine-readable error token.
        """
        super().__init__(message, error_code=error_code)
