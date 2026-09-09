"""Lifecycle adapter for Mandate Enforcement."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.composition.logging import get_logger
from app.contracts.agentic.capabilities import ENFORCE_MANDATE_CAPABILITY
from app.contracts.workspace.capabilities import (
    ADMINISTER_SETTINGS_CAPABILITY,
    MANAGE_ACCOUNTS_CAPABILITY,
)
from app.services.agentic.enforce_mandate.config import (
    EnforceMandateConfig,
    from_dict,
)
from app.services.agentic.enforce_mandate.enforce_mandate import (
    EnforceMandateService,
)
from app.services.agentic.enforce_mandate.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

_LOGGER = get_logger("agentic.enforce_mandate.feature")


class EnforceMandateFeature:
    """Mount one lifecycle-owned mandate enforcement coordinator."""

    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Build and register the mandate enforcement service.

        Args:
            context: Lifecycle-owned feature context.
            config: Mapping, parsed configuration, or None.

        Raises:
            TypeError: If config has an unsupported type.
            ValueError: If config contains invalid values.
        """
        if config is None or isinstance(config, dict):
            from_dict(config)
        elif isinstance(config, EnforceMandateConfig):
            pass
        else:
            msg = "enforce-mandate config must be a mapping or EnforceMandateConfig"
            raise TypeError(msg)

        accounts_port = context.require(MANAGE_ACCOUNTS_CAPABILITY)
        settings_port = context.require(ADMINISTER_SETTINGS_CAPABILITY)

        service = EnforceMandateService(
            accounts_port=accounts_port,
            settings_port=settings_port,
        )

        context.register_callback(service.close)
        context.provide(ENFORCE_MANDATE_CAPABILITY, service)
        _LOGGER.info("Mounted EnforceMandateFeature successfully")


def feature() -> EnforceMandateFeature:
    """Return a new mandate enforcement feature instance."""
    return EnforceMandateFeature()


def create_feature() -> EnforceMandateFeature:
    """Return a new mandate enforcement feature instance (canonical factory)."""
    return EnforceMandateFeature()


__all__ = ["EnforceMandateFeature", "create_feature", "feature"]
