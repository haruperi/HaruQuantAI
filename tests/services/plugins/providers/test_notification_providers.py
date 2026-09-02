"""Tests for notification delivery providers (desktop, email, sms, telegram)."""

from __future__ import annotations

import sys
import types

import pytest
from app.contracts.notification.delivery.v1 import (
    NotificationDeliveryResultV1,
)
from app.kernel.effects import EffectScope


class MockDesktopConfig:
    def __init__(self, enabled: bool = True, timeout_seconds: float = 5.0):
        self.enabled = enabled
        self.timeout_seconds = timeout_seconds


class MockDesktopNotifier:
    def __init__(self, config: MockDesktopConfig):
        self.config = config
        self.active = config.enabled
        self.sent: list[tuple[str, str, str | None]] = []

    def send(self, title: str, text: str, html_body: str | None = None) -> None:
        self.sent.append((title, text, html_body))


def build_desktop_notification_config(
    enabled: bool = False, timeout_seconds: float = 5.0
):
    return MockDesktopConfig(enabled=enabled, timeout_seconds=timeout_seconds)


class MockEmailConfig:
    def __init__(
        self,
        host: str = "",
        port: int = 587,
        sender: str = "",
        recipients: tuple[str, ...] = (),
        enabled: bool = True,
    ):
        self.host = host
        self.port = port
        self.sender = sender
        self.recipients = recipients
        self.enabled = enabled


class MockEmailNotifier:
    def __init__(self, config: MockEmailConfig):
        self.config = config
        self.active = config.enabled
        self.sent: list[tuple[str, str, str | None]] = []

    def send(
        self, title: str, text: str, html_body: str | None = None
    ) -> dict[str, object]:
        self.sent.append((title, text, html_body))
        return {"recipients": len(self.config.recipients)}


def build_email_notification_config(
    host: str = "",
    port: int = 587,
    sender: str = "",
    recipients: tuple[str, ...] = (),
    enabled: bool = False,
):
    return MockEmailConfig(
        host=host,
        port=port,
        sender=sender,
        recipients=recipients,
        enabled=enabled,
    )


class MockSMSConfig:
    def __init__(
        self,
        account_sid: str = "",
        auth_token: str = "",
        from_phone: str = "",
        recipients: tuple[str, ...] = (),
        enabled: bool = True,
    ):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_phone = from_phone
        self.recipients = recipients
        self.enabled = enabled


class MockSMSNotifier:
    def __init__(self, config: MockSMSConfig):
        self.config = config
        self.active = config.enabled
        self.sent: list[tuple[str, str, str | None]] = []

    def send(
        self, title: str, text: str, html_body: str | None = None
    ) -> dict[str, object]:
        self.sent.append((title, text, html_body))
        return {"recipients": len(self.config.recipients)}


def build_sms_notification_config(
    account_sid: str = "",
    auth_token: str = "",
    from_phone: str = "",
    recipients: tuple[str, ...] = (),
    enabled: bool = False,
):
    return MockSMSConfig(
        account_sid=account_sid,
        auth_token=auth_token,
        from_phone=from_phone,
        recipients=recipients,
        enabled=enabled,
    )


class MockTelegramConfig:
    def __init__(
        self,
        bot_token: str = "",
        chat_ids: tuple[str, ...] = (),
        enabled: bool = True,
    ):
        self.bot_token = bot_token
        self.chat_ids = chat_ids
        self.enabled = enabled


class MockTelegramNotifier:
    def __init__(self, config: MockTelegramConfig):
        self.config = config
        self.active = config.enabled
        self.sent: list[tuple[str, str, str | None]] = []

    def send(
        self, title: str, text: str, html_body: str | None = None
    ) -> dict[str, object]:
        self.sent.append((title, text, html_body))
        return {"recipients": len(self.config.chat_ids)}


def build_telegram_notification_config(
    bot_token: str = "", chat_ids: tuple[str, ...] = (), enabled: bool = False
):
    return MockTelegramConfig(bot_token=bot_token, chat_ids=chat_ids, enabled=enabled)


