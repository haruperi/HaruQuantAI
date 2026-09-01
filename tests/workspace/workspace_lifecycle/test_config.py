"""Tests for WorkspaceLifecycleConfig."""

from app.services.workspace.workspace_lifecycle.config import (
    WorkspaceLifecycleConfig,
)


def test_workspace_lifecycle_config_defaults() -> None:
    """Test default values of WorkspaceLifecycleConfig."""
    config = WorkspaceLifecycleConfig()
    assert config.auto_migrate is True
    assert config.busy_timeout_seconds == 5.0
    assert config.staged_grace_period_seconds == 86400.0


def test_workspace_lifecycle_config_custom_values() -> None:
    """Test creating WorkspaceLifecycleConfig with custom options."""
    config = WorkspaceLifecycleConfig(
        auto_migrate=False,
        busy_timeout_seconds=10.0,
        staged_grace_period_seconds=3600.0,
    )
    assert config.auto_migrate is False
    assert config.busy_timeout_seconds == 10.0
    assert config.staged_grace_period_seconds == 3600.0
