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
    """Characterization test: [profile] legacy section must be rejected with an error rather than silently defaulting."""
    legacy_toml = """
    [profile]
    name = "live"

    [features."FEAT-BROKER-FEED_MOCK"]
    enabled = true
    """
    with pytest.raises((ValueError, KeyError), match=r"(?i)profile|legacy|application"):
        load_config_from_toml_string(legacy_toml)


def test_unknown_profile_rejected() -> None:
    """Characterization test: unknown profile names must be rejected."""
    unknown_toml = """
    [application]
    profile = "unknown_quantum_profile"
    """
    with pytest.raises((ValueError, KeyError), match=r"(?i)profile|unknown|invalid"):
        load_config_from_toml_string(unknown_toml)
