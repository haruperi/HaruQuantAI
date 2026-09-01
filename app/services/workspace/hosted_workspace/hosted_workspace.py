"""Hosted Workspace Boundary domain logic and capability implementation.

Purpose:
    Isolate hosted workspaces and authorize principals.

Key capabilities:
    * Provision and describe hosted workspace contexts with isolated scopes.
    * Enforce strict cross-workspace uniqueness for all six scope kinds.
    * Evaluate pluggable, fail-closed principal authorization for hosted actions.

Python API usage:
    from app.services.workspace.hosted_workspace.hosted_workspace import (
        HostedWorkspaceService,
    )
    service = HostedWorkspaceService()
    result = await service.host_workspaces(request)

CLI usage:
    uv run python -m app.services.workspace.hosted_workspace.hosted_workspace
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import override

from app.contracts.common.models import ProblemDetails, Uuid7
from app.contracts.workspace.errors import WorkspaceFailure, WorkspaceFailureCode
from app.contracts.workspace.models import (
    HostedWorkspaceContext,
    HostWorkspacesRequest,
    HostWorkspacesSuccess,
    PrincipalRef,
    WorkspaceAuthorizationDecision,
)
from app.contracts.workspace.ports import HostWorkspacesCapability
from app.services.workspace.hosted_workspace.config import HostedWorkspaceConfig

logger = logging.getLogger(__name__)


def _now_utc() -> str:
    """Return current UTC timestamp in ISO 8601 microseconds format.

    Returns:
        Current UTC timestamp formatted as ISO 8601 string.
    """
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _add_seconds_utc(iso_ts: str, seconds: int) -> str:
    """Add seconds to an ISO 8601 UTC timestamp.

    Args:
        iso_ts: Source timestamp ISO string.
        seconds: Number of seconds to add.

    Returns:
        Updated ISO 8601 UTC timestamp string.
    """
    dt = datetime.fromisoformat(iso_ts)
    return (dt + timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _make_failure(
    request_id: Uuid7,
    code: WorkspaceFailureCode,
    status: int,
    title: str,
    detail: str,
) -> WorkspaceFailure:
    """Construct a standard WorkspaceFailure envelope with ProblemDetails.

    Args:
        request_id: Request UUID identifier.
        code: Machine-readable failure code.
        status: HTTP-aligned integer status code.
        title: Short human-readable summary.
        detail: Detailed explanation of the failure.

    Returns:
        Populated WorkspaceFailure model instance.
    """
    error_slug = code.lower().replace("_", "-")
    return WorkspaceFailure(
        request_id=request_id,
        code=code,
        problem=ProblemDetails(
            type=f"urn:haruquantai:workspace:{error_slug}",
            title=title,
            status=status,
            code=code,
            detail=detail,
            request_id=request_id,
        ),
    )


class HostedWorkspaceService(HostWorkspacesCapability):
    """Domain service implementing the HostWorkspacesCapability protocol.

    Provides multi-workspace isolation validation and fail-closed principal
    authorization for hosted deployments.
    """

    def __init__(self, config: HostedWorkspaceConfig | None = None) -> None:
        """Initialize the hosted workspace service.

        Args:
            config: Optional configuration settings.
        """
        self._config = config or HostedWorkspaceConfig()
        self._contexts: dict[str, HostedWorkspaceContext] = {}
        self._grants: dict[tuple[str, str], set[str]] = {}
        self._lock = asyncio.Lock()

    def grant_permission(
        self,
        workspace_id: str,
        principal_id: str,
        action: str,
    ) -> None:
        """Grant an authorized action to a principal on a workspace.

        Args:
            workspace_id: Target workspace UUID string.
            principal_id: Principal UUID string.
            action: Action permission name (e.g. 'workspace.read' or '*').
        """
        key = (workspace_id, principal_id)
        if key not in self._grants:
            self._grants[key] = set()
        self._grants[key].add(action)

    def revoke_permission(
        self,
        workspace_id: str,
        principal_id: str,
        action: str,
    ) -> None:
        """Revoke an authorized action from a principal on a workspace.

        Args:
            workspace_id: Target workspace UUID string.
            principal_id: Principal UUID string.
            action: Action permission name to remove.
        """
        key = (workspace_id, principal_id)
        if key in self._grants:
            self._grants[key].discard(action)

    @override
    async def host_workspaces(
        self,
        request: HostWorkspacesRequest,
    ) -> HostWorkspacesSuccess | WorkspaceFailure:
        """Provision, describe, and authorize isolated hosted workspaces.

        Args:
            request: Operation-discriminated hosted workspace request.

        Returns:
            Success envelope containing context or authorization decision,
            or a structured failure envelope.
        """
        match request.operation:
            case "PROVISION":
                return await self._handle_provision(request)
            case "DESCRIBE":
                return await self._handle_describe(request)
            case "AUTHORIZE":
                return await self._handle_authorize(request)

    async def _handle_provision(
        self,
        request: HostWorkspacesRequest,
    ) -> HostWorkspacesSuccess | WorkspaceFailure:
        """Handle PROVISION to register an isolated hosted workspace context.

        Args:
            request: Validated PROVISION request with context.

        Returns:
            Success result with context or WorkspaceFailure on conflict.
        """
        context = request.context
        if context is None:
            return _make_failure(
                request.request_id,
                "WORKSPACE_VALIDATION_FAILED",
                400,
                "Missing Context",
                "PROVISION operation requires a valid HostedWorkspaceContext.",
            )

        ws_id = str(context.workspace_id)
        async with self._lock:
            if self._config.enforce_scope_isolation:
                collision_err = self._check_scope_collisions(ws_id, context)
                if collision_err is not None:
                    scope_kind, colliding_value, existing_ws = collision_err
                    detail = (
                        f"Scope collision on {scope_kind}='{colliding_value}': "
                        f"already assigned to workspace '{existing_ws}'."
                    )
                    return _make_failure(
                        request.request_id,
                        "ISOLATION_CONFLICT",
                        409,
                        "Isolation Conflict",
                        detail,
                    )

            self._contexts[ws_id] = context
            logger.info("Provisioned hosted workspace %s", ws_id)
            return HostWorkspacesSuccess(
                request_id=request.request_id,
                context=context,
            )

    def _check_scope_collisions(
        self,
        ws_id: str,
        context: HostedWorkspaceContext,
    ) -> tuple[str, str, str] | None:
        """Check if any scope in context is already used by another workspace.

        Args:
            ws_id: Workspace UUID string.
            context: Candidate HostedWorkspaceContext.

        Returns:
            Tuple of (scope_kind, colliding_value, existing_workspace_id) or None.
        """
        scope_checks = (
            ("metadata_scope", context.metadata_scope),
            ("artifact_scope", context.artifact_scope),
            ("queue_scope", context.queue_scope),
            ("credential_scope", context.credential_scope),
            ("quota_scope", context.quota_scope),
            ("plugin_permission_scope", context.plugin_permission_scope),
        )
        for existing_id, existing_ctx in self._contexts.items():
            if existing_id == ws_id:
                continue
            for scope_name, scope_val in scope_checks:
                if getattr(existing_ctx, scope_name) == scope_val:
                    return scope_name, scope_val, existing_id
        return None

    async def _handle_describe(
        self,
        request: HostWorkspacesRequest,
    ) -> HostWorkspacesSuccess | WorkspaceFailure:
        """Handle DESCRIBE to retrieve an existing hosted workspace context.

        Args:
            request: Validated DESCRIBE request with workspace_id.

        Returns:
            Success result with context or WorkspaceFailure.
        """
        ws_id = str(request.workspace_id)
        async with self._lock:
            context = self._contexts.get(ws_id)
            if context is None:
                return _make_failure(
                    request.request_id,
                    "WORKSPACE_NOT_FOUND",
                    404,
                    "Workspace Not Found",
                    f"Hosted workspace '{ws_id}' not found.",
                )
            return HostWorkspacesSuccess(
                request_id=request.request_id,
                context=context,
            )

    async def _handle_authorize(
        self,
        request: HostWorkspacesRequest,
    ) -> HostWorkspacesSuccess | WorkspaceFailure:
        """Handle AUTHORIZE operation with fail-closed policy evaluation.

        Args:
            request: Validated AUTHORIZE request with workspace_id, principal, action.

        Returns:
            HostWorkspacesSuccess with WorkspaceAuthorizationDecision (ALLOW or DENY).
        """
        ws_id = str(request.workspace_id)
        principal = request.principal
        action = str(request.action)
        now_ts = _now_utc()

        if principal is None:
            return _make_failure(
                request.request_id,
                "WORKSPACE_VALIDATION_FAILED",
                400,
                "Missing Principal",
                "AUTHORIZE operation requires a valid PrincipalRef.",
            )

        async with self._lock:
            # Policy evaluation: fail closed
            if ws_id not in self._contexts:
                outcome = "DENY"
                reason = f"Hosted workspace '{ws_id}' is not provisioned or unknown."
            else:
                grants = self._grants.get((ws_id, str(principal.principal_id)), set())
                if action in grants or "*" in grants:
                    outcome = "ALLOW"
                    reason = ""
                else:
                    outcome = "DENY"
                    reason = (
                        f"Principal '{principal.principal_id}' lacks permission "
                        f"'{action}' on workspace '{ws_id}'."
                    )

            expires_at = (
                _add_seconds_utc(now_ts, self._config.default_decision_ttl_seconds)
                if outcome == "ALLOW"
                else None
            )

            decision = WorkspaceAuthorizationDecision(
                decision_id=str(uuid.uuid7()),
                principal=principal,
                workspace_id=request.workspace_id,  # type: ignore[arg-type]
                action=action,
                outcome=outcome,  # type: ignore[arg-type]
                reason=reason,
                decided_at=now_ts,
                expires_at=expires_at,
            )
            return HostWorkspacesSuccess(
                request_id=request.request_id,
                decision=decision,
            )


# ============================================================================
# Functional Requirement Trace Functions
# ============================================================================


async def fr_ws_isolate_hosted_workspaces(
    service: HostedWorkspaceService,
    target: HostedWorkspaceContext | str,
) -> HostedWorkspaceContext:
    """Implementation trace for FR-WS-ISOLATE_HOSTED_WORKSPACES.

    Provisions or describes an isolated hosted workspace context.

    Args:
        service: HostedWorkspaceService instance.
        target: HostedWorkspaceContext to provision, or workspace ID to describe.

    Returns:
        The provisioned or retrieved HostedWorkspaceContext.

    Raises:
        RuntimeError: If provisioning or describing fails.
    """
    req_id = str(uuid.uuid7())
    snap_id = str(uuid.uuid7())

    if isinstance(target, HostedWorkspaceContext):
        request = HostWorkspacesRequest(
            request_id=req_id,
            capability_snapshot_id=snap_id,
            operation="PROVISION",
            context=target,
        )
    else:
        request = HostWorkspacesRequest(
            request_id=req_id,
            capability_snapshot_id=snap_id,
            operation="DESCRIBE",
            workspace_id=target,
        )

    result = await service.host_workspaces(request)
    match result:
        case WorkspaceFailure():
            msg = (
                f"FR-WS-ISOLATE_HOSTED_WORKSPACES failed: "
                f"[{result.code}] {result.problem.detail}"
            )
            raise RuntimeError(msg)
        case HostWorkspacesSuccess():
            if result.context is None:
                msg = (
                    "FR-WS-ISOLATE_HOSTED_WORKSPACES failed: "
                    "no context in success response"
                )
                raise RuntimeError(msg)
            return result.context


async def fr_ws_authorize_hosted_workspaces(
    service: HostedWorkspaceService,
    workspace_id: str,
    principal: PrincipalRef,
    action: str,
) -> WorkspaceAuthorizationDecision:
    """Implementation trace for FR-WS-AUTHORIZE_HOSTED_WORKSPACES.

    Authorizes an authenticated principal for an action on a hosted workspace.

    Args:
        service: HostedWorkspaceService instance.
        workspace_id: Target workspace UUID string.
        principal: Authenticated principal reference.
        action: Requested action string.

    Returns:
        WorkspaceAuthorizationDecision with ALLOW or fail-closed DENY.

    Raises:
        RuntimeError: If authorization processing fails unexpectedly.
    """
    req_id = str(uuid.uuid7())
    snap_id = str(uuid.uuid7())
    request = HostWorkspacesRequest(
        request_id=req_id,
        capability_snapshot_id=snap_id,
        operation="AUTHORIZE",
        workspace_id=workspace_id,
        principal=principal,
        action=action,
    )
    result = await service.host_workspaces(request)
    match result:
        case WorkspaceFailure():
            msg = (
                f"FR-WS-AUTHORIZE_HOSTED_WORKSPACES failed: "
                f"[{result.code}] {result.problem.detail}"
            )
            raise RuntimeError(msg)
        case HostWorkspacesSuccess():
            if result.decision is None:
                msg = (
                    "FR-WS-AUTHORIZE_HOSTED_WORKSPACES failed: "
                    "no decision in success response"
                )
                raise RuntimeError(msg)
            return result.decision


# ============================================================================
# Executable Teaching and Usage Harness
# ============================================================================


async def _async_run_scenarios() -> None:
    """Run requirement-driven scenarios as an executable teaching harness.

    Raises:
        RuntimeError: If any scenario expectation fails.
    """
    print("=== FEAT-WS-HOST_WORKSPACES Executable Usage Harness ===")
    service = HostedWorkspaceService()

    # Scenario 1: FR-WS-ISOLATE_HOSTED_WORKSPACES
    print("\n--- Scenario 1: FR-WS-ISOLATE_HOSTED_WORKSPACES ---")
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
    prov1 = await fr_ws_isolate_hosted_workspaces(service, ctx1)
    print(f"Provisioned Workspace 1: {prov1.workspace_id}")
    print(f"  Metadata scope: {prov1.metadata_scope}")
    print(f"  Artifact scope: {prov1.artifact_scope}")

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
    prov2 = await fr_ws_isolate_hosted_workspaces(service, ctx2)
    print(f"Provisioned Workspace 2: {prov2.workspace_id}")

    # Demonstrate isolation collision detection
    ws3_id = str(uuid.uuid7())
    ctx3_colliding = HostedWorkspaceContext(
        workspace_id=ws3_id,
        deployment_mode="HOSTED",
        metadata_scope=f"meta-ws3-{ws3_id}",
        artifact_scope=prov1.artifact_scope,  # Collision with ws1!
        queue_scope=f"queue-ws3-{ws3_id}",
        credential_scope=f"cred-ws3-{ws3_id}",
        quota_scope=f"quota-ws3-{ws3_id}",
        plugin_permission_scope=f"plugin-ws3-{ws3_id}",
    )
    req_collision = HostWorkspacesRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=str(uuid.uuid7()),
        operation="PROVISION",
        context=ctx3_colliding,
    )
    fail_res = await service.host_workspaces(req_collision)
    if (
        not isinstance(fail_res, WorkspaceFailure)
        or fail_res.code != "ISOLATION_CONFLICT"
    ):
        msg = "Expected ISOLATION_CONFLICT on scope collision"
        raise RuntimeError(msg)
    print(
        f"Collision correctly rejected with: "
        f"[{fail_res.code}] {fail_res.problem.detail}"
    )

    # Describe existing workspace
    desc1 = await fr_ws_isolate_hosted_workspaces(service, ws1_id)
    if desc1.workspace_id != ws1_id:
        msg = "Describe returned mismatched workspace ID"
        raise RuntimeError(msg)
    print(f"Described Workspace 1 successfully: {desc1.workspace_id}")

    # Scenario 2: FR-WS-AUTHORIZE_HOSTED_WORKSPACES
    print("\n--- Scenario 2: FR-WS-AUTHORIZE_HOSTED_WORKSPACES ---")
    p1 = PrincipalRef(
        principal_id=str(uuid.uuid7()),
        auth_provider="keycloak-oidc",
    )
    service.grant_permission(ws1_id, p1.principal_id, "workspace.read")
    service.grant_permission(ws1_id, p1.principal_id, "workspace.run_backtest")

    # Authorized action -> ALLOW
    dec1 = await fr_ws_authorize_hosted_workspaces(
        service, ws1_id, p1, "workspace.read"
    )
    print(
        f"Principal '{p1.principal_id}' on 'workspace.read': "
        f"outcome={dec1.outcome}, reason='{dec1.reason}'"
    )
    if dec1.outcome != "ALLOW" or dec1.reason != "":
        msg = "Expected ALLOW decision with empty reason"
        raise RuntimeError(msg)

    # Unauthorized action -> DENY (fail-closed)
    dec2 = await fr_ws_authorize_hosted_workspaces(
        service, ws1_id, p1, "workspace.delete"
    )
    print(
        f"Principal '{p1.principal_id}' on 'workspace.delete': "
        f"outcome={dec2.outcome}, reason='{dec2.reason}'"
    )
    if dec2.outcome != "DENY" or not dec2.reason:
        msg = "Expected DENY decision with descriptive reason"
        raise RuntimeError(msg)

    # Unknown principal -> DENY
    p2_unknown = PrincipalRef(
        principal_id=str(uuid.uuid7()),
        auth_provider="keycloak-oidc",
    )
    dec3 = await fr_ws_authorize_hosted_workspaces(
        service, ws1_id, p2_unknown, "workspace.read"
    )
    print(
        f"Unknown Principal '{p2_unknown.principal_id}': "
        f"outcome={dec3.outcome}, reason='{dec3.reason}'"
    )
    if dec3.outcome != "DENY" or not dec3.reason:
        msg = "Expected DENY decision for unknown principal"
        raise RuntimeError(msg)

    print("\n=== All Scenarios Verified Successfully ===")


def _run_scenarios() -> None:
    """Execute all requirement scenarios as an executable teaching harness."""
    asyncio.run(_async_run_scenarios())


if __name__ == "__main__":
    _run_scenarios()
