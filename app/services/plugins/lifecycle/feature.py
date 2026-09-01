"""Lifecycle adapter for the transactional plugin lifecycle capability."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.contracts.plugins.capabilities import (
    DECLARE_MANIFESTS_CAPABILITY,
    MANAGE_LIFECYCLE_CAPABILITY,
)
from app.services.plugins.lifecycle.config import PluginLifecycleConfig
from app.services.plugins.lifecycle.manifest import SPEC
from app.services.plugins.lifecycle.plugin_lifecycle import PluginLifecycleService

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class PluginLifecycleFeature:
    """Composable feature that provides transactional plugin lifecycle changes."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature with its immutable specification.

        Args:
            spec: Feature declaration for this lifecycle provider.
        """
        self.spec = spec
        self._service: PluginLifecycleService | None = None

    @property
    def service(self) -> PluginLifecycleService | None:
        """Return the mounted service, if the feature is active."""
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Validate configuration and stage the lifecycle capability provider.

        Args:
            context: Scoped context used for required-capability validation and
                provision.
            config: Required raw lifecycle configuration mapping.
        """
        raw_config: dict[str, Any] | None = config if isinstance(config, dict) else None
        parsed_config = PluginLifecycleConfig.from_dict(raw_config)
        context.require(DECLARE_MANIFESTS_CAPABILITY)
        service = PluginLifecycleService(parsed_config)
        context.provide(MANAGE_LIFECYCLE_CAPABILITY, service)
        self._service = service


def feature() -> PluginLifecycleFeature:
    """Create the discovery entry-point feature instance.

    Returns:
        A new lifecycle feature instance.
    """
    return PluginLifecycleFeature()
