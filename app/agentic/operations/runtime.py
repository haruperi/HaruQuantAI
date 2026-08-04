"""Durable Agentic operations store over Agentic-owned relational records."""

from __future__ import annotations

from typing import cast

from pydantic import BaseModel

from app.agentic.operations.models import (
    AgenticTrace,
    IncidentRecord,
    ReplayOutcome,
    ReplayRequest,
)
from app.agentic.persistence import (
    create_agentic_persistence_store,
    create_incident_record,
    create_operation_trace_record,
    create_replay_record,
    read_incident_records,
    read_operation_trace_record,
)


def _encode(value: object) -> str:
    """Encode one validated operations model.

    Returns:
        JSON text.

    Raises:
        TypeError: If the value is not a validated model.
    """
    if not isinstance(value, BaseModel):
        raise TypeError("Agentic operations state must be a validated model")
    return value.model_dump_json()


class DurableOperationsStore:
    """Data-backed implementation of the Agentic operations-store port."""

    def __init__(self) -> None:
        """Build the relational persistence handle."""
        self._store = create_agentic_persistence_store(
            {
                "incident": (_encode, IncidentRecord.model_validate_json),
                "replay": (_encode, ReplayOutcome.model_validate_json),
                "replay-request": (_encode, ReplayRequest.model_validate_json),
                "trace": (_encode, AgenticTrace.model_validate_json),
            }
        )

    def save_trace(self, trace: AgenticTrace) -> AgenticTrace:
        """Persist one immutable trace.

        Returns:
            Persisted trace.
        """
        create_operation_trace_record(
            self._store,
            trace.trace_hash,
            trace,
        )
        return trace

    def load_trace(self, trace_hash: str) -> AgenticTrace | None:
        """Load one trace by digest.

        Returns:
            Trace or ``None``.
        """
        return cast(
            "AgenticTrace | None",
            read_operation_trace_record(
                self._store,
                trace_hash,
            ),
        )

    def record_incident(self, incident: IncidentRecord) -> IncidentRecord:
        """Atomically enforce incident uniqueness and append its evidence.

        Returns:
            Persisted incident.

        Raises:
            ValueError: If the incident classification is already recorded.
        """
        incidents = self._all_incidents()
        committed = create_incident_record(
            self._store,
            guard_key=f"{incident.run_id}:{incident.correlation_id}:{incident.kind}",
            incident_key=incident.incident_id,
            sequence=len(incidents) + 1,
            value=incident,
        )
        if not committed:
            raise ValueError("Agentic incident classification is already recorded")
        return incident

    def _all_incidents(self) -> tuple[IncidentRecord, ...]:
        """Load the bounded global incident ledger.

        Returns:
            Ordered incidents.
        """
        return cast(
            "tuple[IncidentRecord, ...]",
            read_incident_records(
                self._store,
                "incidents",
                1_000,
            ),
        )

    def list_incidents(self, run_id: str) -> tuple[IncidentRecord, ...]:
        """List incidents for one run.

        Returns:
            Ordered matching incidents.
        """
        return tuple(item for item in self._all_incidents() if item.run_id == run_id)

    def quarantined_roles(self) -> tuple[str, ...]:
        """List unique quarantined roles.

        Returns:
            Ordered role identities.
        """
        return tuple(
            sorted(
                {
                    item.quarantined_role_id
                    for item in self._all_incidents()
                    if item.quarantined_role_id is not None
                }
            )
        )

    def record_replay(
        self, request: ReplayRequest, outcome: ReplayOutcome
    ) -> ReplayOutcome:
        """Record one replay outcome once.

        Returns:
            Persisted outcome.

        Raises:
            ValueError: If the replay identity already exists.
        """
        if request.replay_id != outcome.replay_id:
            raise ValueError("Agentic replay request and outcome conflict")
        create_replay_record(
            self._store,
            request.replay_id,
            request,
            outcome,
        )
        return outcome


__all__ = ("DurableOperationsStore",)
