"""Feature lifecycle mount for the market-data reference browser."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import BROWSE_REFERENCE_CAPABILITY
from app.services.data.browse_reference.browse_reference import (
    BrowseReferenceService,
)
from app.services.data.browse_reference.config import (
    BrowseReferenceConfig,
    from_dict,
)
from app.services.data.browse_reference.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class BrowseReferenceFeature:
    """Composable feature package providing market reference operations."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature with its specification.

        Args:
            spec: Feature specification declaring the served capability.
        """
        self.spec = spec
        self._service: BrowseReferenceService | None = None

    @property
    def service(self) -> BrowseReferenceService | None:
        """Return the mounted service, or None before mount.

        Returns:
            Active browse reference service if mounted, otherwise None.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the browse reference service and provide its capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Mapping, BrowseReferenceConfig, or None.

        Raises:
            ValueError: If configuration contains unknown keys.
            TypeError: If configuration has an unsupported type.
        """
        if config is None or isinstance(config, dict):
            parsed = from_dict(config)
        elif isinstance(config, BrowseReferenceConfig):
            parsed = config
        else:
            message = "browse-reference configuration must be a mapping or config"
            raise TypeError(message)

        service = BrowseReferenceService(config=parsed)
        self._service = service
        context.register_callback(service.close)
        context.provide(BROWSE_REFERENCE_CAPABILITY, service)


def feature() -> BrowseReferenceFeature:
    """Factory for discovery via entry points.

    Returns:
        New BrowseReferenceFeature instance.
    """
    return BrowseReferenceFeature()
