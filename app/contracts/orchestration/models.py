"""Strict Pydantic v2 wire records for the ratified Orchestration v1 contracts."""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

from app.contracts.common.models import (
    CapabilityIdentifier,
    ContentHash,
    DecimalValue,
    JsonObject,
    JsonValue,
    UtcTimestamp,
    Uuid7,
    ValidationIssue,
    WireModel,
)

# Constrained local string alias reused across orchestration records.
type NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]


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


def _reachable(adjacency: dict[str, list[str]], start: str, target: str) -> bool:
    """Report whether ``target`` is reachable from ``start`` over transitions.

    Args:
        adjacency: Outgoing transition targets keyed by source task key.
        start: Task key where the directed search begins.
        target: Task key sought by the directed search.

    Returns:
        True when at least one directed path leads from ``start`` to
        ``target``, otherwise False.
    """
    pending = [start]
    seen = {start}
    while pending:
        current = pending.pop()
        for neighbour in adjacency.get(current, ()):
            if neighbour == target:
                return True
            if neighbour not in seen:
                seen.add(neighbour)
                pending.append(neighbour)
    return False


class ProjectExpression(WireModel):
    """One sandboxed deterministic project expression.

    Conditions run over declared task results, counters, and variables only;
    filesystem, network, clock, and undeclared access are impossible by
    construction in the owning runtime, not by this wire record.
    """

    expression_id: Uuid7
    expression: NonEmptyStr
    language_version: int = Field(ge=1)
    referenced_outputs: tuple[NonEmptyStr, ...] = ()
    schema_version: Literal[1] = 1


class PortSpec(WireModel):
    """One named typed task port at a declared schema version."""

    name: NonEmptyStr
    schema_version: int = Field(ge=1)


class TaskContract(WireModel):
    """Declared execution contract for one task type."""

    task_type: NonEmptyStr
    contract_version: int = Field(ge=1)
    input_ports: tuple[PortSpec, ...] = ()
    output_ports: tuple[PortSpec, ...] = ()
    required_capabilities: tuple[CapabilityIdentifier, ...] = ()
    supports_checkpoint: bool
    cancellation_behavior: Literal["COOPERATIVE", "IMMEDIATE", "NONE"]
    permissions: tuple[NonEmptyStr, ...] = ()
    resource_estimator: NonEmptyStr
    schema_version: Literal[1] = 1


class TaskDefinition(WireModel):
    """One task instance inside a project graph."""

    task_key: NonEmptyStr
    task_type: NonEmptyStr
    settings: JsonObject
    resource_refs: tuple[Uuid7, ...] = ()
    contract: TaskContract
    schema_version: Literal[1] = 1


class TransitionEdge(WireModel):
    """One transition between two task keys of a project graph."""

    from_task_key: NonEmptyStr
    to_task_key: NonEmptyStr
    condition: ProjectExpression | None = None
    kind: Literal["ORDERED", "BRANCH", "LOOP", "GOTO", "STOP_AND_START"] = "ORDERED"
    cycle_bound: JsonObject | None = None


