"""Domain exceptions and errors for Workspace lifecycle capabilities."""

from __future__ import annotations

from typing import Literal

# These wire aliases and base classes are annotation-only for readers but
# Pydantic resolves them at class-creation time, so they must remain runtime
# imports.
from app.contracts.common.models import (
    ProblemDetails,
    Uuid7,
    WireModel,
)


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


class PersistenceError(WorkspaceError):
    """Base exception for bounded persistence operations."""

    def __init__(self, message: str, error_code: str = "PERSISTENCE_ERROR") -> None:
        """Initialize persistence error."""
        super().__init__(message, error_code=error_code)


class NamespaceAccessDeniedError(PersistenceError):
    """Raised when an operation attempts undeclared table or namespace access."""

    def __init__(
        self,
        namespace: str,
        table: str | None = None,
        message: str = "Access to table or namespace is denied",
    ) -> None:
        """Initialize namespace access denied error."""
        self.namespace = namespace
        self.table = table
        detail = (
            f" (namespace={namespace}, table={table})"
            if table
            else f" (namespace={namespace})"
        )
        super().__init__(f"{message}{detail}", error_code="NAMESPACE_ACCESS_DENIED")


class RevisionConflictError(PersistenceError):
    """Raised when expected revision does not match the current revision."""

    def __init__(
        self,
        namespace: str,
        expected: int,
        actual: int,
        message: str = "Optimistic revision conflict",
    ) -> None:
        """Initialize revision conflict error."""
        self.namespace = namespace
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"{message}: namespace={namespace}, expected={expected}, actual={actual}",
            error_code="REVISION_CONFLICT",
        )


class MigrationChecksumError(PersistenceError):
    """Raised when an already applied migration has a changed checksum."""

    def __init__(
        self,
        namespace: str,
        version: int,
        recorded_checksum: str,
        provided_checksum: str,
        message: str = "Migration checksum mismatch",
    ) -> None:
        """Initialize migration checksum error."""
        self.namespace = namespace
        self.version = version
        self.recorded_checksum = recorded_checksum
        self.provided_checksum = provided_checksum
        super().__init__(
            f"{message}: namespace={namespace}, version={version}, "
            f"recorded={recorded_checksum}, provided={provided_checksum}",
            error_code="MIGRATION_CHECKSUM_MISMATCH",
        )


class EvidenceImmutableError(PersistenceError):
    """Raised when an operation attempts to update or delete append-only evidence."""

    def __init__(
        self,
        namespace: str,
        evidence_id: str | None = None,
        message: str = (
            "Retained append-only evidence is immutable and "
            "cannot be updated or deleted"
        ),
    ) -> None:
        """Initialize evidence immutable error."""
        self.namespace = namespace
        self.evidence_id = evidence_id
        detail = f" (evidence_id={evidence_id})" if evidence_id else ""
        super().__init__(f"{message}{detail}", error_code="EVIDENCE_IMMUTABLE")


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


class SecretResolutionDeniedError(WorkspaceError):
    """Raised when unauthorized caller or mismatched purpose resolves a secret."""

    def __init__(
        self,
        message: str = "Secret resolution denied",
        reason: str | None = None,
        secret_id: str | None = None,
        caller_role: str | None = None,
        allowed_roles: tuple[str, ...] | None = None,
        allowed_adapter_generation: str | None = None,
        provided_adapter_generation: str | None = None,
        allowed_purpose: str | None = None,
        provided_purpose: str | None = None,
    ) -> None:
        """Initialize the secret resolution denied error.

        Args:
            message: Error description.
            reason: Optional failure reason detail.
            secret_id: Optional identifier of the secret reference.
            caller_role: Optional caller role that attempted resolution.
            allowed_roles: Optional tuple of roles authorized to resolve.
            allowed_adapter_generation: Expected adapter generation.
            provided_adapter_generation: Provided adapter generation.
            allowed_purpose: Expected purpose.
            provided_purpose: Provided purpose.
        """
        self.secret_id = secret_id
        self.reason = reason
        self.caller_role = caller_role
        self.allowed_roles = allowed_roles
        self.allowed_adapter_generation = allowed_adapter_generation
        self.provided_adapter_generation = provided_adapter_generation
        self.allowed_purpose = allowed_purpose
        self.provided_purpose = provided_purpose
        detail = f": {reason}" if reason else ""
        super().__init__(f"{message}{detail}", error_code="SECRET_RESOLUTION_DENIED")


