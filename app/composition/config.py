"""Declarative TOML configuration models and loader."""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.composition.readiness import KNOWN_PROFILES


class ConfigurationError(ValueError):
    """Base exception for configuration parsing and validation errors."""


class InvalidProfileError(ConfigurationError):
    """Raised when a deployment profile specification is missing, invalid, or legacy."""


@dataclass(frozen=True, slots=True)
class FeatureConfig:
    """Configuration section for a single feature package.

    Attributes:
        enabled: Whether the feature is enabled.
        config: Dictionary of feature-specific configuration parameters.
    """

    enabled: bool = True
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Top-level application deployment configuration.

    Attributes:
        profile: Active deployment profile ('research', 'backtest', 'live', 'offline').
        features: Mapping of feature_id to FeatureConfig.
        provider_selections: Mapping of capability identifiers to selected provider IDs.
    """

    profile: str = "research"
    features: dict[str, FeatureConfig] = field(default_factory=dict)
    provider_selections: dict[str, str] = field(default_factory=dict)

    def is_feature_enabled(self, feature_id: str) -> bool:
        """Check if a given feature is declared and enabled.

        Args:
            feature_id: Unique feature identifier.

        Returns:
            True if enabled, False otherwise.
        """
        feat_cfg = self.features.get(feature_id)
        if feat_cfg is not None:
            return feat_cfg.enabled
        return False

    def get_feature_config(self, feature_id: str) -> dict[str, Any]:
        """Retrieve the configuration dictionary for a feature.

        Args:
            feature_id: Unique feature identifier.

        Returns:
            Dictionary of feature parameters.
        """
        feat_cfg = self.features.get(feature_id)
        if feat_cfg is not None:
            return feat_cfg.config
        return {}

    def get_selected_provider(self, capability_identifier: str) -> str | None:
        """Retrieve the explicitly selected provider feature ID for a capability.

        Args:
            capability_identifier: Target capability identifier.

        Returns:
            Selected feature ID if configured, None otherwise.
        """
        return self.provider_selections.get(capability_identifier)


def _parse_profile(raw: dict[str, Any]) -> str:
    """Validate and extract profile name from raw TOML dictionary.

    Args:
        raw: Parsed TOML content dictionary.

    Returns:
        Normalized lowercase profile string.

    Raises:
        InvalidProfileError: If profile table is legacy, missing, blank, or unknown.
    """
    if "profile" in raw:
        msg = (
            "Legacy '[profile]' table is not supported. "
            "Use '[application]' table with 'profile = \"<name>\"'."
        )
        raise InvalidProfileError(msg)

    app_section = raw.get("application")
    if app_section is None or not isinstance(app_section, dict):
        msg = "Missing required '[application]' table in configuration"
        raise InvalidProfileError(msg)

    profile_raw = app_section.get("profile")
    if (
        profile_raw is None
        or not isinstance(profile_raw, str)
        or not profile_raw.strip()
    ):
        msg = "Missing or blank 'profile' string in '[application]' table"
        raise InvalidProfileError(msg)

    profile = profile_raw.strip().lower()
    if profile not in KNOWN_PROFILES:
        supported = sorted(KNOWN_PROFILES)
        msg = (
            f"Unknown deployment profile '{profile_raw}'. "
            f"Supported profiles: {supported}"
        )
        raise InvalidProfileError(msg)

    return profile


def _parse_features(raw: dict[str, Any]) -> dict[str, FeatureConfig]:
    """Validate and extract feature configurations from raw TOML dictionary.

    Args:
        raw: Parsed TOML content dictionary.

    Returns:
        Dictionary mapping feature ID to parsed FeatureConfig.

    Raises:
        ConfigurationError: If features table structure is invalid.
    """
    features_raw = raw.get("features", {})
    if not isinstance(features_raw, dict):
        msg = "'features' section must be a table if present"
        raise ConfigurationError(msg)

    features: dict[str, FeatureConfig] = {}
    for f_id, f_data in features_raw.items():
        if isinstance(f_data, dict):
            enabled = bool(f_data.get("enabled", True))
            if "config" in f_data and isinstance(f_data["config"], dict):
                cfg = f_data["config"]
            else:
                cfg = {k: v for k, v in f_data.items() if k != "enabled"}
            features[f_id] = FeatureConfig(enabled=enabled, config=cfg)
    return features


def _parse_providers(raw: dict[str, Any]) -> dict[str, str]:
    """Validate and extract provider selections from raw TOML dictionary.

    Args:
        raw: Parsed TOML content dictionary.

    Returns:
        Dictionary mapping capability identifiers to selected provider IDs.

    Raises:
        ConfigurationError: If providers table structure or identifiers are invalid.
    """
    providers_raw = raw.get("providers", {})
    if not isinstance(providers_raw, dict):
        msg = "'providers' section must be a table if present"
        raise ConfigurationError(msg)

    provider_selections: dict[str, str] = {}
    for cap_id, feat_id in providers_raw.items():
        if not isinstance(cap_id, str) or "@" not in cap_id or not cap_id.strip():
            msg = f"Invalid capability identifier in '[providers]': '{cap_id}'"
            raise ConfigurationError(msg)
        if not isinstance(feat_id, str) or not feat_id.strip():
            msg = (
                f"Invalid provider feature ID in '[providers]' for "
                f"'{cap_id}': '{feat_id}'"
            )
            raise ConfigurationError(msg)
        provider_selections[cap_id.strip()] = feat_id.strip()
    return provider_selections


def load_config_from_toml_string(content: str) -> AppConfig:
    """Parse application configuration from a TOML string.

    Args:
        content: Raw TOML text content.

    Returns:
        Parsed AppConfig instance.

    Raises:
        InvalidProfileError: If profile grammar is legacy, missing, invalid, or unknown.
        ConfigurationError: If configuration structure is malformed.
    """
    try:
        raw = tomllib.loads(content)
    except Exception as err:
        msg = f"Failed to parse TOML configuration: {err}"
        raise ConfigurationError(msg) from err

    profile = _parse_profile(raw)
    features = _parse_features(raw)
    provider_selections = _parse_providers(raw)

    return AppConfig(
        profile=profile,
        features=features,
        provider_selections=provider_selections,
    )


def load_config_from_file(path: str | Path) -> AppConfig:
    """Load and parse application configuration from a TOML file.

    Args:
        path: Path to the TOML configuration file.

    Returns:
        Parsed AppConfig instance.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ConfigurationError: If config parsing or validation fails.
    """
    file_path = Path(path)
    if not file_path.is_file():
        msg = f"Configuration file not found: {file_path}"
        raise FileNotFoundError(msg)

    content = file_path.read_text(encoding="utf-8")
    return load_config_from_toml_string(content)
