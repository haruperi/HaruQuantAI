"""Email notification delivery provider factory."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from app.contracts.notification.delivery.v1 import (
    NotificationDeliveryCapabilityV1,
    NotificationDeliveryResultV1,
)
from app.utils.notifications.email import (  # type: ignore[import-untyped]
    EmailConfig,
    EmailNotifier,
)

if TYPE_CHECKING:
    from app.kernel.effects import EffectScope
    from app.kernel.identifiers import CapabilityId


class _EmailDeliveryAdapter:
    """Adapts internal EmailNotifier to NotificationDeliveryCapabilityV1 protocol."""

    def __init__(self, notifier: EmailNotifier) -> None:
        self._notifier = notifier
        self._active = True

    @property
    def channel(self) -> str:
        return "email"

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
            msg = "Email delivery transport is closed"
            raise RuntimeError(msg)
        result = self._notifier.send(title, text, html_body)
        raw_count = result.get("recipients")
        recipient_count = int(raw_count) if isinstance(raw_count, (int, str)) else 1
        return NotificationDeliveryResultV1(
            channel="email",
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
    """Create scoped Email notification delivery provider instance.

    Args:
        dependencies: Must be empty.
        config: Must contain only 'configuration' with EmailConfig.
        scope: EffectScope managing provider lifecycle.

    Returns:
        NotificationDeliveryCapabilityV1 instance.

    Raises:
        ValueError: If config or dependencies are invalid.
    """
    if dependencies or set(config.keys()) != {"configuration"}:
        msg = "email notification provider requires only 'configuration'"
        raise ValueError(msg)

    configuration = config["configuration"]
    if not isinstance(configuration, EmailConfig):
        msg = "email notification provider requires only 'configuration'"
        raise ValueError(msg)  # noqa: TRY004

    notifier = EmailNotifier(configuration)
    adapter = _EmailDeliveryAdapter(notifier)
    scope.callback(adapter.close)
    return adapter


__all__ = ("create_provider",)
