"""Unit tests for FEAT-AGT-05 tool registry, permissions, and approvals.

Covers FR-AGENTIC-013 (deny-by-default authorization), FR-AGENTIC-014
(authenticated, single-purpose, scoped, expiring, non-replayable, unforgeable
attestations), and FR-AGENTIC-015 (no broker, override, kill-switch,
deployment, or order tool is registrable).
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from app.agentic import (
    authorize_tool_call,
    build_agent_policy,
    build_in_memory_nonce_store,
    build_tool_approval_attestation,
    build_tool_policy,
    derive_object_hash,
    get_forbidden_permission_classes,
    validate_policy_registry,
)
from pydantic import ValidationError

from tests.agentic.fixtures import (
    COMPUTE_TOOL,
    NOW,
    READ_TOOL,
    TECHNICAL_ROLE_ID,
    build_sandbox_mandate,
)

OBJECT_HASH = derive_object_hash({"symbol": "EURUSD", "timeframe": "H1"})


def tool_fields(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "tool_name": READ_TOOL,
        "version": "1.0.0",
        "owning_feature": "FEAT-AGT-11",
        "receiver_domain": "data",
        "public_operation": "get_market_data",
        "request_schema_id": "data.market_data_request.v1",
        "result_schema_id": "data.market_dataset.v1",
        "permission_class": "read_evidence",
        "side_effect_class": "read_only",
        "eligible_roles": (TECHNICAL_ROLE_ID,),
        "scope": {"environment": "sandbox", "asset_class": "fx"},
        "idempotent": True,
        "requires_approval": False,
        "max_input_bytes": 8_192,
        "max_output_bytes": 1_048_576,
        "timeout_seconds": 30,
        "max_calls_per_task": 8,
        "enabled": True,
    }
    data.update(overrides)
    return data


def compute_tool_fields(**overrides: object) -> dict[str, object]:
    return tool_fields(
        tool_name=COMPUTE_TOOL,
        owning_feature="FEAT-AGT-12",
        receiver_domain="indicators",
        public_operation="validate_indicator",
        request_schema_id="indicators.request.v1",
        result_schema_id="indicators.series.v1",
        permission_class="compute_deterministic",
        side_effect_class="deterministic_compute",
        **overrides,
    )


def policy_fields(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "role_id": TECHNICAL_ROLE_ID,
        "role_version": "1.0.0",
        "permission_classes": ("read_evidence", "compute_deterministic"),
        "allowed_tools": (READ_TOOL, COMPUTE_TOOL),
        "environment": "sandbox",
        "max_tool_calls": 8,
        "max_cost": Decimal("2.50"),
        "enabled": True,
    }
    data.update(overrides)
    return data


def attestation_fields(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "attestation_id": "att-0001",
        "principal_id": "operator-owner",
        "permission_class": "read_evidence",
        "tool_name": READ_TOOL,
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
    return data


def _authorize(**kwargs: object):
    defaults: dict[str, object] = {
        "mandate": build_sandbox_mandate(),
        "policy": build_agent_policy(policy_fields()),
        "tool": build_tool_policy(tool_fields()),
        "principal_id": "agent-technical",
        "object_hash": OBJECT_HASH,
        "request_scope": {"environment": "sandbox", "asset_class": "fx"},
        "at_time": NOW,
    }
    defaults.update(kwargs)
    return authorize_tool_call(**defaults)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# FR-AGENTIC-013 - deny by default
# --------------------------------------------------------------------------


def test_a_fully_agreeing_call_is_authorized() -> None:
    decision = _authorize()
    assert decision.allowed is True
    assert decision.reason == "allowed"
    assert decision.grant_expires_at is not None


def test_disabled_tool_is_denied() -> None:
    assert _authorize(tool=build_tool_policy(tool_fields(enabled=False))).reason == (
        "tool_disabled"
    )


def test_disabled_role_is_denied() -> None:
    decision = _authorize(policy=build_agent_policy(policy_fields(enabled=False)))
    assert decision.reason == "role_disabled"


def test_tool_absent_from_the_mandate_is_denied() -> None:
    unregistered = build_tool_policy(tool_fields(tool_name="research.run_edge_lab"))
    decision = _authorize(tool=unregistered)
    assert decision.reason == "tool_not_registered_by_mandate"


def test_mandate_granting_a_different_class_is_denied() -> None:
    mismatched = build_tool_policy(
        tool_fields(permission_class="compute_deterministic"),
    )
    assert _authorize(tool=mismatched).reason == "tool_not_registered_by_mandate"


def test_role_not_listed_as_eligible_is_denied() -> None:
    restricted = build_tool_policy(tool_fields(eligible_roles=("sentiment_analyst",)))
    assert _authorize(tool=restricted).reason == "role_not_eligible_for_tool"


def test_role_without_the_permission_class_is_denied() -> None:
    narrow = build_agent_policy(
        policy_fields(
            permission_classes=("compute_deterministic",),
            allowed_tools=(READ_TOOL,),
        ),
    )
    assert _authorize(policy=narrow).reason == "permission_class_not_held"


def test_tool_not_allowed_for_the_role_is_denied() -> None:
    narrow = build_agent_policy(policy_fields(allowed_tools=(COMPUTE_TOOL,)))
    assert _authorize(policy=narrow).reason == "tool_not_allowed_for_role"


def test_environment_mismatch_is_denied() -> None:
    decision = _authorize(request_scope={"environment": "demo"})
    assert decision.reason == "environment_mismatch"


def test_scope_mismatch_is_denied() -> None:
    decision = _authorize(
        request_scope={"environment": "sandbox", "asset_class": "equities"},
    )
    assert decision.reason == "scope_mismatch"


def test_exhausted_role_budget_is_denied() -> None:
    assert _authorize(calls_used=8).reason == "budget_exhausted"


def test_exhausted_tool_budget_is_denied() -> None:
    limited = build_tool_policy(tool_fields(max_calls_per_task=2))
    assert _authorize(tool=limited, calls_used=2).reason == "budget_exhausted"


def test_a_denied_decision_issues_no_grant() -> None:
    decision = _authorize(tool=build_tool_policy(tool_fields(enabled=False)))
    assert decision.allowed is False
    assert decision.grant_expires_at is None


# --------------------------------------------------------------------------
# FR-AGENTIC-014 - approval attestations
# --------------------------------------------------------------------------


def _approval_tool(**overrides: object):
    return build_tool_policy(
        tool_fields(
            tool_name=COMPUTE_TOOL,
            owning_feature="FEAT-AGT-12",
            permission_class="compute_deterministic",
            side_effect_class="deterministic_compute",
            requires_approval=True,
            **overrides,
        ),
    )


def _approval_attestation(**overrides: object):
    fields: dict[str, object] = {
        "tool_name": COMPUTE_TOOL,
        "permission_class": "compute_deterministic",
    }
    fields.update(overrides)
    return build_tool_approval_attestation(attestation_fields(**fields))


def test_missing_approval_is_denied_when_required() -> None:
    assert _authorize(tool=_approval_tool()).reason == "approval_required"


def test_valid_approval_is_accepted_once() -> None:
    store = build_in_memory_nonce_store()
    decision = _authorize(
        tool=_approval_tool(),
        attestation=_approval_attestation(),
        nonce_store=store,
    )
    assert decision.allowed is True


def test_replayed_approval_is_denied() -> None:
    store = build_in_memory_nonce_store()
    first = _authorize(
        tool=_approval_tool(),
        attestation=_approval_attestation(),
        nonce_store=store,
    )
    assert first.allowed is True
    second = _authorize(
        tool=_approval_tool(),
        attestation=_approval_attestation(),
        nonce_store=store,
    )
    assert second.reason == "approval_replayed"


def test_approval_without_single_use_enforcement_fails_closed() -> None:
    decision = _authorize(
        tool=_approval_tool(),
        attestation=_approval_attestation(),
        nonce_store=None,
    )
    assert decision.reason == "approval_replayed"


def test_expired_approval_is_denied() -> None:
    decision = _authorize(
        tool=_approval_tool(),
        attestation=_approval_attestation(),
        nonce_store=build_in_memory_nonce_store(),
        at_time=NOW + timedelta(hours=1),
    )
    assert decision.reason == "approval_expired"


def test_approval_for_a_different_object_is_denied() -> None:
    decision = _authorize(
        tool=_approval_tool(),
        attestation=_approval_attestation(object_hash=derive_object_hash({"x": "y"})),
        nonce_store=build_in_memory_nonce_store(),
    )
    assert decision.reason == "approval_object_mismatch"


def test_approval_for_a_different_tool_is_denied() -> None:
    decision = _authorize(
        tool=_approval_tool(),
        attestation=_approval_attestation(tool_name=READ_TOOL),
        nonce_store=build_in_memory_nonce_store(),
    )
    assert decision.reason == "approval_object_mismatch"


def test_approval_for_a_different_environment_is_denied() -> None:
    decision = _authorize(
        tool=_approval_tool(),
        attestation=_approval_attestation(environment="demo"),
        nonce_store=build_in_memory_nonce_store(),
    )
    assert decision.reason == "approval_scope_mismatch"


def test_self_approval_is_denied() -> None:
    decision = _authorize(
        tool=_approval_tool(),
        attestation=_approval_attestation(principal_id="agent-technical"),
        nonce_store=build_in_memory_nonce_store(),
        principal_id="agent-technical",
    )
    assert decision.reason == "self_approval"


def test_inverted_attestation_window_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_tool_approval_attestation(
            attestation_fields(issued_at=NOW + timedelta(hours=1), expires_at=NOW),
        )


def test_attestation_requires_a_real_object_digest() -> None:
    with pytest.raises(ValidationError):
        build_tool_approval_attestation(attestation_fields(object_hash="not-a-digest"))


def test_attestation_rejects_a_wildcard_scope() -> None:
    with pytest.raises(ValidationError):
        build_tool_approval_attestation(attestation_fields(scope={"account": "*"}))


# --------------------------------------------------------------------------
# FR-AGENTIC-015 - forbidden capabilities are unregistrable
# --------------------------------------------------------------------------


def test_forbidden_permission_classes_are_declared() -> None:
    assert get_forbidden_permission_classes() == ("controlled_mutation", "critical")


def test_broker_receiver_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_tool_policy(tool_fields(receiver_domain="brokers"))


@pytest.mark.parametrize(
    "operation",
    [
        "place_order",
        "cancel_order",
        "close_position",
        "clear_kill_switch",
        "override_mandate",
        "deploy",
    ],
)
def test_forbidden_operations_are_rejected(operation) -> None:
    with pytest.raises(ValidationError):
        build_tool_policy(tool_fields(public_operation=operation))


def test_forbidden_permission_class_is_unrepresentable() -> None:
    with pytest.raises(ValidationError):
        build_tool_policy(tool_fields(permission_class="controlled_mutation"))
    with pytest.raises(ValidationError):
        build_agent_policy(policy_fields(permission_classes=("critical",)))


def test_staging_write_must_require_approval() -> None:
    with pytest.raises(ValidationError):
        build_tool_policy(
            tool_fields(side_effect_class="staging_write", requires_approval=False),
        )


def test_proposal_submission_must_require_approval() -> None:
    with pytest.raises(ValidationError):
        build_tool_policy(
            tool_fields(
                side_effect_class="proposal_submission",
                requires_approval=False,
            ),
        )


def test_tool_scope_may_not_be_a_wildcard() -> None:
    with pytest.raises(ValidationError):
        build_tool_policy(tool_fields(scope={"environment": "*"}))


# --------------------------------------------------------------------------
# Registry validation
# --------------------------------------------------------------------------


def _registry(**overrides: object):
    mandate = overrides.pop("mandate", build_sandbox_mandate())
    tools = overrides.pop(
        "tools",
        (build_tool_policy(tool_fields()), build_tool_policy(compute_tool_fields())),
    )
    policies = overrides.pop("policies", (build_agent_policy(policy_fields()),))
    return validate_policy_registry(mandate, tools, policies)  # type: ignore[arg-type]


def test_registry_validates_a_consistent_configuration() -> None:
    tools, policies = _registry()
    assert set(tools) == {READ_TOOL, COMPUTE_TOOL}
    assert set(policies) == {TECHNICAL_ROLE_ID}


def test_duplicate_tool_identity_is_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate tool identity"):
        _registry(
            tools=(build_tool_policy(tool_fields()), build_tool_policy(tool_fields())),
        )


def test_duplicate_agent_policy_is_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate agent policy"):
        _registry(
            policies=(
                build_agent_policy(policy_fields()),
                build_agent_policy(policy_fields()),
            ),
        )


def test_tool_owned_by_a_disabled_feature_is_rejected() -> None:
    with pytest.raises(ValueError, match="does not enable"):
        _registry(tools=(build_tool_policy(tool_fields(owning_feature="FEAT-AGT-20")),))


def test_role_enabled_outside_the_mandate_is_rejected() -> None:
    with pytest.raises(ValueError, match="enabled outside the mandate"):
        _registry(policies=(build_agent_policy(policy_fields(role_id="ghost_role")),))


def test_policy_referencing_an_unregistered_tool_is_rejected() -> None:
    with pytest.raises(ValueError, match="unregistered tool"):
        _registry(tools=(build_tool_policy(tool_fields()),))


def test_mandate_tool_with_no_policy_is_rejected() -> None:
    with pytest.raises(ValueError, match="no policy"):
        _registry(
            tools=(build_tool_policy(tool_fields()),),
            policies=(build_agent_policy(policy_fields(allowed_tools=(READ_TOOL,))),),
        )
