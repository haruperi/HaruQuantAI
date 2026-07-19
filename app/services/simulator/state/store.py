"""Injected Simulation persistence port.

Simulation declares this port and its own migration definitions only. Data owns
the shared connection, locking, and migration-execution infrastructure, and the
caller supplies the concrete implementation. This module therefore contains no
connection, schema statement, filesystem write, or SQL of any kind.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, Protocol, runtime_checkable

type RunStatus = Literal["started", "completed", "failed"]


@runtime_checkable
class SimulationStateStore(Protocol):
    """Persistence operations Simulation depends on and never implements."""

    def append_journal(self, run_id: str, canonical_event: str) -> None:
        """Append one canonical journal record durably and transactionally.

        Args:
            run_id: Safe Simulation run identity.
            canonical_event: Canonical single-line event JSON.

        Raises:
            SimulationError: If the implementation cannot persist the record.
        """
        ...

    def flush_journal(self, run_id: str) -> None:
        """Make every previously appended event durable.

        Called by `JournalWriter` on the `JOURNAL_FSYNC_INTERVAL` group-commit
        boundary and again before finalization.

        Args:
            run_id: Safe Simulation run identity.

        Raises:
            SimulationError: If the batch cannot be made durable.
        """
        ...

    def finalize_journal(
        self,
        run_id: str,
        expected_event_count: int,
        expected_tail_hash: str,
    ) -> str:
        """Atomically publish one completed journal and return its checksum.

        Args:
            run_id: Safe Simulation run identity.
            expected_event_count: Exact number of durable events.
            expected_tail_hash: Expected final event hash.

        Returns:
            Lowercase SHA-256 checksum of the finalized JSONL bytes.

        Raises:
            SimulationError: If continuity or publication fails.
        """
        ...

    def load_run(self, request_id: str) -> Mapping[str, object] | None:
        """Load a recorded idempotency row by request identity.

        Args:
            request_id: Canonical request identifier.

        Returns:
            Immutable stored row, or ``None`` when the request is unknown.

        Raises:
            SimulationError: If stored state cannot be read.
        """
        ...

    def record_idempotency(
        self,
        request_id: str,
        request_hash: str,
        run_id: str,
        status: RunStatus,
        result_payload: Mapping[str, object] | None = None,
    ) -> None:
        """Record or advance one request-id lifecycle state without ambiguity.

        Args:
            request_id: Canonical request identifier.
            request_hash: Canonical request material hash.
            run_id: Stable run identity.
            status: Monotonic lifecycle status.
            result_payload: Completed canonical result payload when applicable.

        Raises:
            SimulationError: If identity conflicts or persistence fails.
        """
        ...


__all__ = ["RunStatus", "SimulationStateStore"]
