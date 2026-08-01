"""Simulation state adapter over Data-owned durable runtime records."""

# ruff: noqa: TRY301 - owner errors are normalized at this adapter boundary.

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Literal, cast

from app.services.data import (
    build_simulator_runtime_store,
    execute_runtime_store_operation,
)
from app.services.simulator.errors.exception import SimulationError
from app.services.simulator.errors.responses import operation_guard
from app.utils import canonical_json, get_logger

logger = get_logger(__name__)
type RunStatus = Literal["started", "completed", "failed"]


def _encode_json(value: object) -> str:
    """Encode one validated JSON-compatible runtime value.

    Returns:
        Canonical JSON text.
    """
    return canonical_json(value, max_items=None)


def _decode_json(payload: str) -> object:
    """Decode one persisted JSON value.

    Returns:
        Decoded JSON value.
    """
    return json.loads(payload)


class _DurableSimulationStateStore:
    """Simulation protocol adapter over an opaque Data runtime handle."""

    def __init__(self, artifact_root: Path) -> None:
        """Initialize the adapter without opening a connection.

        Args:
            artifact_root: Approved Simulation artifact root.
        """
        self._artifact_root = artifact_root.resolve()
        self._store = build_simulator_runtime_store(
            {
                "journal": (_encode_json, _decode_json),
                "run": (_encode_json, _decode_json),
            }
        )

    @operation_guard(
        operation="simulation.state.runtime.append_journal",
        risk_level="medium",
        read_only=False,
        modifies_database=True,
    )
    def append_journal(self, run_id: str, canonical_event: str) -> None:
        """Append one canonical event through Data's atomic record operation.

        Raises:
            SimulationError: If the event cannot be validated or persisted.
        """
        try:
            event = json.loads(canonical_event)
            sequence = int(event["sequence"])
            execute_runtime_store_operation(
                self._store,
                "append",
                collection="journals",
                key=f"{run_id}-{sequence + 1}",
                partition=run_id,
                sequence=sequence + 1,
                kind="journal",
                value=canonical_event,
            )
        except (KeyError, TypeError, ValueError) as error:
            raise SimulationError(
                "SIM_PERSISTENCE_FAILED", "Journal append failed"
            ) from error

    @operation_guard(
        operation="simulation.state.runtime.flush_journal",
        risk_level="medium",
        read_only=False,
        modifies_database=True,
    )
    def flush_journal(self, run_id: str) -> None:
        """Confirm the named journal boundary is already transactionally durable.

        Raises:
            SimulationError: If the run identity is absent.
        """
        if not run_id:
            raise SimulationError("SIM_PERSISTENCE_FAILED", "Run identity is invalid")

    @operation_guard(
        operation="simulation.state.runtime.finalize_journal",
        risk_level="medium",
        read_only=False,
        writes_file=True,
        modifies_database=True,
    )
    def finalize_journal(
        self,
        run_id: str,
        expected_event_count: int,
        expected_tail_hash: str,
    ) -> str:
        """Validate, atomically publish, and checksum a completed journal.

        Returns:
            SHA-256 checksum of canonical JSONL bytes.

        Raises:
            SimulationError: If journal validation or publication fails.
            ValueError: If stored journal evidence is inconsistent.
        """
        try:
            values = cast(
                "tuple[object, ...]",
                execute_runtime_store_operation(
                    self._store,
                    "list",
                    collection="journals",
                    partition=run_id,
                    limit=expected_event_count,
                ),
            )
            lines = tuple(str(value) for value in values)
            if len(lines) != expected_event_count or not lines:
                raise ValueError("journal event count does not match")
            tail = json.loads(lines[-1])
            if tail.get("event_hash") != expected_tail_hash:
                raise ValueError("journal tail hash does not match")
            payload = ("\n".join(lines) + "\n").encode()
            run_root = (self._artifact_root / run_id).resolve()
            if self._artifact_root not in run_root.parents:
                raise ValueError("journal path escapes the artifact root")
            run_root.mkdir(parents=True, exist_ok=True)
            temporary = run_root / "journal.jsonl.tmp"
            final = run_root / "journal.jsonl"
            temporary.write_bytes(payload)
            temporary.replace(final)
            return hashlib.sha256(payload).hexdigest()
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
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
        value = execute_runtime_store_operation(
            self._store,
            "get",
            collection="runs",
            key=request_id,
        )
        if value is None:
            return None
        if not isinstance(value, Mapping):
            raise SimulationError("SIM_PERSISTENCE_FAILED", "Stored run is invalid")
        return cast("Mapping[str, object]", value)

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
            ValueError: If stored lifecycle evidence is inconsistent.
        """
        try:
            existing = cast(
                "Mapping[str, object] | None",
                execute_runtime_store_operation(
                    self._store,
                    "get",
                    collection="runs",
                    key=request_id,
                ),
            )
            rank = {"started": 1, "completed": 2, "failed": 2}
            if existing is not None:
                if (
                    existing.get("request_hash") != request_hash
                    or existing.get("run_id") != run_id
                ):
                    raise SimulationError(
                        "SIM_RUN_ID_CONFLICT",
                        "Request identity conflicts with stored run",
                    )
                prior = str(existing["status"])
                if rank[status] < rank[cast("RunStatus", prior)]:
                    raise ValueError("Simulation lifecycle cannot move backwards")
                revision = int(cast("int", existing["revision"]))
            else:
                revision = 0
            value: dict[str, object] = {
                "request_id": request_id,
                "request_hash": request_hash,
                "run_id": run_id,
                "status": status,
                "result_payload": dict(result_payload or {}),
                "revision": revision + 1,
            }
            execute_runtime_store_operation(
                self._store,
                "put_once" if revision == 0 else "compare_and_swap",
                collection="runs",
                key=request_id,
                kind="run",
                value=value,
                expected_revision=revision or None,
            )
        except SimulationError:
            raise
        except (KeyError, TypeError, ValueError) as error:
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
