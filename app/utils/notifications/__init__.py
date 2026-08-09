"""Function-only public facade for unified notification delivery."""

from app.utils.notifications.desktop import build_desktop_notification_config
from app.utils.notifications.email import build_email_notification_config
from app.utils.notifications.manager import (
    build_notification_manager_config,
    close_notification_manager,
    create_notification_manager,
    get_notification_manager_status,
    get_notification_template_names,
    register_notification_template,
    render_notification_template,
    send_notification,
)
from app.utils.notifications.sms import build_sms_notification_config
from app.utils.notifications.telegram import build_telegram_notification_config

__all__ = (
    "build_desktop_notification_config",
    "build_email_notification_config",
    "build_notification_manager_config",
    "build_sms_notification_config",
    "build_telegram_notification_config",
    "close_notification_manager",
    "create_notification_manager",
    "get_notification_manager_status",
    "get_notification_template_names",
    "register_notification_template",
    "render_notification_template",
    "send_notification",
)
