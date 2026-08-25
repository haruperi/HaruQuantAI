"""Trading domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.trading.ports import (
        AccountOperationsCapability,
        DispatchOrdersCapability,
        ExecutePublicActionsCapability,
        JournalExecutionCapability,
        ManageProtectionsCapability,
        ManageTradingSessionsCapability,
        ReconcileTradingCapability,
        ValidateTradePlansCapability,
    )

MANAGE_TRADING_SESSIONS_CAPABILITY: CapabilityKey[ManageTradingSessionsCapability] = (
    CapabilityKey(
        name="trading.manage-trading-sessions",
        major=1,
    )
)

VALIDATE_TRADE_PLANS_CAPABILITY: CapabilityKey[ValidateTradePlansCapability] = (
    CapabilityKey(
        name="trading.validate-trade-plans",
        major=1,
    )
)

ACCOUNT_OPERATIONS_CAPABILITY: CapabilityKey[AccountOperationsCapability] = (
    CapabilityKey(
        name="trading.account-operations",
        major=1,
    )
)

DISPATCH_ORDERS_CAPABILITY: CapabilityKey[DispatchOrdersCapability] = CapabilityKey(
    name="trading.dispatch-orders",
    major=1,
)

RECONCILE_TRADING_CAPABILITY: CapabilityKey[ReconcileTradingCapability] = CapabilityKey(
    name="trading.reconcile-trading",
    major=1,
)

MANAGE_PROTECTIONS_CAPABILITY: CapabilityKey[ManageProtectionsCapability] = (
    CapabilityKey(
        name="trading.manage-protections",
        major=1,
    )
)

JOURNAL_EXECUTION_CAPABILITY: CapabilityKey[JournalExecutionCapability] = CapabilityKey(
    name="trading.journal-execution",
    major=1,
)

EXECUTE_PUBLIC_ACTIONS_CAPABILITY: CapabilityKey[ExecutePublicActionsCapability] = (
    CapabilityKey(
        name="trading.execute-public-actions",
        major=1,
    )
)
