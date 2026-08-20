"""Thread-safe orchestration for configured notification channels."""

from __future__ import annotations

import importlib
from collections import defaultdict, deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from threading import RLock
from time import monotonic
from types import MappingProxyType
from typing import Any, Protocol

from app.capabilities.notification.delivery.v1 import (
    NotificationDeliveryCapabilityV1,
    NotificationDeliveryResultV1,
)
from app.kernel.effects import EffectScope
from app.utils.errors.exceptions import ConfigurationError
from app.utils.logging import get_logger
from app.utils.notifications.desktop import DesktopConfig
from app.utils.notifications.email import EmailConfig
from app.utils.notifications.sms import SMSConfig
from app.utils.notifications.telegram import TelegramConfig
from app.utils.notifications.templates import TemplateRegistry

_LOGGER = get_logger(__name__)
_MIN_RATE_WINDOW_SECONDS = 0.1
_MAX_RATE_WINDOW_SECONDS = 86_400.0

_PROVIDER_FACTORIES: Mapping[str, str] = {
    "desktop": "app.utils.notifications.providers.desktop.plugin",
    "email": "app.utils.notifications.providers.email.plugin",
    "telegram": "app.utils.notifications.providers.telegram.plugin",
    "sms": "app.utils.notifications.providers.sms.plugin",
}


class _Notifier(Protocol):
    """Internal notifier substitution contract."""

    @property
    def active(self) -> bool:
        """Return whether the channel is active."""
        ...

    def send(
        self, title: str, text: str, html_body: str | None = None
    ) -> Mapping[str, object] | NotificationDeliveryResultV1:
        """Send a message through the notifier."""
        ...


@dataclass(frozen=True, slots=True)
class NotificationManagerConfig:
    """Validated internal manager configuration.

    Attributes:
        enabled: Whether notification management is enabled.
        default_channels: Default target channel names.
        rate_limit: Maximum allowed sends per rate window per channel.
        rate_window_seconds: Rate window duration in seconds.
    """

    enabled: bool = False
    default_channels: tuple[str, ...] = ()
    rate_limit: int = 10
    rate_window_seconds: float = 60.0


