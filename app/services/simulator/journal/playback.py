"""Validated streaming reads for finalized Simulation journals."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ValidationError

from app.composition.logging import get_logger
from app.services.simulator.errors import SimulationError
from app.services.simulator.journal.replay import _computed_hash, _parse_event_line

if TYPE_CHECKING:
    from app.services.simulator.journal.contracts import JournalEvent

logger = get_logger(__name__)

_GENESIS_HASH = "0" * 64
_RUN_IDENTITY_FIELDS = frozenset({"config_hash", "data_hash", "engine_version"})


def _line(raw_line: str) -> str:
    """Remove one JSONL newline without accepting other trailing bytes.

    Args:
        raw_line: One physical journal line.

    Returns:
        Canonical event JSON without its line terminator.
    """
    if raw_line.endswith("\r\n"):
        return raw_line[:-2]
    return raw_line.removesuffix("\n")


def _validate_event(
    event: JournalEvent,
    *,
    run_id: str,
    sequence: int,
    previous_hash: str,
) -> None:
    """Validate one event's identity and chain position.

    Args:
        event: Parsed canonical journal event.
        run_id: Expected owner run identity.
        sequence: Expected zero-based sequence.
        previous_hash: Expected predecessor digest.

    Raises:
        ValueError: If identity, continuity, or initial evidence is invalid.
    """
    if (
        event.run_id != run_id
        or event.sequence != sequence
        or event.previous_hash != previous_hash
        or event.event_hash != _computed_hash(event)
    ):
        raise ValueError("journal hash chain is broken")
    if sequence == 0 and (
        event.event_type != "run_started"
        or not _RUN_IDENTITY_FIELDS.issubset(event.payload)
    ):
        raise ValueError("run identity event is missing")


def _validate_journal(path: Path, run_id: str) -> int:
    """Validate a complete finalized journal with bounded memory.

    Args:
        path: Finalized canonical JSONL path.
        run_id: Expected owner run identity.

    Returns:
        Final journal sequence.

    Raises:
        SimulationError: If the journal is unavailable or invalid.
    """
    logger.info("Validating finalized Simulation journal for playback")
    previous_hash = _GENESIS_HASH
    count = 0
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            for sequence, raw_line in enumerate(handle):
                event = _parse_event_line(_line(raw_line))
                _validate_event(
                    event,
                    run_id=run_id,
                    sequence=sequence,
                    previous_hash=previous_hash,
                )
                previous_hash = event.event_hash
                count += 1
    except OSError as error:
        raise SimulationError(
            "SIM_PERSISTENCE_FAILED", "Finalized journal cannot be read"
        ) from error
    except (TypeError, ValueError, ValidationError) as error:
        raise SimulationError(
            "SIM_CHECKPOINT_INCOMPATIBLE", "Journal event is invalid"
        ) from error
    if count == 0:
        raise SimulationError("SIM_CHECKPOINT_INCOMPATIBLE", "Journal is empty")
    return count - 1


async def stream_journal_events(
    path: Path,
    run_id: str,
    *,
    resume_after: int,
) -> AsyncIterator[JournalEvent]:
    """Yield validated journal events after one sequence cursor.

    The first pass validates the complete hash chain before the second pass emits
    any frame. This doubles sequential file reads but keeps memory usage constant.

    Args:
        path: Finalized canonical JSONL path.
        run_id: Expected owner run identity.
        resume_after: Last sequence already observed, or ``-1`` for the beginning.

    Yields:
        Ordered immutable journal events after ``resume_after``.

    Raises:
        SimulationError: If the cursor or journal is invalid.
    """
    if resume_after < -1:
        raise SimulationError(
            "SIM_PLAYBACK_CURSOR_INVALID", "Playback cursor is invalid"
        )
    final_sequence = _validate_journal(path, run_id)
    if resume_after > final_sequence:
        raise SimulationError(
            "SIM_PLAYBACK_CURSOR_INVALID", "Playback cursor exceeds the journal"
        )
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            for raw_line in handle:
                event = _parse_event_line(_line(raw_line))
                if event.sequence > resume_after:
                    yield event
    except OSError as error:
        raise SimulationError(
            "SIM_PERSISTENCE_FAILED", "Finalized journal cannot be read"
        ) from error


__all__ = ["stream_journal_events"]
