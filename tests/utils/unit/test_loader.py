import pytest
from app.utils import (
    ConfigurationError,
    load_settings,
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


def test_load_settings_rejects_unknown_environment_key() -> None:
    """Reject exact unknown or mis-cased keys in supplied environments."""
    source = {"UNKNOWN": "value"}
    with pytest.raises(ConfigurationError):
        load_settings({}, source)
    assert source == {"UNKNOWN": "value"}
    with pytest.raises(ConfigurationError):
        load_settings({}, {"environment": "test"})
