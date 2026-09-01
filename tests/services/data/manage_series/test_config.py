"""Configuration tests for FEAT-DATA-MANAGE_SERIES."""

from pathlib import Path

import pytest

from app.services.data.manage_series.config import ManageSeriesConfig


def test_config_uses_default_database_path() -> None:
    config = ManageSeriesConfig.from_dict({})

    assert config.database_path == Path(".haruquant/data-series.sqlite3")


def test_config_accepts_database_path() -> None:
    config = ManageSeriesConfig.from_dict({"database_path": "tmp/data.sqlite3"})

    assert config.database_path == Path("tmp/data.sqlite3")


def test_config_rejects_unknown_keys() -> None:
    with pytest.raises(ValueError, match="unknown config keys"):
        ManageSeriesConfig.from_dict({"unexpected": True})


def test_config_rejects_empty_database_path() -> None:
    with pytest.raises(ValueError, match="database_path"):
        ManageSeriesConfig.from_dict({"database_path": ""})
