"""Strategy registry, version, configuration, and definition query operations."""

from collections.abc import Mapping
from typing import Any

from app.services.data import is_data_error
from app.services.strategy.contracts.enums import StrategyLifecycleStatus
from app.services.strategy.contracts.manifest import StrategyManifest
from app.services.strategy.contracts.outcomes import failure
from app.services.strategy.contracts.policy import StrategyValidationPolicy
from app.services.strategy.contracts.references import (
    ValidatedStrategyConfig,
    ValidatedStrategyRef,
)
from app.services.strategy.contracts.responses import guard_strategy_boundary
from app.services.strategy.diagnostics.errors import StrategyErrorCode
from app.services.strategy.persistence.read import (
    read_strategy_config_record,
    read_strategy_configs,
    read_strategy_definitions,
    read_strategy_versions,
)
from app.utils import generate_id, get_logger

logger = get_logger(__name__)


@guard_strategy_boundary
def list_strategy_definitions() -> tuple[Mapping[str, Any], ...]:
    """List stable definitions registered across versions.

    Returns:
        Tuple of registered Strategy definition dictionary mappings.
    """
    logger.info("Listing stable Strategy definitions")
    request_id = generate_id("req")
    rows = read_strategy_definitions(request_id)
    return tuple(dict(row) for row in rows)


@guard_strategy_boundary
def get_strategy_definition(
    strategy_id: str,
) -> Mapping[str, Any]:
    """Get one stable Strategy definition by strategy_id.

    Args:
        strategy_id: Unique Strategy identifier.

    Returns:
        Strategy definition dictionary mapping.
    """
    logger.info("Getting Strategy definition for %s", strategy_id)
    request_id = generate_id("req")
    rows = read_strategy_definitions(request_id, strategy_id=strategy_id)
    if not rows:
        failure(
            StrategyErrorCode.NOT_FOUND,
            f"Strategy definition not found for id: {strategy_id}",
            request_id=request_id,
        )
    return dict(rows[0])


@guard_strategy_boundary
def list_strategy_versions(
    strategy_id: str | None = None,
    *,
    _runtime_profile: str = "RESEARCH",
) -> tuple[ValidatedStrategyRef, ...]:
    """List immutable Strategy versions matching optional filters.

    Args:
        strategy_id: Optional Strategy identifier filter.
        _runtime_profile: Optional runtime profile filter.

    Returns:
        Tuple of public validated references.
    """
    logger.info("Listing immutable Strategy versions")
    request_id = generate_id("req")
    correlation_id = generate_id("cor")
    try:
        rows = read_strategy_versions(request_id, strategy_id=strategy_id)
    except Exception as error:
        if not is_data_error(error):
            raise
        logger.warning("Strategy versions query failed")
        failure(
            StrategyErrorCode.INTERNAL_ERROR,
            "strategy versions query failed",
            request_id=request_id,
            correlation_id=correlation_id,
        )
    if strategy_id is not None and not rows:
        failure(
            StrategyErrorCode.NOT_FOUND,
            f"Strategy versions not found for id: {strategy_id}",
            request_id=request_id,
            correlation_id=correlation_id,
        )
    return tuple(_row_to_ref(row, request_id, correlation_id) for row in rows)


@guard_strategy_boundary
def list_strategy_configs(
    strategy_id: str,
    strategy_version: str,
    *,
    _runtime_profile: str = "RESEARCH",
) -> tuple[ValidatedStrategyConfig, ...]:
    """List parameter configurations for one Strategy version.

    Args:
        strategy_id: Exact Strategy identifier.
        strategy_version: Exact Strategy version.
        _runtime_profile: Optional runtime profile filter.

    Returns:
        Tuple of validated configurations.
    """
    logger.info("Listing strategy configs for %s@%s", strategy_id, strategy_version)
    request_id = generate_id("req")
    rows = read_strategy_configs(strategy_id, strategy_version, request_id)
    configs = []
    for row in rows:
        cfg = ValidatedStrategyConfig.model_validate_json(str(row["config_json"]))
        configs.append(cfg)
    return tuple(configs)


@guard_strategy_boundary
def resolve_strategy_config(
    config_id: str,
) -> ValidatedStrategyConfig:
    """Resolve one immutable validated configuration by config_id.

    Args:
        config_id: Unique configuration identifier.

    Returns:
        Resolved validated configuration.
    """
    logger.info("Resolving strategy config for id %s", config_id)
    request_id = generate_id("req")
    rows = read_strategy_config_record(config_id, request_id)
    if not rows:
        failure(
            StrategyErrorCode.NOT_FOUND,
            f"Strategy configuration not found for id: {config_id}",
            request_id=request_id,
        )
    row = rows[0]
    return ValidatedStrategyConfig.model_validate_json(str(row["config_json"]))


def _row_to_ref(
    row: Mapping[str, object],
    request_id: str,
    correlation_id: str,
) -> ValidatedStrategyRef:
    """Convert one normalized Data row to a public registry reference.

    Args:
        row: Normalized database row mapping.
        request_id: Tracing request identifier.
        correlation_id: Tracing correlation identifier.

    Returns:
        ValidatedStrategyRef contract instance.
    """
    logger.debug("Converting Strategy registry row to public contract")
    manifest = StrategyManifest.model_validate_json(str(row["manifest_json"]))
    policy = StrategyValidationPolicy.model_validate_json(str(row["policy_json"]))
    return ValidatedStrategyRef(
        manifest=manifest,
        lifecycle_status=StrategyLifecycleStatus(str(row["lifecycle_status"])),
        environment=manifest.permitted_environments[0],
        policy_version=policy.policy_version,
        validation_policy=policy,
        registry_record_hash=str(row["record_hash"]),
        request_id=request_id,
        correlation_id=correlation_id,
    )


__all__ = [
    "get_strategy_definition",
    "list_strategy_configs",
    "list_strategy_definitions",
    "list_strategy_versions",
    "resolve_strategy_config",
]
