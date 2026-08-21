"""Reconciler comparing desired and actual states to execute mount/unmount."""

import inspect
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from app.kernel.context import DefaultFeatureContext
from app.kernel.feature import Feature, FeatureSpec, FeatureState
from app.kernel.graph import DependencyGraph, GraphResolution
from app.kernel.scope import FeatureScope

if TYPE_CHECKING:
    from app.kernel.capability import CapabilityKey
    from app.kernel.events import EventBus
    from app.kernel.registry import ServiceRegistry


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    """Report summarizing the outcome of a reconciliation pass.

    Attributes:
        started: Tuple of feature IDs started during this pass.
        stopped: Tuple of feature IDs stopped during this pass.
        active_features: Tuple of currently active feature IDs.
        blocked_features: Mapping of blocked feature IDs to diagnostic reasons.
        feature_states: Snapshot map of all feature IDs to FeatureState.
        errors: Mapping of feature IDs to startup error descriptions.
    """

    started: tuple[str, ...]
    stopped: tuple[str, ...]
    active_features: tuple[str, ...]
    blocked_features: dict[str, str]
    feature_states: dict[str, FeatureState]
    errors: dict[str, str]


class Reconciler:
    """Orchestrates transactional mounting and unmounting of features."""

    def __init__(
        self,
        registry: ServiceRegistry,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the reconciler.

        Args:
            registry: Central ServiceRegistry used for capability binding.
            event_bus: Optional central EventBus used for inter-feature messaging.
        """
        self._registry = registry
        if event_bus is None:
            from app.kernel.events import EventBus as BusClass

            self._event_bus = BusClass()
        else:
            self._event_bus = event_bus
        self._active_features: dict[str, Feature] = {}
        self._active_scopes: dict[str, FeatureScope] = {}
        self._feature_states: dict[str, FeatureState] = {}
        self._active_configs: dict[str, object] = {}

    @property
    def feature_states(self) -> dict[str, FeatureState]:
        """Return a copy of all current feature states.

        Returns:
            Dictionary mapping feature IDs to FeatureState.
        """
        return dict(self._feature_states)

    @property
    def active_features(self) -> tuple[str, ...]:
        """Return tuple of all currently active feature IDs.

        Returns:
            Tuple of active feature IDs.
        """
        return tuple(self._active_features.keys())

    async def reconcile(
        self,
        discovered_features: Mapping[str, Feature],
        enabled_feature_ids: Iterable[str],
        configs: Mapping[str, object] | None = None,
        provider_selections: Mapping[str, str] | None = None,
    ) -> ReconciliationReport:
        """Reconcile active features with desired configuration.

        Args:
            discovered_features: Mapping of feature_id to Feature instances.
            enabled_feature_ids: Collection of feature IDs requested to run.
            configs: Optional mapping of feature_id to feature config objects.
            provider_selections: Optional capability-to-provider mappings.

        Returns:
            ReconciliationReport detailing started, stopped, and active features.
        """
        enabled_set = set(enabled_feature_ids)
        config_map = dict(configs or {})
        specs: dict[str, FeatureSpec] = {
            f_id: feat.spec for f_id, feat in discovered_features.items()
        }

        graph = DependencyGraph(specs, provider_selections=provider_selections)
        resolution = graph.resolve(enabled_set, provider_selections=provider_selections)

        to_stop, to_start = self._plan_transitions(resolution, config_map)
        stopped_list = await self._execute_stops(to_stop)
        started_list, errors = await self._execute_starts(
            resolution.start_order, to_start, discovered_features, config_map
        )

        all_blocked = self._update_feature_states(
            discovered_features, enabled_set, resolution, errors
        )

        return ReconciliationReport(
            started=tuple(started_list),
            stopped=tuple(stopped_list),
            active_features=tuple(self._active_features.keys()),
            blocked_features=all_blocked,
            feature_states=dict(self._feature_states),
            errors=errors,
        )

    def _plan_transitions(
        self,
        resolution: GraphResolution,
        config_map: dict[str, object],
    ) -> tuple[set[str], set[str]]:
        """Calculate features to stop and start.

        Args:
            resolution: Current dependency resolution.
            config_map: Desired configuration mapping.

        Returns:
            Tuple of (features_to_stop set, features_to_start set).
        """
        target_active = set(resolution.eligible_features)
        current_active = set(self._active_features.keys())

        to_remount: set[str] = set()
        for f_id in current_active.intersection(target_active):
            if self._active_configs.get(f_id) != config_map.get(f_id):
                to_remount.add(f_id)

        to_stop = (current_active - target_active) | to_remount
        to_start = (target_active - current_active) | to_remount
        return to_stop, to_start

    async def _execute_stops(self, to_stop: set[str]) -> list[str]:
        """Execute unmounting of features in reverse active order.

        Args:
            to_stop: Set of feature IDs to stop.

        Returns:
            List of successfully stopped feature IDs.
        """
        stopped: list[str] = []
        for f_id in list(self._active_features.keys())[::-1]:
            if f_id in to_stop:
                await self._stop_feature(f_id)
                stopped.append(f_id)
        return stopped

    async def _execute_starts(
        self,
        start_order: Sequence[str],
        to_start: set[str],
        discovered_features: Mapping[str, Feature],
        config_map: dict[str, object],
    ) -> tuple[list[str], dict[str, str]]:
        """Execute mounting of features in topological start order.

        Args:
            start_order: Topological execution order.
            to_start: Set of features to start.
            discovered_features: Discovered feature instances.
            config_map: Configuration dictionary.

        Returns:
            Tuple of (started feature ID list, errors map).
        """
        started: list[str] = []
        errors: dict[str, str] = {}

        for f_id in start_order:
            if f_id in to_start:
                feature = discovered_features.get(f_id)
                if feature is None:
                    self._feature_states[f_id] = FeatureState.MISSING
                    continue

                cfg = config_map.get(f_id)
                success, error_msg = await self._start_feature(feature, cfg)
                if success:
                    started.append(f_id)
                else:
                    errors[f_id] = error_msg or "Failed to mount"

        return started, errors

    def _update_feature_states(
        self,
        discovered_features: Mapping[str, Feature],
        enabled_set: set[str],
        resolution: GraphResolution,
        errors: Mapping[str, str],
    ) -> dict[str, str]:
        """Update lifecycle state enum for all known features.

        Args:
            discovered_features: Discovered feature instances.
            enabled_set: Enabled feature IDs.
            resolution: Graph resolution results.
            errors: Startup errors map.

        Returns:
            Combined blocked features reason map.
        """
        blocked = dict(resolution.blocked_features)
        for f_id in discovered_features:
            if f_id in self._active_features:
                self._feature_states[f_id] = FeatureState.ACTIVE
            elif f_id in errors:
                self._feature_states[f_id] = FeatureState.FAILED_START
            elif f_id in blocked:
                self._feature_states[f_id] = FeatureState.BLOCKED
            elif f_id not in enabled_set:
                self._feature_states[f_id] = FeatureState.DISABLED

        for f_id in enabled_set:
            if f_id not in discovered_features:
                self._feature_states[f_id] = FeatureState.MISSING
                blocked[f_id] = "Feature package not found (MISSING)"

        return blocked

    async def _start_feature(
        self,
        feature: Feature,
        config: object,
    ) -> tuple[bool, str | None]:
        """Mount a single feature within a new temporal scope transactionally.

        Args:
            feature: Feature instance to mount.
            config: Configuration object for the feature.

        Returns:
            Tuple of (success boolean, optional error message).
        """
        f_id = feature.spec.feature_id
        self._feature_states[f_id] = FeatureState.PREPARING
        scope = FeatureScope(owner_id=f_id)

        def registrar(cap: CapabilityKey[Any], impl: object, sc: FeatureScope) -> None:
            self._registry.register(cap, impl, owner_id=f_id, scope=sc)

        context = DefaultFeatureContext(
            spec=feature.spec,
            scope=scope,
            resolver=self._registry.resolve,
            provider_registrar=registrar,
            event_bus=self._event_bus,
        )

        try:
            await feature.mount(context, config)
            self._active_features[f_id] = feature
            self._active_scopes[f_id] = scope
            self._active_configs[f_id] = config
            self._feature_states[f_id] = FeatureState.ACTIVE
            return True, None
        except Exception as err:  # noqa: BLE001
            await scope.close()
            self._feature_states[f_id] = FeatureState.FAILED_START
            return False, str(err)

    async def swap_feature_transactional(
        self,
        feature: Feature,
        config: object,
    ) -> tuple[bool, str | None]:
        """Perform zero-downtime transactional replacement using a shadow scope.

        Sequence (Section 26):
            1. Create shadow scope.
            2. Mount new feature instance in shadow context.
            3. Run optional health check.
            4. Atomically swap registry bindings with incremented generation.
            5. Dispose old scope.
            6. Roll back shadow scope on any failure, leaving active provider intact.

        Args:
            feature: New feature instance to mount.
            config: Configuration for the new feature.

        Returns:
            Tuple of (success boolean, optional error message).
        """
        f_id = feature.spec.feature_id
        shadow_scope = FeatureScope(owner_id=f"{f_id}_shadow")
        shadow_providers: list[tuple[CapabilityKey[Any], object]] = []

        def shadow_registrar(
            cap: CapabilityKey[Any], impl: object, _sc: FeatureScope
        ) -> None:
            shadow_providers.append((cap, impl))

        shadow_context = DefaultFeatureContext(
            spec=feature.spec,
            scope=shadow_scope,
            resolver=self._registry.resolve,
            provider_registrar=shadow_registrar,
            event_bus=self._event_bus,
        )

        try:
            # 1. Mount into shadow context
            await feature.mount(shadow_context, config)

            # 2. Optional health check
            if hasattr(feature, "health_check") and callable(feature.health_check):
                res = feature.health_check()
                if inspect.isawaitable(res):
                    await res

            # 3. Commit: Transfer shadow providers into global registry with real scope
            real_scope = FeatureScope(owner_id=f_id)
            for cap, impl in shadow_providers:
                self._registry.replace_binding(
                    cap, impl, owner_id=f_id, scope=real_scope
                )

            # 4. Dispose old scope and record new active feature
            old_scope = self._active_scopes.get(f_id)
            self._active_features[f_id] = feature
            self._active_scopes[f_id] = real_scope
            self._active_configs[f_id] = config
            self._feature_states[f_id] = FeatureState.ACTIVE

            if old_scope is not None:
                await old_scope.close()

            await shadow_scope.close()
            return True, None
        except Exception as err:  # noqa: BLE001
            # Rollback: dispose shadow scope without touching active provider
            await shadow_scope.close()
            return False, str(err)

    async def _stop_feature(self, f_id: str) -> None:
        """Unmount an active feature and close its private scope.

        Args:
            f_id: Identifier of the feature to stop.
        """
        self._feature_states[f_id] = FeatureState.STOPPING
        scope = self._active_scopes.pop(f_id, None)
        self._active_features.pop(f_id, None)
        self._active_configs.pop(f_id, None)

        if scope is not None:
            await scope.close()

        self._feature_states[f_id] = FeatureState.STOPPED

    async def stop_all(self) -> None:
        """Stop all active features in reverse order."""
        for f_id in list(self._active_features.keys())[::-1]:
            await self._stop_feature(f_id)
