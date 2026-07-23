"""Deterministic immutable Strategy registry listing."""

from __future__ import annotations

from collections.abc import Mapping

from app.services.data.contracts import DataError
from app.services.data.persistence import execute_transaction
from app.services.data.persistence.contracts import (
    StatementPlan,
    TransactionRequest,
)
from app.services.strategy.contracts.enums import StrategyLifecycleStatus
from app.services.strategy.contracts.manifest import StrategyManifest
from app.services.strategy.contracts.outcomes import (
    StrategyOutcome,
    failure,
    success,
)
from app.services.strategy.contracts.policy import StrategyValidationPolicy
from app.services.strategy.contracts.references import (
    ValidatedStrategyRef,
)
from app.services.strategy.diagnostics.errors import StrategyErrorCode
from app.services.strategy.registry.migrations import _ensure_strategy_storage
from app.utils import generate_id, logger


def list_strategy_versions(
    strategy_id: str | None = None,
) -> StrategyOutcome[tuple[ValidatedStrategyRef, ...]]:
    """List immutable registry versions in deterministic order.

    Args:
        strategy_id: Optional exact strategy filter.

    Returns:
        Ordered validated references or a missing-id error.
    """
    logger.info("Listing immutable Strategy versions")
    request_id = generate_id("req")
    correlation_id = generate_id("cor")
    try:
        _ensure_strategy_storage(request_id)
        if strategy_id is None:
            statement = (
                "SELECT manifest_json, lifecycle_status, policy_json, record_hash "
                "FROM strategy_versions ORDER BY strategy_id, strategy_version"
            )
            params: tuple[str, ...] = ()
        else:
            statement = (
                "SELECT manifest_json, lifecycle_status, policy_json, record_hash "
                "FROM strategy_versions WHERE strategy_id = ? ORDER BY strategy_id, "
                "strategy_version"
            )
            params = (strategy_id,)
        result = execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=(statement,),
                    parameter_sets=(params,),
                    max_rows=1_000,
                ),
                request_id=request_id,
            )
        )
    except DataError:
        return failure(
            StrategyErrorCode.INTERNAL_ERROR,
            "strategy registry read failed",
            request_id=request_id,
            correlation_id=correlation_id,
        )
    if strategy_id is not None and not result.rows:
        return failure(
            StrategyErrorCode.NOT_FOUND,
            "strategy was not found",
            request_id=request_id,
            correlation_id=correlation_id,
        )
    refs = tuple(_row_to_ref(row, request_id, correlation_id) for row in result.rows)
    return success(refs)


def _row_to_ref(
    row: Mapping[str, object],
    request_id: str,
    correlation_id: str,
) -> ValidatedStrategyRef:
    """Convert one normalized Data row to a public registry reference.

    Args:
        row: Normalized Data-owned row mapping.
        request_id: Request trace identifier.
        correlation_id: Correlation trace identifier.

    Returns:
        Public immutable validated reference.
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


__all__ = ["list_strategy_versions"]
