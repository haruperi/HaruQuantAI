"""Declarative TOML configuration models and validation."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.composition.readiness import KNOWN_PROFILES

_CAPABILITY_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]*@[1-9][0-9]*$")
_FEATURE_ID_PATTERN = re.compile(r"^FEAT-[A-Z0-9_-]+$")
_ALLOWED_TOP_LEVEL = frozenset({"application", "features", "providers"})


class ConfigurationError(ValueError):
    """Base exception for configuration parsing or validation errors."""


class InvalidProfileError(ConfigurationError):
    """Raised when deployment profile configuration is invalid."""


@dataclass(frozen=True, slots=True)
class FeatureConfig:
    """Configuration and enablement state for one feature."""

    enabled: bool = True
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Validated application composition configuration."""

    profile: str = "research"
    features: dict[str, FeatureConfig] = field(default_factory=dict)
    provider_selections: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Normalize and validate direct AppConfig construction.

        Raises:
            InvalidProfileError: If the deployment profile is unsupported.
            ConfigurationError: If a provider selection identifier is invalid.
        """
        normalized = self.profile.strip().lower()
        if normalized not in KNOWN_PROFILES:
            msg = (
                f"Unknown deployment profile '{self.profile}'. "
                f"Supported profiles: {sorted(KNOWN_PROFILES)}"
            )
            raise InvalidProfileError(msg)
        object.__setattr__(self, "profile", normalized)
        for capability, feature_id in self.provider_selections.items():
            _validate_provider_selection(capability, feature_id)

    def is_feature_enabled(self, feature_id: str) -> bool:
        """Return whether a feature is declared and enabled."""
        feature = self.features.get(feature_id)
        return feature.enabled if feature is not None else False

    def get_feature_config(self, feature_id: str) -> dict[str, Any]:
        """Return a copy of a feature's configuration mapping."""
        feature = self.features.get(feature_id)
        return dict(feature.config) if feature is not None else {}

    def get_selected_provider(self, capability_identifier: str) -> str | None:
        """Return the explicitly selected provider for a capability."""
        return self.provider_selections.get(capability_identifier)


def _parse_profile(raw: dict[str, Any]) -> str:
    if "profile" in raw:
        raise InvalidProfileError(
            "Legacy '[profile]' is not supported. Use "
            "'[application]' with 'profile = \"<name>\"'."
        )
    application = raw.get("application")
    if not isinstance(application, dict):
        raise InvalidProfileError(
            "Missing required '[application]' table in configuration"
        )
    unknown_application_keys = set(application) - {"profile"}
    if unknown_application_keys:
        raise ConfigurationError(
            "Unknown keys in [application]: "
            + ", ".join(sorted(unknown_application_keys))
        )
    profile = application.get("profile")
    if not isinstance(profile, str) or not profile.strip():
        raise InvalidProfileError(
            "Missing or blank 'profile' string in '[application]'"
        )
    normalized = profile.strip().lower()
    if normalized not in KNOWN_PROFILES:
        msg = (
            f"Unknown deployment profile '{profile}'. "
            f"Supported profiles: {sorted(KNOWN_PROFILES)}"
        )
        raise InvalidProfileError(msg)
    return normalized


def _parse_features(raw: dict[str, Any]) -> dict[str, FeatureConfig]:
    features_raw = raw.get("features", {})
    if not isinstance(features_raw, dict):
        raise ConfigurationError("'[features]' must be a TOML table")

    features: dict[str, FeatureConfig] = {}
    for feature_id, feature_data in features_raw.items():
        if not isinstance(feature_id, str) or not _FEATURE_ID_PATTERN.fullmatch(
            feature_id
        ):
            msg = f"Invalid feature ID '{feature_id}'"
            raise ConfigurationError(msg)
        if not isinstance(feature_data, dict):
            msg = f"Feature '{feature_id}' configuration must be a TOML table"
            raise ConfigurationError(msg)
        enabled = feature_data.get("enabled", True)
        if not isinstance(enabled, bool):
            msg = f"Feature '{feature_id}'.enabled must be a boolean"
            raise ConfigurationError(msg)
        if "config" in feature_data:
            config = feature_data["config"]
            if not isinstance(config, dict):
                msg = f"Feature '{feature_id}'.config must be a TOML table"
                raise ConfigurationError(msg)
            unexpected = set(feature_data) - {"enabled", "config"}
            if unexpected:
                msg = (
                    f"Feature '{feature_id}' mixes a .config table with inline "
                    f"configuration keys: {sorted(unexpected)}"
                )
                raise ConfigurationError(msg)
            parsed_config = dict(config)
        else:
            parsed_config = {
                key: value for key, value in feature_data.items() if key != "enabled"
            }
        features[feature_id] = FeatureConfig(
            enabled=enabled,
            config=parsed_config,
        )
    return features


def _validate_provider_selection(capability: str, feature_id: str) -> None:
    if not _CAPABILITY_ID_PATTERN.fullmatch(capability):
        msg = (
            f"Invalid capability identifier '{capability}' in [providers]; "
            "a version suffix such as '@1' is required"
        )
        raise ConfigurationError(msg)
    if not _FEATURE_ID_PATTERN.fullmatch(feature_id):
        msg = f"Invalid provider feature ID '{feature_id}' for '{capability}'"
        raise ConfigurationError(msg)


def _parse_providers(raw: dict[str, Any]) -> dict[str, str]:
    providers_raw = raw.get("providers", {})
    if not isinstance(providers_raw, dict):
        raise ConfigurationError("'[providers]' must be a TOML table")
    providers: dict[str, str] = {}
    for raw_capability, raw_feature_id in providers_raw.items():
        if not isinstance(raw_capability, str) or not isinstance(raw_feature_id, str):
            raise ConfigurationError(
                "Provider selections must map capability strings to feature-ID strings"
            )
        capability = raw_capability.strip()
        feature_id = raw_feature_id.strip()
        _validate_provider_selection(capability, feature_id)
        providers[capability] = feature_id
    return providers


def load_config_from_toml_string(content: str) -> AppConfig:
    """Parse and validate application configuration from TOML text.

    Returns:
        Validated application configuration.

    Raises:
        ConfigurationError: If TOML syntax or configuration semantics are invalid.
    """
    try:
        raw = tomllib.loads(content)
    except tomllib.TOMLDecodeError as error:
        msg = f"Failed to parse TOML configuration: {error}"
        raise ConfigurationError(msg) from error

    if "profile" in raw:
        _parse_profile(raw)
    unknown_top_level = set(raw) - _ALLOWED_TOP_LEVEL
    if unknown_top_level:
        raise ConfigurationError(
            "Unknown top-level configuration sections: "
            + ", ".join(sorted(unknown_top_level))
        )
    return AppConfig(
        profile=_parse_profile(raw),
        features=_parse_features(raw),
        provider_selections=_parse_providers(raw),
    )


def load_config_from_file(path: str | Path) -> AppConfig:
    """Load and validate application configuration from a TOML file.

    Returns:
        Validated application configuration.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ConfigurationError: If the file content is invalid.
    """
    file_path = Path(path)
    if not file_path.is_file():
        msg = f"Configuration file not found: {file_path}"
        raise FileNotFoundError(msg)
    return load_config_from_toml_string(file_path.read_text(encoding="utf-8"))