class ProjectGraph(WireModel):
    """One immutable executable task graph.

    Domain assumptions: ``task_key`` values identify tasks uniquely inside
    one graph, every transition endpoint must reference a declared task key,
    and every transition lying on a directed cycle must carry an explicit
    ``cycle_bound`` so no reachable cycle is unbounded. ``GOTO`` and
    ``STOP_AND_START`` compile to explicit bounded transitions at runtime.
    """

    graph_id: Uuid7
    tasks: tuple[TaskDefinition, ...] = Field(min_length=1)
    transitions: tuple[TransitionEdge, ...] = ()
    content_hash: ContentHash
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_graph_structure(self) -> ProjectGraph:
        """Reject duplicate task keys, dangling edges, and unbounded cycles.

        The cycle check tests, per transition, whether its target can reach
        its source; that is exactly the condition for the transition lying
        on a directed cycle. The per-transition search is linear in graph
        size, which is acceptable for wire-sized graphs.

        Returns:
            The validated project graph.

        Raises:
            ValueError: Task keys are duplicated, a transition references an
                undeclared task key, or a cyclic transition omits
                ``cycle_bound``.
        """
        task_keys = tuple(task.task_key for task in self.tasks)
        if len(set(task_keys)) != len(task_keys):
            raise ValueError("task keys must be unique within a graph")
        known = set(task_keys)
        adjacency: dict[str, list[str]] = {}
        for transition in self.transitions:
            if transition.from_task_key not in known:
                raise ValueError(
                    "transition source must be a declared task key: "
                    + transition.from_task_key
                )
            if transition.to_task_key not in known:
                raise ValueError(
                    "transition target must be a declared task key: "
                    + transition.to_task_key
                )
            adjacency.setdefault(transition.from_task_key, []).append(
                transition.to_task_key
            )
        for transition in self.transitions:
            if transition.cycle_bound is None and _reachable(
                adjacency, transition.to_task_key, transition.from_task_key
            ):
                raise ValueError(
                    "cyclic transitions must declare cycle_bound: "
                    + transition.from_task_key
                    + " -> "
                    + transition.to_task_key
                )
        return self


class ProjectVariable(WireModel):
    """One typed, scoped, immutable variable assignment of a project run."""

    assignment_id: Uuid7
    project_run_id: Uuid7
    name: NonEmptyStr
    value_type: Literal[
        "BOOLEAN",
        "INTEGER",
        "DECIMAL",
        "STRING",
        "TIMEFRAME",
        "INSTRUMENT",
        "UUID",
    ]
    value: JsonValue
    sequence: int = Field(ge=1)
    source: Literal["PROJECT_INPUT", "PREDECESSOR_OUTPUT"]
    schema_version: Literal[1] = 1


class ProjectRef(WireModel):
    """Reference to one project identity."""

    project_id: Uuid7
    schema_version: Literal[1] = 1


class ProjectVersion(WireModel):
    """One immutable version of a project.

    Editing a project creates a new version and rejected versions cannot be
    published through any transport; both are runtime rules, while this wire
    record only carries the versioned content.
    """

    project_version_id: Uuid7
    project_id: Uuid7
    version: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=160)
    project_type: Literal["MANUAL_RESEARCH"] = "MANUAL_RESEARCH"
    graph: ProjectGraph
    inputs: tuple[ProjectVariable, ...] = ()
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class TaskState(WireModel):
    """One logical task-run state observation.

    Progress is monotonic within an attempt at runtime; the wire record
    bounds it to ``[0, 1]`` and leaves it absent for indeterminate phases.
    """

    task_run_id: Uuid7
    logical_state: Literal[
        "QUEUED",
        "RUNNING",
        "PAUSING",
        "PAUSED",
        "RESUMING",
        "STOPPING",
        "STOPPED",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
    ]
    logical_iteration: int = Field(ge=1)
    progress: DecimalValue | None = None
    entered_at: UtcTimestamp
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_progress_range(self) -> TaskState:
        """Reject determinate progress outside the closed interval [0, 1].

        Returns:
            The validated task state.

        Raises:
            ValueError: ``progress`` is present and outside [0, 1].
        """
        if self.progress is not None and not (
            Decimal(0) <= Decimal(self.progress) <= Decimal(1)
        ):
            raise ValueError("progress must be within [0, 1]")
        return self


class ProjectRunRef(WireModel):
    """Reference to one pinned project run.

    The run manifest pins project version, referenced object versions,
    effective settings, seeds, resource policy, and initiator, and is
    complete before the first task is queued at runtime.
    """

    project_run_id: Uuid7
    project_version_id: Uuid7
    run_number: int = Field(ge=1)
    run_manifest_id: Uuid7
    initiator: Uuid7
    state: Literal[
        "QUEUED",
        "RUNNING",
        "PAUSED",
        "STOPPING",
        "STOPPED",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
    ]
    schema_version: Literal[1] = 1


