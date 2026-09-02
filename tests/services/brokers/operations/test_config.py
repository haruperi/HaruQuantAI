"""Unit tests for BrokerOperationsConfig."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.services.brokers.operations.config import BrokerOperationsConfig


def test_config_defaults() -> None:
    """Verify default BrokerOperationsConfig settings."""
    cfg = BrokerOperationsConfig()
    assert cfg.database_path is None


def test_config_custom_path() -> None:
    """Verify custom database path is retained."""
    custom_path = Path("custom/path/operations.db")
    cfg = BrokerOperationsConfig(database_path=custom_path)
    assert cfg.database_path == custom_path


def test_config_from_dict_valid() -> None:
    """Verify from_dict parses valid string path."""
    cfg = BrokerOperationsConfig.from_dict({"database_path": "custom/db.sqlite"})
    assert cfg.database_path == Path("custom/db.sqlite")

    cfg_none = BrokerOperationsConfig.from_dict(None)
    assert cfg_none.database_path is None

    cfg_empty_dict = BrokerOperationsConfig.from_dict({})
    assert cfg_empty_dict.database_path is None


def test_config_from_dict_unknown_keys_fails() -> None:
    """Verify from_dict rejects unrecognized configuration keys."""
    with pytest.raises(
        ValueError, match="Unknown Broker Operations configuration keys"
    ):
        BrokerOperationsConfig.from_dict({"unknown_setting": "val"})


def test_config_from_dict_invalid_type_fails() -> None:
    """Verify from_dict rejects non-string database_path."""
    with pytest.raises(TypeError, match="database_path must be a string or Path"):
        BrokerOperationsConfig.from_dict({"database_path": 12345})


def test_config_from_dict_blank_string_fails() -> None:
    """Verify from_dict rejects empty string database_path."""
    with pytest.raises(ValueError, match="database_path cannot be an empty string"):
        BrokerOperationsConfig.from_dict({"database_path": "   "})