# Set up sys.modules before imports
desktop_mod = types.ModuleType("app.utils.notifications.desktop")
desktop_mod.DesktopConfig = MockDesktopConfig  # type: ignore[attr-defined]
desktop_mod.DesktopNotifier = MockDesktopNotifier  # type: ignore[attr-defined]
desktop_mod.build_desktop_notification_config = build_desktop_notification_config  # type: ignore[attr-defined]

email_mod = types.ModuleType("app.utils.notifications.email")
email_mod.EmailConfig = MockEmailConfig  # type: ignore[attr-defined]
email_mod.EmailNotifier = MockEmailNotifier  # type: ignore[attr-defined]
email_mod.build_email_notification_config = build_email_notification_config  # type: ignore[attr-defined]

sms_mod = types.ModuleType("app.utils.notifications.sms")
sms_mod.SMSConfig = MockSMSConfig  # type: ignore[attr-defined]
sms_mod.SMSNotifier = MockSMSNotifier  # type: ignore[attr-defined]
sms_mod.build_sms_notification_config = build_sms_notification_config  # type: ignore[attr-defined]

tg_mod = types.ModuleType("app.utils.notifications.telegram")
tg_mod.TelegramConfig = MockTelegramConfig  # type: ignore[attr-defined]
tg_mod.TelegramNotifier = MockTelegramNotifier  # type: ignore[attr-defined]
tg_mod.build_telegram_notification_config = build_telegram_notification_config  # type: ignore[attr-defined]

sys.modules["app.utils"] = types.ModuleType("app.utils")
sys.modules["app.utils.notifications"] = types.ModuleType("app.utils.notifications")
sys.modules["app.utils.notifications.desktop"] = desktop_mod
sys.modules["app.utils.notifications.email"] = email_mod
sys.modules["app.utils.notifications.sms"] = sms_mod
sys.modules["app.utils.notifications.telegram"] = tg_mod

from app.services.plugins.providers.desktop import (  # noqa: E402
    plugin as desktop_plugin,
)
from app.services.plugins.providers.email import plugin as email_plugin  # noqa: E402
from app.services.plugins.providers.sms import plugin as sms_plugin  # noqa: E402
from app.services.plugins.providers.telegram import plugin as tg_plugin  # noqa: E402

sys.modules["app.utils.notifications.providers"] = types.ModuleType(
    "app.utils.notifications.providers"
)
sys.modules["app.utils.notifications.providers.desktop"] = types.ModuleType(
    "app.utils.notifications.providers.desktop"
)
sys.modules["app.utils.notifications.providers.desktop.plugin"] = desktop_plugin
sys.modules["app.utils.notifications.providers.email"] = types.ModuleType(
    "app.utils.notifications.providers.email"
)
sys.modules["app.utils.notifications.providers.email.plugin"] = email_plugin
sys.modules["app.utils.notifications.providers.sms"] = types.ModuleType(
    "app.utils.notifications.providers.sms"
)
sys.modules["app.utils.notifications.providers.sms.plugin"] = sms_plugin
sys.modules["app.utils.notifications.providers.telegram"] = types.ModuleType(
    "app.utils.notifications.providers.telegram"
)
sys.modules["app.utils.notifications.providers.telegram.plugin"] = tg_plugin


def test_desktop_provider_lifecycle():
    from app.services.plugins.providers.desktop.example import main as desktop_main
    from app.services.plugins.providers.desktop.plugin import create_provider

    config = MockDesktopConfig(enabled=True)
    scope = EffectScope()
    adapter = create_provider(
        dependencies={},
        config={"configuration": config},
        scope=scope,
    )

    assert adapter.channel == "desktop"
    assert adapter.active is True

    result = adapter.send("Test Title", "Test Text", "<b>HTML</b>")
    assert isinstance(result, NotificationDeliveryResultV1)
    assert result.channel == "desktop"
    assert result.status == "accepted"
    assert result.recipient_count is None

    scope.close()
    assert adapter.active is False
    with pytest.raises(RuntimeError, match="closed"):
        adapter.send("Title", "Text")

    # Invalid configurations
    with pytest.raises(ValueError, match="desktop notification provider requires"):
        create_provider(
            dependencies={"dummy": object()},  # type: ignore[arg-type]
            config={"configuration": config},
            scope=scope,
        )

    with pytest.raises(ValueError, match="desktop notification provider requires"):
        create_provider(
            dependencies={},
            config={"configuration": "invalid_type"},
            scope=scope,
        )

    # Run usage example
    desktop_main()


