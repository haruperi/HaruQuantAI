"""Integration evidence for `WF-AGT-SEC` — promote artefact.

Exercises the promotion path over real evidence: a `FEAT-AGT-16` staged
artefact, a `FEAT-AGT-14` experiment verdict, a `FEAT-AGT-15` sweep verdict,
and a `FEAT-AGT-17` critique memo, assembled into one packet, gated
deterministically, approved by an authenticated human, and recorded in an
append-only ledger.

What this does **not** exercise, deliberately: no receiver is called. Strategy
alone registers a strategy version, and `WF-AGT-SEC` step 7 is the receiver's.
The workflow stays `Missing` until `FEAT-AGT-22` supplies the handoff, and the
final test here asserts that boundary rather than papering over it.
"""

from __future__ import annotations

import pytest
from app.agentic.lifecycle import (
    assess_promotion,
    build_in_memory_lifecycle_store,
    build_promotion_evidence_packet,
    get_artifact_history,
    get_artifact_state,
    is_terminal_state,
    transition_artifact,
)

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


def _evidence(**overrides: object) -> dict[str, object]:
    """Assemble the four contracts a promotion packet carries."""
    data: dict[str, object] = {
        "artifact": build_promotion_artifact(),
        "experiment_verdict": build_promotion_experiment_verdict(),
        "sweep_verdict": build_promotion_sweep_verdict(),
        "critique": build_promotion_critique(),
    }
    data.update(overrides)
    return data


def _packet(evidence: dict[str, object]):
    return build_promotion_evidence_packet(
        {
            "packet_id": "packet-integration-a",
            "task_id": PROMOTION_TASK_ID,
            **evidence,
            "simulation_manifest_ref": "simulator.artifact_manifest:run-a",
            "lifetime_trial_ceiling": CEILING,
            "approver_id": PROMOTION_APPROVER_ID,
            "approval_environment": PROMOTION_ENVIRONMENT,
            "assembled_at": NOW.isoformat(),
        },
    )


def test_promotion_traverses_the_full_governed_path() -> None:
    store = build_in_memory_lifecycle_store()
    evidence = _evidence()
    artifact = evidence["artifact"]
    digest = artifact.artifact_hash  # type: ignore[union-attr]

    # 1. The coder's artefact enters the ledger at `staged` and nowhere else.
    staged = transition_artifact(
        store,
        digest,
        artifact.artifact_id,  # type: ignore[union-attr]
        "staged",
        "process-coder",
        "the coder staged a complete artefact",
        at_time=NOW,
    )
    assert staged.sequence == 1
    assert staged.previous_state is None

    # 2. Evaluation evidence exists, so the artefact advances to `evaluated`.
    transition_artifact(
        store,
        digest,
        artifact.artifact_id,  # type: ignore[union-attr]
        "evaluated",
        "process-evaluation",
        "the critique addressed every required challenge",
        unresolved_concerns=evidence["critique"].blocking_concerns,  # type: ignore[union-attr]
        at_time=NOW,
    )
    assert get_artifact_state(store, digest) == "evaluated"

    # 3. The packet assembles only because every piece of evidence exists.
    packet = _packet(evidence)
    assert packet.packet_hash

    # 4. The deterministic gates run over evidence the packet already carries.
    assessment = assess_promotion(
        **evidence,  # type: ignore[arg-type]
        task_id=PROMOTION_TASK_ID,
        lifetime_trial_ceiling=CEILING,
        environment=PROMOTION_ENVIRONMENT,
        approver=ApprovingUser(),
        packet_hash=packet.packet_hash,
        at_time=NOW,
    )
    assert assessment.promotable is True
    assert assessment.failed_gates == ()

    # 5. Approval is recorded against the packet that justified it.
    approved = transition_artifact(
        store,
        digest,
        artifact.artifact_id,  # type: ignore[union-attr]
        "approved",
        PROMOTION_APPROVER_ID,
        "an authenticated reviewer approved the complete packet",
        packet=packet,
        at_time=NOW,
    )
    assert approved.packet_hash == packet.packet_hash
    assert store.load_packet(packet.packet_hash) is not None

    # 6. The whole history is append-only and readable in order.
    history = get_artifact_history(store, digest)
    assert [record.state for record in history] == ["staged", "evaluated", "approved"]
    assert [record.sequence for record in history] == [1, 2, 3]


