"""Unit tests for Hosted Workspace Boundary capability implementation."""

from __future__ import annotations

import uuid

import pytest
from app.contracts.workspace.errors import WorkspaceFailure
from app.contracts.workspace.models import (
    HostedWorkspaceContext,
    HostWorkspacesRequest,
    PrincipalRef,
)
from app.services.workspace.hosted_workspace.config import HostedWorkspaceConfig
from app.services.workspace.hosted_workspace.hosted_workspace import (
    HostedWorkspaceService,
    fr_ws_authorize_hosted_workspaces,
    fr_ws_isolate_hosted_workspaces,
)


@pytest.mark.asyncio
async def test_ws_isolate_hosted_workspaces() -> None:
    """Test FR-WS-ISOLATE_HOSTED_WORKSPACES: provision, describe, and collision."""
    service = HostedWorkspaceService()

    # 1. Successful provision
    ws1_id = str(uuid.uuid7())
    ctx1 = HostedWorkspaceContext(
        workspace_id=ws1_id,
        deployment_mode="HOSTED",
        metadata_scope=f"meta-{ws1_id}",
        artifact_scope=f"art-{ws1_id}",
        queue_scope=f"queue-{ws1_id}",
        credential_scope=f"cred-{ws1_id}",
        quota_scope=f"quota-{ws1_id}",
        plugin_permission_scope=f"plugin-{ws1_id}",
    )
    res1 = await fr_ws_isolate_hosted_workspaces(service, ctx1)
    assert res1.workspace_id == ws1_id
    assert res1.metadata_scope == ctx1.metadata_scope
    assert res1.artifact_scope == ctx1.artifact_scope

    # 2. Successful describe
    desc1 = await fr_ws_isolate_hosted_workspaces(service, ws1_id)
    assert desc1.workspace_id == ws1_id
    assert desc1 == ctx1

    # 3. Describe non-existent workspace -> failure
    missing_ws_id = str(uuid.uuid7())
    with pytest.raises(RuntimeError, match=r"\[WORKSPACE_NOT_FOUND\]"):
        await fr_ws_isolate_hosted_workspaces(service, missing_ws_id)

    # 4. Collision testing on all 6 scopes
    scope_fields = (
        "metadata_scope",
        "artifact_scope",
        "queue_scope",
        "credential_scope",
        "quota_scope",
        "plugin_permission_scope",
    )
    for field_name in scope_fields:
        colliding_ws_id = str(uuid.uuid7())
        scope_kwargs = {
            "metadata_scope": f"meta-{colliding_ws_id}",
            "artifact_scope": f"art-{colliding_ws_id}",
            "queue_scope": f"queue-{colliding_ws_id}",
            "credential_scope": f"cred-{colliding_ws_id}",
            "quota_scope": f"quota-{colliding_ws_id}",
            "plugin_permission_scope": f"plugin-{colliding_ws_id}",
        }
        # Force one scope to collide with ctx1
        scope_kwargs[field_name] = getattr(ctx1, field_name)

        colliding_ctx = HostedWorkspaceContext(
            workspace_id=colliding_ws_id,
            deployment_mode="HOSTED",
            metadata_scope=scope_kwargs["metadata_scope"],
            artifact_scope=scope_kwargs["artifact_scope"],
            queue_scope=scope_kwargs["queue_scope"],
            credential_scope=scope_kwargs["credential_scope"],
            quota_scope=scope_kwargs["quota_scope"],
            plugin_permission_scope=scope_kwargs["plugin_permission_scope"],
        )
        req = HostWorkspacesRequest(
            request_id=str(uuid.uuid7()),
            capability_snapshot_id=str(uuid.uuid7()),
            operation="PROVISION",
            context=colliding_ctx,
        )
        res = await service.host_workspaces(req)
        assert isinstance(res, WorkspaceFailure)
        assert res.code == "ISOLATION_CONFLICT"
        assert res.problem.status == 409
        assert field_name in res.problem.detail

    # 5. Disable scope isolation and confirm collision bypass
    permissive_service = HostedWorkspaceService(
        config=HostedWorkspaceConfig(enforce_scope_isolation=False)
    )
    await fr_ws_isolate_hosted_workspaces(permissive_service, ctx1)
    ws_dup_id = str(uuid.uuid7())
    ctx_dup = HostedWorkspaceContext(
        workspace_id=ws_dup_id,
        deployment_mode="HOSTED",
        metadata_scope=ctx1.metadata_scope,
        artifact_scope=ctx1.artifact_scope,
        queue_scope=ctx1.queue_scope,
        credential_scope=ctx1.credential_scope,
        quota_scope=ctx1.quota_scope,
        plugin_permission_scope=ctx1.plugin_permission_scope,
    )
    res_dup = await fr_ws_isolate_hosted_workspaces(permissive_service, ctx_dup)
    assert res_dup.workspace_id == ws_dup_id


