"""Shared Typed Documents, Structural Metamodels, and Lifecycle Protocols.

Description:
    This module defines the authoritative typed contracts, data transfer models,
    and lifecycle protocols for the HaruQuantAI host runtime. It exists to guarantee
    strict schema immutability, prevent attribute mutation, validate syntactic
    plugin/workspace identities, declare algebraic port structures, and standardize
    wire communication payloads. Externally, these contracts are shared across all
    host boundaries: `bootstrap.py` uses `StageResult`, `BootSnapshot`, and
    `LifecycleHook` to track boot progress and execute provider hooks; `packages.py`
    and `discovery.py` consume `PluginDescriptor`, `ExtensionSlot`, and
    `CapabilityRequirement` to inspect manifests and bind plugin slots; and
    `transport.py` serializes snapshots for the `/api/v1/lifecycle` and
    `/api/v1/catalog` endpoints. Internally, `Document` establishes a frozen,
    extra-forbidden Pydantic base configuration; `StageResult` and
    `BootSnapshot` model monotonic progress; `PluginDescriptor` encapsulates
    namespaced contribution metadata; and `LifecycleHook` standardizes
    trusted asynchronous lifecycle callbacks.

Purpose:
    FEAT-HOST-CONTRACTS: Structural Metamodels, Ports, and Lifecycle Protocols.
    Provides immutable Pydantic schemas, algebraic node port declarations,
    descriptor metadata structures, and lifecycle hook callback protocols.

Key Capabilities:
    - FR-HOST-BROKER-TIME-PROVENANCE:
      Immutable raw broker documents; custody logs validate row correspondence.
    - FR-HOST-TRANSPORT-UNIFORM-ENVELOPE: Safe typed operation rejections;
      the transport boundary logs the validated code and request correlation.
    - FR-HOST-CLOCK-CONTRACT: Immutable clock schedules/provenance; operation
      boundaries log validation/admission and publication outcomes.
    - FR-HOST-CONTRACTS-IMMUTABLE-DOCUMENT: Schema-Enforced Frozen Document Base
      Associated: `Document`
      Logging: Enforces strict immutable attribute assignment and forbids
      unrecognized fields at model validation time.
    - FR-HOST-CONTRACTS-LIFECYCLE-TELEMETRY: Boot Progression Telemetry Models
      Associated: `StageResult`, `StageEvent`, `BootSnapshot`
      Logging: Structures wire payloads for lifecycle stage outcomes, monotonic
      durations, and event bus sequence counters.
    - FR-HOST-CONTRACTS-CONTRIBUTION-DESCRIPTOR: Package Descriptor Schema
      Associated: `PluginDescriptor`, `ExtensionSlot`,
      `CapabilityRequirement`, `Port`
      Logging: Validates syntactic identities, capability dependencies, and
      algebraic ports for dynamic catalog discovery.
    - FR-HOST-CONTRACTS-LIFECYCLE-HOOK: Trusted Asynchronous Lifecycle Callback
      Associated: `LifecycleHook`
      Logging: Structures hook timeouts, repeat intervals, execution callables,
      and reverse-order disposal handlers.

Python API Usage:
    ```python
    from app.host.contracts import BootSnapshot, LifecycleHook, StageResult

    # 1. Instantiate immutable lifecycle stage result
    result = StageResult(
        stage="runtime", label="Configure runtime", outcome="succeeded"
    )

    # 2. Build immutable boot snapshot
    snapshot = BootSnapshot(
        schema_version=2,
        state="SERVER_READY",
        sequence=42,
        stages=(result,),
    )

    # 3. Declare trusted provider lifecycle hook
    hook = LifecycleHook(
        id="provider.cache",
        stage="services",
        run=lambda: None,
        timeout=10.0,
    )
    ```

CLI Usage:
    Contract schemas and validation constraints are verified via host test
    suites:
    ```bash
    # Verify contract schemas and serialization rules
    uv run pytest tests/host/test_lifecycle.py

    # Verify static typing compliance across contracts
    uv run mypy app/host/contracts.py
    ```
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

CLOCK_MAX_MINUTES = 840
MAX_REJECTION_CODE = 64
MAX_REJECTION_MESSAGE = 500
REJECTION_CODE_CHARACTERS = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789"  # pragma: allowlist secret
)


class OperationRejectedError(ValueError):
    """Expected rejection with an explicitly safe, developer-authored message.

    Never construct this contract from an unrestricted exception string or input.
    Transport owns serialization; the rejecting component owns its reason code.
    """

    def __init__(self, code: str, public_message: str, *, status: int = 422) -> None:
        """Validate bounded public diagnostics without emitting log records."""
        if (
            not 1 <= len(code) <= MAX_REJECTION_CODE
            or not all(character in REJECTION_CODE_CHARACTERS for character in code)
            or not 1 <= len(public_message) <= MAX_REJECTION_MESSAGE
            or status not in {409, 422, 503}
        ):
            raise ValueError("Invalid operation rejection contract")
        self.code = code
        self.public_message = public_message
        self.status = status
        super().__init__(public_message)


Outcome = Literal[
    "pending", "running", "succeeded", "unavailable", "failed", "cancelled"
]
State = Literal[
    "OFFLINE",
    "INITIALIZING",
    "SERVER_READY",
    "DEGRADED",
    "FAILED",
    "STOPPED",
]


class Document(BaseModel):
    """Base model forbidding extra fields and top-level reassignment.

    Nested collection contents remain mutable; frozen does not provide deep
    immutability or thread synchronization.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")