def test_a_terminated_promotion_ends_the_artefact() -> None:
    store = build_in_memory_lifecycle_store()
    evidence = _evidence(
        experiment_verdict=build_promotion_experiment_verdict(
            evidence_classes={"run-a": "discovery"},
        ),
    )
    artifact = evidence["artifact"]
    digest = artifact.artifact_hash  # type: ignore[union-attr]
    transition_artifact(
        store,
        digest,
        artifact.artifact_id,  # type: ignore[union-attr]
        "staged",
        "process-coder",
        "the coder staged a complete artefact",
        at_time=NOW,
    )

    assessment = assess_promotion(
        **evidence,  # type: ignore[arg-type]
        task_id=PROMOTION_TASK_ID,
        lifetime_trial_ceiling=CEILING,
        environment=PROMOTION_ENVIRONMENT,
        approver=ApprovingUser(),
        at_time=NOW,
    )
    assert assessment.promotable is False
    assert assessment.termination_reason == "leakage_detected"

    terminal = transition_artifact(
        store,
        digest,
        artifact.artifact_id,  # type: ignore[union-attr]
        "research_only",
        "process-lifecycle",
        "the experiment carries no out-of-sample evidence",
        termination_reason=assessment.termination_reason,
        at_time=NOW,
    )
    assert is_terminal_state(terminal.state)

    # Re-assembling a passing packet does not reopen it.
    with pytest.raises(ValueError, match="terminal"):
        transition_artifact(
            store,
            digest,
            artifact.artifact_id,  # type: ignore[union-attr]
            "evaluated",
            "process-lifecycle",
            "a second attempt with better evidence",
            at_time=NOW,
        )


def test_an_approved_artefact_cannot_skip_to_registered_by_a_fresh_packet() -> None:
    store = build_in_memory_lifecycle_store()
    evidence = _evidence()
    artifact = evidence["artifact"]
    digest = artifact.artifact_hash  # type: ignore[union-attr]
    transition_artifact(
        store,
        digest,
        artifact.artifact_id,  # type: ignore[union-attr]
        "staged",
        "process-coder",
        "staged",
        at_time=NOW,
    )
    # A caller holding a valid packet still cannot bypass evaluation: the
    # current state is read from the ledger, never supplied by the caller.
    with pytest.raises(ValueError, match="may only follow evaluated"):
        transition_artifact(
            store,
            digest,
            artifact.artifact_id,  # type: ignore[union-attr]
            "approved",
            PROMOTION_APPROVER_ID,
            "approving directly from staged",
            packet=_packet(evidence),
            at_time=NOW,
        )


def test_a_regenerated_artefact_starts_over() -> None:
    store = build_in_memory_lifecycle_store()
    original = build_promotion_artifact()
    for state in ("staged", "evaluated", "approved", "registered"):
        transition_artifact(
            store,
            original.artifact_hash,
            original.artifact_id,
            state,  # type: ignore[arg-type]
            "process-lifecycle",
            f"advancing to {state}",
            at_time=NOW,
        )
    assert get_artifact_state(store, original.artifact_hash) == "registered"

    # One changed dependency is a material change, so the digest changes and
    # the new artefact inherits nothing — not even its predecessor's approval.
    revised = build_promotion_artifact(dependencies={"numpy": "2.5.0"})
    assert revised.artifact_hash != original.artifact_hash
    assert get_artifact_state(store, revised.artifact_hash) is None
    with pytest.raises(ValueError, match="must enter at 'staged'"):
        transition_artifact(
            store,
            revised.artifact_hash,
            revised.artifact_id,
            "registered",
            "process-lifecycle",
            "inheriting the previous approval",
            at_time=NOW,
        )


def test_promotion_stops_at_the_receiver_boundary() -> None:
    # `WF-AGT-SEC` step 7 belongs to Strategy. This domain records that an
    # artefact reached `registered`; it never causes the registration, and the
    # workflow stays incomplete until FEAT-AGT-22 supplies the handoff.
    from pathlib import Path

    sources = "".join(
        path.read_text(encoding="utf-8")
        for path in Path("app/agentic/lifecycle").glob("*.py")
    )
    assert "register_strategy_version" not in sources
    assert "StrategyRegistrationRequest" not in sources