@pytest.mark.asyncio
async def test_ws_authorize_hosted_workspaces() -> None:
    """Test FR-WS-AUTHORIZE_HOSTED_WORKSPACES: allow, deny, wildcard, and revocation."""
    service = HostedWorkspaceService()

    ws_id = str(uuid.uuid7())
    ctx = HostedWorkspaceContext(
        workspace_id=ws_id,
        deployment_mode="HOSTED",
        metadata_scope=f"meta-{ws_id}",
        artifact_scope=f"art-{ws_id}",
        queue_scope=f"queue-{ws_id}",
        credential_scope=f"cred-{ws_id}",
        quota_scope=f"quota-{ws_id}",
        plugin_permission_scope=f"plugin-{ws_id}",
    )
    await fr_ws_isolate_hosted_workspaces(service, ctx)

    p1 = PrincipalRef(
        principal_id=str(uuid.uuid7()),
        auth_provider="jwt-bearer",
    )

    # 1. No grant -> DENY with reason
    dec_deny = await fr_ws_authorize_hosted_workspaces(
        service, ws_id, p1, "workspace.read"
    )
    assert dec_deny.outcome == "DENY"
    assert "lacks permission 'workspace.read'" in dec_deny.reason
    assert dec_deny.expires_at is None

    # 2. Grant exact action -> ALLOW with empty reason
    service.grant_permission(ws_id, p1.principal_id, "workspace.read")
    dec_allow = await fr_ws_authorize_hosted_workspaces(
        service, ws_id, p1, "workspace.read"
    )
    assert dec_allow.outcome == "ALLOW"
    assert dec_allow.reason == ""
    assert dec_allow.expires_at is not None

    # 3. Unauthorized other action -> DENY
    dec_unauth = await fr_ws_authorize_hosted_workspaces(
        service, ws_id, p1, "workspace.write"
    )
    assert dec_unauth.outcome == "DENY"
    assert "lacks permission 'workspace.write'" in dec_unauth.reason

    # 4. Revoke grant -> DENY
    service.revoke_permission(ws_id, p1.principal_id, "workspace.read")
    dec_revoked = await fr_ws_authorize_hosted_workspaces(
        service, ws_id, p1, "workspace.read"
    )
    assert dec_revoked.outcome == "DENY"

    # 5. Wildcard grant -> ALLOW
    service.grant_permission(ws_id, p1.principal_id, "*")
    dec_wild = await fr_ws_authorize_hosted_workspaces(
        service, ws_id, p1, "workspace.admin"
    )
    assert dec_wild.outcome == "ALLOW"
    assert dec_wild.reason == ""

    # 6. Unprovisioned workspace -> DENY
    unknown_ws = str(uuid.uuid7())
    dec_unknown_ws = await fr_ws_authorize_hosted_workspaces(
        service, unknown_ws, p1, "workspace.read"
    )
    assert dec_unknown_ws.outcome == "DENY"
    assert "not provisioned or unknown" in dec_unknown_ws.reason
