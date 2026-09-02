"""Tests for strict Plugin Lifecycle configuration."""

from pathlib import Path

import pytest
from app.services.plugins.lifecycle.config import PluginLifecycleConfig


def test_config_requires_only_non_blank_database_path() -> None:
    """Verify the explicit database binding is parsed without I/O."""
    config = PluginLifecycleConfig.from_dict({"database_path": "state/plugins.db"})
    assert config.database_path == Path("state/plugins.db")

    with pytest.raises(ValueError, match="requires database_path"):
        PluginLifecycleConfig.from_dict(None)
    with pytest.raises(ValueError, match="non-blank string"):
        PluginLifecycleConfig.from_dict({"database_path": " "})
    with pytest.raises(TypeError, match="non-blank string"):
        PluginLifecycleConfig.from_dict({"database_path": 12})
    with pytest.raises(ValueError, match="Unknown Plugin Lifecycle"):
        PluginLifecycleConfig.from_dict(
            {"database_path": "state.db", "unexpected": True}
        )
