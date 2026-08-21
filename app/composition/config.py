"""Declarative TOML configuration models and loader."""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


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
        profile: Active deployment profile ('research', 'backtest', 'live').
        features: Mapping of feature_id to FeatureConfig.
    """

    profile: str = "research"
    features: dict[str, FeatureConfig] = field(default_factory=dict)

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


def load_config_from_toml_string(content: str) -> AppConfig:
    """Parse application configuration from a TOML string.

    Args:
        content: Raw TOML text content.

    Returns:
        Parsed AppConfig instance.
    """
    raw = tomllib.loads(content)
    app_section = raw.get("application", {})
    profile = app_section.get("profile", "research")

    features_raw = raw.get("features", {})
    features: dict[str, FeatureConfig] = {}

    for f_id, f_data in features_raw.items():
        if isinstance(f_data, dict):
            enabled = bool(f_data.get("enabled", True))
            if "config" in f_data and isinstance(f_data["config"], dict):
                cfg = f_data["config"]
            else:
                cfg = {k: v for k, v in f_data.items() if k != "enabled"}
            features[f_id] = FeatureConfig(enabled=enabled, config=cfg)

    return AppConfig(profile=profile, features=features)


def load_config_from_file(path: str | Path) -> AppConfig:
    """Load and parse application configuration from a TOML file.

    Args:
        path: Path to the TOML configuration file.

    Returns:
        Parsed AppConfig instance.

    Raises:
        FileNotFoundError: If the config file does not exist.
    """
    file_path = Path(path)
    if not file_path.is_file():
        msg = f"Configuration file not found: {file_path}"
        raise FileNotFoundError(msg)

    content = file_path.read_text(encoding="utf-8")
    return load_config_from_toml_string(content)
