"""Tests for notification.delivery.email provider."""

# ruff: noqa: INP001
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from app.capabilities.notification.delivery.v1 import (
    NotificationDeliveryCapabilityV1,
    NotificationDeliveryResultV1,
)
from app.kernel.effects import EffectScope
from app.kernel.manifests import load_manifest
from app.utils.errors.exceptions import ConfigurationError
from app.utils.notifications.email import build_email_notification_config
from app.utils.notifications.providers.email.plugin import create_provider
from tests.removability.harness import run_in_fresh_process


def test_manifest_structure() -> None:
    """Verify email provider manifest matches specification."""
    manifest_path = (
        Path(__file__).resolve().parents[4]
        / "app"
        / "utils"
        / "notifications"
        / "providers"
        / "email"
        / "manifest.toml"
    )
    manifest = load_manifest(manifest_path)
    assert str(manifest.provider_id) == "notification.delivery.email"
    assert manifest.entry_point == (
        "app.utils.notifications.providers.email.plugin:create_provider"
    )
    assert len(manifest.provides) == 1
    assert str(manifest.provides[0].capability_id) == "notification.delivery.v1"
    assert manifest.lifecycle == "scoped"
    assert manifest.reload == "config_restart"


def test_no_import_io() -> None:
    """Verify importing provider plugin initiates no I/O."""
    script = """
import sys
import app.utils.notifications.providers.email.plugin as plugin
assert plugin is not None
"""
    repo_root = Path(__file__).resolve().parents[4]
    res = run_in_fresh_process(repository_root=repo_root, script=script)
    assert res.returncode == 0, res.stderr


def test_factory_rejection_and_acceptance() -> None:
    """Verify factory validates dependencies and configuration."""
    scope = EffectScope()
    config = build_email_notification_config(
        host="smtp.example.com",
        port=587,
        sender="noreply@example.com",
        recipients=("user@example.com",),
        enabled=False,
    )

    # Rejection: invalid config key
    with pytest.raises(
        ValueError,
        match="email notification provider requires only 'configuration'",
    ):
        create_provider(dependencies={}, config={"invalid": 123}, scope=scope)

    # Success: valid config
    adapter = create_provider(
        dependencies={}, config={"configuration": config}, scope=scope
    )
    assert isinstance(adapter, NotificationDeliveryCapabilityV1)
    assert adapter.channel == "email"
    assert adapter.active is False
    scope.close()


def test_send_mapping_parity_with_mock() -> None:
    """Verify send delegates to SMTP and wraps result in NotificationDeliveryResultV1."""
    config = build_email_notification_config(
        host="smtp.example.com",
        port=587,
        sender="sender@example.com",
        recipients=("r1@example.com", "r2@example.com"),
        enabled=True,
    )
    scope = EffectScope()
    adapter = create_provider(
        dependencies={}, config={"configuration": config}, scope=scope
    )
    assert adapter.active is True

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.send_message.return_value = {}

    with patch("smtplib.SMTP", return_value=mock_client):
        result = adapter.send("Test Title", "Test Message", "<p>HTML</p>")

    assert isinstance(result, NotificationDeliveryResultV1)
    assert result.channel == "email"
    assert result.status == "accepted"
    assert result.recipient_count == 2
    mock_client.send_message.assert_called_once()
    scope.close()


def test_close_and_lifecycle() -> None:
    """Verify closing adapter marks it inactive and prevents subsequent sends."""
    config = build_email_notification_config(
        host="smtp.example.com",
        port=587,
        sender="sender@example.com",
        recipients=("r1@example.com",),
        enabled=True,
    )
    scope = EffectScope()
    adapter = create_provider(
        dependencies={}, config={"configuration": config}, scope=scope
    )
    assert bool(adapter.active) is True

    adapter.close()
    assert bool(adapter.active) is False
    with pytest.raises(RuntimeError, match="Email delivery transport is closed"):
        adapter.send("Title", "Body")
    scope.close()


def test_no_fallback_behavior() -> None:
    """Verify sending on disabled configuration raises ConfigurationError without fallback."""
    config = build_email_notification_config(
        host="smtp.example.com",
        port=587,
        sender="sender@example.com",
        recipients=("r1@example.com",),
        enabled=False,
    )
    scope = EffectScope()
    adapter = create_provider(
        dependencies={}, config={"configuration": config}, scope=scope
    )
    with pytest.raises(ConfigurationError, match="NOTIFICATION_CHANNEL_UNAVAILABLE"):
        adapter.send("Title", "Body")
    scope.close()
