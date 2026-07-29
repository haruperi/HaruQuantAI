"""Executable FEAT-AGT-05 permissions usage example.

Demonstrates every public operation registered for FEAT-AGT-05 through the
documented function-only `app.agentic` package-root API. Authorization is
deny-by-default: the allow path is shown once, then each facet is broken in
turn to show the deterministic refusal.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.agentic import (
    authorize_tool_call,
    build_agent_policy,
    build_firm_mandate,
    build_in_memory_nonce_store,
    build_tool_approval_attestation,
    build_tool_policy,
    derive_object_hash,
    get_forbidden_permission_classes,
    validate_policy_registry,
)

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
READ_TOOL = "data.get_market_data"
COMPUTE_TOOL = "indicators.validate_indicator"
ROLE_ID = "technical_analyst"
OBJECT_HASH = derive_object_hash({"symbol": "EURUSD", "timeframe": "H1"})
OTHER_HASH = derive_object_hash({"symbol": "GBPUSD", "timeframe": "H4"})

UNIVERSAL_PROHIBITIONS = (
    "broker_credential_access",
    "broker_native_mutation",
    "mandate_modification",
    "kill_switch_clearing",
    "self_approval",
    "approval_delegation",
    "production_code_mutation",
    "hot_loading",
    "unbounded_discussion",
    "unbounded_spend",
    "unverified_evidence_use",
    "receipt_as_fill",
)

SCOPE = {"environment": "sandbox", "asset_class": "fx"}


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def make_mandate():
    """Build the sandbox mandate registering both tools."""
    return build_firm_mandate(
        {
            "mandate_id": "mandate-sandbox",
            "version": "1.0.0",
            "environment": "sandbox",
            "effective_at": datetime(2026, 7, 1, tzinfo=UTC),
            "expires_at": datetime(2026, 12, 31, tzinfo=UTC),
            "owner_principal": "operator-owner",
            "objectives": ("market_research",),
            "asset_scopes": {"asset_class": "fx"},
            "enabled_features": ("FEAT-AGT-11", "FEAT-AGT-12"),
            "enabled_roles": (ROLE_ID,),
            "model_profiles": ("profile-market-analysis-a",),
            "tool_scopes": {
                READ_TOOL: "read_evidence",
                COMPUTE_TOOL: "compute_deterministic",
            },
            "limits_profile_id": "agentic-limits-sandbox-v1",
            "budgets": {"cost": Decimal("50.00")},
            "approval_policy": ("deterministic_compute",),
            "retention_policy": {"evidence": "365d"},
            "prohibited_actions": UNIVERSAL_PROHIBITIONS,
            "fallback_policy": "refuse",
        },
        "owner-signature-sandbox",
    )


def make_tool(**overrides):
    """Build the read-evidence tool policy."""
    data = {
        "tool_name": READ_TOOL,
        "version": "1.0.0",
        "owning_feature": "FEAT-AGT-11",
        "receiver_domain": "data",
        "public_operation": "get_market_data",
        "request_schema_id": "data.market_data_request.v1",
        "result_schema_id": "data.market_dataset.v1",
        "permission_class": "read_evidence",
        "side_effect_class": "read_only",
        "eligible_roles": (ROLE_ID,),
        "scope": dict(SCOPE),
        "idempotent": True,
        "requires_approval": False,
        "max_input_bytes": 8_192,
        "max_output_bytes": 1_048_576,
        "timeout_seconds": 30,
        "max_calls_per_task": 8,
        "enabled": True,
    }
    data.update(overrides)
    return build_tool_policy(data)


def make_compute_tool(**overrides):
    """Build the approval-gated deterministic compute tool policy."""
    data = {
        "tool_name": COMPUTE_TOOL,
        "owning_feature": "FEAT-AGT-12",
        "receiver_domain": "indicators",
        "public_operation": "validate_indicator",
        "permission_class": "compute_deterministic",
        "side_effect_class": "deterministic_compute",
        "requires_approval": True,
    }
    data.update(overrides)
    return make_tool(**data)


def make_policy(**overrides):
    """Build the technical-analyst agent policy."""
    data = {
        "role_id": ROLE_ID,
        "role_version": "1.0.0",
        "permission_classes": ("read_evidence", "compute_deterministic"),
        "allowed_tools": (READ_TOOL, COMPUTE_TOOL),
        "environment": "sandbox",
        "max_tool_calls": 8,
        "max_cost": Decimal("2.50"),
        "enabled": True,
    }
    data.update(overrides)
    return build_agent_policy(data)


def make_attestation(**overrides):
    """Build one authenticated single-use approval."""
    data = {
        "attestation_id": "att-0001",
        "principal_id": "operator-owner",
        "permission_class": "compute_deterministic",
        "tool_name": COMPUTE_TOOL,
        "tool_version": "1.0.0",
        "object_hash": OBJECT_HASH,
        "workflow_id": "wf-research",
        "run_id": "run-0001",
        "environment": "sandbox",
        "scope": {"asset_class": "fx"},
        "issued_at": NOW,
        "expires_at": NOW + timedelta(minutes=10),
        "nonce": "nonce-0001",
        "policy_version": "1.0.0",
        "signature": "owner-signature",
    }
    data.update(overrides)
    return build_tool_approval_attestation(data)


def fr_agentic_013() -> None:
    """FR-AGENTIC-013: Authorization is deny-by-default."""
    _header(
        "FR-AGENTIC-013: Tool and agent authorization is deny-by-default and "
        "requires registered principal, role, tool/version, scope, environment, "
        "budget, and trusted runtime context."
    )

    mandate, tool, policy = make_mandate(), make_tool(), make_policy()
    allowed = authorize_tool_call(
        mandate,
        policy,
        tool,
        "agent-technical",
        OBJECT_HASH,
        request_scope=dict(SCOPE),
        at_time=NOW,
    )
    print(f"  allow: {allowed.allowed} reason={allowed.reason}")
    print(f"         grant expires {allowed.grant_expires_at.isoformat()}")

    breaks = (
        ("disabled tool", {"tool": make_tool(enabled=False)}),
        ("disabled role", {"policy": make_policy(enabled=False)}),
        ("unregistered tool", {"tool": make_tool(tool_name="research.run_edge_lab")}),
        (
            "role not eligible",
            {"tool": make_tool(eligible_roles=("sentiment_analyst",))},
        ),
        (
            "class not held",
            {"policy": make_policy(permission_classes=("compute_deterministic",))},
        ),
        ("wrong environment", {"request_scope": {"environment": "paper"}}),
        (
            "wrong asset scope",
            {"request_scope": {"environment": "sandbox", "asset_class": "equities"}},
        ),
        ("budget exhausted", {"calls_used": 8}),
    )
    for label, override in breaks:
        call = {
            "mandate": mandate,
            "policy": policy,
            "tool": tool,
            "principal_id": "agent-technical",
            "object_hash": OBJECT_HASH,
            "request_scope": dict(SCOPE),
            "at_time": NOW,
        }
        call.update(override)
        print(f"  deny ({label}): {authorize_tool_call(**call).reason}")


def fr_agentic_014() -> None:
    """FR-AGENTIC-014: Approvals are single-use, scoped, and unforgeable."""
    _header(
        "FR-AGENTIC-014: Approval attestations are authenticated, single-purpose, "
        "scoped, expiring, non-replayable, and impossible for an agent to forge."
    )

    mandate, tool, policy = make_mandate(), make_compute_tool(), make_policy()
    store = build_in_memory_nonce_store()

    def call(**overrides):
        data = {
            "mandate": mandate,
            "policy": policy,
            "tool": tool,
            "principal_id": "agent-technical",
            "object_hash": OBJECT_HASH,
            "request_scope": dict(SCOPE),
            "nonce_store": store,
            "at_time": NOW,
        }
        data.update(overrides)
        return authorize_tool_call(**data)

    cases = (
        ("no approval supplied", {}),
        ("valid approval", {"attestation": make_attestation()}),
        ("same approval replayed", {"attestation": make_attestation()}),
        (
            "no single-use enforcement",
            {"attestation": make_attestation(nonce="n2"), "nonce_store": None},
        ),
        (
            "expired approval",
            {
                "attestation": make_attestation(nonce="n3"),
                "at_time": NOW + timedelta(hours=1),
            },
        ),
        (
            "different object",
            {"attestation": make_attestation(nonce="n4", object_hash=OTHER_HASH)},
        ),
        (
            "different environment",
            {"attestation": make_attestation(nonce="n5", environment="paper")},
        ),
        (
            "self-approval",
            {
                "attestation": make_attestation(
                    nonce="n6",
                    principal_id="agent-technical",
                ),
            },
        ),
    )
    for label, override in cases:
        decision = call(**override)
        print(f"  {label:<26} allowed={decision.allowed} reason={decision.reason}")


def fr_agentic_015() -> None:
    """FR-AGENTIC-015: Forbidden capabilities cannot be registered at all."""
    _header(
        "FR-AGENTIC-015: Agentic exposes no broker mutation, mandate override, "
        "kill-switch clear, production deployment, or direct order tool."
    )

    print(f"  never granted: {', '.join(get_forbidden_permission_classes())}")

    for label, override in (
        ("broker receiver", {"receiver_domain": "brokers"}),
        ("order placement", {"public_operation": "place_order"}),
        ("kill-switch clear", {"public_operation": "clear_kill_switch"}),
        ("mandate override", {"public_operation": "override_mandate"}),
        ("production deploy", {"public_operation": "deploy"}),
        ("controlled mutation", {"permission_class": "controlled_mutation"}),
    ):
        try:
            make_tool(**override)
            outcome = f"ERROR: {label} was registrable"
        except Exception:  # noqa: BLE001 - usage demonstrates rejection.
            outcome = f"{label} correctly unregistrable"
        print(f"  {outcome}")

    registered_tools, registered_policies = validate_policy_registry(
        make_mandate(),
        (make_tool(), make_compute_tool()),
        (make_policy(),),
    )
    print(
        f"  registry validated: {len(registered_tools)} tools, "
        f"{len(registered_policies)} agent policies"
    )

    try:
        validate_policy_registry(make_mandate(), (make_tool(),), (make_policy(),))
        outcome = "ERROR: a mandate tool with no policy was accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "Mandate tool with no registered policy correctly rejected"
    print(f"  {outcome}")


def main() -> None:
    """Run every functional-requirement demonstration for Agentic permissions."""
    fr_agentic_013()
    fr_agentic_014()
    fr_agentic_015()


if __name__ == "__main__":
    main()
