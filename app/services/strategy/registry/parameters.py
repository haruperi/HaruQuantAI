"""Immutable Strategy parameter-version recording."""

from __future__ import annotations

from typing import Any

from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
    is_data_error,
)
from app.services.strategy.contracts.outcomes import (
    StrategyMutationResult,
    failure,
    success,
)
from app.services.strategy.contracts.requests import (  # noqa: TC001
    StrategyParameterUpdateRequest,
)
from app.services.strategy.contracts.responses import (
    StrategyOperationError,
    guard_strategy_boundary,
    unwrap_data_response,
    unwrap_strategy_response,
)
from app.services.strategy.diagnostics.errors import StrategyErrorCode
from app.services.strategy.migrations.definitions import _ensure_strategy_storage
from app.services.strategy.registry._mutations import (
    _UPDATE_PERMISSION,
    _load_mutation,
    _load_policy,
    _mutation_id,
    _publish_mutation,
)
from app.services.strategy.registry.configuration import validate_strategy_config
from app.services.strategy.registry.resolution import validate_strategy_ref
from app.utils import get_logger

type AuthContext = Any

logger = get_logger(__name__)


@guard_strategy_boundary
def update_strategy_parameters(  # noqa: PLR0911
    request: StrategyParameterUpdateRequest,
    auth: AuthContext,
) -> StrategyMutationResult:
    """Validate and persist one immutable configuration hash.

    Args:
        request: Parameter update command.
        auth: Authenticated principal and trace context.

    Returns:
        Accepted, idempotent, or rejected mutation truth; infrastructure
        failures use the error branch.
    """
    logger.info("Updating Strategy parameters for %s", request.config.strategy_id)
    if _UPDATE_PERMISSION not in auth.permissions:
        return success(
            _rejected_update(request, "AUTHORIZATION_DENIED", auth.workflow_id)
        )
    policy_outcome = _load_policy(request.ref, request.request_id)
    if policy_outcome is None:
        return success(
            _rejected_update(request, "STRATEGY_NOT_FOUND", auth.workflow_id)
        )
    try:
        ref = unwrap_strategy_response(
            validate_strategy_ref(request.ref, policy_outcome),
            operation="strategy.registry.validate_strategy_ref",
        )
    except StrategyOperationError:
        return success(
            _rejected_update(request, "REFERENCE_VALIDATION_FAILED", auth.workflow_id)
        )
    try:
        config = unwrap_strategy_response(
            validate_strategy_config(ref, request.config),
            operation="strategy.registry.validate_strategy_config",
        )
    except StrategyOperationError:
        return success(
            _rejected_update(request, "CONFIG_VALIDATION_FAILED", auth.workflow_id)
        )
    mutation = StrategyMutationResult(
        mutation_id=_mutation_id(request.command_id),
        mutation_type="UPDATE_PARAMETERS",
        status="ACCEPTED",
        strategy_id=config.strategy_id,
        strategy_version=config.strategy_version,
        validated_config=config,
        record_ref=config.config_hash,
        record_hash=config.config_hash,
        request_id=request.request_id,
        correlation_id=request.correlation_id,
        workflow_id=auth.workflow_id,
        completed_at=request.requested_at,
        publication_pending=True,
    )
    try:
        _ensure_strategy_storage(request.request_id)
        existing = _load_mutation(request.command_id, request.request_id)
        if existing is not None:
            return success(existing.model_copy(update={"status": "IDEMPOTENT"}))
        unwrap_data_response(
            execute_transaction(
                build_transaction_request(
                    plan=build_statement_plan(
                        statements=(
                            "INSERT OR IGNORE INTO strategy_configs (strategy_id, "
                            "strategy_version, config_hash, config_json, "
                            "policy_version, "
                            "request_id) VALUES (?, ?, ?, ?, ?, ?)",
                            "INSERT INTO strategy_mutations (command_id, "
                            "mutation_json, "
                            "publication_pending) VALUES (?, ?, 1)",
                        ),
                        parameter_sets=(
                            (
                                config.strategy_id,
                                config.strategy_version,
                                config.config_hash,
                                config.model_dump_json(),
                                config.policy_version,
                                request.request_id,
                            ),
                            (request.command_id, mutation.model_dump_json()),
                        ),
                        max_rows=2,
                    ),
                    request_id=request.request_id,
                )
            ),
            operation="data.execute_transaction.strategy_parameter_mutation",
        )
    except Exception as error:
        if not is_data_error(error):
            raise
        logger.exception("Strategy parameter persistence failed")
        return failure(
            StrategyErrorCode.INTERNAL_ERROR,
            "strategy parameter persistence failed",
            request_id=request.request_id,
            correlation_id=request.correlation_id,
        )
    return success(_publish_mutation(mutation, request.command_id, auth))


def _rejected_update(
    request: StrategyParameterUpdateRequest, reason: str, workflow_id: str
) -> StrategyMutationResult:
    """Build a rejected parameter update result.

    Args:
        request: Parameter update command.
        reason: Stable rejection reason.
        workflow_id: Workflow trace identifier.

    Returns:
        Rejected mutation truth.
    """
    logger.info("Rejecting Strategy parameter update: %s", reason)
    return StrategyMutationResult(
        mutation_id=_mutation_id(request.command_id),
        mutation_type="UPDATE_PARAMETERS",
        status="REJECTED",
        strategy_id=request.config.strategy_id,
        strategy_version=request.config.strategy_version,
        reason_codes=(reason,),
        request_id=request.request_id,
        correlation_id=request.correlation_id,
        workflow_id=workflow_id,
        completed_at=request.requested_at,
    )


__all__ = ["update_strategy_parameters"]
