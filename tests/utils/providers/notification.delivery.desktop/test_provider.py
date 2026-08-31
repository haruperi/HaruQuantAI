"""Tests for notification.delivery.desktop provider."""

# ruff: noqa: INP001
import subprocess
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
from app.utils.notifications.desktop import build_desktop_notification_config
from app.utils.notifications.providers.desktop.plugin import create_provider
from tests.removability.harness import run_in_fresh_process


def test_manifest_structure() -> None:
    """Verify Desktop provider manifest matches specification."""
    manifest_path = (
        Path(__file__).resolve().parents[4]
        / "app"
        / "utils"
        / "notifications"
        / "providers"
        / "desktop"
        / "manifest.toml"
    )
    manifest = load_manifest(manifest_path)
    assert str(manifest.provider_id) == "notification.delivery.desktop"
    assert manifest.entry_point == (
        "app.utils.notifications.providers.desktop.plugin:create_provider"
    )
    assert len(manifest.provides) == 1
    assert str(manifest.provides[0].capability_id) == "notification.delivery.v1"
    assert manifest.lifecycle == "scoped"
    assert manifest.reload == "config_restart"


def test_no_import_io() -> None:
    """Verify importing provider plugin initiates no I/O."""
    script = """
import sys
import app.utils.notifications.providers.desktop.plugin as plugin
assert plugin is not None
"""
    repo_root = Path(__file__).resolve().parents[4]
    res = run_in_fresh_process(repository_root=repo_root, script=script)
    assert res.returncode == 0, res.stderr


def test_factory_rejection_and_acceptance() -> None:
    """Verify factory validates dependencies and configuration."""
    scope = EffectScope()
    config = build_desktop_notification_config(enabled=False)

    with pytest.raises(
        ValueError,
        match="desktop notification provider requires only 'configuration'",
    ):
        create_provider(dependencies={}, config={"invalid": 123}, scope=scope)

    adapter = create_provider(
        dependencies={}, config={"configuration": config}, scope=scope
    )
    assert isinstance(adapter, NotificationDeliveryCapabilityV1)
    assert adapter.channel == "desktop"
    assert bool(adapter.active) is False
    scope.close()


def test_send_mapping_parity_with_mock() -> None:
    """Verify send delegates to platform command and wraps result in NotificationDeliveryResultV1."""
    config = build_desktop_notification_config(enabled=True)
    scope = EffectScope()
    adapter = create_provider(
        dependencies={}, config={"configuration": config}, scope=scope
    )
    assert bool(adapter.active) is True

    mock_process = subprocess.CompletedProcess(
        args=["powershell"], returncode=0, stdout="", stderr=""
    )
    with patch("subprocess.run", return_value=mock_process):
        result = adapter.send("Title", "Desktop message")

    assert isinstance(result, NotificationDeliveryResultV1)
    assert result.channel == "desktop"
    assert result.status == "accepted"
    assert result.recipient_count is None
    scope.close()


def test_close_and_lifecycle() -> None:
    """Verify closing adapter marks it inactive and prevents subsequent sends."""
    config = build_desktop_notification_config(enabled=True)
    scope = EffectScope()
    adapter = create_provider(
        dependencies={}, config={"configuration": config}, scope=scope
    )
    assert bool(adapter.active) is True

    adapter.close()
    assert bool(adapter.active) is False
    with pytest.raises(RuntimeError, match="Desktop delivery transport is closed"):
        adapter.send("Title", "Body")
    scope.close()


def test_no_fallback_behavior() -> None:
    """Verify sending on disabled configuration raises ConfigurationError without fallback."""
    config = build_desktop_notification_config(enabled=False)
    scope = EffectScope()
    adapter = create_provider(
        dependencies={}, config={"configuration": config}, scope=scope
    )
    with pytest.raises(ConfigurationError, match="NOTIFICATION_CHANNEL_UNAVAILABLE"):
        adapter.send("Title", "Body")
    scope.close()
