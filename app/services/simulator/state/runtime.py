"""Simulation state adapter over relational run state and JSONL journals."""

# ruff: noqa: TRY301 - owner errors are normalized at this adapter boundary.

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Literal, cast

from app.services.simulator.errors.exception import SimulationError
from app.services.simulator.errors.responses import operation_guard
from app.services.simulator.persistence import (
    complete_run_record,
    create_run_record,
    create_simulator_persistence_store,
    read_result_record,
    read_run_record,
    update_run_record,
)
from app.services.simulator.reporting.contracts import (
    PortfolioSimulationResult,
    SimulationResult,
)
from app.utils import canonical_json, get_logger

logger = get_logger(__name__)
type RunStatus = Literal["started", "completed", "failed"]


def _decode_result(payload: str) -> object:
    """Decode one validated completed Simulation result.

    Returns:
        A canonical single-run or portfolio result.

    Raises:
        TypeError: If the stored payload is not an object.
        ValueError: If the result schema is unsupported.
    """
    material = json.loads(payload)
    if not isinstance(material, dict):
        raise TypeError("Simulation result payload must be an object")
    schema_id = material.get("schema_id")
    if schema_id == "simulation.result.v1":
        return SimulationResult.model_validate(material)
    if schema_id == "simulation.portfolio_result.v1":
        return PortfolioSimulationResult.model_validate(material)
    raise ValueError("unsupported Simulation result schema")


def _validate_identity(value: str, field: str) -> str:
    """Validate one artifact-safe identity.

    Returns:
        The validated identity.

    Raises:
        ValueError: If path-control material is present.
    """
    if (
        not value
        or value != value.strip()
        or any(character in value for character in ("/", "\\", ".."))
    ):
        message = f"{field} is invalid"
        raise ValueError(message)
    return value


def _safe_run_root(artifact_root: Path, run_id: str) -> Path:
    """Resolve a run directory beneath the approved artifact root.

    Returns:
        Safe resolved run directory.

    Raises:
        ValueError: If the path escapes the approved root.
    """
    run_root = (artifact_root / _validate_identity(run_id, "run_id")).resolve()
    if artifact_root not in run_root.parents:
        raise ValueError("journal path escapes the artifact root")
    return run_root


def _parse_event(canonical_event: str) -> dict[str, object]:
    """Parse and validate one canonical journal event.

    Returns:
        Parsed canonical event.

    Raises:
        TypeError: If the decoded event is not an object.
        ValueError: If the event is malformed or not canonical.
    """
    event = json.loads(canonical_event)
    if not isinstance(event, dict):
        raise TypeError("journal event must be an object")
    if (
        "\n" in canonical_event
        or canonical_json(event, max_items=None) != canonical_event
    ):
        raise ValueError("journal event must be canonical single-line JSON")
    sequence = event.get("sequence")
    if not isinstance(sequence, int) or sequence < 0:
        raise ValueError("journal event sequence is invalid")
    return event


def _read_journal(path: Path) -> tuple[tuple[str, ...], tuple[dict[str, object], ...]]:
    """Read and validate one partial or finalized journal.

    Returns:
        Canonical lines and parsed contiguous events.

    Raises:
        ValueError: If journal material is malformed or discontinuous.
    """
    if not path.exists():
        return (), ()
    lines = tuple(path.read_text(encoding="utf-8").splitlines())
    events = tuple(_parse_event(line) for line in lines)
    if any(event["sequence"] != index for index, event in enumerate(events)):
        raise ValueError("journal event sequence is not contiguous")
    return lines, events


def _fsync(path: Path) -> None:
    """Make the current journal bytes durable."""
    if not path.exists():
        return
    with path.open("rb+") as handle:
        handle.flush()
        os.fsync(handle.fileno())


def _lifecycle_value(
    request_id: str,
    request_hash: str,
    run_id: str,
    status: RunStatus,
    result_payload: Mapping[str, object] | None,
) -> dict[str, object]:
    """Build and validate one lifecycle replacement value.

    Returns:
        Normalized lifecycle value.

    Raises:
        ValueError: If status and result material are inconsistent.
    """
    if status not in {"started", "completed", "failed"}:
        raise ValueError("Simulation lifecycle status is invalid")
    if status == "completed" and not result_payload:
        raise ValueError("completed run requires result payload")
    if status != "completed" and result_payload is not None:
        raise ValueError("non-completed run cannot carry a result payload")
    return {
        "request_id": request_id,
        "request_hash": request_hash,
        "run_id": run_id,
        "status": status,
        "result_payload": None if result_payload is None else dict(result_payload),
    }


