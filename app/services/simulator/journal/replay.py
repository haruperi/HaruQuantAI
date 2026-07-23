"""Deterministic journal replay and request-id resolution."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path
from types import MappingProxyType

from pydantic import ValidationError

from app.services.simulator.errors import SimulationError
from app.services.simulator.journal.contracts import JournalEvent
from app.utils import canonical_digest, canonical_json, logger

type JournalReducer = Callable[
    [Mapping[str, object], JournalEvent], Mapping[str, object]
]


def _parse_event_line(line: str) -> JournalEvent:
    """Parse one canonical journal line.

    Args:
        line: Candidate canonical JSON line.

    Returns:
        Validated journal event.

    Raises:
        ValueError: If the line is not canonical.
        ValidationError: If the event contract is invalid.
    """
    logger.debug("Parsing one Simulation journal replay line")
    raw = json.loads(line)
    if canonical_json(raw) != line:
        raise ValueError("journal line is not canonical")
    return JournalEvent.model_validate(raw)


def _computed_hash(event: JournalEvent) -> str:
    """Recompute an event hash from its canonical identity fields.

    Args:
        event: Journal event to verify.

    Returns:
        Lowercase recomputed digest.
    """
    logger.debug("Recomputing Simulation journal event hash")
    material = event.model_dump(mode="python", exclude={"event_hash"}, warnings=False)
    return canonical_digest(material)


def replay_journal(path: Path, reducer: JournalReducer) -> Mapping[str, object]:
    """Validate and reduce one complete canonical journal.

    Args:
        path: Explicit finalized JSONL journal path.
        reducer: Deterministic state reducer.

    Returns:
        Immutable reconstructed state.

    Raises:
        SimulationError: If reading, identity, continuity, or reduction fails.
    """
    logger.info("Replaying Simulation journal %s", path.name)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise SimulationError(
            "SIM_PERSISTENCE_FAILED", "Journal cannot be read"
        ) from error
    if not lines:
        raise SimulationError("SIM_CHECKPOINT_INCOMPATIBLE", "Journal is empty")
    state: Mapping[str, object] = MappingProxyType({})
    previous_hash = "0" * 64
    for sequence, line in enumerate(lines):
        try:
            event = _parse_event_line(line)
        except (ValueError, json.JSONDecodeError, ValidationError) as error:
            raise SimulationError(
                "SIM_CHECKPOINT_INCOMPATIBLE", "Journal event is invalid"
            ) from error
        if (
            event.sequence != sequence
            or event.previous_hash != previous_hash
            or event.event_hash != _computed_hash(event)
        ):
            raise SimulationError(
                "SIM_CHECKPOINT_INCOMPATIBLE", "Journal hash chain is broken"
            )
        if sequence == 0 and (
            event.event_type != "run_started"
            or not {"config_hash", "data_hash", "engine_version"}.issubset(
                event.payload
            )
        ):
            raise SimulationError(
                "SIM_CHECKPOINT_INCOMPATIBLE", "Run identity event is missing"
            )
        try:
            state = MappingProxyType(dict(reducer(state, event)))
        except (KeyError, TypeError, ValueError) as error:
            raise SimulationError(
                "SIM_ACCOUNT_INVARIANT_BROKEN", "Journal reducer failed"
            ) from error
        previous_hash = event.event_hash
    return state


def resolve_idempotent_run(
    request_id: str,
    request_hash: str,
    lookup: Callable[[str], Mapping[str, object] | None],
) -> str | None:
    """Resolve a completed matching run or reject identity ambiguity.

    Args:
        request_id: Request identity to resolve.
        request_hash: Canonical current request hash.
        lookup: Injected read-only request lookup.

    Returns:
        Existing completed run identity or ``None``.

    Raises:
        SimulationError: If stored request material differs.
    """
    logger.info("Resolving idempotent Simulation request %s", request_id)
    existing = lookup(request_id)
    if existing is None:
        return None
    if existing.get("request_hash") != request_hash:
        raise SimulationError(
            "SIM_RUN_ID_CONFLICT", "Request ID is bound to different material"
        )
    if existing.get("status") == "completed" and isinstance(
        existing.get("run_id"), str
    ):
        return str(existing["run_id"])
    return None


__all__ = ["replay_journal", "resolve_idempotent_run"]
