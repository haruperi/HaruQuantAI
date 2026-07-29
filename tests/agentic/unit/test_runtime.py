"""Unit tests for FEAT-AGT-03 runtime and provider-neutral models.

Covers FR-AGENTIC-007 (no ADK/provider object crosses the boundary),
FR-AGENTIC-008 (profile pinning and enforced limits), and FR-AGENTIC-009
(a model change stays disabled until every gate passes).
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import app.agentic
import pytest
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
from app.agentic.runtime import AdkRuntime, ModelGateway, ModelOutcome
from pydantic import ValidationError

from tests.agentic.fixtures import PROMPT_DIGEST


def profile_fields(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
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


def invocation_fields(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "invocation_id": "inv-0001",
        "task_id": "task-0001",
        "role_id": "technical_analyst",
        "composite_instruction_hash": PROMPT_DIGEST,
        "trusted_context": {"instrument": "EURUSD"},
        "untrusted_evidence": {"headline": "Rates unchanged."},
        "max_output_tokens": 2_000,
        "seed": 7,
    }
    data.update(overrides)
    return data


def outcome(**overrides: object) -> ModelOutcome:
    data: dict[str, object] = {
        "invocation_id": "inv-0001",
        "status": "ok",
        "output": {"trend": "up"},
        "reasons": (),
        "provider": "gemini",
        "model_identifier": "gemini-3.0-pro-002",
        "tokens_used": 1_200,
        "latency_ms": 900,
        "cost": Decimal("0.02"),
    }
    data.update(overrides)
    return ModelOutcome.model_validate(data)


def _runtime(result: ModelOutcome) -> AdkRuntime:
    gateway = build_deterministic_model_gateway({"inv-0001": result})
    return build_deterministic_adk_runtime(gateway)


# --------------------------------------------------------------------------
# FR-AGENTIC-007 - no ADK or provider object crosses the boundary
# --------------------------------------------------------------------------


def test_no_agentic_source_imports_an_adk_or_provider_sdk() -> None:
    # Static scan: FR-AGENTIC-007 is about what the package may import at all,
    # not about what a given test session happens to have loaded.
    forbidden = ("google.adk", "google.genai", "vertexai", "openai", "anthropic")
    package = Path(app.agentic.__file__).parent
    offenders = [
        f"{source.relative_to(package)}:{number}"
        for source in package.rglob("*.py")
        for number, line in enumerate(
            source.read_text(encoding="utf-8").splitlines(), start=1
        )
        if line.startswith(("import ", "from "))
        and any(token in line for token in forbidden)
    ]
    assert offenders == []


def test_no_agentic_source_imports_brokers() -> None:
    package = Path(app.agentic.__file__).parent
    offenders = [
        f"{source.relative_to(package)}:{number}"
        for source in package.rglob("*.py")
        for number, line in enumerate(
            source.read_text(encoding="utf-8").splitlines(), start=1
        )
        if line.startswith(("import ", "from ")) and "services.brokers" in line
    ]
    assert offenders == []


def test_runtime_and_gateway_are_structural_ports() -> None:
    result = outcome()
    gateway = build_deterministic_model_gateway({"inv-0001": result})
    assert isinstance(gateway, ModelGateway)
    assert isinstance(build_deterministic_adk_runtime(gateway), AdkRuntime)


def test_node_execution_returns_a_provider_neutral_outcome() -> None:
    profile = build_model_profile(profile_fields())
    invocation = build_model_invocation(invocation_fields())
    served = _runtime(outcome()).execute_node("collect_briefs", profile, invocation)
    assert served.status == "ok"
    assert served.output == {"trend": "up"}
    assert type(served).__module__.startswith("app.agentic.")


# --------------------------------------------------------------------------
# FR-AGENTIC-008 - profile pinning and enforced limits
# --------------------------------------------------------------------------


def test_floating_alias_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_model_profile(profile_fields(model_identifier="gemini-3.0-pro-latest"))


def test_wildcard_identifier_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_model_profile(profile_fields(model_identifier="gemini-*"))


@pytest.mark.parametrize(
    "secret",
    ["sk-abcdefghijklmnop", "ghp_abcdefghijklmnop", "A" * 48],
)
def test_secret_material_is_rejected_where_a_reference_belongs(secret) -> None:
    with pytest.raises(ValidationError):
        build_model_profile(profile_fields(credential_ref=secret))


def test_output_ceiling_may_not_exceed_context_ceiling() -> None:
    with pytest.raises(ValidationError):
        build_model_profile(
            profile_fields(max_context_tokens=1_000, max_output_tokens=2_000),
        )


def test_profile_may_not_be_its_own_fallback() -> None:
    with pytest.raises(ValidationError):
        build_model_profile(
            profile_fields(fallback_profile_id="profile-market-analysis-a"),
        )


def test_disabled_evaluation_state_may_not_be_enabled() -> None:
    with pytest.raises(ValidationError):
        build_model_profile(profile_fields(evaluation_state="disabled", enabled=True))


def test_disabled_profile_refuses_invocation() -> None:
    profile = build_model_profile(profile_fields(enabled=False))
    with pytest.raises(ValueError, match="disabled"):
        invoke_model(
            build_deterministic_model_gateway({"inv-0001": outcome()}),
            profile,
            build_model_invocation(invocation_fields()),
        )


def test_shadow_profile_refuses_governed_invocation() -> None:
    profile = build_model_profile(profile_fields(evaluation_state="shadow"))
    with pytest.raises(ValueError, match="only an evaluated profile"):
        invoke_model(
            build_deterministic_model_gateway({"inv-0001": outcome()}),
            profile,
            build_model_invocation(invocation_fields()),
        )


def test_invocation_exceeding_the_output_ceiling_is_refused() -> None:
    profile = build_model_profile(profile_fields())
    invocation = build_model_invocation(invocation_fields(max_output_tokens=99_000))
    with pytest.raises(ValueError, match="exceeding the profile ceiling"):
        invoke_model(
            build_deterministic_model_gateway({"inv-0001": outcome()}),
            profile,
            invocation,
        )


def test_silent_model_substitution_is_detected() -> None:
    profile = build_model_profile(profile_fields())
    substituted = outcome(model_identifier="gemini-3.0-flash-001")
    with pytest.raises(ValueError, match="model substitution detected"):
        invoke_model(
            build_deterministic_model_gateway({"inv-0001": substituted}),
            profile,
            build_model_invocation(invocation_fields()),
        )


def test_silent_provider_substitution_is_detected() -> None:
    profile = build_model_profile(profile_fields())
    substituted = outcome(provider="openai")
    with pytest.raises(ValueError, match="provider substitution detected"):
        invoke_model(
            build_deterministic_model_gateway({"inv-0001": substituted}),
            profile,
            build_model_invocation(invocation_fields()),
        )


def test_cost_ceiling_breach_is_detected() -> None:
    profile = build_model_profile(profile_fields())
    expensive = outcome(cost=Decimal("5.00"))
    with pytest.raises(ValueError, match="observed cost"):
        invoke_model(
            build_deterministic_model_gateway({"inv-0001": expensive}),
            profile,
            build_model_invocation(invocation_fields()),
        )


def test_latency_ceiling_breach_is_detected() -> None:
    profile = build_model_profile(profile_fields())
    slow = outcome(latency_ms=90_000)
    with pytest.raises(ValueError, match="observed latency"):
        invoke_model(
            build_deterministic_model_gateway({"inv-0001": slow}),
            profile,
            build_model_invocation(invocation_fields()),
        )


def test_mismatched_outcome_is_rejected() -> None:
    profile = build_model_profile(profile_fields())
    mismatched = outcome(invocation_id="inv-9999")
    gateway = build_deterministic_model_gateway({"inv-0001": mismatched})
    with pytest.raises(ValueError, match="does not answer"):
        invoke_model(gateway, profile, build_model_invocation(invocation_fields()))


def test_refused_outcome_requires_a_reason() -> None:
    with pytest.raises(ValidationError):
        outcome(status="refused", output=None, reasons=())


def test_refused_outcome_carries_no_output() -> None:
    with pytest.raises(ValidationError):
        outcome(status="refused", reasons=("INSUFFICIENT_EVIDENCE",))


def test_profile_digest_is_deterministic() -> None:
    profile = build_model_profile(profile_fields())
    assert derive_profile_digest(profile) == derive_profile_digest(profile)
    assert len(derive_profile_digest(profile)) == 64


def test_unscripted_invocation_fails_closed() -> None:
    profile = build_model_profile(profile_fields())
    gateway = build_deterministic_model_gateway({})
    with pytest.raises(ValueError, match="no scripted outcome"):
        invoke_model(gateway, profile, build_model_invocation(invocation_fields()))


def test_malformed_instruction_hash_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_model_invocation(invocation_fields(composite_instruction_hash="nope"))


# --------------------------------------------------------------------------
# FR-AGENTIC-009 - upgrades stay disabled until every gate passes
# --------------------------------------------------------------------------


def _all_gates(value: bool = True) -> dict[str, bool]:
    return dict.fromkeys(get_required_upgrade_gates(), value)


def test_required_gates_are_declared() -> None:
    gates = get_required_upgrade_gates()
    assert "shadow_comparison" in gates
    assert "privacy_and_retention" in gates
    assert len(set(gates)) == len(gates)


def test_upgrade_approved_when_every_gate_passes() -> None:
    current = build_model_profile(profile_fields())
    candidate = build_model_profile(
        profile_fields(profile_id="profile-b", model_identifier="gemini-3.1-pro-001"),
    )
    decision = validate_model_upgrade(current, candidate, _all_gates())
    assert decision.approved is True
    assert decision.reason == "approved"


def test_upgrade_refused_when_a_gate_fails() -> None:
    current = build_model_profile(profile_fields())
    candidate = build_model_profile(profile_fields(profile_id="profile-b"))
    gates = _all_gates()
    gates["injection_regression"] = False
    decision = validate_model_upgrade(current, candidate, gates)
    assert decision.approved is False
    assert decision.reason == "gate_failed"
    assert decision.failed_gates == ("injection_regression",)


def test_missing_gate_evidence_is_not_a_default_pass() -> None:
    current = build_model_profile(profile_fields())
    candidate = build_model_profile(profile_fields(profile_id="profile-b"))
    decision = validate_model_upgrade(current, candidate, {})
    assert decision.approved is False
    assert decision.reason == "gate_evidence_missing"
    assert set(decision.missing_gates) == set(get_required_upgrade_gates())


def test_unevaluated_candidate_is_refused() -> None:
    current = build_model_profile(profile_fields())
    candidate = build_model_profile(
        profile_fields(profile_id="profile-b", evaluation_state="shadow"),
    )
    decision = validate_model_upgrade(current, candidate, _all_gates())
    assert decision.approved is False
    assert decision.reason == "candidate_not_evaluated"


def test_capability_regression_is_refused() -> None:
    current = build_model_profile(profile_fields())
    candidate = build_model_profile(
        profile_fields(
            profile_id="profile-b", max_context_tokens=1_000, max_output_tokens=500
        ),
    )
    decision = validate_model_upgrade(current, candidate, _all_gates())
    assert decision.approved is False
    assert decision.reason == "capability_regression"


def test_structured_output_mode_change_is_a_regression() -> None:
    current = build_model_profile(profile_fields())
    candidate = build_model_profile(
        profile_fields(profile_id="profile-b", structured_output_mode="tool_call"),
    )
    decision = validate_model_upgrade(current, candidate, _all_gates())
    assert decision.approved is False
    assert decision.reason == "capability_regression"


def test_upgrade_decision_is_frozen() -> None:
    current = build_model_profile(profile_fields())
    candidate = build_model_profile(profile_fields(profile_id="profile-b"))
    decision = validate_model_upgrade(current, candidate, _all_gates())
    with pytest.raises(ValidationError):
        decision.approved = False
