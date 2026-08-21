"""System domain public capability-aware facade and introspection."""

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
    """Introspection report for a versioned capability.

    Attributes:
        identifier: Formatted capability identifier (e.g. 'data.historical-bars@1').
        is_available: Whether an active provider is bound.
        provider_feature_id: Owning feature ID if available, None otherwise.
        generation: Active binding generation number, or None.
        registered_at: Timestamp when provider was bound, or None.
    """

    identifier: str
    is_available: bool
    provider_feature_id: str | None = None
    generation: int | None = None
    registered_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class FeatureDiagnosticInfo:
    """Diagnostic report for a feature, separating package and capability dependencies.

    Attributes:
        feature_id: Unique feature identifier.
        is_active: Whether feature is currently mounted and active.
        state: Current lifecycle state name if known.
        package_error: Python package/import failure reason, if any.
        capability_error: Runtime capability dependency failure reason, if any.
    """

    feature_id: str
    is_active: bool
    state: str | None = None
    package_error: str | None = None
    capability_error: str | None = None


class SystemAPI:
    """Stable facade providing system infrastructure capabilities and introspection."""

    def __init__(
        self,
        registry: ServiceRegistry,
        engine: CompositionEngine | None = None,
    ) -> None:
        """Initialize SystemAPI.

        Args:
            registry: Central ServiceRegistry.
            engine: Optional CompositionEngine for runtime status introspection.
        """
        self._registry = registry
        self._engine = engine

    @property
    def is_storage_available(self) -> bool:
        """Check if persistent storage engine is active."""
        return self._registry.is_available(SYSTEM_STORAGE)

    @property
    def is_clock_available(self) -> bool:
        """Check if system clock capability is active."""
        return self._registry.is_available(SYSTEM_CLOCK)

    @property
    def is_metrics_available(self) -> bool:
        """Check if system metrics collector is active."""
        return self._registry.is_available(SYSTEM_METRICS)

    def get_storage_engine(self) -> StorageEngine:
        """Resolve active persistent storage engine.

        Returns:
            Active StorageEngine provider.

        Raises:
            CapabilityUnavailableError: If system.storage@1 is absent.
        """
        return self._registry.require(SYSTEM_STORAGE)

    def get_clock(self) -> SystemClock:
        """Resolve active system clock.

        Returns:
            Active SystemClock provider.

        Raises:
            CapabilityUnavailableError: If system.clock@1 is absent.
        """
        return self._registry.require(SYSTEM_CLOCK)

    def get_metrics(self) -> MetricsCollector:
        """Resolve active metrics collector.

        Returns:
            Active MetricsCollector provider.

        Raises:
            CapabilityUnavailableError: If system.metrics@1 is absent.
        """
        return self._registry.require(SYSTEM_METRICS)

    def inspect_capability(
        self,
        capability: CapabilityKey[Any] | str,
    ) -> CapabilityInfo:
        """Inspect status and provider metadata for a capability.

        Args:
            capability: Capability key or formatted identifier string.

        Returns:
            CapabilityInfo snapshot.
        """
        cap_id = capability if isinstance(capability, str) else capability.identifier
        binding = self._registry.get_binding(cap_id)
        if binding is not None:
            return CapabilityInfo(
                identifier=cap_id,
                is_available=True,
                provider_feature_id=binding.token.owner_id,
                generation=binding.token.generation,
                registered_at=binding.registered_at,
            )
        return CapabilityInfo(
            identifier=cap_id,
            is_available=False,
            provider_feature_id=None,
            generation=None,
            registered_at=None,
        )

    def list_capabilities(self) -> dict[str, CapabilityInfo]:
        """List all active capabilities and their metadata.

        Returns:
            Dictionary of capability identifier to CapabilityInfo.
        """
        active_tokens = self._registry.active_capabilities()
        res: dict[str, CapabilityInfo] = {}
        for cap_id in active_tokens:
            res[cap_id] = self.inspect_capability(cap_id)
        return res

    def inspect_feature(self, feature_id: str) -> FeatureDiagnosticInfo:
        """Inspect detailed health and dependency diagnostics for a feature.

        Args:
            feature_id: Unique feature identifier.

        Returns:
            FeatureDiagnosticInfo detailing package vs capability dependency health.
        """
        is_active = False
        state_name: str | None = None
        pkg_err: str | None = None
        cap_err: str | None = None

        if self._engine is not None:
            status = self._engine.get_status()
            is_active = feature_id in status.active_features
            state = status.feature_states.get(feature_id)
            if state is not None:
                state_name = state.value
            pkg_err = status.package_dependency_errors.get(feature_id)
            cap_err = status.capability_dependency_errors.get(feature_id)

        return FeatureDiagnosticInfo(
            feature_id=feature_id,
            is_active=is_active,
            state=state_name,
            package_error=pkg_err,
            capability_error=cap_err,
        )

    def list_package_dependency_errors(self) -> dict[str, str]:
        """List all features failing due to missing Python package dependencies.

        Returns:
            Dictionary mapping feature ID to import error explanation.
        """
        if self._engine is not None:
            return dict(self._engine.get_status().package_dependency_errors)
        return {}

    def list_capability_dependency_errors(self) -> dict[str, str]:
        """List all features blocked due to missing runtime capability dependencies.

        Returns:
            Dictionary mapping feature ID to capability block explanation.
        """
        if self._engine is not None:
            return dict(self._engine.get_status().capability_dependency_errors)
        return {}

    def get_runtime_status(self) -> RuntimeStatus | None:
        """Retrieve overall application runtime readiness status if engine is bound.

        Returns:
            RuntimeStatus snapshot or None.
        """
        if self._engine is not None:
            return self._engine.get_status()
        return None
