"""Composition engine coordinating configuration, discovery, and reconciliation."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from app.composition.config import (
    AppConfig,
    FeatureConfig,
    load_config_from_file,
    load_config_from_toml_string,
)
from app.composition.discovery import DiscoveryResult, FeatureDiscoverer
from app.composition.readiness import check_profile_readiness
from app.contracts.events.system import (
    ConfigurationReloadedEvent,
    FeatureReconfiguredEvent,
    FeatureRuntimeFailedEvent,
)
from app.kernel.events import EventBus
from app.kernel.feature import FeatureState
from app.kernel.reconciler import Reconciler, ReconciliationReport
from app.kernel.registry import ServiceRegistry
from app.kernel.replacement import ReplacementReport


@dataclass(frozen=True, slots=True)
class RuntimeStatus:
    """Snapshot of runtime readiness, features, capabilities, and degradation."""

    profile: str
    is_ready: bool
    missing_profile_capabilities: tuple[str, ...]
    active_features: tuple[str, ...]
    active_capabilities: tuple[str, ...]
    feature_states: dict[str, FeatureState]
    blocked_features: dict[str, str] = field(default_factory=dict)
    package_dependency_errors: dict[str, str] = field(default_factory=dict)
    capability_dependency_errors: dict[str, str] = field(default_factory=dict)
    runtime_failures: dict[str, str] = field(default_factory=dict)
    replacement_reports: dict[str, ReplacementReport] = field(default_factory=dict)
    cleanup_errors: dict[str, tuple[str, ...]] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)


class CompositionEngine:
    """Serialize composition mutations and expose committed runtime state."""

    def __init__(
        self,
        registry: ServiceRegistry | None = None,
        discoverer: FeatureDiscoverer | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the composition engine."""
        self._registry = registry or ServiceRegistry()
        self._discoverer = discoverer or FeatureDiscoverer()
        self._event_bus = event_bus or EventBus()
        self._mutation_lock = asyncio.Lock()
        self._reconciler = Reconciler(
            registry=self._registry,
            event_bus=self._event_bus,
            failure_callback=self._on_feature_runtime_failed,
        )
        self._config = AppConfig()
        self._last_discovery: DiscoveryResult | None = None
        self._last_report: ReconciliationReport | None = None

    async def _on_feature_runtime_failed(
        self,
        feature_id: str,
        task_name: str,
        error: BaseException,
    ) -> None:
        """Serialize runtime-failure reconciliation and publish its event."""
        async with self._mutation_lock:
            await self._reconciler.handle_runtime_failure(
                feature_id,
                task_name,
                error,
            )
            self._last_report = self._reconciler.last_report
        await self._event_bus.publish(
            FeatureRuntimeFailedEvent(
                feature_id=feature_id,
                task_name=task_name,
                error_message=str(error),
                timestamp=datetime.now(UTC),
            )
        )

    @property
    def event_bus(self) -> EventBus:
        """Return the shared event bus."""
        return self._event_bus

    @property
    def registry(self) -> ServiceRegistry:
        """Return the capability registry."""
        return self._registry

    @property
    def discoverer(self) -> FeatureDiscoverer:
        """Return the feature discoverer."""
        return self._discoverer

    @property
    def reconciler(self) -> Reconciler:
        """Return the feature reconciler."""
        return self._reconciler

    @property
    def config(self) -> AppConfig:
        """Return the last successfully committed configuration."""
        return self._config

    async def load_and_reconcile_toml(
        self,
        toml_content: str,
    ) -> ReconciliationReport:
        """Parse TOML and reconcile it atomically."""
        return await self.reconcile_with_config(
            load_config_from_toml_string(toml_content)
        )

    async def load_and_reconcile_file(
        self,
        config_path: str | Path,
    ) -> ReconciliationReport:
        """Load a TOML file and reconcile it atomically."""
        return await self.reconcile_with_config(load_config_from_file(config_path))

    async def _reconcile_unlocked(
        self,
        config: AppConfig,
    ) -> ReconciliationReport:
        discovery = self._discoverer.discover()
        enabled_ids = [
            feature_id
            for feature_id in config.features
            if config.is_feature_enabled(feature_id)
        ]
        feature_configs = {
            feature_id: config.get_feature_config(feature_id)
            for feature_id in enabled_ids
        }
        report = await self._reconciler.reconcile(
            discovered_features=discovery.discovered,
            enabled_feature_ids=enabled_ids,
            configs=feature_configs,
            provider_selections=config.provider_selections,
        )
        self._config = config
        self._last_discovery = discovery
        self._last_report = report
        return report

    async def reconcile_with_config(
        self,
        config: AppConfig,
    ) -> ReconciliationReport:
        """Serialize and commit one configuration reconciliation."""
        async with self._mutation_lock:
            return await self._reconcile_unlocked(config)

    async def hot_reload_config(
        self,
        new_config: AppConfig,
    ) -> ReconciliationReport:
        """Reconcile a new configuration and emit a reload event."""
        async with self._mutation_lock:
            report = await self._reconcile_unlocked(new_config)
        modified = tuple(sorted(set(report.started) | set(report.stopped)))
        await self._event_bus.publish(
            ConfigurationReloadedEvent(
                profile=self._config.profile,
                modified_features=modified,
                timestamp=datetime.now(UTC),
            )
        )
        return report

    async def replace_feature_transactional(
        self,
        feature_id: str,
        new_config: object | None = None,
    ) -> tuple[bool, str | None]:
        """Replace a feature and return a compatibility success tuple."""
        report = await self.replace_feature_transactional_detailed(
            feature_id,
            new_config=new_config,
        )
        errors = [
            message
            for message in (
                report.error,
                *report.consumer_errors,
                *report.cleanup_errors,
            )
            if message
        ]
        return report.committed, "; ".join(errors) if errors else None

    async def replace_feature_transactional_detailed(
        self,
        feature_id: str,
        new_config: object | None = None,
    ) -> ReplacementReport:
        """Serialize a staged feature replacement and return full diagnostics."""
        async with self._mutation_lock:
            discovery = self._discoverer.discover()
            feature = discovery.discovered.get(feature_id)
            if feature is None:
                return ReplacementReport(
                    feature_id=feature_id,
                    old_generation=0,
                    new_generation=0,
                    committed=False,
                    rolled_back=True,
                    status="rolled_back",
                    error=f"Feature '{feature_id}' not found in discovery",
                )
            config = (
                new_config
                if new_config is not None
                else self._config.get_feature_config(feature_id)
            )
            report = await self._reconciler.swap_feature_transactional(
                feature,
                config,
            )
            self._last_discovery = discovery
            self._last_report = self._reconciler.last_report
            if report.committed and isinstance(config, dict):
                features = dict(self._config.features)
                previous = features.get(feature_id, FeatureConfig())
                features[feature_id] = FeatureConfig(
                    enabled=previous.enabled,
                    config=dict(config),
                )
                self._config = AppConfig(
                    profile=self._config.profile,
                    features=features,
                    provider_selections=dict(self._config.provider_selections),
                )

        if report.committed:
            await self._event_bus.publish(
                FeatureReconfiguredEvent(
                    feature_id=feature_id,
                    generation=report.new_generation,
                    timestamp=datetime.now(UTC),
                )
            )
        return report

    def get_status(self) -> RuntimeStatus:
        """Return the current committed runtime status."""
        active_capabilities = tuple(sorted(self._registry.active_capabilities()))
        is_ready, missing = check_profile_readiness(
            self._config.profile,
            active_capabilities,
        )

        package_errors: dict[str, str] = {}
        if self._last_discovery is not None:
            for feature_id in self._config.features:
                if not self._config.is_feature_enabled(feature_id):
                    continue
                if feature_id in self._last_discovery.failed_imports:
                    package_errors[feature_id] = self._last_discovery.failed_imports[
                        feature_id
                    ]
                elif feature_id in self._last_discovery.missing_targets:
                    package_errors[feature_id] = self._last_discovery.missing_targets[
                        feature_id
                    ]

        latest_report = self._reconciler.last_report or self._last_report
        blocked = (
            dict(latest_report.blocked_features) if latest_report is not None else {}
        )
        capability_errors = {
            feature_id: reason
            for feature_id, reason in blocked.items()
            if self._reconciler.feature_states.get(feature_id) == FeatureState.BLOCKED
        }
        runtime_failures = self._reconciler.runtime_failures
        replacement_reports = self._reconciler.replacement_reports
        cleanup_errors = {
            feature_id: report.cleanup_errors
            for feature_id, report in replacement_reports.items()
            if report.cleanup_errors
        }

        combined_errors = dict(package_errors)
        if latest_report is not None:
            combined_errors.update(latest_report.errors)
        combined_errors.update(runtime_failures)
        for feature_id, report in replacement_reports.items():
            if report.is_degraded:
                details = (*report.consumer_errors, *report.cleanup_errors)
                combined_errors[feature_id] = "; ".join(details)

        return RuntimeStatus(
            profile=self._config.profile,
            is_ready=is_ready,
            missing_profile_capabilities=missing,
            active_features=self._reconciler.active_features,
            active_capabilities=active_capabilities,
            feature_states=self._reconciler.feature_states,
            blocked_features=blocked,
            package_dependency_errors=package_errors,
            capability_dependency_errors=capability_errors,
            runtime_failures=runtime_failures,
            replacement_reports=replacement_reports,
            cleanup_errors=cleanup_errors,
            errors=combined_errors,
        )

    async def shutdown(self) -> None:
        """Serialize shutdown and release all lifecycle-owned resources."""
        async with self._mutation_lock:
            await self._reconciler.stop_all()
            self._registry.clear()
            self._event_bus.clear()
