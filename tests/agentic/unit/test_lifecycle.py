"""Unit tests for `FEAT-AGT-18` artefact promotion and lifecycle.

Three requirements, three sections. The packet is complete or unbuildable
(`FR-AGENTIC-052`); five named conditions terminate promotion as
`research_only` (`FR-AGENTIC-053`); and transitions are append-only,
version-specific, non-skippable, demotable, and never inherited
(`FR-AGENTIC-054`).
"""

from __future__ import annotations

import pytest
from app.agentic.lifecycle.models import (
    PROMOTION_PERMISSION,
    REQUIRED_PROVENANCE,
    TERMINAL_STATES,
    approval_refusal,
    build_lifecycle_record,
    build_promotion_assessment,
    build_promotion_evidence_packet,
    derive_packet_hash,
    is_terminal_state,
    latest_state,
    missing_provenance,
    permitted_next_states,
    validate_transition,
)
from app.agentic.lifecycle.repository import build_in_memory_lifecycle_store
from app.agentic.lifecycle.service import (
    assess_promotion,
    can_transition,
    get_artifact_history,
    get_artifact_state,
    is_settled,
    transition_artifact,
)
from app.agentic.migrations.lifecycle import (
    build_lifecycle_migration_request,
    get_lifecycle_migration_statements,
)
from app.kernel.identity import generate_id
from pydantic import ValidationError

from tests.agentic.fixtures import (
    NOW,
    PROMOTION_APPROVER_ID,
    PROMOTION_ENVIRONMENT,
    PROMOTION_TASK_ID,
    ApprovingUser,
    build_promotion_artifact,
    build_promotion_critique,
    build_promotion_experiment_verdict,
    build_promotion_sweep_verdict,
)

CEILING = 100


def _packet_fields(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "packet_id": "packet-a",
        "task_id": PROMOTION_TASK_ID,
        "artifact": build_promotion_artifact(),
        "experiment_verdict": build_promotion_experiment_verdict(),
        "sweep_verdict": build_promotion_sweep_verdict(),
        "critique": build_promotion_critique(),
        "simulation_manifest_ref": "simulator.artifact_manifest:run-a",
        "lifetime_trial_ceiling": CEILING,
        "approver_id": PROMOTION_APPROVER_ID,
        "approval_environment": PROMOTION_ENVIRONMENT,
        "assembled_at": NOW.isoformat(),
    }
    data.update(overrides)
    return data


def _packet(**overrides: object):
    return build_promotion_evidence_packet(_packet_fields(**overrides))


def _assess(**overrides: object):
    data: dict[str, object] = {
        "artifact": build_promotion_artifact(),
        "experiment_verdict": build_promotion_experiment_verdict(),
        "sweep_verdict": build_promotion_sweep_verdict(),
        "critique": build_promotion_critique(),
        "task_id": PROMOTION_TASK_ID,
        "lifetime_trial_ceiling": CEILING,
        "environment": PROMOTION_ENVIRONMENT,
        "approver": ApprovingUser(),
        "at_time": NOW,
    }
    data.update(overrides)
    return assess_promotion(**data)  # type: ignore[arg-type]


def _record_fields(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "record_id": "record-a",
        "artifact_hash": "sha256:artifact-a",
        "artifact_id": "artifact-a",
        "sequence": 1,
        "previous_state": None,
        "state": "staged",
        "actor_id": "process-lifecycle",
        "rationale": "The coder staged the artefact.",
        "recorded_at": NOW.isoformat(),
    }
    data.update(overrides)
    return data


def _advance(store, artifact_hash: str, states: tuple[str, ...]) -> None:
    """Walk an artefact through an ordered sequence of states."""
    for state in states:
        transition_artifact(
            store,
            artifact_hash,
            "artifact-a",
            state,  # type: ignore[arg-type]
            "process-lifecycle",
            f"advancing to {state}",
            at_time=NOW,
        )


