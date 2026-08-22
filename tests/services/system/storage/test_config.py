"""Tests for strict StorageConfig validation."""

from pathlib import Path

import pytest

from app.services.system.storage.config import StorageConfig


def test_storage_config_defaults() -> None:
    """Default storage paths and driver are stable."""
    config = StorageConfig()
    assert config.db_path == "data/db/haruquantai.db"
    assert config.base_path == "data/storage"
    assert config.driver == "sqlite"
    assert config.database_file == Path("data/db/haruquantai.db")
    assert config.root_directory == Path("data/storage")


def test_storage_config_from_dict() -> None:
    """Documented storage fields are parsed together."""
    config = StorageConfig.from_dict(
        {
            "db_path": "custom/db/app.db",
            "base_path": "var/custom_data",
            "driver": "disk",
        }
    )
    assert config.database_file == Path("custom/db/app.db")
    assert config.root_directory == Path("var/custom_data")
    assert config.driver == "disk"


def test_storage_config_invalid_values() -> None:
    """Invalid paths and drivers are rejected."""
    with pytest.raises(ValueError, match="base_path must not be empty"):
        StorageConfig.from_dict({"base_path": ""})
    with pytest.raises(ValueError, match="db_path must not be empty"):
        StorageConfig.from_dict({"db_path": ""})
    with pytest.raises(ValueError, match="driver must be 'sqlite' or 'disk'"):
        StorageConfig.from_dict({"driver": "invalid_driver"})


def test_storage_config_rejects_legacy_or_unknown_keys() -> None:
    """base_path is the only documented filesystem-root key."""
    with pytest.raises(ValueError, match="Unknown Persistent Storage configuration"):
        StorageConfig.from_dict({"root_dir": "legacy/path"})
