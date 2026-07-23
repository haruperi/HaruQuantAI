"""Private Strategy mutation persistence, policy load, and publication."""

from __future__ import annotations

import hashlib

from app.services.data.audit import persist_audit_event
from app.services.data.contracts import DataError
from app.services.data.persistence import execute_transaction
from app.services.data.persistence.contracts import (
    StatementPlan,
    TransactionRequest,
)
from app.services.strategy.contracts.outcomes import (
    StrategyMutationResult,
)
from app.services.strategy.contracts.policy import StrategyValidationPolicy
from app.services.strategy.contracts.references import (  # noqa: TC001
    StrategyRef,
)
from app.services.strategy.registry.migrations import _ensure_strategy_storage
from app.utils import AuditEvent, AuthContext, generate_id, logger

_REGISTER_PERMISSION = "strategy:register"
_UPDATE_PERMISSION = "strategy:update"


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
    _ensure_strategy_storage(request_id)
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


__all__: list[str] = []
