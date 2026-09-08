"""Feature lifecycle mount for the account identity gateway."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.composition.logging import get_logger
from app.contracts.interfaces.capabilities import OPERATE_IDENTITY_CAPABILITY
from app.contracts.workspace.capabilities import MANAGE_ACCOUNTS_CAPABILITY
from app.services.interfaces.operate_identity.config import (
    OperateIdentityConfig,
    from_dict,
)
from app.services.interfaces.operate_identity.gateway import IdentityGateway
from app.services.interfaces.operate_identity.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec

logger = get_logger(__name__)


class OperateIdentityFeature:
    """Composable feature package providing identity operations."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature with its specification.

        Args:
            spec: Feature specification declaring the served capability.
        """
        self.spec = spec
        self._gateway: IdentityGateway | None = None

    @property
    def gateway(self) -> IdentityGateway | None:
        """Return the mounted gateway, or None before mount.

        Returns:
            Active gateway instance if mounted, otherwise None.
        """
        return self._gateway

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the gateway against the resolved Workspace provider.

        Args:
            context: Scoped runtime context for this feature.
            config: Mapping, OperateIdentityConfig, or None.

        Raises:
            ValueError: If configuration contains unknown keys.
            TypeError: If configuration has an unsupported type.
            CapabilityUnavailableError: If the required Workspace
                capability has no active provider.
        """
        logger.info(
            "Mounting OperateIdentityFeature",
            capability=OPERATE_IDENTITY_CAPABILITY.identifier,
        )
        if config is None or isinstance(config, dict):
            parsed = from_dict(config)
        elif isinstance(config, OperateIdentityConfig):
            parsed = config
        else:
            message = (
                "operate-identity configuration must be a mapping, "
                "OperateIdentityConfig, or None"
            )
            raise TypeError(message)
        provider = context.require(MANAGE_ACCOUNTS_CAPABILITY)
        gateway = IdentityGateway(provider, parsed)
        context.register_callback(gateway.close)
        context.provide(OPERATE_IDENTITY_CAPABILITY, gateway)
        self._gateway = gateway
        logger.info(
            "OperateIdentityFeature mounted successfully",
            capability=OPERATE_IDENTITY_CAPABILITY.identifier,
        )


def feature() -> OperateIdentityFeature:
    """Factory for discovery via entry points.

    Returns:
        New OperateIdentityFeature instance.
    """
    return OperateIdentityFeature()
