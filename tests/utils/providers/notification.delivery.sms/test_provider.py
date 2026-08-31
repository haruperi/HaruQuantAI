"""Tests for notification.delivery.sms provider."""

# ruff: noqa: INP001
import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from app.contracts.notification.delivery.v1 import (
    NotificationDeliveryCapabilityV1,
    NotificationDeliveryResultV1,
)
from app.kernel.effects import EffectScope
from app.kernel.manifests import load_manifest
from app.utils.errors.exceptions import ConfigurationError
from app.utils.notifications.providers.sms.plugin import create_provider
from app.utils.notifications.sms import build_sms_notification_config
from tests.removability.harness import run_in_fresh_process


def test_manifest_structure() -> None:
    """Verify SMS provider manifest matches specification."""
    manifest_path = (
        Path(__file__).resolve().parents[4]
        / "app"
        / "utils"
        / "notifications"
        / "providers"
        / "sms"
        / "manifest.toml"
    )
    manifest = load_manifest(manifest_path)
    assert str(manifest.provider_id) == "notification.delivery.sms"
    assert manifest.entry_point == (
        "app.utils.notifications.providers.sms.plugin:create_provider"
    )
    assert len(manifest.provides) == 1
    assert str(manifest.provides[0].capability_id) == "notification.delivery.v1"
    assert manifest.lifecycle == "scoped"
    assert manifest.reload == "config_restart"


def test_no_import_io() -> None:
    """Verify importing provider plugin initiates no I/O."""
    script = """
import sys
import app.utils.notifications.providers.sms.plugin as plugin
assert plugin is not None
"""
    repo_root = Path(__file__).resolve().parents[4]
    res = run_in_fresh_process(repository_root=repo_root, script=script)
    assert res.returncode == 0, res.stderr


def test_factory_rejection_and_acceptance() -> None:
    """Verify factory validates dependencies and configuration."""
    scope = EffectScope()
    config = build_sms_notification_config(
        account_sid="AC00000000000000000000000000000000",  # pragma: allowlist secret
        auth_token="dummy_token",
        from_phone="+15550001",
        recipients=("+15550002",),
        enabled=False,
    )

    with pytest.raises(
        ValueError,
        match="sms notification provider requires only 'configuration'",
    ):
        create_provider(dependencies={}, config={"invalid": 123}, scope=scope)

    adapter = create_provider(
        dependencies={}, config={"configuration": config}, scope=scope
    )
    assert isinstance(adapter, NotificationDeliveryCapabilityV1)
    assert adapter.channel == "sms"
    assert bool(adapter.active) is False
    scope.close()


def test_send_mapping_parity_with_mock() -> None:
    """Verify send delegates to HTTPS gateway and wraps result in NotificationDeliveryResultV1."""
    config = build_sms_notification_config(
        account_sid="AC00000000000000000000000000000000",  # pragma: allowlist secret
        auth_token="dummy_token",
        from_phone="+15550001",
        recipients=("+15550002", "+15550003"),
        enabled=True,
    )
    scope = EffectScope()
    adapter = create_provider(
        dependencies={}, config={"configuration": config}, scope=scope
    )
    assert bool(adapter.active) is True

    class _FakeResponse:
        def __enter__(self) -> io.BytesIO:
            return io.BytesIO(json.dumps({"sid": "SM1234567890abcdef"}).encode())

        def __exit__(self, *args: object) -> None:
            pass

    with patch("urllib.request.urlopen", side_effect=lambda *a, **kw: _FakeResponse()):
        result = adapter.send("Title", "SMS body text")

    assert isinstance(result, NotificationDeliveryResultV1)
    assert result.channel == "sms"
    assert result.status == "accepted"
    assert result.recipient_count == 2
    scope.close()


def test_close_and_lifecycle() -> None:
    """Verify closing adapter marks it inactive and prevents subsequent sends."""
    config = build_sms_notification_config(
        account_sid="AC00000000000000000000000000000000",  # pragma: allowlist secret
        auth_token="dummy_token",
        from_phone="+15550001",
        recipients=("+15550002",),
        enabled=True,
    )
    scope = EffectScope()
    adapter = create_provider(
        dependencies={}, config={"configuration": config}, scope=scope
    )
    assert bool(adapter.active) is True

    adapter.close()
    assert bool(adapter.active) is False
    with pytest.raises(RuntimeError, match="SMS delivery transport is closed"):
        adapter.send("Title", "Body")
    scope.close()


def test_no_fallback_behavior() -> None:
    """Verify sending on disabled configuration raises ConfigurationError without fallback."""
    config = build_sms_notification_config(
        account_sid="AC00000000000000000000000000000000",  # pragma: allowlist secret
        auth_token="dummy_token",
        from_phone="+15550001",
        recipients=("+15550002",),
        enabled=False,
    )
    scope = EffectScope()
    adapter = create_provider(
        dependencies={}, config={"configuration": config}, scope=scope
    )
    with pytest.raises(ConfigurationError, match="NOTIFICATION_CHANNEL_UNAVAILABLE"):
        adapter.send("Title", "Body")
    scope.close()
