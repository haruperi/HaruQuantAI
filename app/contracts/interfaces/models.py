"""Public domain models and data transfer objects for Interfaces capabilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

# Cross-namespace reference records are annotation-only for readers, but
# Pydantic resolves them at class-creation time, so they must remain runtime
# imports.
from app.contracts.analytics.models import (  # noqa: TC001
    OperationalJournalArtifact,
    OperatorQualification,
)
from app.contracts.broker.models import (  # noqa: TC001
    BrokerAccountSnapshot,
    BrokerMarketState,
)
from app.contracts.common.events import DomainEvent  # noqa: TC001
from app.contracts.common.models import (
    CapabilityIdentifier,
    CapabilitySnapshot,
    ContentHash,
    DecimalValue,
    FeatureIdentifier,
    FeatureState,
    JsonObject,
    TradingModeValue,
    TradingSessionStateValue,
    UtcTimestamp,
    Uuid7,
    ValidationIssue,
    WireModel,
)
from app.contracts.orchestration.models import ProjectGraph  # noqa: TC001
from app.contracts.portfolio.models import (  # noqa: TC001
    CorrelationMatrix,
    PortfolioConstraintSet,
    PortfolioMember,
    PortfolioResult,
)
from app.contracts.research.models import ResearchManifest  # noqa: TC001
from app.contracts.risk.models import (  # noqa: TC001
    KillSwitchState,
    RiskDecision,
)
from app.contracts.trading.models import (  # noqa: TC001
    ExecutionAuthorityRef,
    TradePlan,
    TradingSession,
    TradingSessionRef,
)


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


# ---------------------------------------------------------------------------
# Ratified v1 wire contracts (additive; the frozen v1 dataclasses above stay
# unchanged as process contracts). Wire projections of frozen records are
# named ``<Record>Wire``; wire-native records keep their inventory names.
# Process-local callables, ``Path`` inputs, binary payloads, and the v1
# ``InterfaceEventEnvelope`` never enter wire schemas: the wire form of an
# interface-stream event is the common ``DomainEvent`` envelope per Shared
# Contracts §4.5. Wire progress ratios use ``DecimalValue`` in [0, 1] so no
# binary floats cross the boundary.

# Constrained local string aliases reused across Interfaces wire records.
type NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]
type ApiVersionLabel = Annotated[str, StringConstraints(pattern=r"^v[1-9][0-9]*$")]
# Domain assumption: artifact filenames are single path segments carrying no
# separators; traversal names are rejected by the record validator.
type ArtifactFilename = Annotated[str, StringConstraints(pattern=r"^[^/\\]+$")]

# Closed literal unions reused across Interfaces wire records. The trading
# mode, trading session state, and feature state unions reuse the Shared
# Contracts §4.3 core enums imported from ``app/contracts/common/`` instead
# of redeclaring equivalent unions.
type AsyncJobStateValue = Literal[
    "QUEUED", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"
]
type CommandSourceValue = Literal["CLI", "UI", "MCP", "API", "SYSTEM"]
type BulkConflictPolicy = Literal["REJECT", "KEEP_EXISTING", "CREATE_NEW_VERSION"]
type McpOperationName = Literal[
    "LIST_PROJECTS",
    "LIST_DATABANKS",
    "LIST_STRATEGIES",
    "GET_STRATEGY_STATISTICS",
    "RUN_PROJECT",
    "STOP_PROJECT",
]
type TradingActionKind = Literal[
    "ORDER", "CANCEL", "MODIFY", "CLOSE", "FLATTEN", "HOLD", "PROTECTION"
]
type HealthState = Literal["HEALTHY", "DEGRADED", "UNHEALTHY"]
type TradingEventScope = Literal["TRADING", "RISK", "BROKER", "ALL"]


def _require_present(fields: tuple[tuple[str, object], ...]) -> None:
    """Reject an operation request that omits a required field.

    Args:
        fields: ``(field name, value)`` pairs that must not be None.

    Raises:
        ValueError: Any listed field is None.
    """
    for name, value in fields:
        if value is None:
            raise ValueError("required field is missing: " + name)


def _require_absent(fields: tuple[tuple[str, object], ...]) -> None:
    """Reject an operation request that sets a forbidden field.

    Args:
        fields: ``(field name, value)`` pairs that must be None.

    Raises:
        ValueError: Any listed field is not None.
    """
    for name, value in fields:
        if value is not None:
            raise ValueError("forbidden field is set: " + name)


class ApiVersionWire(WireModel):
    """Wire projection of the served API semantic version (record R1)."""

    major: int = Field(default=1, ge=1)
    minor: int = Field(default=0, ge=0)
    patch: int = Field(default=0, ge=0)
    label: ApiVersionLabel = "v1"
    is_deprecated: bool = False
    schema_version: Literal[1] = 1


class ConcurrencyTokenWire(WireModel):
    """Wire projection of an optimistic concurrency token (record R2).

    A stale ``If-Match`` returns 412 ``VERSION_CONFLICT`` with no partial
    mutation.
    """

    resource_id: Uuid7
    version: int = Field(ge=1)
    token_hash: ContentHash
    issued_at: UtcTimestamp
    schema_version: Literal[1] = 1


class EventCursorWire(WireModel):
    """Wire projection of an SSE replay cursor position (record R3).

    ``Last-Event-ID`` reconnect never duplicates an externally visible
    transition.
    """

    last_event_id: Uuid7
    sequence_number: int = Field(ge=0)
    timestamp: UtcTimestamp
    schema_version: Literal[1] = 1


class EventReplayBatchWire(WireModel):
    """Wire projection of one SSE replay batch (record R4).

    Retention-expired cursors raise ``EVENT_CURSOR_EXPIRED`` and set
    ``is_resync_required``.
    """

    events: tuple[DomainEvent, ...] = ()
    next_cursor: Uuid7 | None = None
    has_more: bool = False
    is_resync_required: bool = False
    schema_version: Literal[1] = 1


class AsyncJobRefWire(WireModel):
    """Wire projection of an asynchronous job handle (record R5).

    Long-running actions return a job ID immediately; the wire progress
    ratio is a ``DecimalValue`` string, not a binary float.
    """

    job_id: Uuid7
    command_type: NonEmptyStr
    state: AsyncJobStateValue = "QUEUED"
    progress: DecimalValue = "0"
    stage: str = ""
    error_message: str | None = None
    result_ref: Uuid7 | None = None
    created_at: UtcTimestamp
    updated_at: UtcTimestamp
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_progress(self) -> AsyncJobRefWire:
        """Reject progress ratios outside the unit interval.

        Returns:
            The validated job reference.

        Raises:
            ValueError: ``progress`` is not within [0, 1].
        """
        # The wire ratio is an exact decimal string, so compare it as a
        # Decimal rather than converting through a binary float.
        if not (Decimal(0) <= Decimal(self.progress) <= Decimal(1)):
            raise ValueError("progress must be within [0, 1]")
        return self


class ArtifactDownloadRequestWire(WireModel):
    """Wire projection of an artifact download request (record R6).

    Uncommitted artifacts and traversal attempts are denied
    ``ARTIFACT_ACCESS_DENIED``; the v1 ``ArtifactRangeSpec`` and the binary
    ``ArtifactDownloadResponse`` stay process contracts because response
    bytes are a transport body, not a record.
    """

    artifact_id: Uuid7
    filename: ArtifactFilename
    range_start_byte: int = Field(default=0, ge=0)
    range_end_byte: int | None = Field(default=None, ge=0)
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_filename_and_range(self) -> ArtifactDownloadRequestWire:
        """Reject traversal filenames and inverted byte ranges.

        Returns:
            The validated download request.

        Raises:
            ValueError: ``filename`` is a traversal name or
                ``range_end_byte`` precedes ``range_start_byte``.
        """
        # A filename without separators can still traverse only as one of
        # the two dot directory aliases.
        if self.filename in (".", ".."):
            raise ValueError("filename must not be a traversal name")
        if self.range_end_byte is not None and (
            self.range_end_byte < self.range_start_byte
        ):
            raise ValueError("range_end_byte must be at or after range_start_byte")
        return self


class BulkRequestToken(WireModel):
    """Wire-native pinned bulk request token (record R7).

    Pairs with the Analytics-owned ``BulkSelectionToken``; replay with the
    same token and idempotency key never broadens scope or duplicates
    mutations.
    """

    token_id: Uuid7
    pinned_query_hash: ContentHash
    estimated_impact: int = Field(ge=1)
    idempotency_key: NonEmptyStr
    conflict_policy: BulkConflictPolicy
    created_at: UtcTimestamp
    expires_at: UtcTimestamp
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_expiry(self) -> BulkRequestToken:
        """Reject tokens that expire at or before creation.

        Returns:
            The validated bulk request token.

        Raises:
            ValueError: ``expires_at`` is not after ``created_at``.
        """
        # UtcTimestamp strings use one fixed-width format, so lexicographic
        # order equals chronological order.
        if self.expires_at <= self.created_at:
            raise ValueError("expires_at must be after created_at")
        return self


class AutomationCommand(WireModel):
    """Wire-native presentation-neutral automation command (record R8).

    UI-exported manifests dry-run identically through CLI and API; secret
    values are ``SecretRef`` identities resolved explicitly before
    execution, never inline payloads.
    """

    command_name: NonEmptyStr
    payload: JsonObject = Field(default_factory=dict)
    source: CommandSourceValue = "CLI"
    correlation_id: Uuid7 | None = None
    session_id: str = ""
    secret_refs: tuple[Uuid7, ...] = ()
    schema_version: Literal[1] = 1


class AutomationCommandDescriptor(WireModel):
    """Nested command descriptor inside ``AutomationSchema`` (record R9).

    ``input_schema`` and ``output_schema`` are bounded JSON-Schema
    documents, the declared extension surface of the record.
    """

    command_name: NonEmptyStr
    input_schema: JsonObject
    output_schema: JsonObject
    is_durable: bool


class AutomationSchema(WireModel):
    """Wire-native published automation command schema set (record R9)."""

    schema_id: Uuid7
    contract_version: str = "1.0.0"
    commands: tuple[AutomationCommandDescriptor, ...]
    exported_at: UtcTimestamp
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class McpOperation(WireModel):
    """Wire-native MCP tool invocation (record R10).

    MCP enforces identical validation, authorization, idempotency, and
    audit as direct API; no raw paths, database access, compilers, or
    plugin credentials cross the adapter.
    """

    operation: McpOperationName
    arguments: JsonObject = Field(default_factory=dict)
    schema_version: Literal[1] = 1


class ResearchPreview(WireModel):
    """Wire-native research preview and admission envelope (record R11).

    Admission must supply the approved ``manifest_hash``; a mismatch or
    any ``unbounded_domains`` member blocks launch.
    """

    preview_id: Uuid7
    resolved_manifest: ResearchManifest
    warnings: tuple[ValidationIssue, ...] = ()
    estimated_evaluations: int = Field(ge=0)
    unbounded_domains: tuple[NonEmptyStr, ...] = ()
    manifest_hash: ContentHash
    schema_version: Literal[1] = 1


class ProjectGraphProjection(WireModel):
    """Wire-native project graph visualization projection (record R12).

    A version rejected by the authoritative server validator carries its
    issues and cannot be published through any transport.
    """

    projection_id: Uuid7
    project_version_id: Uuid7
    graph: ProjectGraph
    ordered_task_keys: tuple[NonEmptyStr, ...] = Field(min_length=1)
    validation: tuple[ValidationIssue, ...] = ()
    has_bounded_cycles: bool
    compared_version_id: Uuid7 | None = None
    added_task_keys: tuple[NonEmptyStr, ...] = ()
    removed_task_keys: tuple[NonEmptyStr, ...] = ()
    changed_task_keys: tuple[NonEmptyStr, ...] = ()
    schema_version: Literal[1] = 1


class PortfolioBuilderProjection(WireModel):
    """Wire-native portfolio builder projection (record R13).

    Every transport produces the same portfolio manifests and selected
    results for the same versioned input.
    """

    projection_id: Uuid7
    portfolio_version_id: Uuid7
    constituents: tuple[PortfolioMember, ...] = ()
    constraints: PortfolioConstraintSet | None = None
    correlation: CorrelationMatrix | None = None
    validation: tuple[ValidationIssue, ...] = ()
    latest_result: PortfolioResult | None = None
    schema_version: Literal[1] = 1


class ComponentStateSummary(WireModel):
    """Nested per-component state summary (record R14).

    Inline record part of ``CapabilityAdministrationProjection``; the
    feature-state literal is the Shared Contracts §4.3 core enum.
    """

    capability_key: CapabilityIdentifier
    feature_id: FeatureIdentifier
    feature_state: FeatureState
    generation: int = Field(ge=1)
    health: HealthState | None = None
    diagnostic: str = ""


class CapabilityAdministrationProjection(WireModel):
    """Wire-native capability administration projection (record R14).

    No secrets or credential values ever appear in the snapshot or its
    component summaries.
    """

    projection_id: Uuid7
    capability_snapshot: CapabilitySnapshot
    components: tuple[ComponentStateSummary, ...] = ()
    schema_version: Literal[1] = 1


class TradingActionPreview(WireModel):
    """Wire-native governed trading action preview (record R15).

    Commit must supply the matching ``preview_hash``; scope or preview
    drift requires reconfirmation and no adapter is called directly.
    """

    preview_id: Uuid7
    action: TradingActionKind
    normalized_plan: TradePlan
    risk_result: RiskDecision | None = None
    authority: ExecutionAuthorityRef
    environment: TradingModeValue
    affected_orders: tuple[Uuid7, ...] = ()
    affected_positions: tuple[Uuid7, ...] = ()
    idempotency_key: NonEmptyStr
    preview_hash: ContentHash
    schema_version: Literal[1] = 1


class TradingReadinessProjection(WireModel):
    """Wire-native trading readiness projection (record R16).

    Stale, unknown, or degraded state is explicit and machine-readable so
    consumers can block unsafe commands; cached state is never presented
    as authority.
    """

    projection_id: Uuid7
    session_ref: TradingSessionRef
    session_generation: int = Field(ge=1)
    session_state: TradingSessionStateValue
    environment: TradingModeValue
    authority: ExecutionAuthorityRef
    permissions: tuple[NonEmptyStr, ...] = ()
    account: BrokerAccountSnapshot | None = None
    market: BrokerMarketState | None = None
    open_orders: tuple[Uuid7, ...] = ()
    positions: tuple[Uuid7, ...] = ()
    protections: tuple[Uuid7, ...] = ()
    reconciliation_clean: bool
    freshness_observed_at: UtcTimestamp | None = None
    is_stale: bool
    critical_findings: tuple[NonEmptyStr, ...] = ()
    schema_version: Literal[1] = 1


class OperateResearchRequest(WireModel):
    """Operation-discriminated research preview gateway request.

    PREVIEW requires ``manifest``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["PREVIEW"]
    manifest: ResearchManifest | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> OperateResearchRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        _require_present((("manifest", self.manifest),))
        return self


