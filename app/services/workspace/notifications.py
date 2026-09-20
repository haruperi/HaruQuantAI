"""Multi-channel user notifications and pause gates feature module.

Purpose:
    Provides best-effort multi-channel notifications across email, acoustic
    sound alerts, desktop popups, Telegram, and webhooks, plus cooperative
    human-in-the-loop pause gates and structured notification templates.

Key capabilities:
    * Channel dispatch for Telegram, Email, Desktop popups, and Sound alerts.
    * Built-in template registry with 27 financial and system templates.
    * Secret and credential redaction on all message bodies and metadata.
    * Human-in-the-loop pause gates via cooperative threading events.
    * Failure isolation: notification errors never alter research or job status.

Python API usage:
    notifications = ctx.require(WORKSPACE_NOTIFICATIONS)
    receipt = notifications.send_templated_notification(
        NotificationChannel.TELEGRAM,
        recipient="5398524142",
        template_name="trading_signal",
        values={"symbol": "EURUSD", "signal_type": "BUY", ...},
    )

CLI usage:
    uv run python -m tests.examples.01_workspace
"""

from __future__ import annotations

import contextlib
import html
import json
import smtplib
import sys
import threading
import urllib.error
import urllib.request
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from email.message import EmailMessage
from string import Formatter
from threading import RLock
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, override
from uuid import uuid4

from app.contracts.workspace import (
    WORKSPACE_NOTIFICATIONS,
    ConfigurationError,
    NotificationChannel,
    NotificationReceipt,
)
from app.contracts.workspace import (
    NotificationService as INotificationService,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)

_SECRET_KEYS: frozenset[str] = frozenset(
    {"token", "secret", "password", "key", "api_key", "auth"}
)


