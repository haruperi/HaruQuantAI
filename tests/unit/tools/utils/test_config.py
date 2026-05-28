"""Unit tests for tools.utils.config."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.utils.config import (
    DEFAULT_APP_NAME,
    DEFAULT_ENVIRONMENT,
    DEFAULT_LOG_LEVEL,
    Settings,
    get_environment,
    get_settings,
    is_production,
    is_test,
)
from tools.utils.errors import ConfigurationError


def test_get_settings_returns_defaults_when_dotenv_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HARUQUANT_ENV", raising=False)
    monkeypatch.delenv("HARUQUANT_APP_NAME", raising=False)
    monkeypatch.delenv("HARUQUANT_LOG_LEVEL", raising=False)

    settings = get_settings(tmp_path / "missing.env")

    assert settings.environment == DEFAULT_ENVIRONMENT
    assert settings.app_name == DEFAULT_APP_NAME
    assert settings.log_level == DEFAULT_LOG_LEVEL


def test_dotenv_values_are_loaded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("HARUQUANT_ENV", raising=False)
    monkeypatch.delenv("HARUQUANT_APP_NAME", raising=False)
    monkeypatch.delenv("HARUQUANT_LOG_LEVEL", raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text(
        """
        HARUQUANT_ENV=staging
        HARUQUANT_APP_NAME="haruquant-test"
        HARUQUANT_LOG_LEVEL=debug
        """,
        encoding="utf-8",
    )

    settings = get_settings(env_file)

    assert settings.environment == "staging"
    assert settings.app_name == "haruquant-test"
    assert settings.log_level == "DEBUG"


def test_environment_variables_override_dotenv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "HARUQUANT_ENV=staging\nHARUQUANT_APP_NAME=dotenv-app\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("HARUQUANT_ENV", "production")
    monkeypatch.setenv("HARUQUANT_APP_NAME", "env-app")
    monkeypatch.setenv("HARUQUANT_LOG_LEVEL", "ERROR")

    settings = get_settings(env_file)

    assert settings.environment == "production"
    assert settings.app_name == "env-app"
    assert settings.log_level == "ERROR"


def test_settings_normalizes_direct_construction() -> None:
    settings = Settings(
        environment="LOCAL",
        app_name="  HaruQuant  ",
        log_level="debug",
    )

    assert settings.environment == "local"
    assert settings.app_name == "HaruQuant"
    assert settings.log_level == "DEBUG"


@pytest.mark.parametrize(
    "environment", ["local", "development", "test", "staging", "production"]
)
def test_valid_environments_pass(environment: str) -> None:
    settings = Settings(environment=environment)

    assert settings.environment == environment


def test_invalid_environment_raises_configuration_error() -> None:
    with pytest.raises(ConfigurationError, match="Invalid HARUQUANT_ENV"):
        Settings(environment="demo")


def test_empty_app_name_raises_configuration_error() -> None:
    with pytest.raises(ConfigurationError, match="HARUQUANT_APP_NAME cannot be empty"):
        Settings(app_name=" ")


def test_invalid_log_level_raises_configuration_error() -> None:
    with pytest.raises(ConfigurationError, match="Invalid HARUQUANT_LOG_LEVEL"):
        Settings(log_level="LOUD")


def test_env_file_directory_raises_configuration_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="env_file points to a directory"):
        get_settings(tmp_path)


def test_env_file_wrong_type_raises_configuration_error() -> None:
    with pytest.raises(ConfigurationError, match="env_file must be"):
        get_settings(123)  # type: ignore[arg-type]


def test_dotenv_export_syntax_is_supported(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HARUQUANT_ENV", raising=False)
    monkeypatch.delenv("HARUQUANT_APP_NAME", raising=False)
    monkeypatch.delenv("HARUQUANT_LOG_LEVEL", raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text(
        "export HARUQUANT_ENV=test\nexport HARUQUANT_LOG_LEVEL='warning'\n",
        encoding="utf-8",
    )

    settings = get_settings(env_file)

    assert settings.environment == "test"
    assert settings.log_level == "WARNING"


def test_malformed_dotenv_lines_are_ignored(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HARUQUANT_ENV", raising=False)
    monkeypatch.delenv("HARUQUANT_APP_NAME", raising=False)
    monkeypatch.delenv("HARUQUANT_LOG_LEVEL", raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text(
        """
        # comment
        MALFORMED
        =bad
        HARUQUANT_ENV=test
        """,
        encoding="utf-8",
    )

    settings = get_settings(env_file)

    assert settings.environment == "test"


def test_get_environment_and_environment_helpers(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("HARUQUANT_ENV=production\n", encoding="utf-8")

    assert get_environment(env_file) == "production"
    assert is_production(env_file) is True
    assert is_test(env_file) is False


def test_is_test_returns_true_for_test_environment(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("HARUQUANT_ENV=test\n", encoding="utf-8")

    assert is_test(env_file) is True
    assert is_production(env_file) is False
