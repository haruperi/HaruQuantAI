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
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue

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
