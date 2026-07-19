"""Caller-side implementation of the Simulation state port, owned by the tests.

Simulation declares `SimulationStateStore` as a Protocol and supplies no
implementation. This module is the caller-side implementation used by the
domain test suite. It is deliberately test infrastructure: no production
composition root exists yet, and placing it inside `app/services/simulator`
would restore the persistence-authority violation the port exists to prevent.

Run identity is held in SQLite. The canonical journal is append-only JSONL
written directly to the artifact root and made durable on the writer's
group-commit boundary, because a SQLite journal sidecar is an explicit Phase 1
exclusion.
"""

from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Mapping
from contextlib import closing
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType

from app.services.simulator.errors import SimulationError
from app.services.simulator.state import SIMULATION_MIGRATIONS, RunStatus
from app.utils import canonical_json, logger


def _parse_canonical_event(canonical_event: str) -> tuple[dict[str, object], int]:
    """Parse and validate one canonical journal record.

    Args:
        canonical_event: Candidate canonical JSON line.

    Returns:
        Parsed event and its sequence.

    Raises:
        ValueError: If the record is not canonical or sequenced.
    """
    logger.debug("Parsing canonical Simulation journal record")
    parsed: dict[str, object] = json.loads(canonical_event)
    if canonical_json(parsed) != canonical_event or "\n" in canonical_event:
        raise ValueError("event is not canonical single-line JSON")
    sequence = parsed.get("sequence")
    if not isinstance(sequence, int) or sequence < 0:
        raise ValueError("event sequence is invalid")
    return parsed, sequence


def _validate_finalized_events(
    events: tuple[dict[str, object], ...],
    expected_event_count: int,
    expected_tail_hash: str,
) -> None:
    """Validate final journal count and tail identity.

    Args:
        events: Ordered parsed journal events.
        expected_event_count: Exact expected count.
        expected_tail_hash: Exact expected tail hash.

    Raises:
        ValueError: If finalization evidence differs.
    """
    logger.debug("Validating completed Simulation journal evidence")
    if len(events) != expected_event_count:
        raise ValueError("journal event count differs")
    if not events or events[-1].get("event_hash") != expected_tail_hash:
        raise ValueError("journal tail hash differs")


def _safe_run_root(artifact_root: Path, run_id: str) -> Path:
    """Resolve a run artifact directory beneath its approved root.

    Args:
        artifact_root: Approved resolved artifact root.
        run_id: Previously validated run identity.

    Returns:
        Resolved run artifact directory.

    Raises:
        OSError: If the resolved path escapes the approved root.
    """
    logger.debug("Resolving safe Simulation run artifact path")
    run_root = (artifact_root / run_id).resolve()
    if artifact_root not in run_root.parents:
        raise OSError("journal path escaped artifact root")
    return run_root


