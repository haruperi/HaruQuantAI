"""Integration evidence for the Google ADK 2.x binding (FEAT-AGT-03).

Verifies the binding structurally: port conformance, credential containment,
cost derivation, profile pinning, and the async/sync bridge guard.

**No live provider call is made anywhere in this file.** ADK is exercised only
as far as construction and guard conditions allow; a real Gemini call costs
money and sends data to a third party, so it is a separate, explicitly
authorized step. The binding is therefore structurally verified, not
live-verified.
"""

from __future__ import annotations

import asyncio
import sys
from decimal import Decimal

import pytest
from app.agentic import build_model_invocation, build_model_profile
from app.agentic.runtime import AdkRuntime
from app.agentic.runtime.adk import (
    _derive_cost,
    _structured_output,
    build_adk_runtime,
)
from app.kernel.serialization import canonical_digest

FAKE_KEY = "test-key-not-a-real-credential"

# Both deprecations below originate entirely inside `google-adk` /
# `google-genai`, not in this repository. They are exempted by exact message so
# that `-W error` still catches any deprecation our own code introduces, here
# or anywhere else in the suite.
pytestmark = [
    pytest.mark.filterwarnings("ignore:.*_UnionGenericAlias.*:DeprecationWarning"),
    pytest.mark.filterwarnings("ignore:.*BaseAgentConfig is deprecated.*"),
]


def _profile(**overrides: object):
    fields: dict[str, object] = {
        "profile_id": "profile-agent",
        "version": "1.0.0",
        "provider": "gemini",
        "model_identifier": "gemini-3.6-flash",
        "region": "europe-west4",
        "credential_ref": "settings.google_genai.api_key",
        "structured_output_mode": "json_schema",
        "max_context_tokens": 120_000,
        "max_output_tokens": 8_000,
        "max_latency_ms": 30_000,
        "max_cost_per_call": Decimal("0.50"),
        "retention_policy": "zero-retention",
        "training_use_permitted": False,
        "fallback_profile_id": None,
        "cost_per_1k_input": Decimal("0.00010"),
        "cost_per_1k_output": Decimal("0.00040"),
        "evaluation_state": "evaluated",
        "enabled": True,
    }
    fields.update(overrides)
    return build_model_profile(fields)


def _invocation(**overrides: object):
    fields: dict[str, object] = {
        "invocation_id": "inv-adk-0001",
        "task_id": "task-adk",
        "role_id": "technical_analyst",
        "composite_instruction_hash": canonical_digest("composite"),
        "trusted_context": {"instrument": "EURUSD"},
        "untrusted_evidence": {"headline": "Rates unchanged."},
        "max_output_tokens": 2_000,
        "seed": None,
    }
    fields.update(overrides)
    return build_model_invocation(fields)


def _runtime(**overrides: object):
    return build_adk_runtime(
        overrides.pop("profile", _profile()),  # type: ignore[arg-type]
        overrides.pop("api_key", FAKE_KEY),  # type: ignore[arg-type]
        overrides.pop("instructions", {"technical_analyst": "Base instruction."}),  # type: ignore[arg-type]
    )


# --------------------------------------------------------------------------
# Containment - no ADK or provider object crosses the boundary
# --------------------------------------------------------------------------


def test_importing_the_public_api_loads_no_provider_module() -> None:
    # The bare `google` namespace package is pulled in by protobuf via other
    # domains; what must never load is an ADK or provider SDK module.
    import app.agentic  # noqa: F401

    forbidden = ("google.adk", "google.genai", "vertexai", "openai", "anthropic")
    loaded = [m for m in sys.modules if m.startswith(forbidden)]
    assert loaded == []


def test_the_binding_satisfies_the_runtime_port() -> None:
    assert isinstance(_runtime(), AdkRuntime)


def test_the_credential_never_enters_a_contract() -> None:
    profile = _profile()
    invocation = _invocation()
    for contract in (profile, invocation):
        assert FAKE_KEY not in str(contract.model_dump(mode="json"))
    # The profile carries a reference, never the secret itself.
    assert profile.credential_ref == "settings.google_genai.api_key"


def test_a_profile_carrying_secret_material_is_rejected() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        _profile(credential_ref="sk-abcdefghijklmnopqrst")