class OperateResearchSuccess(WireModel):
    """Successful research preview gateway operation result."""

    outcome: Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: Literal[1] = 1
    preview: ResearchPreview | None = None
    schema_version: Literal[1] = 1


class EditProjectsRequest(WireModel):
    """Operation-discriminated project graph gateway request.

    PROJECT_GRAPH, VALIDATE, and COMPARE require ``project_version_id``;
    COMPARE additionally requires ``compared_version_id``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["PROJECT_GRAPH", "VALIDATE", "COMPARE"]
    project_version_id: Uuid7 | None = None
    compared_version_id: Uuid7 | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> EditProjectsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        _require_present((("project_version_id", self.project_version_id),))
        if self.operation == "COMPARE":
            _require_present((("compared_version_id", self.compared_version_id),))
        else:
            _require_absent((("compared_version_id", self.compared_version_id),))
        return self


class EditProjectsSuccess(WireModel):
    """Successful project graph gateway operation result."""

    outcome: Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: Literal[1] = 1
    projection: ProjectGraphProjection | None = None
    schema_version: Literal[1] = 1


class OperatePortfoliosRequest(WireModel):
    """Operation-discriminated portfolio operations gateway request.

    VIEW, VALIDATE, and COMPARE require ``portfolio_version_id``; COMPARE
    additionally requires ``compared_result_id``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["VIEW", "VALIDATE", "COMPARE"]
    portfolio_version_id: Uuid7 | None = None
    compared_result_id: Uuid7 | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> OperatePortfoliosRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        _require_present((("portfolio_version_id", self.portfolio_version_id),))
        if self.operation == "COMPARE":
            _require_present((("compared_result_id", self.compared_result_id),))
        else:
            _require_absent((("compared_result_id", self.compared_result_id),))
        return self


