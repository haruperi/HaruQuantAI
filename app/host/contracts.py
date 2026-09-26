"""Shared typed documents for host lifecycle and contribution metadata.

Pydantic documents reject unknown fields and prevent attribute reassignment.
Nested mappings are not recursively frozen; producers must avoid mutating
published data. These contracts describe host transport and capability slots,
not centralized plugin-specific algorithms or schemas. LifecycleHook supplies
explicit trusted callbacks; descriptors alone never load executable providers.
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
    "RESTORING",
    "STANDBY",
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

    stage is the B/I/A identifier and label is its display description. outcome starts
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
    stage: str
    run: Callable[[], Awaitable[None]]
    required: bool = False
    timeout: float = 30
    interval: float | None = None
    close: Callable[[], Awaitable[None]] | None = None
