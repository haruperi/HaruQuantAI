"""Feature lifecycle for mandate enforcement."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.agentic.capabilities import MANDATE_CAPABILITY
from app.contracts.workspace.capabilities import ADMINISTER_SETTINGS_CAPABILITY, MANAGE_ACCOUNTS_CAPABILITY
from app.services.agentic.enforce_mandate.config import EnforceMandateConfig, from_dict
from app.services.agentic.enforce_mandate.enforce_mandate import MandateService
from app.services.agentic.enforce_mandate.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class EnforceMandateFeature:
    """Composable mandate-enforcement feature."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        self.spec = spec
        self._service: MandateService | None = None

    async def mount(self, context: FeatureContext, config: object) -> None:
        if config is None or isinstance(config, dict):
            from_dict(config)
        elif not isinstance(config, EnforceMandateConfig):
            raise TypeError("enforce-mandate configuration must be a mapping, EnforceMandateConfig, or None")
        service = MandateService(context.require(MANAGE_ACCOUNTS_CAPABILITY), context.require(ADMINISTER_SETTINGS_CAPABILITY))
        context.register_callback(service.close)
        context.provide(MANDATE_CAPABILITY, service)
        self._service = service


def feature() -> EnforceMandateFeature:
    """Return a fresh discovery instance."""
    return EnforceMandateFeature()
