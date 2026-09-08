"""Feature lifecycle mount for Secure Local Access."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.workspace.capabilities import (
    MANAGE_ACCOUNTS_CAPABILITY,
    SECURE_LOCAL_ACCESS_CAPABILITY,
)
from app.services.workspace.secure_local_access.config import (
    SecureLocalAccessConfig,
)
from app.services.workspace.secure_local_access.manifest import SPEC
from app.services.workspace.secure_local_access.secure_local_access import (
    SecureLocalAccessService,
)

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class SecureLocalAccessFeature:
    """Composable feature package providing secure local access and host protection."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature with its specification.

        Args:
            spec: Feature specification declaring the served capability.
        """
        self.spec = spec
        self._service: SecureLocalAccessService | None = None

    @property
    def service(self) -> SecureLocalAccessService | None:
        """Return the mounted service, or None before mount.

        Returns:
            Active SecureLocalAccessService if mounted, otherwise None.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the secure local access service and provide its capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Mapping, SecureLocalAccessConfig, or None.

        Raises:
            ValueError: If configuration contains unknown keys.
            TypeError: If configuration has an unsupported type.
        """
        if config is None or isinstance(config, dict):
            parsed = SecureLocalAccessConfig.from_dict(config)
        elif isinstance(config, SecureLocalAccessConfig):
            parsed = config
        else:
            msg = "secure-local-access configuration must be a mapping or config"
            raise TypeError(msg)

        manage_accounts = context.require(MANAGE_ACCOUNTS_CAPABILITY)
        service = SecureLocalAccessService(
            config=parsed,
            manage_accounts=manage_accounts,
        )
        context.register_callback(service.close)
        context.provide(SECURE_LOCAL_ACCESS_CAPABILITY, service)
        self._service = service


def feature() -> SecureLocalAccessFeature:
    """Factory for discovery via entry points.

    Returns:
        New SecureLocalAccessFeature instance.
    """
    return SecureLocalAccessFeature()


__all__ = [
    "SecureLocalAccessFeature",
    "feature",
]
