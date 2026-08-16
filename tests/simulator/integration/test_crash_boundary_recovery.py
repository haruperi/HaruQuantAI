"""All deterministic crash-boundary convergence evidence."""

from app.services.simulator import (
    create_simulation_recovery_state,
    get_simulation_crash_points,
    recover_simulation_unknown_outcome,
)


def test_every_crash_boundary_converges_without_duplicate_mutation() -> None:
    """FR-SIM-230: every crash point queries authority without resubmission."""
    queries: list[str] = []
    for point in get_simulation_crash_points():
        state = create_simulation_recovery_state(
            command_id=f"command-{point}", crash_point=point, outcome="unknown"
        )
        result = recover_simulation_unknown_outcome(
            state,
            authority_query=lambda command_id: queries.append(command_id) or "accepted",
        )
        assert result["mutation_attempts"] == 1
        assert result["recovery_state"] == "VERIFIED"
        assert result["outcome"] == "accepted"
    assert len(queries) == len(get_simulation_crash_points())


def test_inflight_kill_switch_blocks_new_mutation_and_converges() -> None:
    """FR-SIM-230: an in-flight kill switch preserves convergence but blocks exposure."""
    state = create_simulation_recovery_state(
        command_id="command-kill",
        crash_point="after_command_submission",
        outcome="unknown",
    )
    result = recover_simulation_unknown_outcome(
        state,
        authority_query=lambda _command_id: "accepted",
        kill_switch_active=True,
    )
    assert result["outcome"] == "accepted"
    assert result["exposure_blocked"] is True
    assert result["new_mutation_allowed"] is False
