"""Lifecycle mount for plugin development compatibility."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.plugins.capabilities import (
    DECLARE_MANIFESTS_CAPABILITY,
    MAINTAIN_COMPATIBILITY_CAPABILITY,
    REGISTER_CONTRIBUTIONS_CAPABILITY,
)
from app.services.plugins.development_compatibility import (
    plugin_development_compatibility,
)
from app.services.plugins.development_compatibility.config import (
    DevelopmentCompatibilityConfig,
)
from app.services.plugins.development_compatibility.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class DevelopmentCompatibilityFeature:
    """Composable provider for plugin conformance and compatibility policy."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature adapter.

        Args:
            spec: Immutable feature declaration.
        """
        self.spec = spec
        self._service: (
            plugin_development_compatibility.DevelopmentCompatibilityService | None
        ) = None

    @property
    def service(
        self,
    ) -> plugin_development_compatibility.DevelopmentCompatibilityService | None:
        """Return the active service, if mounted."""
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Resolve required public capabilities and publish this provider.

        Args:
            context: Lifecycle-owned feature context.
            config: Optional feature configuration mapping.
        """
        raw = config if isinstance(config, dict) else None
        parsed = DevelopmentCompatibilityConfig.from_dict(raw)
        manifests = context.require(DECLARE_MANIFESTS_CAPABILITY)
        contributions = context.require(REGISTER_CONTRIBUTIONS_CAPABILITY)
        service = plugin_development_compatibility.DevelopmentCompatibilityService(
            config=parsed,
            manifests=manifests,
            contributions=contributions,
        )
        context.register_callback(service.clear)
        context.provide(MAINTAIN_COMPATIBILITY_CAPABILITY, service)
        self._service = service

    async def unmount(self, context: FeatureContext) -> None:
        """Clear policy state on feature removal.

        Args:
            context: Lifecycle context for this feature.
        """
        del context
        if self._service is not None:
            self._service.clear()
            self._service = None


def feature() -> DevelopmentCompatibilityFeature:
    """Create the discovery entry-point feature instance.

    Returns:
        A new unmounted feature instance.
    """
    return DevelopmentCompatibilityFeature()