class NotificationManager:
    """Coordinate notifier lifetimes, templates, and per-channel rate limits."""

    def __init__(
        self,
        config: NotificationManagerConfig,
        notifiers: (
            Mapping[str, NotificationDeliveryCapabilityV1] | Mapping[str, _Notifier]
        ),
    ) -> None:
        """Initialize one manager session.

        Args:
            config: Manager configuration settings.
            notifiers: Channel name to notifier adapter map.
        """
        self._config = config
        self._notifiers = dict(notifiers)
        self._templates = TemplateRegistry()
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = RLock()
        self._closed = False

    def status(self) -> Mapping[str, object]:
        """Return secret-safe manager and channel state.

        Returns:
            Mapping of manager state and channel availability.
        """
        with self._lock:
            return MappingProxyType(
                {
                    "enabled": self._config.enabled,
                    "closed": self._closed,
                    "channels": tuple(
                        (name, notifier.active)
                        for name, notifier in sorted(self._notifiers.items())
                    ),
                }
            )

    def send(
        self,
        title: str,
        text: str,
        *,
        html_body: str | None = None,
        channels: Sequence[str] | None = None,
    ) -> Mapping[str, object]:
        """Send a message through each selected active channel.

        Args:
            title: Notification title.
            text: Plain-text notification body.
            html_body: Optional HTML body.
            channels: Optional channel override.

        Returns:
            Immutable aggregate delivery result.

        Raises:
            ConfigurationError: If the message or channel selection is invalid.
        """
        if not title.strip() or not text.strip():
            raise ConfigurationError("NOTIFICATION_MESSAGE_INVALID")
        selected = tuple(dict.fromkeys(channels or self._config.default_channels))
        if not selected:
            raise ConfigurationError("NOTIFICATION_CHANNELS_MISSING")
        results: list[Mapping[str, object]] = []
        for channel in selected:
            notifier = self._reserve(channel)
            if notifier is None:
                results.append({"channel": channel, "status": "unavailable"})
                continue
            try:
                result = notifier.send(title, text, html_body)
                result_payload: dict[str, object]
                if isinstance(result, NotificationDeliveryResultV1):
                    result_payload = {
                        "channel": result.channel,
                        "status": result.status,
                    }
                    if result.recipient_count is not None:
                        result_payload["recipients"] = result.recipient_count
                else:
                    result_payload = dict(result)
                results.append(
                    {"channel": channel, "status": "sent", "result": result_payload}
                )
            except (ConfigurationError, OSError, RuntimeError) as error:
                _LOGGER.exception("Notification channel failed: %s", channel)
                results.append(
                    {
                        "channel": channel,
                        "status": "failed",
                        "error": type(error).__name__,
                    }
                )
        sent = sum(result["status"] == "sent" for result in results)
        status = "success" if sent == len(results) else "partial" if sent else "error"
        return MappingProxyType({"status": status, "results": tuple(results)})

    def _reserve(self, channel: str) -> _Notifier | None:
        """Reserve one rate-limit slot while holding the manager lock.

        Args:
            channel: Registered channel name.

        Returns:
            Active notifier, or ``None`` when unavailable or rate limited.

        Raises:
            ConfigurationError: If the manager is closed or disabled.
        """
        with self._lock:
            if self._closed or not self._config.enabled:
                raise ConfigurationError("NOTIFICATIONS_DISABLED")
            notifier = self._notifiers.get(channel)
            if notifier is None or not notifier.active:
                return None
            now = monotonic()
            events = self._events[channel]
            while events and now - events[0] >= self._config.rate_window_seconds:
                events.popleft()
            if len(events) >= self._config.rate_limit:
                return None
            events.append(now)
            return notifier

    def close(self) -> None:
        """Close this manager against future sends."""
        with self._lock:
            self._closed = True
            for notifier in self._notifiers.values():
                close_func = getattr(notifier, "close", None)
                if callable(close_func):
                    try:
                        close_func()
                    except Exception:
                        _LOGGER.exception("Failed to close notification delivery")
            self._notifiers.clear()
            self._events.clear()

    def template_names(self) -> tuple[str, ...]:
        """Return registered template names.

        Returns:
            Tuple of registered template names.
        """
        return self._templates.names()

    def register_template(
        self, name: str, title: str, text: str, html_body: str
    ) -> None:
        """Register a session-local custom template.

        Args:
            name: Template name.
            title: Title format string.
            text: Plain text body format string.
            html_body: HTML body format string.
        """
        self._templates.register(name, title, text, html_body)

    def render_template(
        self, name: str, values: Mapping[str, object]
    ) -> Mapping[str, str]:
        """Render one registered template.

        Args:
            name: Registered template name.
            values: Template rendering values.

        Returns:
            Rendered notification fields.
        """
        return self._templates.render(name, values)


def build_notification_manager_config(
    *,
    enabled: bool = False,
    default_channels: Sequence[str] = (),
    rate_limit: int = 10,
    rate_window_seconds: float = 60.0,
) -> object:
    """Build an opaque validated notification-manager configuration.

    Args:
        enabled: Whether notification delivery is enabled.
        default_channels: Default delivery channels.
        rate_limit: Maximum deliveries per channel and window.
        rate_window_seconds: Rate-limit window duration.

    Returns:
        Opaque immutable manager configuration.

    Raises:
        ConfigurationError: If a channel or rate limit is invalid.
    """
    channels = tuple(
        dict.fromkeys(
            value.strip().lower() for value in default_channels if value.strip()
        )
    )
    if any(value not in {"desktop", "email", "telegram", "sms"} for value in channels):
        raise ConfigurationError("NOTIFICATION_CHANNEL_INVALID")
    if (
        rate_limit < 1
        or not _MIN_RATE_WINDOW_SECONDS
        <= rate_window_seconds
        <= _MAX_RATE_WINDOW_SECONDS
    ):
        raise ConfigurationError("NOTIFICATION_CONFIG_INVALID")
    return NotificationManagerConfig(enabled, channels, rate_limit, rate_window_seconds)


