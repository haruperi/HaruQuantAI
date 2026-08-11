"""SMTP email notification delivery."""

from __future__ import annotations

import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage

from app.utils.errors.exceptions import ConfigurationError

_MAX_PORT = 65_535
_MIN_TIMEOUT_SECONDS = 0.1
_MAX_TIMEOUT_SECONDS = 60.0


@dataclass(frozen=True, slots=True)
class EmailConfig:
    """Validated internal SMTP configuration.

    Attributes:
        host: SMTP server hostname.
        port: SMTP server port number.
        tls_mode: TLS mode ("none", "starttls", or "ssl").
        username: Optional SMTP authentication username.
        password: Optional SMTP authentication password.
        sender: Sender email address.
        recipients: Recipient email address tuple.
        enabled: Whether email delivery is active.
        timeout_seconds: Network connection timeout in seconds.
    """

    host: str
    port: int
    tls_mode: str
    username: str | None
    password: str | None
    sender: str
    recipients: tuple[str, ...]
    enabled: bool = False
    timeout_seconds: float = 10.0


class EmailNotifier:
    """Deliver multipart email through a bounded SMTP session."""

    def __init__(self, config: EmailConfig) -> None:
        """Initialize EmailNotifier.

        Args:
            config: Email notification configuration.
        """
        self._config = config

    @property
    def active(self) -> bool:
        """Return whether complete SMTP delivery configuration is enabled.

        Returns:
            True if enabled with non-empty host and recipients.
        """
        return self._config.enabled and bool(
            self._config.host and self._config.recipients
        )

    def send(self, title: str, text: str, html: str | None = None) -> dict[str, object]:
        """Send one plain-text and optional HTML email.

        Args:
            title: Email subject.
            text: Plain-text body.
            html: Optional HTML alternative.

        Returns:
            Secret-safe channel delivery result.

        Raises:
            ConfigurationError: If unavailable or the SMTP outcome is unsuccessful.
        """
        if not self.active:
            raise ConfigurationError("NOTIFICATION_CHANNEL_UNAVAILABLE")
        message = EmailMessage()
        message["Subject"] = title
        message["From"] = self._config.sender
        message["To"] = ", ".join(self._config.recipients)
        message.set_content(text)
        if html is not None:
            message.add_alternative(html, subtype="html")
        context = ssl.create_default_context()
        try:
            client_cm: smtplib.SMTP | smtplib.SMTP_SSL
            if self._config.tls_mode == "ssl":
                client_cm = smtplib.SMTP_SSL(
                    self._config.host,
                    self._config.port,
                    timeout=self._config.timeout_seconds,
                    context=context,
                )
            else:
                client_cm = smtplib.SMTP(
                    self._config.host,
                    self._config.port,
                    timeout=self._config.timeout_seconds,
                )
            with client_cm as client:
                if self._config.tls_mode == "starttls":
                    client.starttls(context=context)
                if (
                    self._config.username is not None
                    and self._config.password is not None
                ):
                    client.login(self._config.username, self._config.password)
                refused = client.send_message(message)
        except (OSError, smtplib.SMTPException) as error:
            raise ConfigurationError("NOTIFICATION_DELIVERY_UNKNOWN") from error
        if refused:
            raise ConfigurationError("NOTIFICATION_DELIVERY_FAILED")
        return {
            "channel": "email",
            "status": "accepted",
            "recipients": len(self._config.recipients),
        }


def build_email_notification_config(
    *,
    host: str,
    port: int,
    sender: str,
    recipients: tuple[str, ...],
    tls_mode: str = "starttls",
    username: str | None = None,
    password: str | None = None,
    enabled: bool = False,
    timeout_seconds: float = 10.0,
) -> object:
    """Build validated SMTP notification configuration.

    Args:
        host: SMTP host name.
        port: SMTP TCP port.
        sender: Sender email address.
        recipients: Destination email addresses.
        tls_mode: Exactly ``ssl``, ``starttls``, or ``none``.
        username: Optional SMTP username.
        password: Optional SMTP password.
        enabled: Whether SMTP delivery is active.
        timeout_seconds: Network timeout.

    Returns:
        Opaque immutable email configuration.

    Raises:
        ConfigurationError: If configuration is malformed or incomplete.
    """
    normalized = tuple(value.strip() for value in recipients if value.strip())
    if (
        not host.strip()
        or not sender.strip()
        or not 1 <= port <= _MAX_PORT
        or tls_mode not in {"ssl", "starttls", "none"}
        or not normalized
        or not _MIN_TIMEOUT_SECONDS <= timeout_seconds <= _MAX_TIMEOUT_SECONDS
        or ((username is None) != (password is None))
    ):
        raise ConfigurationError("NOTIFICATION_CONFIG_INVALID")
    return EmailConfig(
        host.strip(),
        port,
        tls_mode,
        username,
        password,
        sender.strip(),
        normalized,
        enabled,
        timeout_seconds,
    )


__all__ = ("build_email_notification_config",)
