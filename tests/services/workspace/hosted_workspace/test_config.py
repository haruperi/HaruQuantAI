"""Unit tests for HostedWorkspaceConfig."""

from app.services.workspace.hosted_workspace.config import (
    HostedWorkspaceConfig,
)


def test_hosted_workspace_config_defaults() -> None:
    """Verify default configuration values."""
    config = HostedWorkspaceConfig()
    assert config.default_decision_ttl_seconds == 3600
    assert config.enforce_scope_isolation is True


def test_hosted_workspace_config_custom() -> None:
    """Verify custom configuration instantiation."""
    config = HostedWorkspaceConfig(
        default_decision_ttl_seconds=7200,
        enforce_scope_isolation=False,
    )
    assert config.default_decision_ttl_seconds == 7200
    assert config.enforce_scope_isolation is False
