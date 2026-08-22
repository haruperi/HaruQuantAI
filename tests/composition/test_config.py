"""Tests for declarative TOML configuration loading and validation."""

from pathlib import Path

import pytest

from app.composition.config import (
    AppConfig,
    ConfigurationError,
    InvalidProfileError,
    load_config_from_file,
    load_config_from_toml_string,
)

SAMPLE_TOML = """
[application]
profile = "research"

[features."FEAT-SYS-PROVIDE_CLOCK"]
enabled = true

[features."FEAT-DATA-RETRIEVE_BARS"]
enabled = true

[features."FEAT-DATA-RETRIEVE_BARS".config]
default_timeframe = "M1"

[features."FEAT-TEST-DISABLE_ME"]
enabled = false

[providers]
"broker.market-data@1" = "FEAT-BROKER-FEED_MOCK"
"""


def test_load_config_from_toml_string() -> None:
    """A complete canonical configuration is parsed exactly."""
    config = load_config_from_toml_string(SAMPLE_TOML)
    assert config.profile == "research"
    assert config.is_feature_enabled("FEAT-SYS-PROVIDE_CLOCK")
    assert config.is_feature_enabled("FEAT-DATA-RETRIEVE_BARS")
    assert not config.is_feature_enabled("FEAT-TEST-DISABLE_ME")
    assert not config.is_feature_enabled("FEAT-TEST-NONEXISTENT")
    assert config.get_feature_config("FEAT-DATA-RETRIEVE_BARS") == {
        "default_timeframe": "M1"
    }
    assert config.get_feature_config("FEAT-SYS-PROVIDE_CLOCK") == {}
    assert config.get_selected_provider("broker.market-data@1") == (
        "FEAT-BROKER-FEED_MOCK"
    )
    assert config.get_selected_provider("system.clock@1") is None


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
            '[features."FEAT-BROKER-FEED_MOCK"]\nenabled = true\n'
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
            "data.historical-bars@1" = ""
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
