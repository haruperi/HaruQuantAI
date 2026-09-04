"""Desktop notification delivery provider factory."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from app.contracts.notification.delivery.v1 import (
    NotificationDeliveryCapabilityV1,
    NotificationDeliveryResultV1,
)
from app.utils.notifications.desktop import (  # type: ignore[import-untyped]
    DesktopConfig,
    DesktopNotifier,
)

if TYPE_CHECKING:
    from app.kernel.effects import EffectScope
    from app.kernel.identifiers import CapabilityId


class _DesktopDeliveryAdapter:
    """Adapts internal DesktopNotifier to NotificationDeliveryCapabilityV1 protocol."""

    def __init__(self, notifier: DesktopNotifier) -> None:
        self._notifier = notifier
        self._active = True

    @property
    def channel(self) -> str:
        return "desktop"

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
            msg = "Desktop delivery transport is closed"
            raise RuntimeError(msg)
        self._notifier.send(title, text, html_body)
        return NotificationDeliveryResultV1(
            channel="desktop",
            status="accepted",
            recipient_count=None,
        )

    def close(self) -> None:
        self._active = False


def create_provider(
    *,
    dependencies: Mapping[CapabilityId, object],
    config: Mapping[str, object],
    scope: EffectScope,
) -> NotificationDeliveryCapabilityV1:
    """Create scoped Desktop notification delivery provider instance.

    Args:
        dependencies: Must be empty.
        config: Must contain only 'configuration' with DesktopConfig.
        scope: EffectScope managing provider lifecycle.

    Returns:
        NotificationDeliveryCapabilityV1 instance.

    Raises:
        ValueError: If config or dependencies are invalid.
    """
    if dependencies or set(config.keys()) != {"configuration"}:
        msg = "desktop notification provider requires only 'configuration'"
        raise ValueError(msg)

    configuration = config["configuration"]
    if not isinstance(configuration, DesktopConfig):
        msg = "desktop notification provider requires only 'configuration'"
        raise ValueError(msg)  # noqa: TRY004

    notifier = DesktopNotifier(configuration)
    adapter = _DesktopDeliveryAdapter(notifier)
    scope.callback(adapter.close)
    return adapter


__all__ = ("create_provider",)