# --------------------------------------------------------------------------
# The feature invokes no model
# --------------------------------------------------------------------------


def test_the_package_declares_no_role_and_calls_no_model() -> None:
    from pathlib import Path

    package = Path("app/agentic/lifecycle")
    assert not (package / "prompt.md").exists()
    assert not (package / "agent.py").exists()
    sources = "".join(path.read_text(encoding="utf-8") for path in package.glob("*.py"))
    for forbidden in ("execute_node", "AdkRuntime", "ModelProfile"):
        assert forbidden not in sources


def test_the_package_never_calls_a_receiver() -> None:
    from pathlib import Path

    sources = "".join(
        path.read_text(encoding="utf-8")
        for path in Path("app/agentic/lifecycle").glob("*.py")
    )
    for forbidden in (
        "register_strategy_version",
        "run_backtest",
        "app.services.strategy",
        "app.services.simulator",
    ):
        assert forbidden not in sources


def test_only_migrations_reaches_a_service_domain() -> None:
    from pathlib import Path

    importers = {
        str(path.as_posix())
        for path in (
            *Path("app/agentic/lifecycle").glob("*.py"),
            Path("app/agentic/migrations/lifecycle.py"),
        )
        if "app.services" in path.read_text(encoding="utf-8")
    }
    # Data owns migration execution, so declaring a schema is the one legitimate
    # service import. Anything else would be this package reaching a receiver.
    assert importers == {"app/agentic/migrations/lifecycle.py"}


# --------------------------------------------------------------------------
# FR-AGENTIC-052 - the complete ordered evidence packet
# --------------------------------------------------------------------------


def test_a_complete_packet_assembles() -> None:
    packet = _packet()
    assert packet.packet_hash
    assert packet.artifact.promotion_status == "ready"
    assert len(packet.critique.challenges) == 7


@pytest.mark.parametrize(
    "dropped",
    [
        "artifact",
        "experiment_verdict",
        "sweep_verdict",
        "critique",
        "simulation_manifest_ref",
        "approver_id",
    ],
)
def test_a_packet_missing_any_evidence_is_unrepresentable(dropped) -> None:
    fields = _packet_fields()
    del fields[dropped]
    with pytest.raises(ValidationError, match="Field required"):
        build_promotion_evidence_packet(fields)


def test_the_packet_digest_covers_the_whole_assembly() -> None:
    packet = _packet()
    altered = _packet_fields(simulation_manifest_ref="simulator.manifest:other")
    assert derive_packet_hash(altered) != packet.packet_hash


def test_evidence_appended_after_assembly_changes_the_digest() -> None:
    packet = _packet()
    later = _packet_fields(critique=build_promotion_critique(blocking_concerns=("x",)))
    assert derive_packet_hash(later) != packet.packet_hash


def test_a_non_positive_search_ceiling_is_rejected() -> None:
    with pytest.raises(ValidationError, match="must be positive"):
        build_promotion_evidence_packet(_packet_fields(lifetime_trial_ceiling=0))


def test_an_authenticated_human_may_approve() -> None:
    assert approval_refusal(ApprovingUser(), PROMOTION_ENVIRONMENT) is None


def test_a_service_account_may_not_approve() -> None:
    failure = approval_refusal(
        ApprovingUser(principal_type="SERVICE_ACCOUNT"),
        PROMOTION_ENVIRONMENT,
    )
    assert failure is not None
    assert "human principal" in failure


def test_a_principal_without_the_permission_may_not_approve() -> None:
    failure = approval_refusal(
        ApprovingUser(permissions=("agentic:read",)),
        PROMOTION_ENVIRONMENT,
    )
    assert failure is not None
    assert PROMOTION_PERMISSION in failure


def test_an_approval_for_another_environment_is_refused() -> None:
    failure = approval_refusal(
        ApprovingUser(tenant_or_environment="production"),
        PROMOTION_ENVIRONMENT,
    )
    assert failure is not None
    assert "production" in failure


