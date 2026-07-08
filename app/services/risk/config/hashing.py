"""Stable, canonical, order-invariant hashing for Risk configuration profiles.

Allows auditing, tracking config identity, and validating token compatibility.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from app.utils.logger import logger
from app.utils.standard import canonical_json

if TYPE_CHECKING:
    from app.services.risk.models import RiskConfig
    from app.utils.validations import ValidationResult


@dataclass(frozen=True)
class ConfigHashComparison:
    """Comparison result of two risk configuration profiles."""

    identical: bool
    materially_changed: bool
    changed_fields: tuple[str, ...]


def _sort_dict_recursive(d: Any) -> Any:  # noqa: ANN401
    """Recursively sort dict keys for canonical serialization."""
    if isinstance(d, dict):
        return {k: _sort_dict_recursive(d[k]) for k in sorted(d.keys())}
    if isinstance(d, list):
        return [_sort_dict_recursive(x) for x in d]
    return d


def canonicalize_risk_config_for_hash(config: RiskConfig) -> dict[str, Any]:
    """Normalize a validated risk config into sorted JSON-safe hash material.

    Args:
        config: The RiskConfig instance.

    Returns:
        dict[str, Any]: Normalized JSON-safe dictionary.
    """
    logger.debug(f"Canonicalizing config for hash: {config.profile_name}")
    raw = config.model_dump(mode="json")
    return cast("dict[str, Any]", _sort_dict_recursive(raw))


def hash_risk_config(config: RiskConfig) -> str:
    """Generate a stable hash for decisions, tokens, audit events, and replay.

    Args:
        config: The RiskConfig instance.

    Returns:
        str: SHA256 hash.
    """
    logger.info(f"Hashing risk config: {config.profile_name}")
    normalized = canonicalize_risk_config_for_hash(config)
    serialized = canonical_json(normalized)
    h = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    logger.debug(f"Config hash generated: {h}")
    return h


def compare_risk_config_hashes(
    left: RiskConfig, right: RiskConfig
) -> ConfigHashComparison:
    """Compare two risk configurations and report differences.

    Args:
        left: Left RiskConfig.
        right: Right RiskConfig.

    Returns:
        ConfigHashComparison: The comparison result.
    """
    logger.info(f"Comparing risk configs: {left.profile_name} vs {right.profile_name}")
    left_dict = left.model_dump(mode="json")
    right_dict = right.model_dump(mode="json")

    # A material change is any configuration field change, excluding profile_name.
    changed_fields = []
    all_keys = set(left_dict.keys()) | set(right_dict.keys())
    for k in sorted(all_keys):
        if left_dict.get(k) != right_dict.get(k):
            changed_fields.append(k)

    identical = len(changed_fields) == 0
    materially_changed = any(k != "profile_name" for k in changed_fields)

    logger.debug(
        f"Comparison complete. Identical: {identical}, Changed fields: {changed_fields}"
    )
    return ConfigHashComparison(
        identical=identical,
        materially_changed=materially_changed,
        changed_fields=tuple(changed_fields),
    )


def validate_risk_config_hash(
    expected_hash: str, config: RiskConfig
) -> ValidationResult:
    """Verify that the config's hash matches the expected hash.

    Args:
        expected_hash: The SHA256 hash expected.
        config: The RiskConfig to verify.

    Returns:
        ValidationResult: The result of validation.
    """
    logger.info(f"Validating config hash. Expected: {expected_hash}")
    actual_hash = hash_risk_config(config)
    if actual_hash == expected_hash:
        logger.info("Config hash validation passed.")
        return {
            "valid": True,
            "message": "Configuration hash verification passed.",
            "code": "OK",
            "details": {"hash": actual_hash},
        }
    msg = f"Configuration hash mismatch: expected {expected_hash}, got {actual_hash}"
    logger.error(msg)
    return {
        "valid": False,
        "message": msg,
        "code": "VALIDATION_FAILED",
        "details": {"expected_hash": expected_hash, "actual_hash": actual_hash},
    }
