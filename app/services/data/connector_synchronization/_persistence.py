"""Persistence and state storage for Connector Synchronization."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.contracts.common.models import Uuid7
    from app.contracts.data.models import (
        ConnectorSyncPlan,
        ConnectorSyncReceipt,
    )


class ConnectorSyncPersistence:
    """In-memory plan, receipt, and checkpoint store for connector synchronization."""

    def __init__(self) -> None:
        self._plans: dict[Uuid7, ConnectorSyncPlan] = {}
        self._receipts: dict[Uuid7, ConnectorSyncReceipt] = {}
        self._checkpoints: dict[str, str] = {}

    def save_plan(self, plan: ConnectorSyncPlan) -> None:
        """Store a connector sync plan."""
        self._plans[plan.plan_id] = plan

    def get_plan(self, plan_id: Uuid7) -> ConnectorSyncPlan | None:
        """Retrieve a sync plan by its ID."""
        return self._plans.get(plan_id)

    def get_all_plans(self) -> list[ConnectorSyncPlan]:
        """Return all stored sync plans."""
        return list(self._plans.values())

    def save_receipt(self, receipt: ConnectorSyncReceipt) -> None:
        """Store an execution receipt."""
        self._receipts[receipt.receipt_id] = receipt

    def get_receipt(self, receipt_id: Uuid7) -> ConnectorSyncReceipt | None:
        """Retrieve an execution receipt by its ID."""
        return self._receipts.get(receipt_id)

    def get_all_receipts(self) -> list[ConnectorSyncReceipt]:
        """Return all stored receipts."""
        return list(self._receipts.values())

    def set_checkpoint(self, connector_id: str, checkpoint: str) -> None:
        """Record sync cursor checkpoint."""
        self._checkpoints[connector_id] = checkpoint

    def get_checkpoint(self, connector_id: str) -> str | None:
        """Get sync cursor checkpoint."""
        return self._checkpoints.get(connector_id)

    def clear(self) -> None:
        """Reset all in-memory stores."""
        self._plans.clear()
        self._receipts.clear()
        self._checkpoints.clear()
