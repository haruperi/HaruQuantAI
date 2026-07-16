import logging

import pytest
from app.utils import (
    ConfigurationError,
    SecurityError,
    load_settings,
    resolve_secret_reference,
)


def test_load_settings_precedence_order() -> None:
    settings = load_settings(
        {"ENVIRONMENT": "test", "LOG_LEVEL": "DEBUG"},
        {"ENVIRONMENT": "production", "RUNTIME_PROFILE": "paper"},
    )
    assert settings.environment == "test"
    assert settings.runtime_profile == "paper"
    assert settings.logging.level == "DEBUG"


def test_load_settings_includes_log_directory() -> None:
    settings = load_settings(
        {
            "LOG_DIRECTORY": "logs",
            "LOG_RETENTION_DAYS": "12",
            "LOG_COMPRESSION": "none",
            "LOG_ENQUEUE": "false",
            "LOG_COLORIZE": "false",
        },
        {},
    )
    assert str(settings.logging.log_directory) == "logs"
    assert settings.logging.retention_days == 12
    assert settings.logging.compression == "none"
    assert settings.logging.enqueue is False
    assert settings.logging.colorize is False


def test_load_settings_rejects_invalid_boolean() -> None:
    with pytest.raises(ConfigurationError):
        load_settings({"LOG_ENQUEUE": "yes"}, {})


def test_resolve_secret_reference_never_logs_secret(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    secret = resolve_secret_reference("secret://broker/demo", lambda _: "abc123")
    assert secret.get_secret_value() == "abc123"
    assert "abc123" not in caplog.text
    with pytest.raises(ConfigurationError):
        resolve_secret_reference("plain-text", lambda _: "abc123")
    with pytest.raises(SecurityError):
        resolve_secret_reference("secret://missing", lambda _: "")
