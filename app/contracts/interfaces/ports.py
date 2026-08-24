"""Public capability protocols (ports) for Interfaces domain."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pathlib import Path

    from app.contracts.interfaces.models import (
        ApiCompatibilityReport,
        ApiDeprecationNotice,
        ApplicationCommandRequest,
        ApplicationCommandResult,
        ArtifactDownloadRequest,
        ArtifactDownloadResponse,
        AsyncJobRef,
        AsyncJobState,
        DurableCommandRef,
        DurableJobStatus,
        EventReplayBatch,
        InterfaceEventEnvelope,
        OpenApiManifest,
    )


@runtime_checkable
class ServeApiEventsCapability(Protocol):
    """Protocol for serving versioned HTTP/OpenAPI contracts and SSE events."""

    def get_openapi_manifest(self) -> OpenApiManifest:
        """Get the complete OpenAPI 3.1 contract specification for served endpoints.

        Returns:
            OpenApiManifest containing all exposed route and schema definitions.
        """
        ...

    def serve_versioned_api(self, api_version: str = "v1") -> OpenApiManifest:
        """Serve versioned API contracts and route schemas for a version label.

        Args:
            api_version: API version string (e.g. 'v1').

        Returns:
            OpenApiManifest filtered and validated for the specified version.

        Raises:
            ApiIncompatibleError: If requested API version is unsupported.
        """
        ...

    def validate_concurrency_token(
        self,
        resource_id: str,
        expected_version: str | int | None,
        current_version: str | int,
    ) -> bool:
        """Validate an optimistic concurrency token against current version.

        Args:
            resource_id: Protected resource identifier.
            expected_version: Expected token from If-Match header.
            current_version: Current server-side version of the resource.

        Returns:
            True if version matches and mutation is permitted.

        Raises:
            VersionConflictError: If expected version does not match current version.
        """
        ...

    def deduplicate_mutation(
        self,
        idempotency_key: str,
        session_id: str,
        command_type: str,
        execute_fn: Callable[[], dict[str, object]],
    ) -> dict[str, object]:
        """Execute a mutation idempotently, returning cached results on repeat.

        Args:
            idempotency_key: Client-supplied idempotency key.
            session_id: Session identifier scope.
            command_type: Command classification.
            execute_fn: Callable producing the mutation response dictionary.

        Returns:
            Dictionary response payload from initial execution or cached replay.

        Raises:
            IdempotencyConflictError: If a concurrent execution is already in flight.
        """
        ...

    def publish_interface_event(
        self,
        event_type: str,
        topic: str,
        payload: dict[str, object],
    ) -> InterfaceEventEnvelope:
        """Publish a typed event into the interface event buffer.

        Args:
            event_type: Domain event classification name.
            topic: Topic or channel name.
            payload: Event data dictionary.

        Returns:
            InterfaceEventEnvelope with assigned sequence and event ID.
        """
        ...

    def replay_interface_events(
        self,
        last_event_id: str | None,
        max_events: int = 100,
    ) -> EventReplayBatch:
        """Replay retained interface events following a cursor.

        Args:
            last_event_id: Last received event ID / cursor string, or None for latest.
            max_events: Maximum number of events to return in this batch.

        Returns:
            EventReplayBatch with envelopes, next cursor, and resync flags.

        Raises:
            EventCursorExpiredError: If requested cursor is beyond the retention window.
        """
        ...

    def submit_async_job(
        self,
        command_type: str,
        runner_fn: Callable[[AsyncJobRef], None] | None = None,
    ) -> AsyncJobRef:
        """Submit a long-running task and return an AsyncJobRef immediately.

        Args:
            command_type: Initiating action category.
            runner_fn: Optional synchronous runner callable.

        Returns:
            AsyncJobRef with unique job ID and initial QUEUED or RUNNING state.
        """
        ...

    def get_async_job(self, job_id: str) -> AsyncJobRef:
        """Query the current state and progress of an asynchronous job.

        Args:
            job_id: Unique job UUID string.

        Returns:
            AsyncJobRef describing current state, progress, and stage.

        Raises:
            JobNotFoundError: If job ID is not registered.
        """
        ...

    def update_async_job(
        self,
        job_id: str,
        *,
        state: AsyncJobState | None = None,
        progress: float | None = None,
        stage: str | None = None,
        error_message: str | None = None,
        result_ref: str | None = None,
    ) -> AsyncJobRef:
        """Update the state or progress of an active asynchronous job.

        Args:
            job_id: Target job UUID string.
            state: Optional updated lifecycle state.
            progress: Optional updated progress float between 0.0 and 1.0.
            stage: Optional updated stage description.
            error_message: Optional error message on failure.
            result_ref: Optional result reference pointer on completion.

        Returns:
            Updated AsyncJobRef.

        Raises:
            JobNotFoundError: If job ID is not registered.
        """
        ...

    def validate_artifact_download(
        self,
        request: ArtifactDownloadRequest,
        storage_root: Path,
        committed_artifacts: dict[str, Path] | None = None,
    ) -> ArtifactDownloadResponse:
        """Validate and resolve an artifact file download.

        Validates artifact committed state, requested filename, byte range,
        and strict path containment against directory traversal.

        Args:
            request: Download request specification.
            storage_root: Root filesystem directory containing committed artifacts.
            committed_artifacts: Optional mapping of committed artifact IDs to paths.

        Returns:
            ArtifactDownloadResponse containing validated data bytes and range info.

        Raises:
            ArtifactAccessDeniedError: If artifact is uncommitted, missing,
                or escapes storage root containment.
        """
        ...

    def check_api_compatibility(self, client_version: str) -> ApiCompatibilityReport:
        """Check whether a client API version is compatible with this server.

        Args:
            client_version: Semantic version string of the client.

        Returns:
            ApiCompatibilityReport with status, deprecations, and breaking changes.
        """
        ...

    def get_deprecations(self) -> tuple[ApiDeprecationNotice, ...]:
        """Get all active machine-readable deprecation notices for this API version.

        Returns:
            Tuple of ApiDeprecationNotice descriptors.
        """
        ...


@runtime_checkable
class AutomateCommandsCapability(Protocol):
    """Protocol for unified CLI, MCP, and application command automation."""

    def delegate_application_call(
        self,
        request: ApplicationCommandRequest,
    ) -> ApplicationCommandResult:
        """Execute a normalized application command across UI, CLI, or MCP callers.

        Args:
            request: Standardized command invocation request.

        Returns:
            ApplicationCommandResult describing status, data, and errors.
        """
        ...

    def register_command_handler(
        self,
        command_name: str,
        handler: Callable[[dict[str, object]], dict[str, object]],
    ) -> None:
        """Register a handler callback for an application command name.

        Args:
            command_name: Canonical registered command name string.
            handler: Callable taking payload dictionary and returning output dictionary.
        """
        ...

    def track_durable_command(
        self,
        command_name: str,
        payload: dict[str, object],
        runner_fn: Callable[[DurableCommandRef], None] | None = None,
    ) -> DurableCommandRef:
        """Admit a durable long-running CLI or MCP command and return reference.

        Args:
            command_name: Target action or command name.
            payload: Parameter dictionary.
            runner_fn: Optional synchronous runner callable.

        Returns:
            DurableCommandRef with unique job ID and initial QUEUED state.
        """
        ...

    def get_durable_command_status(
        self,
        durable_job_id: str,
    ) -> DurableCommandRef:
        """Query lifecycle state and progress of a durable command.

        Args:
            durable_job_id: Unique durable job UUID string.

        Returns:
            DurableCommandRef describing current status, progress, and stage.

        Raises:
            DurableJobNotFoundError: If durable job is not registered.
        """
        ...

    def cancel_durable_command(
        self,
        durable_job_id: str,
    ) -> DurableCommandRef:
        """Request cooperative cancellation of an active durable command.

        Args:
            durable_job_id: Target durable job UUID string.

        Returns:
            Updated DurableCommandRef marked with cancellation requested.

        Raises:
            DurableJobNotFoundError: If durable job is not registered.
        """
        ...

    def update_durable_command(
        self,
        durable_job_id: str,
        *,
        status: DurableJobStatus | None = None,
        progress: float | None = None,
        stage: str | None = None,
        result: dict[str, object] | None = None,
        error: str | None = None,
    ) -> DurableCommandRef:
        """Update lifecycle state or progress of a durable command.

        Args:
            durable_job_id: Target durable job UUID string.
            status: Optional updated lifecycle state.
            progress: Optional progress float between 0.0 and 1.0.
            stage: Optional stage description.
            result: Optional completed result payload dictionary.
            error: Optional error description string.

        Returns:
            Updated DurableCommandRef.

        Raises:
            DurableJobNotFoundError: If durable job is not registered.
        """
        ...