class ClockTransition(Document):
    """Immutable UTC boundary supplied by an assessed source clock policy."""

    transition_utc: datetime
    offset_before_minutes: int = Field(strict=True, ge=-720, le=840)
    offset_after_minutes: int = Field(strict=True, ge=-720, le=840)

    @model_validator(mode="after")
    def utc_boundary(self) -> ClockTransition:
        """Reject local or naive boundaries; log validated policy boundaries."""
        if self.transition_utc.utcoffset() != UTC.utcoffset(None):
            raise ValueError("Clock transition must be explicit UTC")
        return self


class ClockPolicy(Document):
    """Immutable assessed clock schedule; host custody does not evaluate DST."""

    schema_version: Literal[1] = 1
    revision: int = Field(strict=True, gt=0)
    effective_from_utc: datetime
    effective_to_utc: datetime
    tick_time_basis: Literal["utc", "server_wall_clock", "unknown"] = "unknown"
    bar_time_basis: Literal["utc", "server_wall_clock", "unknown"] = "unknown"
    request_time_basis: Literal["utc", "server_wall_clock", "unknown"] = "unknown"
    standard_offset_minutes: int = Field(strict=True, ge=-720, le=840)
    dst_increment_minutes: int = Field(default=0, strict=True, ge=0, le=120)
    dst_rule: Literal["none", "us", "eu", "iana", "explicit_transitions"] = "none"
    iana_timezone: str = Field(default="", max_length=100)
    timezone_data_identity: str = Field(default="", max_length=100)
    initial_offset_minutes: int = Field(strict=True, ge=-720, le=840)
    transitions: tuple[ClockTransition, ...] = Field(default=(), max_length=1000)
    verified: bool = Field(default=False, strict=True)
    evidence_references: tuple[str, ...] = Field(default=(), max_length=50)
    assessed_at: datetime
    limitations: str = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def coherent_schedule(self) -> ClockPolicy:  # noqa: C901 -- schedule invariants are validated together.
        """Reject inconsistent schedules before persistence or publication."""
        dates = (self.effective_from_utc, self.effective_to_utc, self.assessed_at)
        if any(date.utcoffset() != UTC.utcoffset(None) for date in dates):
            raise ValueError("Policy dates must be explicit UTC")
        if self.effective_from_utc >= self.effective_to_utc:
            raise ValueError("Clock policy coverage is empty")
        if self.verified and not self.evidence_references:
            raise ValueError("Verified clock policy needs evidence")
        if any(not reference.strip() for reference in self.evidence_references):
            raise ValueError("Clock evidence references must be nonempty")
        if self.dst_rule == "iana" and not (
            self.iana_timezone and self.timezone_data_identity
        ):
            raise ValueError("IANA policy needs pinned timezone data identity")
        offsets = {
            self.standard_offset_minutes,
            self.standard_offset_minutes + self.dst_increment_minutes,
        }
        if (
            max(offsets) > CLOCK_MAX_MINUTES
            or self.initial_offset_minutes not in offsets
        ):
            raise ValueError("Initial clock offset conflicts with policy")
        previous = self.effective_from_utc
        offset = self.initial_offset_minutes
        for transition in self.transitions:
            if not previous < transition.transition_utc < self.effective_to_utc:
                raise ValueError("Clock transitions must be ordered within coverage")
            if transition.offset_before_minutes != offset:
                raise ValueError("Clock transition offsets are not contiguous")
            if transition.offset_after_minutes not in offsets:
                raise ValueError("Clock transition conflicts with policy offsets")
            previous = transition.transition_utc
            offset = transition.offset_after_minutes
        if self.dst_rule == "none" and (self.transitions or self.dst_increment_minutes):
            raise ValueError("Fixed clock policy cannot contain DST transitions")
        if self.dst_rule != "none" and not self.transitions:
            raise ValueError(
                "Seasonal clock policy needs a resolved transition schedule"
            )
        return self


class ClockProvenance(Document):
    """Pinned policy and row-aligned raw milliseconds for one partition revision."""

    schema_version: Literal[1] = 1
    policy: ClockPolicy
    input_basis: Literal["utc", "server_wall_clock"]
    converter_version: Literal["mt5.clock.v1"] = "mt5.clock.v1"
    raw_timestamps_ms: tuple[int, ...] = Field(max_length=500000)