def _redact_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of data with sensitive credentials redacted.

    Args:
        data: Mapping containing arbitrary payload values.

    Returns:
        Redacted dictionary copy with secrets masked.
    """
    redacted: dict[str, Any] = {}
    for k, v in data.items():
        if any(secret_term in k.lower() for secret_term in _SECRET_KEYS):
            redacted[k] = "[REDACTED]"
        elif isinstance(v, dict):
            redacted[k] = _redact_payload(v)
        else:
            redacted[k] = v
    return redacted


# ---------------------------------------------------------------------------
# Built-in Notification Templates
# ---------------------------------------------------------------------------

_BUILT_INS: MappingProxyType[str, tuple[str, str, str]] = MappingProxyType(
    {
        "trading_alert": (
            "Trading Alert: {symbol} {action}",
            (
                "Symbol: {symbol}\nAction: {action}\nPrice: {price}\nReason: {reason}\n"
                "Time: {timestamp}\nAccount: {account}\nStrategy: {strategy}\n"
                "Risk Level: {risk_level}"
            ),
            (
                "<p>Symbol: {symbol}<br>Action: {action}<br>Price: {price}<br>"
                "Reason: {reason}<br>Time: {timestamp}<br>Account: {account}<br>"
                "Strategy: {strategy}<br>Risk Level: {risk_level}</p>"
            ),
        ),
        "trading_signal": (
            "Trading Signal: {symbol} {signal_type}",
            (
                "{signal_type} {symbol} @ {entry_price}\n"
                "Stop Loss: {stop_loss} ({stop_loss_pips} pips)\n"
                "Take Profit: {take_profit} ({take_profit_pips} pips)\n"
                "Lots: {lots}\nStrategy: {strategy}\nStrength: {strength}\n"
                "ADR: {adr}\nRange: {range}%\nCurrent VAR: {current_var}\n"
                "Proposed VAR: {proposed_var}\nVAR Difference: {var_difference}%\n"
                "Time: {timestamp}"
            ),
            (
                "<p>{signal_type} {symbol} @ {entry_price}<br>"
                "Stop Loss: {stop_loss}<br>Take Profit: {take_profit}<br>"
                "Lots: {lots}<br>Strategy: {strategy}<br>Strength: {strength}<br>"
                "Time: {timestamp}</p>"
            ),
        ),
        "position_opened": (
            "Position Opened: {symbol} {direction}",
            (
                "Symbol: {symbol}\nDirection: {direction}\nSize: {size}\n"
                "Entry: {entry_price}\nStop Loss: {stop_loss}\n"
                "Take Profit: {take_profit}\nTime: {timestamp}\n"
                "Account: {account}\nStrategy: {strategy}\nRisk: {risk_amount}"
            ),
            (
                "<p>Position opened: {symbol} {direction}<br>"
                "Size: {size}<br>Entry: {entry_price}</p>"
            ),
        ),
        "position_closed": (
            "Position Closed: {symbol} {direction}",
            (
                "Symbol: {symbol}\nDirection: {direction}\nSize: {size}\n"
                "Entry: {entry_price}\nExit: {exit_price}\nP&amp;L: {pnl}\n"
                "P&amp;L %: {pnl_percent}\nDuration: {duration}\n"
                "Time: {timestamp}\nAccount: {account}\nStrategy: {strategy}"
            ),
            (
                "<p>Position closed: {symbol} {direction}<br>"
                "P&amp;L: {pnl}<br>Duration: {duration}</p>"
            ),
        ),
        "position_update": (
            "Position Update: {symbol}",
            (
                "Symbol: {symbol}\nType: {position_type}\nSize: {size}\n"
                "Entry: {entry_price}\nCurrent: {current_price}\nP&amp;L: {pnl}\n"
                "P&amp;L %: {pnl_percent}\nTime: {timestamp}"
            ),
            (
                "<p>Position update: {symbol}<br>"
                "Current: {current_price}<br>P&amp;L: {pnl}</p>"
            ),
        ),
        "system_alert": (
            "System Alert: {level} - {message}",
            (
                "Level: {level}\nMessage: {message}\nDetails: {details}\n"
                "Time: {timestamp}\nComponent: {component}\nStatus: {status}"
            ),
            (
                "<p><strong>{level}</strong>: {message}<br>"
                "{details}<br>{component}: {status}</p>"
            ),
        ),
        "system_startup": (
            "System Startup: HaruQuantAI",
            (
                "Started: {timestamp}\nVersion: {version}\n"
                "Environment: {environment}\nAccount: {account}\n"
                "MT5: {mt5_status}\nData Feed: {data_feed_status}\n"
                "Strategy: {strategy_status}\nRisk Manager: {risk_manager_status}"
            ),
            ("<p>HaruQuantAI started at {timestamp}<br>Environment: {environment}</p>"),
        ),
        "system_shutdown": (
            "System Shutdown: HaruQuantAI",
            (
                "Shutdown: {timestamp}\nReason: {reason}\nDuration: {duration}\n"
                "Open Positions: {open_positions}\nBalance: {account_balance}\n"
                "Daily P&amp;L: {daily_pnl}"
            ),
            "<p>HaruQuantAI shutdown at {timestamp}<br>Reason: {reason}</p>",
        ),
        "connection_lost": (
            "Connection Lost: {service}",
            (
                "Service: {service}\nLost: {timestamp}\n"
                "Error: {error_message}\nRetry: {retry_count}\n"
                "Next Retry: {next_retry}"
            ),
            "<p>Connection lost: {service}<br>Error: {error_message}</p>",
        ),
        "connection_restored": (
            "Connection Restored: {service}",
            (
                "Service: {service}\nRestored: {timestamp}\n"
                "Downtime: {downtime}\nStatus: Active"
            ),
            "<p>Connection restored: {service}<br>Downtime: {downtime}</p>",
        ),
        "error_alert": (
            "Error Alert: {error_type}",
            (
                "Type: {error_type}\nMessage: {message}\n"
                "Component: {component}\nTime: {timestamp}\n"
                "Stack Trace: {stack_trace}"
            ),
            "<p>Error: {error_type}<br>{message}<br>Component: {component}</p>",
        ),
        "strategy_error": (
            "Strategy Error: {strategy_name}",
            (
                "Strategy: {strategy_name}\nError: {error_message}\n"
                "Symbol: {symbol}\nTime: {timestamp}\nAction: {action}\n"
                "Status: {status}"
            ),
            "<p>Strategy error: {strategy_name}<br>{error_message}</p>",
        ),
        "performance_alert": (
            "Performance Alert: {alert_type}",
            (
                "Type: {alert_type}\nMetric: {metric}\nValue: {value}\n"
                "Threshold: {threshold}\nTime: {timestamp}\n"
                "Period: {period}\nAccount: {account}"
            ),
            "<p>{metric}: {value}<br>Threshold: {threshold}</p>",
        ),
        "drawdown_alert": (
            "Drawdown Alert: {drawdown_type}",
            (
                "Type: {drawdown_type}\nCurrent: {current_drawdown}%\n"
                "Peak: {peak_drawdown}%\nDuration: {duration}\n"
                "Time: {timestamp}\nAccount: {account}\n"
                "Balance: {balance}\nEquity: {equity}"
            ),
            "<p>Drawdown: {current_drawdown}%<br>Peak: {peak_drawdown}%</p>",
        ),
        "market_alert": (
            "Market Alert: {symbol}",
            (
                "Symbol: {symbol}\nEvent: {event}\nPrice: {price}\n"
                "Time: {timestamp}\nImpact: {impact}\nDetails: {details}"
            ),
            "<p>Market alert: {symbol}<br>{event}<br>Impact: {impact}</p>",
        ),
        "news_alert": (
            "News Alert: {headline}",
            (
                "Headline: {headline}\nSource: {source}\nTime: {timestamp}\n"
                "Impact: {impact}\nSummary: {summary}\nSymbols: {symbols}"
            ),
            "<p>{headline}<br>Source: {source}<br>{summary}</p>",
        ),
        "risk_alert": (
            "Risk Alert: {risk_type}",
            (
                "Type: {risk_type}\nSeverity: {severity}\nMessage: {message}\n"
                "Time: {timestamp}\nAccount: {account}\nCurrent Risk: {current_risk}\n"
                "Max Risk: {max_risk}\nAction: {action}"
            ),
            "<p>Risk: {risk_type} ({severity})<br>{message}<br>Action: {action}</p>",
        ),
        "margin_alert": (
            "Margin Alert: {account}",
            (
                "Account: {account}\nMargin Level: {margin_level}%\n"
                "Free Margin: {free_margin}\nUsed Margin: {used_margin}\n"
                "Time: {timestamp}\nWarning Level: {warning_level}%\nAction: {action}"
            ),
            "<p>Margin level: {margin_level}%<br>Action: {action}</p>",
        ),
        "custom_message": ("{title}", "{body}", "<p>{body}</p>"),
        "test_message": (
            "Test Message: {service}",
            (
                "Service: {service}\nTime: {timestamp}\nStatus: {status}\n"
                "This is a notification configuration test."
            ),
            "<p>Test: {service}<br>Time: {timestamp}<br>Status: {status}</p>",
        ),
        "info": ("Information", "{message}", "<p>{message}</p>"),
        "warning": (
            "Warning",
            "{message}",
            "<p><strong>Warning:</strong> {message}</p>",
        ),
        "error": ("Error", "{message}", "<p><strong>Error:</strong> {message}</p>"),
        "critical": (
            "Critical alert",
            "{message}",
            "<p><strong>Critical:</strong> {message}</p>",
        ),
        "trading": (
            "Trading alert",
            "{message}",
            "<p><strong>Trading:</strong> {message}</p>",
        ),
        "risk": ("Risk alert", "{message}", "<p><strong>Risk:</strong> {message}</p>"),
        "system_health": (
            "System health",
            "{message}",
            "<p><strong>System health:</strong> {message}</p>",
        ),
    }
)


class TemplateRegistry:
    """Own built-in and session-local custom notification templates."""

    def __init__(self) -> None:
        """Initialize an isolated registry."""
        self._lock = RLock()
        self._templates: dict[str, tuple[str, str, str]] = dict(_BUILT_INS)

    def names(self) -> tuple[str, ...]:
        """Return registered names in deterministic order.

        Returns:
            Tuple of registered template names.
        """
        with self._lock:
            return tuple(sorted(self._templates))

    def register(self, name: str, title: str, text: str, html_body: str) -> None:
        """Register or replace a custom template.

        Args:
            name: Custom template name.
            title: Title format string.
            text: Plain-text format string.
            html_body: HTML format string.

        Raises:
            ConfigurationError: If the custom template is invalid.
        """
        normalized = name.strip().lower()
        if (
            not normalized
            or normalized in _BUILT_INS
            or not title.strip()
            or not text.strip()
        ):
            raise ConfigurationError("NOTIFICATION_TEMPLATE_INVALID")
        with self._lock:
            self._templates[normalized] = (title, text, html_body)

    def render(self, name: str, values: Mapping[str, object]) -> Mapping[str, str]:
        """Render one template with complete, escaped values.

        Args:
            name: Registered template name.
            values: Complete rendering values.

        Returns:
            Immutable rendered title, text, and HTML mapping.

        Raises:
            ConfigurationError: If the template or a required value is missing.
        """
        with self._lock:
            template = self._templates.get(name.strip().lower())
        if template is None:
            raise ConfigurationError("NOTIFICATION_TEMPLATE_UNKNOWN")
        fields = {
            field_name
            for part in template
            for _, field_name, _, _ in Formatter().parse(part)
            if field_name
        }
        if not fields.issubset(values):
            raise ConfigurationError("NOTIFICATION_TEMPLATE_VALUE_MISSING")
        plain = {key: str(value) for key, value in values.items()}
        escaped = {key: html.escape(value) for key, value in plain.items()}
        return MappingProxyType(
            {
                "title": template[0].format_map(plain),
                "text": template[1].format_map(plain),
                "html": template[2].format_map(escaped),
            }
        )


# ---------------------------------------------------------------------------
# Channel Dispatch Helpers
# ---------------------------------------------------------------------------


def _dispatch_telegram(
    recipient: str,
    title: str,
    body: str,
    metadata: dict[str, Any],
) -> tuple[bool, str | None]:
    """Dispatch message to Telegram Bot API.

    Args:
        recipient: Default destination chat ID.
        title: Notification subject.
        body: Plain text notification body.
        metadata: Telegram parameters including bot_token and optional chat_id.

    Returns:
        Tuple of (delivered_boolean, optional_error_string).
    """
    bot_token = metadata.get("bot_token")
    if not bot_token:
        return False, "skipped: telegram bot token not configured"

    chat_id = metadata.get("chat_id") or recipient
    parse_mode = str(metadata.get("parse_mode", "HTML"))
    disable_notification = bool(metadata.get("disable_notification", False))

    if parse_mode.upper() == "HTML":
        # Telegram Bot API supports <b>, <i>, <code>, <pre> but rejects <p> and <br>.
        # Format bold title followed by clean escaped body text.
        text = f"<b>{html.escape(title)}</b>\n\n{html.escape(body)}"
    else:
        text = f"{title}\n\n{body}"

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps(
        {
            "chat_id": str(chat_id),
            "text": text,
            "parse_mode": parse_mode,
            "disable_notification": disable_notification,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "HaruQuantAI/1.0"},
    )
    http_ok = 200
    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:  # noqa: S310
            if resp.status == http_ok:
                return True, None
            return False, f"Telegram API returned HTTP status {resp.status}"
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        OSError,
        TimeoutError,
    ) as exc:
        logger.warning("telegram_dispatch_failed", error=str(exc))
        return False, f"Telegram dispatch failed: {exc}"


def _dispatch_email(
    recipient: str,
    title: str,
    body: str,
    metadata: dict[str, Any],
) -> tuple[bool, str | None]:
    """Dispatch message via SMTP email.

    Args:
        recipient: Destination email address.
        title: Email subject line.
        body: Email text body.
        metadata: SMTP settings including server, port, credentials.

    Returns:
        Tuple of (delivered_boolean, optional_error_string).
    """
    smtp_server = metadata.get("smtp_server")
    if not smtp_server:
        return False, "skipped: SMTP server not configured"

    smtp_port = int(metadata.get("smtp_port", 587))
    username = metadata.get("username")
    password = metadata.get("password")
    use_tls = bool(metadata.get("use_tls", True))
    use_ssl = bool(metadata.get("use_ssl", False))
    from_address = str(
        metadata.get("from_address") or username or "noreply@haruquant.internal"
    )
    recipients = metadata.get("recipient_addresses") or [recipient]

    msg = EmailMessage()
    msg["Subject"] = title
    msg["From"] = from_address
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)

    html_content = metadata.get("html_body")
    if html_content:
        msg.add_alternative(html_content, subtype="html")

    try:
        server = (
            smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15.0)
            if use_ssl
            else smtplib.SMTP(smtp_server, smtp_port, timeout=15.0)
        )
        try:
            if not use_ssl and use_tls:
                server.starttls()
            if username and password:
                server.login(str(username), str(password))
            server.send_message(msg)
            return True, None
        finally:
            with contextlib.suppress(Exception):
                server.close()
    except smtplib.SMTPAuthenticationError as exc:
        err_raw = exc.smtp_error
        err_detail = (
            err_raw.decode(errors="replace").strip()
            if isinstance(err_raw, bytes)
            else err_raw.strip()
        )
        err_msg = f"SMTP 535 BadCredentials (App Password required): {err_detail}"
        logger.warning("email_auth_failed", error=err_msg)
        return False, err_msg
    except (smtplib.SMTPException, OSError, TimeoutError) as exc:
        logger.warning("email_dispatch_failed", error=str(exc))
        return False, f"Email dispatch failed: {exc}"


def _dispatch_sound(
    title: str,  # noqa: ARG001
    body: str,  # noqa: ARG001
    metadata: dict[str, Any],
) -> tuple[bool, str | None]:
    """Play acoustic notification chime.

    Args:
        title: Notification subject.
        body: Notification body.
        metadata: Optional parameters including sound_enabled.

    Returns:
        Tuple of (delivered_boolean, optional_error_string).
    """
    if sys.platform != "win32":
        return False, "skipped: sound channel unavailable on this platform"

    sound_enabled = bool(metadata.get("sound_enabled", True))
    if not sound_enabled:
        return False, "skipped: sound disabled in notification metadata"

    try:
        import winsound

        winsound.MessageBeep(winsound.MB_ICONASTERISK)
        return True, None
    except Exception as exc:  # noqa: BLE001
        logger.warning("sound_dispatch_failed", error=str(exc))
        return False, f"Sound dispatch failed: {exc}"


def _dispatch_webhook(
    recipient: str,
    title: str,
    body: str,
    metadata: dict[str, Any],
) -> tuple[bool, str | None]:
    """Send webhook notification via HTTP POST.

    Args:
        recipient: Default destination URL.
        title: Notification subject.
        body: Plain text notification body.
        metadata: Webhook parameters including webhook_url and optional headers.

    Returns:
        Tuple of (delivered_boolean, optional_error_string).
    """
    webhook_url = metadata.get("webhook_url") or recipient
    if not webhook_url:
        return False, "skipped: webhook URL not configured"

    headers = {"Content-Type": "application/json", "User-Agent": "HaruQuantAI/1.0"}
    custom_headers = metadata.get("headers")
    if isinstance(custom_headers, dict):
        for k, v in custom_headers.items():
            headers[str(k)] = str(v)

    payload = json.dumps(
        {
            "title": title,
            "body": body,
            "metadata": _redact_payload(metadata),
        }
    ).encode("utf-8")

    req = urllib.request.Request(  # noqa: S310
        webhook_url,
        data=payload,
        headers=headers,
    )
    timeout = float(metadata.get("timeout", 10.0))
    http_ok_min = 200
    http_ok_max = 299
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            status_code = getattr(resp, "status", getattr(resp, "code", 200))
            if http_ok_min <= status_code <= http_ok_max:
                return True, None
            return False, f"Webhook returned unexpected HTTP status {status_code}"
    except urllib.error.HTTPError as exc:
        err_msg = f"Webhook HTTP {exc.code}: {exc.reason}"
        logger.warning("webhook_http_error", error=err_msg, code=exc.code)
        return False, err_msg
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        err_msg = f"Webhook dispatch failed: {exc}"
        logger.warning("webhook_dispatch_failed", error=err_msg)
        return False, err_msg


def _dispatch_desktop(
    recipient: str,  # noqa: ARG001
    title: str,
    body: str,
    metadata: dict[str, Any],
) -> tuple[bool, str | None]:
    """Display native Windows desktop popup notification and sound chime.

    Args:
        recipient: Desktop target / recipient label.
        title: Popup dialog title.
        body: Popup dialog body message.
        metadata: Optional parameters including duration_seconds and sound_enabled.

    Returns:
        Tuple of (delivered_boolean, optional_error_string).
    """
    if sys.platform != "win32":
        return False, "skipped: desktop popups unavailable on this platform"

    duration_seconds = float(metadata.get("duration_seconds", 5.0))
    duration_ms = int(duration_seconds * 1000)
    sound_enabled = bool(metadata.get("sound_enabled", True))

    if sound_enabled:
        with contextlib.suppress(Exception):
            import winsound

            winsound.MessageBeep(winsound.MB_ICONASTERISK)

    def _show_box() -> None:
        try:
            import ctypes

            # MB_OK (0x0) | MB_ICONINFORMATION (0x40) | MB_TOPMOST (0x40000)
            flags = 0x00040040
            ctypes.windll.user32.MessageBoxTimeoutW(
                0, body, title, flags, 0, duration_ms
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("desktop_popup_failed", error=str(exc))

    popup_thread = threading.Thread(
        target=_show_box, daemon=True, name="desktop_notification_popup"
    )
    popup_thread.start()
    if metadata.get("blocking", False):
        popup_thread.join(timeout=duration_seconds)

    return True, None


# ---------------------------------------------------------------------------
# Notification Configuration & Service Implementation
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class NotificationConfig:
    """Runtime configuration for notification dispatch."""

    enable_sound: bool = True
    enable_email: bool = True
    enable_webhooks: bool = True
    enable_telegram: bool = True
    enable_desktop: bool = True
    default_timeout_seconds: float = 300.0

    def __post_init__(self) -> None:
        """Validate notification parameters."""
        if self.default_timeout_seconds <= 0:
            msg = (
                "default_timeout_seconds must be positive; "
                f"got {self.default_timeout_seconds}"
            )
            raise ValueError(msg)


class NotificationService(INotificationService):
    """Implement multi-channel user notifications and pause gates.

    Operates as an in-process dispatcher providing thread-safe notification
    history with bounded memory, templated message synthesis, and cooperative
    pause gates.
    """

    def __init__(
        self,
        config: NotificationConfig,
        templates: TemplateRegistry | None = None,
    ) -> None:
        """Initialize notification service with active gate tracker.

        Args:
            config: Runtime notification configuration.
            templates: Optional custom or pre-populated TemplateRegistry.
        """
        self._config = config
        self._templates = templates if templates is not None else TemplateRegistry()
        self._pause_gates: dict[str, threading.Event] = {}
        self._sent_messages: deque[NotificationReceipt] = deque(maxlen=1000)

    @property
    def templates(self) -> TemplateRegistry:
        """Return the active notification template registry.

        Returns:
            TemplateRegistry instance owning all registered templates.
        """
        return self._templates

    def _dispatch_channel(
        self,
        channel: NotificationChannel,
        recipient: str,
        title: str,
        body: str,
        metadata: dict[str, Any],
    ) -> tuple[bool, str | None]:
        dispatch_table: dict[
            NotificationChannel,
            tuple[bool, str, Callable[[], tuple[bool, str | None]]],
        ] = {
            NotificationChannel.TELEGRAM: (
                self._config.enable_telegram,
                "Telegram",
                lambda: _dispatch_telegram(recipient, title, body, metadata),
            ),
            NotificationChannel.EMAIL: (
                self._config.enable_email,
                "Email",
                lambda: _dispatch_email(recipient, title, body, metadata),
            ),
            NotificationChannel.DESKTOP: (
                self._config.enable_desktop,
                "Desktop",
                lambda: _dispatch_desktop(recipient, title, body, metadata),
            ),
            NotificationChannel.SOUND: (
                self._config.enable_sound,
                "Sound",
                lambda: _dispatch_sound(title, body, metadata),
            ),
            NotificationChannel.WEBHOOK: (
                self._config.enable_webhooks,
                "Webhook",
                lambda: _dispatch_webhook(recipient, title, body, metadata),
            ),
        }
        entry = dispatch_table.get(channel)
        if entry is None:
            return False, f"Unsupported channel: {channel}"
        enabled, name, handler = entry
        if not enabled:
            return False, f"{name} channel is disabled by configuration"
        return handler()

    @override
    def send_notification(
        self,
        channel: NotificationChannel,
        recipient: str,
        title: str,
        body: str,
        *,
        require_user_action: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> NotificationReceipt:
        """Dispatch a notification across the requested channel.

        Args:
            channel: Target medium (email, sound, webhook, telegram, desktop).
            recipient: Destination target.
            title: Short subject title.
            body: Message body text.
            require_user_action: Whether this triggers a workflow pause gate.
            metadata: Optional contextual metadata.

        Returns:
            Delivery receipt confirming dispatch.
        """
        message_id = str(uuid4())
        now = datetime.now(UTC)
        raw_meta = dict(metadata or {})
        redacted_meta = _redact_payload(raw_meta)

        logger.info(
            "notification_dispatching",
            message_id=message_id,
            channel=str(channel),
            recipient=recipient,
            title=title,
            require_user_action=require_user_action,
            metadata=redacted_meta,
        )

        delivered, error = self._dispatch_channel(
            channel, recipient, title, body, raw_meta
        )

        receipt = NotificationReceipt(
            message_id=message_id,
            delivered=delivered,
            error=error,
            sent_at_utc=now,
        )
        self._sent_messages.append(receipt)

        if require_user_action:
            self._pause_gates[message_id] = threading.Event()

        return receipt

    @override
    def send_templated_notification(
        self,
        channel: NotificationChannel,
        recipient: str,
        template_name: str,
        values: Mapping[str, object],
        *,
        require_user_action: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> NotificationReceipt:
        """Dispatch a notification rendered from a registered template.

        Args:
            channel: Target medium (email, sound, webhook, telegram, desktop).
            recipient: Destination address, chat ID, or target.
            template_name: Registered template identifier.
            values: Values used to populate template placeholders.
            require_user_action: Whether this triggers a workflow pause gate.
            metadata: Optional contextual parameters.

        Returns:
            Delivery receipt.
        """
        rendered = self._templates.render(template_name, values)
        merged_metadata = dict(metadata or {})
        merged_metadata["html_body"] = rendered["html"]

        return self.send_notification(
            channel=channel,
            recipient=recipient,
            title=rendered["title"],
            body=rendered["text"],
            require_user_action=require_user_action,
            metadata=merged_metadata,
        )

    @override
    def wait_for_user_action(self, prompt_id: str, timeout_seconds: float) -> bool:
        """Wait until a human unpauses the gate or timeout occurs.

        Args:
            prompt_id: The pause gate / message identifier.
            timeout_seconds: Timeout in seconds.

        Returns:
            True if resolved; False on timeout or unknown prompt.
        """
        gate = self._pause_gates.get(prompt_id)
        if gate is None:
            logger.warning("pause_gate_unknown", prompt_id=prompt_id)
            return False

        try:
            return gate.wait(timeout=timeout_seconds)
        finally:
            self._pause_gates.pop(prompt_id, None)

    @override
    def resume_user_action(self, prompt_id: str) -> None:
        """Unpause an active user action gate.

        Args:
            prompt_id: Target gate ID.
        """
        gate = self._pause_gates.get(prompt_id)
        if gate is not None:
            gate.set()
            logger.info("pause_gate_resumed", prompt_id=prompt_id)
        else:
            logger.warning("pause_gate_resume_missing", prompt_id=prompt_id)


SPEC: FeatureSpec = FeatureSpec(
    name="workspace.notifications",
    provides=frozenset({WORKSPACE_NOTIFICATIONS}),
    requires=frozenset(),
    optional=frozenset(),
    description="Multi-channel notifications, template registry, and pause gates.",
)


class NotificationFeature:
    """Lifecycle-managed runtime feature providing multi-channel notification dispatch.

    Mounts the NotificationService, binds configuration parameters, and publishes
    the WORKSPACE_NOTIFICATIONS capability token into the runtime composition.
    """

    def __init__(self, config: NotificationConfig | None = None) -> None:
        """Initialize notification feature with runtime dispatch configuration.

        Args:
            config: Notification configuration specifying channel toggles and delivery
                timeouts. If None, default NotificationConfig is used.
        """
        self._config = config or NotificationConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return immutable specification declaring capabilities and dependencies."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Start notification service and publish WORKSPACE_NOTIFICATIONS capability.

        Args:
            context: Runtime feature context used for capability provision and
                resolution.
        """
        service = NotificationService(self._config)
        context.provide(WORKSPACE_NOTIFICATIONS, service)
        logger.info("workspace_notifications_started")


def feature() -> NotificationFeature:
    """Construct an unmounted NotificationFeature instance for runtime bootstrapping.

    Returns:
        Configured NotificationFeature instance ready for composition registration.
    """
    return NotificationFeature()


__all__ = [
    "SPEC",
    "ConfigurationError",
    "NotificationConfig",
    "NotificationFeature",
    "NotificationService",
    "TemplateRegistry",
    "feature",
]
