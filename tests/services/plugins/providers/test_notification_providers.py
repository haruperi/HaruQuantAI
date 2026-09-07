"""Tests for notification delivery providers (desktop, email, sms, telegram)."""

from __future__ import annotations

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


def test_desktop_provider_lifecycle():
    from app.services.plugins.providers.desktop.example import main as desktop_main
    from app.services.plugins.providers.desktop.plugin import create_provider

    config = MockDesktopConfig(enabled=True)
    notifier = MockDesktopNotifier(config)
    scope = EffectScope()
    adapter = create_provider(
        dependencies={},
        config={"configuration": notifier},
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
            config={"configuration": notifier},
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
    notifier = MockEmailNotifier(config)
    scope = EffectScope()
    adapter = create_provider(
        dependencies={},
        config={"configuration": notifier},
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
            config={"configuration": notifier},
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
    notifier = MockSMSNotifier(config)
    scope = EffectScope()
    adapter = create_provider(
        dependencies={},
        config={"configuration": notifier},
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
            config={"configuration": notifier},
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
    notifier = MockTelegramNotifier(config)
    scope = EffectScope()
    adapter = create_provider(
        dependencies={},
        config={"configuration": notifier},
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
            config={"configuration": notifier},
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
