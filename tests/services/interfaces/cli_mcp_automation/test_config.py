"""Unit tests for Unified CLI and MCP Automation configuration."""

import pytest

from app.services.interfaces.cli_mcp_automation.config import (
    CliMcpAutomationConfig,
)


def test_cli_mcp_automation_config_defaults() -> None:
    """Verify default values of CliMcpAutomationConfig."""
    config = CliMcpAutomationConfig()
    assert config.title == "HaruQuantAI Automation Gateway"
    assert config.command_timeout_seconds == 30.0
    assert config.max_durable_jobs == 1000
    assert config.enable_mcp is True


def test_cli_mcp_automation_config_from_dict_valid() -> None:
    """Verify parsing from valid dictionary."""
    data = {
        "title": "Custom Automation Gateway",
        "command_timeout_seconds": 60.0,
        "max_durable_jobs": 500,
        "enable_mcp": False,
    }
    config = CliMcpAutomationConfig.from_dict(data)
    assert config.title == "Custom Automation Gateway"
    assert config.command_timeout_seconds == 60.0
    assert config.max_durable_jobs == 500
    assert config.enable_mcp is False


def test_cli_mcp_automation_config_from_dict_none_or_empty() -> None:
    """Verify parsing from None or empty dictionary returns defaults."""
    assert CliMcpAutomationConfig.from_dict(None) == CliMcpAutomationConfig()
    assert CliMcpAutomationConfig.from_dict({}) == CliMcpAutomationConfig()


def test_cli_mcp_automation_config_unknown_keys_rejected() -> None:
    """Verify unknown keys raise ValueError."""
    with pytest.raises(
        ValueError, match="Unknown CliMcpAutomation configuration keys: invalid_key"
    ):
        CliMcpAutomationConfig.from_dict({"invalid_key": 123})


def test_cli_mcp_automation_config_invalid_bounds() -> None:
    """Verify out-of-bounds parameters raise ValueError."""
    with pytest.raises(ValueError, match="command_timeout_seconds must be positive"):
        CliMcpAutomationConfig.from_dict({"command_timeout_seconds": 0.0})

    with pytest.raises(ValueError, match="command_timeout_seconds must be positive"):
        CliMcpAutomationConfig.from_dict({"command_timeout_seconds": -5.0})

    with pytest.raises(ValueError, match="max_durable_jobs must be positive"):
        CliMcpAutomationConfig.from_dict({"max_durable_jobs": 0})
