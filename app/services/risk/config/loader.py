"""Configuration loading and caching for Risk Governance.

Handles JSON/YAML parsing, registry caching, environment overrides, and
canonical validation before instantiation. Performs no I/O at import-time.
"""

from __future__ import annotations

import json
import os
from decimal import Decimal
from pathlib import Path
from typing import Any

from pydantic import Field

from app.services.risk.config.schema import validate_risk_config
from app.services.risk.errors import RiskValidationError as ValidationError
from app.services.risk.models import RiskConfig, RiskContract
from app.utils.logger import logger

# PyYAML is used for YAML config parsing
try:
    import yaml
except ImportError:
    yaml = None

RiskConfigSource = str | Path | dict[str, Any]

CONFIGS_DIR = Path(__file__).resolve().parent.parent / "configs"

# Whitelisted keys that can be overridden via environment variables
APPROVED_OVERRIDE_KEYS = {
    "correlation_threshold",
    "max_risk_per_trade",
    "var_confidence",
    "es_confidence",
    "max_daily_loss_pct",
    "max_total_loss_pct",
    "max_margin_utilization_pct",
    "max_effective_leverage",
}


class RiskConfigHash(RiskContract):
    """Container for a stable configuration profile hash."""

    profile_name: str = Field(..., description="Name of the risk profile.")
    config_hash: str = Field(..., description="Stable SHA256 configuration hash.")


class RiskProfileRegistry:
    """Registry of loaded risk configuration profiles."""

    def __init__(self) -> None:
        self._profiles: dict[str, RiskConfig] = {}

    def register(self, profile_name: str, config: RiskConfig) -> None:
        """Register a profile in the registry."""
        self._profiles[profile_name] = config

    def get(self, profile_name: str) -> RiskConfig | None:
        """Get a registered profile by name."""
        return self._profiles.get(profile_name)

    def clear(self) -> None:
        """Clear all registered profiles."""
        self._profiles.clear()


# Global registry instance
_registry = RiskProfileRegistry()


class RiskConfigLoader:
    """Loader utility for parsing and caching risk configurations."""

    @staticmethod
    def load(profile_name: str, source: RiskConfigSource | None = None) -> RiskConfig:
        """Load configuration profile by name or source."""
        return load_risk_config(profile_name, source)

    @staticmethod
    def validate(config: RiskConfig) -> None:
        """Validate configuration object."""
        res = validate_risk_config(config)
        if not res["valid"]:
            raise ValidationError(res["message"])


def load_risk_config(
    profile_name: str, source: RiskConfigSource | None = None
) -> RiskConfig:
    """Load, parse, override, and validate a risk configuration profile.

    Args:
        profile_name: Name of the configuration profile.
        source: Explicit config dict, file path, or None to load from defaults.

    Returns:
        RiskConfig: The parsed and validated RiskConfig instance.

    Raises:
        ValidationError: If loading, parsing, or validation fails.
    """
    logger.info(f"Loading risk configuration for profile: {profile_name}")

    # Check cache first (only if loaded from name without custom source dict)
    if source is None:
        cached = _registry.get(profile_name)
        if cached is not None:
            logger.debug(f"Config cache hit for: {profile_name}")
            return cached

    # 1. Resolve raw content dictionary
    if isinstance(source, dict):
        raw_dict = source.copy()
    else:
        file_path = _resolve_config_path(profile_name, source)
        raw_dict = _read_config_file(file_path)

    # 2. Check schema/profile name consistency
    raw_dict.setdefault("profile_name", profile_name)
    _check_unknown_keys(profile_name, raw_dict)

    # 3. Apply Environment Overrides
    _apply_env_overrides(raw_dict)

    # 4. Instantiate and Validate Pydantic Contract model
    try:
        config = RiskConfig(**raw_dict)
    except Exception as e:
        msg = (
            f"Failed to instantiate RiskConfig model for profile '{profile_name}': {e}"
        )
        logger.error(msg)
        raise ValidationError(msg) from e

    # 5. Run Custom Validation Rules & Ceilings
    validation_res = validate_risk_config(config)
    if not validation_res["valid"]:
        logger.error(
            f"Validation failed for profile '{profile_name}': "
            f"{validation_res['message']}"
        )
        raise ValidationError(validation_res["message"])

    # 6. Cache successfully loaded built-in profile configurations
    if source is None:
        _registry.register(profile_name, config)

    logger.info(f"Config load successful for profile: {profile_name}")
    return config