def create_notification_manager(
    config: object,
    *,
    desktop_config: object | None = None,
    email_config: object | None = None,
    telegram_config: object | None = None,
    sms_config: object | None = None,
    deliveries: Mapping[str, NotificationDeliveryCapabilityV1] | None = None,
) -> object:
    """Create one thread-safe notification manager from opaque configurations.

    Args:
        config: Opaque manager configuration.
        desktop_config: Optional opaque desktop configuration.
        email_config: Optional opaque email configuration.
        telegram_config: Optional opaque Telegram configuration.
        sms_config: Optional opaque SMS configuration.
        deliveries: Optional explicit mapping of channel to delivery capabilities.

    Returns:
        Opaque thread-safe manager.

    Raises:
        ConfigurationError: If any opaque configuration has the wrong type.
    """
    if not isinstance(config, NotificationManagerConfig):
        raise ConfigurationError("NOTIFICATION_CONFIG_INVALID")

    notifiers: dict[str, Any] = {}
    if deliveries is not None:
        notifiers.update(deliveries)

    pairs = (
        ("desktop", desktop_config, DesktopConfig),
        ("email", email_config, EmailConfig),
        ("telegram", telegram_config, TelegramConfig),
        ("sms", sms_config, SMSConfig),
    )

    for name, value, expected in pairs:
        if value is not None:
            if not isinstance(value, expected):
                raise ConfigurationError("NOTIFICATION_CONFIG_INVALID")
            module_name = _PROVIDER_FACTORIES.get(name)
            if module_name is not None:
                try:
                    mod = importlib.import_module(module_name)
                    create_func = mod.create_provider
                    scope = EffectScope()
                    adapter = create_func(
                        dependencies={},
                        config={"configuration": value},
                        scope=scope,
                    )
                    notifiers[name] = adapter
                except (ImportError, AttributeError, ValueError) as err:
                    _LOGGER.warning(
                        "Notification provider %s could not be loaded: %s", name, err
                    )

    return NotificationManager(config, notifiers)


def get_notification_manager_status(manager: object) -> Mapping[str, object]:
    """Return secret-safe status for an opaque manager.

    Args:
        manager: Opaque notification manager.

    Returns:
        Secret-safe manager status.

    Raises:
        ConfigurationError: If the manager has the wrong type.
    """
    return _require_manager(manager).status()


def send_notification(
    manager: object,
    title: str,
    text: str,
    *,
    html_body: str | None = None,
    channels: Sequence[str] | None = None,
) -> Mapping[str, object]:
    """Send one notification through an opaque manager.

    Args:
        manager: Opaque notification manager.
        title: Notification title.
        text: Plain-text body.
        html_body: Optional HTML body.
        channels: Optional channel override.

    Returns:
        Aggregate delivery result.

    Raises:
        ConfigurationError: If the manager or message is invalid.
    """
    return _require_manager(manager).send(
        title, text, html_body=html_body, channels=channels
    )


def get_notification_template_names(manager: object) -> tuple[str, ...]:
    """Return template names registered in an opaque manager.

    Args:
        manager: Opaque notification manager.

    Returns:
        Registered template names.

    Raises:
        ConfigurationError: If the manager has the wrong type.
    """
    return _require_manager(manager).template_names()


def register_notification_template(
    manager: object, name: str, title: str, text: str, html_body: str
) -> None:
    """Register a session-local custom template.

    Args:
        manager: Opaque notification manager.
        name: Custom template name.
        title: Title format string.
        text: Plain-text format string.
        html_body: HTML format string.

    Raises:
        ConfigurationError: If the manager or template is invalid.
    """
    _require_manager(manager).register_template(name, title, text, html_body)


def render_notification_template(
    manager: object, name: str, values: Mapping[str, object]
) -> Mapping[str, str]:
    """Render a registered notification template.

    Args:
        manager: Opaque notification manager.
        name: Registered template name.
        values: Template rendering values.

    Returns:
        Rendered notification fields.

    Raises:
        ConfigurationError: If the manager, template, or values are invalid.
    """
    return _require_manager(manager).render_template(name, values)


def close_notification_manager(manager: object) -> None:
    """Close an opaque manager.

    Args:
        manager: Opaque notification manager.

    Raises:
        ConfigurationError: If the manager has the wrong type.
    """
    _require_manager(manager).close()


def _require_manager(manager: object) -> NotificationManager:
    """Validate an opaque manager value.

    Args:
        manager: Candidate manager.

    Returns:
        Validated internal manager.

    Raises:
        ConfigurationError: If the value has the wrong type.
    """
    if not isinstance(manager, NotificationManager):
        raise ConfigurationError("NOTIFICATION_MANAGER_INVALID")
    return manager


__all__ = (
    "build_notification_manager_config",
    "close_notification_manager",
    "create_notification_manager",
    "get_notification_manager_status",
    "get_notification_template_names",
    "register_notification_template",
    "render_notification_template",
    "send_notification",
)
