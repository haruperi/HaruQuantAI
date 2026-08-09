"""Twilio SMS notification delivery."""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from app.utils.errors.exceptions import ConfigurationError

_MAX_SMS_LENGTH = 1600
_MIN_TIMEOUT_SECONDS = 0.1
_MAX_TIMEOUT_SECONDS = 60.0


@dataclass(frozen=True, slots=True)
class SMSConfig:
    """Validated internal Twilio SMS configuration."""

    account_sid: str
    auth_token: str
    from_phone: str
    recipients: tuple[str, ...]
    enabled: bool = False
    timeout_seconds: float = 10.0


class SMSNotifier:
    """Deliver bounded warning text through Twilio's Message resource."""

    def __init__(self, config: SMSConfig) -> None:
        self._config = config

    @property
    def active(self) -> bool:
        """Return whether Twilio delivery is fully configured and enabled."""
        return self._config.enabled and bool(self._config.recipients)

    def send(
        self, _title: str, message: str, _html_body: str | None = None
    ) -> dict[str, object]:
        """Submit one SMS message for every configured recipient.

        Args:
            _title: Uniform manager title, unused by SMS.
            message: Bounded SMS body.

        Returns:
            Secret-safe channel delivery result.

        Raises:
            ConfigurationError: If unavailable or a provider outcome is unsuccessful.
        """
        if not self.active:
            raise ConfigurationError("NOTIFICATION_CHANNEL_UNAVAILABLE")
        if not 1 <= len(message) <= _MAX_SMS_LENGTH:
            raise ConfigurationError("NOTIFICATION_CONTENT_INVALID")
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self._config.account_sid}/Messages.json"
        auth = base64.b64encode(
            f"{self._config.account_sid}:{self._config.auth_token}".encode()
        ).decode("ascii")
        for recipient in self._config.recipients:
            data = urllib.parse.urlencode(
                {"From": self._config.from_phone, "To": recipient, "Body": message}
            ).encode()
            request = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Authorization": f"Basic {auth}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(  # noqa: S310 - fixed HTTPS Twilio URL.
                    request, timeout=self._config.timeout_seconds
                ) as response:
                    result = json.loads(response.read())
            except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
                raise ConfigurationError("NOTIFICATION_DELIVERY_UNKNOWN") from error
            if not isinstance(result, dict) or not str(
                result.get("sid", "")
            ).startswith("SM"):
                raise ConfigurationError("NOTIFICATION_DELIVERY_FAILED")
        return {
            "channel": "sms",
            "status": "accepted",
            "recipients": len(self._config.recipients),
        }


def build_sms_notification_config(
    *,
    account_sid: str,
    auth_token: str,
    from_phone: str,
    recipients: tuple[str, ...],
    enabled: bool = False,
    timeout_seconds: float = 10.0,
) -> object:
    """Build validated Twilio SMS notification configuration.

    Args:
        account_sid: Twilio account identifier.
        auth_token: Twilio authentication credential.
        from_phone: Twilio sender number.
        recipients: Destination mobile numbers.
        enabled: Whether SMS delivery is active.
        timeout_seconds: Network timeout.

    Returns:
        Opaque immutable SMS configuration.

    Raises:
        ConfigurationError: If configuration is malformed or incomplete.
    """
    normalized = tuple(value.strip() for value in recipients if value.strip())
    if (
        not account_sid.startswith("AC")
        or not auth_token.strip()
        or not from_phone.startswith("+")
        or not normalized
        or any(not value.startswith("+") for value in normalized)
        or not _MIN_TIMEOUT_SECONDS <= timeout_seconds <= _MAX_TIMEOUT_SECONDS
    ):
        raise ConfigurationError("NOTIFICATION_CONFIG_INVALID")
    return SMSConfig(
        account_sid, auth_token, from_phone, normalized, enabled, timeout_seconds
    )


__all__ = ("build_sms_notification_config",)