def _validate_existing_transition(
    existing: Mapping[str, object],
    *,
    request_hash: str,
    run_id: str,
    status: RunStatus,
    result_payload: Mapping[str, object] | None,
) -> tuple[str, Mapping[str, object] | None, bool]:
    """Validate identity and prior lifecycle material.

    Returns:
        Prior status, prior result payload, and identical-replay flag.

    Raises:
        SimulationError: If request identity conflicts.
        TypeError: If stored result material is malformed.
        ValueError: If lifecycle state is malformed or terminal.
    """
    if existing.get("request_hash") != request_hash or existing.get("run_id") != run_id:
        raise SimulationError(
            "SIM_RUN_ID_CONFLICT",
            "Request identity conflicts with stored run",
        )
    prior = str(existing.get("status"))
    if prior not in {"started", "completed", "failed"}:
        raise ValueError("stored Simulation lifecycle status is invalid")
    prior_result = existing.get("result_payload")
    if prior_result is not None and not isinstance(prior_result, Mapping):
        raise TypeError("stored Simulator result payload is malformed")
    expected_result = cast("Mapping[str, object] | None", prior_result)
    if prior == status:
        if expected_result != result_payload:
            raise ValueError("terminal Simulation result cannot change")
        return prior, expected_result, True
    if prior != "started":
        raise ValueError("Simulation lifecycle cannot change after terminal state")
    return prior, expected_result, False