def test_an_absent_approval_is_refused() -> None:
    failure = approval_refusal(None, PROMOTION_ENVIRONMENT)
    assert failure is not None
    assert "authenticated human" in failure


def test_a_complete_packet_passes_every_gate() -> None:
    assessment = _assess()
    assert assessment.promotable is True
    assert assessment.failed_gates == ()
    assert assessment.termination_reason is None


# --------------------------------------------------------------------------
# FR-AGENTIC-053 - five conditions terminate promotion as research_only
# --------------------------------------------------------------------------


def test_in_sample_only_evidence_terminates_promotion() -> None:
    assessment = _assess(
        experiment_verdict=build_promotion_experiment_verdict(
            evidence_classes={"run-a": "discovery"},
        ),
    )
    assert assessment.promotable is False
    assert assessment.termination_reason == "leakage_detected"


@pytest.mark.parametrize("evidence_class", ["validation", "holdout"])
def test_out_of_sample_evidence_clears_the_leakage_gate(evidence_class) -> None:
    assessment = _assess(
        experiment_verdict=build_promotion_experiment_verdict(
            evidence_classes={"run-a": evidence_class},
            holdout_consumed=evidence_class == "holdout",
        ),
    )
    assert assessment.promotable is True


def test_holdout_spent_by_both_the_experiment_and_the_sweep_terminates() -> None:
    assessment = _assess(
        experiment_verdict=build_promotion_experiment_verdict(
            evidence_classes={"run-a": "holdout"},
            holdout_consumed=True,
        ),
        sweep_verdict=build_promotion_sweep_verdict(holdout_consumed=True),
    )
    assert assessment.promotable is False
    assert assessment.termination_reason == "holdout_reused"


def test_holdout_spent_once_does_not_terminate() -> None:
    assessment = _assess(
        experiment_verdict=build_promotion_experiment_verdict(
            evidence_classes={"run-a": "holdout"},
            holdout_consumed=True,
        ),
    )
    assert assessment.promotable is True


def test_search_beyond_the_declared_ceiling_terminates() -> None:
    assessment = _assess(
        sweep_verdict=build_promotion_sweep_verdict(lifetime_trials=CEILING + 1),
    )
    assert assessment.promotable is False
    assert assessment.termination_reason == "search_budget_exhausted"


def test_search_exactly_at_the_ceiling_is_permitted() -> None:
    assessment = _assess(
        sweep_verdict=build_promotion_sweep_verdict(lifetime_trials=CEILING),
    )
    assert assessment.promotable is True


@pytest.mark.parametrize("field", list(REQUIRED_PROVENANCE[1:]))
def test_an_artefact_missing_provenance_terminates(field) -> None:
    artifact = build_promotion_artifact()
    stripped = artifact.model_copy(update={field: "   "})
    assert missing_provenance(stripped) == (field,)


def test_an_artefact_that_is_not_promotable_as_staged_terminates() -> None:
    assessment = _assess(
        artifact=build_promotion_artifact(
            required_indicators=("kalman_slope",),
            unregistered_indicators=("kalman_slope",),
            promotion_status="blocked_on_indicator_merge",
        ),
    )
    assert assessment.promotable is False
    assert assessment.termination_reason == "provenance_incomplete"


def test_an_unapproved_promotion_terminates() -> None:
    assessment = _assess(approver=None)
    assert assessment.promotable is False
    assert assessment.termination_reason == "approval_absent"


def test_every_failed_gate_is_reported_not_only_the_first() -> None:
    assessment = _assess(
        experiment_verdict=build_promotion_experiment_verdict(
            evidence_classes={"run-a": "discovery"},
        ),
        sweep_verdict=build_promotion_sweep_verdict(lifetime_trials=CEILING + 1),
        approver=None,
    )
    assert assessment.termination_reason == "leakage_detected"
    assert len(assessment.failed_gates) == 3
    assert any(entry.startswith("approval:") for entry in assessment.failed_gates)