class TaskRunRef(WireModel):
    """Reference to one logical task run inside a project run."""

    task_run_id: Uuid7
    project_run_id: Uuid7
    task_key: NonEmptyStr
    logical_iteration: int = Field(ge=1)
    resolved_inputs: JsonObject = Field(default_factory=dict)
    state: TaskState | None = None
    schema_version: Literal[1] = 1


class TaskAttemptRef(WireModel):
    """One versioned execution attempt of a logical task run.

    Retry creates a new attempt on the same logical run while history,
    failure cause, and the selected recovery point remain visible.
    """

    attempt_id: Uuid7
    task_run_id: Uuid7
    attempt_no: int = Field(ge=1)
    retry_policy_version: int = Field(ge=1)
    failure_cause: NonEmptyStr | None = None
    recovery_point: JsonObject | None = None
    started_at: UtcTimestamp | None = None
    ended_at: UtcTimestamp | None = None
    schema_version: Literal[1] = 1


class TaskLease(WireModel):
    """One expiring worker lease over a task attempt.

    Workers heartbeat and lose commit authority after expiry or fencing
    token replacement at runtime.
    """

    lease_id: Uuid7
    task_run_id: Uuid7
    attempt_no: int = Field(ge=1)
    worker_id: Uuid7
    fencing_token: int = Field(ge=1)
    acquired_at: UtcTimestamp
    last_heartbeat_at: UtcTimestamp
    expires_at: UtcTimestamp
    state: Literal["ACTIVE", "RELEASED", "EXPIRED", "SUPERSEDED"]
    schema_version: Literal[1] = 1


class TaskCheckpoint(WireModel):
    """One immutable, content-addressed task checkpoint.

    A checkpoint is valid only for a compatible implementation plus
    manifest pair at runtime; corrupt checkpoints never resume.
    """

    checkpoint_id: Uuid7
    task_run_id: Uuid7
    attempt_no: int = Field(ge=1)
    sequence: int = Field(ge=1)
    implementation_hash: ContentHash
    manifest_hash: ContentHash
    state_artifact_id: Uuid7
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class TaskOutputCommit(WireModel):
    """One atomic output commit of a task attempt.

    Commits accept only the current fencing token before lease expiry at
    runtime, and fault injection never exposes partial output to a
    successor.
    """

    commit_id: Uuid7
    task_run_id: Uuid7
    attempt_no: int = Field(ge=1)
    fencing_token: int = Field(ge=1)
    output_artifact_ids: tuple[Uuid7, ...] = ()
    committed_at: UtcTimestamp
    schema_version: Literal[1] = 1


class DomainTaskRequest(WireModel):
    """One built-in domain task delegation request.

    ``pinned_selection_token_id`` is consumed by the mass-config, clear,
    load, and save task types; ``connector_sync_plan_id`` by UPDATE_DATA;
    ``databank_snapshot`` by LOG_DATABANK_STATS. Those task-type
    associations are runtime semantics and are not enforced per task type
    on this wire record.
    """

    request_id: Uuid7
    task_type: Literal[
        "BUILD",
        "RETEST",
        "OPTIMIZE",
        "FILTERING",
        "CUSTOM_ANALYSIS",
        "CREATE_PORTFOLIO",
        "AUTOMATIC_PORTFOLIO_BUILDER",
        "AUTOMATIC_RETEST",
        "APPLY_MASS_CONFIG",
        "CLEAR_DATABANKS",
        "LOAD_FROM_FILES",
        "SAVE_TO_FILES",
        "UPDATE_DATA",
        "LOG_DATABANK_STATS",
    ]
    delegated_capability: CapabilityIdentifier
    pinned_selection_token_id: Uuid7 | None = None
    connector_sync_plan_id: Uuid7 | None = None
    databank_snapshot: JsonObject | None = None
    input_refs: tuple[Uuid7, ...] = ()
    schema_version: Literal[1] = 1


