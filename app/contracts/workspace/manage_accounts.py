"""Public contract for account, principal, session, and scope verification."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.contracts.workspace.models import (
    AccountRecord,
    ManageAccountsRequest,
    ManageAccountsSuccess,
)

if TYPE_CHECKING:
    from app.contracts.workspace.errors import WorkspaceFailure


@runtime_checkable
class ManageAccountsCapability(Protocol):
    """Capability protocol for account and current-session verification."""

    async def manage_accounts(
        self,
        request: ManageAccountsRequest,
    ) -> ManageAccountsSuccess | WorkspaceFailure:
        """Serve one account/session operation.

        Args:
            request: REGISTER, LOGIN, ME, or LOGOUT request.

        Returns:
            A typed success or Workspace failure.
        """
        ...


__all__ = [
    "AccountRecord",
    "ManageAccountsCapability",
    "ManageAccountsRequest",
    "ManageAccountsSuccess",
]
