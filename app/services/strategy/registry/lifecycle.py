"""Immutable Strategy lifecycle governance rules."""

# ruff: noqa: DOC201, DOC501

from app.utils import get_logger

logger = get_logger(__name__)

_TRANSITIONS = {
    "DRAFT": {"TESTING", "RETIRED"},
    "TESTING": {"APPROVED", "DRAFT", "RETIRED"},
    "APPROVED": {"SUSPENDED", "RETIRED"},
    "SUSPENDED": {"APPROVED", "RETIRED"},
    "RETIRED": set(),
}


def govern_strategy_lifecycle(
    *,
    strategy_id: str,
    strategy_version: str,
    current_status: str,
    target_status: str,
    reason: str,
) -> dict[str, str]:
    """Build append-only lifecycle mutation evidence after a valid transition."""
    if target_status not in _TRANSITIONS.get(current_status, set()):
        logger.warning("Rejected Strategy lifecycle transition")
        raise ValueError("strategy lifecycle transition is not allowed")
    if not strategy_id.strip() or not strategy_version.strip() or not reason.strip():
        raise ValueError("lifecycle mutation fields must be non-empty")
    return {
        "contract_version": "v1",
        "schema_id": "strategy.lifecycle_mutation.v1",
        "strategy_id": strategy_id,
        "strategy_version": strategy_version,
        "from_status": current_status,
        "to_status": target_status,
        "reason": reason,
    }


__all__ = ["govern_strategy_lifecycle"]
