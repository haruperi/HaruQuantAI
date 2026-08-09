"""JSON-safe state-transition audit records."""

from datetime import UTC, datetime

from app.utils.errors.exceptions import ValidationError

_OUTCOMES = {"ACCEPTED", "REJECTED_UNDECLARED_EDGE", "REJECTED_TERMINAL", "REGRESSED"}


def build_transition_record(
    *,
    entity_id: str,
    source_state: str,
    target_state: str,
    outcome: str,
    reason_code: str,
    actor_ref: str,
    occurred_at: datetime,
    sequence: int,
) -> dict[str, object]:
    """Build one transition record for append-only persistence.

    Args:
        entity_id: Owning entity identifier.
        source_state: Previous state.
        target_state: Proposed state.
        outcome: Transition outcome.
        reason_code: Symbolic reason.
        actor_ref: Actor reference.
        occurred_at: Aware UTC instant.
        sequence: Monotonic sequence.

    Returns:
        JSON-safe transition record.

    Raises:
        ValidationError: If evidence is invalid.
    """
    if (
        not all((entity_id, source_state, target_state, reason_code, actor_ref))
        or outcome not in _OUTCOMES
        or occurred_at.tzinfo is None
        or occurred_at.utcoffset() != UTC.utcoffset(occurred_at)
        or sequence < 0
    ):
        raise ValidationError("TRANSITION_RECORD_INVALID")
    return {
        "contract_version": "v1",
        "schema_id": "utils.transition_record.v1",
        "entity_id": entity_id,
        "source_state": source_state,
        "target_state": target_state,
        "outcome": outcome,
        "reason_code": reason_code,
        "actor_ref": actor_ref,
        "occurred_at": occurred_at.isoformat().replace("+00:00", "Z"),
        "sequence": sequence,
    }
