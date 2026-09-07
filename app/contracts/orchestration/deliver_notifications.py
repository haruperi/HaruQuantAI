"""Focused public contract for governed notification delivery."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.contracts.common.models import JsonObject
    from app.contracts.orchestration.models import (
        NotificationChannelConfig,
        NotificationReceipt,
        NotificationTemplate,
    )


@runtime_checkable
class DeliverNotificationsCapability(Protocol):
    """Coordinate idempotent, policy-gated notification delivery."""

    async def deliver(
        self,
        *,
        delivery_id: str,
        channel: NotificationChannelConfig,
        template: NotificationTemplate,
        variables: JsonObject | None = None,
        title: str = "HaruQuantAI",
        master_enabled: bool = False,
    ) -> NotificationReceipt:
        """Return the durable receipt for one logical delivery."""
        ...
