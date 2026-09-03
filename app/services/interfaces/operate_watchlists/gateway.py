"""Account watchlist gateway: the capability provider.

Purpose:
    Translate the ratified Interfaces watchlist contract onto the
    Workspace-owned manage-watchlists capability: LIST, CREATE, UPDATE,
    and DELETE with the standalone default account applied until the
    identity boundary (gap G2) is ratified.

Key capabilities:
    * Serve operation-discriminated watchlist requests.
    * Map workspace failures to the stable interface failure envelope.
    * Fail closed with CAPABILITY_UNAVAILABLE after disposal.

Python API usage:
    gateway = WatchlistGateway(provider, OperateWatchlistsConfig())
    result = await gateway.operate_watchlists(request)

CLI usage:
    uv run python -m app.services.interfaces.operate_watchlists.gateway
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid7

from app.contracts.common.models import ProblemDetails
from app.contracts.interfaces.errors import InterfaceFailure
from app.contracts.interfaces.models import (
    OperateWatchlistsRequest,
    OperateWatchlistsSuccess,
)
from app.contracts.workspace.errors import WorkspaceFailure
from app.contracts.workspace.models import (
    ManageWatchlistsRequest,
)

_EXPECTED_SEED_ITEMS = 4

if TYPE_CHECKING:
    from app.contracts.workspace.ports import ManageWatchlistsCapability
    from app.services.interfaces.operate_watchlists.config import (
        OperateWatchlistsConfig,
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
            detail="The watchlist gateway is disposed.",
        ),
    )


class WatchlistGateway:
    """OperateWatchlistsCapability provider for one mounted generation."""

    def __init__(
        self,
        provider: ManageWatchlistsCapability,
        config: OperateWatchlistsConfig,
    ) -> None:
        """Assemble the gateway around the resolved provider.

        Args:
            provider: Active workspace.manage-watchlists provider.
            config: Gateway configuration with the default account.
        """
        self._provider = provider
        self._config = config
        self._closed = False

    @property
    def config(self) -> OperateWatchlistsConfig:
        """Return the validated gateway configuration."""
        return self._config

    async def operate_watchlists(
        self,
        request: OperateWatchlistsRequest,
    ) -> OperateWatchlistsSuccess | InterfaceFailure:
        """Serve one watchlist gateway request.

        Args:
            request: Operation-discriminated gateway request.

        Returns:
            The operation result on success, otherwise a structured
            interface failure.
        """
        if self._closed:
            return _closed_failure()
        provider_request = ManageWatchlistsRequest(
            request_id=request.request_id,
            capability_snapshot_id=request.capability_snapshot_id,
            account_id=self._config.default_account_id,
            operation=request.operation,
            watchlist_id=request.watchlist_id,
            name=request.name,
            symbols=request.symbols,
            is_default=request.is_default,
            sort_order=request.sort_order,
        )
        result = await self._provider.manage_watchlists(provider_request)
        if isinstance(result, WorkspaceFailure):
            return _failure_from_workspace(result)
        return OperateWatchlistsSuccess(
            request_id=request.request_id,
            watchlists=result.watchlists,
            watchlist=result.watchlist,
            deleted=result.deleted,
        )

    def close(self) -> None:
        """Dispose the gateway; safe to call repeatedly."""
        self._closed = True
