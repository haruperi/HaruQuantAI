"""Lifecycle mount for the plugin analysis boundary capability."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.plugins.capabilities import (
    ISOLATE_ANALYSIS_CAPABILITY,
    SANDBOX_PERMISSIONS_CAPABILITY,
)
from app.services.plugins.analysis_boundary.config import IsolateAnalysisConfig
from app.services.plugins.analysis_boundary.manifest import SPEC
from app.services.plugins.analysis_boundary.plugin_analysis_boundary import (
    IsolateAnalysisService,
)

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class IsolateAnalysisFeature:
    """Composable provider for the isolated plugin analysis boundary."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature adapter.

        Args:
            spec: Feature specification declaring capabilities and config keys.
        """
        self.spec = spec
        self._service: IsolateAnalysisService | None = None

    @property
    def service(self) -> IsolateAnalysisService | None:
        """Return the active analysis service, if mounted.

        Returns:
            The service instance if mounted, else None.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Validate configuration and mount the analysis boundary capability.

        Args:
            context: FeatureContext providing service resolution and registration.
            config: Optional configuration dictionary or object.
        """
        raw = config if isinstance(config, dict) else None
        parsed = IsolateAnalysisConfig.from_dict(raw)
        sandbox = context.optional(SANDBOX_PERMISSIONS_CAPABILITY)
        service = IsolateAnalysisService(config=parsed, sandbox=sandbox)
        context.register_callback(service.clear)
        context.provide(ISOLATE_ANALYSIS_CAPABILITY, service)
        self._service = service

    async def unmount(self, context: FeatureContext) -> None:
        """Unmount and clean up resources.

        Args:
            context: FeatureContext associated with this unmount.
        """
        del context
        if self._service is not None:
            self._service.clear()
            self._service = None


def feature() -> IsolateAnalysisFeature:
    """Create the discovery entry-point feature instance.

    Returns:
        New unmounted feature instance.
    """
    return IsolateAnalysisFeature()
