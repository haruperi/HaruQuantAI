"""Public domain models and data transfer objects for Interfaces capabilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class MutationStatus(StrEnum):
    """Execution status of an idempotent mutation."""

    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AsyncJobState(StrEnum):
    """Lifecycle state of an asynchronous interface job."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class CommandSource(StrEnum):
    """Originating interface source of an application command."""

    CLI = "CLI"
    UI = "UI"
    MCP = "MCP"
    API = "API"
    SYSTEM = "SYSTEM"


class CommandStatus(StrEnum):
    """Execution status outcome of an application command."""

    SUCCESS = "SUCCESS"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    CANCELLED = "CANCELLED"
    PENDING = "PENDING"


class DurableJobStatus(StrEnum):
    """Lifecycle state of a durable long-running CLI/MCP command."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class ApiVersion:
    """Semantic version descriptor for an API surface.

    Attributes:
        major: Major version integer.
        minor: Minor version integer.
        patch: Patch version integer.
        label: Standard URL prefix label (e.g. 'v1').
        is_deprecated: True if this API version is marked for deprecation.
    """

    major: int = 1
    minor: int = 0
    patch: int = 0
    label: str = "v1"
    is_deprecated: bool = False


@dataclass(frozen=True, slots=True)
class ApiRouteSpec:
    """Specification of an exposed API route.

    Attributes:
        path: Route URL template.
        method: HTTP verb (GET, POST, PUT, DELETE, PATCH).
        summary: Concise human-readable operation summary.
        description: Detailed endpoint documentation.
        tags: Categorization tags.
        version: API version label (e.g. 'v1').
        is_deprecated: True if endpoint is deprecated.
        deprecation_message: Optional deprecation advice or replacement pointer.
    """

    path: str
    method: str
    summary: str
    description: str = ""
    tags: tuple[str, ...] = ()
    version: str = "v1"
    is_deprecated: bool = False
    deprecation_message: str | None = None


@dataclass(frozen=True, slots=True)
class OpenApiManifest:
    """OpenAPI 3.1 contract specification for served endpoints.

    Attributes:
        openapi_version: OpenAPI specification version.
        title: API title.
        version: Application API version string.
        description: API description.
        routes: Tuple of exposed route specifications.
        servers: Tuple of server URL base paths.
    """

    openapi_version: str = "3.1.0"
    title: str = "HaruQuantAI API"
    version: str = "1.0.0"
    description: str = (
        "Versioned HTTP/SSE interface contracts for HaruQuantAI platform."
    )
    routes: tuple[ApiRouteSpec, ...] = ()
    servers: tuple[str, ...] = ("/api/v1",)


@dataclass(frozen=True, slots=True)
class ConcurrencyToken:
    """Optimistic concurrency token preventing lost updates.

    Attributes:
        resource_id: Identifier of the protected resource.
        version: Monotonic version integer.
        token_hash: Cryptographic hash or ETag string.
        issued_at: ISO 8601 UTC timestamp of token issuance.
    """

    resource_id: str
    version: int
    token_hash: str
    issued_at: str


@dataclass(frozen=True, slots=True)
class MutationIdempotencyRecord:
    """Record of an executed or in-flight mutation for deduplication.

    Attributes:
        idempotency_key: Client-supplied idempotency key.
        session_id: Session or caller scope identifier.
        command_type: Command or mutation action category.
        status: Current mutation execution status.
        response_payload: Cached response dictionary if completed successfully.
        error_code: Error code if execution failed.
        created_at: ISO 8601 UTC timestamp of first receipt.
        completed_at: ISO 8601 UTC timestamp of execution completion.
    """

    idempotency_key: str
    session_id: str
    command_type: str
    status: MutationStatus = MutationStatus.IN_PROGRESS
    response_payload: dict[str, object] | None = None
    error_code: str | None = None
    created_at: str = ""
    completed_at: str | None = None


@dataclass(frozen=True, slots=True)
class EventCursor:
    """Cursor position for SSE event stream consumption and replay.

    Attributes:
        last_event_id: String event ID of the last received event.
        sequence_number: Monotonically increasing event sequence index.
        timestamp: ISO 8601 UTC timestamp of the cursor event.
    """

    last_event_id: str
    sequence_number: int
    timestamp: str


@dataclass(frozen=True, slots=True)
class InterfaceEventEnvelope:
    """Typed event envelope emitted over the interface event stream.

    Attributes:
        event_id: Unique event identifier / cursor string.
        sequence_number: Monotonic global sequence number.
        event_type: Domain event classification name.
        topic: Channel or domain topic.
        payload: Event payload dictionary.
        timestamp: ISO 8601 UTC timestamp of emission.
    """

    event_id: str
    sequence_number: int
    event_type: str
    topic: str
    payload: dict[str, object] = field(default_factory=dict)
    timestamp: str = ""


@dataclass(frozen=True, slots=True)
class EventReplayBatch:
    """Batch of replayed events from an SSE stream query.

    Attributes:
        events: Tuple of event envelopes in sequence order.
        next_cursor: Cursor identifier for the next batch or latest event.
        has_more: True if additional events remain beyond this batch.
        is_resync_required: True if requested cursor expired and resync needed.
    """

    events: tuple[InterfaceEventEnvelope, ...] = ()
    next_cursor: str | None = None
    has_more: bool = False
    is_resync_required: bool = False


@dataclass(frozen=True, slots=True)
class AsyncJobRef:
    """Reference handle to an asynchronously executing task.

    Attributes:
        job_id: Unique job UUID.
        command_type: Initiating action or command type.
        state: Current lifecycle state.
        progress: Normalized progress float between 0.0 and 1.0.
        stage: Current human-readable execution stage.
        error_message: Error description if state is FAILED.
        result_ref: Reference pointer to completed result artifact if available.
        created_at: ISO 8601 UTC timestamp of job creation.
        updated_at: ISO 8601 UTC timestamp of last state update.
    """

    job_id: str
    command_type: str
    state: AsyncJobState = AsyncJobState.QUEUED
    progress: float = 0.0
    stage: str = ""
    error_message: str | None = None
    result_ref: str | None = None
    created_at: str = ""
    updated_at: str = ""


@dataclass(frozen=True, slots=True)
class ArtifactRangeSpec:
    """Byte range specification for partial artifact downloads.

    Attributes:
        start_byte: Zero-based starting byte offset.
        end_byte: Inclusive ending byte offset if specified.
        total_bytes: Total artifact content length in bytes.
    """

    start_byte: int = 0
    end_byte: int | None = None
    total_bytes: int = 0


@dataclass(frozen=True, slots=True)
class ArtifactDownloadRequest:
    """Request to download or inspect an artifact file.

    Attributes:
        artifact_id: Identifier of the committed artifact.
        filename: Requested target filename.
        range_spec: Optional byte range specification.
    """

    artifact_id: str
    filename: str
    range_spec: ArtifactRangeSpec | None = None


@dataclass(frozen=True, slots=True)
class ArtifactDownloadResponse:
    """Validated artifact download payload.

    Attributes:
        artifact_id: Identifier of the downloaded artifact.
        filename: Verified filename.
        content_type: MIME type of the artifact content.
        total_size: Total artifact byte size.
        data_bytes: Payload binary content.
        is_partial: True if response satisfies a partial range request.
        range_spec: Applied byte range specification if partial.
    """

    artifact_id: str
    filename: str
    content_type: str
    total_size: int
    data_bytes: bytes
    is_partial: bool = False
    range_spec: ArtifactRangeSpec | None = None


@dataclass(frozen=True, slots=True)
class ApiDeprecationNotice:
    """Notice describing a deprecated API endpoint or feature.

    Attributes:
        feature_or_endpoint: Target route or capability identifier.
        deprecated_version: Version when deprecation began.
        sunset_version: Planned removal version.
        replacement: Recommended replacement route or capability.
        migration_guide_url: Optional link to migration documentation.
    """

    feature_or_endpoint: str
    deprecated_version: str
    sunset_version: str
    replacement: str
    migration_guide_url: str = ""


@dataclass(frozen=True, slots=True)
class ApiCompatibilityReport:
    """Report on client API version compatibility.

    Attributes:
        is_compatible: True if client version is fully supported.
        current_version: Current server API version string.
        client_version: Client API version string.
        deprecations: Active deprecation notices applicable to this version.
        breaking_changes: List of breaking changes if version is incompatible.
    """

    is_compatible: bool
    current_version: str
    client_version: str
    deprecations: tuple[ApiDeprecationNotice, ...] = ()
    breaking_changes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ApplicationCommandRequest:
    """Presentation-neutral application command invocation request.

    Attributes:
        command_name: Canonical registered command name.
        payload: Input argument mapping.
        source: Calling interface type (CLI, UI, MCP, API, SYSTEM).
        correlation_id: Distributed tracing correlation UUID string.
        session_id: Client or session scope identifier.
    """

    command_name: str
    payload: dict[str, object] = field(default_factory=dict)
    source: CommandSource = CommandSource.CLI
    correlation_id: str = ""
    session_id: str = ""


@dataclass(frozen=True, slots=True)
class ApplicationCommandResult:
    """Normalized application command execution result.

    Attributes:
        command_name: Invoked command name.
        status: Execution status (SUCCESS, VALIDATION_FAILED, etc.).
        data: Execution result payload if successful.
        errors: Tuple of validation or execution error messages.
        correlation_id: Propagated correlation UUID string.
        durable_job_id: Associated durable job UUID string if asynchronous.
    """

    command_name: str
    status: CommandStatus = CommandStatus.SUCCESS
    data: dict[str, object] | None = None
    errors: tuple[str, ...] = ()
    correlation_id: str = ""
    durable_job_id: str | None = None


@dataclass(frozen=True, slots=True)
class DurableCommandRef:
    """Handle to a durable long-running CLI or MCP command execution.

    Attributes:
        durable_job_id: Unique durable job UUID string.
        command_name: Associated command name.
        status: Current lifecycle state (QUEUED, RUNNING, etc.).
        progress: Progress ratio between 0.0 and 1.0.
        stage: Human-readable stage description.
        is_cancel_requested: True if cancellation was requested.
        result: Completed result dictionary if finished successfully.
        error: Error description if execution failed.
        created_at: ISO 8601 UTC timestamp of job creation.
        updated_at: ISO 8601 UTC timestamp of last status update.
    """

    durable_job_id: str
    command_name: str
    status: DurableJobStatus = DurableJobStatus.QUEUED
    progress: float = 0.0
    stage: str = ""
    is_cancel_requested: bool = False
    result: dict[str, object] | None = None
    error: str | None = None
    created_at: str = ""
    updated_at: str = ""
