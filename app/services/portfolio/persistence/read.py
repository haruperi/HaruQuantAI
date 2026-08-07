"""Read operations for Portfolio-owned relational records."""

from __future__ import annotations

import json
from collections.abc import Mapping

from app.services.portfolio.persistence.create import _execute, _require_store


def _one_row(
    statement: str, parameters: tuple[object, ...]
) -> Mapping[str, object] | None:
    """Read at most one normalized row.

    Returns:
        Stored row or ``None``.
    """
    rows = _execute((statement,), (parameters,)).rows
    return None if not rows else rows[0]


def read_construction_record(store: object, key: str) -> object | None:
    """Read one immutable construction by canonical hash.

    Returns:
        Decoded construction or ``None``.
    """
    row = _one_row(
        "SELECT result_json FROM portfolio_construction_results "
        "WHERE canonical_hash=? ORDER BY created_at DESC LIMIT 1",
        (key,),
    )
    if row is None:
        return None
    return _require_store(store).decode("construction", str(row["result_json"]))


def read_definition_record(
    store: object, portfolio_id: str, portfolio_version: str
) -> object | None:
    """Read one exact immutable Portfolio definition.

    Args:
        store: Portfolio persistence handle.
        portfolio_id: Stable Portfolio identity.
        portfolio_version: Exact immutable version.

    Returns:
        Decoded definition or ``None``.
    """
    row = _one_row(
        "SELECT definition_json FROM portfolio_definitions "
        "WHERE portfolio_id=? AND portfolio_version=?",
        (portfolio_id, portfolio_version),
    )
    if row is None:
        return None
    return _require_store(store).decode("definition", str(row["definition_json"]))


def read_active_allocation_record(
    store: object, portfolio_id: str, scope_key: str
) -> tuple[object, int] | None:
    """Read one active allocation and revision for an exact scope.

    Returns:
        Decoded allocation and revision, or ``None``.

    Raises:
        TypeError: If the stored revision is malformed.
    """
    row = _one_row(
        "SELECT versions.allocation_json, active.revision "
        "FROM portfolio_active_scopes active "
        "JOIN portfolio_allocation_versions versions ON "
        "versions.portfolio_id=active.portfolio_id AND "
        "versions.allocation_version=active.allocation_version "
        "WHERE active.portfolio_id=? AND active.scope_key=?",
        (portfolio_id, scope_key),
    )
    if row is None:
        return None
    value = _require_store(store).decode("allocation", str(row["allocation_json"]))
    revision = row["revision"]
    if not isinstance(revision, int):
        raise TypeError("stored Portfolio active revision is malformed")
    return value, revision


def read_allocation_record(
    store: object, portfolio_id: str, allocation_version: str
) -> object | None:
    """Read one immutable allocation version.

    Returns:
        Decoded allocation or ``None``.
    """
    row = _one_row(
        "SELECT allocation_json FROM portfolio_allocation_versions "
        "WHERE portfolio_id=? AND allocation_version=?",
        (portfolio_id, allocation_version),
    )
    if row is None:
        return None
    return _require_store(store).decode("allocation", str(row["allocation_json"]))


def read_allocation_history_records(
    store: object, portfolio_id: str
) -> tuple[Mapping[str, object], ...]:
    """Read ordered immutable allocation-history records.

    Returns:
        Ordered allocation payload mappings.
    """
    _require_store(store)
    rows = _execute(
        (
            "SELECT allocation_json FROM portfolio_allocation_versions "
            "WHERE portfolio_id=? ORDER BY activated_at ASC, allocation_id ASC "
            "LIMIT 1000",
        ),
        ((portfolio_id,),),
        max_rows=1_000,
    ).rows
    return tuple(
        {"allocation": json.loads(str(row["allocation_json"]))} for row in rows
    )


def read_idempotency_record(store: object, key: str) -> Mapping[str, object] | None:
    """Read one allocation idempotency binding.

    Returns:
        Normalized binding or ``None``.
    """
    _require_store(store)
    return _one_row(
        "SELECT material_hash, result_type, result_id FROM portfolio_idempotency "
        "WHERE idempotency_key=?",
        (key,),
    )


def read_plan_record(store: object, plan_id: str, plan_version: str) -> object | None:
    """Read one exact immutable rebalance-plan version.

    Returns:
        Decoded plan or ``None``.
    """
    row = _one_row(
        "SELECT plan_json FROM portfolio_rebalance_plans "
        "WHERE plan_id=? AND plan_version=?",
        (plan_id, plan_version),
    )
    if row is None:
        return None
    return _require_store(store).decode("plan", str(row["plan_json"]))


def read_plan_version_records(
    store: object, plan_id: str
) -> tuple[Mapping[str, object], ...]:
    """Read ordered immutable plan-version records.

    Returns:
        Ordered plan payload mappings.
    """
    _require_store(store)
    rows = _execute(
        (
            "SELECT plan_json FROM portfolio_rebalance_plans WHERE plan_id=? "
            "ORDER BY created_at ASC, plan_version ASC LIMIT 1000",
        ),
        ((plan_id,),),
        max_rows=1_000,
    ).rows
    return tuple({"plan": json.loads(str(row["plan_json"]))} for row in rows)


__all__ = [
    "read_active_allocation_record",
    "read_allocation_history_records",
    "read_allocation_record",
    "read_construction_record",
    "read_definition_record",
    "read_idempotency_record",
    "read_plan_record",
    "read_plan_version_records",
]
