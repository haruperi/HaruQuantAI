"""Feature specifications, lifecycle states, and interface protocols."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.kernel.capability import CapabilityKey
    from app.kernel.context import FeatureContext
    from app.kernel.state import StateDeclaration


class FeatureState(StrEnum):
    """Lifecycle states of a composable feature package."""

    DISCOVERED = "DISCOVERED"
    DISABLED = "DISABLED"
    MISSING = "MISSING"
    BLOCKED = "BLOCKED"
    PREPARING = "PREPARING"
    ACTIVE = "ACTIVE"
    QUIESCING = "QUIESCING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED_IMPORT = "FAILED_IMPORT"
    FAILED_CONFIG = "FAILED_CONFIG"
    FAILED_START = "FAILED_START"
    FAILED_RUNTIME = "FAILED_RUNTIME"


@dataclass(frozen=True, slots=True)
class FeatureSpec:
    """Static capability declaration and metadata for a feature package."""

    feature_id: str
    domain: str
    provides: frozenset[CapabilityKey[Any]]
    requires: frozenset[CapabilityKey[Any]] = field(default_factory=frozenset)
    optional: frozenset[CapabilityKey[Any]] = field(default_factory=frozenset)
    conflicts: frozenset[str] = field(default_factory=frozenset)
    description: str = ""
    state: StateDeclaration | None = None

    def validate(self) -> None:
        """Validate specification consistency and structural integrity."""
        if not self.feature_id.strip():
            raise ValueError("Feature ID must not be empty.")
        if not self.domain.strip():
            raise ValueError("Domain must not be empty.")
        overlap = self.provides.intersection(self.requires)
        if overlap:
            overlap_ids = ", ".join(capability.identifier for capability in overlap)
            raise ValueError(
                f"Feature cannot both provide and require capability: {overlap_ids}"
            )


@runtime_checkable
class Feature(Protocol):
    """Protocol satisfied by all composable feature implementations."""

    spec: FeatureSpec

    async def mount(
        self,
        context: FeatureContext,
        config: object,
    ) -> None:
        """Mount the feature into a reversible lifecycle context."""
        ...


@runtime_checkable
class HealthCheckableFeature(Protocol):
    """Optional pre-commit health-check protocol for replacement."""

    async def health_check(self) -> None:
        """Raise when the staged feature is not healthy enough to commit."""
        ...


@runtime_checkable
class QuiesceableFeature(Protocol):
    """Optional protocol for stopping new work before provider retirement."""

    async def quiesce(self) -> None:
        """Stop accepting new work while preserving in-flight operations."""
        ...


@runtime_checkable
class DrainableFeature(Protocol):
    """Optional protocol for draining in-flight operations before retirement."""

    async def drain(self) -> None:
        """Wait until in-flight feature work has safely completed."""
        ...
