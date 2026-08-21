"""Reconcile desired and actual feature state with lifecycle-safe transitions."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from app.kernel.capability import CapabilityKey
from app.kernel.context import DefaultFeatureContext
from app.kernel.feature import (
    DrainableFeature,
    Feature,
    FeatureSpec,
    FeatureState,
    HealthCheckableFeature,
    QuiesceableFeature,
)
from app.kernel.graph import DependencyGraph, GraphResolution
from app.kernel.replacement import ReplacementReport
from app.kernel.scope import FeatureScope

if TYPE_CHECKING:
    from app.kernel.events import EventBus
    from app.kernel.registry import ServiceRegistry

RuntimeFailureCallback = Callable[[str, str, BaseException], Awaitable[None] | None]
StagedProvider = tuple[CapabilityKey[Any], object]


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    """Summarize one desired-versus-actual reconciliation pass."""

    started: tuple[str, ...]
    stopped: tuple[str, ...]
    active_features: tuple[str, ...]
    blocked_features: dict[str, str]
    feature_states: dict[str, FeatureState]
    errors: dict[str, str]


class Reconciler:
    """Own feature scopes and execute deterministic lifecycle transitions."""

    def __init__(
        self,
        registry: ServiceRegistry,
        event_bus: EventBus | None = None,
        failure_callback: RuntimeFailureCallback | None = None,
    ) -> None:
        """Initialize the reconciler."""
        self._registry = registry
        if event_bus is None:
            from app.kernel.events import EventBus as BusClass

            self._event_bus = BusClass()
        else:
            self._event_bus = event_bus
        self._failure_callback = failure_callback
        self._active_features: dict[str, Feature] = {}
        self._active_scopes: dict[str, FeatureScope] = {}
        self._feature_states: dict[str, FeatureState] = {}
        self._active_configs: dict[str, object] = {}
        self._active_resolution: GraphResolution | None = None
        self._known_features: dict[str, Feature] = {}
        self._desired_enabled: set[str] = set()
        self._desired_configs: dict[str, object] = {}
        self._provider_selections: dict[str, str] = {}
        self._runtime_failures: dict[str, str] = {}
        self._replacement_reports: dict[str, ReplacementReport] = {}
        self._startup_blocks: dict[str, str] = {}
        self._last_report: ReconciliationReport | None = None

    def set_failure_callback(
        self,
        callback: RuntimeFailureCallback | None,
    ) -> None:
        """Set the engine-level serialized runtime-failure callback."""
        self._failure_callback = callback

    @property
    def feature_states(self) -> dict[str, FeatureState]:
        """Return a snapshot of feature lifecycle states."""
        return dict(self._feature_states)

    @property
    def active_features(self) -> tuple[str, ...]:
        """Return active feature IDs in activation order."""
        return tuple(self._active_features)

    @property
    def runtime_failures(self) -> dict[str, str]:
        """Return the most recent runtime failure per feature."""
        return dict(self._runtime_failures)

    @property
    def replacement_reports(self) -> dict[str, ReplacementReport]:
        """Return the latest replacement report per feature."""
        return dict(self._replacement_reports)

    @property
    def last_report(self) -> ReconciliationReport | None:
        """Return the latest reconciliation report."""
        return self._last_report

    async def reconcile(
        self,
        discovered_features: Mapping[str, Feature],
        enabled_feature_ids: Iterable[str],
        configs: Mapping[str, object] | None = None,
        provider_selections: Mapping[str, str] | None = None,
    ) -> ReconciliationReport:
        """Reconcile active features against a desired configuration."""
        enabled_set = set(enabled_feature_ids)
        config_map = dict(configs or {})
        selection_map = dict(provider_selections or {})
        specs = {
            feature_id: feature.spec
            for feature_id, feature in discovered_features.items()
        }
        resolution = DependencyGraph(
            specs,
            provider_selections=selection_map,
        ).resolve(enabled_set)

        to_stop, to_start = self._plan_transitions(resolution, config_map)
        stop_order = self._combined_stop_order(resolution)
        stopped = await self._execute_stops(to_stop, stop_order)
        self._startup_blocks = {}
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

        self._known_features = dict(discovered_features)
        self._desired_enabled = set(enabled_set)
        self._desired_configs = dict(config_map)
        self._provider_selections = dict(selection_map)
        for feature_id in started:
            self._runtime_failures.pop(feature_id, None)
        self._commit_active_resolution()

        report = ReconciliationReport(
            started=tuple(started),
            stopped=tuple(stopped),
            active_features=tuple(self._active_features),
            blocked_features=blocked,
            feature_states=dict(self._feature_states),
            errors=errors,
        )
        self._last_report = report
        return report

    def _plan_transitions(
        self,
        resolution: GraphResolution,
        config_map: Mapping[str, object],
    ) -> tuple[set[str], set[str]]:
        target_active = set(resolution.eligible_features)
        current_active = set(self._active_features)
        seeds = current_active.symmetric_difference(target_active)
        seeds.update(
            feature_id
            for feature_id in current_active.intersection(target_active)
            if self._active_configs.get(feature_id) != config_map.get(feature_id)
        )

        previous_provider_map = (
            self._active_resolution.provider_map
            if self._active_resolution is not None
            else {}
        )
        for capability in set(previous_provider_map) | set(resolution.provider_map):
            previous_provider = previous_provider_map.get(capability)
            next_provider = resolution.provider_map.get(capability)
            if previous_provider == next_provider:
                continue
            if previous_provider is not None:
                seeds.add(previous_provider)
            if next_provider is not None:
                seeds.add(next_provider)

        affected = set(seeds)
        for feature_id in tuple(seeds):
            if self._active_resolution is not None:
                affected.update(
                    self._active_resolution.get_transitive_dependents(feature_id)
                )
            affected.update(resolution.get_transitive_dependents(feature_id))

        remount = affected.intersection(current_active).intersection(target_active)
        to_stop = (current_active - target_active) | remount
        to_start = (target_active - current_active) | remount
        return to_stop, to_start

    def _combined_stop_order(
        self,
        next_resolution: GraphResolution,
    ) -> tuple[str, ...]:
        ordered: list[str] = []
        if self._active_resolution is not None:
            ordered.extend(self._active_resolution.stop_order)
        ordered.extend(next_resolution.stop_order)
        ordered.extend(reversed(tuple(self._active_features)))
        return tuple(dict.fromkeys(ordered))

    async def _execute_stops(
        self,
        to_stop: set[str],
        stop_order: Sequence[str],
    ) -> list[str]:
        stopped: list[str] = []
        for feature_id in stop_order:
            if feature_id in to_stop and feature_id in self._active_features:
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
            missing = [
                capability.identifier
                for capability in feature.spec.requires
                if not self._registry.is_available(capability)
            ]
            if missing:
                self._startup_blocks[feature_id] = (
                    "Required capabilities failed to activate: "
                    + ", ".join(sorted(missing))
                )
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
        blocked.update(self._startup_blocks)
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

    async def _stage_feature(
        self,
        feature: Feature,
        config: object,
        scope: FeatureScope,
    ) -> list[StagedProvider]:
        staged_providers: list[StagedProvider] = []

        def collect_provider(
            capability: CapabilityKey[Any],
            implementation: object,
            _scope: FeatureScope,
        ) -> None:
            staged_providers.append((capability, implementation))

        context = DefaultFeatureContext(
            spec=feature.spec,
            scope=scope,
            resolver=self._registry.resolve,
            provider_registrar=collect_provider,
            event_bus=self._event_bus,
        )
        await feature.mount(context, config)
        self._validate_provider_bundle(feature.spec, staged_providers)
        return staged_providers

    def _validate_provider_bundle(
        self,
        spec: FeatureSpec,
        providers: Sequence[StagedProvider],
    ) -> None:
        declared = {capability.identifier for capability in spec.provides}
        actual = [capability.identifier for capability, _implementation in providers]
        if len(actual) != len(set(actual)):
            msg = f"Feature '{spec.feature_id}' registered a capability more than once"
            raise ValueError(msg)
        actual_set = set(actual)
        if declared != actual_set:
            missing = sorted(declared - actual_set)
            unexpected = sorted(actual_set - declared)
            msg = (
                f"Feature '{spec.feature_id}' provider bundle mismatch; "
                f"missing={missing}, unexpected={unexpected}"
            )
            raise ValueError(msg)

    async def _start_feature(
        self,
        feature: Feature,
        config: object,
    ) -> tuple[bool, str | None]:
        feature_id = feature.spec.feature_id
        self._feature_states[feature_id] = FeatureState.PREPARING
        scope = FeatureScope(owner_id=feature_id)
        try:
            providers = await self._stage_feature(feature, config, scope)
            self._registry.register_many(
                [
                    (capability, implementation, feature_id)
                    for capability, implementation in providers
                ],
                scope=scope,
            )
        except Exception as error:  # noqa: BLE001
            try:
                await scope.close()
            finally:
                self._feature_states[feature_id] = FeatureState.FAILED_START
            return False, str(error)

        scope.set_failure_callback(self._dispatch_runtime_failure)
        self._active_features[feature_id] = feature
        self._active_scopes[feature_id] = scope
        self._active_configs[feature_id] = config
        self._feature_states[feature_id] = FeatureState.ACTIVE
        return True, None

    async def _dispatch_runtime_failure(
        self,
        feature_id: str,
        task_name: str,
        error: BaseException,
    ) -> None:
        if self._failure_callback is None:
            await self.handle_runtime_failure(feature_id, task_name, error)
            return
        result = self._failure_callback(feature_id, task_name, error)
        if inspect.isawaitable(result):
            await result

    async def _run_health_check(self, feature: Feature) -> None:
        if isinstance(feature, HealthCheckableFeature) or (
            hasattr(feature, "health_check") and callable(feature.health_check)
        ):
            result = feature.health_check()
            if inspect.isawaitable(result):
                await result

    async def _cleanup_old_feature(
        self,
        old_feature: Feature | None,
        old_scope: FeatureScope | None,
    ) -> list[str]:
        cleanup_errors: list[str] = []
        if old_feature is not None:
            if isinstance(old_feature, QuiesceableFeature) or (
                hasattr(old_feature, "quiesce") and callable(old_feature.quiesce)
            ):
                try:
                    result = old_feature.quiesce()
                    if inspect.isawaitable(result):
                        await result
                except Exception as error:  # noqa: BLE001
                    cleanup_errors.append(f"Quiesce error: {error}")
            if isinstance(old_feature, DrainableFeature) or (
                hasattr(old_feature, "drain") and callable(old_feature.drain)
            ):
                try:
                    result = old_feature.drain()
                    if inspect.isawaitable(result):
                        await result
                except Exception as error:  # noqa: BLE001
                    cleanup_errors.append(f"Drain error: {error}")
        if old_scope is not None:
            try:
                await old_scope.close()
            except Exception as error:  # noqa: BLE001
                cleanup_errors.append(f"Scope cleanup error: {error}")
        return cleanup_errors

    async def swap_feature_transactional(
        self,
        feature: Feature,
        config: object,
    ) -> ReplacementReport:
        """Stage, atomically publish, and reconcile a feature replacement."""
        feature_id = feature.spec.feature_id
        old_feature = self._active_features.get(feature_id)
        old_scope = self._active_scopes.get(feature_id)
        if old_feature is None or old_scope is None:
            report = ReplacementReport(
                feature_id=feature_id,
                old_generation=0,
                new_generation=0,
                committed=False,
                rolled_back=True,
                status="rolled_back",
                error=f"Feature '{feature_id}' is not active",
            )
            self._replacement_reports[feature_id] = report
            return report

        old_capabilities = {
            capability.identifier for capability in old_feature.spec.provides
        }
        new_capabilities = {
            capability.identifier for capability in feature.spec.provides
        }
        if old_capabilities != new_capabilities:
            report = ReplacementReport(
                feature_id=feature_id,
                old_generation=0,
                new_generation=0,
                committed=False,
                rolled_back=True,
                status="rolled_back",
                error=(
                    "Hot replacement requires an unchanged provided-capability "
                    f"bundle; old={sorted(old_capabilities)}, "
                    f"new={sorted(new_capabilities)}"
                ),
            )
            self._replacement_reports[feature_id] = report
            return report

        old_tokens = [
            token
            for token in self._registry.active_capabilities().values()
            if token.owner_id == feature_id
        ]
        old_generation = max(
            (token.generation for token in old_tokens),
            default=0,
        )
        staged_scope = FeatureScope(owner_id=feature_id)
        try:
            staged_providers = await self._stage_feature(
                feature,
                config,
                staged_scope,
            )
            await self._run_health_check(feature)

            replacement_features = dict(self._known_features)
            replacement_features[feature_id] = feature
            replacement_specs = {
                item_id: item.spec for item_id, item in replacement_features.items()
            }
            desired_resolution = DependencyGraph(
                replacement_specs,
                provider_selections=self._provider_selections,
            ).resolve(self._desired_enabled)

            new_tokens = self._registry.replace_many(
                [
                    (capability, implementation, feature_id)
                    for capability, implementation in staged_providers
                ],
                scope=staged_scope,
            )
        except Exception as error:  # noqa: BLE001
            await staged_scope.close()
            report = ReplacementReport(
                feature_id=feature_id,
                old_generation=old_generation,
                new_generation=old_generation,
                committed=False,
                rolled_back=True,
                status="rolled_back",
                error=str(error),
            )
            self._replacement_reports[feature_id] = report
            return report

        staged_scope.set_failure_callback(self._dispatch_runtime_failure)
        self._active_features[feature_id] = feature
        self._active_scopes[feature_id] = staged_scope
        self._active_configs[feature_id] = config
        self._feature_states[feature_id] = FeatureState.ACTIVE
        self._known_features[feature_id] = feature
        self._desired_configs[feature_id] = config

        dependent_ids: set[str] = set()
        if self._active_resolution is not None:
            dependent_ids.update(
                self._active_resolution.get_transitive_dependents(feature_id)
            )
        dependent_ids.update(desired_resolution.get_transitive_dependents(feature_id))
        active_dependents = dependent_ids.intersection(self._active_features)
        previous_stop_order = (
            self._active_resolution.stop_order
            if self._active_resolution is not None
            else tuple(reversed(tuple(self._active_features)))
        )
        await self._execute_stops(active_dependents, previous_stop_order)

        consumer_errors: list[str] = []
        if active_dependents:
            self._startup_blocks = {}
            _started, start_errors = await self._execute_starts(
                desired_resolution.start_order,
                active_dependents,
                replacement_features,
                self._desired_configs,
            )
            consumer_errors.extend(
                f"{item_id}: {message}"
                for item_id, message in sorted(start_errors.items())
            )
            consumer_errors.extend(
                f"{item_id}: {message}"
                for item_id, message in sorted(self._startup_blocks.items())
            )

        cleanup_errors = await self._cleanup_old_feature(old_feature, old_scope)
        self._commit_active_resolution()
        new_generation = max(
            (token.generation for token in new_tokens),
            default=old_generation,
        )
        status = "degraded" if cleanup_errors or consumer_errors else "committed"
        report = ReplacementReport(
            feature_id=feature_id,
            old_generation=old_generation,
            new_generation=new_generation,
            committed=True,
            rolled_back=False,
            cleanup_errors=tuple(cleanup_errors),
            consumer_errors=tuple(consumer_errors),
            status=status,
        )
        self._replacement_reports[feature_id] = report
        return report

    async def handle_runtime_failure(
        self,
        feature_id: str,
        task_name: str,
        error: BaseException,
    ) -> None:
        """Remove a failed owner and reconcile required and optional consumers."""
        if feature_id not in self._active_features:
            return
        desired_enabled = set(self._desired_enabled or self._active_features)
        desired_configs = dict(self._desired_configs or self._active_configs)
        provider_selections = dict(self._provider_selections)
        known_features = dict(self._known_features or self._active_features)

        recovery_enabled = desired_enabled - {feature_id}
        recovery_selections = {
            capability: provider
            for capability, provider in provider_selections.items()
            if provider != feature_id
        }
        await self.reconcile(
            known_features,
            recovery_enabled,
            configs=desired_configs,
            provider_selections=recovery_selections,
        )

        self._desired_enabled = desired_enabled
        self._desired_configs = desired_configs
        self._provider_selections = provider_selections
        self._known_features = known_features
        self._feature_states[feature_id] = FeatureState.FAILED_RUNTIME
        self._runtime_failures[feature_id] = (
            f"Task '{task_name}' failed: {type(error).__name__}: {error}"
        )
        if self._last_report is not None:
            self._last_report = ReconciliationReport(
                started=self._last_report.started,
                stopped=self._last_report.stopped,
                active_features=self._last_report.active_features,
                blocked_features=self._last_report.blocked_features,
                feature_states=dict(self._feature_states),
                errors=self._last_report.errors,
            )

    async def _stop_feature(self, feature_id: str) -> None:
        self._feature_states[feature_id] = FeatureState.STOPPING
        scope = self._active_scopes.pop(feature_id, None)
        self._active_features.pop(feature_id, None)
        self._active_configs.pop(feature_id, None)
        if scope is not None:
            await scope.close()
        self._feature_states[feature_id] = FeatureState.STOPPED

    def _commit_active_resolution(self) -> None:
        if not self._active_features:
            self._active_resolution = GraphResolution(
                eligible_features=(),
                start_order=(),
                stop_order=(),
                blocked_features={},
                provider_map={},
            )
            return
        active_specs = {
            feature_id: feature.spec
            for feature_id, feature in self._active_features.items()
        }
        self._active_resolution = DependencyGraph(active_specs).resolve(
            self._active_features
        )

    async def stop_all(self) -> None:
        """Stop all active features in dependency-safe order."""
        stop_order = (
            self._active_resolution.stop_order
            if self._active_resolution is not None
            else tuple(reversed(tuple(self._active_features)))
        )
        await self._execute_stops(set(self._active_features), stop_order)
        self._commit_active_resolution()
