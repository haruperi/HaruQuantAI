"""Immutable Strategy registry and configuration persistence operations."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping

from app.services.data.contracts import DataError, StatementPlan, TransactionRequest
from app.services.data.storage import execute_transaction, persist_audit_event
from app.services.strategy.contracts.models import (
    StrategyLifecycleStatus,
    StrategyManifest,
    StrategyParameterUpdateRequest,
    StrategyRef,
    StrategyRegistrationRequest,
    StrategyValidationPolicy,
    ValidatedStrategyRef,
)
from app.services.strategy.contracts.outcomes import (
    StrategyMutationResult,
    StrategyOutcome,
    failure,
    success,
)
from app.services.strategy.diagnostics.errors import StrategyErrorCode
from app.services.strategy.registry.migrations import ensure_strategy_storage
from app.services.strategy.registry.validation import (
    validate_strategy_config,
    validate_strategy_ref,
)
from app.utils import AuditEvent, AuthContext, canonical_json, generate_id, logger

_REGISTER_PERMISSION = "strategy:register"
_UPDATE_PERMISSION = "strategy:update"


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
        environment=request.manifest.permitted_environments[0],
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
        ensure_strategy_storage(request.request_id)
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


def update_strategy_parameters(  # noqa: PLR0911
    request: StrategyParameterUpdateRequest,
    auth: AuthContext,
) -> StrategyOutcome[StrategyMutationResult]:
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
    ref_outcome = validate_strategy_ref(request.ref, policy_outcome)
    if ref_outcome.status == "error" or ref_outcome.data is None:
        return success(
            _rejected_update(request, "REFERENCE_VALIDATION_FAILED", auth.workflow_id)
        )
    config_outcome = validate_strategy_config(ref_outcome.data, request.config)
    if config_outcome.status == "error" or config_outcome.data is None:
        return success(
            _rejected_update(request, "CONFIG_VALIDATION_FAILED", auth.workflow_id)
        )
    config = config_outcome.data
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
        ensure_strategy_storage(request.request_id)
        existing = _load_mutation(request.command_id, request.request_id)
        if existing is not None:
            return success(existing.model_copy(update={"status": "IDEMPOTENT"}))
        execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=(
                        "INSERT OR IGNORE INTO strategy_configs (strategy_id, "
                        "strategy_version, config_hash, config_json, policy_version, "
                        "request_id) VALUES (?, ?, ?, ?, ?, ?)",
                        "INSERT INTO strategy_mutations (command_id, mutation_json, "
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
        )
    except DataError:
        logger.error("Strategy parameter persistence failed")
        return failure(
            StrategyErrorCode.INTERNAL_ERROR,
            "strategy parameter persistence failed",
            request_id=request.request_id,
            correlation_id=request.correlation_id,
        )
    return success(_publish_mutation(mutation, request.command_id, auth))


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
        ensure_strategy_storage(request_id)
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


def _load_mutation(command_id: str, request_id: str) -> StrategyMutationResult | None:
    """Load a prior mutation result by idempotency command identifier.

    Args:
        command_id: Stable caller command identifier.
        request_id: Request trace identifier.

    Returns:
        Prior mutation result or ``None``.
    """
    logger.debug("Loading prior Strategy mutation")
    result = execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(
                    "SELECT mutation_json FROM strategy_mutations WHERE command_id = ?",
                ),
                parameter_sets=((command_id,),),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    if not result.rows:
        return None
    return StrategyMutationResult.model_validate_json(
        str(result.rows[0]["mutation_json"])
    )


def _load_policy(ref: StrategyRef, request_id: str) -> StrategyValidationPolicy | None:
    """Load the host policy recorded with a strategy version.

    Args:
        ref: Exact strategy selector.
        request_id: Request trace identifier.

    Returns:
        Recorded policy or ``None``.
    """
    logger.debug("Loading recorded Strategy validation policy")
    ensure_strategy_storage(request_id)
    version = ref.exact_version
    if version is None:
        return None
    result = execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(
                    "SELECT policy_json FROM strategy_versions WHERE strategy_id = ? "
                    "AND strategy_version = ?",
                ),
                parameter_sets=((ref.strategy_id, version),),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    if not result.rows:
        return None
    return StrategyValidationPolicy.model_validate_json(
        str(result.rows[0]["policy_json"])
    )


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


def _publish_mutation(
    mutation: StrategyMutationResult,
    command_id: str,
    auth: AuthContext,
) -> StrategyMutationResult:
    """Publish mutation audit evidence and update publication state.

    Args:
        mutation: Committed mutation truth.
        command_id: Idempotency command identifier.
        auth: Authenticated principal.

    Returns:
        Mutation result with publication evidence or pending state.
    """
    logger.info("Publishing Strategy mutation audit evidence")
    event_id = generate_id("evt")
    try:
        persist_audit_event(
            AuditEvent(
                contract_version="v1",
                schema_id="utils.audit_event.v1",
                event_id=event_id,
                timestamp=mutation.completed_at,
                domain="strategy",
                action=mutation.mutation_type,
                principal_id=auth.principal_id,
                request_id=mutation.request_id,
                correlation_id=mutation.correlation_id,
                payload={
                    "mutation_id": mutation.mutation_id,
                    "status": mutation.status,
                    "strategy_id": mutation.strategy_id,
                    "strategy_version": mutation.strategy_version,
                },
            )
        )
        published = mutation.model_copy(
            update={"audit_event_ref": event_id, "publication_pending": False}
        )
        execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=(
                        "UPDATE strategy_mutations SET mutation_json = ?, "
                        "publication_pending = 0 WHERE command_id = ?",
                    ),
                    parameter_sets=((published.model_dump_json(), command_id),),
                    max_rows=1,
                ),
                request_id=mutation.request_id,
            )
        )
        return published
    except DataError:
        logger.warning("Strategy mutation audit publication remains pending")
        return mutation


def _mutation_id(command_id: str) -> str:
    """Derive a stable Strategy-owned mutation identifier.

    Args:
        command_id: Caller idempotency command identifier.

    Returns:
        Namespaced SHA-256 mutation identity.
    """
    logger.debug("Deriving stable Strategy mutation identity")
    digest = hashlib.sha256(command_id.encode("utf-8")).hexdigest()
    return f"mut-{digest}"


__all__ = [
    "list_strategy_versions",
    "register_strategy_version",
    "update_strategy_parameters",
]
