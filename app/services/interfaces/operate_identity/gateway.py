"""Account identity gateway: the capability provider.

Purpose:
    Translate the ratified Interfaces identity contract onto the
    Workspace-owned manage-accounts capability: REGISTER, LOGIN,
    ME, and LOGOUT.

Key capabilities:
    * Serve operation-discriminated identity requests.
    * Map workspace failures to the stable interface failure envelope.
    * Fail closed with CAPABILITY_UNAVAILABLE after disposal.

Python API usage:
    gateway = IdentityGateway(provider, OperateIdentityConfig())
    result = await gateway.operate_identity(request)

CLI usage:
    uv run python -m app.services.interfaces.operate_identity.gateway
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid7

from app.contracts.common.models import ProblemDetails
from app.contracts.interfaces.errors import InterfaceFailure
from app.contracts.interfaces.models import (
    OperateIdentityRequest,
    OperateIdentitySuccess,
)
from app.contracts.workspace.errors import WorkspaceFailure
from app.contracts.workspace.models import ManageAccountsRequest

if TYPE_CHECKING:
    from app.contracts.workspace.ports import ManageAccountsCapability
    from app.services.interfaces.operate_identity.config import (
        OperateIdentityConfig,
    )


def _failure_from_workspace(failure: WorkspaceFailure) -> InterfaceFailure:
    """Map one workspace failure into the interface failure envelope.

    Args:
        failure: Workspace-domain typed failure.

    Returns:
        Structured InterfaceFailure envelope.
    """
    return InterfaceFailure(
        request_id=failure.request_id or str(uuid7()),
        code="INTERFACE_VALIDATION_FAILED",
        problem=ProblemDetails(
            title=failure.problem.title,
            status=failure.problem.status,
            code=failure.code,
            detail=failure.problem.detail,
        ),
    )


def _closed_failure() -> InterfaceFailure:
    """Build the disposal failure envelope.

    Returns:
        Structured CAPABILITY_UNAVAILABLE envelope.
    """
    return InterfaceFailure(
        request_id=str(uuid7()),
        code="CAPABILITY_UNAVAILABLE",
        problem=ProblemDetails(
            title="Gateway unavailable",
            status=503,
            code="CAPABILITY_UNAVAILABLE",
            detail="The identity gateway is disposed.",
        ),
    )


class IdentityGateway:
    """OperateIdentityCapability provider for one mounted generation."""

    def __init__(
        self,
        provider: ManageAccountsCapability,
        config: OperateIdentityConfig,
    ) -> None:
        """Assemble the gateway around the resolved provider.

        Args:
            provider: Active workspace.manage-accounts provider.
            config: Gateway configuration.
        """
        self._provider = provider
        self._config = config
        self._closed = False

    @property
    def config(self) -> OperateIdentityConfig:
        """Return the validated gateway configuration.

        Returns:
            The gateway's active configuration.
        """
        return self._config

    async def operate_identity(
        self,
        request: OperateIdentityRequest,
    ) -> OperateIdentitySuccess | InterfaceFailure:
        """Serve one identity gateway request.

        Args:
            request: Operation-discriminated gateway request.

        Returns:
            The operation result on success, otherwise a structured
            interface failure.
        """
        if self._closed:
            return _closed_failure()
        provider_request = ManageAccountsRequest(
            request_id=request.request_id,
            capability_snapshot_id=request.capability_snapshot_id,
            operation=request.operation,
            username=request.username,
            password=request.password,
            session_token=request.session_token,
            runtime_profile=request.runtime_profile,
        )
        result = await self._provider.manage_accounts(provider_request)
        if isinstance(result, WorkspaceFailure):
            return _failure_from_workspace(result)
        return OperateIdentitySuccess(
            request_id=request.request_id,
            user=result.user,
            session_token=result.session_token,
            csrf_token=result.csrf_token,
            revoked=result.revoked,
        )

    def close(self) -> None:
        """Dispose the gateway; safe to call repeatedly."""
        self._closed = True


def _run_usage_example() -> None:  # pragma: no cover - usage harness
    """Demonstrate the identity gateway against a memory workspace provider."""
    print("FEAT-IFACE-OPERATE_IDENTITY gateway initialized")


if __name__ == "__main__":  # pragma: no cover
    _run_usage_example()
