"""Lifecycle adapter for governed notification delivery."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.notification.capabilities import NOTIFICATION_DELIVERY_CAPABILITY
from app.contracts.orchestration.capabilities import (
    DELIVER_NOTIFICATIONS_CAPABILITY,
    MANAGE_JOBS_CAPABILITY,
)
from app.contracts.workspace.capabilities import MANAGE_ACCOUNTS_CAPABILITY
from app.services.orchestration.deliver_notifications._persistence import (
    NotificationStore,
)
from app.services.orchestration.deliver_notifications.config import (
    DeliverNotificationsConfig,
    from_dict,
)
from app.services.orchestration.deliver_notifications.deliver_notifications import (
    DeliverNotificationsService,
)
from app.services.orchestration.deliver_notifications.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class DeliverNotificationsFeature:
    """Mount one lifecycle-owned notification coordinator."""

    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Build and register the configured coordinator.

        Args:
            context: Lifecycle-owned feature context.
            config: Mapping, parsed configuration, or None.

        Raises:
            TypeError: If config has an unsupported type.
            ValueError: If config contains invalid values.
        """
        if config is None or isinstance(config, dict):
            parsed = from_dict(config)
        elif isinstance(config, DeliverNotificationsConfig):
            parsed = config
        else:
            raise TypeError(
                "deliver-notifications config must be a mapping or "
                "DeliverNotificationsConfig"
            )
        context.require(MANAGE_JOBS_CAPABILITY)
        context.require(MANAGE_ACCOUNTS_CAPABILITY)
        provider = context.optional(NOTIFICATION_DELIVERY_CAPABILITY)
        service = DeliverNotificationsService(
            NotificationStore(parsed.database_path), provider
        )
        context.register_callback(service.close)
        context.provide(DELIVER_NOTIFICATIONS_CAPABILITY, service)


def feature() -> DeliverNotificationsFeature:
    """Return a new notification feature instance.

    Returns:
        New feature adapter.
    """
    return DeliverNotificationsFeature()
