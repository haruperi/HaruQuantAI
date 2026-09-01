"""Lifecycle mount for the plugin result panels capability."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.plugins.capabilities import (
    REGISTER_CONTRIBUTIONS_CAPABILITY,
    RENDER_RESULT_PANELS_CAPABILITY,
)
from app.services.plugins.result_panels.config import ResultPanelsConfig
from app.services.plugins.result_panels.manifest import SPEC
from app.services.plugins.result_panels.plugin_result_panels import (
    ResultPanelsService,
)

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class ResultPanelsFeature:
    """Composable provider for sandboxed plugin result panels."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature adapter.

        Args:
            spec: Feature specification declaring capabilities and config keys.
        """
        self.spec = spec
        self._service: ResultPanelsService | None = None

    @property
    def service(self) -> ResultPanelsService | None:
        """Return the active result panels service, if mounted.

        Returns:
            The service instance if mounted, else None.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Validate configuration and mount the result panels capability.

        Args:
            context: FeatureContext providing service resolution and registration.
            config: Optional configuration dictionary or object.
        """
        raw = config if isinstance(config, dict) else None
        parsed = ResultPanelsConfig.from_dict(raw)
        contributions = context.optional(REGISTER_CONTRIBUTIONS_CAPABILITY)
        service = ResultPanelsService(
            config=parsed, contributions_service=contributions
        )
        context.register_callback(service.clear)
        context.provide(RENDER_RESULT_PANELS_CAPABILITY, service)
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


def feature() -> ResultPanelsFeature:
    """Create the discovery entry-point feature instance.

    Returns:
        New unmounted feature instance.
    """
    return ResultPanelsFeature()
