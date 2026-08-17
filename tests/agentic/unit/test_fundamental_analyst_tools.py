"""Unit tests for agentic market intelligence fundamental analyst tools and permission registry."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from app.agentic.agents.experimentation.experiment_designer.runtime import (
    _encode,
)
from app.agentic.agents.market_intelligence.fundamental_analyst.tools import (
    build_fundamental_evidence_port,
    call_intelligence_tool,
    get_registered_tool_names,
    parse_coverage,
    verify_coverage,
    verify_projection,
)
from app.agentic.permissions.registry import (
    _validate_policy_against_mandate,
    _validate_tool_against_mandate,
    get_forbidden_permission_classes,
)


def test_agentic_fundamental_tools_branches() -> None:
    """Verify verify_projection, parse_coverage, and verify_coverage edge cases."""
    proj_missing = {"asset_scope": "US"}
    err = verify_projection(proj_missing)
    assert err is not None
    assert "the fundamental projection omits:" in err

    proj_full = {
        "asset_scope": "US",
        "canonical_hash": "hash123",
        "coverage": "filing=2, macro=0",
        "document_references": "doc1",
    }
    assert verify_projection(proj_full) is None

    counts = parse_coverage(proj_full)
    assert counts == {"filing": 2, "macro": 0}

    assert (
        verify_coverage(proj_full, ())
        == "a fundamental reading must declare the coverage it requires"
    )
    assert verify_coverage(proj_full, ("filing",)) is None
    cov_err = verify_coverage(proj_full, ("macro",))
    assert cov_err is not None
    assert "the projection covers no macro evidence" in cov_err

    mock_evidence = MagicMock()
    mock_evidence.assess_applicability.return_value = {"applicable": "true"}
    mock_evidence.get_fundamental_projection.return_value = proj_full

    port = build_fundamental_evidence_port(mock_evidence)
    assert port.assess_applicability("equity", "issuer") == {"applicable": "true"}
    assert (
        port.get_fundamental_projection(
            "AAPL", "equity", "issuer", ("filing",), "2026-01-01"
        )
        == proj_full
    )

    tool_names = get_registered_tool_names()
    assert len(tool_names) == 2


def test_call_intelligence_tool_audit_hook() -> None:
    """Verify call_intelligence_tool audit_hook callback execution."""
    mandate = MagicMock()
    policy = MagicMock()
    policy.role_id = "role-1"
    tool = MagicMock()
    principal_id = "user-1"
    task_id = "task-1"
    request_scope = {"env": "sandbox"}
    at_time = datetime.now(UTC)
    mock_audit = MagicMock()

    receiver_call = lambda: {"result": "ok"}  # noqa: E731

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "app.agentic.agents.market_intelligence.fundamental_analyst.tools.call_governed_tool",
            lambda *_args, **kw: kw["audit_hook"]("tool.name", "COMPLETED"),
        )

        call_intelligence_tool(
            mandate,
            policy,
            tool,
            principal_id,
            task_id,
            request_scope,
            receiver_call,
            at_time,
            audit_store=mock_audit,
        )
    assert mock_audit is not None


def test_permissions_registry_validation_branches() -> None:
    """Verify registry validation exception cases."""
    assert len(get_forbidden_permission_classes()) > 0

    tool = MagicMock()
    tool.tool_name = "test_tool"
    tool.permission_class = "READ_ONLY"
    tool.owning_feature = "FEAT-1"

    mandate = MagicMock()
    mandate.tool_scopes = {}
    mandate.enabled_features = {"FEAT-1"}

    with pytest.raises(
        ValueError, match="tool test_tool is not registered by the mandate"
    ):
        _validate_tool_against_mandate(tool, mandate)

    mandate.tool_scopes = {"test_tool": "controlled_mutation"}
    with pytest.raises(ValueError, match="is granted forbidden class"):
        _validate_tool_against_mandate(tool, mandate)

    mandate.tool_scopes = {"test_tool": "WRITE_ONLY"}
    with pytest.raises(ValueError, match="mandate grants WRITE_ONLY"):
        _validate_tool_against_mandate(tool, mandate)

    mandate.tool_scopes = {"test_tool": "READ_ONLY"}
    mandate.enabled_features = set()
    with pytest.raises(ValueError, match="mandate does not enable"):
        _validate_tool_against_mandate(tool, mandate)

    policy = MagicMock()
    policy.enabled = True
    policy.role_id = "role-1"
    policy.permission_classes = ("READ_ONLY",)
    policy.allowed_tools = ("test_tool",)
    policy.environment = "sandbox"

    mandate.enabled_roles = set()
    tools = {}
    with pytest.raises(ValueError, match="role role-1 is enabled outside the mandate"):
        _validate_policy_against_mandate(policy, mandate, tools)

    mandate.enabled_roles = {"role-1"}
    policy.permission_classes = ("controlled_mutation",)
    with pytest.raises(ValueError, match="holds forbidden class"):
        _validate_policy_against_mandate(policy, mandate, tools)

    policy.permission_classes = ("READ_ONLY",)
    with pytest.raises(ValueError, match="allows unregistered tool"):
        _validate_policy_against_mandate(policy, mandate, tools)


def test_durable_experiment_store_encode() -> None:
    """Verify _encode error on non-BaseModel input."""
    with pytest.raises(
        TypeError, match="Agentic experiment state must be a validated model"
    ):
        _encode({"not": "a model"})
