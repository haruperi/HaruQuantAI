"""Executable FEAT-AGT-01 Agentic contracts usage example.

Demonstrates every public constructor registered for FEAT-AGT-01 through the
documented function-only `app.agentic` package-root API, using realistic
bounded secret-safe data. Each functional requirement FR-AGENTIC-001 through
FR-AGENTIC-003 has a dedicated demonstration function.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.agentic import (
    build_agent_artifact,
    build_agent_message,
    build_agent_provenance,
    build_agent_result,
    build_agent_task,
    build_budget_usage,
    build_workflow_checkpoint,
)
from app.kernel.identity import derive_stable_id, generate_id
from app.kernel.serialization import canonical_digest

from tests.agentic.usage._runner import run_feature_usage

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)

TASK_ID = derive_stable_id("id", "task-eurusd-trend-council")
USAGE_ID = derive_stable_id("id", "usage-eurusd-trend-council")
PROVENANCE_ID = derive_stable_id("id", "provenance-eurusd-trend-council")
MESSAGE_ID = derive_stable_id("id", "message-technical-brief")
ARTIFACT_ID = derive_stable_id("id", "artifact-deliberation-record")
CHECKPOINT_ID = derive_stable_id("id", "checkpoint-collect-briefs")
RESULT_ID = derive_stable_id("id", "result-eurusd-trend-council")

REQUEST_ID = generate_id("req")
WORKFLOW_ID = generate_id("wf")
CORRELATION_ID = generate_id("cor")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _envelope() -> dict[str, object]:
    """Return the shared identity, time, and lineage envelope."""
    return {
        "created_at": NOW,
        "request_id": REQUEST_ID,
        "workflow_id": WORKFLOW_ID,
        "correlation_id": CORRELATION_ID,
        "causation_id": None,
    }


def make_task():
    """Build one bounded governed research task."""
    return build_agent_task(
        {
            **_envelope(),
            "task_id": TASK_ID,
            "workflow_name": "firm_research_council",
            "workflow_version": "1.0.0",
            "objective": (
                "Assess EURUSD H1 trend evidence for the current London session."
            ),
            "input_refs": ("evidence-market-eurusd-h1", "evidence-indicator-ema-200"),
            "principal_id": "operator-owner",
            "scope": {
                "environment": "sandbox",
                "asset_class": "fx",
                "instrument": "EURUSD",
            },
            "deadline_at": NOW + timedelta(minutes=30),
            "idempotency_key": "idem-research-eurusd-0001",
            "budgets": {
                "tokens": Decimal(40_000),
                "model_calls": Decimal(12),
                "tool_calls": Decimal(8),
                "cost": Decimal("5.00"),
            },
        },
    )


def make_usage():
    """Build bounded consumption for the demonstrated task."""
    return build_budget_usage(
        {
            **_envelope(),
            "usage_id": USAGE_ID,
            "task_id": TASK_ID,
            "tokens": 12_480,
            "model_calls": 4,
            "tool_calls": 3,
            "cost": Decimal("1.24"),
            "compute_seconds": Decimal("7.500"),
            "storage_bytes": 0,
            "search_trials": 0,
        },
    )


def make_provenance():
    """Build reproducible lineage for the demonstrated result."""
    return build_agent_provenance(
        {
            **_envelope(),
            "provenance_id": PROVENANCE_ID,
            "task_id": TASK_ID,
            "role_id": "technical_analyst",
            "role_version": "1.0.0",
            "model_profile_id": "profile-market-analysis-a",
            "model_provider": "gemini",
            "model_identifier": "gemini-3.0-pro-002",
            "base_prompt_hash": canonical_digest("technical-analyst-base-prompt"),
            "manifest_hash": canonical_digest("technical-analyst-manifest"),
            "composite_instruction_hash": canonical_digest("technical-composite"),
            "tool_refs": ("data.get_market_data", "indicators.validate_indicator"),
            "evidence_refs": ("evidence-market-eurusd-h1",),
            "mandate_id": "mandate-sandbox",
            "mandate_version": "1.0.0",
            "policy_version": "1.0.0",
            "limits_profile_id": "agentic-limits-sandbox-v1",
            "seed": 20260729,
        },
    )


def make_message():
    """Build one typed deliberation brief."""
    return build_agent_message(
        {
            **_envelope(),
            "message_id": MESSAGE_ID,
            "task_id": TASK_ID,
            "sender_role_id": "technical_analyst",
            "sender_role_version": "1.0.0",
            "recipient_role_id": "strategy_thesis_analyst",
            "message_type": "brief",
            "round_index": 0,
            "content": {
                "observation": "EURUSD H1 printed three consecutive higher lows.",
                "invalidation": "A close below the 200-period EMA invalidates it.",
                "uncertainty": "Session volume is incomplete before 08:00 UTC.",
            },
            "evidence_refs": ("evidence-market-eurusd-h1",),
        },
    )


def make_artifact():
    """Build one content-addressed artefact reference."""
    return build_agent_artifact(
        {
            **_envelope(),
            "artifact_id": ARTIFACT_ID,
            "task_id": TASK_ID,
            "artifact_type": "deliberation_record",
            "content_ref": "staging/agentic/deliberation/eurusd-trend-council",
            "content_schema_id": "agentic.deliberation_record.v1",
            "content_hash": canonical_digest("deliberation-record-content"),
            "size_bytes": 8_192,
            "provenance_id": PROVENANCE_ID,
        },
    )


def make_checkpoint():
    """Build one crash-safe committed workflow position."""
    return build_workflow_checkpoint(
        {
            **_envelope(),
            "checkpoint_id": CHECKPOINT_ID,
            "task_id": TASK_ID,
            "workflow_name": "firm_research_council",
            "workflow_version": "1.0.0",
            "node_id": "collect_briefs",
            "sequence": 2,
            "state": "running",
            "expected_version": 2,
            "state_payload_hash": canonical_digest("checkpoint-collect-briefs"),
        },
    )


def make_result(status="ok", payload=None, reasons=(), detail=None):
    """Build one typed Agentic result in the requested terminal state."""
    return build_agent_result(
        {
            **_envelope(),
            "result_id": RESULT_ID,
            "task_id": TASK_ID,
            "status": status,
            "payload": payload,
            "reasons": reasons,
            "detail": detail,
            "provenance": make_provenance(),
            "budget_usage": make_usage(),
        },
    )


def fr_agentic_001() -> None:
    """FR-AGENTIC-001: Immutable, versioned, finite, strict, JSON-safe contracts."""
    _header(
        "FR-AGENTIC-001: All public contracts are immutable, versioned, finite, "
        "strictly validated, and JSON-safe."
    )

    task = make_task()
    instances = (
        task,
        make_usage(),
        make_provenance(),
        make_message(),
        make_artifact(),
        make_checkpoint(),
        make_result(payload={"trend": "up"}, detail="Two briefs agreed."),
    )
    for instance in instances:
        wire_value = instance.model_dump(mode="json")
        print(f"  {wire_value['schema_id']}: JSON-safe with {len(wire_value)} fields")

    try:
        task.objective = "mutated objective"
        outcome = "ERROR: a frozen contract accepted mutation"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "Mutation of a frozen contract correctly rejected"
    print(outcome)

    try:
        build_agent_task({**task.model_dump(), "unexpected_field": "bad"})
        outcome = "ERROR: an unknown field was accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "Unknown field correctly rejected"
    print(outcome)

    print(f"Exact budget limits preserved: {dict(task.budgets)}")


def fr_agentic_002() -> None:
    """FR-AGENTIC-002: ok, refused, and failed are distinguished."""
    _header(
        "FR-AGENTIC-002: AgentResult distinguishes ok, refused, and failed, and no "
        "free text populates a deterministic execution field."
    )

    ok_result = make_result(payload={"trend": "up"}, detail="Two briefs agreed.")
    print(f"  ok:      payload={ok_result.payload} reasons={ok_result.reasons}")

    refused = make_result(
        status="refused",
        reasons=("INSUFFICIENT_EVIDENCE", "CALENDAR_UNVERIFIED"),
        detail="Session evidence was unavailable at the decision time.",
    )
    print(f"  refused: payload={refused.payload} reasons={refused.reasons}")

    failed = make_result(
        status="failed",
        reasons=("PROVIDER_TIMEOUT",),
        detail="The evaluated model provider exceeded its declared deadline.",
    )
    print(f"  failed:  payload={failed.payload} reasons={failed.reasons}")

    try:
        make_result(status="refused", reasons=("the evidence just felt weak",))
        outcome = "ERROR: a free-text reason was accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "Free-text reason correctly rejected in favour of enumerated codes"
    print(outcome)

    message_fields = {
        key: value
        for key, value in make_message().model_dump().items()
        if key != "canonical_hash"
    }
    try:
        build_agent_message({**message_fields, "content": {"broker_order_id": "1"}})
        outcome = "ERROR: a broker-native execution field was accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "Broker-native execution field correctly rejected"
    print(outcome)


def fr_agentic_003() -> None:
    """FR-AGENTIC-003: Identity, UTC time, schema/version, lineage, and hash."""
    _header(
        "FR-AGENTIC-003: Every contract instance carries stable identity, UTC time, "
        "schema/version, correlation lineage, and a canonical content hash."
    )

    instances = (
        make_task(),
        make_usage(),
        make_provenance(),
        make_message(),
        make_artifact(),
        make_checkpoint(),
        make_result(payload={"trend": "up"}, detail="Two briefs agreed."),
    )
    for instance in instances:
        assert instance.contract_version == "v1"
        assert instance.created_at.utcoffset() == timedelta(0)
        assert instance.request_id.startswith("req-")
        assert instance.workflow_id.startswith("wf-")
        assert instance.correlation_id.startswith("cor-")
        assert len(instance.canonical_hash) == 64
        print(f"  {instance.schema_id}: identity, UTC, lineage, and hash present")

    # The digest is derived from content, so identical content hashes alike.
    assert make_task().canonical_hash == make_task().canonical_hash
    print(f"Derived digest is deterministic: {make_task().canonical_hash[:16]}...")


def main() -> None:
    """Run every functional-requirement demonstration for Agentic contracts."""
    fr_agentic_001()
    fr_agentic_002()
    fr_agentic_003()


if __name__ == "__main__":
    run_feature_usage("FEAT-AGT-01", main)