def test_the_first_reported_reason_follows_the_requirement_order() -> None:
    assessment = _assess(
        sweep_verdict=build_promotion_sweep_verdict(
            holdout_consumed=True,
            lifetime_trials=CEILING + 1,
        ),
        experiment_verdict=build_promotion_experiment_verdict(
            evidence_classes={"run-a": "holdout"},
            holdout_consumed=True,
        ),
    )
    assert assessment.termination_reason == "holdout_reused"


def test_blocking_concerns_survive_a_passing_assessment() -> None:
    assessment = _assess(
        critique=build_promotion_critique(
            blocking_concerns=("The counterfactual baseline is not ruled out.",),
        ),
    )
    assert assessment.promotable is True
    assert assessment.unresolved_concerns == (
        "The counterfactual baseline is not ruled out.",
    )


def test_a_promotable_assessment_cannot_carry_failed_gates() -> None:
    with pytest.raises(ValidationError, match="cannot be promotable"):
        build_promotion_assessment(
            {
                "assessment_id": "assessment-a",
                "task_id": PROMOTION_TASK_ID,
                "artifact_hash": "sha256:artifact-a",
                "promotable": True,
                "failed_gates": ("approval: absent",),
                "unresolved_concerns": (),
                "assessed_at": NOW.isoformat(),
            },
        )


def test_a_terminated_assessment_must_state_its_reason() -> None:
    with pytest.raises(ValidationError, match="must state its termination reason"):
        build_promotion_assessment(
            {
                "assessment_id": "assessment-a",
                "task_id": PROMOTION_TASK_ID,
                "artifact_hash": "sha256:artifact-a",
                "promotable": False,
                "failed_gates": ("approval: absent",),
                "unresolved_concerns": (),
                "assessed_at": NOW.isoformat(),
            },
        )


# --------------------------------------------------------------------------
# FR-AGENTIC-054 - append-only, version-specific, non-skippable transitions
# --------------------------------------------------------------------------


def test_an_unrecorded_artefact_enters_at_staged() -> None:
    assert validate_transition(None, "staged") is None


@pytest.mark.parametrize(
    "state",
    ["evaluated", "approved", "registered", "research_only", "demoted"],
)
def test_an_unrecorded_artefact_cannot_enter_anywhere_else(state) -> None:
    failure = validate_transition(None, state)
    assert failure is not None
    assert "must enter at 'staged'" in failure


def test_the_ordered_path_is_permitted() -> None:
    store = build_in_memory_lifecycle_store()
    _advance(store, "sha256:a", ("staged", "evaluated", "approved", "registered"))
    assert get_artifact_state(store, "sha256:a") == "registered"
    assert len(get_artifact_history(store, "sha256:a")) == 4


@pytest.mark.parametrize(
    ("current", "requested"),
    [
        ("staged", "approved"),
        ("staged", "registered"),
        ("evaluated", "registered"),
    ],
)
def test_a_skipped_step_is_refused(current, requested) -> None:
    failure = validate_transition(current, requested)
    assert failure is not None
    assert "may only follow" in failure


def test_a_repeated_state_is_refused() -> None:
    failure = validate_transition("evaluated", "evaluated")
    assert failure is not None
    assert "already" in failure


def test_an_unknown_state_is_refused() -> None:
    failure = validate_transition("staged", "blessed")
    assert failure is not None
    assert "not a recognized artefact state" in failure


def test_research_only_is_terminal() -> None:
    assert is_terminal_state("research_only")
    assert permitted_next_states("research_only") == ()


def test_nothing_reopens_a_research_only_artefact() -> None:
    store = build_in_memory_lifecycle_store()
    _advance(store, "sha256:a", ("staged",))
    transition_artifact(
        store,
        "sha256:a",
        "artifact-a",
        "research_only",
        "process-lifecycle",
        "the packet failed a gate",
        termination_reason="approval_absent",
        at_time=NOW,
    )
    assert is_settled(store, "sha256:a")
    with pytest.raises(ValueError, match="terminal"):
        _advance(store, "sha256:a", ("evaluated",))