class UtilityTaskRequest(WireModel):
    """One external or utility task request.

    ``allowlist_entry_id`` is consumed by CALL_EXTERNAL_SCRIPT,
    ``artifact_handle_id`` by DELETE_FILE, the wait fields by WAIT_FOR, the
    notification fields by NOTIFICATION, and ``training_plan_id`` by
    NEURAL_NETWORK_TRAINER. Those task-type associations are runtime
    semantics and are not enforced per task type on this wire record.
    """

    request_id: Uuid7
    task_type: Literal[
        "CALL_EXTERNAL_SCRIPT",
        "DELETE_FILE",
        "WAIT_FOR",
        "NOTIFICATION",
        "NEURAL_NETWORK_TRAINER",
    ]
    allowlist_entry_id: Uuid7 | None = None
    arguments: tuple[str, ...] = ()
    working_directory: str | None = None
    environment: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: int | None = Field(default=None, ge=1)
    input_artifact_ids: tuple[Uuid7, ...] = ()
    output_contract: JsonObject = Field(default_factory=dict)
    artifact_handle_id: Uuid7 | None = None
    wait_duration_seconds: int | None = Field(default=None, ge=1)
    wait_condition: ProjectExpression | None = None
    channel_id: Uuid7 | None = None
    template_id: Uuid7 | None = None
    training_plan_id: Uuid7 | None = None
    schema_version: Literal[1] = 1


class ExecutableAllowlistEntry(WireModel):
    """One principal-granted executable allowlist entry."""

    entry_id: Uuid7
    executable_path: NonEmptyStr
    allowed_arguments: tuple[str, ...] = ()
    allowed_working_directory: str | None = None
    allowed_environment: dict[str, str] = Field(default_factory=dict)
    max_timeout_seconds: int = Field(ge=1)
    granted_by: Uuid7
    schema_version: Literal[1] = 1


class NotificationChannelConfig(WireModel):
    """One strictly validated notification channel configuration.

    Delivery is disabled by default and requires the master switch plus the
    channel switch at runtime; rate limits are enforced before any external
    call. ``secret_ref_ids`` are Workspace-owned in-memory secret
    references, so the configuration stays opaque on the wire.
    """

    channel_id: Uuid7
    kind: Literal["DESKTOP", "SMTP_EMAIL", "TELEGRAM", "TWILIO_SMS"]
    is_enabled: bool = False
    master_switch_required: Literal[True] = True
    rate_limit: NonEmptyStr
    transport_policy: Literal["DISABLED", "STARTTLS", "TLS"] = "DISABLED"
    sender_ref: NonEmptyStr | None = None
    recipient_refs: tuple[NonEmptyStr, ...] = ()
    secret_ref_ids: tuple[Uuid7, ...] = ()
    segment_policy: JsonObject = Field(default_factory=dict)
    schema_version: Literal[1] = 1


class NotificationTemplate(WireModel):
    """One versioned notification message template."""

    template_id: Uuid7
    version: int = Field(ge=1)
    message_kind: Literal[
        "TRADING",
        "POSITION",
        "SYSTEM",
        "CONNECTION",
        "ERROR",
        "PERFORMANCE",
        "MARKET",
        "NEWS",
        "RISK",
        "CUSTOM",
        "TEST",
        "SESSION_LOCAL",
    ]
    body_template: NonEmptyStr
    content_kind: Literal["PLAIN_TEXT", "HTML"] = "PLAIN_TEXT"
    redaction_policy: NonEmptyStr
    schema_version: Literal[1] = 1


class NotificationSession(WireModel):
    """One thread-safe notification manager session."""

    session_id: Uuid7
    manager_instance: Literal["SHARED_SINGLETON"]
    channel_readiness: dict[Uuid7, Literal["READY", "DISABLED", "INVALID"]]
    opened_at: UtcTimestamp
    schema_version: Literal[1] = 1


class NotificationReceipt(WireModel):
    """One notification delivery receipt.

    The rendered template is redacted to ``rendered_hash`` only; the message
    payload is never embedded.
    """

    receipt_id: Uuid7
    delivery_id: NonEmptyStr
    channel_id: Uuid7
    status: Literal["DELIVERED", "FAILED", "SUPPRESSED_RATE_LIMIT", "DISABLED"]
    rendered_hash: ContentHash
    sent_at: UtcTimestamp | None = None
    error: NonEmptyStr | None = None
    schema_version: Literal[1] = 1


