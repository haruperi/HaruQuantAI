"""Unit tests for Notification service, template registry, and feature."""

from __future__ import annotations

import asyncio
import sys
import urllib.error
from unittest.mock import MagicMock, patch

import pytest
from app.contracts.workspace import (
    WORKSPACE_NOTIFICATIONS,
    ConfigurationError,
    NotificationChannel,
)
from app.kernel.bootstrapper import Runtime
from app.services.workspace.notifications import (
    SPEC,
    NotificationConfig,
    NotificationService,
    TemplateRegistry,
    feature,
)


def test_notification_config_validation() -> None:
    """Verify notification configuration bounds checks."""
    config = NotificationConfig(default_timeout_seconds=60.0)
    assert config.default_timeout_seconds == 60.0
    assert config.enable_telegram is True
    assert config.enable_desktop is True

    with pytest.raises(ValueError, match="default_timeout_seconds must be positive"):
        NotificationConfig(default_timeout_seconds=0.0)


def test_notification_dispatch_and_redaction() -> None:
    """Verify notification sending and credential redaction."""
    service = NotificationService(NotificationConfig())

    receipt = service.send_notification(
        channel=NotificationChannel.EMAIL,
        recipient="trader@haruquant.internal",
        title="Optimization Done",
        body="Walk-forward completed.",
        metadata={"api_key": "secret-12345", "token": "bearer-token-abc"},
    )
    assert receipt.delivered is False
    assert receipt.error == "skipped: SMTP server not configured"
    assert len(receipt.message_id) > 0


def test_template_registry_built_ins_and_rendering() -> None:
    """Verify TemplateRegistry built-in templates and variable interpolation."""
    registry = TemplateRegistry()
    names = registry.names()

    assert "trading_signal" in names
    assert "system_alert" in names
    assert "custom_message" in names
    assert len(names) >= 27

    # Render trading_signal
    rendered = registry.render(
        "trading_signal",
        {
            "symbol": "EURUSD",
            "signal_type": "BUY",
            "entry_price": "1.0850",
            "stop_loss": "1.0800",
            "stop_loss_pips": "50",
            "take_profit": "1.0950",
            "take_profit_pips": "100",
            "lots": "0.5",
            "strategy": "TrendFollower",
            "strength": "High",
            "adr": "85 pips",
            "range": "65",
            "current_var": "1.2%",
            "proposed_var": "1.5%",
            "var_difference": "0.3",
            "timestamp": "2026-09-20 10:00:00 UTC",
        },
    )
    assert "BUY EURUSD @ 1.0850" in rendered["text"]
    assert "Trading Signal: EURUSD BUY" == rendered["title"]
    assert "<p>BUY EURUSD @ 1.0850<br>" in rendered["html"]


def test_template_registry_html_escaping() -> None:
    """Verify TemplateRegistry escapes dangerous HTML characters in html body."""
    registry = TemplateRegistry()
    rendered = registry.render(
        "custom_message",
        {
            "title": "Alert <Test>",
            "body": "<script>alert('pwned')</script> & safe",
        },
    )
    assert rendered["title"] == "Alert <Test>"
    assert rendered["text"] == "<script>alert('pwned')</script> & safe"
    assert (
        "&lt;script&gt;alert(&#x27;pwned&#x27;)&lt;/script&gt; &amp; safe"
        in rendered["html"]
    )


def test_template_registry_missing_field_and_unknown_errors() -> None:
    """Verify ConfigurationError on missing variables or unknown templates."""
    registry = TemplateRegistry()

    with pytest.raises(ConfigurationError, match="NOTIFICATION_TEMPLATE_UNKNOWN"):
        registry.render("non_existent_template", {})

    with pytest.raises(ConfigurationError, match="NOTIFICATION_TEMPLATE_VALUE_MISSING"):
        registry.render("trading_signal", {"symbol": "EURUSD"})


def test_template_registry_custom_registration() -> None:
    """Verify registering valid and invalid custom templates."""
    registry = TemplateRegistry()

    # Valid custom registration
    registry.register(
        name="custom_summary",
        title="Summary: {date}",
        text="Daily total: {total}",
        html_body="<h3>Total: {total}</h3>",
    )
    assert "custom_summary" in registry.names()
    rendered = registry.render(
        "custom_summary", {"date": "2026-09-20", "total": "$500"}
    )
    assert rendered["title"] == "Summary: 2026-09-20"
    assert rendered["text"] == "Daily total: $500"

    # Invalid: built-in name collision
    with pytest.raises(ConfigurationError, match="NOTIFICATION_TEMPLATE_INVALID"):
        registry.register("trading_signal", "Title", "Text", "<p>HTML</p>")

    # Invalid: empty title/text
    with pytest.raises(ConfigurationError, match="NOTIFICATION_TEMPLATE_INVALID"):
        registry.register("bad_tpl", "", "", "")


def test_send_templated_notification() -> None:
    """Verify service level templated notification dispatch."""
    service = NotificationService(NotificationConfig())
    receipt = service.send_templated_notification(
        channel=NotificationChannel.DESKTOP,
        recipient="local_user",
        template_name="system_alert",
        values={
            "level": "INFO",
            "message": "Optimization started",
            "details": "Population size: 50",
            "time": "2026-09-20 10:00:00",
            "timestamp": "2026-09-20 10:00:00",
            "component": "GeneticEngine",
            "status": "Running",
        },
        metadata={"duration_seconds": 0.1, "sound_enabled": False},
    )
    if sys.platform == "win32":
        assert receipt.delivered is True
        assert receipt.error is None
    else:
        assert receipt.delivered is False
        assert receipt.error is not None and "skipped:" in receipt.error
    assert bool(receipt.message_id)


