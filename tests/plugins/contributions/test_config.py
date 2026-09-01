"""Tests for Plugin Contributions configuration parser."""

import pytest
from app.services.plugins.contributions.config import PluginContributionsConfig


def test_config_defaults() -> None:
    """Verify default values when parsed from empty data."""
    config = PluginContributionsConfig.from_dict({})
    assert config.strict_contract_tests is True
    assert config.max_contributions_per_plugin == 100

    none_config = PluginContributionsConfig.from_dict(None)
    assert none_config == config


def test_config_custom_values() -> None:
    """Verify custom valid configuration values."""
    data = {
        "strict_contract_tests": False,
        "max_contributions_per_plugin": 25,
    }
    config = PluginContributionsConfig.from_dict(data)
    assert config.strict_contract_tests is False
    assert config.max_contributions_per_plugin == 25


def test_config_unknown_keys_rejected() -> None:
    """Verify rejection of unknown configuration keys."""
    with pytest.raises(
        ValueError, match="Unknown Plugin Contributions configuration keys: extra"
    ):
        PluginContributionsConfig.from_dict({"extra": 123})


def test_config_invalid_values_rejected() -> None:
    """Verify rejection of non-positive limits."""
    with pytest.raises(
        ValueError, match="max_contributions_per_plugin must be positive"
    ):
        PluginContributionsConfig.from_dict({"max_contributions_per_plugin": 0})

    with pytest.raises(
        ValueError, match="max_contributions_per_plugin must be positive"
    ):
        PluginContributionsConfig.from_dict({"max_contributions_per_plugin": -5})