class ProjectProgress(WireModel):
    """Logical progress of one project run.

    Logical progress is distinguished from retry attempts by carrying the
    attempt count separately.
    """

    project_run_id: Uuid7
    phase: Literal["INDETERMINATE", "DETERMINATE"]
    completed_units: int = Field(default=0, ge=0)
    total_units: int | None = Field(default=None, ge=0)
    attempt_count: int = Field(ge=1)
    schema_version: Literal[1] = 1


class ProjectHistoryEntry(WireModel):
    """One retained history entry of a project run."""

    entry_id: Uuid7
    project_run_id: Uuid7
    sequence: int = Field(ge=1)
    kind: Literal[
        "STATE_TRANSITION",
        "COMMAND",
        "CHECKPOINT",
        "LOG",
        "RESOURCE_USAGE",
        "OUTPUT",
        "CAUSAL_LINK",
    ]
    recorded_at: UtcTimestamp
    detail: JsonObject
    schema_version: Literal[1] = 1


class NetworkTrainingPlan(WireModel):
    """One experimental neural network training plan (section 21.3)."""

    plan_id: Uuid7
    dataset_artifact_ids: tuple[Uuid7, ...]
    leakage_prevention: JsonObject
    preprocessing: JsonObject
    model_spec: JsonObject
    validation_spec: JsonObject
    seeds: tuple[NonEmptyStr, ...]
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class NetworkTrainingResult(WireModel):
    """One experimental neural network training result (section 21.3)."""

    result_id: Uuid7
    plan_id: Uuid7
    trained_model_artifact_id: Uuid7
    validation_metrics: JsonObject
    reproducibility_manifest: JsonObject
    inference_artifact_id: Uuid7 | None = None
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class DefineProjectsRequest(WireModel):
    """Operation-discriminated project definition request.

    CREATE and EDIT_GRAPH require only ``version`` (editing creates the
    successor version); VALIDATE requires exactly one of ``version`` or
    ``graph``; PUBLISH_VERSION requires ``project_id`` plus
    ``target_version``; COMPARE requires ``project_id`` plus
    ``baseline_version`` and ``target_version``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["CREATE", "EDIT_GRAPH", "VALIDATE", "PUBLISH_VERSION", "COMPARE"]
    version: ProjectVersion | None = None
    graph: ProjectGraph | None = None
    project_id: Uuid7 | None = None
    baseline_version: int | None = Field(default=None, ge=1)
    target_version: int | None = Field(default=None, ge=1)
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> DefineProjectsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing, forbidden fields are
                set, or VALIDATE carries neither or both of ``version`` and
                ``graph``.
        """
        match self.operation:
            case "CREATE" | "EDIT_GRAPH":
                _require_present((("version", self.version),))
                _require_absent(
                    (
                        ("graph", self.graph),
                        ("project_id", self.project_id),
                        ("baseline_version", self.baseline_version),
                        ("target_version", self.target_version),
                    )
                )
            case "VALIDATE":
                if (self.version is None) == (self.graph is None):
                    raise ValueError(
                        "VALIDATE requires exactly one of version or graph"
                    )
                _require_absent(
                    (
                        ("project_id", self.project_id),
                        ("baseline_version", self.baseline_version),
                        ("target_version", self.target_version),
                    )
                )
            case "PUBLISH_VERSION":
                _require_present(
                    (
                        ("project_id", self.project_id),
                        ("target_version", self.target_version),
                    )
                )
                _require_absent(
                    (
                        ("version", self.version),
                        ("graph", self.graph),
                        ("baseline_version", self.baseline_version),
                    )
                )
            case "COMPARE":
                _require_present(
                    (
                        ("project_id", self.project_id),
                        ("baseline_version", self.baseline_version),
                        ("target_version", self.target_version),
                    )
                )
                _require_absent(
                    (
                        ("version", self.version),
                        ("graph", self.graph),
                    )
                )
        return self


