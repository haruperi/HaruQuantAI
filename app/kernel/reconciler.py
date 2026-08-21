"""Reconcile desired and actual feature state with lifecycle-safe transitions."""

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
    """Report summarizing one reconciliation pass."""

    started: tuple[str, ...]
    stopped: tuple[str, ...]
    active_features: tuple[str, ...]
    blocked_features: dict[str, str]
    feature_states: dict[str, FeatureState]
    errors: dict[str, str]


class Reconciler:
    """Orchestrate transactional mounting, unmounting, and dependency recovery."""

    def __init__(
        self,
        registry: ServiceRegistry,
        event_bus: EventBus | None = None,
    ) -> None:
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
        return dict(self._feature_states)

    @property
    def active_features(self) -> tuple[str, ...]:
        return tuple(self._active_features)

    async def reconcile(
        self,
        discovered_features: Mapping[str, Feature],
        enabled_feature_ids: Iterable[str],
        configs: Mapping[str, object] | None = None,
        provider_selection: Mapping[str, str] | None = None,
    ) -> ReconciliationReport:
        """Reconcile active features against desired configuration."""
        enabled_set = set(enabled_feature_ids)
        config_map = dict(configs or {})
        specs = {
            feature_id: feature.spec
            for feature_id, feature in discovered_features.items()
        }
        resolution = DependencyGraph(specs).resolve(
            enabled_set,
            provider_selection=provider_selection,
        )
        to_stop, to_start = self._plan_transitions(
            resolution,
            config_map,
            specs,
        )
        stopped = await self._execute_stops(to_stop)
        started, errors = await self._execute_starts(
            resolution.start_order,
            to_start,
            discovered_features,
            config_map,
        )
        blocked = self._update_feature_states(
            discovered_features,
            enabled_set,
            resolution,
            errors,
        )
        return ReconciliationReport(
            started=tuple(started),
            stopped=tuple(stopped),
            active_features=tuple(self._active_features),
            blocked_features=blocked,
            feature_states=dict(self._feature_states),
            errors=errors,
        )

    def _plan_transitions(
        self,
        resolution: GraphResolution,
        config_map: Mapping[str, object],
        specs: Mapping[str, FeatureSpec],
    ) -> tuple[set[str], set[str]]:
        target_active = set(resolution.eligible_features)
        current_active = set(self._active_features)

        seeds: set[str] = current_active.symmetric_difference(target_active)
        seeds.update(
            feature_id
            for feature_id in current_active.intersection(target_active)
            if self._active_configs.get(feature_id) != config_map.get(feature_id)
        )

        for capability, target_provider in resolution.provider_map.items():
            active_binding = self._registry.get_binding(capability)
            if (
                active_binding is not None
                and active_binding.token.owner_id != target_provider
            ):
                seeds.add(active_binding.token.owner_id)
                seeds.add(target_provider)

        affected = self._dependent_closure(seeds, specs)
        remount = affected.intersection(current_active).intersection(target_active)
        to_stop = (current_active - target_active) | remount
        to_start = (target_active - current_active) | remount
        return to_stop, to_start

    def _dependent_closure(
        self,
        seed_features: Iterable[str],
        specs: Mapping[str, FeatureSpec],
    ) -> set[str]:
        """Return seed features plus every transitive required/optional consumer."""
        affected = set(seed_features)
        changed = True
        while changed:
            changed = False
            provided_capabilities = {
                capability.identifier
                for feature_id in affected
                if feature_id in specs
                for capability in specs[feature_id].provides
            }
            for consumer_id, spec in specs.items():
                if consumer_id in affected:
                    continue
                consumed = {
                    capability.identifier
                    for capability in tuple(spec.requires) + tuple(spec.optional)
                }
                if consumed.intersection(provided_capabilities):
                    affected.add(consumer_id)
                    changed = True
        return affected

    async def _execute_stops(self, to_stop: set[str]) -> list[str]:
        stopped: list[str] = []
        for feature_id in list(self._active_features)[::-1]:
            if feature_id in to_stop:
                await self._stop_feature(feature_id)
                stopped.append(feature_id)
        return stopped

    async def _execute_starts(
        self,
        start_order: Sequence[str],
        to_start: set[str],
        discovered_features: Mapping[str, Feature],
        config_map: Mapping[str, object],
    ) -> tuple[list[str], dict[str, str]]:
        started: list[str] = []
        errors: dict[str, str] = {}
        for feature_id in start_order:
            if feature_id not in to_start:
                continue
            feature = discovered_features.get(feature_id)
            if feature is None:
                self._feature_states[feature_id] = FeatureState.MISSING
                continue
            success, error = await self._start_feature(
                feature,
                config_map.get(feature_id),
            )
            if success:
                started.append(feature_id)
            else:
                errors[feature_id] = error or "Failed to mount"
        return started, errors

    def _update_feature_states(
        self,
        discovered_features: Mapping[str, Feature],
        enabled_set: set[str],
        resolution: GraphResolution,
        errors: Mapping[str, str],
    ) -> dict[str, str]:
        blocked = dict(resolution.blocked_features)
        for feature_id in discovered_features:
            if feature_id in self._active_features:
                self._feature_states[feature_id] = FeatureState.ACTIVE
            elif feature_id in errors:
                self._feature_states[feature_id] = FeatureState.FAILED_START
            elif feature_id in blocked:
                self._feature_states[feature_id] = FeatureState.BLOCKED
            elif feature_id not in enabled_set:
                self._feature_states[feature_id] = FeatureState.DISABLED
        for feature_id in enabled_set:
            if feature_id not in discovered_features:
                self._feature_states[feature_id] = FeatureState.MISSING
                blocked[feature_id] = "Feature package not found (MISSING)"
        return blocked

    async def _handle_task_failure(
        self,
        owner_id: str,
        error: BaseException,
    ) -> None:
        """Fail a feature at runtime and stop every active transitive consumer."""
        if owner_id not in self._active_features:
            return
        specs = {
            feature_id: feature.spec
            for feature_id, feature in self._active_features.items()
        }
        affected = self._dependent_closure({owner_id}, specs)
        for feature_id in list(self._active_features)[::-1]:
            if feature_id not in affected:
                continue
            self._feature_states[feature_id] = (
                FeatureState.FAILED_RUNTIME
                if feature_id == owner_id
                else FeatureState.BLOCKED
            )
            await self._remove_active_feature(feature_id)
        self._feature_states[owner_id] = FeatureState.FAILED_RUNTIME
        _ = error

    def _new_scope(self, owner_id: str) -> FeatureScope:
        return FeatureScope(
            owner_id=owner_id,
            on_task_failure=self._handle_task_failure,
        )

    async def _start_feature(
        self,
        feature: Feature,
        config: object,
    ) -> tuple[bool, str | None]:
        feature_id = feature.spec.feature_id
        self._feature_states[feature_id] = FeatureState.PREPARING
        scope = self._new_scope(feature_id)

        def registrar(
            capability: CapabilityKey[Any],
            implementation: object,
            owner_scope: FeatureScope,
        ) -> None:
            self._registry.register(
                capability,
                implementation,
                owner_id=feature_id,
                scope=owner_scope,
            )

        context = DefaultFeatureContext(
            spec=feature.spec,
            scope=scope,
            resolver=self._registry.resolve,
            provider_registrar=registrar,
            event_bus=self._event_bus,
        )
        try:
            await feature.mount(context, config)
        except Exception as error:  # noqa: BLE001
            await scope.close()
            self._feature_states[feature_id] = FeatureState.FAILED_START
            return False, str(error)

        self._active_features[feature_id] = feature
        self._active_scopes[feature_id] = scope
        self._active_configs[feature_id] = config
        self._feature_states[feature_id] = FeatureState.ACTIVE
        return True, None

    async def swap_feature_transactional(
        self,
        feature: Feature,
        config: object,
        discovered_features: Mapping[str, Feature],
        configs: Mapping[str, object],
        provider_selection: Mapping[str, str] | None = None,
    ) -> tuple[bool, str | None]:
        """Replace a feature using a staged scope that becomes the active scope."""
        feature_id = feature.spec.feature_id
        staged_scope = self._new_scope(feature_id)
        staged_providers: list[tuple[CapabilityKey[Any], object]] = []

        def staged_registrar(
            capability: CapabilityKey[Any],
            implementation: object,
            _scope: FeatureScope,
        ) -> None:
            staged_providers.append((capability, implementation))

        context = DefaultFeatureContext(
            spec=feature.spec,
            scope=staged_scope,
            resolver=self._registry.resolve,
            provider_registrar=staged_registrar,
            event_bus=self._event_bus,
        )
        try:
            await feature.mount(context, config)
            health_check = getattr(feature, "health_check", None)
            if callable(health_check):
                result = health_check()
                if inspect.isawaitable(result):
                    await result
        except Exception as error:  # noqa: BLE001
            await staged_scope.close()
            return False, str(error)

        old_scope = self._active_scopes.get(feature_id)
        for capability, implementation in staged_providers:
            self._registry.register(
                capability,
                implementation,
                owner_id=feature_id,
                scope=staged_scope,
            )

        self._active_features[feature_id] = feature
        self._active_scopes[feature_id] = staged_scope
        self._active_configs[feature_id] = config
        self._feature_states[feature_id] = FeatureState.ACTIVE

        warning: str | None = None
        if old_scope is not None:
            try:
                await old_scope.close()
            except Exception as error:  # noqa: BLE001
                warning = (
                    "Replacement committed, but old scope cleanup failed: "
                    + str(error)
                )

        enabled_ids = set(configs)
        enabled_ids.add(feature_id)
        specs = {
            item_id: item.spec
            for item_id, item in discovered_features.items()
        }
        resolution = DependencyGraph(specs).resolve(
            enabled_ids,
            provider_selection=provider_selection,
        )
        dependents = self._dependent_closure({feature_id}, specs) - {feature_id}
        active_dependents = dependents.intersection(self._active_features)
        if active_dependents:
            await self._execute_stops(active_dependents)
            ordered_dependents = [
                item
                for item in resolution.start_order
                if item in active_dependents
            ]
            _, errors = await self._execute_starts(
                ordered_dependents,
                active_dependents,
                discovered_features,
                configs,
            )
            if errors:
                prefix = f"{warning}; " if warning else ""
                warning = prefix + "Dependent remount failures: " + ", ".join(
                    f"{item_id}: {message}"
                    for item_id, message in errors.items()
                )
        return True, warning

    async def _remove_active_feature(self, feature_id: str) -> None:
        scope = self._active_scopes.pop(feature_id, None)
        self._active_features.pop(feature_id, None)
        self._active_configs.pop(feature_id, None)
        if scope is not None:
            await scope.close()

    async def _stop_feature(self, feature_id: str) -> None:
        self._feature_states[feature_id] = FeatureState.STOPPING
        await self._remove_active_feature(feature_id)
        self._feature_states[feature_id] = FeatureState.STOPPED

    async def stop_all(self) -> None:
        """Stop all active features in reverse activation order."""
        for feature_id in list(self._active_features)[::-1]:
            await self._stop_feature(feature_id)
