"""Unit tests for LocalAccessHealthConfig."""

from __future__ import annotations

from app.services.workspace.local_access_health.config import (
    LocalAccessHealthConfig,
)


def test_config_defaults() -> None:
    """Test default values for LocalAccessHealthConfig."""
    config = LocalAccessHealthConfig()
    assert config.default_session_ttl_seconds == 3600
    assert config.enforce_loopback is True


def test_config_custom_values() -> None:
    """Test custom values for LocalAccessHealthConfig."""
    config = LocalAccessHealthConfig(
        default_session_ttl_seconds=7200,
        enforce_loopback=False,
    )
    assert config.default_session_ttl_seconds == 7200
    assert config.enforce_loopback is False
