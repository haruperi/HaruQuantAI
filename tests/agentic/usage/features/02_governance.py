"""Executable FEAT-AGT-02 firm governance usage example.

Demonstrates every public operation registered for FEAT-AGT-02 through the
documented function-only `app.agentic` package-root API, using a realistic
bounded secret-safe `sandbox` mandate and two-role roster. Each functional
requirement FR-AGENTIC-004 through FR-AGENTIC-006 has a dedicated
demonstration function.
"""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.agentic import (
    build_firm_mandate,
    build_role_manifest,
    get_registry_mandate,
    get_role_registry,
    list_enabled_roles,
    list_registered_roles,
    resolve_role_manifest,
    validate_firm_mandate,
)
from app.kernel.serialization import canonical_digest

from tests.agentic.usage._runner import run_feature_usage

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
MANDATE_START = datetime(2026, 7, 1, tzinfo=UTC)
MANDATE_END = datetime(2026, 12, 31, tzinfo=UTC)

READ_TOOL = "data.get_market_data"
COMPUTE_TOOL = "indicators.validate_indicator"

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


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def mandate_fields(**overrides):
    """Return complete firm-mandate fields excluding derived values."""
    data = {
        "mandate_id": "mandate-sandbox",
        "version": "1.0.0",
        "environment": "sandbox",
        "effective_at": MANDATE_START,
        "expires_at": MANDATE_END,
        "owner_principal": "operator-owner",
        "objectives": ("market_research", "risk_advisory"),
        "asset_scopes": {"asset_class": "fx", "venue": "otc"},
        "enabled_features": ("FEAT-AGT-11", "FEAT-AGT-12"),
        "enabled_roles": ("technical_analyst", "quantitative_analyst"),
        "model_profiles": ("profile-market-analysis-a", "profile-market-analysis-b"),
        "tool_scopes": {
            READ_TOOL: "read_evidence",
            COMPUTE_TOOL: "compute_deterministic",
        },
        "limits_profile_id": "agentic-limits-sandbox-v1",
        "budgets": {"cost": Decimal("50.00"), "tokens": Decimal(500_000)},
        "approval_policy": ("artifact_promotion", "trade_proposal_submission"),
        "retention_policy": {"evidence": "365d", "audit": "730d"},
        "prohibited_actions": UNIVERSAL_PROHIBITIONS,
        "fallback_policy": "refuse",
    }
    data.update(overrides)
    return data


def manifest_fields(**overrides):
    """Return complete role-manifest fields excluding derived digests."""
    data = {
        "role_id": "technical_analyst",
        "version": "1.0.0",
        "owning_feature": "FEAT-AGT-11",
        "department": "market_analysis",
        "agent_package": "agents/market_analysis/technical_analyst",
        "description": "Interprets canonical Data and Indicators evidence.",
        "objective": "Describe observable market structure with invalidation.",
        "expertise_boundary": "Does not size positions or approve any action.",
        "supported_assets": ("fx",),
        "refusal_conditions": ("missing_evidence", "stale_evidence"),
        "input_schema_id": "agentic.technical_request.v1",
        "output_schema_id": "agentic.technical_evidence_pack.v1",
        "base_prompt_hash": canonical_digest("technical-analyst-base-prompt"),
        "role_instruction": None,
        "model_profile_id": "profile-market-analysis-a",
        "permitted_fallback": "profile-market-analysis-b",
        "tools": (READ_TOOL, COMPUTE_TOOL),
        "permission_classes": ("read_evidence", "compute_deterministic"),
        "data_requirements": ("canonical_market_data", "indicator_versions"),
        "freshness_seconds": 900,
        "budgets": {"cost": Decimal("2.50"), "tokens": Decimal(40_000)},
        "evaluation_set_id": "eval-technical-v1",
        "baseline_id": "baseline-deterministic-indicators",
        "enabled": True,
    }
    data.update(overrides)
    return data


def quant_manifest_fields(**overrides):
    """Return complete quantitative-analyst manifest fields."""
    data = manifest_fields(
        role_id="quantitative_analyst",
        owning_feature="FEAT-AGT-12",
        agent_package="agents/market_analysis/quantitative_analyst",
        description="Analyses versioned Research and Analytics evidence.",
        input_schema_id="agentic.quantitative_request.v1",
        output_schema_id="agentic.quantitative_evidence_pack.v1",
        base_prompt_hash=canonical_digest("quantitative-analyst-base-prompt"),
        evaluation_set_id="eval-quantitative-v1",
    )
    data.update(overrides)
    return data