class DefineProjectsSuccess(WireModel):
    """Successful project definition operation result.

    The ratified envelope names the Interfaces-owned
    ``ProjectGraphProjection``; this shared contract carries the owning
    ``graph`` payload instead, as ratified for the shared envelope.
    """

    request_id: Uuid7
    version: ProjectVersion | None = None
    graph: ProjectGraph | None = None
    findings: tuple[ValidationIssue, ...] = ()
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class RunTasksRequest(WireModel):
    """Operation-discriminated project run and task command request.

    START_RUN requires only ``project_version_id``; PAUSE, RESUME, STOP,
    CANCEL, and RETRY require ``project_run_id`` with an optional
    ``task_run_id`` for task-scoped commands; REPORT_PROGRESS requires
    ``project_run_id`` plus a task state or run-level progress payload.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal[
        "START_RUN",
        "PAUSE",
        "RESUME",
        "STOP",
        "CANCEL",
        "RETRY",
        "REPORT_PROGRESS",
    ]
    project_version_id: Uuid7 | None = None
    project_run_id: Uuid7 | None = None
    task_run_id: Uuid7 | None = None
    state: TaskState | None = None
    progress: ProjectProgress | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> RunTasksRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing, forbidden fields are
                set, or REPORT_PROGRESS carries neither state nor progress.
        """
        match self.operation:
            case "START_RUN":
                _require_present((("project_version_id", self.project_version_id),))
                _require_absent(
                    (
                        ("project_run_id", self.project_run_id),
                        ("task_run_id", self.task_run_id),
                        ("state", self.state),
                        ("progress", self.progress),
                    )
                )
            case "PAUSE" | "RESUME" | "STOP" | "CANCEL" | "RETRY":
                _require_present((("project_run_id", self.project_run_id),))
                _require_absent(
                    (
                        ("project_version_id", self.project_version_id),
                        ("state", self.state),
                        ("progress", self.progress),
                    )
                )
            case "REPORT_PROGRESS":
                _require_present((("project_run_id", self.project_run_id),))
                _require_absent(
                    (
                        ("project_version_id", self.project_version_id),
                        ("task_run_id", self.task_run_id),
                    )
                )
                if self.state is None and self.progress is None:
                    raise ValueError("REPORT_PROGRESS requires state or progress")
        return self


class RunTasksSuccess(WireModel):
    """Successful project run and task command operation result."""

    request_id: Uuid7
    run: ProjectRunRef | None = None
    state: TaskState | None = None
    progress: ProjectProgress | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class EvaluateConditionsRequest(WireModel):
    """Operation-discriminated variable and condition request.

    RESOLVE_VARIABLES requires only ``project_run_id`` with an optional
    name filter; EVALUATE requires ``project_run_id`` and ``expression``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["RESOLVE_VARIABLES", "EVALUATE"]
    project_run_id: Uuid7 | None = None
    names: tuple[NonEmptyStr, ...] = ()
    expression: ProjectExpression | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> EvaluateConditionsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "RESOLVE_VARIABLES":
                _require_present((("project_run_id", self.project_run_id),))
                _require_absent((("expression", self.expression),))
            case "EVALUATE":
                _require_present(
                    (
                        ("project_run_id", self.project_run_id),
                        ("expression", self.expression),
                    )
                )
                if self.names:
                    raise ValueError("forbidden field is set: names")
        return self


class EvaluateConditionsSuccess(WireModel):
    """Successful variable and condition operation result."""

    request_id: Uuid7
    variables: tuple[ProjectVariable, ...] = ()
    result: JsonValue | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class RunDomainTasksRequest(WireModel):
    """Operation-discriminated built-in domain task request.

    DELEGATE executes the carried task request, PIN_SELECTION pins the
    selection scope it names, and DRY_RUN previews its impact; every
    operation requires ``request``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["DELEGATE", "PIN_SELECTION", "DRY_RUN"]
    request: DomainTaskRequest | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> RunDomainTasksRequest:
        """Require the domain task request for every operation.

        Returns:
            The validated request.

        Raises:
            ValueError: ``request`` is missing.
        """
        _require_present((("request", self.request),))
        return self


