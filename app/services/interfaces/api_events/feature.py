"""Feature lifecycle mount implementation for HTTP and Event Contracts."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.contracts.interfaces.capabilities import SERVE_API_EVENTS_CAPABILITY
from app.services.interfaces.api_events.api_events import ApiEventsService
from app.services.interfaces.api_events.config import ApiEventsConfig
from app.services.interfaces.api_events.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class ApiEventsFeature:
    """Composable feature package providing HTTP and Event Contracts capabilities."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: ApiEventsService | None = None

    @property
    def service(self) -> ApiEventsService | None:
        """Return the underlying API events service instance if mounted.

        Returns:
            The API events service instance.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the serve-api-events capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.
        """
        raw_config: dict[str, Any] = config if isinstance(config, dict) else {}
        parsed_config = ApiEventsConfig.from_dict(raw_config)
        self._service = ApiEventsService(parsed_config)
        context.provide(SERVE_API_EVENTS_CAPABILITY, self._service)


def feature() -> ApiEventsFeature:
    """Factory function for discovery via entry points.

    Returns:
        New ApiEventsFeature instance.
    """
    return ApiEventsFeature()
