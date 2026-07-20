"""Notification service tool exports.

Purpose:
    Expose deterministic notification function tools from focused modules
    without placing implementation logic in this package initializer.
"""

from __future__ import annotations

from app.services.utils.standard import standardize_domain_exports

from .base import (
    NotificationLevel,
    NotificationMessage,
    NotificationResult,
)
from .config import NotificationConfig
from .desktop import DesktopConfig, DesktopNotifier
from .email import EmailConfig, EmailNotifier
from .manager import NotificationManager, NotificationManagerConfig
from .sms import SMSConfig, SMSNotifier
from .telegram import TelegramConfig, TelegramNotifier

# tools.py tools
from .tools import (
    build_notification_manager_config,
    build_notification_message,
    create_notification_manager,
    get_notification_service_status,
    render_notification_template,
    send_custom_notification,
    send_error_notification,
    send_position_notification,
    send_system_notification,
    send_trading_notification,
    validate_notification_config,
)

__version__ = "1.0.0"
__author__ = "HaruPyQuant Team"


__all__ = [
    # base models
    "NotificationLevel",
    "NotificationMessage",
    "NotificationResult",
    # configs
    "NotificationConfig",
    "DesktopConfig",
    "EmailConfig",
    "SMSConfig",
    "TelegramConfig",
    # managers
    "NotificationManager",
    "NotificationManagerConfig",
    # notifiers
    "DesktopNotifier",
    "EmailNotifier",
    "SMSNotifier",
    "TelegramNotifier",
    # tools.py tools
    "build_notification_manager_config",
    "build_notification_message",
    "create_notification_manager",
    "get_notification_service_status",
    "render_notification_template",
    "send_custom_notification",
    "send_error_notification",
    "send_position_notification",
    "send_system_notification",
    "send_trading_notification",
    "validate_notification_config",
]


standardize_domain_exports(globals(), __all__, tool_category="notification")

