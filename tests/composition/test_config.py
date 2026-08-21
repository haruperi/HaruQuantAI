"""Tests for declarative TOML configuration loading and models."""

from pathlib import Path

import pytest

from app.composition.config import (
    AppConfig,
    ConfigurationError,
    load_config_from_file,
    load_config_from_toml_string,
)

SAMPLE_TOML = """
[application]
profile = "research"

[providers]
"broker.market-data@1" = "FEAT-BROKER-FEED_MOCK"

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
    config = load_config_from_toml_string(SAMPLE_TOML)
    assert config.profile == "research"
    assert config.is_feature_enabled("FEAT-SYS-PROVIDE_CLOCK")
    assert config.is_feature_enabled("FEAT-DATA-RETRIEVE_BARS")
    assert not config.is_feature_enabled("FEAT-TEST-DISABLE_ME")
    assert not config.is_feature_enabled("FEAT-TEST-NONEXISTENT")
    assert (
        config.provider_selections["broker.market-data@1"]
        == "FEAT-BROKER-FEED_MOCK"
    )

    data_config = config.get_feature_config("FEAT-DATA-RETRIEVE_BARS")
    assert data_config["default_timeframe"] == "M1"
    assert data_config["cache_enabled"] is True
    assert config.get_feature_config("FEAT-SYS-PROVIDE_CLOCK") == {}
    assert config.get_feature_config("FEAT-TEST-NONEXISTENT") == {}


def test_legacy_profile_syntax_is_rejected() -> None:
    with pytest.raises(ConfigurationError, match="Legacy \\[profile\\]"):
        load_config_from_toml_string('[profile]\nname = "backtest"\n')


def test_unknown_profile_fails_closed() -> None:
    with pytest.raises(ConfigurationError, match="Unknown application profile"):
        load_config_from_toml_string('[application]\nprofile = "mystery"\n')


def test_blank_profile_is_rejected() -> None:
    with pytest.raises(ConfigurationError, match="non-empty string"):
        load_config_from_toml_string('[application]\nprofile = ""\n')


def test_invalid_provider_selection_key_fails() -> None:
    content = """
    [application]
    profile = "research"
    [providers]
    "broker.market-data" = "FEAT-BROKER-FEED_MOCK"
    """
    with pytest.raises(ConfigurationError, match="versioned capability identifiers"):
        load_config_from_toml_string(content)


def test_invalid_provider_feature_id_fails() -> None:
    content = """
    [application]
    profile = "research"
    [providers]
    "broker.market-data@1" = "mock"
    """
    with pytest.raises(ConfigurationError, match="Invalid provider feature ID"):
        load_config_from_toml_string(content)


def test_non_boolean_feature_enabled_is_rejected() -> None:
    content = """
    [application]
    profile = "research"
    [features.FEAT-DATA-RETRIEVE_BARS]
    enabled = "yes"
    """
    with pytest.raises(ConfigurationError, match="enabled must be a boolean"):
        load_config_from_toml_string(content)


def test_load_config_from_file(tmp_path: Path) -> None:
    config_file = tmp_path / "app.toml"
    config_file.write_text(SAMPLE_TOML, encoding="utf-8")
    config = load_config_from_file(config_file)
    assert config.profile == "research"
    assert config.is_feature_enabled("FEAT-DATA-RETRIEVE_BARS")


def test_load_config_from_file_missing_raises(tmp_path: Path) -> None:
    missing_file = tmp_path / "non_existent.toml"
    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        load_config_from_file(missing_file)


def test_default_app_config() -> None:
    config = AppConfig()
    assert config.profile == "research"
    assert config.features == {}
    assert config.provider_selections == {}