class SqliteSimulationStateStore:
    """SQLite-backed state store satisfying `SimulationStateStore`."""

    def __init__(self, database_path: Path, artifact_root: Path) -> None:
        """Initialize the isolated store and its Simulation-owned schema.

        Args:
            database_path: Explicit SQLite database file.
            artifact_root: Approved root for canonical artifacts.

        Raises:
            SimulationError: If paths or schema initialization fail.
        """
        logger.info("Initializing SQLite Simulation state store")
        self._database_path = database_path.resolve()
        self._artifact_root = artifact_root.resolve()
        self._appended: dict[str, int] = {}
        try:
            self._database_path.parent.mkdir(parents=True, exist_ok=True)
            self._artifact_root.mkdir(parents=True, exist_ok=True)
            with closing(self._connect()) as connection, connection:
                for migration in SIMULATION_MIGRATIONS:
                    for statement in migration.statements:
                        connection.execute(statement)
        except (OSError, sqlite3.Error) as error:
            raise SimulationError(
                "SIM_PERSISTENCE_FAILED", "State initialization failed"
            ) from error

    def _connect(self) -> sqlite3.Connection:
        """Open one configured SQLite connection.

        Returns:
            SQLite connection with atomic transaction semantics.
        """
        logger.debug("Opening Simulation state connection")
        connection = sqlite3.connect(self._database_path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _validate_identity(value: str, field: str) -> str:
        """Validate an artifact-safe identifier.

        Args:
            value: Candidate identifier.
            field: Safe field label.

        Returns:
            Validated identifier.

        Raises:
            SimulationError: If path-control characters are present.
        """
        logger.debug("Validating Simulation persistence identity %s", field)
        if (
            not value
            or value != value.strip()
            or any(character in value for character in ("/", "\\", ".."))
        ):
            raise SimulationError("SIM_PERSISTENCE_FAILED", f"{field} is invalid")
        return value

    def _partial_path(self, run_id: str) -> Path:
        """Resolve the in-progress append-only journal path.

        Args:
            run_id: Previously validated run identity.

        Returns:
            Path of the partial JSONL journal.
        """
        run_root = _safe_run_root(self._artifact_root, run_id)
        run_root.mkdir(parents=True, exist_ok=True)
        return run_root / "journal.jsonl.partial"

    def _append_line(self, run_id: str, canonical_event: str) -> None:
        """Validate sequence continuity and append one buffered JSONL line.

        Args:
            run_id: Previously validated run identity.
            canonical_event: Canonical single-line event JSON.

        Raises:
            ValueError: If the event is not canonical or contiguous.
        """
        _, sequence = _parse_canonical_event(canonical_event)
        expected = self._appended.get(run_id, 0)
        if sequence != expected:
            raise ValueError("journal sequence is not contiguous")
        with self._partial_path(run_id).open("a", encoding="utf-8") as handle:
            handle.write(f"{canonical_event}\n")
        self._appended[run_id] = expected + 1

    def append_journal(self, run_id: str, canonical_event: str) -> None:
        """Append one canonical event to the append-only JSONL journal.

        The write is buffered; durability is provided by `flush_journal` on the
        writer's group-commit boundary.

        Args:
            run_id: Safe Simulation run identity.
            canonical_event: Canonical single-line event JSON.

        Raises:
            SimulationError: If parsing or persistence fails.
        """
        logger.info("Appending canonical journal record for run %s", run_id)
        self._validate_identity(run_id, "run_id")
        try:
            self._append_line(run_id, canonical_event)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise SimulationError(
                "SIM_PERSISTENCE_FAILED", "Journal append failed"
            ) from error

    def flush_journal(self, run_id: str) -> None:
        """Make every appended event durable for this run.

        Args:
            run_id: Safe Simulation run identity.

        Raises:
            SimulationError: If the batch cannot be made durable.
        """
        logger.info("Flushing the canonical journal for run %s", run_id)
        self._validate_identity(run_id, "run_id")
        try:
            path = self._partial_path(run_id)
            if not path.exists():
                return
            with path.open("rb+") as handle:
                os.fsync(handle.fileno())
        except OSError as error:
            raise SimulationError(
                "SIM_PERSISTENCE_FAILED", "Journal flush failed"
            ) from error

    def finalize_journal(
        self,
        run_id: str,
        expected_event_count: int,
        expected_tail_hash: str,
    ) -> str:
        """Atomically publish one completed journal and return its SHA-256.

        Args:
            run_id: Safe Simulation run identity.
            expected_event_count: Exact number of durable events.
            expected_tail_hash: Expected final event hash.

        Returns:
            Lowercase checksum of the finalized JSONL bytes.

        Raises:
            SimulationError: If continuity, writing, or replacement fails.
        """
        logger.info("Finalizing canonical journal for run %s", run_id)
        self._validate_identity(run_id, "run_id")
        try:
            partial = self._partial_path(run_id)
            lines = partial.read_text(encoding="utf-8").splitlines()
            events = tuple(json.loads(line) for line in lines)
            _validate_finalized_events(events, expected_event_count, expected_tail_hash)
            data = ("\n".join(lines) + "\n").encode("utf-8")
            run_root = _safe_run_root(self._artifact_root, run_id)
            temporary = run_root / "journal.jsonl.tmp"
            final = run_root / "journal.jsonl"
            with temporary.open("wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            temporary.replace(final)
            partial.unlink(missing_ok=True)
            return sha256(data).hexdigest()
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise SimulationError(
                "SIM_PERSISTENCE_FAILED", "Journal finalization failed"
            ) from error

    def load_run(self, request_id: str) -> Mapping[str, object] | None:
        """Load a recorded idempotency result by request identity.

        Args:
            request_id: Canonical request identifier.

        Returns:
            Immutable stored row or ``None``.

        Raises:
            SimulationError: If storage cannot be read.
        """
        logger.debug("Loading Simulation run for request %s", request_id)
        try:
            with closing(self._connect()) as connection, connection:
                row = connection.execute(
                    "SELECT request_hash, run_id, status, result_payload "
                    "FROM simulation_runs WHERE request_id = ?",
                    (request_id,),
                ).fetchone()
            if row is None:
                return None
            result_payload = None if row[3] is None else json.loads(str(row[3]))
            return MappingProxyType(
                {
                    "request_id": request_id,
                    "request_hash": str(row[0]),
                    "run_id": str(row[1]),
                    "status": str(row[2]),
                    "result_payload": result_payload,
                }
            )
        except (json.JSONDecodeError, sqlite3.Error) as error:
            raise SimulationError(
                "SIM_PERSISTENCE_FAILED", "Run load failed"
            ) from error

    def record_idempotency(
        self,
        request_id: str,
        request_hash: str,
        run_id: str,
        status: RunStatus,
        result_payload: Mapping[str, object] | None = None,
    ) -> None:
        """Record or advance one request-id state without ambiguity.

        Args:
            request_id: Canonical request identifier.
            request_hash: Canonical request material hash.
            run_id: Stable run identity.
            status: Monotonic lifecycle status.
            result_payload: Completed canonical result payload when applicable.

        Raises:
            SimulationError: If identity conflicts or persistence fails.
        """
        logger.info("Recording Simulation idempotency state %s", status)
        self._validate_identity(run_id, "run_id")
        serialized = None if result_payload is None else canonical_json(result_payload)
        conflict = False
        try:
            with closing(self._connect()) as connection, connection:
                existing = connection.execute(
                    "SELECT request_hash, run_id, status FROM simulation_runs "
                    "WHERE request_id = ?",
                    (request_id,),
                ).fetchone()
                if existing is not None and (
                    str(existing[0]) != request_hash or str(existing[1]) != run_id
                ):
                    conflict = True
                elif existing is None:
                    connection.execute(
                        "INSERT INTO simulation_runs"
                        "(request_id, request_hash, run_id, status, result_payload) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (request_id, request_hash, run_id, status, serialized),
                    )
                else:
                    connection.execute(
                        "UPDATE simulation_runs SET status = ?, result_payload = ? "
                        "WHERE request_id = ?",
                        (status, serialized, request_id),
                    )
        except (sqlite3.Error, ValueError) as error:
            raise SimulationError(
                "SIM_PERSISTENCE_FAILED", "Idempotency write failed"
            ) from error
        if conflict:
            raise SimulationError(
                "SIM_RUN_ID_CONFLICT",
                "Request identity conflicts with stored run",
            )


__all__ = ["SqliteSimulationStateStore"]
