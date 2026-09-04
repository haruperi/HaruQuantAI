"""Feature lifecycle mount for the account registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.workspace.capabilities import MANAGE_ACCOUNTS_CAPABILITY
from app.services.workspace.manage_accounts.accounts import AccountService
from app.services.workspace.manage_accounts.config import (
    ManageAccountsConfig,
    from_dict,
)
from app.services.workspace.manage_accounts.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class ManageAccountsFeature:
    """Composable feature package providing account operations."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature with its specification.

        Args:
            spec: Feature specification declaring the served capability.
        """
        self.spec = spec
        self._service: AccountService | None = None

    @property
    def service(self) -> AccountService | None:
        """Return the mounted service, or None before mount.

        Returns:
            Active account service if mounted, otherwise None.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the account service and provide its capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Mapping, ManageAccountsConfig, or None.

        Raises:
            ValueError: If configuration contains unknown keys.
            TypeError: If configuration has an unsupported type.
        """
        if config is None or isinstance(config, dict):
            parsed = from_dict(config)
        elif isinstance(config, ManageAccountsConfig):
            parsed = config
        else:
            message = "manage-accounts configuration must be a mapping or config"
            raise TypeError(message)
        service = AccountService(parsed)
        context.register_callback(service.close)
        context.provide(MANAGE_ACCOUNTS_CAPABILITY, service)
        self._service = service


def feature() -> ManageAccountsFeature:
    """Factory for discovery via entry points.

    Returns:
        New ManageAccountsFeature instance.
    """
    return ManageAccountsFeature()
