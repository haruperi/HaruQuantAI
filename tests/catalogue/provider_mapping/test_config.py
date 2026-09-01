"""Unit tests for ProviderMappingConfig."""

from pathlib import Path

from app.services.catalogue.provider_mapping.config import ProviderMappingConfig


def test_config_defaults() -> None:
    """Test default settings for ProviderMappingConfig."""
    cfg = ProviderMappingConfig()
    assert cfg.database_path is None
    assert cfg.auto_migrate is True


def test_config_custom_values(tmp_path: Path) -> None:
    """Test custom configuration options."""
    db_file = tmp_path / "custom_map.db"
    cfg = ProviderMappingConfig(
        database_path=db_file,
        auto_migrate=False,
    )
    assert cfg.database_path == db_file
    assert cfg.auto_migrate is False
