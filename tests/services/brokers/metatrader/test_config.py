"""Unit tests for MetaTraderConfig."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.services.brokers.metatrader.config import MetaTraderConfig


def test_config_defaults() -> None:
    """Verify default MetaTraderConfig values."""
    cfg = MetaTraderConfig()
    assert cfg.database_path is None
    assert cfg.terminal_path is None
    assert cfg.login is None
    assert cfg.password is None
    assert cfg.server is None
    assert cfg.timeout == 30


def test_config_from_dict_valid() -> None:
    """Verify parsing valid config dictionaries."""
    cfg = MetaTraderConfig.from_dict(
        {
            "database_path": "custom/path.db",
            "terminal_path": "C:/MT5/terminal64.exe",
            "login": 888888,
            "password": "pwd",  # pragma: allowlist secret
            "server": "DemoServer",
            "timeout": 45,
        }
    )
    assert cfg.database_path == Path("custom/path.db")
    assert cfg.terminal_path == "C:/MT5/terminal64.exe"
    assert cfg.login == 888888
    assert cfg.password == "pwd"  # pragma: allowlist secret
    assert cfg.server == "DemoServer"
    assert cfg.timeout == 45

    cfg_str_login = MetaTraderConfig.from_dict({"login": "999999"})
    assert cfg_str_login.login == 999999

    assert MetaTraderConfig.from_dict(None).timeout == 30


def test_config_from_dict_unknown_keys() -> None:
    """Verify rejecting unknown configuration keys."""
    with pytest.raises(ValueError, match="Unknown MetaTrader configuration keys"):
        MetaTraderConfig.from_dict({"invalid_key": 123})


def test_config_from_dict_invalid_types() -> None:
    """Verify rejecting invalid configuration types."""
    with pytest.raises(TypeError, match="database_path must be a string or Path"):
        MetaTraderConfig.from_dict({"database_path": 123})

    with pytest.raises(TypeError, match="login must be an integer or digit string"):
        MetaTraderConfig.from_dict({"login": "not_a_number"})

    with pytest.raises(TypeError, match="timeout must be a positive integer"):
        MetaTraderConfig.from_dict({"timeout": -5})
