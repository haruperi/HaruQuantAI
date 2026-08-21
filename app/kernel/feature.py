"""Feature specifications, lifecycle states, and optional lifecycle protocols."""

from __future__ import annotations

from collections.abc import Awaitable
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
    """Static identity, capability graph, state, and configuration declaration."""

    feature_id: str
    domain: str
    provides: frozenset[CapabilityKey[Any]]
    requires: frozenset[CapabilityKey[Any]] = field(default_factory=frozenset)
    optional: frozenset[CapabilityKey[Any]] = field(default_factory=frozenset)
    conflicts: frozenset[str] = field(default_factory=frozenset)
    description: str = ""
    state: StateDeclaration | None = None
    config_keys: frozenset[str] = field(default_factory=frozenset)

    def validate(self) -> None:
        """Validate feature identity and declaration consistency."""
        if not self.feature_id.strip():
            raise ValueError("Feature ID must not be empty")
        if not self.domain.strip():
            raise ValueError("Domain must not be empty")
        overlap = self.provides.intersection(self.requires)
        if overlap:
            identifiers = ", ".join(
                sorted(capability.identifier for capability in overlap)
            )
            raise ValueError(
                "Feature cannot both provide and require capability: " + identifiers
            )
        dependency_overlap = self.requires.intersection(self.optional)
        if dependency_overlap:
            identifiers = ", ".join(
                sorted(capability.identifier for capability in dependency_overlap)
            )
            raise ValueError(
                "Capability cannot be both required and optional: " + identifiers
            )
        invalid_config_keys = sorted(
            key for key in self.config_keys if not key or key.strip() != key
        )
        if invalid_config_keys:
            raise ValueError(
                f"Feature config keys must be non-empty and trimmed: "
                f"{invalid_config_keys}"
            )


@runtime_checkable
class Feature(Protocol):
    """Protocol satisfied by every composable feature implementation."""

    spec: FeatureSpec

    async def mount(
        self,
        context: FeatureContext,
        config: object,
    ) -> None:
        """Register all lifecycle-owned effects and capability providers."""
        ...


@runtime_checkable
class HealthCheckableFeature(Protocol):
    """Optional pre-commit health-check lifecycle protocol."""

    def health_check(self) -> Awaitable[None] | None:
        """Validate replacement health before publication."""
        ...


@runtime_checkable
class QuiesceableFeature(Protocol):
    """Optional protocol for pausing new work before retirement."""

    def quiesce(self) -> Awaitable[None] | None:
        """Stop accepting new work before teardown."""
        ...


@runtime_checkable
class DrainableFeature(Protocol):
    """Optional protocol for draining in-flight work before retirement."""

    def drain(self) -> Awaitable[None] | None:
        """Wait for in-flight work to complete before teardown."""
        ...
