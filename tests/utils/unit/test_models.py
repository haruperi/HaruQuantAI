from pathlib import Path

import pytest
from app.utils import (
    ConfigurationError,
    LoggingSettings,
    RuntimeSettings,
    load_settings,
)
from pydantic import ValidationError


def test_default_logging_profile() -> None:
    settings = LoggingSettings()
    assert settings.level == "DEBUG"
    assert settings.render == "human"
    assert settings.log_directory == Path("data/logs")
    assert settings.max_bytes == 10_000_000
    assert settings.backup_count == 10
    assert settings.retention_days == 10
    assert settings.compression == "zip"
    assert settings.enqueue is True
    assert settings.colorize is True


def test_runtime_settings_are_immutable() -> None:
    settings = RuntimeSettings()
    with pytest.raises(ValidationError):
        settings.environment = "production"


def test_settings_reject_unknown_value_without_mutation() -> None:
    source = {"UNKNOWN": "value"}
    with pytest.raises(ConfigurationError):
        load_settings(source, {})
    assert source == {"UNKNOWN": "value"}
    with pytest.raises(ConfigurationError):
        LoggingSettings.model_validate({"level": "TRACE"})
