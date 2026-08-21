"""Composition engine coordinating configuration, discovery, and reconciliation."""

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from app.composition.config import (
    AppConfig,
    load_config_from_file,
    load_config_from_toml_string,
)
from app.composition.discovery import DiscoveryResult, FeatureDiscoverer
from app.composition.readiness import check_profile_readiness
from app.contracts.events.system import (
    ConfigurationReloadedEvent,
    FeatureReconfiguredEvent,
)
from app.kernel.events import EventBus
from app.kernel.feature import FeatureState
from app.kernel.reconciler import Reconciler, ReconciliationReport
from app.kernel.registry import ServiceRegistry


@dataclass(frozen=True, slots=True)
class RuntimeStatus:
    """Comprehensive snapshot of application runtime and capability status."""

    profile: str
    is_ready: bool
    missing_profile_capabilities: tuple[str, ...]
    active_features: tuple[str, ...]
    active_capabilities: tuple[str, ...]
    feature_states: dict[str, FeatureState]
    blocked_features: dict[str, str] = field(default_factory=dict)
    package_dependency_errors: dict[str, str] = field(default_factory=dict)
    capability_dependency_errors: dict[str, str] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)


class CompositionEngine:
    """Coordinate declarative configuration, discovery, and runtime reconciliation."""

    def __init__(
        self,
        registry: ServiceRegistry | None = None,
        discoverer: FeatureDiscoverer | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._registry = registry or ServiceRegistry()
        self._discoverer = discoverer or FeatureDiscoverer()
        self._event_bus = event_bus or EventBus()
        self._reconciler = Reconciler(self._registry, self._event_bus)
        self._config = AppConfig()
        self._last_discovery: DiscoveryResult | None = None
        self._last_report: ReconciliationReport | None = None
        self._reconcile_lock = asyncio.Lock()

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    @property
    def registry(self) -> ServiceRegistry:
        return self._registry

    @property
    def discoverer(self) -> FeatureDiscoverer:
        return self._discoverer

    @property
    def reconciler(self) -> Reconciler:
        return self._reconciler

    @property
    def config(self) -> AppConfig:
        return self._config

    async def load_and_reconcile_toml(self, toml_content: str) -> ReconciliationReport:
        """Parse TOML configuration and reconcile runtime state."""
        return await self.reconcile_with_config(load_config_from_toml_string(toml_content))

    async def load_and_reconcile_file(
        self,
        config_path: str | Path,
    ) -> ReconciliationReport:
        """Load configuration from a file and reconcile runtime state."""
        return await self.reconcile_with_config(load_config_from_file(config_path))

    async def reconcile_with_config(self, config: AppConfig) -> ReconciliationReport:
        """Reconcile runtime state against a parsed AppConfig serially."""
        async with self._reconcile_lock:
            discovery = self._discoverer.discover()
            enabled_ids = [
                f_id for f_id in config.features if config.is_feature_enabled(f_id)
            ]
            feature_configs = {
                f_id: config.get_feature_config(f_id) for f_id in enabled_ids
            }
            report = await self._reconciler.reconcile(
                discovered_features=discovery.discovered,
                enabled_feature_ids=enabled_ids,
                configs=feature_configs,
                provider_selection=config.capability_providers,
            )
            self._config = config
            self._last_discovery = discovery
            self._last_report = report
            return report

    async def hot_reload_config(self, new_config: AppConfig) -> ReconciliationReport:
        """Perform a live configuration reload and emit a lifecycle event."""
        report = await self.reconcile_with_config(new_config)
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
        """Replace a feature with a staged lifecycle-safe scope."""
        async with self._reconcile_lock:
            discovery = self._discoverer.discover()
            feature = discovery.discovered.get(feature_id)
            if feature is None:
                return False, f"Feature '{feature_id}' not found in discovery"

            config = (
                new_config
                if new_config is not None
                else self._config.get_feature_config(feature_id)
            )
            configs = {
                f_id: self._config.get_feature_config(f_id)
                for f_id in self._config.features
                if self._config.is_feature_enabled(f_id)
            }
            configs[feature_id] = config
            success, warning = await self._reconciler.swap_feature_transactional(
                feature,
                config,
                discovered_features=discovery.discovered,
                configs=configs,
                provider_selection=self._config.capability_providers,
            )
            if success:
                active_tokens = self._registry.active_capabilities()
                generation = max(
                    (
                        token.generation
                        for token in active_tokens.values()
                        if token.owner_id == feature_id
                    ),
                    default=1,
                )
                await self._event_bus.publish(
                    FeatureReconfiguredEvent(
                        feature_id=feature_id,
                        generation=generation,
                        timestamp=datetime.now(UTC),
                    )
                )
            return success, warning

    def get_status(self) -> RuntimeStatus:
        """Return full runtime readiness and diagnostic state."""
        active_caps = tuple(sorted(self._registry.active_capabilities()))
        is_ready, missing_caps = check_profile_readiness(self._config.profile, active_caps)

        package_errors: dict[str, str] = {}
        if self._last_discovery is not None:
            for f_id in self._config.features:
                if not self._config.is_feature_enabled(f_id):
                    continue
                if f_id in self._last_discovery.failed_imports:
                    package_errors[f_id] = self._last_discovery.failed_imports[f_id]
                elif f_id in self._last_discovery.missing_targets:
                    package_errors[f_id] = self._last_discovery.missing_targets[f_id]

        blocked_features = (
            dict(self._last_report.blocked_features) if self._last_report is not None else {}
        )
        capability_errors = {
            f_id: reason
            for f_id, reason in blocked_features.items()
            if self._reconciler.feature_states.get(f_id) == FeatureState.BLOCKED
        }
        combined_errors = dict(package_errors)
        if self._last_report is not None:
            combined_errors.update(self._last_report.errors)

        return RuntimeStatus(
            profile=self._config.profile,
            is_ready=is_ready,
            missing_profile_capabilities=missing_caps,
            active_features=self._reconciler.active_features,
            active_capabilities=active_caps,
            feature_states=self._reconciler.feature_states,
            blocked_features=blocked_features,
            package_dependency_errors=package_errors,
            capability_dependency_errors=capability_errors,
            errors=combined_errors,
        )

    async def shutdown(self) -> None:
        """Stop all active features and release runtime resources."""
        async with self._reconcile_lock:
            await self._reconciler.stop_all()
            self._registry.clear()
