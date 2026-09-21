"""Tests for command automator configuration."""

from __future__ import annotations

import pytest
from app.services.gateway.command_automator import CommandAutomationConfig


def test_command_automator_config_defaults() -> None:
    """Verify default configuration attributes."""
    config = CommandAutomationConfig()
    assert config.command_timeout_s == 60.0
    assert config.max_batch_lines == 1000


def test_command_automator_config_validation() -> None:
    """Verify validation on invalid parameter values."""
    with pytest.raises(ValueError, match="command_timeout_s must be > 0"):
        CommandAutomationConfig(command_timeout_s=0.0)

    with pytest.raises(ValueError, match="max_batch_lines must be > 0"):
        CommandAutomationConfig(max_batch_lines=-1)
