"""Declarative TOML configuration models and loader."""

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_CAPABILITY_PATTERN = re.compile(r"^[a-z][a-z0-9.-]*@[1-9][0-9]*$")
_FEATURE_ID_PATTERN = re.compile(r"^FEAT-[A-Z0-9]+-[A-Z0-9_]+$")


class ConfigurationError(ValueError):
    """Raised when deployment configuration is malformed or unsupported."""


@dataclass(frozen=True, slots=True)
class DeploymentProfile:
    """Immutable deployment profile and its readiness requirements."""

    name: str
    required_capabilities: frozenset[str]


DEPLOYMENT_PROFILES: dict[str, DeploymentProfile] = {
    "research": DeploymentProfile(
        name="research",
        required_capabilities=frozenset({"data.historical-bars@1"}),
    ),
    "backtest": DeploymentProfile(
        name="backtest",
        required_capabilities=frozenset(
            {"data.historical-bars@1", "system.clock@1"}
        ),
    ),
    "live": DeploymentProfile(
        name="live",
        required_capabilities=frozenset(
            {
                "system.clock@1",
                "broker.market-data@1",
                "broker.execution@1",
                "data.realtime-ticks@1",
                "portfolio.positions@1",
                "risk.approval@1",
                "trading.execution@1",
            }
        ),
    ),
}


@dataclass(frozen=True, slots=True)
class FeatureConfig:
    """Configuration section for one feature package."""

    enabled: bool = True
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Validated top-level application deployment configuration."""

    profile: str = "research"
    features: dict[str, FeatureConfig] = field(default_factory=dict)
    provider_selections: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized = self.profile.strip().lower()
        if normalized not in DEPLOYMENT_PROFILES:
            allowed = ", ".join(sorted(DEPLOYMENT_PROFILES))
            msg = f"Unknown application profile '{self.profile}'. Allowed: {allowed}"
            raise ConfigurationError(msg)
        object.__setattr__(self, "profile", normalized)

        for capability, feature_id in self.provider_selections.items():
            if _CAPABILITY_PATTERN.fullmatch(capability) is None:
                msg = (
                    "Provider keys must be versioned capability identifiers such as "
                    f"'broker.market-data@1', got '{capability}'"
                )
                raise ConfigurationError(msg)
            if _FEATURE_ID_PATTERN.fullmatch(feature_id) is None:
                msg = f"Invalid provider feature ID '{feature_id}' for '{capability}'"
                raise ConfigurationError(msg)

    @property
    def deployment_profile(self) -> DeploymentProfile:
        """Return the selected immutable deployment profile."""
        return DEPLOYMENT_PROFILES[self.profile]

    def is_feature_enabled(self, feature_id: str) -> bool:
        """Return whether a feature is declared and enabled."""
        feature_config = self.features.get(feature_id)
        return feature_config.enabled if feature_config is not None else False

    def get_feature_config(self, feature_id: str) -> dict[str, Any]:
        """Return a copy of a feature's configuration dictionary."""
        feature_config = self.features.get(feature_id)
        return dict(feature_config.config) if feature_config is not None else {}


def _parse_profile(raw: dict[str, Any]) -> str:
    """Parse the canonical ``[application].profile`` declaration."""
    if "profile" in raw:
        raise ConfigurationError(
            "Legacy [profile] configuration is unsupported; use "
            "[application] with profile = '<name>'"
        )
    application = raw.get("application")
    if application is None:
        return "research"
    if not isinstance(application, dict):
        raise ConfigurationError("[application] must be a TOML table")
    profile = application.get("profile", "research")
    if not isinstance(profile, str) or not profile.strip():
        raise ConfigurationError("[application].profile must be a non-empty string")
    return profile.strip().lower()


def _parse_features(raw: dict[str, Any]) -> dict[str, FeatureConfig]:
    """Parse feature enablement and feature-local configuration."""
    features_raw = raw.get("features", {})
    if not isinstance(features_raw, dict):
        raise ConfigurationError("[features] must be a TOML table")

    features: dict[str, FeatureConfig] = {}
    for feature_id, feature_data in features_raw.items():
        if _FEATURE_ID_PATTERN.fullmatch(feature_id) is None:
            raise ConfigurationError(f"Invalid feature ID '{feature_id}'")
        if not isinstance(feature_data, dict):
            raise ConfigurationError(
                f"Feature '{feature_id}' configuration must be a TOML table"
            )
        enabled_value = feature_data.get("enabled", True)
        if not isinstance(enabled_value, bool):
            raise ConfigurationError(
                f"Feature '{feature_id}'.enabled must be a boolean"
            )
        if "config" in feature_data:
            raw_config = feature_data["config"]
            if not isinstance(raw_config, dict):
                raise ConfigurationError(
                    f"Feature '{feature_id}'.config must be a TOML table"
                )
            config = dict(raw_config)
        else:
            config = {
                key: value
                for key, value in feature_data.items()
                if key != "enabled"
            }
        features[feature_id] = FeatureConfig(
            enabled=enabled_value,
            config=config,
        )
    return features


def _parse_provider_selections(raw: dict[str, Any]) -> dict[str, str]:
    """Parse explicit capability-provider selections."""
    providers_raw = raw.get("providers", {})
    if not isinstance(providers_raw, dict):
        raise ConfigurationError("[providers] must be a TOML table")
    selections: dict[str, str] = {}
    for capability, feature_id in providers_raw.items():
        if not isinstance(feature_id, str):
            raise ConfigurationError(
                f"Provider selection for '{capability}' must be a feature ID string"
            )
        selections[str(capability)] = feature_id
    return selections


def load_config_from_toml_string(content: str) -> AppConfig:
    """Parse and validate application configuration from a TOML string."""
    raw = tomllib.loads(content)
    return AppConfig(
        profile=_parse_profile(raw),
        features=_parse_features(raw),
        provider_selections=_parse_provider_selections(raw),
    )


def load_config_from_file(path: str | Path) -> AppConfig:
    """Load and validate application configuration from a TOML file."""
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    return load_config_from_toml_string(file_path.read_text(encoding="utf-8"))
