"""System capability facade and runtime diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from app.contracts.system.clock import SYSTEM_CLOCK, SystemClock
from app.contracts.system.metrics import SYSTEM_METRICS, MetricsCollector
from app.contracts.system.storage import SYSTEM_STORAGE, StorageEngine

if TYPE_CHECKING:
    from app.composition.engine import CompositionEngine, RuntimeStatus
    from app.kernel.capability import CapabilityKey
    from app.kernel.registry import ServiceRegistry


@dataclass(frozen=True, slots=True)
class CapabilityInfo:
    """Provider metadata for one versioned capability."""

    identifier: str
    is_available: bool
    provider_feature_id: str | None = None
    generation: int | None = None
    registered_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class FeatureDiagnosticInfo:
    """Lifecycle and degradation diagnostics for one feature."""

    feature_id: str
    is_active: bool
    state: str | None = None
    package_error: str | None = None
    capability_error: str | None = None
    runtime_error: str | None = None
    replacement_status: str | None = None
    cleanup_errors: tuple[str, ...] = ()
    consumer_errors: tuple[str, ...] = ()


class SystemAPI:
    """Resolve system capabilities and inspect composition state."""

    def __init__(
        self,
        registry: ServiceRegistry,
        engine: CompositionEngine | None = None,
    ) -> None:
        """Initialize the system facade."""
        self._registry = registry
        self._engine = engine

    @property
    def is_storage_available(self) -> bool:
        """Return whether persistent storage is active."""
        return self._registry.is_available(SYSTEM_STORAGE)

    @property
    def is_clock_available(self) -> bool:
        """Return whether the system clock is active."""
        return self._registry.is_available(SYSTEM_CLOCK)

    @property
    def is_metrics_available(self) -> bool:
        """Return whether metrics collection is active."""
        return self._registry.is_available(SYSTEM_METRICS)

    def get_storage_engine(self) -> StorageEngine:
        """Resolve the active storage engine."""
        return self._registry.require(SYSTEM_STORAGE)

    def get_clock(self) -> SystemClock:
        """Resolve the active system clock."""
        return self._registry.require(SYSTEM_CLOCK)

    def get_metrics(self) -> MetricsCollector:
        """Resolve the active metrics collector."""
        return self._registry.require(SYSTEM_METRICS)

    def inspect_capability(
        self,
        capability: CapabilityKey[Any] | str,
    ) -> CapabilityInfo:
        """Inspect one capability and its active provider generation."""
        identifier = (
            capability if isinstance(capability, str) else capability.identifier
        )
        binding = self._registry.get_binding(identifier)
        if binding is None:
            return CapabilityInfo(identifier=identifier, is_available=False)
        return CapabilityInfo(
            identifier=identifier,
            is_available=True,
            provider_feature_id=binding.token.owner_id,
            generation=binding.token.generation,
            registered_at=binding.registered_at,
        )

    def list_capabilities(self) -> dict[str, CapabilityInfo]:
        """Return active capability metadata keyed by identifier."""
        return {
            identifier: self.inspect_capability(identifier)
            for identifier in self._registry.active_capabilities()
        }

    def inspect_feature(self, feature_id: str) -> FeatureDiagnosticInfo:
        """Inspect package, capability, runtime, and replacement health."""
        if self._engine is None:
            return FeatureDiagnosticInfo(feature_id=feature_id, is_active=False)
        status = self._engine.get_status()
        state = status.feature_states.get(feature_id)
        replacement = status.replacement_reports.get(feature_id)
        return FeatureDiagnosticInfo(
            feature_id=feature_id,
            is_active=feature_id in status.active_features,
            state=state.value if state is not None else None,
            package_error=status.package_dependency_errors.get(feature_id),
            capability_error=status.capability_dependency_errors.get(feature_id),
            runtime_error=status.runtime_failures.get(feature_id),
            replacement_status=(
                replacement.status if replacement is not None else None
            ),
            cleanup_errors=(
                replacement.cleanup_errors if replacement is not None else ()
            ),
            consumer_errors=(
                replacement.consumer_errors if replacement is not None else ()
            ),
        )

    def list_package_dependency_errors(self) -> dict[str, str]:
        """Return package/import failures for enabled features."""
        if self._engine is None:
            return {}
        return dict(self._engine.get_status().package_dependency_errors)

    def list_capability_dependency_errors(self) -> dict[str, str]:
        """Return runtime capability blocks for enabled features."""
        if self._engine is None:
            return {}
        return dict(self._engine.get_status().capability_dependency_errors)

    def get_runtime_status(self) -> RuntimeStatus | None:
        """Return overall runtime status when an engine is attached."""
        return self._engine.get_status() if self._engine is not None else None
