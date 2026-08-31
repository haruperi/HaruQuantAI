"""Declarative TOML configuration models and validation."""

from __future__ import annotations

import re
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, cast

from app.composition.logging import LoggingConfig
from app.composition.readiness import KNOWN_PROFILES

_CAPABILITY_ID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9_.-]*@[1-9][0-9]*$"
)
_FEATURE_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^FEAT-[A-Z0-9_-]+$")
_ALLOWED_TOP_LEVEL: Final[frozenset[str]] = frozenset(
    {"application", "features", "providers", "logging"}
)


def _default_config_dict() -> dict[str, object]:
    return {}


def _default_features_dict() -> dict[str, FeatureConfig]:
    return {}


def _default_providers_dict() -> dict[str, str]:
    return {}


class ConfigurationError(ValueError):
    """Base exception for configuration parsing or validation errors."""


class InvalidProfileError(ConfigurationError):
    """Raised when deployment profile configuration is invalid."""


@dataclass(frozen=True, slots=True)
class FeatureConfig:
    """Configuration and enablement state for one feature."""

    enabled: bool = True
    config: dict[str, object] = field(default_factory=_default_config_dict)


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Validated application composition configuration."""

    profile: str = "research"
    features: dict[str, FeatureConfig] = field(default_factory=_default_features_dict)
    provider_selections: dict[str, str] = field(default_factory=_default_providers_dict)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    def __post_init__(self) -> None:
        """Normalize and validate direct AppConfig construction.

        Raises:
            InvalidProfileError: If the deployment profile is unsupported.
            ConfigurationError: If provider selection or logging config is invalid.
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
        try:
            self.logging.validate()
        except ValueError as err:
            raise ConfigurationError(str(err)) from err

    def is_feature_enabled(self, feature_id: str) -> bool:
        """Return whether a feature is declared and enabled."""
        feature = self.features.get(feature_id)
        return feature.enabled if feature is not None else False

    def get_feature_config(self, feature_id: str) -> dict[str, object]:
        """Return a copy of a feature's configuration mapping."""
        feature = self.features.get(feature_id)
        return dict(feature.config) if feature is not None else {}

    def get_selected_provider(self, capability_identifier: str) -> str | None:
        """Return the explicitly selected provider for a capability."""
        return self.provider_selections.get(capability_identifier)


def _parse_profile(raw: Mapping[str, object]) -> str:
    if "profile" in raw:
        msg = (
            "Legacy '[profile]' is not supported. Use "
            "'[application]' with 'profile = \"<name>\"'."
        )
        raise InvalidProfileError(msg)
    application: object = raw.get("application")
    if not isinstance(application, Mapping):
        msg = "Missing required '[application]' table in configuration"
        raise InvalidProfileError(msg)
    app_mapping = cast("Mapping[str, object]", application)
    unknown_application_keys = set(app_mapping) - {"profile"}
    if unknown_application_keys:
        msg = "Unknown keys in [application]: " + ", ".join(
            sorted(unknown_application_keys)
        )
        raise ConfigurationError(msg)
    profile = app_mapping.get("profile")
    if not isinstance(profile, str) or not profile.strip():
        msg = "Missing or blank 'profile' string in '[application]'"
        raise InvalidProfileError(msg)
    normalized = profile.strip().lower()
    if normalized not in KNOWN_PROFILES:
        msg = (
            f"Unknown deployment profile '{profile}'. "
            f"Supported profiles: {sorted(KNOWN_PROFILES)}"
        )
        raise InvalidProfileError(msg)
    return normalized


def _parse_features(raw: Mapping[str, object]) -> dict[str, FeatureConfig]:
    features_raw = raw.get("features", {})
    if not isinstance(features_raw, Mapping):
        msg = "'[features]' must be a TOML table"
        raise ConfigurationError(msg)
    features_mapping = cast("Mapping[str, object]", features_raw)

    features: dict[str, FeatureConfig] = {}
    for feature_id, raw_feature_data in features_mapping.items():
        if not _FEATURE_ID_PATTERN.fullmatch(feature_id):
            msg = f"Invalid feature ID '{feature_id}'"
            raise ConfigurationError(msg)
        if not isinstance(raw_feature_data, Mapping):
            msg = f"Feature '{feature_id}' configuration must be a TOML table"
            raise ConfigurationError(msg)
        feature_data = cast("Mapping[str, object]", raw_feature_data)
        enabled = feature_data.get("enabled", True)
        if not isinstance(enabled, bool):
            msg = f"Feature '{feature_id}'.enabled must be a boolean"
            raise ConfigurationError(msg)
        if "config" in feature_data:
            config_val = feature_data["config"]
            if not isinstance(config_val, Mapping):
                msg = f"Feature '{feature_id}'.config must be a TOML table"
                raise ConfigurationError(msg)
            config_mapping = cast("Mapping[str, object]", config_val)
            unexpected = set(feature_data) - {"enabled", "config"}
            if unexpected:
                msg = (
                    f"Feature '{feature_id}' mixes a .config table with inline "
                    f"configuration keys: {sorted(unexpected)}"
                )
                raise ConfigurationError(msg)
            parsed_config = dict(config_mapping)
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