class OperatePortfoliosSuccess(WireModel):
    """Successful portfolio operations gateway operation result."""

    outcome: Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: Literal[1] = 1
    projection: PortfolioBuilderProjection | None = None
    issues: tuple[ValidationIssue, ...] = ()
    schema_version: Literal[1] = 1


class AdministerCapabilitiesRequest(WireModel):
    """Operation-discriminated capability administration gateway request."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["PROJECT"]
    capability_filter: tuple[CapabilityIdentifier, ...] = ()
    schema_version: Literal[1] = 1


class AdministerCapabilitiesSuccess(WireModel):
    """Successful capability administration gateway operation result."""

    outcome: Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: Literal[1] = 1
    projection: CapabilityAdministrationProjection | None = None
    schema_version: Literal[1] = 1


class OperateTradingRequest(WireModel):
    """Operation-discriminated trading operations gateway request.

    MANAGE_SESSION requires ``session`` and ``mode``; READINESS requires
    ``session_ref``; PREVIEW_ACTION requires ``session_ref`` and ``plan``;
    EMERGENCY requires ``reason``, ``scope``, and ``current_version``
    (authenticated role, impact, and separate attestation are required by
    the delegated Risk/Trading contracts); MARKET_DATA and
    OPERATOR_ANALYTICS carry no operation-specific fields.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal[
        "MANAGE_SESSION",
        "READINESS",
        "PREVIEW_ACTION",
        "EMERGENCY",
        "MARKET_DATA",
        "OPERATOR_ANALYTICS",
    ]
    session: TradingSession | None = None
    mode: TradingModeValue | None = None
    session_ref: TradingSessionRef | None = None
    plan: TradePlan | None = None
    reason: NonEmptyStr | None = None
    scope: NonEmptyStr | None = None
    current_version: int | None = Field(default=None, ge=1)
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> OperateTradingRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "MANAGE_SESSION":
                _require_present((("session", self.session), ("mode", self.mode)))
                _require_absent(
                    (
                        ("session_ref", self.session_ref),
                        ("plan", self.plan),
                        ("reason", self.reason),
                        ("scope", self.scope),
                        ("current_version", self.current_version),
                    )
                )
            case "READINESS":
                _require_present((("session_ref", self.session_ref),))
                _require_absent(
                    (
                        ("session", self.session),
                        ("mode", self.mode),
                        ("plan", self.plan),
                        ("reason", self.reason),
                        ("scope", self.scope),
                        ("current_version", self.current_version),
                    )
                )
            case "PREVIEW_ACTION":
                _require_present(
                    (("session_ref", self.session_ref), ("plan", self.plan))
                )
                _require_absent(
                    (
                        ("session", self.session),
                        ("mode", self.mode),
                        ("reason", self.reason),
                        ("scope", self.scope),
                        ("current_version", self.current_version),
                    )
                )
            case "EMERGENCY":
                _require_present(
                    (
                        ("reason", self.reason),
                        ("scope", self.scope),
                        ("current_version", self.current_version),
                    )
                )
                _require_absent(
                    (
                        ("session", self.session),
                        ("mode", self.mode),
                        ("session_ref", self.session_ref),
                        ("plan", self.plan),
                    )
                )
            case "MARKET_DATA" | "OPERATOR_ANALYTICS":
                _require_absent(
                    (
                        ("session", self.session),
                        ("mode", self.mode),
                        ("session_ref", self.session_ref),
                        ("plan", self.plan),
                        ("reason", self.reason),
                        ("scope", self.scope),
                        ("current_version", self.current_version),
                    )
                )
        return self


