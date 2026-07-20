"""Startup-time reconciliation loading helpers.

Classes and functions:
    ReconciliationStartupLoader: Class. Provides ReconciliationStartupLoader behavior for execution workflows.
"""

from __future__ import annotations

from collections.abc import Iterable

from app.services.governance.workflow import ProposalState
from data.database import ExecutionIntentRecord, ExecutionRepository

DEFAULT_IN_FLIGHT_EXECUTION_STATUSES: tuple[str, ...] = (
    ProposalState.EXECUTION_PENDING.value,
    ProposalState.SENT.value,
    ProposalState.ACKNOWLEDGED.value,
    ProposalState.PARTIALLY_FILLED.value,
)


class ReconciliationStartupLoader:
    """Loads execution intents that must be reconciled before live recovery."""

    def __init__(
        self,
        execution_repository: ExecutionRepository,
        *,
        in_flight_statuses: Iterable[str] = DEFAULT_IN_FLIGHT_EXECUTION_STATUSES,
    ) -> None:
        self._execution_repository = execution_repository
        self._in_flight_statuses = tuple(in_flight_statuses)

    def load_in_flight_execution_intents(self) -> list[ExecutionIntentRecord]:
        """Perform the load_in_flight_execution_intents execution service operation."""
        return self._execution_repository.list_intents_by_statuses(
            self._in_flight_statuses
        )