class _DurableSimulationStateStore:
    """Simulation adapter over `sim_runs` and canonical JSONL artifacts."""

    def __init__(self, artifact_root: Path) -> None:
        """Initialize the adapter without opening a database connection.

        Args:
            artifact_root: Approved Simulation artifact root.
        """
        self._artifact_root = artifact_root.resolve()
        self._store = create_simulator_persistence_store(_decode_result)
        self._appended: dict[str, int] = {}

    def _journal_paths(self, run_id: str) -> tuple[Path, Path]:
        """Return partial and published paths for one run."""
        run_root = _safe_run_root(self._artifact_root, run_id)
        return run_root / "journal.jsonl.partial", run_root / "journal.jsonl"

    @operation_guard(
        operation="simulation.state.runtime.append_journal",
        risk_level="medium",
        read_only=False,
        modifies_database=False,
        writes_file=True,
    )
    def append_journal(self, run_id: str, canonical_event: str) -> None:
        """Append one canonical event to the partial JSONL journal.

        Raises:
            SimulationError: If the event cannot be validated or persisted.
            ValueError: If the resolved journal path is unsafe.
        """
        try:
            event = _parse_event(canonical_event)
            partial, final = self._journal_paths(run_id)
            if final.exists():
                raise ValueError("finalized journal cannot be appended")
            partial.parent.mkdir(parents=True, exist_ok=True)
            if run_id not in self._appended:
                _, existing = _read_journal(partial)
                self._appended[run_id] = len(existing)
            expected = self._appended[run_id]
            if event["sequence"] != expected:
                raise ValueError("journal event sequence is not contiguous")
            with partial.open("a", encoding="utf-8") as handle:
                handle.write(f"{canonical_event}\n")
            self._appended[run_id] = expected + 1
        except (OSError, TypeError, ValueError) as error:
            raise SimulationError(
                "SIM_PERSISTENCE_FAILED", "Journal append failed"
            ) from error

    @operation_guard(
        operation="simulation.state.runtime.flush_journal",
        risk_level="medium",
        read_only=False,
        modifies_database=False,
        writes_file=True,
    )
    def flush_journal(self, run_id: str) -> None:
        """Make all partial journal bytes durable.

        Raises:
            SimulationError: If the journal cannot be flushed.
        """
        try:
            partial, _ = self._journal_paths(run_id)
            _fsync(partial)
        except (OSError, ValueError) as error:
            raise SimulationError(
                "SIM_PERSISTENCE_FAILED", "Journal flush failed"
            ) from error

    @operation_guard(
        operation="simulation.state.runtime.finalize_journal",
        risk_level="medium",
        read_only=False,
        writes_file=True,
        modifies_database=False,
    )
    def finalize_journal(
        self,
        run_id: str,
        expected_event_count: int,
        expected_tail_hash: str,
    ) -> str:
        """Validate and atomically publish a completed journal.

        Returns:
            SHA-256 checksum of canonical JSONL bytes.

        Raises:
            SimulationError: If journal validation or publication fails.
            ValueError: If the resolved journal path is unsafe.
        """
        try:
            partial, final = self._journal_paths(run_id)
            source = partial if partial.exists() else final
            lines, events = _read_journal(source)
            if len(events) != expected_event_count or not events:
                raise ValueError("journal event count does not match")
            if events[-1].get("event_hash") != expected_tail_hash:
                raise ValueError("journal tail hash does not match")
            payload = ("\n".join(lines) + "\n").encode("utf-8")
            if source == partial:
                _fsync(partial)
                partial.replace(final)
            return hashlib.sha256(payload).hexdigest()
        except (OSError, TypeError, ValueError) as error:
            raise SimulationError(
                "SIM_PERSISTENCE_FAILED", "Journal finalization failed"
            ) from error

    @operation_guard(
        operation="simulation.state.runtime.load_run",
        risk_level="low",
        read_only=True,
    )
    def load_run(self, request_id: str) -> Mapping[str, object] | None:
        """Load one durable idempotency row.

        Returns:
            Stored run row or ``None``.

        Raises:
            SimulationError: If stored state is malformed.
        """
        try:
            return read_run_record(self._store, request_id)
        except (TypeError, ValueError) as error:
            raise SimulationError(
                "SIM_PERSISTENCE_FAILED", "Stored run is invalid"
            ) from error

    @operation_guard(
        operation="simulation.state.runtime.load_result",
        risk_level="low",
        read_only=True,
    )
    def load_result(self, run_id: str) -> object | None:
        """Load one validated completed result by run identity.

        Returns:
            A canonical completed result or ``None``.

        Raises:
            SimulationError: If the run identity or stored result is invalid.
        """
        if not run_id:
            raise SimulationError("SIM_INVALID_CONFIG", "Run identity is invalid")
        try:
            return read_result_record(self._store, run_id)
        except (TypeError, ValueError) as error:
            raise SimulationError(
                "SIM_PERSISTENCE_FAILED", "Stored result is invalid"
            ) from error

    @operation_guard(
        operation="simulation.state.runtime.record_idempotency",
        risk_level="medium",
        read_only=False,
        modifies_database=True,
    )
    def record_idempotency(
        self,
        request_id: str,
        request_hash: str,
        run_id: str,
        status: RunStatus,
        result_payload: Mapping[str, object] | None = None,
    ) -> None:
        """Record or monotonically advance one Simulation request lifecycle.

        Raises:
            SimulationError: If identity, lifecycle, or persistence validation fails.
            TypeError: If stored result material is malformed.
            ValueError: If lifecycle evidence is inconsistent.
        """
        try:
            value = _lifecycle_value(
                request_id, request_hash, run_id, status, result_payload
            )
            existing = read_run_record(self._store, request_id)
            if existing is None:
                create_run_record(self._store, request_id, value)
                return
            prior, expected_result, replay = _validate_existing_transition(
                existing,
                request_hash=request_hash,
                run_id=run_id,
                status=status,
                result_payload=result_payload,
            )
            if replay:
                return
            if status == "completed":
                complete_run_record(
                    self._store,
                    key=request_id,
                    value=value,
                    expected_status=prior,
                    expected_result_payload=expected_result,
                )
                return
            if not update_run_record(
                self._store,
                key=request_id,
                value=value,
                expected_status=prior,
                expected_result_payload=expected_result,
            ):
                raise ValueError("Simulator run lifecycle state conflict")
        except SimulationError:
            raise
        except (TypeError, ValueError) as error:
            raise SimulationError(
                "SIM_PERSISTENCE_FAILED", "Idempotency write failed"
            ) from error


def build_simulation_state_store(*, artifact_root: Path) -> object:
    """Build the production Simulation state adapter.

    Args:
        artifact_root: Approved root for canonical Simulation artifacts.

    Returns:
        Opaque object satisfying ``SimulationStateStore``.
    """
    logger.info("Building durable Simulation state adapter")
    return _DurableSimulationStateStore(artifact_root)


__all__ = ("build_simulation_state_store",)
