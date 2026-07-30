"""Executable FEAT-AGT-18 artefact promotion and lifecycle usage example.

Demonstrates every registered public operation through the documented API. The
ledger is the deterministic in-memory double, so nothing is written to disk, no
network call occurs, and Agentic holds no credential.

The point of the demonstration is that promotion is a decision procedure, not a
judgement. No model is invoked anywhere in this feature: the packet is complete
or unbuildable, the five gates read evidence the packet already carries, and
the transition machine decides what may follow what.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.agentic.lifecycle import (
    LifecycleRecord,
    PromotionAssessment,
    PromotionEvidencePacket,
    assess_promotion,
    build_in_memory_lifecycle_store,
    build_lifecycle_migration_request,
    build_lifecycle_record,
    build_promotion_assessment,
    build_promotion_evidence_packet,
    can_transition,
    get_artifact_history,
    get_artifact_state,
    get_lifecycle_migration_statements,
    is_settled,
    is_terminal_state,
    permitted_next_states,
    transition_artifact,
    validate_transition,
)
from app.utils import generate_id

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from agentic.fixtures import (
    PROMOTION_APPROVER_ID,
    PROMOTION_ENVIRONMENT,
    PROMOTION_TASK_ID,
    ApprovingUser,
    build_promotion_artifact,
    build_promotion_critique,
    build_promotion_experiment_verdict,
    build_promotion_sweep_verdict,
)

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
CEILING = 100

BANNER = "=" * 88


def heading(requirement: str, statement: str) -> None:
    """Print one requirement heading.

    Args:
        requirement: Functional requirement identifier.
        statement: What the requirement obliges.
    """
    print(f"\n{BANNER}\n{requirement}: {statement}\n{BANNER}")


def evidence(**overrides: object) -> dict[str, object]:
    """Assemble the four contracts a promotion packet carries.

    Args:
        **overrides: Optional evidence overrides.

    Returns:
        Complete candidate evidence.
    """
    data: dict[str, object] = {
        "artifact": build_promotion_artifact(),
        "experiment_verdict": build_promotion_experiment_verdict(),
        "sweep_verdict": build_promotion_sweep_verdict(),
        "critique": build_promotion_critique(),
    }
    data.update(overrides)
    return data


def packet(items: dict[str, object]) -> PromotionEvidencePacket:
    """Build one complete promotion evidence packet.

    Args:
        items: Candidate evidence.

    Returns:
        A validated immutable packet carrying its assembly digest.
    """
    return build_promotion_evidence_packet(
        {
            "packet_id": "packet-usage-a",
            "task_id": PROMOTION_TASK_ID,
            **items,
            "simulation_manifest_ref": "simulator.artifact_manifest:run-a",
            "lifetime_trial_ceiling": CEILING,
            "approver_id": PROMOTION_APPROVER_ID,
            "approval_environment": PROMOTION_ENVIRONMENT,
            "assembled_at": NOW.isoformat(),
        },
    )


def assess(items: dict[str, object], **overrides: object) -> PromotionAssessment:
    """Run the deterministic gates over assembled evidence.

    Args:
        items: Candidate evidence.
        **overrides: Optional assessment overrides.

    Returns:
        What the gates concluded.
    """
    data: dict[str, object] = {
        **items,
        "task_id": PROMOTION_TASK_ID,
        "lifetime_trial_ceiling": CEILING,
        "environment": PROMOTION_ENVIRONMENT,
        "approver": ApprovingUser(),
        "at_time": NOW,
    }
    data.update(overrides)
    return assess_promotion(**data)


def fr_agentic_052() -> None:
    """Demonstrate the complete ordered packet and human approval."""
    heading(
        "FR-AGENTIC-052",
        "Promotion requires the complete ordered evidence packet, deterministic "
        "gates, and authenticated human approval.",
    )

    items = evidence()
    assembled = packet(items)
    print(f"  packet digest:       {assembled.packet_hash}")
    print(f"  artefact:            {assembled.artifact.artifact_id}")
    print(f"  experiment outcome:  {assembled.experiment_verdict.outcome}")
    print(f"  search identity:     {assembled.sweep_verdict.search_id}")
    print(f"  challenges answered: {len(assembled.critique.challenges)}")
    print(f"  simulation evidence: {assembled.simulation_manifest_ref}")
    print(f"  approved by:         {assembled.approver_id}")

    print("\n  A packet missing any one piece of evidence cannot be built:")
    for dropped in (
        "artifact",
        "experiment_verdict",
        "sweep_verdict",
        "critique",
        "simulation_manifest_ref",
        "approver_id",
    ):
        fields = {
            "packet_id": "packet-usage-a",
            "task_id": PROMOTION_TASK_ID,
            **items,
            "simulation_manifest_ref": "simulator.artifact_manifest:run-a",
            "lifetime_trial_ceiling": CEILING,
            "approver_id": PROMOTION_APPROVER_ID,
            "approval_environment": PROMOTION_ENVIRONMENT,
            "assembled_at": NOW.isoformat(),
        }
        del fields[dropped]
        try:
            build_promotion_evidence_packet(fields)
            outcome = "ERROR: an incomplete packet was accepted"
        except Exception:  # noqa: BLE001 - usage demonstrates rejection.
            outcome = "unbuildable"
        print(f"    without {dropped:<24} -> {outcome}")

    print("\n  Only an authenticated human holding the permission may approve:")
    approvers = (
        ("a reviewer with the permission", ApprovingUser()),
        ("a service account", ApprovingUser(principal_type="SERVICE_ACCOUNT")),
        ("a user without it", ApprovingUser(permissions=("agentic:read",))),
        (
            "an approval for production",
            ApprovingUser(tenant_or_environment="production"),
        ),
        ("nobody", None),
    )
    for label, approver in approvers:
        result = assess(items, approver=approver)
        verdict = "promotable" if result.promotable else result.termination_reason
        print(f"    {label:<32} -> {verdict}")


def fr_agentic_053() -> None:
    """Demonstrate the five conditions that terminate promotion."""
    heading(
        "FR-AGENTIC-053",
        "Leakage, holdout reuse, search-budget exhaustion, missing provenance, "
        "or absent approval terminates promotion as research_only.",
    )

    cases = (
        (
            "in-sample evidence only",
            evidence(
                experiment_verdict=build_promotion_experiment_verdict(
                    evidence_classes={"run-a": "discovery"},
                ),
            ),
            {},
        ),
        (
            "holdout spent twice",
            evidence(
                experiment_verdict=build_promotion_experiment_verdict(
                    evidence_classes={"run-a": "holdout"},
                    holdout_consumed=True,
                ),
                sweep_verdict=build_promotion_sweep_verdict(holdout_consumed=True),
            ),
            {},
        ),
        (
            "search beyond its ceiling",
            evidence(
                sweep_verdict=build_promotion_sweep_verdict(
                    lifetime_trials=CEILING + 1,
                ),
            ),
            {},
        ),
        (
            "artefact not promotable as staged",
            evidence(
                artifact=build_promotion_artifact(
                    required_indicators=("kalman_slope",),
                    unregistered_indicators=("kalman_slope",),
                    promotion_status="blocked_on_indicator_merge",
                ),
            ),
            {},
        ),
        ("no approval", evidence(), {"approver": None}),
        ("everything in order", evidence(), {}),
    )
    for label, items, overrides in cases:
        result = assess(items, **overrides)
        verdict = "promotable" if result.promotable else result.termination_reason
        print(f"    {label:<34} -> {verdict}")

    print("\n  Every failed gate is reported, not only the first:")
    multiple = assess(
        evidence(
            experiment_verdict=build_promotion_experiment_verdict(
                evidence_classes={"run-a": "discovery"},
            ),
            sweep_verdict=build_promotion_sweep_verdict(lifetime_trials=CEILING + 1),
        ),
        approver=None,
    )
    print(f"    termination reason: {multiple.termination_reason}")
    for gate in multiple.failed_gates:
        print(f"      - {gate}")

    print("\n  A blocking concern survives a passing assessment:")
    concerned = assess(
        evidence(
            critique=build_promotion_critique(
                blocking_concerns=("The counterfactual baseline is not ruled out.",),
            ),
        ),
    )
    print(f"    promotable:          {concerned.promotable}")
    print(f"    unresolved concerns: {concerned.unresolved_concerns}")

    print("\n  A promotable assessment carrying a failed gate cannot be built:")
    try:
        build_promotion_assessment(
            {
                "assessment_id": "assessment-usage-a",
                "task_id": PROMOTION_TASK_ID,
                "artifact_hash": "sha256:artifact-a",
                "promotable": True,
                "failed_gates": ("approval: absent",),
                "unresolved_concerns": (),
                "assessed_at": NOW.isoformat(),
            },
        )
        outcome = "ERROR: a contradictory assessment was accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "unbuildable"
    print(f"    {outcome}")


def fr_agentic_054() -> None:
    """Demonstrate append-only, non-skippable, non-inherited transitions."""
    heading(
        "FR-AGENTIC-054",
        "Artefact transitions are append-only, version-specific, non-skippable, "
        "automatically demotable, and never inherited across material changes.",
    )

    store = build_in_memory_lifecycle_store()
    items = evidence()
    artifact = items["artifact"]
    digest = artifact.artifact_hash
    assembled = packet(items)

    print("  The ordered path, one append at a time:")
    for state, actor, why, carried in (
        ("staged", "process-coder", "the coder staged a complete artefact", None),
        ("evaluated", "process-evaluation", "every challenge was addressed", None),
        (
            "approved",
            PROMOTION_APPROVER_ID,
            "an authenticated reviewer approved the packet",
            assembled,
        ),
        ("registered", "process-handoff", "the receiver registered the version", None),
    ):
        record: LifecycleRecord = transition_artifact(
            store,
            digest,
            artifact.artifact_id,
            state,
            actor,
            why,
            packet=carried,
            at_time=NOW,
        )
        print(
            f"    {record.sequence}. {record.previous_state or 'none':<12} -> "
            f"{record.state:<12} by {record.actor_id}"
        )

    print(f"\n  current state:   {get_artifact_state(store, digest)}")
    print(f"  history length:  {len(get_artifact_history(store, digest))}")
    print(f"  next permitted:  {permitted_next_states('registered')}")

    print("\n  A skipped step is refused:")
    for current, requested in (
        ("staged", "approved"),
        ("staged", "registered"),
        ("evaluated", "registered"),
    ):
        print(
            f"    {current:<12} -> {requested:<14} {validate_transition(current, requested)}"
        )

    print("\n  Demotion needs no approval and ends the artefact:")
    demoted = transition_artifact(
        store,
        digest,
        artifact.artifact_id,
        "demoted",
        "process-monitoring",
        "live behaviour diverged from the recorded backtest",
        at_time=NOW,
    )
    print(
        f"    {demoted.previous_state} -> {demoted.state}, terminal: {is_settled(store, digest)}"
    )

    print("\n  Terminal states admit nothing further:")
    for state in ("research_only", "demoted"):
        print(
            f"    {state:<14} terminal={is_terminal_state(state)}, next={permitted_next_states(state)}"
        )

    print("\n  A materially changed artefact inherits no state:")
    revised = build_promotion_artifact(dependencies={"numpy": "2.5.0"})
    print(f"    original digest: {digest[:24]}...")
    print(f"    revised digest:  {revised.artifact_hash[:24]}...")
    print(f"    revised state:   {get_artifact_state(store, revised.artifact_hash)}")
    print(
        f"    may register:    {can_transition(store, revised.artifact_hash, 'registered')}"
    )
    print(
        f"    may stage:       {can_transition(store, revised.artifact_hash, 'staged') is None}"
    )

    print("\n  A position already written cannot be written again:")
    duplicate = build_lifecycle_record(
        {
            "record_id": "record-duplicate",
            "artifact_hash": digest,
            "artifact_id": artifact.artifact_id,
            "sequence": 1,
            "previous_state": None,
            "state": "staged",
            "actor_id": "process-rewrite",
            "rationale": "rewriting the beginning of the history",
            "recorded_at": NOW.isoformat(),
        },
    )
    try:
        store.append_record(duplicate)
        outcome = "ERROR: history was rewritten"
    except ValueError as error:
        outcome = str(error)
    print(f"    {outcome}")

    print("\n  The durable ledger backs the same rule:")
    for statement in get_lifecycle_migration_statements():
        print(f"    {statement[:96]}")
    request = build_lifecycle_migration_request(generate_id("req"))
    print(f"    migration request built: {type(request).__name__}")

    print(
        "\n  Note: this feature records that an artefact reached a state; it does "
        "not\n  cause one. Strategy alone registers a strategy version, and the "
        "handoff\n  that reaches it belongs to FEAT-AGT-22."
    )


def main() -> None:
    """Run every functional-requirement demonstration for the lifecycle."""
    fr_agentic_052()
    fr_agentic_053()
    fr_agentic_054()


if __name__ == "__main__":
    main()
