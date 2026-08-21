"""Tests for declarative TOML configuration loading and models."""

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
cache_enabled = true

[features."FEAT-TEST-DISABLE_ME"]
enabled = false
"""


def test_load_config_from_toml_string() -> None:
    """Test parsing complete TOML configuration."""
    cfg = load_config_from_toml_string(SAMPLE_TOML)

    assert cfg.profile == "research"
    assert cfg.is_feature_enabled("FEAT-SYS-PROVIDE_CLOCK")
    assert cfg.is_feature_enabled("FEAT-DATA-RETRIEVE_BARS")
    assert not cfg.is_feature_enabled("FEAT-TEST-DISABLE_ME")
    assert not cfg.is_feature_enabled("FEAT-TEST-NONEXISTENT")

    data_cfg = cfg.get_feature_config("FEAT-DATA-RETRIEVE_BARS")
    assert data_cfg["default_timeframe"] == "M1"
    assert data_cfg["cache_enabled"] is True

    assert cfg.get_feature_config("FEAT-SYS-PROVIDE_CLOCK") == {}
    assert cfg.get_feature_config("FEAT-TEST-NONEXISTENT") == {}


def test_load_config_from_file(tmp_path: Path) -> None:
    """Test loading configuration from a temporary TOML file."""
    config_file = tmp_path / "app.toml"
    config_file.write_text(SAMPLE_TOML, encoding="utf-8")

    cfg = load_config_from_file(config_file)
    assert cfg.profile == "research"
    assert cfg.is_feature_enabled("FEAT-DATA-RETRIEVE_BARS")


def test_load_config_from_file_missing_raises(tmp_path: Path) -> None:
    """Test loading from non-existent file raises FileNotFoundError."""
    missing_file = tmp_path / "non_existent.toml"
    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        load_config_from_file(missing_file)


def test_default_app_config() -> None:
    """Test default values of AppConfig."""
    cfg = AppConfig()
    assert cfg.profile == "research"
    assert len(cfg.features) == 0


def test_legacy_profile_section_rejected() -> None:
    """Test that [profile] legacy section is rejected with InvalidProfileError."""
    legacy_toml = """
    [profile]
    name = "live"

    [features."FEAT-BROKER-FEED_MOCK"]
    enabled = true
    """
    with pytest.raises(InvalidProfileError, match=r"(?i)legacy.*profile"):
        load_config_from_toml_string(legacy_toml)


def test_unknown_profile_rejected() -> None:
    """Test that unknown profile names are rejected with InvalidProfileError."""
    unknown_toml = """
    [application]
    profile = "unknown_quantum_profile"
    """
    with pytest.raises(InvalidProfileError, match=r"(?i)unknown deployment profile"):
        load_config_from_toml_string(unknown_toml)


def test_missing_application_section_rejected() -> None:
    """Test that missing [application] section raises InvalidProfileError."""
    no_app_toml = """
    [features."FEAT-BROKER-FEED_MOCK"]
    enabled = true
    """
    with pytest.raises(
        InvalidProfileError, match=r"(?i)missing required '\[application\]'"
    ):
        load_config_from_toml_string(no_app_toml)


def test_blank_profile_rejected() -> None:
    """Test that blank profile string raises InvalidProfileError."""
    blank_profile_toml = """
    [application]
    profile = "   "
    """
    with pytest.raises(InvalidProfileError, match=r"(?i)missing or blank 'profile'"):
        load_config_from_toml_string(blank_profile_toml)


def test_malformed_toml_raises_configuration_error() -> None:
    """Test that invalid TOML syntax raises ConfigurationError."""
    malformed = "invalid = [ unclosed array"
    with pytest.raises(ConfigurationError, match=r"(?i)failed to parse toml"):
        load_config_from_toml_string(malformed)