# --------------------------------------------------------------------------
# Construction guards
# --------------------------------------------------------------------------


@pytest.mark.parametrize("blank", ["", "   "])
def test_a_blank_credential_is_refused(blank) -> None:
    with pytest.raises(ValueError, match="credential is required"):
        _runtime(api_key=blank)


def test_an_unpriced_profile_cannot_serve_a_real_call() -> None:
    with pytest.raises(ValueError, match="must declare token pricing"):
        _runtime(profile=_profile(cost_per_1k_input=None, cost_per_1k_output=None))


# --------------------------------------------------------------------------
# Cost derivation - a false zero must never defeat the ceiling
# --------------------------------------------------------------------------


def test_cost_is_derived_from_reported_tokens() -> None:
    cost = _derive_cost(_profile(), input_tokens=2_000, output_tokens=1_000)
    # 2.000 * 0.00010 + 1.000 * 0.00040
    assert cost == Decimal("0.00060")


def test_zero_tokens_derive_zero_cost() -> None:
    assert _derive_cost(_profile(), 0, 0) == Decimal(0)


def test_an_unpriced_profile_raises_rather_than_reporting_zero() -> None:
    unpriced = _profile(cost_per_1k_input=None, cost_per_1k_output=None)
    with pytest.raises(ValueError, match="must not be reported as zero"):
        _derive_cost(unpriced, 1_000, 1_000)


def test_derived_cost_is_exact_not_floating_point() -> None:
    cost = _derive_cost(_profile(), input_tokens=3, output_tokens=7)
    assert isinstance(cost, Decimal)


# --------------------------------------------------------------------------
# Output adaptation
# --------------------------------------------------------------------------


def test_json_object_output_is_flattened_to_strings() -> None:
    adapted = _structured_output('{"claim:trend": "up", "round": 2}')
    assert adapted == {"claim:trend": "up", "round": "2"}


def test_non_json_output_is_preserved_as_text() -> None:
    assert _structured_output("plain reading") == {"text": "plain reading"}


def test_malformed_json_falls_back_to_text() -> None:
    adapted = _structured_output('{"unterminated": ')
    assert set(adapted) == {"text"}


def test_json_array_output_falls_back_to_text() -> None:
    assert _structured_output("[1, 2, 3]") == {"text": "[1, 2, 3]"}


# --------------------------------------------------------------------------
# Execution guards - no live call is required to prove these
# --------------------------------------------------------------------------


def test_a_mismatched_profile_is_refused_before_any_provider_call() -> None:
    runtime = _runtime()
    other = _profile(profile_id="profile-other")
    with pytest.raises(ValueError, match="refusing to serve"):
        runtime.execute_node("interpret", other, _invocation())


def test_calling_from_inside_an_event_loop_fails_closed() -> None:
    runtime = _runtime()

    async def caller() -> None:
        runtime.execute_node("interpret", _profile(), _invocation())

    with pytest.raises(ValueError, match="running event loop"):
        asyncio.run(caller())


def test_an_unverified_role_instruction_is_refused() -> None:
    runtime = _runtime(instructions={})
    with pytest.raises(ValueError, match="no verified instruction"):
        runtime._build_agent("interpret", _invocation())


def test_the_bound_agent_uses_the_pinned_model_and_supplied_instruction() -> None:
    runtime = _runtime(instructions={"technical_analyst": "Verified instruction."})
    agent = runtime._build_agent("interpret", _invocation())
    assert agent.name == "interpret"
    assert agent.instruction == "Verified instruction."
    assert agent.model.model == "gemini-3.6-flash"


def test_the_bound_agent_carries_the_credential_only_in_client_kwargs() -> None:
    runtime = _runtime()
    agent = runtime._build_agent("interpret", _invocation())
    # The key reaches the provider client and nowhere else on the agent.
    assert agent.model.client_kwargs == {"api_key": FAKE_KEY}
    assert FAKE_KEY not in str(agent.instruction)
    assert FAKE_KEY not in str(agent.name)


def test_the_payload_separates_trusted_context_from_untrusted_evidence() -> None:
    runtime = _runtime()
    content = runtime._build_message(_invocation())
    payload = content.parts[0].text
    assert '"trusted_context"' in payload
    assert '"untrusted_evidence"' in payload
    assert "Rates unchanged." in payload
