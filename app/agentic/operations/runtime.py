"""Durable Agentic operations store over Data-owned runtime records."""

from __future__ import annotations

from typing import cast

from pydantic import BaseModel

from app.agentic.operations.models import (
    AgenticTrace,
    IncidentRecord,
    ReplayOutcome,
    ReplayRequest,
)
from app.services.data import (
    build_agentic_runtime_store,
    execute_runtime_store_operation,
    execute_runtime_store_transition,
)
from app.utils import canonical_digest


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


def _key(*values: str) -> str:
    """Derive one storage-safe identifier.

    Returns:
        Bounded key.
    """
    return f"record-{canonical_digest(values)}"


class DurableOperationsStore:
    """Data-backed implementation of the Agentic operations-store port."""

    def __init__(self) -> None:
        """Build the lazy Data runtime handle."""
        self._store = build_agentic_runtime_store(
            {
                "incident": (_encode, IncidentRecord.model_validate_json),
                "replay": (_encode, ReplayOutcome.model_validate_json),
                "trace": (_encode, AgenticTrace.model_validate_json),
            }
        )

    def save_trace(self, trace: AgenticTrace) -> AgenticTrace:
        """Persist one immutable trace.

        Returns:
            Persisted trace.
        """
        execute_runtime_store_operation(
            self._store,
            "put_once",
            collection="operation-traces",
            key=_key(trace.trace_hash),
            kind="trace",
            value=trace,
        )
        return trace

    def load_trace(self, trace_hash: str) -> AgenticTrace | None:
        """Load one trace by digest.

        Returns:
            Trace or ``None``.
        """
        return cast(
            "AgenticTrace | None",
            execute_runtime_store_operation(
                self._store,
                "get",
                collection="operation-traces",
                key=_key(trace_hash),
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
        committed = execute_runtime_store_transition(
            self._store,
            state_collection="incident-guards",
            state_key=_key(incident.run_id, incident.correlation_id, incident.kind),
            state_kind="incident",
            state_value=incident,
            expected_revision=0,
            event_collection="operation-incidents",
            event_key=_key(incident.incident_id),
            event_partition="incidents",
            event_sequence=len(incidents) + 1,
            event_kind="incident",
            event_value=incident,
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
            execute_runtime_store_operation(
                self._store,
                "list",
                collection="operation-incidents",
                partition="incidents",
                limit=1_000,
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
        execute_runtime_store_operation(
            self._store,
            "put_once",
            collection="operation-replays",
            key=_key(request.replay_id),
            kind="replay",
            value=outcome,
        )
        return outcome


__all__ = ("DurableOperationsStore",)