def fr_agentic_004() -> None:
    """FR-AGENTIC-004: The mandate defines the complete operating envelope."""
    _header(
        "FR-AGENTIC-004: The firm mandate defines objectives, prohibited authority, "
        "assets, environments, budgets, approvals, and enabled capability roles."
    )

    mandate = build_firm_mandate(mandate_fields(), "owner-signature-sandbox")
    print(f"  mandate:     {mandate.mandate_id} v{mandate.version}")
    print(f"  environment: {mandate.environment}")
    print(f"  objectives:  {', '.join(mandate.objectives)}")
    print(f"  features:    {', '.join(mandate.enabled_features)}")
    print(f"  limits:      {mandate.limits_profile_id}")
    print(f"  denies:      {len(mandate.prohibited_actions)} universal prohibitions")
    print(f"  content hash derived: {mandate.content_hash[:16]}...")

    validated = validate_firm_mandate(mandate, NOW)
    print(f"Mandate validated in force at {NOW.isoformat()}: {validated is mandate}")

    tampered = mandate.model_copy(update={"owner_principal": "attacker"})
    try:
        validate_firm_mandate(tampered, NOW)
        outcome = "ERROR: a tampered mandate was accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "Tampered mandate correctly rejected by content-hash mismatch"
    print(outcome)

    try:
        validate_firm_mandate(mandate, datetime(2027, 1, 2, tzinfo=UTC))
        outcome = "ERROR: an expired mandate was accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "Expired mandate correctly rejected"
    print(outcome)


def fr_agentic_005() -> None:
    """FR-AGENTIC-005: The role registry validates the roster at startup."""
    _header(
        "FR-AGENTIC-005: The role registry validates unique roles, owning features, "
        "agent packages, prompt and instruction hashes, profiles, tools, and schemas."
    )

    mandate = build_firm_mandate(mandate_fields(), "owner-signature-sandbox")
    technical = build_role_manifest(manifest_fields())
    quantitative = build_role_manifest(quant_manifest_fields())

    print(f"  manifest hash derived:  {technical.manifest_hash[:16]}...")
    print(f"  composite hash derived: {technical.composite_instruction_hash[:16]}...")

    registry = get_role_registry(mandate, (technical, quantitative), NOW)
    print(f"  registered roles: {', '.join(list_registered_roles(registry))}")
    print(f"  enabled roles:    {', '.join(list_enabled_roles(registry))}")
    print(f"  backing mandate:  {get_registry_mandate(registry).mandate_id}")

    resolved = resolve_role_manifest(registry, "technical_analyst")
    print(f"  resolved {resolved.role_id} -> {resolved.agent_package}")

    mutated = technical.model_copy(update={"composite_instruction_hash": "b" * 64})
    try:
        get_role_registry(mandate, (mutated,), NOW)
        outcome = "ERROR: a mutated composite instruction was accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "Mutated composite instruction correctly rejected"
    print(outcome)

    try:
        get_role_registry(mandate, (technical, technical), NOW)
        outcome = "ERROR: a duplicate role identity was accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "Duplicate role identity correctly rejected"
    print(outcome)

    try:
        resolve_role_manifest(registry, "sentiment_analyst")
        outcome = "ERROR: an unregistered role resolved"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "Unregistered role correctly refused"
    print(outcome)


def fr_agentic_006() -> None:
    """FR-AGENTIC-006: Titles grant no implicit authority."""
    _header(
        "FR-AGENTIC-006: Leadership and department titles coordinate work but grant "
        "no implicit tool, approval, risk, promotion, or execution authority."
    )

    coordinator = build_role_manifest(
        manifest_fields(
            department="executive_coordination",
            description="Firm Coordinator classifying requests and composing work.",
            tools=(READ_TOOL,),
            permission_classes=("read_evidence",),
        ),
    )
    mandate = build_firm_mandate(
        mandate_fields(enabled_roles=("technical_analyst",)),
        "owner-signature-sandbox",
    )
    registry = get_role_registry(mandate, (coordinator,), NOW)
    resolved = resolve_role_manifest(registry, "technical_analyst")
    print(f"  coordinator department: {resolved.department}")
    print(f"  coordinator tools:      {resolved.tools}")
    print(f"  coordinator classes:    {resolved.permission_classes}")
    print("A leadership title resolved to exactly its declared capability.")

    escalating = build_role_manifest(
        manifest_fields(permission_classes=("read_evidence",)),
    )
    try:
        get_role_registry(mandate, (escalating,), NOW)
        outcome = "ERROR: a role held a tool class it does not declare"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "Privilege escalation via an undeclared tool class correctly rejected"
    print(outcome)

    try:
        build_role_manifest(manifest_fields(permission_classes=("critical",)))
        outcome = "ERROR: a critical permission class was accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "Critical permission class correctly rejected"
    print(outcome)

    try:
        get_role_registry(
            mandate,
            (build_role_manifest(manifest_fields(tools=("brokers.place_order",))),),
            NOW,
        )
        outcome = "ERROR: a Brokers tool was accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "Brokers tool correctly rejected; Agentic has no Brokers dependency"
    print(outcome)


def main() -> None:
    """Run every functional-requirement demonstration for Agentic governance."""
    fr_agentic_004()
    fr_agentic_005()
    fr_agentic_006()


if __name__ == "__main__":
    run_feature_usage("FEAT-AGT-02", main)
