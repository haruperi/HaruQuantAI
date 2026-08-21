"""Declarative TOML configuration models and loader."""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

KNOWN_PROFILES: frozenset[str] = frozenset({"research", "backtest", "live"})


@dataclass(frozen=True, slots=True)
class FeatureConfig:
    """Configuration section for a single feature package."""

    enabled: bool = True
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Top-level application deployment configuration."""

    profile: str = "research"
    features: dict[str, FeatureConfig] = field(default_factory=dict)
    capability_providers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized = self.profile.strip().lower()
        if normalized not in KNOWN_PROFILES:
            allowed = ", ".join(sorted(KNOWN_PROFILES))
            msg = f"Unknown application profile '{self.profile}'. Allowed: {allowed}"
            raise ValueError(msg)
        object.__setattr__(self, "profile", normalized)

        for capability, feature_id in self.capability_providers.items():
            if "@" not in capability or not capability.strip():
                msg = (
                    "Capability provider keys must be versioned identifiers "
                    f"like 'broker.market-data@1', got '{capability}'"
                )
                raise ValueError(msg)
            if not feature_id.strip():
                msg = f"Provider feature ID for '{capability}' must not be empty"
                raise ValueError(msg)

    def is_feature_enabled(self, feature_id: str) -> bool:
        """Check if a given feature is declared and enabled."""
        feat_cfg = self.features.get(feature_id)
        return feat_cfg.enabled if feat_cfg is not None else False

    def get_feature_config(self, feature_id: str) -> dict[str, Any]:
        """Retrieve the configuration dictionary for a feature."""
        feat_cfg = self.features.get(feature_id)
        return feat_cfg.config if feat_cfg is not None else {}


def _parse_profile(raw: dict[str, Any]) -> str:
    """Resolve the application profile while accepting the legacy profile table."""
    app_section = raw.get("application", {})
    legacy_section = raw.get("profile", {})

    app_profile = app_section.get("profile") if isinstance(app_section, dict) else None
    legacy_profile = legacy_section.get("name") if isinstance(legacy_section, dict) else None

    if app_profile is not None and legacy_profile is not None:
        if str(app_profile).strip().lower() != str(legacy_profile).strip().lower():
            msg = (
                "Conflicting profile declarations in [application].profile and "
                "legacy [profile].name"
            )
            raise ValueError(msg)

    selected = app_profile if app_profile is not None else legacy_profile
    return str(selected if selected is not None else "research").strip().lower()


def load_config_from_toml_string(content: str) -> AppConfig:
    """Parse application configuration from a TOML string."""
    raw = tomllib.loads(content)
    profile = _parse_profile(raw)

    features_raw = raw.get("features", {})
    if not isinstance(features_raw, dict):
        raise ValueError("[features] must be a TOML table")

    features: dict[str, FeatureConfig] = {}
    for f_id, f_data in features_raw.items():
        if not isinstance(f_data, dict):
            msg = f"Feature '{f_id}' configuration must be a TOML table"
            raise ValueError(msg)
        enabled = bool(f_data.get("enabled", True))
        if "config" in f_data:
            raw_cfg = f_data["config"]
            if not isinstance(raw_cfg, dict):
                msg = f"Feature '{f_id}'.config must be a TOML table"
                raise ValueError(msg)
            cfg = dict(raw_cfg)
        else:
            cfg = {k: v for k, v in f_data.items() if k != "enabled"}
        features[f_id] = FeatureConfig(enabled=enabled, config=cfg)

    provider_raw = raw.get("capabilities", {})
    if not isinstance(provider_raw, dict):
        raise ValueError("[capabilities] must be a TOML table")

    provider_selection: dict[str, str] = {}
    for capability, feature_id in provider_raw.items():
        if not isinstance(feature_id, str):
            msg = f"Provider selection for '{capability}' must be a feature ID string"
            raise ValueError(msg)
        provider_selection[str(capability)] = feature_id

    return AppConfig(
        profile=profile,
        features=features,
        capability_providers=provider_selection,
    )


def load_config_from_file(path: str | Path) -> AppConfig:
    """Load and parse application configuration from a TOML file."""
    file_path = Path(path)
    if not file_path.is_file():
        msg = f"Configuration file not found: {file_path}"
        raise FileNotFoundError(msg)

    content = file_path.read_text(encoding="utf-8")
    return load_config_from_toml_string(content)
