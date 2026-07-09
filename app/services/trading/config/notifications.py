"""Operational notification channel configuration and payload redaction."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field, model_validator

from app.services.trading.config.models import TradingConfigModel
from app.utils.logger import logger
from app.utils.security import redact_value

if TYPE_CHECKING:
    from app.services.trading.contracts import JsonObject


class NotificationChannel(TradingConfigModel):
    """Approved operational notification channel."""

    name: str
    kind: str
    enabled: bool = True
    approved: bool = False
    target_ref: str

    @model_validator(mode="after")
    def validate_channel(self) -> NotificationChannel:
        """Validate notification channel metadata.

        Returns:
            NotificationChannel: Validated channel.
        """
        logger.info("Validating notification channel {}.", self.name)
        missing_required_text = (
            not self.name.strip()
            or not self.kind.strip()
            or not self.target_ref.strip()
        )
        if missing_required_text:
            raise ValueError("notification channel fields must be non-empty.")
        return self


class NotificationConfig(TradingConfigModel):
    """Operational notification routing configuration."""

    channels: tuple[NotificationChannel, ...] = Field(default_factory=tuple)

    def approved_channel(self, name: str) -> NotificationChannel:
        """Resolve an approved notification channel.

        Args:
            name: Channel name.

        Returns:
            NotificationChannel: Approved enabled channel.

        Raises:
            ValueError: If the channel is missing, disabled, or unapproved.
        """
        logger.info("Resolving approved notification channel {}.", name)
        for channel in self.channels:
            if channel.name == name and channel.enabled and channel.approved:
                return channel
        raise ValueError("notification channel is not approved.")


def build_notification_payload(
    *,
    config: NotificationConfig,
    channel_name: str,
    event_type: str,
    payload: JsonObject,
) -> JsonObject:
    """Build a strictly redacted notification payload.

    Args:
        config: Notification routing config.
        channel_name: Target channel name.
        event_type: Operational event type.
        payload: JSON-safe notification details.

    Returns:
        JsonObject: Redacted notification payload.
    """
    logger.info("Building notification payload for {}.", event_type)
    channel = config.approved_channel(channel_name)
    redacted = redact_value(payload)
    if not isinstance(redacted, dict):
        raise TypeError("notification payload must redact to a mapping.")
    return {
        "channel": channel.name,
        "channel_kind": channel.kind,
        "target_ref": channel.target_ref,
        "event_type": event_type,
        "payload": redacted,
    }
