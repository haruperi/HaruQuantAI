"""Integration tests for Hosted Workspace Boundary lifecycle and cross-workspace isolation."""

from __future__ import annotations

import uuid

import pytest
from app.contracts.workspace.models import (
    HostedWorkspaceContext,
    PrincipalRef,
)
from app.services.workspace.hosted_workspace.hosted_workspace import (
    HostedWorkspaceService,
    fr_ws_authorize_hosted_workspaces,
    fr_ws_isolate_hosted_workspaces,
)


@pytest.mark.asyncio
async def test_hosted_workspace_end_to_end_lifecycle() -> None:
    """Verify multi-workspace provisioning, describe, cross-workspace isolation, and authorization."""
    service = HostedWorkspaceService()

    # 1. Provision two independent hosted workspaces
    ws1_id = str(uuid.uuid7())
    ctx1 = HostedWorkspaceContext(
        workspace_id=ws1_id,
        deployment_mode="HOSTED",
        metadata_scope=f"meta-ws1-{ws1_id}",
        artifact_scope=f"art-ws1-{ws1_id}",
        queue_scope=f"queue-ws1-{ws1_id}",
        credential_scope=f"cred-ws1-{ws1_id}",
        quota_scope=f"quota-ws1-{ws1_id}",
        plugin_permission_scope=f"plugin-ws1-{ws1_id}",
    )
    p1_res = await fr_ws_isolate_hosted_workspaces(service, ctx1)
    assert p1_res.workspace_id == ws1_id

    ws2_id = str(uuid.uuid7())
    ctx2 = HostedWorkspaceContext(
        workspace_id=ws2_id,
        deployment_mode="HOSTED",
        metadata_scope=f"meta-ws2-{ws2_id}",
        artifact_scope=f"art-ws2-{ws2_id}",
        queue_scope=f"queue-ws2-{ws2_id}",
        credential_scope=f"cred-ws2-{ws2_id}",
        quota_scope=f"quota-ws2-{ws2_id}",
        plugin_permission_scope=f"plugin-ws2-{ws2_id}",
    )
    p2_res = await fr_ws_isolate_hosted_workspaces(service, ctx2)
    assert p2_res.workspace_id == ws2_id

    # 2. Verify describe retrieves correct isolated context for each
    desc1 = await fr_ws_isolate_hosted_workspaces(service, ws1_id)
    desc2 = await fr_ws_isolate_hosted_workspaces(service, ws2_id)
    assert desc1.metadata_scope == ctx1.metadata_scope
    assert desc2.metadata_scope == ctx2.metadata_scope
    assert desc1.metadata_scope != desc2.metadata_scope

    # 3. Setup distinct principals and verify workspace authorization isolation
    tenant_admin = PrincipalRef(
        principal_id=str(uuid.uuid7()),
        auth_provider="enterprise-sso",
    )
    researcher = PrincipalRef(
        principal_id=str(uuid.uuid7()),
        auth_provider="enterprise-sso",
    )

    # Grant tenant_admin full permissions on ws1 only
    service.grant_permission(ws1_id, tenant_admin.principal_id, "*")
    # Grant researcher read on ws2 only
    service.grant_permission(ws2_id, researcher.principal_id, "workspace.read")

    # tenant_admin on ws1 -> ALLOW
    dec1 = await fr_ws_authorize_hosted_workspaces(
        service, ws1_id, tenant_admin, "workspace.delete"
    )
    assert dec1.outcome == "ALLOW"

    # tenant_admin on ws2 (no grant on ws2) -> DENY (cross-workspace isolation)
    dec2 = await fr_ws_authorize_hosted_workspaces(
        service, ws2_id, tenant_admin, "workspace.delete"
    )
    assert dec2.outcome == "DENY"

    # researcher on ws2 read -> ALLOW
    dec3 = await fr_ws_authorize_hosted_workspaces(
        service, ws2_id, researcher, "workspace.read"
    )
    assert dec3.outcome == "ALLOW"

    # researcher on ws2 write -> DENY
    dec4 = await fr_ws_authorize_hosted_workspaces(
        service, ws2_id, researcher, "workspace.write"
    )
    assert dec4.outcome == "DENY"

    # researcher on ws1 read -> DENY
    dec5 = await fr_ws_authorize_hosted_workspaces(
        service, ws1_id, researcher, "workspace.read"
    )
    assert dec5.outcome == "DENY"