@pytest.mark.parametrize("origin", ["staged", "evaluated", "approved"])
def test_promotion_may_terminate_from_any_non_terminal_state(origin) -> None:
    assert "research_only" in permitted_next_states(origin)


def test_a_registered_artefact_is_demotable_without_approval() -> None:
    store = build_in_memory_lifecycle_store()
    _advance(store, "sha256:a", ("staged", "evaluated", "approved", "registered"))
    record = transition_artifact(
        store,
        "sha256:a",
        "artifact-a",
        "demoted",
        "process-monitoring",
        "live behaviour diverged from the backtest",
        at_time=NOW,
    )
    assert record.state == "demoted"
    assert record.previous_state == "registered"
    assert is_settled(store, "sha256:a")


def test_only_a_registered_artefact_may_be_demoted() -> None:
    failure = validate_transition("approved", "demoted")
    assert failure is not None
    assert "may only follow registered" in failure


def test_history_is_keyed_on_the_artefact_digest_not_its_identity() -> None:
    store = build_in_memory_lifecycle_store()
    _advance(store, "sha256:a", ("staged", "evaluated", "approved"))
    # The same artefact_id, one changed byte, therefore a different digest.
    assert get_artifact_state(store, "sha256:changed") is None
    assert can_transition(store, "sha256:changed", "approved") is not None
    assert can_transition(store, "sha256:changed", "staged") is None


def test_a_materially_changed_artefact_inherits_no_state() -> None:
    original = build_promotion_artifact()
    changed = build_promotion_artifact(tests=("test_something_else",))
    assert original.artifact_hash != changed.artifact_hash
    store = build_in_memory_lifecycle_store()
    _advance(
        store,
        original.artifact_hash,
        ("staged", "evaluated", "approved", "registered"),
    )
    assert get_artifact_state(store, changed.artifact_hash) is None
    assert get_artifact_history(store, changed.artifact_hash) == ()


def test_the_ledger_refuses_a_position_already_written() -> None:
    store = build_in_memory_lifecycle_store()
    _advance(store, "sha256:a", ("staged",))
    duplicate = build_lifecycle_record(
        _record_fields(record_id="record-b", artifact_hash="sha256:a"),
    )
    with pytest.raises(ValueError, match="not appendable"):
        store.append_record(duplicate)


def test_the_ledger_refuses_a_position_out_of_order() -> None:
    store = build_in_memory_lifecycle_store()
    out_of_order = build_lifecycle_record(
        _record_fields(sequence=2, previous_state="staged", state="evaluated"),
    )
    with pytest.raises(ValueError, match="not appendable"):
        store.append_record(out_of_order)


def test_the_current_state_comes_from_the_ledger_not_the_caller() -> None:
    store = build_in_memory_lifecycle_store()
    _advance(store, "sha256:a", ("staged",))
    with pytest.raises(ValueError, match="may only follow evaluated"):
        _advance(store, "sha256:a", ("approved",))


def test_the_first_record_has_no_previous_state() -> None:
    # The transition itself is legal; it is the position that is not.
    with pytest.raises(ValidationError, match="no previous state"):
        build_lifecycle_record(
            _record_fields(sequence=1, previous_state="staged", state="evaluated"),
        )


def test_a_later_record_must_name_its_previous_state() -> None:
    with pytest.raises(ValidationError, match="only the first"):
        build_lifecycle_record(
            _record_fields(sequence=2, previous_state=None, state="staged"),
        )


def test_a_sequence_starts_at_one() -> None:
    with pytest.raises(ValidationError, match="starts at one"):
        build_lifecycle_record(_record_fields(sequence=0))


