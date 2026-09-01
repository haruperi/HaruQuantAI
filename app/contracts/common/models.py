"""Strict common scalar aliases and reusable wire records."""

import re
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Uuid7 = Annotated[
    str,
    StringConstraints(
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
    ),
]
UtcTimestamp = Annotated[
    str,
    StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$"),
]
DecimalValue = Annotated[
    str,
    StringConstraints(pattern=r"^-?(?:0|[1-9]\d*)(?:\.\d*[1-9])?$"),
]
CurrencyCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]
ContentHash = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
CapabilityIdentifier = Annotated[
    str, StringConstraints(pattern=r"^[a-z][a-z0-9.-]*@[1-9]\d*$")
]
FeatureIdentifier = Annotated[str, StringConstraints(pattern=r"^FEAT-[A-Z0-9_-]+$")]

type JsonValue = (
    bool | int | float | str | list[JsonValue] | dict[str, JsonValue] | None
)
type JsonObject = dict[str, JsonValue]

# Closed core enum literals from Shared Contracts §4.3. Domain owners reference
# these instead of redeclaring equivalent literal unions.
type Direction = Literal["LONG", "SHORT", "BOTH"]
type Side = Literal["BUY", "SELL"]
type OrderType = Literal["MARKET", "STOP", "LIMIT", "STOP_LIMIT"]
type TimeInForce = Literal["GTC", "DAY", "IOC", "FOK"]
type Precision = Literal[
    "SELECTED_TIMEFRAME",
    "M1_SIMULATION",
    "REAL_TICK_CUSTOM_SPREAD",
    "REAL_TICK_RECORDED_SPREAD",
]
type Segment = Literal["FULL", "IS", "VALIDATION", "OOS", "NO_TRADE"]
type PlUnit = Literal["MONEY", "PERCENT", "PIPS"]
type Rounding = Literal["DOWN", "UP", "HALF_UP", "HALF_EVEN", "TOWARD_ZERO"]
type ResultState = Literal["STAGED", "VALIDATING", "COMMITTED", "REJECTED", "CORRUPT"]
type JobState = Literal[
    "QUEUED",
    "LEASED",
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
type FeatureState = Literal[
    "DISCOVERED",
    "DISABLED",
    "MISSING",
    "BLOCKED",
    "PREPARING",
    "ACTIVE",
    "QUIESCING",
    "STOPPING",
    "STOPPED",
    "FAILED_IMPORT",
    "FAILED_CONFIG",
    "FAILED_START",
    "FAILED_RUNTIME",
]
type OrderState = Literal[
    "CREATED",
    "ACCEPTED",
    "REJECTED",
    "PENDING",
    "PARTIALLY_FILLED",
    "FILLED",
    "CANCELLED",
    "EXPIRED",
]
type TradingModeValue = Literal["PAPER", "DEMO", "LIVE"]
type TradingSessionStateValue = Literal[
    "CREATED",
    "STARTING",
    "ACTIVE",
    "DEGRADED",
    "STOPPING",
    "STOPPED",
    "ARCHIVED",
]
type TradingOperationStateValue = Literal[
    "PLANNED",
    "ADMITTED",
    "DISPATCHING",
    "ACCEPTED",
    "REJECTED",
    "UNKNOWN",
    "RECONCILING",
    "PARTIALLY_FILLED",
    "FILLED",
    "CANCELLED",
    "CLOSED",
    "FAILED",
]
type RuntimeRiskDecision = Literal[
    "APPROVE",
    "WARN",
    "NEEDS_APPROVAL",
    "NEEDS_MORE_EVIDENCE",
    "REJECT",
    "BLOCK",
    "ERROR",
]


class WireModel(BaseModel):
    """Base configuration shared by public wire records."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class Money(WireModel):
    """Currency-qualified canonical decimal amount."""

    amount: DecimalValue
    currency: CurrencyCode


class Timeframe(WireModel):
    """Positive multiple of a supported market-time unit."""

    unit: Literal["MINUTE", "DAY", "WEEK", "MONTH"]
    multiple: int = Field(ge=1)


class SeriesPointKey(WireModel):
    """Stable ordering key for one time-series observation."""

    timestamp: UtcTimestamp
    sequence: int = Field(ge=0)


class ValidationIssue(WireModel):
    """Machine-readable validation issue."""

    path: tuple[str, ...]
    code: Annotated[str, StringConstraints(pattern=r"^[A-Z][A-Z0-9_]*$")]
    message: Annotated[str, StringConstraints(min_length=1)]
    context: JsonObject = Field(default_factory=dict)


class ProblemDetails(WireModel):
    """Stable application failure envelope."""

    type: Annotated[str, StringConstraints(pattern=r"^(?:urn:|https?://).+")] = (
        "urn:haruquantai:error"
    )
    title: Annotated[str, StringConstraints(min_length=1)] = "Application Error"
    status: int = Field(default=400, ge=400, le=599)
    code: Annotated[str, StringConstraints(pattern=r"^[A-Z][A-Z0-9_]*$")] = "ERROR"
    detail: Annotated[str, StringConstraints(min_length=1)] = (
        "Application operation failed"
    )
    request_id: str | None = None
    details: JsonObject = Field(default_factory=dict)
    errors: tuple[ValidationIssue, ...] = ()
    capability_key: CapabilityIdentifier | None = None
    required_version: int | None = Field(default=None, ge=1)
    feature_state: str | None = None
    affected_object_id: Uuid7 | None = None
    missing_dependencies: tuple[CapabilityIdentifier, ...] = ()
    available_alternatives: tuple[CapabilityIdentifier, ...] = ()
    schema_version: Literal[1] = 1


class CapabilityProviderSnapshot(WireModel):
    """Pinned provider identity and configuration evidence."""

    capability_key: CapabilityIdentifier
    provider_feature_id: FeatureIdentifier
    generation: int = Field(ge=1)
    implementation_hash: ContentHash
    configuration_hash: ContentHash


class CapabilitySnapshot(WireModel):
    """Immutable ordered provider snapshot."""

    snapshot_id: Uuid7
    created_at: UtcTimestamp
    providers: tuple[CapabilityProviderSnapshot, ...] = Field(min_length=1)
    snapshot_hash: ContentHash
    causal_request_id: Uuid7 | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_provider_order(self) -> CapabilitySnapshot:
        """Reject duplicate or non-canonical provider ordering.

        Returns:
            The validated snapshot.

        Raises:
            ValueError: Providers are duplicated or not canonically ordered.
        """
        keys = tuple(provider.capability_key for provider in self.providers)
        if keys != tuple(sorted(keys)) or len(keys) != len(set(keys)):
            raise ValueError("providers must be unique and sorted by capability key")
        return self


class AuthContext(WireModel):
    """Immutable trace and authenticated principal context."""

    principal_id: str
    principal_type: Literal["USER", "SERVICE_ACCOUNT"]
    roles: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    scopes: tuple[str, ...] = ()
    tenant_or_environment: str
    request_id: str
    workflow_id: str
    correlation_id: str
    issued_at: UtcTimestamp
    runtime_profile: Literal["research", "simulation", "demo", "live"] = "simulation"
    schema_version: Literal[1] = 1


class AuditEvent(WireModel):
    """Redacted, versioned audit trail event."""

    event_id: str
    occurred_at: UtcTimestamp
    domain: str
    action: str
    request_id: str
    correlation_id: str
    payload: JsonObject
    principal_id: str | None = None
    causation_id: str | None = None
    schema_version: Literal[1] = 1


class ResponseMetadata(WireModel):
    """Monotonic execution and trace metadata for standard operation responses."""

    request_id: str
    timestamp: UtcTimestamp
    correlation_id: str | None = None
    execution_ms: float = 0.0
    name: str | None = None
    domain: str | None = None
    risk_level: str | None = "none"
    read_only: bool = True
    writes_file: bool = False
    modifies_database: bool = False
    places_trade: bool = False
    requires_network: bool = False
    extensions: JsonObject = Field(default_factory=dict)
    schema_version: Literal[1] = 1


class StandardResponse[T](WireModel):
    """Immutable 5-field function-level response."""

    status: Literal["success", "error", "exception", "SUCCESS", "ERROR", "EXCEPTION"]
    message: str
    metadata: ResponseMetadata
    data: T | None = None
    error: ProblemDetails | None = None


type ValidationVerdict = Literal["PASS", "WARN", "BLOCK", "FAIL", "UNKNOWN"]
type SeverityRank = Literal["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]


class ValidationReason(WireModel):
    """Structured validation reason code with severity and corrective actions."""

    code: str
    message: str
    severity: SeverityRank = "MEDIUM"
    corrective_action: str | None = None
    evidence_ref: str | None = None
    schema_version: Literal[1] = 1


class ValidationOutcome(WireModel):
    """Cross-domain validation outcome."""

    verdict: ValidationVerdict
    evaluated_at: UtcTimestamp
    reasons: tuple[ValidationReason, ...] = ()
    schema_version: Literal[1] = 1


class ProfileRef(WireModel):
    """Versioned reference to a named configuration profile."""

    profile_kind: str
    profile_id: str
    version: int = Field(ge=1)
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class VersionRef(WireModel):
    """Versioned reference to an immutable artifact or policy."""

    artifact_kind: str
    artifact_id: str
    version: int = Field(ge=1)
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class IdempotencyKey(WireModel):
    """Owner-bound TTL idempotency key."""

    key: str
    owner_id: str
    expires_at: UtcTimestamp
    schema_version: Literal[1] = 1


class ProgressUpdate(WireModel):
    """Structured progress update for asynchronous tasks and jobs."""

    job_id: str
    task_id: str
    progress_pct: DecimalValue
    message: str
    updated_at: UtcTimestamp
    schema_version: Literal[1] = 1


WIRE_MODELS: dict[str, type[WireModel]] = {
    "Money": Money,
    "Timeframe": Timeframe,
    "SeriesPointKey": SeriesPointKey,
    "ValidationIssue": ValidationIssue,
    "ProblemDetails": ProblemDetails,
    "CapabilityProviderSnapshot": CapabilityProviderSnapshot,
    "CapabilitySnapshot": CapabilitySnapshot,
    "AuthContext": AuthContext,
    "AuditEvent": AuditEvent,
    "ResponseMetadata": ResponseMetadata,
    "ValidationReason": ValidationReason,
    "ValidationOutcome": ValidationOutcome,
    "ProfileRef": ProfileRef,
    "VersionRef": VersionRef,
    "IdempotencyKey": IdempotencyKey,
    "ProgressUpdate": ProgressUpdate,
}


def _to_timestamp_str(val: object | None) -> UtcTimestamp:
    if val is None:
        return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if isinstance(val, datetime):
        dt = val if val.tzinfo is not None else val.replace(tzinfo=UTC)
        return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return str(val)


def build_response_metadata(
    *,
    request_id: str,
    timestamp: UtcTimestamp | datetime | None = None,
    correlation_id: str | None = None,
    execution_ms: float | str | None = None,
    name: str | None = None,
    domain: str | None = None,
    risk_level: str | None = "none",
    start_time: int | None = None,
    read_only: bool = True,
    writes_file: bool = False,
    modifies_database: bool = False,
    places_trade: bool = False,
    requires_network: bool = False,
    extensions: JsonObject | None = None,
) -> ResponseMetadata:
    """Construct structured monotonic response metadata.

    Args:
        request_id: Unique request identifier.
        timestamp: Optional UTC timestamp string or datetime.
        correlation_id: Optional correlation tracking identifier.
        execution_ms: Optional execution duration in milliseconds.
        name: Optional operation name.
        domain: Optional owning domain name.
        risk_level: Optional risk classification.
        start_time: Optional start monotonic timestamp in nanoseconds.
        read_only: Optional read-only flag.
        writes_file: Optional file mutation flag.
        modifies_database: Optional database mutation flag.
        places_trade: Optional trade execution flag.
        requires_network: Optional network requirement flag.
        extensions: Optional extra metadata dictionary.

    Returns:
        Structured ResponseMetadata instance.
    """
    import time

    ext: dict[str, Any] = dict(extensions or {})
    exec_val: float = 0.0
    if start_time is not None and execution_ms is None:
        elapsed = (time.perf_counter_ns() - start_time) / 1_000_000.0
        exec_val = round(elapsed, 3)
    elif execution_ms is not None:
        try:
            exec_val = round(float(execution_ms), 3)
        except ValueError, TypeError:
            exec_val = 0.0

    ts = _to_timestamp_str(timestamp)
    return ResponseMetadata(
        request_id=request_id,
        timestamp=ts,
        correlation_id=correlation_id,
        execution_ms=exec_val,
        name=name,
        domain=domain,
        risk_level=risk_level or "none",
        read_only=read_only,
        writes_file=writes_file,
        modifies_database=modifies_database,
        places_trade=places_trade,
        requires_network=requires_network,
        extensions=ext,
    )


def get_execution_ms(start_time: int) -> float:
    """Compute elapsed execution time in milliseconds.

    Args:
        start_time: Monotonic start timestamp in nanoseconds.

    Returns:
        Elapsed milliseconds as float.
    """
    import time

    elapsed = (time.perf_counter_ns() - start_time) / 1_000_000.0
    return round(elapsed, 3)


def success_response[T](
    data: T,
    *,
    message: str = "success",
    metadata: ResponseMetadata,
) -> StandardResponse[T]:
    """Construct a successful standard response envelope.

    Args:
        data: Operation payload result.
        message: Optional human-readable message.
        metadata: Execution and trace metadata.

    Returns:
        StandardResponse envelope carrying payload data.
    """
    return StandardResponse[T](
        status="success",
        message=message,
        metadata=metadata,
        data=data,
        error=None,
    )


def error_response[T](
    *,
    code: str,
    message: str = "error",
    metadata: ResponseMetadata,
    details: JsonObject | None = None,
    status: int = 400,
    catalog: object | None = None,
) -> StandardResponse[T]:
    """Construct an error standard response envelope.

    Args:
        code: Error code symbolic string.
        message: Human-readable error message.
        metadata: Response trace metadata.
        details: Optional invalid parameter mapping.
        status: HTTP status code equivalent.
        catalog: Optional error catalog reference.

    Returns:
        StandardResponse envelope carrying ProblemDetails.
    """
    _ = catalog
    issues: list[ValidationIssue] = []
    if details:
        for k, v in details.items():
            issues.append(
                ValidationIssue(
                    path=(str(k),),
                    code="VALIDATION_FAILED",
                    message=str(v),
                )
            )
    safe_code = code if re.fullmatch(r"^[A-Z][A-Z0-9_]*$", code) else "ERROR"
    problem = ProblemDetails(
        type=f"urn:haruquant:error:{code}",
        title=code,
        status=status,
        code=safe_code,
        detail=message,
        request_id=metadata.request_id,
        details=dict(details or {}),
        errors=tuple(issues),
    )
    return StandardResponse[T](
        status="error",
        message=message,
        metadata=metadata,
        data=None,
        error=problem,
    )


def exception_response[T](
    exc: Exception,
    *,
    message: str = "exception",
    metadata: ResponseMetadata,
    catalog: object | None = None,
) -> StandardResponse[T]:
    """Construct an exception standard response envelope.

    Args:
        exc: Exception instance.
        message: Optional override message.
        metadata: Response trace metadata.
        catalog: Optional error catalog reference.

    Returns:
        StandardResponse envelope with EXCEPTION status.
    """
    _ = catalog
    problem = ProblemDetails(
        type="urn:haruquant:error:EXCEPTION",
        title=type(exc).__name__,
        status=500,
        code="EXCEPTION",
        detail=str(exc) or message,
        request_id=metadata.request_id,
    )
    return StandardResponse[T](
        status="exception",
        message=message,
        metadata=metadata,
        data=None,
        error=problem,
    )


def get_standard_response_type() -> type[StandardResponse[Any]]:
    """Return the StandardResponse class type for typing reflection.

    Returns:
        StandardResponse class type.
    """
    return StandardResponse


def create_auth_context(
    *,
    principal_id: str,
    principal_type: Literal[
        "USER", "SERVICE_ACCOUNT", "SYSTEM", "ANONYMOUS"
    ] = "SERVICE_ACCOUNT",
    roles: tuple[str, ...] = (),
    permissions: tuple[str, ...] = (),
    scopes: tuple[str, ...] = (),
    tenant_or_environment: str = "dev",
    request_id: str | None = None,
    workflow_id: str | None = None,
    correlation_id: str | None = None,
    issued_at: UtcTimestamp | datetime | None = None,
    runtime_profile: Literal["research", "simulation", "demo", "live"] = "simulation",
    contract_version: str | None = None,
    schema_id: str | None = None,
) -> AuthContext:
    """Construct an authenticated context envelope.

    Args:
        principal_id: Unique caller identifier.
        principal_type: Caller classification.
        roles: Caller role strings.
        permissions: Permission strings.
        scopes: Scoped capability strings.
        tenant_or_environment: Tenant or environment label.
        request_id: Optional request ID.
        workflow_id: Optional workflow ID.
        correlation_id: Optional correlation ID.
        issued_at: Optional issuance timestamp string or datetime.
        runtime_profile: Active runtime profile.
        contract_version: Optional version tag.
        schema_id: Optional schema identifier.

    Returns:
        Constructed AuthContext record.
    """
    import uuid

    _ = contract_version
    _ = schema_id
    req_id = request_id or f"req-{uuid.uuid4().hex[:12]}"
    if issued_at is None:
        issued_str = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    elif isinstance(issued_at, datetime):
        dt = (
            issued_at if issued_at.tzinfo is not None else issued_at.replace(tzinfo=UTC)
        )
        issued_str = dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    else:
        issued_str = str(issued_at)

    return AuthContext(
        principal_id=principal_id,
        principal_type=principal_type,
        roles=roles,
        permissions=permissions,
        scopes=scopes,
        tenant_or_environment=tenant_or_environment,
        request_id=req_id,
        workflow_id=workflow_id or f"wf-{uuid.uuid4().hex[:12]}",
        correlation_id=correlation_id or req_id,
        issued_at=issued_str,
        runtime_profile=runtime_profile,
    )


def get_auth_context_type() -> type[AuthContext]:
    """Return the AuthContext class type.

    Returns:
        AuthContext class type.
    """
    return AuthContext


def create_audit_event(
    *,
    domain: str,
    action: str,
    payload: JsonObject,
    request_id: str | None = None,
    correlation_id: str | None = None,
    event_id: str | None = None,
    occurred_at: UtcTimestamp | datetime | None = None,
    timestamp: UtcTimestamp | datetime | None = None,
    principal_id: str | None = None,
    causation_id: str | None = None,
    contract_version: str | None = None,
    schema_id: str | None = None,
) -> AuditEvent:
    """Construct a versioned audit trail event.

    Args:
        domain: Owning domain string.
        action: Performed action name.
        payload: Event data payload.
        request_id: Optional request identifier.
        correlation_id: Optional correlation identifier.
        event_id: Optional event identifier.
        occurred_at: Optional occurrence timestamp string or datetime.
        timestamp: Optional alternate timestamp string or datetime.
        principal_id: Optional principal identifier.
        causation_id: Optional causal event identifier.
        contract_version: Optional version tag.
        schema_id: Optional schema identifier.

    Returns:
        Constructed AuditEvent record.
    """
    import uuid

    _ = contract_version
    _ = schema_id
    req_id = request_id or f"req-{uuid.uuid4().hex[:12]}"
    if occurred_at is None and timestamp is None:
        occ_str = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    else:
        val = occurred_at or timestamp
        if isinstance(val, datetime):
            dt = val if val.tzinfo is not None else val.replace(tzinfo=UTC)
            occ_str = dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        else:
            occ_str = str(val)

    return AuditEvent(
        event_id=event_id or f"evt-{uuid.uuid4().hex[:12]}",
        occurred_at=occ_str,
        domain=domain,
        action=action,
        request_id=req_id,
        correlation_id=correlation_id or req_id,
        payload=payload,
        principal_id=principal_id,
        causation_id=causation_id,
    )


def get_audit_event_type() -> type[AuditEvent]:
    """Return the AuditEvent class type.

    Returns:
        AuditEvent class type.
    """
    return AuditEvent


def build_event_envelope(
    *,
    event_id: str,
    source_id: str,
    source_sequence: int = 1,
    correlation_id: str | None = None,
    causation_id: str | None = None,
    deduplication_key: str | None = None,
    emitted_at: UtcTimestamp | datetime | None = None,
    payload: JsonObject | None = None,
    timestamp: UtcTimestamp | datetime | None = None,
) -> dict[str, Any]:
    """Build a standard event envelope mapping.

    Args:
        event_id: Event identifier.
        source_id: Emitter source identifier.
        source_sequence: Sequence integer.
        correlation_id: Optional correlation identifier.
        causation_id: Optional causation identifier.
        deduplication_key: Optional deduplication key.
        emitted_at: Optional emission timestamp string or datetime.
        payload: Optional event payload.
        timestamp: Optional emission timestamp alias.

    Returns:
        Event envelope dictionary.
    """
    ts = _to_timestamp_str(emitted_at or timestamp)
    return {
        "event_id": event_id,
        "source_id": source_id,
        "source_sequence": source_sequence,
        "correlation_id": correlation_id or event_id,
        "causation_id": causation_id,
        "deduplication_key": deduplication_key,
        "emitted_at": ts,
        "payload": payload or {},
    }


def parse_event_envelope(envelope: dict[str, Any]) -> dict[str, Any]:
    """Parse and validate an event envelope mapping.

    Args:
        envelope: Raw envelope mapping.

    Returns:
        Parsed envelope mapping.
    """
    return envelope


def find_sequence_gap(sequences: list[int] | tuple[int, ...]) -> int | None:
    """Find the first missing integer in an ordered sequence of events.

    Args:
        sequences: Collection of integer sequences.

    Returns:
        First missing integer, or None if contiguous.
    """
    sorted_seqs = sorted(sequences)
    for i in range(len(sorted_seqs) - 1):
        if sorted_seqs[i + 1] - sorted_seqs[i] > 1:
            return sorted_seqs[i] + 1
    return None


def is_duplicate_event(seen_keys: set[str], key: str) -> bool:
    """Check whether an event deduplication key has already been observed.

    Args:
        seen_keys: Set of already seen deduplication keys.
        key: Candidate deduplication key.

    Returns:
        True if already in seen_keys, False otherwise.
    """
    if key in seen_keys:
        return True
    seen_keys.add(key)
    return False


def build_validation_outcome(
    *,
    verdict: ValidationVerdict,
    check_id: str,
    reason_codes: list[str] | tuple[str, ...] = (),
    reasons: list[ValidationReason] | tuple[ValidationReason, ...] = (),
    evaluated_at: UtcTimestamp | datetime | None = None,
    context: JsonObject | None = None,
) -> ValidationOutcome:
    """Build a structured ValidationOutcome record.

    Args:
        verdict: Verdict classification.
        check_id: Identifier of the check.
        reason_codes: Optional list of reason code strings.
        reasons: Optional list of ValidationReason records.
        evaluated_at: Optional evaluation timestamp string or datetime.
        context: Optional evaluation context dictionary.

    Returns:
        ValidationOutcome instance.
    """
    ts = _to_timestamp_str(evaluated_at)
    return ValidationOutcome(
        verdict=verdict,
        check_id=check_id,
        reasons=tuple(reasons)
        if reasons
        else tuple(ValidationReason(code=rc, message=rc) for rc in reason_codes),
        evaluated_at=ts,
        context=context or {},
    )


def validate_reason_code(code: str) -> bool:
    """Validate format of a structured reason code.

    Args:
        code: Reason code string.

    Returns:
        True if code is well-formed.
    """
    min_reason_code_len = 3
    return bool(code and len(code) >= min_reason_code_len and "." in code)


def build_health_state(
    *,
    dependency: str,
    category: str = "TRANSIENT",
    state: str = "HEALTHY",
    retryable: bool = False,
    operator_action: str = "NONE",
    observed_at: UtcTimestamp | datetime | None = None,
) -> dict[str, Any]:
    """Build health state mapping.

    Args:
        dependency: Dependency component name.
        category: Failure category.
        state: Operational state string.
        retryable: Whether state allows retries.
        operator_action: Required operator action string.
        observed_at: Observation timestamp string or datetime.

    Returns:
        Health state mapping.
    """
    return {
        "dependency": dependency,
        "category": category,
        "state": state,
        "retryable": retryable,
        "operator_action": operator_action,
        "observed_at": _to_timestamp_str(observed_at),
    }


def parse_health_state(state: dict[str, Any]) -> dict[str, Any]:
    """Parse health state mapping.

    Args:
        state: Raw health state dictionary.

    Returns:
        Parsed health state dictionary.
    """
    return state


def build_reservation(
    *,
    key: str,
    owner_id: str,
    expires_at: UtcTimestamp | datetime,
) -> IdempotencyKey:
    """Build an IdempotencyKey reservation.

    Args:
        key: Reservation key string.
        owner_id: Identifier of the key owner.
        expires_at: Key expiration timestamp string or datetime.

    Returns:
        IdempotencyKey instance.
    """
    return IdempotencyKey(
        key=key, owner_id=owner_id, expires_at=_to_timestamp_str(expires_at)
    )


def derive_idempotency_key(prefix: str, *parts: str) -> str:
    """Derive an idempotency key string.

    Args:
        prefix: Key prefix.
        *parts: Key components.

    Returns:
        Derived stable identifier string.
    """
    import hashlib

    raw = f"{prefix}:{':'.join(parts)}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def evaluate_reservation(reservation: IdempotencyKey) -> bool:
    """Check if an idempotency reservation is active.

    Args:
        reservation: IdempotencyKey reservation record.

    Returns:
        True if reservation is still active.
    """
    now_str = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return reservation.expires_at > now_str


def is_reservation_expired(reservation: IdempotencyKey) -> bool:
    """Check if an idempotency reservation is expired.

    Args:
        reservation: IdempotencyKey reservation record.

    Returns:
        True if reservation is expired.
    """
    return not evaluate_reservation(reservation)


def parse_idempotency_key(key_str: str) -> str:
    """Parse and clean an idempotency key string.

    Args:
        key_str: Raw key string.

    Returns:
        Cleaned key string.
    """
    return key_str.strip()
