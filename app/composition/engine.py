"""Composition engine coordinating configuration, discovery, and reconciliation."""

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
    FeatureRuntimeFailedEvent,
)
from app.kernel.events import EventBus
from app.kernel.feature import FeatureState
from app.kernel.reconciler import Reconciler, ReconciliationReport
from app.kernel.registry import ServiceRegistry
from app.kernel.replacement import ReplacementReport


@dataclass(frozen=True, slots=True)
class RuntimeStatus:
    """Comprehensive snapshot of application runtime and capability status.

    Attributes:
        profile: Active deployment profile.
        is_ready: Whether the profile satisfies all required capabilities.
        missing_profile_capabilities: Capabilities required by profile but missing.
        active_features: Tuple of active feature IDs.
        active_capabilities: Tuple of active capability identifiers.
        feature_states: Snapshot map of all feature IDs to FeatureState.
        blocked_features: Diagnostic reason map for blocked features.
        package_dependency_errors: Features failing due to missing Python packages.
        capability_dependency_errors: Features blocked due to missing capabilities.
        errors: Combined diagnostic error map.
    """

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
    """Coordinates declarative configuration, discovery, and runtime reconciliation."""

    def __init__(
        self,
        registry: ServiceRegistry | None = None,
        discoverer: FeatureDiscoverer | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the composition engine.

        Args:
            registry: Optional custom ServiceRegistry.
            discoverer: Optional custom FeatureDiscoverer.
            event_bus: Optional shared EventBus.
        """
        self._registry = registry or ServiceRegistry()
        self._discoverer = discoverer or FeatureDiscoverer()
        self._event_bus = event_bus or EventBus()
        self._reconciler = Reconciler(
            registry=self._registry,
            event_bus=self._event_bus,
            failure_callback=self._on_feature_runtime_failed,
        )
        self._config: AppConfig = AppConfig()
        self._last_discovery: DiscoveryResult | None = None
        self._last_report: ReconciliationReport | None = None

    async def _on_feature_runtime_failed(
        self,
        feature_id: str,
        task_name: str,
        exc: BaseException,
    ) -> None:
        """Publish FeatureRuntimeFailedEvent when a background task crashes.

        Args:
            feature_id: Failing feature ID.
            task_name: Diagnostic name of crashed task.
            exc: Exception that caused the failure.
        """
        await self._event_bus.publish(
            FeatureRuntimeFailedEvent(
                feature_id=feature_id,
                task_name=task_name,
                error_message=str(exc),
                timestamp=datetime.now(UTC),
            )
        )

    @property
    def event_bus(self) -> EventBus:
        """Return the shared event bus.

        Returns:
            Active EventBus instance.
        """
        return self._event_bus

    @property
    def registry(self) -> ServiceRegistry:
        """Return the underlying service registry.

        Returns:
            Active ServiceRegistry.
        """
        return self._registry

    @property
    def discoverer(self) -> FeatureDiscoverer:
        """Return the feature discoverer.

        Returns:
            FeatureDiscoverer instance.
        """
        return self._discoverer

    @property
    def reconciler(self) -> Reconciler:
        """Return the active reconciler.

        Returns:
            Reconciler instance.
        """
        return self._reconciler

    @property
    def config(self) -> AppConfig:
        """Return the current application configuration.

        Returns:
            AppConfig instance.
        """
        return self._config

    async def load_and_reconcile_toml(
        self,
        toml_content: str,
    ) -> ReconciliationReport:
        """Parse TOML configuration content and reconcile runtime state.

        Args:
            toml_content: Raw TOML configuration string.

        Returns:
            ReconciliationReport detailing execution results.
        """
        config = load_config_from_toml_string(toml_content)
        return await self.reconcile_with_config(config)

    async def load_and_reconcile_file(
        self,
        config_path: str | Path,
    ) -> ReconciliationReport:
        """Load configuration from a file and reconcile runtime state.

        Args:
            config_path: Path to TOML configuration file.

        Returns:
            ReconciliationReport detailing execution results.
        """
        config = load_config_from_file(config_path)
        return await self.reconcile_with_config(config)

    async def reconcile_with_config(
        self,
        config: AppConfig,
    ) -> ReconciliationReport:
        """Reconcile runtime state against a parsed AppConfig.

        Args:
            config: Target AppConfig.

        Returns:
            ReconciliationReport.
        """
        self._config = config
        discovery: DiscoveryResult = self._discoverer.discover()
        self._last_discovery = discovery

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
            provider_selections=config.provider_selections,
        )
        self._last_report = report
        return report

    async def hot_reload_config(
        self,
        new_config: AppConfig,
    ) -> ReconciliationReport:
        """Perform a live configuration hot reload and emit lifecycle events.

        Args:
            new_config: Updated AppConfig instance.

        Returns:
            ReconciliationReport detailing changes.
        """
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
        """Perform a zero-downtime transactional feature swap using shadow scopes.

        Args:
            feature_id: Identifier of the feature to replace.
            new_config: Optional updated configuration object.

        Returns:
            Tuple of (success boolean, optional error message).
        """
        report = await self.replace_feature_transactional_detailed(
            feature_id, new_config=new_config
        )
        err = report.error
        if not err and report.cleanup_errors:
            err = "; ".join(report.cleanup_errors)
        return report.committed, err

    async def replace_feature_transactional_detailed(
        self,
        feature_id: str,
        new_config: object | None = None,
    ) -> ReplacementReport:
        """Perform transactional swap returning detailed ReplacementReport.

        Args:
            feature_id: Identifier of the feature to replace.
            new_config: Optional updated configuration object.

        Returns:
            ReplacementReport detailing commit, rollback, generation, and cleanup.
        """
        discovery = self._discoverer.discover()
        feature = discovery.discovered.get(feature_id)
        if feature is None:
            return ReplacementReport(
                feature_id=feature_id,
                old_generation=0,
                new_generation=0,
                committed=False,
                rolled_back=False,
                status="rolled_back",
                error=f"Feature '{feature_id}' not found in discovery",
            )

        cfg = (
            new_config
            if new_config is not None
            else self._config.get_feature_config(feature_id)
        )
        report = await self._reconciler.swap_feature_transactional(feature, cfg)
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
        """Calculate and return full runtime readiness and state snapshot.

        Returns:
            RuntimeStatus snapshot.
        """
        active_caps = tuple(sorted(self._registry.active_capabilities().keys()))
        is_ready, missing_caps = check_profile_readiness(
            self._config.profile,
            active_caps,
        )

        package_errors: dict[str, str] = {}
        if self._last_discovery is not None:
            for f_id in self._config.features:
                if not self._config.is_feature_enabled(f_id):
                    continue
                if f_id in self._last_discovery.failed_imports:
                    package_errors[f_id] = self._last_discovery.failed_imports[f_id]
                elif f_id in self._last_discovery.missing_targets:
                    package_errors[f_id] = self._last_discovery.missing_targets[f_id]

        capability_errors: dict[str, str] = {}
        blocked_features: dict[str, str] = {}
        for f_id, state in self._reconciler.feature_states.items():
            if state == FeatureState.BLOCKED:
                reason = "Blocked on missing required runtime capabilities"
                capability_errors[f_id] = reason
                blocked_features[f_id] = reason

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
        """Stop all active features and release all runtime resources."""
        await self._reconciler.stop_all()
        self._registry.clear()