def test_a_research_only_record_must_state_why() -> None:
    with pytest.raises(ValidationError, match="must state why"):
        build_lifecycle_record(
            _record_fields(previous_state="staged", sequence=2, state="research_only"),
        )


def test_a_termination_reason_belongs_only_to_research_only() -> None:
    with pytest.raises(ValidationError, match="belongs to research_only"):
        build_lifecycle_record(
            _record_fields(
                sequence=2,
                previous_state="staged",
                state="evaluated",
                termination_reason="approval_absent",
            ),
        )


def test_a_packet_describing_another_artefact_is_refused() -> None:
    store = build_in_memory_lifecycle_store()
    packet = _packet()
    _advance(store, "sha256:other", ("staged", "evaluated"))
    with pytest.raises(ValueError, match="the packet describes artefact"):
        transition_artifact(
            store,
            "sha256:other",
            "artifact-a",
            "approved",
            PROMOTION_APPROVER_ID,
            "approved on the packet",
            packet=packet,
            at_time=NOW,
        )


def test_a_transition_carrying_a_packet_persists_it() -> None:
    store = build_in_memory_lifecycle_store()
    packet = _packet()
    digest = packet.artifact.artifact_hash
    _advance(store, digest, ("staged", "evaluated"))
    record = transition_artifact(
        store,
        digest,
        packet.artifact.artifact_id,
        "approved",
        PROMOTION_APPROVER_ID,
        "the reviewer approved the complete packet",
        packet=packet,
        at_time=NOW,
    )
    assert record.packet_hash == packet.packet_hash
    assert store.load_packet(packet.packet_hash) is not None


def test_two_packets_claiming_one_digest_are_refused() -> None:
    store = build_in_memory_lifecycle_store()
    packet = _packet()
    store.save_packet(packet)
    with pytest.raises(ValueError, match="already recorded"):
        store.save_packet(packet.model_copy(update={"packet_id": "packet-b"}))


def test_terminal_states_are_exactly_two() -> None:
    assert {"research_only", "demoted"} == TERMINAL_STATES


def test_latest_state_reads_the_end_of_the_history() -> None:
    store = build_in_memory_lifecycle_store()
    _advance(store, "sha256:a", ("staged", "evaluated"))
    assert latest_state(get_artifact_history(store, "sha256:a")) == "evaluated"
    assert latest_state(()) is None


def test_an_unrecorded_artefact_is_not_settled() -> None:
    store = build_in_memory_lifecycle_store()
    assert is_settled(store, "sha256:missing") is False
    assert get_artifact_state(store, "sha256:missing") is None


# --------------------------------------------------------------------------
# The durable ledger carries the same rule the in-memory double does
# --------------------------------------------------------------------------


def test_the_transition_table_is_keyed_on_the_digest_and_the_position() -> None:
    statements = get_lifecycle_migration_statements()
    transitions = next(
        statement
        for statement in statements
        if "agentic_lifecycle_transitions" in statement and "CREATE TABLE" in statement
    )
    # Append-only survives a restart only because the position can be claimed
    # once. Without this key the property is a convention, not a guarantee.
    assert "PRIMARY KEY (artifact_hash, sequence)" in transitions
    assert "record_id TEXT NOT NULL UNIQUE" in transitions


def test_the_packet_table_is_keyed_on_the_assembly_digest() -> None:
    statements = get_lifecycle_migration_statements()
    packets = next(
        statement
        for statement in statements
        if "agentic_promotion_packets" in statement and "CREATE TABLE" in statement
    )
    assert "packet_hash TEXT PRIMARY KEY" in packets


def test_the_migration_request_is_declared_not_executed() -> None:
    request = build_lifecycle_migration_request(generate_id("req"))
    assert request is not None
    from pathlib import Path

    source = Path("app/agentic/migrations/lifecycle.py").read_text(encoding="utf-8")
    for forbidden in ("connect(", "execute(", "cursor"):
        assert forbidden not in source
