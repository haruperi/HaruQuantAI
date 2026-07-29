"""Integration evidence for WF-AGT-012 - Tool permission grant and approval.

Exercises the documented workflow across governance and permissions: an agent
requests a registered tool for a bounded task scope, the mandate and roster
authority are checked, an approval-gated tool requires explicit human approval,
a scoped time-bounded grant is issued, and the grant is enforced at each
invocation rather than only at issue.

A grant never confers receiver-domain authorization: an unregistered tool is
refused without invocation, and no grant can be escalated into a trade, an
activation, or a registration.
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
    get_role_registry,
    resolve_role_manifest,
    validate_policy_registry,
)

from tests.agentic.fixtures import (
    COMPUTE_TOOL,
    NOW,
    READ_TOOL,
    TECHNICAL_ROLE_ID,
    build_sandbox_mandate,
    build_technical_manifest,
)

OBJECT_HASH = derive_object_hash({"symbol": "EURUSD", "timeframe": "H1"})
SCOPE = {"environment": "sandbox", "asset_class": "fx"}


def _read_tool(**overrides: object):
    fields: dict[str, object] = {
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
        "scope": dict(SCOPE),
        "idempotent": True,
        "requires_approval": False,
        "max_input_bytes": 8_192,
        "max_output_bytes": 1_048_576,
        "timeout_seconds": 30,
        "max_calls_per_task": 4,
        "enabled": True,
    }
    fields.update(overrides)
    return build_tool_policy(fields)


def _compute_tool(**overrides: object):
    fields: dict[str, object] = {
        "tool_name": COMPUTE_TOOL,
        "owning_feature": "FEAT-AGT-12",
        "receiver_domain": "indicators",
        "public_operation": "validate_indicator",
        "permission_class": "compute_deterministic",
        "side_effect_class": "deterministic_compute",
        "requires_approval": True,
    }
    fields.update(overrides)
    return _read_tool(**fields)


def _policy(**overrides: object):
    fields: dict[str, object] = {
        "role_id": TECHNICAL_ROLE_ID,
        "role_version": "1.0.0",
        "permission_classes": ("read_evidence", "compute_deterministic"),
        "allowed_tools": (READ_TOOL, COMPUTE_TOOL),
        "environment": "sandbox",
        "max_tool_calls": 4,
        "max_cost": Decimal("2.50"),
        "enabled": True,
    }
    fields.update(overrides)
    return build_agent_policy(fields)


def _attestation(**overrides: object):
    fields: dict[str, object] = {
        "attestation_id": "att-integration",
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
        "nonce": "nonce-integration",
        "policy_version": "1.0.0",
        "signature": "owner-signature",
    }
    fields.update(overrides)
    return build_tool_approval_attestation(fields)


def test_wf_agt_012_grant_flows_from_registry_through_approval() -> None:
    # 1. The tool is resolved in the validated registries.
    mandate = build_sandbox_mandate(enabled_roles=(TECHNICAL_ROLE_ID,))
    registry = get_role_registry(mandate, (build_technical_manifest(),), NOW)
    manifest = resolve_role_manifest(registry, TECHNICAL_ROLE_ID)
    assert READ_TOOL in manifest.tools

    tools, policies = validate_policy_registry(
        mandate,
        (_read_tool(), _compute_tool()),
        (_policy(),),
    )
    assert set(tools) == {READ_TOOL, COMPUTE_TOOL}
    policy = policies[TECHNICAL_ROLE_ID]

    # 2. A read tool needing no approval issues a scoped time-bounded grant.
    read = authorize_tool_call(
        mandate,
        policy,
        tools[READ_TOOL],
        "agent-technical",
        OBJECT_HASH,
        request_scope=dict(SCOPE),
        at_time=NOW,
    )
    assert read.allowed is True
    assert read.grant_expires_at == NOW + timedelta(seconds=30)

    # 3. An approval-gated tool is refused without explicit human approval.
    store = build_in_memory_nonce_store()
    unapproved = authorize_tool_call(
        mandate,
        policy,
        tools[COMPUTE_TOOL],
        "agent-technical",
        OBJECT_HASH,
        request_scope=dict(SCOPE),
        nonce_store=store,
        at_time=NOW,
    )
    assert unapproved.allowed is False
    assert unapproved.reason == "approval_required"

    # 4. With an authenticated approval it is granted exactly once.
    approved = authorize_tool_call(
        mandate,
        policy,
        tools[COMPUTE_TOOL],
        "agent-technical",
        OBJECT_HASH,
        request_scope=dict(SCOPE),
        attestation=_attestation(),
        nonce_store=store,
        at_time=NOW,
    )
    assert approved.allowed is True

    # 5. The grant is enforced at each invocation, not only at issue.
    replayed = authorize_tool_call(
        mandate,
        policy,
        tools[COMPUTE_TOOL],
        "agent-technical",
        OBJECT_HASH,
        request_scope=dict(SCOPE),
        attestation=_attestation(),
        nonce_store=store,
        at_time=NOW,
    )
    assert replayed.allowed is False
    assert replayed.reason == "approval_replayed"


def test_wf_agt_012_unregistered_tool_is_refused_without_invocation() -> None:
    mandate = build_sandbox_mandate(enabled_roles=(TECHNICAL_ROLE_ID,))
    _, policies = validate_policy_registry(
        mandate,
        (_read_tool(), _compute_tool()),
        (_policy(),),
    )
    ghost = _read_tool(tool_name="research.run_edge_lab")
    decision = authorize_tool_call(
        mandate,
        policies[TECHNICAL_ROLE_ID],
        ghost,
        "agent-technical",
        OBJECT_HASH,
        request_scope=dict(SCOPE),
        at_time=NOW,
    )
    assert decision.allowed is False
    assert decision.reason == "tool_not_registered_by_mandate"


def test_wf_agt_012_no_grant_can_describe_a_consequential_capability() -> None:
    # The escalation path is closed at registration, not at call time: a tool
    # naming an order, kill switch, deployment, or broker cannot be built.
    for override in (
        {"public_operation": "place_order"},
        {"public_operation": "clear_kill_switch"},
        {"public_operation": "deploy"},
        {"receiver_domain": "brokers"},
        {"permission_class": "controlled_mutation"},
    ):
        with pytest.raises(Exception, match=r".+"):
            _read_tool(**override)


def test_wf_agt_012_registry_rejects_a_role_exceeding_its_mandate() -> None:
    mandate = build_sandbox_mandate(enabled_roles=(TECHNICAL_ROLE_ID,))
    escalating = _policy(role_id="ghost_role")
    with pytest.raises(ValueError, match="enabled outside the mandate"):
        validate_policy_registry(
            mandate,
            (_read_tool(), _compute_tool()),
            (escalating,),
        )