def test_email_provider_lifecycle():
    from app.services.plugins.providers.email.example import main as email_main
    from app.services.plugins.providers.email.plugin import create_provider

    config = MockEmailConfig(
        host="smtp.example.com",
        port=587,
        sender="noreply@example.com",
        recipients=("a@example.com", "b@example.com"),
        enabled=True,
    )
    scope = EffectScope()
    adapter = create_provider(
        dependencies={},
        config={"configuration": config},
        scope=scope,
    )

    assert adapter.channel == "email"
    assert adapter.active is True

    result = adapter.send("Alert", "Details", "<p>Details</p>")
    assert isinstance(result, NotificationDeliveryResultV1)
    assert result.channel == "email"
    assert result.status == "accepted"
    assert result.recipient_count == 2

    scope.close()
    assert adapter.active is False
    with pytest.raises(RuntimeError, match="closed"):
        adapter.send("Title", "Text")

    # Invalid configurations
    with pytest.raises(ValueError, match="email notification provider requires"):
        create_provider(
            dependencies={"dummy": object()},  # type: ignore[arg-type]
            config={"configuration": config},
            scope=scope,
        )

    with pytest.raises(ValueError, match="email notification provider requires"):
        create_provider(
            dependencies={},
            config={"configuration": "invalid_type"},
            scope=scope,
        )

    # Run usage example
    email_main()


def test_sms_provider_lifecycle():
    from app.services.plugins.providers.sms.example import main as sms_main
    from app.services.plugins.providers.sms.plugin import create_provider

    config = MockSMSConfig(
        account_sid="AC000",
        auth_token="token",
        from_phone="+1000",
        recipients=("+1001", "+1002"),
        enabled=True,
    )
    scope = EffectScope()
    adapter = create_provider(
        dependencies={},
        config={"configuration": config},
        scope=scope,
    )

    assert adapter.channel == "sms"
    assert adapter.active is True

    result = adapter.send("SMS Alert", "Text Body")
    assert isinstance(result, NotificationDeliveryResultV1)
    assert result.channel == "sms"
    assert result.status == "accepted"
    assert result.recipient_count == 2

    scope.close()
    assert adapter.active is False
    with pytest.raises(RuntimeError, match="closed"):
        adapter.send("Title", "Text")

    # Invalid configurations
    with pytest.raises(ValueError, match="sms notification provider requires"):
        create_provider(
            dependencies={"dummy": object()},  # type: ignore[arg-type]
            config={"configuration": config},
            scope=scope,
        )

    with pytest.raises(ValueError, match="sms notification provider requires"):
        create_provider(
            dependencies={},
            config={"configuration": "invalid_type"},
            scope=scope,
        )

    # Run usage example
    sms_main()


def test_telegram_provider_lifecycle():
    from app.services.plugins.providers.telegram.example import main as tg_main
    from app.services.plugins.providers.telegram.plugin import create_provider

    config = MockTelegramConfig(
        bot_token="token",
        chat_ids=("12345", "67890"),
        enabled=True,
    )
    scope = EffectScope()
    adapter = create_provider(
        dependencies={},
        config={"configuration": config},
        scope=scope,
    )

    assert adapter.channel == "telegram"
    assert adapter.active is True

    result = adapter.send("TG Alert", "Message")
    assert isinstance(result, NotificationDeliveryResultV1)
    assert result.channel == "telegram"
    assert result.status == "accepted"
    assert result.recipient_count == 2

    scope.close()
    assert adapter.active is False
    with pytest.raises(RuntimeError, match="closed"):
        adapter.send("Title", "Text")

    # Invalid configurations
    with pytest.raises(ValueError, match="telegram notification provider requires"):
        create_provider(
            dependencies={"dummy": object()},  # type: ignore[arg-type]
            config={"configuration": config},
            scope=scope,
        )

    with pytest.raises(ValueError, match="telegram notification provider requires"):
        create_provider(
            dependencies={},
            config={"configuration": "invalid_type"},
            scope=scope,
        )

    # Run usage example
    tg_main()
