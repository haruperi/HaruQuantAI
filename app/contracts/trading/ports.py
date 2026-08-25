"""Public capability protocols (ports) for Trading capabilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.contracts.trading.errors import TradingFailure
    from app.contracts.trading.models import (
        AccountOperationsRequest,
        AccountOperationsSuccess,
        DispatchOrdersRequest,
        DispatchOrdersSuccess,
        ExecutePublicActionsRequest,
        ExecutePublicActionsSuccess,
        JournalExecutionRequest,
        JournalExecutionSuccess,
        ManageProtectionsRequest,
        ManageProtectionsSuccess,
        ManageTradingSessionsRequest,
        ManageTradingSessionsSuccess,
        ReconcileTradingRequest,
        ReconcileTradingSuccess,
        ValidateTradePlansRequest,
        ValidateTradePlansSuccess,
    )


@runtime_checkable
class ManageTradingSessionsCapability(Protocol):
    """Capability protocol for trading session lifecycle operations."""

    async def manage_trading_sessions(
        self,
        request: ManageTradingSessionsRequest,
    ) -> ManageTradingSessionsSuccess | TradingFailure:
        """Create, transition, archive, and recover durable sessions.

        Args:
            request: Operation-discriminated trading session request.

        Returns:
            The durable session and its recorded state transition on
            success, otherwise a structured trading failure.
        """
        ...


@runtime_checkable
class ValidateTradePlansCapability(Protocol):
    """Capability protocol for trade plan validation operations."""

    async def validate_trade_plans(
        self,
        request: ValidateTradePlansRequest,
    ) -> ValidateTradePlansSuccess | TradingFailure:
        """Bind intents and plans and assess trading readiness.

        Args:
            request: Operation-discriminated plan validation request.

        Returns:
            The bound intent, validated plan, or readiness assessment on
            success, otherwise a structured trading failure.
        """
        ...


@runtime_checkable
class AccountOperationsCapability(Protocol):
    """Capability protocol for operational account operations."""

    async def account_operations(
        self,
        request: AccountOperationsRequest,
    ) -> AccountOperationsSuccess | TradingFailure:
        """Project, value, and adjust operational accounts.

        Args:
            request: Operation-discriminated operational account request.

        Returns:
            The account projection, valuation, or posted ledger entry on
            success, otherwise a structured trading failure.
        """
        ...


@runtime_checkable
class DispatchOrdersCapability(Protocol):
    """Capability protocol for authority selection and dispatch."""

    async def dispatch_orders(
        self,
        request: DispatchOrdersRequest,
    ) -> DispatchOrdersSuccess | TradingFailure:
        """Obtain authority, stage evidence, and dispatch once.

        Args:
            request: Operation-discriminated authority dispatch request.

        Returns:
            The selected authority, staged evidence, classified receipt, or
            updated operation on success, otherwise a structured trading
            failure.
        """
        ...


@runtime_checkable
class ReconcileTradingCapability(Protocol):
    """Capability protocol for reconciliation and recovery operations."""

    async def reconcile_trading(
        self,
        request: ReconcileTradingRequest,
    ) -> ReconcileTradingSuccess | TradingFailure:
        """Request, execute, and resolve reconciliation runs.

        Args:
            request: Operation-discriminated reconciliation request.

        Returns:
            The reconciliation request and its typed findings on success,
            otherwise a structured trading failure.
        """
        ...


@runtime_checkable
class ManageProtectionsCapability(Protocol):
    """Capability protocol for protective-order lifecycle operations."""

    async def manage_protections(
        self,
        request: ManageProtectionsRequest,
    ) -> ManageProtectionsSuccess | TradingFailure:
        """Install, modify, cancel, and recover owned protections.

        Args:
            request: Operation-discriminated protection management request.

        Returns:
            The protection set and its validated change on success,
            otherwise a structured trading failure.
        """
        ...


@runtime_checkable
class JournalExecutionCapability(Protocol):
    """Capability protocol for execution evidence operations."""

    async def journal_execution(
        self,
        request: JournalExecutionRequest,
    ) -> JournalExecutionSuccess | TradingFailure:
        """Append journal records, pin provenance, and balance the ledger.

        Args:
            request: Operation-discriminated execution journal request.

        Returns:
            The journal record, provenance pin, or balanced ledger entry on
            success, otherwise a structured trading failure.
        """
        ...


@runtime_checkable
class ExecutePublicActionsCapability(Protocol):
    """Capability protocol for route-aware public actions."""

    async def execute_public_actions(
        self,
        request: ExecutePublicActionsRequest,
    ) -> ExecutePublicActionsSuccess | TradingFailure:
        """Route actions, govern bulk actions, and query trading state.

        Args:
            request: Operation-discriminated public action request.

        Returns:
            The routed action, state query, and bounded result rows on
            success, otherwise a structured trading failure.
        """
        ...
