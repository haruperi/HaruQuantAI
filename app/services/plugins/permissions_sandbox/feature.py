"""Lifecycle mount for the plugin permissions sandbox capability."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.plugins.capabilities import SANDBOX_PERMISSIONS_CAPABILITY
from app.services.plugins.permissions_sandbox.config import SandboxPermissionsConfig
from app.services.plugins.permissions_sandbox.manifest import SPEC
from app.services.plugins.permissions_sandbox.plugin_permissions_sandbox import (
    PluginPermissionsSandboxService,
)

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class PluginPermissionsSandboxFeature:
    """Composable provider for the isolated plugin sandbox boundary."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        self.spec = spec
        self._service: PluginPermissionsSandboxService | None = None

    @property
    def service(self) -> PluginPermissionsSandboxService | None:
        """Return the active sandbox service, if mounted."""
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Validate all configuration before publishing the scoped provider."""
        raw = config if isinstance(config, dict) else None
        parsed = SandboxPermissionsConfig.from_dict(raw)
        service = PluginPermissionsSandboxService(parsed)
        context.register_callback(service.clear)
        context.provide(SANDBOX_PERMISSIONS_CAPABILITY, service)
        self._service = service


def feature() -> PluginPermissionsSandboxFeature:
    """Create the discovery entry-point feature instance.

    Returns:
        New unmounted feature instance.
    """
    return PluginPermissionsSandboxFeature()
