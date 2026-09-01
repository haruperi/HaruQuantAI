"""Private Strategy mutation persistence, policy load, and publication."""

from __future__ import annotations

import hashlib
from typing import Any

from app.composition.logging import get_logger
from app.contracts.common.models import create_audit_event
from app.kernel.identity import generate_id
from app.services.data import is_data_error, persist_audit_event
from app.services.strategy.contracts.outcomes import (
    StrategyMutationResult,
)
from app.services.strategy.contracts.policy import StrategyValidationPolicy
from app.services.strategy.contracts.references import (  # noqa: TC001
    StrategyRef,
)
from app.services.strategy.contracts.responses import (
    StrategyOperationError,
    unwrap_data_response,
)
from app.services.strategy.migrations.definitions import _ensure_strategy_storage
from app.services.strategy.persistence import (
    read_strategy_mutation_record,
    read_strategy_policy_record,
    update_strategy_mutation_publication,
)

type AuthContext = Any

logger = get_logger(__name__)

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
    rows = read_strategy_mutation_record(command_id, request_id)
    if not rows:
        return None
    return StrategyMutationResult.model_validate_json(str(rows[0]["mutation_json"]))


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
    rows = read_strategy_policy_record(ref.strategy_id, version, request_id)
    if not rows:
        return None
    return StrategyValidationPolicy.model_validate_json(str(rows[0]["policy_json"]))


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
        unwrap_data_response(
            persist_audit_event(
                create_audit_event(
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
            ),
            operation="data.persist_audit_event.strategy_mutation",
        )
        published = mutation.model_copy(
            update={"audit_event_ref": event_id, "publication_pending": False}
        )
        update_strategy_mutation_publication(published, command_id)
        return published
    except Exception as error:
        if not (is_data_error(error) or isinstance(error, StrategyOperationError)):
            raise
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