class SecretNotFoundError(WorkspaceError):
    """Raised when a requested secret reference is not found."""

    def __init__(
        self,
        secret_id: str | None = None,
        name: str | None = None,
        workspace_id: str | None = None,
        message: str = "Secret reference not found",
    ) -> None:
        """Initialize the secret not found error.

        Args:
            secret_id: Optional identifier of the secret.
            name: Optional name of the secret.
            workspace_id: Optional identifier of the workspace.
            message: Error description.
        """
        self.secret_id = secret_id
        self.name = name
        self.workspace_id = workspace_id
        detail = f" (id={secret_id}, name={name})" if secret_id or name else ""
        super().__init__(f"{message}{detail}", error_code="SECRET_NOT_FOUND")


class SecretRevokedError(WorkspaceError):
    """Raised when attempting to resolve a revoked secret reference."""

    def __init__(
        self,
        secret_id: str | None = None,
        workspace_id: str | None = None,
        revocation_reason: str | None = None,
        message: str = "Secret reference has been revoked and cannot be resolved",
    ) -> None:
        """Initialize the secret revoked error.

        Args:
            secret_id: Optional identifier of the revoked secret.
            workspace_id: Optional identifier of the workspace.
            revocation_reason: Optional reason for revocation.
            message: Error description.
        """
        self.secret_id = secret_id
        self.workspace_id = workspace_id
        self.revocation_reason = revocation_reason
        detail = f" (id={secret_id})" if secret_id else ""
        super().__init__(f"{message}{detail}", error_code="SECRET_REVOKED")


class InvalidHostBindingError(WorkspaceError):
    """Raised when an unauthenticated non-loopback host binding is configured."""

    def __init__(
        self,
        host: str,
        message: str = "Non-loopback host binding requires authenticated remote policy",
    ) -> None:
        """Initialize the invalid host binding error.

        Args:
            host: The invalid or unauthenticated host binding.
            message: Error description.
        """
        self.host = host
        super().__init__(f"{message}: {host}", error_code="INVALID_HOST_BINDING")


# Closed workspace failure-code union from the ratified v1 operation rules.
# ACCOUNT_REGISTRATION_FAILED covers username/password policy violations and
# duplicate registrations; ACCOUNT_AUTHENTICATION_FAILED covers login,
# session-validation, and revocation denials.
type WorkspaceFailureCode = Literal[
    "WORKSPACE_VALIDATION_FAILED",
    "WORKSPACE_NOT_FOUND",
    "WORKSPACE_ALREADY_OPEN",
    "WORKER_UNKNOWN",
    "WORKER_UNTRUSTED",
    "WORKER_EXPIRED",
    "LEASE_UNAVAILABLE",
    "LEASE_TOKEN_STALE",
    "TRANSFER_INVALID",
    "TRANSFER_INCOMPLETE",
    "ISOLATION_CONFLICT",
    "ACCOUNT_REGISTRATION_FAILED",
    "ACCOUNT_AUTHENTICATION_FAILED",
    "CAPABILITY_UNAVAILABLE",
]


class WorkspaceFailure(WireModel):
    """Structured failure envelope shared by the new Workspace capabilities.

    ``WORKER_UNTRUSTED`` covers assignments or leases by untrusted workers,
    ``LEASE_TOKEN_STALE`` covers commits under a superseded token,
    ``TRANSFER_INVALID`` covers hash/size/schema mismatches,
    ``TRANSFER_INCOMPLETE`` covers missing chunks, ``ISOLATION_CONFLICT``
    covers hosted scope collisions at PROVISION, and
    ``CAPABILITY_UNAVAILABLE`` performs no mutation.
    """

    outcome: Literal["FAILURE"] = "FAILURE"
    request_id: Uuid7
    code: WorkspaceFailureCode
    problem: ProblemDetails
    schema_version: Literal[1] = 1


WIRE_FAILURES: dict[str, type[WireModel]] = {
    "WorkspaceFailure": WorkspaceFailure,
}