def test_telegram_dispatch_failure_isolation() -> None:
    """Verify Telegram failures are isolated and returned as delivery errors."""
    service = NotificationService(NotificationConfig())

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.URLError("Network unreachable")
        receipt = service.send_notification(
            channel=NotificationChannel.TELEGRAM,
            recipient="5398524142",
            title="Alert",
            body="Message",
            metadata={"bot_token": "fake_token_123"},
        )
        assert receipt.delivered is False
        assert receipt.error is not None
        assert "Network unreachable" in receipt.error


def test_email_dispatch_failure_isolation() -> None:
    """Verify SMTP failures are isolated and returned as delivery errors."""
    service = NotificationService(NotificationConfig())

    with patch("smtplib.SMTP") as mock_smtp:
        mock_instance = MagicMock()
        mock_instance.__enter__.return_value = mock_instance
        mock_instance.login.side_effect = OSError("Connection refused")
        mock_smtp.return_value = mock_instance

        receipt = service.send_notification(
            channel=NotificationChannel.EMAIL,
            recipient="trader@haruquant.internal",
            title="Subject",
            body="Body",
            metadata={
                "smtp_server": "smtp.invalid.internal",
                "username": "user",
                "password": "pwd",
            },
        )
        assert receipt.delivered is False
        assert receipt.error is not None
        assert "Connection refused" in receipt.error


def test_channel_disabled_by_configuration() -> None:
    """Verify disabled notification channels yield explicit error outcomes (FR-WORKSPACE-004)."""
    cfg = NotificationConfig(
        enable_email=False, enable_telegram=False, enable_desktop=False
    )
    service = NotificationService(cfg)

    email_rcpt = service.send_notification(
        channel=NotificationChannel.EMAIL,
        recipient="user@internal",
        title="Test",
        body="Test",
    )
    assert email_rcpt.delivered is False
    assert "disabled by configuration" in (email_rcpt.error or "")

    tg_rcpt = service.send_notification(
        channel=NotificationChannel.TELEGRAM,
        recipient="12345",
        title="Test",
        body="Test",
    )
    assert tg_rcpt.delivered is False
    assert "disabled by configuration" in (tg_rcpt.error or "")

    desk_rcpt = service.send_notification(
        channel=NotificationChannel.DESKTOP,
        recipient="local",
        title="Test",
        body="Test",
    )
    assert desk_rcpt.delivered is False
    assert "disabled by configuration" in (desk_rcpt.error or "")


def test_pause_gate_resolution() -> None:
    """Verify human-in-the-loop pause gate wait and resume."""
    service = NotificationService(NotificationConfig())

    receipt = service.send_notification(
        channel=NotificationChannel.SOUND,
        recipient="desk-bell",
        title="Action Required",
        body="Review generated candidate before proceeding",
        require_user_action=True,
    )

    # Immediately unpause
    service.resume_user_action(receipt.message_id)
    assert service.wait_for_user_action(receipt.message_id, timeout_seconds=1.0) is True

    # Unknown prompt returns False
    assert (
        service.wait_for_user_action("non-existent-gate", timeout_seconds=0.1) is False
    )


def test_notification_lifecycle_within_runtime() -> None:
    """Verify feature mounting, capability publishing, and shutdown."""
    feat = feature()
    assert feat.spec == SPEC

    async def _test() -> None:
        async with Runtime((feature,)) as runtime:
            notif = runtime.require(WORKSPACE_NOTIFICATIONS)
            with patch("urllib.request.urlopen") as mock_urlopen:
                mock_resp = MagicMock()
                mock_resp.status = 200
                mock_urlopen.return_value.__enter__.return_value = mock_resp
                receipt = notif.send_notification(
                    channel=NotificationChannel.WEBHOOK,
                    recipient="https://alerts.internal/hook",
                    title="Webhook Alert",
                    body="Testing webhook dispatch",
                )
                assert receipt.delivered is True

    asyncio.run(_test())


def test_notifications_bounded_deque_eviction() -> None:
    """Verify sent messages list is bounded by deque maxlen 1000."""
    service = NotificationService(NotificationConfig())
    for i in range(1050):
        service.send_notification(
            channel=NotificationChannel.SOUND,
            recipient="chime",
            title=f"Ping {i}",
            body="Heartbeat",
        )

    assert len(service._sent_messages) == 1000
    # Oldest message retained should be Ping 50
    assert bool(service._sent_messages[0].message_id)


def test_sound_and_webhook_dispatch() -> None:
    """Verify sound alert and webhook dispatch with skip handling."""
    service = NotificationService(NotificationConfig())

    # 1. Unconfigured webhook returns skipped
    wh_skipped = service.send_notification(
        channel=NotificationChannel.WEBHOOK,
        recipient="",
        title="No URL",
        body="Test",
    )
    assert wh_skipped.delivered is False
    assert wh_skipped.error == "skipped: webhook URL not configured"

    # 2. Configured webhook succeeds with HTTP 200 mock
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        wh_ok = service.send_notification(
            channel=NotificationChannel.WEBHOOK,
            recipient="https://example.internal/webhook",
            title="Alert",
            body="Payload",
            metadata={"headers": {"X-Custom": "123"}},
        )
        assert wh_ok.delivered is True
        assert wh_ok.error is None

    # 3. Sound dispatch
    sound_rcpt = service.send_notification(
        channel=NotificationChannel.SOUND,
        recipient="speaker",
        title="Ping",
        body="Ping body",
    )
    if sys.platform == "win32":
        assert sound_rcpt.delivered is True
        assert sound_rcpt.error is None
    else:
        assert sound_rcpt.delivered is False
        assert sound_rcpt.error is not None and "skipped:" in sound_rcpt.error
