"""Unit tests for PluginManifestsConfig."""

import pytest
from app.services.plugins.declare_manifests.config import PluginManifestsConfig


def test_config_defaults() -> None:
    """Verify default configuration limits."""
    config = PluginManifestsConfig()
    assert config.max_package_size_bytes == 50 * 1024 * 1024
    assert config.max_file_count == 1000
    assert not config.strict_signatures


def test_config_from_dict_empty_or_none() -> None:
    """Verify parsing empty or None dictionary returns defaults."""
    assert PluginManifestsConfig.from_dict(None) == PluginManifestsConfig()
    assert PluginManifestsConfig.from_dict({}) == PluginManifestsConfig()


def test_config_from_dict_valid() -> None:
    """Verify parsing valid explicit configuration."""
    data = {
        "max_package_size_bytes": 10 * 1024 * 1024,
        "max_file_count": 50,
        "strict_signatures": True,
    }
    config = PluginManifestsConfig.from_dict(data)
    assert config.max_package_size_bytes == 10 * 1024 * 1024
    assert config.max_file_count == 50
    assert config.strict_signatures is True


def test_config_from_dict_unknown_keys() -> None:
    """Verify rejection of unknown configuration keys."""
    with pytest.raises(ValueError, match="Unknown Plugin Manifests configuration keys"):
        PluginManifestsConfig.from_dict({"unknown_setting": 123})


def test_config_from_dict_invalid_bounds() -> None:
    """Verify rejection of non-positive limit values."""
    with pytest.raises(ValueError, match="max_package_size_bytes must be positive"):
        PluginManifestsConfig.from_dict({"max_package_size_bytes": 0})

    with pytest.raises(ValueError, match="max_package_size_bytes must be positive"):
        PluginManifestsConfig.from_dict({"max_package_size_bytes": -100})

    with pytest.raises(ValueError, match="max_file_count must be positive"):
        PluginManifestsConfig.from_dict({"max_file_count": 0})
