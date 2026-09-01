"""Tests for Plugin Manifests configuration parser."""

import pytest
from app.services.plugins.manifests.config import PluginManifestsConfig


def test_config_defaults() -> None:
    """Verify default values when parsed from empty data."""
    config = PluginManifestsConfig.from_dict({})
    assert config.max_package_size_bytes == 50 * 1024 * 1024
    assert config.max_file_count == 1000
    assert config.strict_signatures is False

    none_config = PluginManifestsConfig.from_dict(None)
    assert none_config == config


def test_config_custom_values() -> None:
    """Verify custom valid configuration values."""
    data = {
        "max_package_size_bytes": 10 * 1024 * 1024,
        "max_file_count": 500,
        "strict_signatures": True,
    }
    config = PluginManifestsConfig.from_dict(data)
    assert config.max_package_size_bytes == 10 * 1024 * 1024
    assert config.max_file_count == 500
    assert config.strict_signatures is True


def test_config_unknown_keys_rejected() -> None:
    """Verify rejection of unknown configuration keys."""
    with pytest.raises(
        ValueError, match="Unknown Plugin Manifests configuration keys: extra_field"
    ):
        PluginManifestsConfig.from_dict({"extra_field": 123})


def test_config_invalid_values_rejected() -> None:
    """Verify rejection of non-positive limits."""
    with pytest.raises(ValueError, match="max_package_size_bytes must be positive"):
        PluginManifestsConfig.from_dict({"max_package_size_bytes": 0})

    with pytest.raises(ValueError, match="max_package_size_bytes must be positive"):
        PluginManifestsConfig.from_dict({"max_package_size_bytes": -100})

    with pytest.raises(ValueError, match="max_file_count must be positive"):
        PluginManifestsConfig.from_dict({"max_file_count": 0})
