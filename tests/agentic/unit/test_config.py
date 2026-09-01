"""Unit tests for the package-wide Agentic settings, limits, and builders.

`_settings.py` and `_limits.py` are approved root-private package
infrastructure introduced with FEAT-AGT-02. They carry no FR of their own but
enforce the Section 5 configuration manifest: Agentic is disabled by default,
an enabled deployment must be completely configured, and no hidden numerical
default may widen authority.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from app.agentic import (
    build_agent_artifact,
    build_agent_message,
    build_agent_provenance,
    build_agent_result,
    build_agent_task,
    build_budget_usage,
    build_workflow_checkpoint,
)
from app.agentic._limits import (
    get_registered_limits_profiles,
    resolve_limits_profile,
)
from app.agentic._settings import get_agentic_settings
from pydantic import ValidationError

from tests.agentic.fixtures import LIMITS_PROFILE_ID

# --------------------------------------------------------------------------
# Settings - disabled by default, complete when enabled
# --------------------------------------------------------------------------


def test_agentic_is_disabled_by_default() -> None:
    settings = get_agentic_settings({})
    assert settings.agentic_enabled is False
    assert settings.agentic_mandate_path is None
    assert settings.agentic_limits_profile is None
    assert settings.agentic_model_profiles == ()


def test_enabled_settings_require_the_complete_configuration() -> None:
    settings = get_agentic_settings(
        {
            "agentic_enabled": True,
            "agentic_mandate_path": Path("data/agentic/agentic_mandate.json"),
            "agentic_limits_profile": LIMITS_PROFILE_ID,
            "agentic_model_profiles": ("profile-a",),
        },
    )
    assert settings.agentic_enabled is True
    assert settings.agentic_limits_profile == LIMITS_PROFILE_ID


@pytest.mark.parametrize(
    "missing",
    ["agentic_mandate_path", "agentic_limits_profile", "agentic_model_profiles"],
)
def test_enabled_settings_fail_closed_when_incomplete(missing) -> None:
    values = {
        "agentic_enabled": True,
        "agentic_mandate_path": Path("mandate.json"),
        "agentic_limits_profile": LIMITS_PROFILE_ID,
        "agentic_model_profiles": ("profile-a",),
    }
    del values[missing]
    with pytest.raises(ValidationError):
        get_agentic_settings(values)


def test_model_profiles_decode_from_a_comma_separated_declaration() -> None:
    settings = get_agentic_settings({"agentic_model_profiles": "profile-a, profile-b"})
    assert settings.agentic_model_profiles == ("profile-a", "profile-b")


def test_blank_model_profile_declaration_is_rejected() -> None:
    with pytest.raises(ValidationError):
        get_agentic_settings({"agentic_model_profiles": "  ,  "})


def test_duplicate_model_profile_is_rejected() -> None:
    with pytest.raises(ValidationError):
        get_agentic_settings({"agentic_model_profiles": ("profile-a", "profile-a")})


def test_settings_are_frozen() -> None:
    settings = get_agentic_settings({})
    with pytest.raises(ValidationError):
        settings.agentic_enabled = True


def test_settings_load_from_the_process_boundary_when_unspecified() -> None:
    # Omitting explicit values resolves through the settings boundary rather
    # than raising; Agentic stays disabled unless configured.
    assert get_agentic_settings().agentic_enabled in {True, False}


# --------------------------------------------------------------------------
# Limits - registered, bounded, and model-non-overridable
# --------------------------------------------------------------------------


def test_registered_limits_profiles_are_discoverable() -> None:
    profiles = get_registered_limits_profiles()
    assert LIMITS_PROFILE_ID in profiles
    assert profiles == tuple(sorted(profiles))


def test_limits_profile_resolves_with_complete_bounds() -> None:
    profile = resolve_limits_profile(LIMITS_PROFILE_ID)
    assert profile.max_participants > 0
    assert profile.max_fan_out > 0
    assert profile.max_rounds == 1
    assert profile.max_schema_repairs == 1
    assert profile.deadline_seconds > 0
    assert profile.audit_retention_days > 0


def test_unregistered_limits_profile_fails_closed() -> None:
    with pytest.raises(ValueError, match="unregistered"):
        resolve_limits_profile("agentic-limits-unbounded")


def test_limits_profile_is_frozen() -> None:
    profile = resolve_limits_profile(LIMITS_PROFILE_ID)
    with pytest.raises(ValidationError):
        profile.max_rounds = 99


# --------------------------------------------------------------------------
# Contract builders - derived digests through the public API
# --------------------------------------------------------------------------


def _envelope(now, request_id, workflow_id, correlation_id) -> dict[str, object]:
    return {
        "created_at": now,
        "request_id": request_id,
        "workflow_id": workflow_id,
        "correlation_id": correlation_id,
        "causation_id": None,
    }


def test_every_builder_derives_a_canonical_digest() -> None:
    from datetime import timedelta

    from app.kernel.identity import derive_stable_id, generate_id
    from app.kernel.serialization import canonical_digest

    from tests.agentic.fixtures import NOW

    env = _envelope(NOW, generate_id("req"), generate_id("wf"), generate_id("cor"))
    task_id = derive_stable_id("id", "task-builder")

    provenance = build_agent_provenance(
        {
            **env,
            "provenance_id": derive_stable_id("id", "prov-builder"),
            "task_id": task_id,
            "role_id": "technical_analyst",
            "role_version": "1.0.0",
            "model_profile_id": "profile-a",
            "model_provider": "gemini",
            "model_identifier": "gemini-3.0-pro-002",
            "base_prompt_hash": canonical_digest("prompt"),
            "manifest_hash": canonical_digest("manifest"),
            "composite_instruction_hash": canonical_digest("composite"),
            "tool_refs": ("data.get_market_data",),
            "evidence_refs": ("evidence-1",),
            "mandate_id": "mandate-sandbox",
            "mandate_version": "1.0.0",
            "policy_version": "1.0.0",
            "limits_profile_id": LIMITS_PROFILE_ID,
            "seed": None,
        },
    )
    usage = build_budget_usage(
        {
            **env,
            "usage_id": derive_stable_id("id", "usage-builder"),
            "task_id": task_id,
            "tokens": 10,
            "model_calls": 1,
            "tool_calls": 0,
            "cost": Decimal("0.01"),
            "compute_seconds": Decimal("0.5"),
            "storage_bytes": 0,
            "search_trials": 0,
        },
    )
    built = (
        build_agent_task(
            {
                **env,
                "task_id": task_id,
                "workflow_name": "firm_research_council",
                "workflow_version": "1.0.0",
                "objective": "Assess trend evidence.",
                "input_refs": ("evidence-1",),
                "principal_id": "operator-owner",
                "scope": {"environment": "sandbox"},
                "deadline_at": NOW + timedelta(minutes=5),
                "idempotency_key": "idem-1",
                "budgets": {"cost": Decimal("1.00")},
            },
        ),
        usage,
        provenance,
        build_agent_message(
            {
                **env,
                "message_id": derive_stable_id("id", "msg-builder"),
                "task_id": task_id,
                "sender_role_id": "technical_analyst",
                "sender_role_version": "1.0.0",
                "recipient_role_id": "strategy_thesis_analyst",
                "message_type": "brief",
                "round_index": 0,
                "content": {"summary": "Trend is up."},
                "evidence_refs": ("evidence-1",),
            },
        ),
        build_agent_artifact(
            {
                **env,
                "artifact_id": derive_stable_id("id", "art-builder"),
                "task_id": task_id,
                "artifact_type": "deliberation_record",
                "content_ref": "staging/a",
                "content_schema_id": "agentic.deliberation_record.v1",
                "content_hash": canonical_digest("content"),
                "size_bytes": 10,
                "provenance_id": provenance.provenance_id,
            },
        ),
        build_workflow_checkpoint(
            {
                **env,
                "checkpoint_id": derive_stable_id("id", "ckpt-builder"),
                "task_id": task_id,
                "workflow_name": "firm_research_council",
                "workflow_version": "1.0.0",
                "node_id": "collect_briefs",
                "sequence": 0,
                "state": "submitted",
                "expected_version": 0,
                "state_payload_hash": canonical_digest("state"),
            },
        ),
        build_agent_result(
            {
                **env,
                "result_id": derive_stable_id("id", "res-builder"),
                "task_id": task_id,
                "status": "refused",
                "payload": None,
                "reasons": ("INSUFFICIENT_EVIDENCE",),
                "detail": None,
                "provenance": provenance,
                "budget_usage": usage,
            },
        ),
    )
    for instance in built:
        assert len(instance.canonical_hash) == 64
        assert instance.canonical_hash != "0" * 64


def test_builder_rejects_a_caller_supplied_digest() -> None:
    with pytest.raises(ValueError, match="derived and must not be supplied"):
        build_agent_task({"canonical_hash": "a" * 64})
