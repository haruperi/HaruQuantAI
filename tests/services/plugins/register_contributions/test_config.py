"""Tests for Plugin Contributions configuration."""

from __future__ import annotations

import pytest
from app.services.plugins.register_contributions.config import (
    PluginContributionsConfig,
)


def test_default_config() -> None:
    """Verify default configuration values."""
    config = PluginContributionsConfig()
    assert config.strict_contract_tests is True
    assert config.max_contributions_per_plugin == 100


def test_from_dict_none() -> None:
    """Verify parsing None returns defaults."""
    config = PluginContributionsConfig.from_dict(None)
    assert config.strict_contract_tests is True
    assert config.max_contributions_per_plugin == 100


def test_from_dict_custom() -> None:
    """Verify parsing valid custom configuration values."""
    data = {
        "strict_contract_tests": False,
        "max_contributions_per_plugin": 50,
    }
    config = PluginContributionsConfig.from_dict(data)
    assert config.strict_contract_tests is False
    assert config.max_contributions_per_plugin == 50


def test_from_dict_unknown_keys() -> None:
    """Verify unknown keys are strictly rejected with ValueError."""
    data = {
        "strict_contract_tests": True,
        "unrecognized_option": 123,
    }
    with pytest.raises(
        ValueError, match="Unknown Plugin Contributions configuration keys"
    ):
        PluginContributionsConfig.from_dict(data)


def test_from_dict_invalid_max_contributions() -> None:
    """Verify non-positive max_contributions_per_plugin is rejected."""
    with pytest.raises(
        ValueError, match="max_contributions_per_plugin must be positive"
    ):
        PluginContributionsConfig.from_dict({"max_contributions_per_plugin": 0})

    with pytest.raises(
        ValueError, match="max_contributions_per_plugin must be positive"
    ):
        PluginContributionsConfig.from_dict({"max_contributions_per_plugin": -10})
