"""Unit tests for Hosted Workspace Boundary manifest."""

from app.contracts.workspace.capabilities import HOST_WORKSPACES_CAPABILITY
from app.services.workspace.hosted_workspace.manifest import SPEC


def test_manifest_specification_invariants() -> None:
    """Verify SPEC fields and capability declaration."""
    assert SPEC.feature_id == "FEAT-WS-HOST_WORKSPACES"
    assert SPEC.domain == "workspace"
    assert HOST_WORKSPACES_CAPABILITY in SPEC.provides
    assert len(SPEC.provides) == 1
    assert len(SPEC.requires) == 0
    assert len(SPEC.conflicts) == 0
    assert SPEC.state is None
