"""Notification provider capability keys."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.notification.delivery.v1 import NotificationDeliveryCapabilityV1

NOTIFICATION_DELIVERY_CAPABILITY: CapabilityKey[NotificationDeliveryCapabilityV1] = (
    CapabilityKey(name="notification.delivery", major=1)
)
