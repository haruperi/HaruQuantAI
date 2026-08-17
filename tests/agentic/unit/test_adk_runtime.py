"""Unit tests for Agentic ADK runtime port, deterministic binding, and helper utilities."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.agentic.runtime.adk import (
    _derive_cost,
    _structured_output,
    build_deterministic_adk_runtime,
    build_deterministic_model_gateway,
)
from app.agentic.runtime.models import ModelInvocation, ModelOutcome, ModelProfile


def _make_profile(**kwargs) -> ModelProfile:
    """Helper to construct a valid ModelProfile instance."""
    defaults = {
        "profile_id": "p-1",
        "version": "1.0.0",
        "provider": "google_genai",
        "model_identifier": "gemini-2.5-flash",
        "region": "us-central1",
        "credential_ref": "env:GEMINI_API_KEY",
        "structured_output_mode": "json_schema",
        "max_context_tokens": 8192,
        "max_output_tokens": 2048,
        "max_latency_ms": 5000,
        "max_cost_per_call": Decimal("0.10"),
        "retention_policy": "zero-retention",
        "training_use_permitted": False,
        "evaluation_state": "evaluated",
        "enabled": True,
        "cost_per_1k_input": Decimal("0.001"),
        "cost_per_1k_output": Decimal("0.002"),
    }
    defaults.update(kwargs)
    return ModelProfile(**defaults)


def _make_outcome(**kwargs) -> ModelOutcome:
    """Helper to construct a valid ModelOutcome instance."""
    defaults = {
        "invocation_id": "inv-1",
        "status": "ok",
        "output": {"result": "ok"},
        "reasons": (),
        "provider": "google_genai",
        "model_identifier": "gemini-2.5-flash",
        "tokens_used": 20,
        "latency_ms": 100,
        "cost": Decimal("0.01"),
    }
    defaults.update(kwargs)
    return ModelOutcome(**defaults)


def _make_invocation(**kwargs) -> ModelInvocation:
    """Helper to construct a valid ModelInvocation instance."""
    defaults = {
        "invocation_id": "inv-1",
        "task_id": "task-1",
        "role_id": "role-1",
        "composite_instruction_hash": "a" * 64,
        "trusted_context": {"ctx": "test"},
        "untrusted_evidence": {"ev": "test"},
        "max_output_tokens": 1000,
    }
    defaults.update(kwargs)
    return ModelInvocation(**defaults)


def test_derive_cost() -> None:
    """Verify _derive_cost correctly calculates token cost."""
    prof = _make_profile(
        cost_per_1k_input=Decimal("0.01"), cost_per_1k_output=Decimal("0.02")
    )
    cost = _derive_cost(prof, input_tokens=1000, output_tokens=500)
    assert cost == Decimal("0.02")

    unpriced = _make_profile(cost_per_1k_input=None, cost_per_1k_output=None)
    with pytest.raises(ValueError, match="declares no token pricing"):
        _derive_cost(unpriced, input_tokens=100, output_tokens=100)


def test_structured_output_parsing() -> None:
    """Verify _structured_output adapts JSON and plain text."""
    json_text = '{"summary": "all good", "score": "0.95"}'
    adapted_json = _structured_output(json_text)
    assert adapted_json == {"summary": "all good", "score": "0.95"}

    raw_text = "Plain text response"
    adapted_raw = _structured_output(raw_text)
    assert adapted_raw == {"text": "Plain text response"}

    invalid_json = "{invalid json"
    adapted_invalid = _structured_output(invalid_json)
    assert adapted_invalid == {"text": "{invalid json"}


def test_deterministic_adk_runtime_execution() -> None:
    """Verify deterministic ADK runtime execution."""
    inv = _make_invocation()
    out = _make_outcome()
    prof = _make_profile()

    gw = build_deterministic_model_gateway({"inv-1": out})
    runtime = build_deterministic_adk_runtime(gw)

    executed_outcome = runtime.execute_node("node-1", prof, inv)
    assert executed_outcome.invocation_id == "inv-1"

    missing_inv = _make_invocation(invocation_id="missing-inv")
    with pytest.raises(ValueError, match="no scripted outcome for invocation"):
        runtime.execute_node("node-1", prof, missing_inv)