def _parse_providers(raw: Mapping[str, object]) -> dict[str, str]:
    providers_raw = raw.get("providers", {})
    if not isinstance(providers_raw, Mapping):
        msg = "'[providers]' must be a TOML table"
        raise ConfigurationError(msg)
    providers_mapping = cast("Mapping[str, object]", providers_raw)
    providers: dict[str, str] = {}
    for capability_key, raw_feature_id in providers_mapping.items():
        if not isinstance(raw_feature_id, str):
            msg = (
                "Provider selections must map capability strings to feature-ID strings"
            )
            raise ConfigurationError(msg)
        capability = capability_key.strip()
        feature_id = raw_feature_id.strip()
        _validate_provider_selection(capability, feature_id)
        providers[capability] = feature_id
    return providers


def _parse_int_field(table: Mapping[str, object], key: str, default: int) -> int:
    val = table.get(key, default)
    if not isinstance(val, int) or isinstance(val, bool):
        msg = f"'[logging].{key}' must be an integer"
        raise ConfigurationError(msg)
    return val


def _parse_str_field(table: Mapping[str, object], key: str, default: str) -> str:
    val = table.get(key, default)
    if not isinstance(val, str):
        msg = f"'[logging].{key}' must be a string"
        raise ConfigurationError(msg)
    return val


def _parse_bool_field(table: Mapping[str, object], key: str, default: bool) -> bool:
    val = table.get(key, default)
    if not isinstance(val, bool):
        msg = f"'[logging].{key}' must be a boolean"
        raise ConfigurationError(msg)
    return val


def _parse_path_or_none(
    table: Mapping[str, object], key: str, default: str | None = None
) -> Path | str | None:
    val = table.get(key, default)
    if val is not None and not isinstance(val, (str, Path)):
        msg = f"'[logging].{key}' must be a string, path, or null"
        raise ConfigurationError(msg)
    return val


def _parse_logging(raw: Mapping[str, object]) -> LoggingConfig:
    logging_raw = raw.get("logging")
    if logging_raw is None:
        return LoggingConfig()
    if not isinstance(logging_raw, Mapping):
        msg = "'[logging]' must be a TOML table"
        raise ConfigurationError(msg)
    logging_mapping = cast("Mapping[str, object]", logging_raw)

    unknown_keys = set(logging_mapping) - {
        "level",
        "console",
        "file_path",
        "log_directory",
        "max_bytes",
        "backup_count",
        "capture_capacity",
        "format",
        "colorize",
        "retention_days",
        "compression",
    }
    if unknown_keys:
        msg = "Unknown keys in [logging]: " + ", ".join(sorted(unknown_keys))
        raise ConfigurationError(msg)

    cfg = LoggingConfig(
        level=_parse_str_field(logging_mapping, "level", "INFO"),
        console=_parse_bool_field(logging_mapping, "console", True),
        file_path=_parse_path_or_none(logging_mapping, "file_path", None),
        log_directory=_parse_path_or_none(
            logging_mapping, "log_directory", "data/logs"
        ),
        max_bytes=_parse_int_field(logging_mapping, "max_bytes", 10 * 1024 * 1024),
        backup_count=_parse_int_field(logging_mapping, "backup_count", 5),
        capture_capacity=_parse_int_field(logging_mapping, "capture_capacity", 1000),
        format=_parse_str_field(logging_mapping, "format", "text"),
        colorize=_parse_bool_field(logging_mapping, "colorize", True),
        retention_days=_parse_int_field(logging_mapping, "retention_days", 30),
        compression=_parse_str_field(logging_mapping, "compression", "zip"),
    )
    try:
        cfg.validate()
    except ValueError as err:
        raise ConfigurationError(str(err)) from err
    return cfg


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

    raw_mapping = cast("Mapping[str, object]", raw)

    if "profile" in raw_mapping:
        _parse_profile(raw_mapping)
    unknown_top_level = set(raw_mapping) - _ALLOWED_TOP_LEVEL
    if unknown_top_level:
        msg = "Unknown top-level configuration sections: " + ", ".join(
            sorted(unknown_top_level)
        )
        raise ConfigurationError(msg)
    return AppConfig(
        profile=_parse_profile(raw_mapping),
        features=_parse_features(raw_mapping),
        provider_selections=_parse_providers(raw_mapping),
        logging=_parse_logging(raw_mapping),
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
