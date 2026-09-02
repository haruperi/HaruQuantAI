"""Tests for declarative TOML configuration loading and validation."""

from pathlib import Path

import pytest
from app.composition.config import (
    AppConfig,
    AppSettings,
    BrokerProviderSettings,
    ConfigurationError,
    InvalidProfileError,
    load_broker_provider_settings,
    load_config_from_file,
    load_config_from_toml_string,
    load_profile_document,
    load_settings,
)

SAMPLE_TOML = """
[application]
profile = "research"

[features."FEAT-TEST-PROVIDE_ROOT"]
enabled = true

[features."FEAT-TEST-CONSUME_SERVICE"]
enabled = true

[features."FEAT-TEST-CONSUME_SERVICE".config]
default_timeframe = "M1"

[features."FEAT-TEST-DISABLE_ME"]
enabled = false

[providers]
"test.provider@1" = "FEAT-TEST-PROVIDE_SERVICE"
"""


def test_load_config_from_toml_string() -> None:
    """A complete canonical configuration is parsed exactly."""
    config = load_config_from_toml_string(SAMPLE_TOML)
    assert config.profile == "research"
    assert config.is_feature_enabled("FEAT-TEST-PROVIDE_ROOT")
    assert config.is_feature_enabled("FEAT-TEST-CONSUME_SERVICE")
    assert not config.is_feature_enabled("FEAT-TEST-DISABLE_ME")
    assert not config.is_feature_enabled("FEAT-TEST-NONEXISTENT")
    assert config.get_feature_config("FEAT-TEST-CONSUME_SERVICE") == {
        "default_timeframe": "M1"
    }
    assert config.get_feature_config("FEAT-TEST-PROVIDE_ROOT") == {}
    assert config.get_selected_provider("test.provider@1") == (
        "FEAT-TEST-PROVIDE_SERVICE"
    )
    assert config.get_selected_provider("test.root@1") is None


def test_load_config_from_file(tmp_path: Path) -> None:
    """Configuration files use the same strict parser."""
    config_file = tmp_path / "app.toml"
    config_file.write_text(SAMPLE_TOML, encoding="utf-8")
    assert load_config_from_file(config_file).profile == "research"


def test_load_config_from_file_missing_raises(tmp_path: Path) -> None:
    """Missing configuration files are explicit startup failures."""
    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        load_config_from_file(tmp_path / "missing.toml")


def test_default_app_config() -> None:
    """Direct construction retains a research default for embedded callers."""
    config = AppConfig()
    assert config.profile == "research"
    assert config.features == {}
    assert config.provider_selections == {}


def test_legacy_profile_section_rejected() -> None:
    """The legacy [profile] grammar cannot silently select another profile."""
    with pytest.raises(InvalidProfileError, match=r"(?i)legacy.*profile"):
        load_config_from_toml_string('[profile]\nname = "live"\n')


def test_unknown_profile_rejected() -> None:
    """Unknown deployment profiles fail closed."""
    with pytest.raises(InvalidProfileError, match=r"(?i)unknown deployment profile"):
        load_config_from_toml_string(
            '[application]\nprofile = "unknown_quantum_profile"\n'
        )


def test_missing_or_blank_profile_rejected() -> None:
    """File-based configuration always declares its profile explicitly."""
    with pytest.raises(InvalidProfileError, match=r"(?i)missing required"):
        load_config_from_toml_string(
            '[features."FEAT-TEST-PROVIDE_SERVICE"]\nenabled = true\n'
        )
    with pytest.raises(InvalidProfileError, match=r"(?i)missing or blank"):
        load_config_from_toml_string('[application]\nprofile = "   "\n')


def test_malformed_toml_raises_configuration_error() -> None:
    """TOML syntax failures are wrapped in a typed configuration error."""
    with pytest.raises(ConfigurationError, match=r"(?i)failed to parse toml"):
        load_config_from_toml_string("invalid = [ unclosed array")


def test_invalid_provider_selection_raises_configuration_error() -> None:
    """Provider selection identifiers are validated before graph construction."""
    with pytest.raises(ConfigurationError, match=r"(?i)invalid capability identifier"):
        load_config_from_toml_string(
            """
            [application]
            profile = "research"
            [providers]
            "invalid_cap_no_version" = "FEAT-TEST"
            """
        )
    with pytest.raises(ConfigurationError, match=r"(?i)invalid provider feature ID"):
        load_config_from_toml_string(
            """
            [application]
            profile = "research"
            [providers]
            "test.consumer@1" = ""
            """
        )


