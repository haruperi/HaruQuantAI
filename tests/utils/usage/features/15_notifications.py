"""Standalone usage evidence for FEAT-UTIL-14 notifications."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.utils import (
    build_desktop_notification_config,
    build_email_notification_config,
    build_notification_manager_config,
    build_sms_notification_config,
    build_telegram_notification_config,
    close_notification_manager,
    create_notification_manager,
    get_notification_manager_status,
    get_notification_template_names,
    register_notification_template,
    render_notification_template,
    send_notification,
)


def main() -> None:
    """Run a safe notification composition example covering public API calls."""
    desktop_cfg = build_desktop_notification_config(enabled=False)
    email_cfg = build_email_notification_config(
        host="localhost",
        port=25,
        sender="sender@example.test",
        recipients=("team@example.test",),
        enabled=False,
    )
    sms_cfg = build_sms_notification_config(
        account_sid="AC12345",
        auth_token="secret",
        from_phone="+15005550006",
        recipients=("+15005550001",),
        enabled=False,
    )
    telegram_cfg = build_telegram_notification_config(
        bot_token="123:abc",
        chat_ids=("12345",),
        enabled=False,
    )
    manager_cfg = build_notification_manager_config(
        enabled=False, default_channels=("desktop",)
    )
    manager = create_notification_manager(
        manager_cfg,
        desktop_config=desktop_cfg,
        email_config=email_cfg,
        sms_config=sms_cfg,
        telegram_config=telegram_cfg,
    )
    status = get_notification_manager_status(manager)
    register_notification_template(
        manager, "usage_template", "Subject: {msg}", "Text: {msg}", "<p>{msg}</p>"
    )
    names = get_notification_template_names(manager)
    rendered = render_notification_template(manager, "usage_template", {"msg": "test"})
    res = send_notification(manager, "Title", "Text")
    close_notification_manager(manager)
    print("FEAT-UTIL-14 notification usage succeeded")
    print(
        f"Data -> status={status['enabled']!r}, names={len(names)}, rendered={rendered['title']!r}, res={res['status']!r}"
    )


if __name__ == "__main__":
    main()
