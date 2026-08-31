"""Notification delivery capability v1 contract.

Traces to: P10-T02, Pilot A - Notifications, Gate G10
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

CAPABILITY_ID = "notification.delivery.v1"


@dataclass(frozen=True, slots=True)
class NotificationDeliveryResultV1:
    """Immutable result returned after delivering a notification payload."""

    channel: str
    status: Literal["accepted"]
    recipient_count: int | None = None


@runtime_checkable
class NotificationDeliveryCapabilityV1(Protocol):
    """Effectful protocol for delivering notifications to external transports."""

    @property
    def channel(self) -> str:
        """Canonical delivery channel identifier (e.g. email, sms, telegram)."""
        ...

    @property
    def active(self) -> bool:
        """Whether the delivery transport is active and configured."""
        ...

    def send(
        self,
        title: str,
        text: str,
        html_body: str | None = None,
    ) -> NotificationDeliveryResultV1:
        """Deliver a message payload through the transport.

        Args:
            title: Notification headline or subject line.
            text: Plaintext body of the notification.
            html_body: Optional rich HTML formatted body.

        Returns:
            NotificationDeliveryResultV1 with accepted status and metadata.
        """
        ...

    def close(self) -> None:
        """Release underlying transport sockets, sessions, or subprocess resources."""
        ...


__all__ = (
    "CAPABILITY_ID",
    "NotificationDeliveryCapabilityV1",
    "NotificationDeliveryResultV1",
)
