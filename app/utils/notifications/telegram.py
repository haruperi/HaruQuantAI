"""Telegram Bot API notification delivery."""

from __future__ import annotations

import html
import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from app.utils.errors.exceptions import ConfigurationError

_MAX_TELEGRAM_LENGTH = 4096
_MIN_TIMEOUT_SECONDS = 0.1
_MAX_TIMEOUT_SECONDS = 60.0


@dataclass(frozen=True, slots=True)
class TelegramConfig:
    """Validated internal Telegram configuration."""

    bot_token: str
    chat_ids: tuple[str, ...]
    enabled: bool = False
    timeout_seconds: float = 10.0


class TelegramNotifier:
    """Deliver formatted messages through Telegram ``sendMessage``."""

    def __init__(self, config: TelegramConfig) -> None:
        self._config = config

    @property
    def active(self) -> bool:
        """Return whether Telegram delivery is fully configured and enabled."""
        return self._config.enabled and bool(
            self._config.bot_token and self._config.chat_ids
        )

    def send(
        self, title: str, message: str, _html_body: str | None = None
    ) -> dict[str, object]:
        """Send one HTML-formatted message to each configured chat.

        Args:
            title: Notification title rendered with Telegram-supported emphasis.
            message: Plain-text notification body escaped by this adapter.
            _html_body: Email-oriented HTML ignored by the Telegram adapter.

        Returns:
            Secret-safe channel delivery result.

        Raises:
            ConfigurationError: If unavailable or any outcome is unsuccessful.
        """
        if not self.active:
            raise ConfigurationError("NOTIFICATION_CHANNEL_UNAVAILABLE")
        telegram_html = f"<b>{html.escape(title)}</b>\n{html.escape(message)}"
        if not 1 <= len(telegram_html) <= _MAX_TELEGRAM_LENGTH:
            raise ConfigurationError("NOTIFICATION_CONTENT_INVALID")
        url = f"https://api.telegram.org/bot{self._config.bot_token}/sendMessage"
        for chat_id in self._config.chat_ids:
            payload = json.dumps(
                {"chat_id": chat_id, "text": telegram_html, "parse_mode": "HTML"}
            ).encode()
            request = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(  # noqa: S310 - fixed HTTPS Telegram URL.
                    request, timeout=self._config.timeout_seconds
                ) as response:
                    result = json.loads(response.read())
            except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
                raise ConfigurationError("NOTIFICATION_DELIVERY_UNKNOWN") from error
            if not isinstance(result, dict) or result.get("ok") is not True:
                raise ConfigurationError("NOTIFICATION_DELIVERY_FAILED")
        return {
            "channel": "telegram",
            "status": "accepted",
            "recipients": len(self._config.chat_ids),
        }


def build_telegram_notification_config(
    *,
    bot_token: str,
    chat_ids: tuple[str, ...],
    enabled: bool = False,
    timeout_seconds: float = 10.0,
) -> object:
    """Build validated Telegram notification configuration.

    Args:
        bot_token: Telegram bot credential.
        chat_ids: Destination user or channel identifiers.
        enabled: Whether Telegram delivery is active.
        timeout_seconds: Network timeout.

    Returns:
        Opaque immutable Telegram configuration.

    Raises:
        ConfigurationError: If configuration is malformed or incomplete.
    """
    normalized = tuple(value.strip() for value in chat_ids if value.strip())
    if (
        not bot_token.strip()
        or not normalized
        or not _MIN_TIMEOUT_SECONDS <= timeout_seconds <= _MAX_TIMEOUT_SECONDS
    ):
        raise ConfigurationError("NOTIFICATION_CONFIG_INVALID")
    return TelegramConfig(bot_token.strip(), normalized, enabled, timeout_seconds)


__all__ = ("build_telegram_notification_config",)