class OperateTradingSuccess(WireModel):
    """Successful trading operations gateway operation result.

    ``session`` is returned for MANAGE_SESSION, ``readiness`` for
    READINESS, ``preview`` for PREVIEW_ACTION, ``kill_switch`` for
    EMERGENCY, ``market`` for MARKET_DATA, and ``operational_journal``
    with ``qualification`` for OPERATOR_ANALYTICS.
    """

    outcome: Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: Literal[1] = 1
    session: TradingSession | None = None
    readiness: TradingReadinessProjection | None = None
    preview: TradingActionPreview | None = None
    kill_switch: KillSwitchState | None = None
    market: BrokerMarketState | None = None
    operational_journal: OperationalJournalArtifact | None = None
    qualification: OperatorQualification | None = None
    schema_version: Literal[1] = 1


class OperateTradingEventSubscription(WireModel):
    """Owner-required trading operations event stream subscription.

    The subscription is the delivery companion of
    ``interfaces.operate-trading@1``: ``resume_event_id`` reconnects after
    interruption with ordered replay/resync semantics and ``replay_limit``
    bounds buffered replay per FR-IFACE-STREAM_TRADING_EVENTS.
    """

    scope: TradingEventScope = "ALL"
    session_ref: Uuid7 | None = None
    resume_event_id: Uuid7 | None = None
    replay_limit: int = Field(default=0, ge=0, le=10000)
    schema_version: Literal[1] = 1