class RunDomainTasksSuccess(WireModel):
    """Successful built-in domain task operation result."""

    request_id: Uuid7
    request: DomainTaskRequest | None = None
    impact: JsonObject = Field(default_factory=dict)
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class RunUtilityTasksRequest(WireModel):
    """Operation-discriminated external and utility task request.

    CALL_EXECUTABLE, DELETE_FILE, WAIT_FOR, and NOTIFY require
    ``request``; MANAGE_ALLOWLIST requires ``allowlist_entry``;
    CONFIGURE_CHANNEL requires ``channel``; RENDER_TEMPLATE requires
    ``template`` with optional ``variables``; OPEN_SESSION carries no
    payload; CLOSE_SESSION requires ``session_id``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal[
        "CALL_EXECUTABLE",
        "DELETE_FILE",
        "WAIT_FOR",
        "NOTIFY",
        "MANAGE_ALLOWLIST",
        "CONFIGURE_CHANNEL",
        "RENDER_TEMPLATE",
        "OPEN_SESSION",
        "CLOSE_SESSION",
    ]
    request: UtilityTaskRequest | None = None
    allowlist_entry: ExecutableAllowlistEntry | None = None
    channel: NotificationChannelConfig | None = None
    template: NotificationTemplate | None = None
    variables: JsonObject | None = None
    session_id: Uuid7 | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> RunUtilityTasksRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        task_payloads = (
            ("allowlist_entry", self.allowlist_entry),
            ("channel", self.channel),
            ("template", self.template),
            ("variables", self.variables),
            ("session_id", self.session_id),
        )
        match self.operation:
            case "CALL_EXECUTABLE" | "DELETE_FILE" | "WAIT_FOR" | "NOTIFY":
                _require_present((("request", self.request),))
                _require_absent(task_payloads)
            case "MANAGE_ALLOWLIST":
                _require_present((("allowlist_entry", self.allowlist_entry),))
                _require_absent(
                    (
                        ("request", self.request),
                        ("channel", self.channel),
                        ("template", self.template),
                        ("variables", self.variables),
                        ("session_id", self.session_id),
                    )
                )
            case "CONFIGURE_CHANNEL":
                _require_present((("channel", self.channel),))
                _require_absent(
                    (
                        ("request", self.request),
                        ("allowlist_entry", self.allowlist_entry),
                        ("template", self.template),
                        ("variables", self.variables),
                        ("session_id", self.session_id),
                    )
                )
            case "RENDER_TEMPLATE":
                _require_present((("template", self.template),))
                _require_absent(
                    (
                        ("request", self.request),
                        ("allowlist_entry", self.allowlist_entry),
                        ("channel", self.channel),
                        ("session_id", self.session_id),
                    )
                )
            case "OPEN_SESSION":
                _require_absent(
                    (
                        ("request", self.request),
                        ("allowlist_entry", self.allowlist_entry),
                        ("channel", self.channel),
                        ("template", self.template),
                        ("variables", self.variables),
                        ("session_id", self.session_id),
                    )
                )
            case "CLOSE_SESSION":
                _require_present((("session_id", self.session_id),))
                _require_absent(
                    (
                        ("request", self.request),
                        ("allowlist_entry", self.allowlist_entry),
                        ("channel", self.channel),
                        ("template", self.template),
                        ("variables", self.variables),
                    )
                )
        return self


class RunUtilityTasksSuccess(WireModel):
    """Successful external and utility task operation result."""

    request_id: Uuid7
    request: UtilityTaskRequest | None = None
    allowlist_entry: ExecutableAllowlistEntry | None = None
    channel: NotificationChannelConfig | None = None
    session: NotificationSession | None = None
    receipt: NotificationReceipt | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class TrackRunHistoryRequest(WireModel):
    """Operation-discriminated run history request.

    RECORD requires only ``entry``; QUERY requires only
    ``project_run_id``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["RECORD", "QUERY"]
    entry: ProjectHistoryEntry | None = None
    project_run_id: Uuid7 | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> TrackRunHistoryRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "RECORD":
                _require_present((("entry", self.entry),))
                _require_absent((("project_run_id", self.project_run_id),))
            case "QUERY":
                _require_present((("project_run_id", self.project_run_id),))
                _require_absent((("entry", self.entry),))
        return self


