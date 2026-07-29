"""Unit tests for FEAT-AGT-02 firm governance, roster, and authority.

Covers FR-AGENTIC-004 (mandate completeness and signature), FR-AGENTIC-005
(registry validation, agent-package parity, prompt integrity), and
FR-AGENTIC-006 (titles grant no implicit authority).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
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
from app.agentic.governance.models import UNIVERSAL_PROHIBITIONS
from pydantic import ValidationError

from tests.agentic.fixtures import (
    LIMITS_PROFILE_ID,
    MANDATE_END,
    MANDATE_START,
    NOW,
    QUANT_ROLE_ID,
    READ_TOOL,
    TECHNICAL_ROLE_ID,
    build_quant_manifest,
    build_sandbox_mandate,
    build_technical_manifest,
    mandate_fields,
    manifest_fields,
)


def _registry(**mandate_overrides):
    mandate = build_sandbox_mandate(**mandate_overrides)
    return get_role_registry(
        mandate,
        (build_technical_manifest(), build_quant_manifest()),
        NOW,
    )


# --------------------------------------------------------------------------
# FR-AGENTIC-004 - mandate completeness, integrity, and validity
# --------------------------------------------------------------------------


def test_mandate_declares_the_complete_operating_envelope() -> None:
    mandate = build_sandbox_mandate()
    assert mandate.environment == "sandbox"
    assert mandate.limits_profile_id == LIMITS_PROFILE_ID
    assert mandate.objectives
    assert mandate.approval_policy
    assert mandate.fallback_policy == "refuse"


def test_mandate_content_hash_is_derived_and_verifies() -> None:
    mandate = build_sandbox_mandate()
    assert validate_firm_mandate(mandate, NOW) is mandate


def test_supplying_a_derived_field_is_rejected() -> None:
    with pytest.raises(ValueError, match="derived fields"):
        build_firm_mandate(mandate_fields(content_hash="a" * 64), "sig")


def test_tampered_mandate_fails_integrity() -> None:
    mandate = build_sandbox_mandate()
    tampered = mandate.model_copy(update={"owner_principal": "attacker"})
    with pytest.raises(ValueError, match="content hash mismatch"):
        validate_firm_mandate(tampered, NOW)


def test_expired_mandate_is_rejected() -> None:
    mandate = build_sandbox_mandate()
    with pytest.raises(ValueError, match="expired"):
        validate_firm_mandate(mandate, MANDATE_END + timedelta(days=1))


def test_not_yet_effective_mandate_is_rejected() -> None:
    mandate = build_sandbox_mandate()
    with pytest.raises(ValueError, match="not yet effective"):
        validate_firm_mandate(mandate, MANDATE_START - timedelta(days=1))


def test_inverted_validity_window_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_firm_mandate(
            mandate_fields(effective_at=MANDATE_END, expires_at=MANDATE_START),
            "sig",
        )


def test_mandate_must_deny_every_universal_prohibition() -> None:
    reduced = tuple(a for a in UNIVERSAL_PROHIBITIONS if a != "kill_switch_clearing")
    with pytest.raises(ValidationError):
        build_firm_mandate(mandate_fields(prohibited_actions=reduced), "sig")


def test_wildcard_asset_scope_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_firm_mandate(mandate_fields(asset_scopes={"asset_class": "*"}), "sig")


def test_mandate_may_not_grant_a_forbidden_permission_class() -> None:
    with pytest.raises(ValidationError):
        build_firm_mandate(
            mandate_fields(tool_scopes={"trading.dispatch": "controlled_mutation"}),
            "sig",
        )


def test_mandate_may_not_register_a_broker_tool() -> None:
    mandate = build_firm_mandate(
        mandate_fields(tool_scopes={"brokers.place_order": "read_evidence"}),
        "sig",
    )
    with pytest.raises(ValueError, match="Brokers"):
        validate_firm_mandate(mandate, NOW)


def test_mandate_may_not_register_a_kill_switch_tool() -> None:
    mandate = build_firm_mandate(
        mandate_fields(tool_scopes={"risk.clear_kill_switch": "read_evidence"}),
        "sig",
    )
    with pytest.raises(ValueError, match="never registered"):
        validate_firm_mandate(mandate, NOW)


def test_non_canonical_enabled_feature_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_firm_mandate(mandate_fields(enabled_features=("FEAT-AGT-99",)), "sig")


# --------------------------------------------------------------------------
# FR-AGENTIC-005 - registry, package parity, and prompt integrity
# --------------------------------------------------------------------------


def test_registry_resolves_enabled_roles() -> None:
    registry = _registry()
    assert list_registered_roles(registry) == (QUANT_ROLE_ID, TECHNICAL_ROLE_ID)
    assert list_enabled_roles(registry) == (QUANT_ROLE_ID, TECHNICAL_ROLE_ID)
    assert resolve_role_manifest(registry, TECHNICAL_ROLE_ID).role_id == (
        TECHNICAL_ROLE_ID
    )
    assert get_registry_mandate(registry).mandate_id == "mandate-sandbox"


def test_unregistered_role_is_refused() -> None:
    registry = _registry()
    with pytest.raises(ValueError, match="unregistered"):
        resolve_role_manifest(registry, "sentiment_analyst")


def test_disabled_role_is_refused() -> None:
    mandate = build_sandbox_mandate()
    registry = get_role_registry(
        mandate,
        (build_technical_manifest(enabled=False), build_quant_manifest()),
        NOW,
    )
    with pytest.raises(ValueError, match="disabled"):
        resolve_role_manifest(registry, TECHNICAL_ROLE_ID)


def test_manifest_hash_is_derived_and_verifies() -> None:
    manifest = build_technical_manifest()
    assert len(manifest.manifest_hash) == 64
    assert len(manifest.composite_instruction_hash) == 64
    assert manifest.manifest_hash != manifest.composite_instruction_hash


def test_supplying_a_derived_digest_is_rejected() -> None:
    with pytest.raises(ValueError, match="derived digests"):
        build_role_manifest(manifest_fields(manifest_hash="a" * 64))


def test_mutated_prompt_hash_fails_manifest_integrity() -> None:
    # The base prompt digest is part of the manifest body, so a mutated
    # prompt.md is caught by the body digest before the composite check runs.
    manifest = build_technical_manifest()
    mutated = manifest.model_copy(update={"base_prompt_hash": "b" * 64})
    with pytest.raises(ValueError, match="hash mismatch"):
        get_role_registry(build_sandbox_mandate(), (mutated,), NOW)


def test_mutated_composite_instruction_fails_integrity() -> None:
    # The composite digest is excluded from the body digest, so tampering with
    # it alone leaves the body valid and must be caught by its own check.
    manifest = build_technical_manifest()
    mutated = manifest.model_copy(update={"composite_instruction_hash": "b" * 64})
    with pytest.raises(ValueError, match="composite instruction mismatch"):
        get_role_registry(build_sandbox_mandate(), (mutated,), NOW)


def test_mutated_manifest_body_fails_integrity() -> None:
    manifest = build_technical_manifest()
    mutated = manifest.model_copy(update={"freshness_seconds": 1})
    with pytest.raises(ValueError, match="hash mismatch"):
        get_role_registry(build_sandbox_mandate(), (mutated,), NOW)


def test_duplicate_role_identity_is_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        get_role_registry(
            build_sandbox_mandate(),
            (build_technical_manifest(), build_technical_manifest()),
            NOW,
        )


def test_duplicate_agent_package_is_rejected() -> None:
    clashing = build_quant_manifest(
        agent_package="agents/market_analysis/technical_analyst",
    )
    with pytest.raises(ValueError, match="claimed by both"):
        get_role_registry(
            build_sandbox_mandate(),
            (build_technical_manifest(), clashing),
            NOW,
        )


def test_malformed_agent_package_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_role_manifest(manifest_fields(agent_package="technical_analyst"))


def test_role_owning_a_disabled_feature_is_rejected() -> None:
    with pytest.raises(ValueError, match="does not enable"):
        get_role_registry(
            build_sandbox_mandate(enabled_features=("FEAT-AGT-12",)),
            (build_technical_manifest(),),
            NOW,
        )


def test_unapproved_model_profile_is_rejected() -> None:
    with pytest.raises(ValueError, match="unapproved model profile"):
        get_role_registry(
            build_sandbox_mandate(),
            (build_technical_manifest(model_profile_id="profile-unevaluated"),),
            NOW,
        )


def test_unapproved_fallback_profile_is_rejected() -> None:
    with pytest.raises(ValueError, match="unapproved fallback"):
        get_role_registry(
            build_sandbox_mandate(),
            (build_technical_manifest(permitted_fallback="profile-unevaluated"),),
            NOW,
        )


def test_mandate_enabling_an_unregistered_role_is_rejected() -> None:
    with pytest.raises(ValueError, match="unregistered roles"):
        get_role_registry(
            build_sandbox_mandate(enabled_roles=(TECHNICAL_ROLE_ID, "ghost_role")),
            (build_technical_manifest(), build_quant_manifest()),
            NOW,
        )


def test_role_enabled_outside_the_mandate_is_rejected() -> None:
    with pytest.raises(ValueError, match="outside the mandate"):
        get_role_registry(
            build_sandbox_mandate(enabled_roles=(TECHNICAL_ROLE_ID,)),
            (build_technical_manifest(), build_quant_manifest()),
            NOW,
        )


# --------------------------------------------------------------------------
# FR-AGENTIC-006 - titles grant no implicit authority
# --------------------------------------------------------------------------


def test_unregistered_tool_request_is_rejected() -> None:
    with pytest.raises(ValueError, match="unregistered tool"):
        get_role_registry(
            build_sandbox_mandate(),
            (build_technical_manifest(tools=(READ_TOOL, "portfolio.activate")),),
            NOW,
        )


def test_role_may_not_hold_a_tool_class_it_lacks() -> None:
    escalating = build_technical_manifest(permission_classes=("read_evidence",))
    with pytest.raises(ValueError, match="which the role does not hold"):
        get_role_registry(build_sandbox_mandate(), (escalating,), NOW)


def test_coordinator_title_confers_no_extra_capability() -> None:
    # A leadership title is only a department label; the manifest still resolves
    # to exactly the tools and classes it declares.
    coordinator = build_technical_manifest(
        department="executive_coordination",
        description="Firm Coordinator classifying requests and composing work.",
        tools=(READ_TOOL,),
        permission_classes=("read_evidence",),
    )
    registry = get_role_registry(
        build_sandbox_mandate(enabled_roles=(TECHNICAL_ROLE_ID,)),
        (coordinator,),
        NOW,
    )
    resolved = resolve_role_manifest(registry, TECHNICAL_ROLE_ID)
    assert resolved.tools == (READ_TOOL,)
    assert resolved.permission_classes == ("read_evidence",)


def test_manifest_may_not_declare_a_forbidden_permission_class() -> None:
    with pytest.raises(ValidationError):
        build_role_manifest(manifest_fields(permission_classes=("critical",)))


def test_manifest_may_not_request_a_broker_tool() -> None:
    with pytest.raises(ValueError, match="Brokers"):
        get_role_registry(
            build_sandbox_mandate(),
            (build_technical_manifest(tools=("brokers.place_order",)),),
            NOW,
        )


def test_repeated_permission_class_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_role_manifest(
            manifest_fields(permission_classes=("read_evidence", "read_evidence")),
        )


def test_non_positive_freshness_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_role_manifest(manifest_fields(freshness_seconds=0))


def test_negative_budget_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_role_manifest(manifest_fields(budgets={"cost": Decimal(-1)}))


def test_naive_mandate_timestamp_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_firm_mandate(
            mandate_fields(effective_at=datetime(2026, 7, 1)),  # noqa: DTZ001
            "sig",
        )


def test_mandate_environments_are_closed() -> None:
    with pytest.raises(ValidationError):
        build_firm_mandate(mandate_fields(environment="production"), "sig")
    accepted = build_firm_mandate(mandate_fields(environment="development"), "sig")
    assert accepted.environment == "development"


def test_registry_default_evaluation_time_uses_current_utc() -> None:
    # The sandbox mandate window brackets the real current time, so omitting
    # the evaluation time must resolve rather than fail closed.
    assert MANDATE_START <= datetime.now(UTC) < MANDATE_END
    assert validate_firm_mandate(build_sandbox_mandate()) is not None
