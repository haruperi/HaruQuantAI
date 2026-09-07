"""SMS notification delivery provider factory."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from app.contracts.notification.delivery.v1 import (
    NotificationDeliveryCapabilityV1,
    NotificationDeliveryResultV1,
)
from app.services.plugins.providers._notification import (
    NotificationBackend,
    recipient_count,
    validate_backend,
)

if TYPE_CHECKING:
    from app.kernel.effects import EffectScope
    from app.kernel.identifiers import CapabilityId


class _SMSDeliveryAdapter:
    """Adapts internal SMSNotifier to NotificationDeliveryCapabilityV1 protocol."""

    def __init__(self, notifier: NotificationBackend) -> None:
        self._notifier = notifier
        self._active = True

    @property
    def channel(self) -> str:
        return "sms"

    @property
    def active(self) -> bool:
        return self._active and self._notifier.active

    def send(
        self,
        title: str,
        text: str,
        html_body: str | None = None,
    ) -> NotificationDeliveryResultV1:
        if not self._active:
            msg = "SMS delivery transport is closed"
            raise RuntimeError(msg)
        result = self._notifier.send(title, text, html_body)
        return NotificationDeliveryResultV1(
            channel="sms",
            status="accepted",
            recipient_count=recipient_count(result),
        )

    def close(self) -> None:
        self._active = False


def create_provider(
    *,
    dependencies: Mapping[CapabilityId, object],
    config: Mapping[str, object],
    scope: EffectScope,
) -> NotificationDeliveryCapabilityV1:
    """Create scoped SMS notification delivery provider instance.

    Args:
        dependencies: Must be empty.
        config: Must contain only 'configuration' with a notification backend.
        scope: EffectScope managing provider lifecycle.

    Returns:
        NotificationDeliveryCapabilityV1 instance.

    Raises:
        ValueError: If config or dependencies are invalid.
    """
    if dependencies or set(config.keys()) != {"configuration"}:
        msg = "sms notification provider requires only 'configuration'"
        raise ValueError(msg)

    notifier = validate_backend(config["configuration"], "sms")
    adapter = _SMSDeliveryAdapter(notifier)
    scope.callback(adapter.close)
    return adapter


__all__ = ("create_provider",)
