"""Read operations for Research-owned expectancy governance records."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
    run_domain_migrations,
)
from app.services.research.contracts.errors import ValidationError
from app.services.research.migrations import build_research_migration_request
from app.utils import get_logger

logger = get_logger(__name__)


def _confirm_migration(request_id: str) -> None:
    """Ensure the expectancy migration is applied before any read.

    Args:
        request_id: Request trace identifier.

    Raises:
        ValidationError: If migration cannot be confirmed.
    """
    migration = run_domain_migrations(
        cast("Any", build_research_migration_request(request_id))
    )
    if migration.status != "success" or migration.data is None:
        raise ValidationError("RES_PERSISTENCE_FAILED", "MIGRATION_FAILED")


def _read_rows(
    statement: str,
    parameters: tuple[object, ...],
    *,
    request_id: str,
    max_rows: int,
) -> tuple[Mapping[str, Any], ...]:
    """Execute one bounded Research governance read.

    Args:
        statement: Parameterized SQL read statement.
        parameters: Bound statement parameters.
        request_id: Request trace identifier.
        max_rows: Maximum accepted result rows.

    Returns:
        Ordered normalized governance rows.

    Raises:
        ValidationError: If Data rejects the read.
    """
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(statement,),
                parameter_sets=(parameters,),
                max_rows=max_rows,
            ),
            request_id=request_id,
        )
    )
    if response.status != "success" or response.data is None:
        raise ValidationError("RES_PERSISTENCE_FAILED", "EXPECTANCY_READ_FAILED")
    return tuple(cast("Any", response.data).rows)


def read_approved_expectancy_profile(
    *,
    profile_id: str,
    request_id: str,
) -> Mapping[str, Any] | None:
    """Return one approved expectancy profile row by surrogate identity.

    Args:
        profile_id: Stable surrogate governance identity.
        request_id: Request trace identifier.

    Returns:
        Normalized governance row, or ``None`` when no profile exists.

    Raises:
        ValidationError: If migration or read cannot be confirmed.
    """
    logger.info("Reading Research expectancy profile %s", profile_id)
    _confirm_migration(request_id)
    rows = _read_rows(
        "SELECT profile_id, exact_version, strategy_ref, hypothesis, "
        "match_keys_json, envelope_json, governance_state, reviewer, decision, "
        "reason, superseded_by, evidence_ref, canonical_hash FROM "
        "research_expectancy_profiles WHERE profile_id = ?",
        (profile_id,),
        request_id=request_id,
        max_rows=1,
    )
    return rows[0] if rows else None


def read_eligible_expectancy_profile(
    *,
    strategy_ref: str,
    request_id: str,
) -> Mapping[str, Any] | None:
    """Return the latest approved expectancy profile eligible for a strategy.

    Args:
        strategy_ref: Strategy identity covered by an approved profile.
        request_id: Request trace identifier.

    Returns:
        Normalized approved governance row, or ``None`` when none is eligible.

    Raises:
        ValidationError: If migration or read cannot be confirmed.
    """
    logger.info("Reading eligible Research expectancy for %s", strategy_ref)
    _confirm_migration(request_id)
    rows = _read_rows(
        "SELECT profile_id, exact_version, strategy_ref, hypothesis, "
        "match_keys_json, envelope_json, governance_state, reviewer, decision, "
        "reason, superseded_by, evidence_ref, canonical_hash FROM "
        "research_expectancy_profiles WHERE strategy_ref = ? "
        "AND governance_state = 'approved' "
        "ORDER BY updated_at DESC LIMIT 1",
        (strategy_ref,),
        request_id=request_id,
        max_rows=1,
    )
    return rows[0] if rows else None


__all__ = (
    "read_approved_expectancy_profile",
    "read_eligible_expectancy_profile",
)