class TrackRunHistorySuccess(WireModel):
    """Successful run history operation result."""

    request_id: Uuid7
    entries: tuple[ProjectHistoryEntry, ...] = ()
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class TrainNetworksRequest(WireModel):
    """Operation-discriminated neural network trainer request (Experimental).

    PLAN requires only ``plan``; TRAIN requires only ``plan_id``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["PLAN", "TRAIN"]
    plan: NetworkTrainingPlan | None = None
    plan_id: Uuid7 | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> TrainNetworksRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "PLAN":
                _require_present((("plan", self.plan),))
                _require_absent((("plan_id", self.plan_id),))
            case "TRAIN":
                _require_present((("plan_id", self.plan_id),))
                _require_absent((("plan", self.plan),))
        return self


class TrainNetworksSuccess(WireModel):
    """Successful neural network trainer operation result (Experimental)."""

    request_id: Uuid7
    plan: NetworkTrainingPlan | None = None
    result: NetworkTrainingResult | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


# TaskLogicalState-style PEP 695 aliases are inlined per record because no
# ratified orchestration record reuses another record's state value set.
# TransitionEdge and PortSpec are the nested records spelled inside the
# ratified public-record table and are registered alongside the 25 public
# records plus the seven request/success pairs.
WIRE_MODELS: dict[str, type[WireModel]] = {
    "ProjectRef": ProjectRef,
    "ProjectVersion": ProjectVersion,
    "ProjectGraph": ProjectGraph,
    "TaskDefinition": TaskDefinition,
    "TaskContract": TaskContract,
    "TaskState": TaskState,
    "ProjectRunRef": ProjectRunRef,
    "TaskRunRef": TaskRunRef,
    "TaskAttemptRef": TaskAttemptRef,
    "TaskLease": TaskLease,
    "TaskCheckpoint": TaskCheckpoint,
    "TaskOutputCommit": TaskOutputCommit,
    "ProjectVariable": ProjectVariable,
    "ProjectExpression": ProjectExpression,
    "DomainTaskRequest": DomainTaskRequest,
    "UtilityTaskRequest": UtilityTaskRequest,
    "ExecutableAllowlistEntry": ExecutableAllowlistEntry,
    "NotificationChannelConfig": NotificationChannelConfig,
    "NotificationTemplate": NotificationTemplate,
    "NotificationSession": NotificationSession,
    "NotificationReceipt": NotificationReceipt,
    "ProjectProgress": ProjectProgress,
    "ProjectHistoryEntry": ProjectHistoryEntry,
    "NetworkTrainingPlan": NetworkTrainingPlan,
    "NetworkTrainingResult": NetworkTrainingResult,
    "TransitionEdge": TransitionEdge,
    "PortSpec": PortSpec,
    "DefineProjectsRequest": DefineProjectsRequest,
    "DefineProjectsSuccess": DefineProjectsSuccess,
    "RunTasksRequest": RunTasksRequest,
    "RunTasksSuccess": RunTasksSuccess,
    "EvaluateConditionsRequest": EvaluateConditionsRequest,
    "EvaluateConditionsSuccess": EvaluateConditionsSuccess,
    "RunDomainTasksRequest": RunDomainTasksRequest,
    "RunDomainTasksSuccess": RunDomainTasksSuccess,
    "RunUtilityTasksRequest": RunUtilityTasksRequest,
    "RunUtilityTasksSuccess": RunUtilityTasksSuccess,
    "TrackRunHistoryRequest": TrackRunHistoryRequest,
    "TrackRunHistorySuccess": TrackRunHistorySuccess,
    "TrainNetworksRequest": TrainNetworksRequest,
    "TrainNetworksSuccess": TrainNetworksSuccess,
}
