"""Tests for StorageConfig validation."""

from pathlib import Path

import pytest

from app.services.system.storage.config import StorageConfig


def test_storage_config_defaults() -> None:
    """Test default values for StorageConfig."""
    cfg = StorageConfig()
    assert cfg.db_path == "data/db/haruquantai.db"
    assert cfg.base_path == "data/storage"
    assert cfg.driver == "sqlite"
    assert cfg.database_file == Path("data/db/haruquantai.db")
    assert cfg.root_directory == Path("data/storage")


def test_storage_config_from_dict() -> None:
    """Test parsing StorageConfig from raw dictionary."""
    cfg = StorageConfig.from_dict(
        {
            "db_path": "custom/db/app.db",
            "base_path": "var/custom_data",
            "driver": "disk",
        }
    )
    assert cfg.db_path == "custom/db/app.db"
    assert cfg.base_path == "var/custom_data"
    assert cfg.driver == "disk"
    assert cfg.database_file == Path("custom/db/app.db")
    assert cfg.root_directory == Path("var/custom_data")


def test_storage_config_invalid() -> None:
    """Test invalid configurations."""
    with pytest.raises(ValueError, match="base_path must not be empty"):
        StorageConfig.from_dict({"base_path": ""})

    with pytest.raises(ValueError, match="db_path must not be empty"):
        StorageConfig.from_dict({"db_path": ""})

    with pytest.raises(ValueError, match="driver must be 'sqlite' or 'disk'"):
        StorageConfig.from_dict({"driver": "invalid_driver"})