# Wire projections register under their inventory names (``<Record>`` ->
# ``<Record>Wire``); wire-native and request/success records register
# directly. Nested components (``AutomationCommandDescriptor``,
# ``ComponentStateSummary``) are inline record parts, not registered
# public records.
WIRE_MODELS: dict[str, type[WireModel]] = {
    "ApiVersion": ApiVersionWire,
    "ConcurrencyToken": ConcurrencyTokenWire,
    "EventCursor": EventCursorWire,
    "EventReplayBatch": EventReplayBatchWire,
    "AsyncJobRef": AsyncJobRefWire,
    "ArtifactDownloadRequest": ArtifactDownloadRequestWire,
    "BulkRequestToken": BulkRequestToken,
    "AutomationCommand": AutomationCommand,
    "AutomationSchema": AutomationSchema,
    "McpOperation": McpOperation,
    "ResearchPreview": ResearchPreview,
    "ProjectGraphProjection": ProjectGraphProjection,
    "PortfolioBuilderProjection": PortfolioBuilderProjection,
    "CapabilityAdministrationProjection": CapabilityAdministrationProjection,
    "TradingActionPreview": TradingActionPreview,
    "TradingReadinessProjection": TradingReadinessProjection,
    "OperateResearchRequest": OperateResearchRequest,
    "OperateResearchSuccess": OperateResearchSuccess,
    "EditProjectsRequest": EditProjectsRequest,
    "EditProjectsSuccess": EditProjectsSuccess,
    "OperatePortfoliosRequest": OperatePortfoliosRequest,
    "OperatePortfoliosSuccess": OperatePortfoliosSuccess,
    "AdministerCapabilitiesRequest": AdministerCapabilitiesRequest,
    "AdministerCapabilitiesSuccess": AdministerCapabilitiesSuccess,
    "OperateTradingRequest": OperateTradingRequest,
    "OperateTradingSuccess": OperateTradingSuccess,
    "OperateTradingEventSubscription": OperateTradingEventSubscription,
}