def _resolve_config_path(profile_name: str, source: RiskConfigSource | None) -> Path:
    """Resolve file path for the configuration profile."""
    # 1. If source is explicitly provided as path/str, use that
    if isinstance(source, (str, Path)):
        file_path = Path(source)
        if file_path.exists():
            return file_path
        msg = f"Explicit configuration source file not found: {source}"
        raise ValidationError(msg)

    # 2. If profile_name itself is an existing file path, use that
    path_direct = Path(profile_name)
    if path_direct.exists() and path_direct.is_file():
        return path_direct

    # 3. Look in configs folder, checking .json, .yaml, and .yml extensions
    for ext in (".json", ".yaml", ".yml"):
        file_path = CONFIGS_DIR / f"{profile_name}{ext}"
        if file_path.exists():
            return file_path

    # Fallback/error if not found
    msg = f"Configuration profile '{profile_name}' not found under {CONFIGS_DIR}."
    logger.error(msg)
    raise ValidationError(msg)


def _read_config_file(file_path: Path) -> dict[str, Any]:
    """Read and parse configuration file (JSON or YAML)."""
    suffix = file_path.suffix.lower()
    if suffix in (".yaml", ".yml") and yaml is None:
        msg = "PyYAML package is not installed but YAML config requested."
        raise ValidationError(msg)

    try:
        with file_path.open(encoding="utf-8") as f:
            if suffix in (".yaml", ".yml"):
                raw_content = yaml.safe_load(f)
            else:
                raw_content = json.load(f)
    except Exception as e:
        msg = f"Failed to parse config from {file_path}: {e}"
        logger.error(msg)
        raise ValidationError(msg) from e

    if not isinstance(raw_content, dict):
        msg = f"Configuration content in {file_path} must be a dictionary."
        logger.error(msg)
        raise ValidationError(msg)

    return raw_content


def _check_unknown_keys(profile_name: str, raw_dict: dict[str, Any]) -> None:
    """Check for unknown configuration keys and reject non-experimental ones."""
    allowed_fields = set(RiskConfig.model_fields.keys())
    extra_keys = set(raw_dict.keys()) - allowed_fields
    for key in extra_keys:
        if key.startswith("experimental_") and raw_dict[key] is False:
            continue
        msg = f"Unknown configuration keys found in '{profile_name}': {key}"
        logger.error(msg)
        raise ValidationError(msg)


def _apply_env_overrides(raw_dict: dict[str, Any]) -> None:
    """Apply environment-specific overrides for whitelisted configuration keys."""
    allowed_fields = set(RiskConfig.model_fields.keys())
    for key in allowed_fields:
        env_val = os.getenv(f"HARUQUANT_RISK_{key.upper()}")
        if env_val is not None:
            if key not in APPROVED_OVERRIDE_KEYS:
                msg = f"Environment override not allowed for key: {key}"
                logger.error(msg)
                raise ValidationError(msg)
            # Apply override by coercing type
            field_info = RiskConfig.model_fields[key]
            field_type = field_info.annotation
            try:
                if field_type is Decimal:
                    raw_dict[key] = Decimal(env_val)
                elif field_type is int:
                    raw_dict[key] = int(env_val)
                elif field_type is float:
                    raw_dict[key] = float(env_val)
                elif field_type is bool:
                    raw_dict[key] = env_val.lower() in ("true", "1", "yes")
                else:
                    raw_dict[key] = env_val
            except Exception as e:
                msg = (
                    f"Failed to parse environment override for '{key}': {env_val} ({e})"
                )
                logger.error(msg)
                raise ValidationError(msg) from e
