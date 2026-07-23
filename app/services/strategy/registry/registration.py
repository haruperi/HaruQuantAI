"""Immutable Strategy version registration."""

from __future__ import annotations

import hashlib

from app.services.data.contracts import DataError
from app.services.data.persistence import execute_transaction
from app.services.data.persistence.contracts import (
    StatementPlan,
    TransactionRequest,
)
from app.services.strategy.contracts.enums import StrategyLifecycleStatus
from app.services.strategy.contracts.outcomes import (
    StrategyMutationResult,
    StrategyOutcome,
    failure,
    success,
)
from app.services.strategy.contracts.policy import (
    StrategyValidationPolicy,  # noqa: TC001
)
from app.services.strategy.contracts.references import (
    ValidatedStrategyRef,
)
from app.services.strategy.contracts.requests import (  # noqa: TC001
    StrategyRegistrationRequest,
)
from app.services.strategy.diagnostics.errors import StrategyErrorCode
from app.services.strategy.registry._mutations import (
    _REGISTER_PERMISSION,
    _load_mutation,
    _mutation_id,
    _publish_mutation,
)
from app.services.strategy.registry.migrations import _ensure_strategy_storage
from app.utils import AuthContext, canonical_json, logger


def register_strategy_version(
    request: StrategyRegistrationRequest,
    auth: AuthContext,
    policy: StrategyValidationPolicy,
) -> StrategyOutcome[StrategyMutationResult]:
    """Register one unique immutable strategy version.

    Args:
        request: Registration command.
        auth: Authenticated principal and trace context.
        policy: Explicit validation policy.

    Returns:
        Accepted, idempotent, or rejected mutation truth; infrastructure
        failures use the error branch.
    """
    logger.info("Registering Strategy version %s", request.manifest.strategy_version)
    rejected = _registration_rejection(request, auth, policy)
    if rejected is not None:
        return success(rejected)
    (environment,) = request.manifest.permitted_environments
    record_material = {
        "manifest": request.manifest.model_dump(mode="json"),
        "lifecycle_status": request.lifecycle_status,
        "policy": policy.model_dump(mode="json"),
    }
    record_hash = hashlib.sha256(
        canonical_json(record_material).encode("utf-8")
    ).hexdigest()
    ref = ValidatedStrategyRef(
        manifest=request.manifest,
        lifecycle_status=request.lifecycle_status,
        environment=environment,
        policy_version=policy.policy_version,
        validation_policy=policy,
        registry_record_hash=record_hash,
        request_id=request.request_id,
        correlation_id=request.correlation_id,
    )
    mutation = StrategyMutationResult(
        mutation_id=_mutation_id(request.command_id),
        mutation_type="REGISTER_VERSION",
        status="ACCEPTED",
        strategy_id=request.manifest.strategy_id,
        strategy_version=request.manifest.strategy_version,
        validated_ref=ref,
        record_ref=f"{request.manifest.strategy_id}@{request.manifest.strategy_version}",
        record_hash=record_hash,
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
        execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=(
                        "INSERT INTO strategy_versions (strategy_id, "
                        "strategy_version, manifest_json, lifecycle_status, "
                        "policy_json, record_hash, request_id, correlation_id) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        "INSERT INTO strategy_mutations (command_id, mutation_json, "
                        "publication_pending) VALUES (?, ?, 1)",
                    ),
                    parameter_sets=(
                        (
                            request.manifest.strategy_id,
                            request.manifest.strategy_version,
                            request.manifest.model_dump_json(),
                            request.lifecycle_status.value,
                            policy.model_dump_json(),
                            record_hash,
                            request.request_id,
                            request.correlation_id,
                        ),
                        (request.command_id, mutation.model_dump_json()),
                    ),
                    max_rows=2,
                ),
                request_id=request.request_id,
            )
        )
    except DataError as error:
        logger.warning("Strategy registration persistence outcome: %s", error.code)
        if error.code == "DB_WRITE_FAILED":
            return success(
                _rejected_registration(
                    request, "IMMUTABLE_VERSION_EXISTS", auth.workflow_id
                )
            )
        return failure(
            StrategyErrorCode.INTERNAL_ERROR,
            "strategy registration persistence failed",
            request_id=request.request_id,
            correlation_id=request.correlation_id,
        )
    return success(_publish_mutation(mutation, request.command_id, auth))


def _registration_rejection(
    request: StrategyRegistrationRequest,
    auth: AuthContext,
    policy: StrategyValidationPolicy,
) -> StrategyMutationResult | None:
    """Return a deterministic registration rejection when applicable.

    Args:
        request: Registration command.
        auth: Authenticated principal.
        policy: Explicit validation policy.

    Returns:
        A rejected mutation or ``None``.
    """
    logger.debug("Checking Strategy registration preconditions")
    if _REGISTER_PERMISSION not in auth.permissions:
        return _rejected_registration(request, "AUTHORIZATION_DENIED", auth.workflow_id)
    if request.lifecycle_status is not StrategyLifecycleStatus.APPROVED:
        return _rejected_registration(
            request, "LIFECYCLE_NOT_APPROVED", auth.workflow_id
        )
    if not any(
        request.manifest.module_path == root
        or request.manifest.module_path.startswith(f"{root}.")
        for root in policy.approved_module_roots
    ):
        return _rejected_registration(request, "UNAPPROVED_MODULE", auth.workflow_id)
    if len(request.manifest.permitted_environments) != 1:
        return _rejected_registration(
            request, "AMBIGUOUS_ENVIRONMENT", auth.workflow_id
        )
    return None


def _rejected_registration(
    request: StrategyRegistrationRequest, reason: str, workflow_id: str
) -> StrategyMutationResult:
    """Build a rejected registration result.

    Args:
        request: Registration command.
        reason: Stable rejection reason.
        workflow_id: Workflow trace identifier.

    Returns:
        Rejected mutation truth.
    """
    logger.info("Rejecting Strategy registration: %s", reason)
    return StrategyMutationResult(
        mutation_id=_mutation_id(request.command_id),
        mutation_type="REGISTER_VERSION",
        status="REJECTED",
        strategy_id=request.manifest.strategy_id,
        strategy_version=request.manifest.strategy_version,
        reason_codes=(reason,),
        request_id=request.request_id,
        correlation_id=request.correlation_id,
        workflow_id=workflow_id,
        completed_at=request.requested_at,
    )


__all__ = ["register_strategy_version"]
