"""Feature lifecycle adapter and factory for test greeting."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.test.greeting import GREETING_SERVICE
from app.services.test.greeting.config import GreetingConfig
from app.services.test.greeting.greeting import GreetingServiceImpl
from app.services.test.greeting.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class GreetingFeature:
    """Composable feature adapter for test greeting."""

    spec: FeatureSpec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Register capability provider in feature scope.

        Args:
            context: FeatureContext for registering capabilities and managed resources.
            config: Raw configuration object or mapping for this feature.
        """
        raw_config = config if isinstance(config, dict) else {}
        parsed = GreetingConfig.from_dict(raw_config)
        service = GreetingServiceImpl(
            default_salutation=parsed.default_salutation,
            max_name_length=parsed.max_name_length,
        )
        context.provide(GREETING_SERVICE, service)


def create_feature() -> GreetingFeature:
    """Zero-argument entry-point factory for test greeting feature.

    Returns:
        An instance of GreetingFeature.
    """
    return GreetingFeature()