class BrokerTimeProvenance(Document):
    """Uninterpreted original broker coordinates; no UTC policy is asserted."""

    schema_version: Literal[1] = 1
    timestamp_basis: Literal["broker_reported"] = "broker_reported"
    acquisition_convention: Literal["mt5.broker_time.v1"] = "mt5.broker_time.v1"
    dataset_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    raw_timestamps_ms: tuple[int, ...] = Field(max_length=500000)


class DatasetMetadata(Document):
    """Optional producer presentation; no concrete provider schema is imported."""

    dataset_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    bar_type: Literal["start", "end"] | None = None
    data_type: str = Field(max_length=80)
    type_source: Literal["calculation_mode", "folder", "unknown"]
    broker_utc_offset: int | None = Field(default=None, ge=-12, le=14)
    clock_status: Literal["estimated", "unknown", "expired"] = "unknown"
    checked_at: datetime | None = None


class DatasetMetadataDocument(Document):
    """Versioned optional acquisition response consumed by workspace projection."""

    schema_version: Literal[1] = 1
    datasets: tuple[DatasetMetadata, ...] = Field(max_length=10000)


class StageResult(Document):
    """Latest recorded outcome for one reference stage.

    stage is the stable host phase identifier; label is its display description.
    outcome starts
    pending; reason explains unavailable, failure, or milestone details. elapsed_ms
    is monotonic elapsed time measured by Startup, not wall-clock execution evidence
    for an unimplemented provider.
    """

    stage: str
    label: str
    outcome: Outcome = "pending"
    reason: str = ""
    elapsed_ms: float = 0


class StageEvent(StageResult):
    """Stage result extended with a replay sequence number.

    sequence orders events within the publishing host process; it is not a durable
    cross-restart identifier.
    """

    sequence: int


class BootSnapshot(Document):
    """Process readiness and ordered stage results for UI/CLI consumers.

    state describes the host, sequence is the current event-bus sequence, and stages
    contains the latest result for every reference ID. Server readiness does not
    imply client readiness or availability of research providers.
    """

    schema_version: Literal[2]
    state: State
    sequence: int
    stages: tuple[StageResult, ...]


class CapabilityRequirement(Document):
    """Namespaced capability declaration with an explicit compatibility version.

    id and version are validated syntactically. required distinguishes mandatory
    from optional dependencies; this document does not resolve implementations or
    prove semantic compatibility.
    """

    id: str = Field(pattern=r"^[a-z][a-z0-9_]*(?:[.][a-z][a-z0-9_]*)+$")
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    required: bool = True


class Port(Document):
    """Named typed input/output metadata for a composable contribution.

    name and type are nonempty bounded strings; units is optional presentation
    metadata. This declaration does not execute conversions or numerical checks.
    """

    name: str = Field(min_length=1, max_length=100)
    type: str = Field(min_length=1, max_length=100)
    units: str = ""


class ExtensionSlot(Document):
    """Typed versioned extension boundary owned by one workspace."""

    id: str = Field(pattern=r"^[a-z][a-z0-9_]*(?:[.][a-z][a-z0-9_]*)+$")
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    maximum: int = Field(default=4096, ge=1, le=4096)


class PluginDescriptor(Document):
    """Validated metadata owned by one plugin or workspace contribution.

    Carries stable identity/version, host compatibility, capability declarations,
    parameter schema, ports, and an optional route base. The catalog reads these
    fields without importing source. Schema contents and declared capabilities are
    metadata, not evidence of a mounted or executable provider.
    """

    id: str = Field(pattern=r"^[a-z][a-z0-9_]*(?:[.][a-z][a-z0-9_]*)+$")
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    compatibility: Literal["1"]
    kind: Literal["plugin", "workspace"] = "plugin"
    capabilities: tuple[CapabilityRequirement, ...] = ()
    requires: tuple[CapabilityRequirement, ...] = ()
    parameter_schema: dict[str, JsonValue] = Field(default_factory=dict)
    inputs: tuple[Port, ...] = ()
    outputs: tuple[Port, ...] = ()
    route_base: str | None = Field(default=None, pattern=r"^/api/v1/[a-z][a-z0-9_-]+$")
    owner_workspace_id: str | None = None
    slot_id: str | None = None
    contract_version: str | None = None
    slots: tuple[ExtensionSlot, ...] = ()


@dataclass(frozen=True)
class LifecycleHook:
    """Trusted callback bundle for an explicit universal lifecycle slot.

    Attributes:
        id: Stable unique provider ID validated by Startup.
        stage: Allowed provider stage to which run contributes.
        run: Async operation with dependencies already injected by its owner.
        required: Whether an initial failure aborts dependent boot work.
        timeout: Per-call execution and cleanup budget in seconds.
        interval: Optional repeat delay in seconds after initial success.
        close: Optional async cleanup for partially or fully acquired resources.

    Callbacks must cooperate with cancellation. The host retains opened hooks for
    reverse-order cleanup; descriptors never resolve or import these callables.
    """

    id: str
    stage: Literal["services", "packages"]
    run: Callable[[], Awaitable[None]]
    required: bool = False
    timeout: float = 30
    interval: float | None = None
    close: Callable[[], Awaitable[None]] | None = None
