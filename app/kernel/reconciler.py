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
        return tuple(self._active_features.keys())

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
        specs = {f_id: feature.spec for f_id, feature in discovered_features.items()}
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
        config_map: dict[str, object],
        specs: Mapping[str, FeatureSpec],
    ) -> tuple[set[str], set[str]]:
        target_active = set(resolution.eligible_features)
        current_active = set(self._active_features)

        changed: set[str] = {
            f_id
            for f_id in current_active.intersection(target_active)
            if self._active_configs.get(f_id) != config_map.get(f_id)
        }
        remount = self._dependent_closure(changed, specs, resolution.provider_map)
        remount &= current_active.intersection(target_active)

        to_stop = (current_active - target_active) | remount
        to_start = (target_active - current_active) | remount
        return to_stop, to_start

    def _dependent_closure(
        self,
        seed_features: Iterable[str],
        specs: Mapping[str, FeatureSpec],
        provider_map: Mapping[str, str],
    ) -> set[str]:
        """Return seed features plus every transitive required/optional consumer."""
        affected = set(seed_features)
        changed = True
        while changed:
            changed = False
            for consumer_id, spec in specs.items():
                if consumer_id in affected:
                    continue
                dependencies = tuple(spec.requires) + tuple(spec.optional)
                providers = {
                    provider_map.get(cap.identifier) for cap in dependencies
                }
                if any(provider in affected for provider in providers):
                    affected.add(consumer_id)
                    changed = True
        return affected

    async def _execute_stops(self, to_stop: set[str]) -> list[str]:
        stopped: list[str] = []
        for f_id in list(self._active_features)[::-1]:
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
        started: list[str] = []
        errors: dict[str, str] = {}
        for f_id in start_order:
            if f_id not in to_start:
                continue
            feature = discovered_features.get(f_id)
            if feature is None:
                self._feature_states[f_id] = FeatureState.MISSING
                continue
            success, error = await self._start_feature(feature, config_map.get(f_id))
            if success:
                started.append(f_id)
            else:
                errors[f_id] = error or "Failed to mount"
        return started, errors

    def _update_feature_states(
        self,
        discovered_features: Mapping[str, Feature],
        enabled_set: set[str],
        resolution: GraphResolution,
        errors: Mapping[str, str],
    ) -> dict[str, str]:
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

    async def _handle_task_failure(self, owner_id: str, error: BaseException) -> None:
        """Fail a feature at runtime and stop active consumers of its capabilities."""
        if owner_id not in self._active_features:
            return
        owner = self._active_features[owner_id]
        provided = {cap.identifier for cap in owner.spec.provides}
        affected: set[str] = {owner_id}
        changed = True
        while changed:
            changed = False
            for f_id, feature in self._active_features.items():
                if f_id in affected:
                    continue
                dependencies = {
                    cap.identifier
                    for cap in tuple(feature.spec.requires) + tuple(feature.spec.optional)
                }
                upstream_caps = set(provided)
                for affected_id in affected:
                    active = self._active_features.get(affected_id)
                    if active is not None:
                        upstream_caps.update(cap.identifier for cap in active.spec.provides)
                if dependencies.intersection(upstream_caps):
                    affected.add(f_id)
                    changed = True

        for f_id in list(self._active_features)[::-1]:
            if f_id not in affected:
                continue
            if f_id == owner_id:
                self._feature_states[f_id] = FeatureState.FAILED_RUNTIME
            else:
                self._feature_states[f_id] = FeatureState.BLOCKED
            await self._remove_active_feature(f_id)
        self._feature_states[owner_id] = FeatureState.FAILED_RUNTIME
        _ = error

    def _new_scope(self, owner_id: str) -> FeatureScope:
        return FeatureScope(owner_id=owner_id, on_task_failure=self._handle_task_failure)

    async def _start_feature(
        self,
        feature: Feature,
        config: object,
    ) -> tuple[bool, str | None]:
        f_id = feature.spec.feature_id
        self._feature_states[f_id] = FeatureState.PREPARING
        scope = self._new_scope(f_id)

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
        except Exception as err:  # noqa: BLE001
            await scope.close()
            self._feature_states[f_id] = FeatureState.FAILED_START
            return False, str(err)

        self._active_features[f_id] = feature
        self._active_scopes[f_id] = scope
        self._active_configs[f_id] = config
        self._feature_states[f_id] = FeatureState.ACTIVE
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
        f_id = feature.spec.feature_id
        staged_scope = self._new_scope(f_id)
        staged_providers: list[tuple[CapabilityKey[Any], object]] = []

        def staged_registrar(
            cap: CapabilityKey[Any], impl: object, _scope: FeatureScope
        ) -> None:
            staged_providers.append((cap, impl))

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
        except Exception as err:  # noqa: BLE001
            await staged_scope.close()
            return False, str(err)

        old_scope = self._active_scopes.get(f_id)
        for cap, impl in staged_providers:
            self._registry.register(cap, impl, owner_id=f_id, scope=staged_scope)

        self._active_features[f_id] = feature
        self._active_scopes[f_id] = staged_scope
        self._active_configs[f_id] = config
        self._feature_states[f_id] = FeatureState.ACTIVE

        cleanup_warning: str | None = None
        if old_scope is not None:
            try:
                await old_scope.close()
            except Exception as err:  # noqa: BLE001
                cleanup_warning = (
                    "Replacement committed, but old scope cleanup failed: " + str(err)
                )

        specs = {feature_id: item.spec for feature_id, item in discovered_features.items()}
        resolution = DependencyGraph(specs).resolve(
            discovered_features.keys(),
            provider_selection=provider_selection,
        )
        dependents = self._dependent_closure({f_id}, specs, resolution.provider_map) - {f_id}
        active_dependents = dependents.intersection(self._active_features)
        if active_dependents:
            await self._execute_stops(active_dependents)
            ordered_dependents = [
                item for item in resolution.start_order if item in active_dependents
            ]
            _, errors = await self._execute_starts(
                ordered_dependents,
                active_dependents,
                discovered_features,
                dict(configs),
            )
            if errors:
                cleanup_warning = (
                    (cleanup_warning + "; " if cleanup_warning else "")
                    + "Dependent remount failures: "
                    + ", ".join(f"{key}: {value}" for key, value in errors.items())
                )
        return True, cleanup_warning

    async def _remove_active_feature(self, f_id: str) -> None:
        scope = self._active_scopes.pop(f_id, None)
        self._active_features.pop(f_id, None)
        self._active_configs.pop(f_id, None)
        if scope is not None:
            await scope.close()

    async def _stop_feature(self, f_id: str) -> None:
        self._feature_states[f_id] = FeatureState.STOPPING
        await self._remove_active_feature(f_id)
        self._feature_states[f_id] = FeatureState.STOPPED

    async def stop_all(self) -> None:
        """Stop all active features in reverse activation order."""
        for f_id in list(self._active_features)[::-1]:
            await self._stop_feature(f_id)
