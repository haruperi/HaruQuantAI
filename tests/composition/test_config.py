"""Tests for declarative TOML configuration loading and models."""

from pathlib import Path

import pytest

from app.composition.config import (
    AppConfig,
    load_config_from_file,
    load_config_from_toml_string,
)

SAMPLE_TOML = """
[application]
profile = "research"

[capabilities]
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
    cfg = load_config_from_toml_string(SAMPLE_TOML)
    assert cfg.profile == "research"
    assert cfg.is_feature_enabled("FEAT-SYS-PROVIDE_CLOCK")
    assert cfg.is_feature_enabled("FEAT-DATA-RETRIEVE_BARS")
    assert not cfg.is_feature_enabled("FEAT-TEST-DISABLE_ME")
    assert not cfg.is_feature_enabled("FEAT-TEST-NONEXISTENT")
    assert (
        cfg.capability_providers["broker.market-data@1"]
        == "FEAT-BROKER-FEED_MOCK"
    )

    data_cfg = cfg.get_feature_config("FEAT-DATA-RETRIEVE_BARS")
    assert data_cfg["default_timeframe"] == "M1"
    assert data_cfg["cache_enabled"] is True
    assert cfg.get_feature_config("FEAT-SYS-PROVIDE_CLOCK") == {}
    assert cfg.get_feature_config("FEAT-TEST-NONEXISTENT") == {}


def test_legacy_profile_syntax_remains_compatible() -> None:
    cfg = load_config_from_toml_string('[profile]\nname = "backtest"\n')
    assert cfg.profile == "backtest"


def test_conflicting_profile_declarations_fail() -> None:
    content = """
    [application]
    profile = "live"
    [profile]
    name = "research"
    """
    with pytest.raises(ValueError, match="Conflicting profile declarations"):
        load_config_from_toml_string(content)


def test_unknown_profile_fails_closed() -> None:
    with pytest.raises(ValueError, match="Unknown application profile"):
        load_config_from_toml_string('[application]\nprofile = "mystery"\n')


def test_invalid_provider_selection_key_fails() -> None:
    content = """
    [application]
    profile = "research"
    [capabilities]
    "broker.market-data" = "FEAT-BROKER-FEED_MOCK"
    """
    with pytest.raises(ValueError, match="versioned identifiers"):
        load_config_from_toml_string(content)


def test_load_config_from_file(tmp_path: Path) -> None:
    config_file = tmp_path / "app.toml"
    config_file.write_text(SAMPLE_TOML, encoding="utf-8")
    cfg = load_config_from_file(config_file)
    assert cfg.profile == "research"
    assert cfg.is_feature_enabled("FEAT-DATA-RETRIEVE_BARS")


def test_load_config_from_file_missing_raises(tmp_path: Path) -> None:
    missing_file = tmp_path / "non_existent.toml"
    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        load_config_from_file(missing_file)


def test_default_app_config() -> None:
    cfg = AppConfig()
    assert cfg.profile == "research"
    assert cfg.features == {}
    assert cfg.capability_providers == {}