def test_unknown_sections_and_invalid_feature_shapes_are_rejected() -> None:
    """Unknown sections and weakly typed feature declarations cannot be ignored."""
    with pytest.raises(ConfigurationError, match="Unknown top-level"):
        load_config_from_toml_string(
            """
            [application]
            profile = "research"
            [unexpected]
            value = true
            """
        )
    with pytest.raises(ConfigurationError, match="enabled must be a boolean"):
        load_config_from_toml_string(
            """
            [application]
            profile = "research"
            [features.FEAT-TEST]
            enabled = "yes"
            """
        )
    with pytest.raises(ConfigurationError, match=r"mixes a \.config table"):
        load_config_from_toml_string(
            """
            [application]
            profile = "research"
            [features.FEAT-TEST]
            enabled = true
            inline_value = 1
            [features.FEAT-TEST.config]
            nested_value = 2
            """
        )


def test_logging_section_parsing_and_defaults() -> None:
    """The [logging] section is parsed into AppConfig.logging with proper overrides."""
    # Test default logging when omitted
    config_default = load_config_from_toml_string(
        """
        [application]
        profile = "research"
        """
    )
    assert config_default.logging.level == "INFO"
    assert config_default.logging.console is True
    assert config_default.logging.file_path is None
    assert config_default.logging.max_bytes == 10 * 1024 * 1024
    assert config_default.logging.backup_count == 5
    assert config_default.logging.capture_capacity == 1000

    # Test explicit [logging] section
    config_explicit = load_config_from_toml_string(
        """
        [application]
        profile = "research"

        [logging]
        level = "DEBUG"
        console = false
        file_path = "logs/test.log"
        max_bytes = 2097152
        backup_count = 3
        capture_capacity = 500
        """
    )
    assert config_explicit.logging.level == "DEBUG"
    assert config_explicit.logging.console is False
    assert config_explicit.logging.file_path == "logs/test.log"
    assert config_explicit.logging.max_bytes == 2097152
    assert config_explicit.logging.backup_count == 3
    assert config_explicit.logging.capture_capacity == 500


def test_logging_section_validation_errors() -> None:
    """Invalid [logging] sections fail closed with ConfigurationError."""
    # Unknown key
    with pytest.raises(ConfigurationError, match="Unknown keys in \\[logging\\]"):
        load_config_from_toml_string(
            """
            [application]
            profile = "research"
            [logging]
            unknown_prop = 123
            """
        )

    # Invalid level
    with pytest.raises(ConfigurationError, match="Unsupported logging level"):
        load_config_from_toml_string(
            """
            [application]
            profile = "research"
            [logging]
            level = "INVALID_LEVEL"
            """
        )

    # Invalid type for console
    with pytest.raises(ConfigurationError, match="must be a boolean"):
        load_config_from_toml_string(
            """
            [application]
            profile = "research"
            [logging]
            console = "yes"
            """
        )

    # Invalid non-positive max_bytes
    with pytest.raises(ConfigurationError, match="max_bytes must be strictly positive"):
        load_config_from_toml_string(
            """
            [application]
            profile = "research"
            [logging]
            max_bytes = 0
            """
        )

    # Invalid non-positive backup_count
    with pytest.raises(
        ConfigurationError, match="backup_count must be strictly positive"
    ):
        load_config_from_toml_string(
            """
            [application]
            profile = "research"
            [logging]
            backup_count = -1
            """
        )


def test_load_settings_and_overrides() -> None:
    """Verify load_settings handles dictionary inputs and overrides."""
    settings = load_settings(
        values={"environment": "staging", "runtime_profile": "live"},
        overrides={"runtime_profile": "simulation"},
    )
    assert isinstance(settings, AppSettings)
    assert settings.environment == "staging"
    assert settings.runtime_profile == "simulation"


def test_load_broker_provider_settings() -> None:
    """Verify load_broker_provider_settings correctly parses bool and secret fields."""
    raw = {
        "mt5_enabled": "true",
        "mt5_login": 123456,
        "mt5_password": "mypassword",  # pragma: allowlist secret
        "binance_enabled": 1,
        "binance_testnet": "false",
        "binance_api_secret": "mysecret",  # pragma: allowlist secret
    }
    broker_settings = load_broker_provider_settings(raw)
    assert isinstance(broker_settings, BrokerProviderSettings)
    assert broker_settings.mt5_enabled is True
    assert broker_settings.mt5_login == 123456
    assert broker_settings.binance_enabled is True
    assert broker_settings.binance_testnet is False


def test_load_profile_document(tmp_path: Path) -> None:
    """Verify load_profile_document loads valid file and handles missing/none path."""
    assert load_profile_document(None) == {}
    assert load_profile_document(tmp_path / "nonexistent.toml") == {}

    doc_file = tmp_path / "profile.toml"
    doc_file.write_text("[profile]\nname = 'demo'", encoding="utf-8")
    loaded = load_profile_document(doc_file)
    assert loaded == {"profile": {"name": "demo"}}
