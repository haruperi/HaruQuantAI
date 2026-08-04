from pathlib import Path
from typing import override

import pytest
from app.utils import (
    get_app_settings_model_config,
    get_app_settings_sources,
    load_settings,
)
from app.utils.errors.exceptions import ConfigurationError
from app.utils.settings.models import AppSettings, LoggingSettings, RuntimeSettings
from pydantic import ValidationError
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource


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


def test_app_settings_model_config_returns_mutable_copy() -> None:
    config = get_app_settings_model_config()
    assert config == AppSettings.model_config
    config["extra"] = "allow"
    assert AppSettings.model_config.get("extra") != "allow"


def test_app_settings_sources_delegate_to_central_model() -> None:
    class _ProbeSettings(BaseSettings):
        model_config = get_app_settings_model_config()

        probe_value: str = "default"

        @override
        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            return get_app_settings_sources(
                settings_cls,
                init_settings,
                env_settings,
                dotenv_settings,
                file_secret_settings,
            )

    assert _ProbeSettings().probe_value == "default"
