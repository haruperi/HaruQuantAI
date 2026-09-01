"""Telegram notification delivery provider factory."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from app.contracts.notification.delivery.v1 import (
    NotificationDeliveryCapabilityV1,
    NotificationDeliveryResultV1,
)
from app.utils.notifications.telegram import TelegramConfig, TelegramNotifier

if TYPE_CHECKING:
    from app.kernel.effects import EffectScope
    from app.kernel.identifiers import CapabilityId


class _TelegramDeliveryAdapter:
    """Adapts internal TelegramNotifier to NotificationDeliveryCapabilityV1 protocol."""

    def __init__(self, notifier: TelegramNotifier) -> None:
        self._notifier = notifier
        self._active = True

    @property
    def channel(self) -> str:
        return "telegram"

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
            msg = "Telegram delivery transport is closed"
            raise RuntimeError(msg)
        result = self._notifier.send(title, text, html_body)
        raw_count = result.get("recipients")
        recipient_count = int(raw_count) if isinstance(raw_count, (int, str)) else None
        return NotificationDeliveryResultV1(
            channel="telegram",
            status="accepted",
            recipient_count=recipient_count,
        )

    def close(self) -> None:
        self._active = False


def create_provider(
    *,
    dependencies: Mapping[CapabilityId, object],
    config: Mapping[str, object],
    scope: EffectScope,
) -> NotificationDeliveryCapabilityV1:
    """Create scoped Telegram notification delivery provider instance.

    Args:
        dependencies: Must be empty.
        config: Must contain only 'configuration' with TelegramConfig.
        scope: EffectScope managing provider lifecycle.

    Returns:
        NotificationDeliveryCapabilityV1 instance.

    Raises:
        ValueError: If config or dependencies are invalid.
    """
    if dependencies or set(config.keys()) != {"configuration"}:
        msg = "telegram notification provider requires only 'configuration'"
        raise ValueError(msg)

    configuration = config["configuration"]
    if not isinstance(configuration, TelegramConfig):
        msg = "telegram notification provider requires only 'configuration'"
        raise ValueError(msg)  # noqa: TRY004

    notifier = TelegramNotifier(configuration)
    adapter = _TelegramDeliveryAdapter(notifier)
    scope.callback(adapter.close)
    return adapter


__all__ = ("create_provider",)
