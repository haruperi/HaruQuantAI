"""Declarative Strategy configuration validation and canonical hashing."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping

from app.services.strategy.contracts._base import JsonValue  # noqa: TC001
from app.services.strategy.contracts.outcomes import StrategyOutcome, failure, success
from app.services.strategy.contracts.policy import (
    StrategyValidationPolicy,  # noqa: TC001
)
from app.services.strategy.contracts.references import (
    StrategyConfig,
    ValidatedStrategyConfig,
    ValidatedStrategyRef,
)
from app.services.strategy.diagnostics.errors import StrategyErrorCode
from app.utils import canonical_json, logger


def validate_strategy_config(
    ref: ValidatedStrategyRef,
    config: StrategyConfig,
) -> StrategyOutcome[ValidatedStrategyConfig]:
    """Validate declarative configuration and derive its canonical hash.

    Args:
        ref: Validated exact strategy reference.
        config: Untrusted declarative configuration.

    Returns:
        Normalized immutable configuration or a deterministic failure.
    """
    logger.info("Validating Strategy configuration for %s", ref.manifest.strategy_id)
    if (
        config.strategy_id != ref.manifest.strategy_id
        or config.strategy_version != ref.manifest.strategy_version
        or config.config_schema_version != ref.manifest.config_schema_version
    ):
        return failure(
            StrategyErrorCode.INVALID_CONFIG,
            "configuration identity does not match the validated strategy",
            request_id=config.request_id,
            correlation_id=ref.correlation_id,
        )
    policy = ref.validation_policy
    payload = canonical_json(config.parameters)
    if len(payload.encode("utf-8")) > policy.max_config_payload_bytes:
        return failure(
            StrategyErrorCode.RESOURCE_LIMIT_EXCEEDED,
            "configuration exceeds the approved payload budget",
            request_id=config.request_id,
            correlation_id=ref.correlation_id,
        )
    if not _within_limits(config.parameters, policy, depth=1):
        return failure(
            StrategyErrorCode.RESOURCE_LIMIT_EXCEEDED,
            "configuration exceeds approved structural limits",
            request_id=config.request_id,
            correlation_id=ref.correlation_id,
        )
    normalized = _apply_schema(config.parameters, ref.manifest.config_schema)
    if normalized is None:
        return failure(
            StrategyErrorCode.SCHEMA_VALIDATION_FAILED,
            "configuration does not satisfy the declared schema",
            request_id=config.request_id,
            correlation_id=ref.correlation_id,
        )
    config_hash = hashlib.sha256(canonical_json(normalized).encode("utf-8")).hexdigest()
    return success(
        ValidatedStrategyConfig(
            strategy_id=config.strategy_id,
            strategy_version=config.strategy_version,
            config_schema_version=config.config_schema_version,
            normalized_parameters=normalized,
            config_hash=config_hash,
            policy_version=policy.policy_version,
            request_id=config.request_id,
        )
    )


def _within_limits(
    value: JsonValue,
    policy: StrategyValidationPolicy,
    *,
    depth: int,
) -> bool:
    """Check recursive configuration bounds.

    Args:
        value: JSON-compatible value.
        policy: Explicit structural bounds.
        depth: Current nesting depth.

    Returns:
        Whether the value remains within every bound.
    """
    logger.debug("Checking Strategy configuration structural bounds")
    if depth > policy.max_config_nesting_depth:
        return False
    if isinstance(value, str):
        return len(value) <= policy.max_config_string_length and not any(
            marker in value.casefold()
            for marker in ("import ", "exec(", "eval(", "__", "file://")
        )
    if isinstance(value, Mapping):
        return len(value) <= policy.max_config_collection_items and all(
            _within_limits(item, policy, depth=depth + 1) for item in value.values()
        )
    if isinstance(value, tuple):
        return len(value) <= policy.max_config_collection_items and all(
            _within_limits(item, policy, depth=depth + 1) for item in value
        )
    return True


def _apply_schema(  # noqa: PLR0911
    parameters: Mapping[str, JsonValue],
    schema: Mapping[str, JsonValue],
) -> dict[str, JsonValue] | None:
    """Apply the approved object-schema subset with explicit defaults.

    Args:
        parameters: Caller parameters.
        schema: Manifest-owned declarative schema.

    Returns:
        Normalized parameters or ``None`` on validation failure.
    """
    logger.debug("Applying Strategy declarative configuration schema")
    properties_value = schema.get("properties", {})
    if not isinstance(properties_value, Mapping):
        return None
    required_value = schema.get("required", ())
    if not isinstance(required_value, tuple):
        return None
    required = {str(item) for item in required_value}
    if not required.issubset(parameters):
        return None
    if schema.get("additionalProperties", False) is not True and any(
        key not in properties_value for key in parameters
    ):
        return None
    normalized: dict[str, JsonValue] = dict(parameters)
    for key, raw_rule in properties_value.items():
        if not isinstance(raw_rule, Mapping):
            return None
        if key not in normalized and "default" in raw_rule:
            normalized[key] = raw_rule["default"]
        if key in normalized and not _matches_rule(normalized[key], raw_rule):
            return None
    return normalized


def _matches_rule(value: JsonValue, rule: Mapping[str, JsonValue]) -> bool:
    """Validate one value against the approved schema-rule subset.

    Args:
        value: Parameter value.
        rule: Declarative schema rule.

    Returns:
        Whether the value matches type, enum, and numeric bounds.
    """
    logger.debug("Validating one Strategy schema property")
    expected = rule.get("type")
    type_matches = {
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "object": isinstance(value, Mapping),
        "array": isinstance(value, tuple),
    }.get(str(expected), True)
    if not type_matches:
        return False
    enum_values = rule.get("enum")
    if isinstance(enum_values, tuple) and value not in enum_values:
        return False
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = rule.get("minimum")
        maximum = rule.get("maximum")
        if isinstance(minimum, (int, float)) and value < minimum:
            return False
        if isinstance(maximum, (int, float)) and value > maximum:
            return False
    return True


__all__ = ["validate_strategy_config"]
