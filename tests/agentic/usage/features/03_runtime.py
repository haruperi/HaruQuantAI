"""Executable FEAT-AGT-03 runtime and model-provider usage example.

Demonstrates every public operation registered for FEAT-AGT-03 through the
documented function-only `app.agentic` package-root API. The agent-graph
runtime is the deterministic in-repo double: no network call is made and
`google-adk` is not a dependency, so the ADK binding half of FR-AGENTIC-007
remains outstanding while its boundary is fully demonstrated here.
"""

import sys
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.agentic import (
    build_deterministic_adk_runtime,
    build_deterministic_model_gateway,
    build_model_invocation,
    build_model_profile,
    derive_profile_digest,
    get_required_upgrade_gates,
    invoke_model,
    validate_model_upgrade,
)
from app.agentic.runtime import ModelOutcome
from app.kernel.serialization import canonical_digest

from tests.agentic.usage._runner import run_feature_usage

INVOCATION_ID = "inv-eurusd-technical-0001"


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def profile_fields(**overrides):
    """Return complete model-profile fields."""
    data = {
        "profile_id": "profile-market-analysis-a",
        "version": "1.0.0",
        "provider": "gemini",
        "model_identifier": "gemini-3.0-pro-002",
        "region": "europe-west4",
        "credential_ref": "vault://agentic/gemini",
        "structured_output_mode": "json_schema",
        "max_context_tokens": 120_000,
        "max_output_tokens": 8_000,
        "max_latency_ms": 30_000,
        "max_cost_per_call": Decimal("0.50"),
        "retention_policy": "zero-retention",
        "training_use_permitted": False,
        "fallback_profile_id": None,
        "evaluation_state": "evaluated",
        "enabled": True,
    }
    data.update(overrides)
    return data


def make_invocation(**overrides):
    """Build one bounded governed invocation."""
    data = {
        "invocation_id": INVOCATION_ID,
        "task_id": "task-eurusd-trend-council",
        "role_id": "technical_analyst",
        "composite_instruction_hash": canonical_digest("technical-composite"),
        "trusted_context": {"instrument": "EURUSD", "timeframe": "H1"},
        "untrusted_evidence": {"headline": "Policy rate left unchanged."},
        "max_output_tokens": 2_000,
        "seed": 20260729,
    }
    data.update(overrides)
    return build_model_invocation(data)


def make_outcome(**overrides) -> ModelOutcome:
    """Build one declared provider-neutral outcome."""
    data = {
        "invocation_id": INVOCATION_ID,
        "status": "ok",
        "output": {"trend": "up", "invalidation": "close below the 200-period EMA"},
        "reasons": (),
        "provider": "gemini",
        "model_identifier": "gemini-3.0-pro-002",
        "tokens_used": 1_240,
        "latency_ms": 880,
        "cost": Decimal("0.02"),
    }
    data.update(overrides)
    return ModelOutcome.model_validate(data)


def fr_agentic_007() -> None:
    """FR-AGENTIC-007: Execution runs behind HaruQuantAI-owned interfaces."""
    _header(
        "FR-AGENTIC-007: Agent execution uses an adapter behind HaruQuantAI-owned "
        "interfaces and exposes no ADK or provider object publicly."
    )

    profile = build_model_profile(profile_fields())
    invocation = make_invocation()
    gateway = build_deterministic_model_gateway({INVOCATION_ID: make_outcome()})
    runtime = build_deterministic_adk_runtime(gateway)

    served = runtime.execute_node("collect_briefs", profile, invocation)
    print(f"  node executed:   collect_briefs -> {served.status}")
    print(f"  outcome type:    {type(served).__name__}")
    print(f"  outcome module:  {type(served).__module__}")
    print(f"  structured out:  {dict(served.output)}")
    print("The outcome is a HaruQuantAI contract; no provider object crosses out.")
    print("NOTE: the Google ADK binding is not implemented; this is the")
    print("      deterministic in-repo runtime satisfying the same port.")


def fr_agentic_008() -> None:
    """FR-AGENTIC-008: Profiles pin capability and enforce policy."""
    _header(
        "FR-AGENTIC-008: Model profiles pin provider and model capability and "
        "enforce schema, tool, privacy, latency, cost, region, and fallback policy."
    )

    profile = build_model_profile(profile_fields())
    print(f"  pinned model:    {profile.provider}/{profile.model_identifier}")
    print(f"  region:          {profile.region}")
    print(f"  retention:       {profile.retention_policy}")
    print(f"  training use:    {profile.training_use_permitted}")
    print(f"  cost ceiling:    {profile.max_cost_per_call}")
    print(f"  profile digest:  {derive_profile_digest(profile)[:16]}...")

    gateway = build_deterministic_model_gateway({INVOCATION_ID: make_outcome()})
    served = invoke_model(gateway, profile, make_invocation())
    print(f"Governed invocation succeeded in {served.latency_ms}ms at {served.cost}")

    for label, override in (
        ("floating alias", {"model_identifier": "gemini-3.0-pro-latest"}),
        ("secret material as credential", {"credential_ref": "sk-abcdefghijklmno"}),
        ("shadow profile used in production", {"evaluation_state": "shadow"}),
    ):
        try:
            candidate = build_model_profile(profile_fields(**override))
            invoke_model(gateway, candidate, make_invocation())
            outcome = f"ERROR: {label} was accepted"
        except Exception:  # noqa: BLE001 - usage demonstrates rejection.
            outcome = f"{label.capitalize()} correctly rejected"
        print(f"  {outcome}")

    substituted = build_deterministic_model_gateway(
        {INVOCATION_ID: make_outcome(model_identifier="gemini-3.0-flash-001")},
    )
    try:
        invoke_model(substituted, profile, make_invocation())
        outcome = "ERROR: a silent model substitution was accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "Silent model substitution correctly detected and refused"
    print(f"  {outcome}")


def fr_agentic_009() -> None:
    """FR-AGENTIC-009: A model change stays disabled until gates pass."""
    _header(
        "FR-AGENTIC-009: A model change remains disabled until versioned "
        "regression, shadow, safety, and economic acceptance gates pass."
    )

    current = build_model_profile(profile_fields())
    candidate = build_model_profile(
        profile_fields(
            profile_id="profile-market-analysis-b",
            model_identifier="gemini-3.1-pro-001",
        ),
    )
    gates = get_required_upgrade_gates()
    print(f"  required gates ({len(gates)}): {', '.join(gates)}")

    no_evidence = validate_model_upgrade(current, candidate, {})
    print(f"  no evidence:   approved={no_evidence.approved} ({no_evidence.reason})")

    failing = dict.fromkeys(gates, True)
    failing["injection_regression"] = False
    failed = validate_model_upgrade(current, candidate, failing)
    print(f"  a gate failed: approved={failed.approved} ({failed.reason})")
    print(f"                 failed gates: {', '.join(failed.failed_gates)}")

    regressed = validate_model_upgrade(
        current,
        build_model_profile(
            profile_fields(
                profile_id="profile-c",
                max_context_tokens=1_000,
                max_output_tokens=500,
            ),
        ),
        dict.fromkeys(gates, True),
    )
    print(f"  regression:    approved={regressed.approved} ({regressed.reason})")

    approved = validate_model_upgrade(current, candidate, dict.fromkeys(gates, True))
    print(f"  all gates pass: approved={approved.approved} ({approved.reason})")


def main() -> None:
    """Run every functional-requirement demonstration for the Agentic runtime."""
    fr_agentic_007()
    fr_agentic_008()
    fr_agentic_009()


if __name__ == "__main__":
    run_feature_usage("FEAT-AGT-03", main)
