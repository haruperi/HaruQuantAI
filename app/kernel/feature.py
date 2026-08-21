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
    """Static capability declaration and metadata for a feature package.

    Attributes:
        feature_id: Unique feature identifier (e.g., 'FEAT-DATA-RETRIEVE_BARS').
        domain: Business domain name (e.g., 'data', 'broker', 'risk').
        provides: Set of capability keys provided by this feature.
        requires: Set of mandatory capability keys required for activation.
        optional: Set of optional capability keys consumed if available.
        conflicts: Set of conflicting feature IDs that cannot run concurrently.
        description: Brief description of the feature responsibility.
        state: Optional persistent state ownership declaration.
    """

    feature_id: str
    domain: str
    provides: frozenset[CapabilityKey[Any]]
    requires: frozenset[CapabilityKey[Any]] = field(default_factory=frozenset)
    optional: frozenset[CapabilityKey[Any]] = field(default_factory=frozenset)
    conflicts: frozenset[str] = field(default_factory=frozenset)
    description: str = ""
    state: StateDeclaration | None = None

    def validate(self) -> None:
        """Validate specification consistency and structural integrity.

        Raises:
            ValueError: If specifications violate invariants (e.g., overlap).
        """
        if not self.feature_id.strip():
            msg = "Feature ID must not be empty."
            raise ValueError(msg)
        if not self.domain.strip():
            msg = "Domain must not be empty."
            raise ValueError(msg)
        overlap = self.provides.intersection(self.requires)
        if overlap:
            overlap_ids = ", ".join(k.identifier for k in overlap)
            msg = f"Feature cannot both provide and require capability: {overlap_ids}"
            raise ValueError(msg)


@runtime_checkable
class Feature(Protocol):
    """Protocol satisfied by all composable feature implementations."""

    spec: FeatureSpec

    async def mount(
        self,
        context: FeatureContext,
        config: object,
    ) -> None:
        """Mount the feature into the given lifecycle context with configuration.

        Args:
            context: Reversible feature context providing scoped operations.
            config: Validated feature-specific configuration object.
        """
        ...
