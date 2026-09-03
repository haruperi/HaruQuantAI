"""Feature lifecycle mount for the serve-api-events transport."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.interfaces.capabilities import SERVE_API_EVENTS_CAPABILITY
from app.services.interfaces.serve_api_events.config import ServeApiEventsConfig
from app.services.interfaces.serve_api_events.manifest import SPEC
from app.services.interfaces.serve_api_events.transport import ServeApiEventsTransport

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class ServeApiEventsFeature:
    """Composable feature package providing the API/event transport."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature with its specification.

        Args:
            spec: Feature specification declaring the served capability.
        """
        self.spec = spec
        self._transport: ServeApiEventsTransport | None = None

    @property
    def transport(self) -> ServeApiEventsTransport | None:
        """Return the mounted transport, or None before mount.

        Returns:
            Active transport instance if mounted, otherwise None.
        """
        return self._transport

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the transport and provide the serving capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Mapping, ServeApiEventsConfig, or None.

        Raises:
            ValueError: If configuration contains unknown or invalid keys.
            TypeError: If configuration has an unsupported type.
        """
        if config is None or isinstance(config, dict):
            parsed = ServeApiEventsConfig.from_dict(config)
        elif isinstance(config, ServeApiEventsConfig):
            parsed = config
        else:
            raise TypeError(
                "serve-api-events configuration must be a mapping, "
                "ServeApiEventsConfig, or None"
            )
        transport = ServeApiEventsTransport(parsed)
        context.register_callback(transport.close)
        context.provide(SERVE_API_EVENTS_CAPABILITY, transport)
        self._transport = transport


def feature() -> ServeApiEventsFeature:
    """Factory for discovery via entry points.

    Returns:
        New ServeApiEventsFeature instance.
    """
    return ServeApiEventsFeature()
