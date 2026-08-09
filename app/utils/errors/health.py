"""Versioned fail-closed dependency health mappings."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime

from app.utils.errors.exceptions import ValidationError

_STATES = {"DEGRADED", "FAILED", "UNKNOWN"}
_CATEGORIES = {
    "TRANSIENT",
    "PERMANENT",
    "INTEGRITY",
    "POLICY",
    "DATA_STALE",
    "UNKNOWN_STATE",
}


def build_health_state(
    *,
    dependency: str,
    category: str,
    state: str,
    retryable: bool,
    operator_action: str,
    observed_at: datetime | None,
) -> dict[str, object]:
    """Build HealthState v1 with absent evidence mapped to UNKNOWN.

    Args:
        dependency: Dependency name.
        category: Closed error category.
        state: Degraded, failed, or unknown state.
        retryable: Whether retry is allowed.
        operator_action: Required safe action text.
        observed_at: Optional aware UTC observation.

    Returns:
        HealthState v1 mapping.

    Raises:
        ValidationError: If evidence is invalid.
    """
    if (
        not dependency
        or category not in _CATEGORIES
        or state not in _STATES
        or not operator_action
    ):
        raise ValidationError("HEALTH_STATE_INVALID")
    if observed_at is None:
        state, category, retryable = "UNKNOWN", "UNKNOWN_STATE", False
        instant = None
    else:
        if observed_at.tzinfo is None or observed_at.utcoffset() != UTC.utcoffset(
            observed_at
        ):
            raise ValidationError("HEALTH_STATE_INVALID")
        instant = observed_at.isoformat().replace("+00:00", "Z")
    return {
        "contract_version": "v1",
        "schema_id": "utils.health_state.v1",
        "dependency": dependency,
        "category": category,
        "state": state,
        "retryable": retryable,
        "operator_action": operator_action,
        "observed_at": instant,
    }


def parse_health_state(value: Mapping[str, object]) -> dict[str, object]:
    """Strictly parse a HealthState v1 mapping.

    Args:
        value: Candidate mapping.

    Returns:
        Validated detached mapping.

    Raises:
        ValidationError: If validation fails.
    """
    expected = {
        "contract_version",
        "schema_id",
        "dependency",
        "category",
        "state",
        "retryable",
        "operator_action",
        "observed_at",
    }
    if (
        set(value) != expected
        or value.get("contract_version") != "v1"
        or value.get("schema_id") != "utils.health_state.v1"
    ):
        raise ValidationError("HEALTH_STATE_INVALID")
    observed = value.get("observed_at")
    instant = None if observed is None else datetime.fromisoformat(str(observed))
    return build_health_state(
        dependency=str(value["dependency"]),
        category=str(value["category"]),
        state=str(value["state"]),
        retryable=bool(value["retryable"]),
        operator_action=str(value["operator_action"]),
        observed_at=instant,
    )
