"""Update operations for Research-owned expectancy governance transitions."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from app.composition.logging import get_logger
from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
    run_domain_migrations,
)
from app.services.research.contracts.errors import (
    ConfigurationError,
    ValidationError,
)
from app.services.research.migrations import build_research_migration_request

logger = get_logger(__name__)
_TRANSITION_STATEMENT_COUNT = 2


def update_expectancy_governance(
    *,
    profile_id: str,
    source_state: str,
    governance_state: str,
    reviewer: str,
    decision: str,
    reason: str,
    superseded_by: str,
    request_id: str,
) -> Mapping[str, object]:
    """Advance one expectancy profile's append-only governance lifecycle.

    Profiles are never hard-deleted; corrections advance ``governance_state``
    to ``revoked`` or ``superseded`` so the audit trail is preserved (settled
    decision: financial records are append-only).

    Args:
        profile_id: Stable surrogate governance identity.
        source_state: Expected current lifecycle state.
        governance_state: Target lifecycle state.
        reviewer: Reviewer principal recording the transition.
        decision: Recorded governance decision label.
        reason: Recorded governance decision reason.
        superseded_by: Surrogate identity superseding this profile, if any.
        request_id: Request trace identifier.

    Returns:
        Detached normalized transition acknowledgement.

    Raises:
        ConfigurationError: If the request identifier is invalid.
        ValidationError: If migration or transition cannot be confirmed.
    """
    if not request_id or request_id != request_id.strip():
        raise ConfigurationError("RES_CONFIGURATION_INVALID", "INVALID_REQUEST_ID")
    logger.info(
        "Transitioning Research expectancy %s to %s", profile_id, governance_state
    )
    migration = run_domain_migrations(
        cast("Any", build_research_migration_request(request_id))
    )
    if migration.status != "success" or migration.data is None:
        raise ValidationError("RES_PERSISTENCE_FAILED", "MIGRATION_FAILED")
    update_statement = """UPDATE research_expectancy_profiles SET
        governance_state = ?, reviewer = ?, decision = ?, reason = ?,
        superseded_by = ?,
        updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
        WHERE profile_id = ? AND governance_state = ?"""
    history_statement = """INSERT INTO research_expectancy_transitions (
        profile_id, source_state, target_state, reviewer, decision, reason,
        superseded_by, request_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
    update_parameters = (
        governance_state,
        reviewer,
        decision,
        reason,
        superseded_by,
        profile_id,
        source_state,
    )
    history_parameters = (
        profile_id,
        source_state,
        governance_state,
        reviewer,
        decision,
        reason,
        superseded_by,
        request_id,
    )
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(update_statement, history_statement),
                parameter_sets=(
                    cast("tuple[Any, ...]", update_parameters),
                    cast("tuple[Any, ...]", history_parameters),
                ),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    if response.status != "success" or response.data is None:
        raise ValidationError("RES_PERSISTENCE_FAILED", "EXPECTANCY_TRANSITION_FAILED")
    result = cast("Any", response.data)
    if result.affected_rows != _TRANSITION_STATEMENT_COUNT:
        raise ValidationError("RES_PERSISTENCE_FAILED", "EXPECTANCY_STATE_CONFLICT")
    return {
        "profile_id": profile_id,
        "governance_state": governance_state,
        "reviewer": reviewer,
        "decision": decision,
        "superseded_by": superseded_by,
    }


__all__ = ("update_expectancy_governance",)
