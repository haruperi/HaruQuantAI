"""Accepted/not-found/ambiguous unknown-outcome recovery evidence."""

import pytest
from app.services.simulator import (
    create_simulation_recovery_state,
    recover_simulation_unknown_outcome,
)


@pytest.mark.parametrize("authority_outcome", ["accepted", "not_found"])
def test_unknown_outcome_converges_to_authority_without_retry(
    authority_outcome: str,
) -> None:
    """FR-SIM-230: authoritative accepted/not-found outcomes never repeat mutation."""
    state = create_simulation_recovery_state(
        command_id="command-unknown",
        crash_point="after_response_receipt",
        outcome="unknown",
    )
    result = recover_simulation_unknown_outcome(
        state, authority_query=lambda _command_id: authority_outcome
    )
    assert result["outcome"] == authority_outcome
    assert result["mutation_attempts"] == 1
    assert result["authority_queries"] == 1


def test_still_ambiguous_authority_remains_blocked() -> None:
    """FR-SIM-230: unresolved authority cannot be guessed or retried."""
    state = create_simulation_recovery_state(
        command_id="command-ambiguous",
        crash_point="after_response_receipt",
        outcome="unknown",
    )
    with pytest.raises(ValueError, match="did not resolve"):
        recover_simulation_unknown_outcome(
            state, authority_query=lambda _command_id: "unknown"
        )
