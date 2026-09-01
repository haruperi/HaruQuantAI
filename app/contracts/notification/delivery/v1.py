"""Notification delivery capability v1 contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class NotificationDeliveryResultV1:
    """Result of a notification delivery attempt."""

    channel: str
    status: str
    recipient_count: int = 1


class NotificationDeliveryCapabilityV1(Protocol):
    """Protocol for a notification delivery channel provider."""

    @property
    def channel(self) -> str:
        """Channel name."""
        ...

    @property
    def active(self) -> bool:
        """Whether this provider is currently active."""
        ...

    def send(
        self,
        title: str,
        text: str,
        html_body: str | None = None,
    ) -> NotificationDeliveryResultV1:
        """Send a notification message."""
        ...

    def close(self) -> None:
        """Close and release provider resources."""
        ...
