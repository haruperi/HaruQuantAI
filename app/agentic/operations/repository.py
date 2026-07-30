"""Operations-store persistence port and its deterministic in-memory double.

Agentic declares the port; a composition root binds the durable implementation
Data owns. Following the Portfolio and Risk precedents, no domain outside Data
implements a database writer, so this module holds a Protocol and an in-memory
double only.

`record_incident` is the enforcement point for evidence preservation. One
classified incident per kind per correlated run: a second containment for the
same kind is refused rather than allowed to replace the first and its evidence,
which is how an investigation would otherwise lose the original.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.utils import get_logger

if TYPE_CHECKING:
    from app.agentic.operations.models import (
        AgenticTrace,
        IncidentRecord,
        ReplayOutcome,
        ReplayRequest,
    )

logger = get_logger(__name__)


@runtime_checkable
class AgenticOperationsStore(Protocol):
    """Durable store for traces, classified incidents, and replay outcomes."""

    def save_trace(self, trace: AgenticTrace) -> AgenticTrace:
        """Persist one assembled trace.

        Args:
            trace: Validated immutable trace.

        Returns:
            The persisted trace.
        """
        ...

    def load_trace(self, trace_hash: str) -> AgenticTrace | None:
        """Load one trace by its content digest.

        Args:
            trace_hash: Content digest.

        Returns:
            The trace, or None when unrecorded.
        """
        ...

    def record_incident(self, incident: IncidentRecord) -> IncidentRecord:
        """Record one classified incident.

        Args:
            incident: Validated immutable incident record.

        Returns:
            The persisted record.

        Raises:
            ValueError: If this kind is already recorded for the run.
        """
        ...

    def list_incidents(self, run_id: str) -> tuple[IncidentRecord, ...]:
        """List every incident recorded against one run.

        Args:
            run_id: Run identity.

        Returns:
            Ordered incident records, empty when none.
        """
        ...

    def quarantined_roles(self) -> tuple[str, ...]:
        """Return every role an incident has quarantined.

        Args:
            None.

        Returns:
            Ordered unique quarantined role identities.
        """
        ...

    def record_replay(
        self,
        request: ReplayRequest,
        outcome: ReplayOutcome,
    ) -> ReplayOutcome:
        """Record one validated replay and its outcome.

        Args:
            request: Validated immutable replay request.
            outcome: Validated immutable replay outcome.

        Returns:
            The persisted outcome.

        Raises:
            ValueError: If the replay identity already exists.
        """
        ...


class _InMemoryOperationsStore:
    """Deterministic in-process operations store for tests and usage."""

    def __init__(self) -> None:
        """Initialize the empty store."""
        self._traces: dict[str, AgenticTrace] = {}
        self._incidents: list[IncidentRecord] = []
        self._replays: dict[str, ReplayOutcome] = {}

    def save_trace(self, trace: AgenticTrace) -> AgenticTrace:
        """Persist one assembled trace.

        Args:
            trace: Validated immutable trace.

        Returns:
            The persisted trace.
        """
        self._traces[trace.trace_hash] = trace
        return trace

    def load_trace(self, trace_hash: str) -> AgenticTrace | None:
        """Load one trace by its content digest.

        Args:
            trace_hash: Content digest.

        Returns:
            The trace, or None when unrecorded.
        """
        return self._traces.get(trace_hash)

    def record_incident(self, incident: IncidentRecord) -> IncidentRecord:
        """Record one classified incident.

        Args:
            incident: Validated immutable incident record.

        Returns:
            The persisted record.

        Raises:
            ValueError: If this kind is already recorded for the run.
        """
        for existing in self._incidents:
            same_run = existing.run_id == incident.run_id
            same_flow = existing.correlation_id == incident.correlation_id
            if same_run and same_flow and existing.kind == incident.kind:
                message = (
                    f"a {incident.kind!r} incident is already recorded for run "
                    f"{incident.run_id}; its evidence is not replaceable"
                )
                raise ValueError(message)
        self._incidents.append(incident)
        return incident

    def list_incidents(self, run_id: str) -> tuple[IncidentRecord, ...]:
        """List every incident recorded against one run.

        Args:
            run_id: Run identity.

        Returns:
            Ordered incident records, empty when none.
        """
        return tuple(item for item in self._incidents if item.run_id == run_id)

    def quarantined_roles(self) -> tuple[str, ...]:
        """Return every role an incident has quarantined.

        Returns:
            Ordered unique quarantined role identities.
        """
        return tuple(
            sorted(
                {
                    item.quarantined_role_id
                    for item in self._incidents
                    if item.quarantined_role_id is not None
                },
            ),
        )

    def record_replay(
        self,
        request: ReplayRequest,
        outcome: ReplayOutcome,
    ) -> ReplayOutcome:
        """Record one validated replay and its outcome.

        Args:
            request: Validated immutable replay request.
            outcome: Validated immutable replay outcome.

        Returns:
            The persisted outcome.

        Raises:
            ValueError: If the replay identity already exists.
        """
        if request.replay_id in self._replays:
            message = f"replay {request.replay_id} is already recorded"
            raise ValueError(message)
        self._replays[request.replay_id] = outcome
        return outcome


def build_in_memory_operations_store() -> AgenticOperationsStore:
    """Build the deterministic in-process operations store.

    Returns:
        A store satisfying `AgenticOperationsStore`.
    """
    logger.debug("Building the in-memory Agentic operations store")
    return _InMemoryOperationsStore()
