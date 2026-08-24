"""Domain exceptions and errors for Interfaces capabilities."""

from __future__ import annotations


class InterfaceError(RuntimeError):
    """Base exception for all interface-related errors."""

    def __init__(self, message: str, error_code: str = "INTERFACE_ERROR") -> None:
        """Initialize the interface error.

        Args:
            message: Human-readable error description.
            error_code: Stable machine-readable error token.
        """
        self.error_code = error_code
        super().__init__(f"[{error_code}] {message}")


class VersionConflictError(InterfaceError):
    """Raised when a mutation has a stale token or version mismatch."""

    def __init__(
        self,
        message: str = "Object version conflict detected",
        expected_version: str | int | None = None,
        current_version: str | int | None = None,
    ) -> None:
        """Initialize the version conflict error.

        Args:
            message: Error description.
            expected_version: Concurrency token supplied in request.
            current_version: Current server-side version of the resource.
        """
        self.expected_version = expected_version
        self.current_version = current_version
        details: list[str] = []
        if expected_version is not None:
            details.append(f"expected={expected_version}")
        if current_version is not None:
            details.append(f"current={current_version}")
        suffix = f" ({', '.join(details)})" if details else ""
        super().__init__(f"{message}{suffix}", error_code="VERSION_CONFLICT")


class IdempotencyConflictError(InterfaceError):
    """Raised when an in-flight mutation is executing for the same idempotency key."""

    def __init__(
        self,
        idempotency_key: str,
        message: str = "A mutation is already executing for this idempotency key",
    ) -> None:
        """Initialize the idempotency conflict error.

        Args:
            idempotency_key: Target idempotency key.
            message: Error description.
        """
        self.idempotency_key = idempotency_key
        super().__init__(
            f"{message} (key={idempotency_key})",
            error_code="IDEMPOTENCY_CONFLICT",
        )


class EventCursorExpiredError(InterfaceError):
    """Raised when an SSE event cursor is older than the retention window."""

    def __init__(
        self,
        cursor: str,
        message: str = "Event stream cursor is expired or invalid; resync required",
    ) -> None:
        """Initialize the event cursor expired error.

        Args:
            cursor: Requested event cursor / Last-Event-ID.
            message: Error description.
        """
        self.cursor = cursor
        super().__init__(
            f"{message} (cursor={cursor})",
            error_code="EVENT_CURSOR_EXPIRED",
        )


class JobNotFoundError(InterfaceError):
    """Raised when an asynchronous job cannot be found."""

    def __init__(self, job_id: str) -> None:
        """Initialize the job not found error.

        Args:
            job_id: ID of the missing job.
        """
        self.job_id = job_id
        super().__init__(f"Job '{job_id}' was not found", error_code="JOB_NOT_FOUND")


class ArtifactAccessDeniedError(InterfaceError):
    """Raised when an artifact download is invalid, uncommitted, or escapes root."""

    def __init__(self, path: str, reason: str) -> None:
        """Initialize the artifact access denied error.

        Args:
            path: Target artifact path or filename.
            reason: Specific reason why access was denied.
        """
        self.path = path
        self.reason = reason
        super().__init__(
            f"Artifact access denied for '{path}': {reason}",
            error_code="ARTIFACT_ACCESS_DENIED",
        )


class ApiIncompatibleError(InterfaceError):
    """Raised when a client request uses an incompatible or unsupported API version."""

    def __init__(
        self,
        client_version: str,
        supported_versions: tuple[str, ...],
        message: str = "API version is incompatible; upgrade required",
    ) -> None:
        """Initialize the API incompatibility error.

        Args:
            client_version: Version requested by client.
            supported_versions: Supported API versions.
            message: Error description.
        """
        self.client_version = client_version
        self.supported_versions = supported_versions
        versions_str = ", ".join(supported_versions)
        super().__init__(
            f"{message} (requested={client_version}, supported={versions_str})",
            error_code="UPGRADE_REQUIRED",
        )


class CommandNotFoundError(InterfaceError):
    """Raised when an automation command name is not registered."""

    def __init__(self, command_name: str) -> None:
        """Initialize command not found error.

        Args:
            command_name: Unrecognized command name string.
        """
        self.command_name = command_name
        super().__init__(
            f"Command '{command_name}' is not recognized",
            error_code="COMMAND_NOT_FOUND",
        )


class CommandValidationError(InterfaceError):
    """Raised when an automation command payload fails schema validation."""

    def __init__(self, command_name: str, validation_errors: tuple[str, ...]) -> None:
        """Initialize command validation error.

        Args:
            command_name: Target command name string.
            validation_errors: Tuple of validation failure messages.
        """
        self.command_name = command_name
        self.validation_errors = validation_errors
        errors_str = "; ".join(validation_errors)
        super().__init__(
            f"Validation failed for command '{command_name}': {errors_str}",
            error_code="COMMAND_VALIDATION_FAILED",
        )


class CommandExecutionError(InterfaceError):
    """Raised when an automation command fails during execution."""

    def __init__(self, command_name: str, reason: str) -> None:
        """Initialize command execution error.

        Args:
            command_name: Target command name string.
            reason: Specific execution failure reason.
        """
        self.command_name = command_name
        self.reason = reason
        super().__init__(
            f"Execution failed for command '{command_name}': {reason}",
            error_code="COMMAND_EXECUTION_FAILED",
        )


class DurableJobNotFoundError(InterfaceError):
    """Raised when a durable command run cannot be found."""

    def __init__(self, durable_job_id: str) -> None:
        """Initialize durable job not found error.

        Args:
            durable_job_id: ID of the missing durable job.
        """
        self.durable_job_id = durable_job_id
        super().__init__(
            f"Durable job '{durable_job_id}' was not found",
            error_code="DURABLE_JOB_NOT_FOUND",
        )
