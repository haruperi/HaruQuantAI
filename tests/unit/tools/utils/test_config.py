"""Unit tests for the merged tools.utils.config module."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.utils.config import (
    DEFAULT_APP_NAME,
    DEFAULT_ENVIRONMENT,
    DEFAULT_LOG_LEVEL,
    RuntimeSettings,
    Settings,
    collect_prefixed_values,
    get_environment,
    get_settings,
    inject_runtime_settings,
    is_production,
    is_test,
    load_runtime_settings,
    load_runtime_settings_from_mapping,
    normalize_environment,
    normalize_log_level,
    parse_env_file,
)
from tools.utils.errors import ConfigurationError


def assert_tool_schema(result: dict) -> None:
    assert set(result) == {"status", "message", "data", "error", "metadata"}
    assert result["metadata"]["tool_category"] == "utils"
    assert isinstance(result["metadata"]["execution_ms"], float)


def test_get_settings_defaults_when_env_file_missing(
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


def test_get_settings_reads_dotenv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("HARUQUANT_ENV", raising=False)
    monkeypatch.delenv("HARUQUANT_APP_NAME", raising=False)
    monkeypatch.delenv("HARUQUANT_LOG_LEVEL", raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text(
        "HARUQUANT_ENV=production\nHARUQUANT_APP_NAME='hq'\nHARUQUANT_LOG_LEVEL=debug\n",
        encoding="utf-8",
    )

    settings = get_settings(env_file)

    assert settings.environment == "production"
    assert settings.app_name == "hq"
    assert settings.log_level == "DEBUG"


def test_get_settings_environment_variables_override_dotenv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("HARUQUANT_ENV=test\n", encoding="utf-8")
    monkeypatch.setenv("HARUQUANT_ENV", "production")

    assert get_settings(env_file).environment == "production"


def test_invalid_settings_raise_configuration_error() -> None:
    with pytest.raises(ConfigurationError):
        get_settings(123)  # type: ignore[arg-type]


def test_environment_helpers(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("HARUQUANT_ENV=production\n", encoding="utf-8")

    assert get_environment(env_file) == "production"
    assert is_production(env_file) is True
    assert is_test(env_file) is False


def test_normalization_helpers() -> None:
    assert normalize_environment("dev") == "development"
    assert normalize_environment("prod") == "production"
    assert normalize_log_level("debug") == "DEBUG"


def test_parse_env_file_export_syntax(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "export HQT_ENVIRONMENT=test\nHQT_API_PORT=9000\n", encoding="utf-8"
    )

    values = parse_env_file(env_file)

    assert values["HQT_ENVIRONMENT"] == "test"
    assert values["HQT_API_PORT"] == "9000"


def test_collect_prefixed_values() -> None:
    values = collect_prefixed_values(
        {"HQT_ENVIRONMENT": "test", "OTHER": "x", "HQT_LOG_LEVEL": "INFO"},
        "HQT_",
    )

    assert values == {"environment": "test", "log_level": "INFO"}


def test_runtime_settings_validation() -> None:
    settings = RuntimeSettings(environment="dev", api_port=9000, log_level="warning")

    assert settings.environment == "development"
    assert settings.api_port == 9000
    assert settings.log_level == "WARNING"


def test_load_runtime_settings_from_mapping_success() -> None:
    result = load_runtime_settings_from_mapping(
        {
            "environment": "paper",
            "app_name": "haruquant",
            "api_port": 8100,
            "custom": "kept",
        },
        request_id="req-config-001",
    )

    assert_tool_schema(result)
    assert result["status"] == "success"
    assert result["data"]["environment"] == "paper"
    assert result["data"]["extra_config"]["custom"] == "kept"
    assert result["metadata"]["request_id"] == "req-config-001"


def test_load_runtime_settings_from_mapping_validation_error() -> None:
    result = load_runtime_settings_from_mapping({"environment": "bad"})

    assert_tool_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "VALIDATION_FAILED"


def test_load_runtime_settings_from_env_dir_and_environ(tmp_path: Path) -> None:
    env_dir = tmp_path / "envs"
    env_dir.mkdir()
    (env_dir / "test.env").write_text(
        "api_port=8100\nlog_level=debug\n", encoding="utf-8"
    )

    result = load_runtime_settings(
        environment="test",
        environ={"HQT_APP_NAME": "from-env"},
        env_dir=env_dir,
    )

    assert_tool_schema(result)
    assert result["status"] == "success"
    assert result["data"]["environment"] == "test"
    assert result["data"]["app_name"] == "from-env"
    assert result["data"]["api_port"] == 8100
    assert result["data"]["log_level"] == "DEBUG"


def test_inject_runtime_settings_updates_target() -> None:
    target: dict[str, object] = {}
    result = inject_runtime_settings(
        target,
        {"environment": "test", "api_port": 8200, "app_name": "hq"},
    )

    assert_tool_schema(result)
    assert result["status"] == "success"
    assert target["environment"] == "test"
    assert target["api_port"] == 8200
