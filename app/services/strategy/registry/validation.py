"""Strategy registry reference and declarative configuration validation."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping

from app.services.data.contracts import DataError, StatementPlan, TransactionRequest
from app.services.data.storage import execute_transaction
from app.services.strategy.contracts.models import (
    JsonValue,
    StrategyConfig,
    StrategyLifecycleStatus,
    StrategyManifest,
    StrategyRef,
    StrategyValidationPolicy,
    ValidatedStrategyConfig,
    ValidatedStrategyRef,
)
from app.services.strategy.contracts.outcomes import StrategyOutcome, failure, success
from app.services.strategy.diagnostics.errors import StrategyErrorCode
from app.services.strategy.registry.migrations import ensure_strategy_storage
from app.utils import canonical_json, logger


def validate_strategy_ref(
    ref: StrategyRef,
    policy: StrategyValidationPolicy,
) -> StrategyOutcome[ValidatedStrategyRef]:
    """Resolve and validate exactly one approved immutable strategy version.

    Args:
        ref: Caller-supplied version reference.
        policy: Explicit current validation policy.

    Returns:
        One validated exact reference or a deterministic failure.
    """
    logger.info("Validating Strategy reference for %s", ref.strategy_id)
    try:
        ensure_strategy_storage(ref.request_id)
        result = execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=(
                        "SELECT manifest_json, lifecycle_status, policy_json, "
                        "record_hash, request_id, correlation_id FROM "
                        "strategy_versions WHERE strategy_id = ? ORDER BY "
                        "strategy_version",
                    ),
                    parameter_sets=((ref.strategy_id,),),
                    max_rows=1_000,
                ),
                request_id=ref.request_id,
            )
        )
    except DataError:
        logger.error("Strategy reference persistence read failed")
        return failure(
            StrategyErrorCode.INTERNAL_ERROR,
            "strategy registry read failed",
            request_id=ref.request_id,
            correlation_id=ref.correlation_id,
        )
    matches: list[ValidatedStrategyRef] = []
    for row in result.rows:
        manifest = StrategyManifest.model_validate_json(str(row["manifest_json"]))
        if not _version_matches(manifest.strategy_version, ref):
            continue
        validated = _validate_record(
            manifest,
            StrategyLifecycleStatus(str(row["lifecycle_status"])),
            str(row["record_hash"]),
            ref,
            policy,
        )
        if validated.status == "success" and validated.data is not None:
            matches.append(validated.data)
        elif validated.status == "error":
            return validated
    if len(matches) != 1:
        code = (
            StrategyErrorCode.NOT_FOUND
            if not result.rows
            else StrategyErrorCode.VERSION_CONSTRAINT_UNSATISFIABLE
        )
        return failure(
            code,
            "strategy reference did not resolve to exactly one approved version",
            request_id=ref.request_id,
            correlation_id=ref.correlation_id,
        )
    return success(matches[0])


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


def _version_matches(version: str, ref: StrategyRef) -> bool:
    """Return whether one stored version matches a caller selector.

    Args:
        version: Stored exact version.
        ref: Caller selector.

    Returns:
        Whether the version matches.
    """
    logger.debug("Matching Strategy version constraint")
    if ref.exact_version is not None:
        return version == ref.exact_version
    constraint = ref.version_constraint or ""
    if constraint == "*":
        return True
    if constraint.startswith("=="):
        return version == constraint[2:]
    return version == constraint


def _validate_record(
    manifest: StrategyManifest,
    lifecycle: StrategyLifecycleStatus,
    record_hash: str,
    ref: StrategyRef,
    policy: StrategyValidationPolicy,
) -> StrategyOutcome[ValidatedStrategyRef]:
    """Validate one resolved registry record.

    Args:
        manifest: Stored immutable manifest.
        lifecycle: Stored lifecycle state.
        record_hash: Stored registry hash.
        ref: Caller reference.
        policy: Current validation policy.

    Returns:
        A validated reference or deterministic error.
    """
    logger.debug("Validating resolved Strategy registry record")
    if lifecycle is not StrategyLifecycleStatus.APPROVED:
        return failure(
            StrategyErrorCode.LIFECYCLE_NOT_APPROVED,
            "strategy lifecycle is not approved",
            request_id=ref.request_id,
            correlation_id=ref.correlation_id,
        )
    if ref.environment not in manifest.permitted_environments:
        return failure(
            StrategyErrorCode.ENVIRONMENT_NOT_PERMITTED,
            "strategy is not permitted in the requested environment",
            request_id=ref.request_id,
            correlation_id=ref.correlation_id,
        )
    if not any(
        manifest.module_path == root or manifest.module_path.startswith(f"{root}.")
        for root in policy.approved_module_roots
    ):
        return failure(
            StrategyErrorCode.UNAPPROVED_MODULE,
            "strategy module is outside approved roots",
            request_id=ref.request_id,
            correlation_id=ref.correlation_id,
        )
    return success(
        ValidatedStrategyRef(
            manifest=manifest,
            lifecycle_status=lifecycle,
            environment=ref.environment,
            policy_version=policy.policy_version,
            validation_policy=policy,
            registry_record_hash=record_hash,
            request_id=ref.request_id,
            correlation_id=ref.correlation_id,
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


__all__ = ["validate_strategy_config", "validate_strategy_ref"]
