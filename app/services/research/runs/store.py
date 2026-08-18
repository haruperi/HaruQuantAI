"""Durable Research experiment, run, and batch ledger.

A Research run is expensive evidence. It outlives the process that produced it:
these functions persist the experiment, the run lifecycle, and the registered
report through Data's transaction boundary so a restart never discards a ledger
whose artifacts are still on disk.

Rows are principal-scoped. Nothing here interprets a report — the stored
projection is exactly the evidence Research already published.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from app.services.research.contracts.errors import ValidationError
from app.services.research.persistence import (
    create_research_experiment_row,
    create_research_run_batch_row,
    read_research_experiment_rows,
    read_research_run_batch_rows,
    read_research_run_rows,
    upsert_research_run_row,
)
from app.utils import get_logger

logger = get_logger(__name__)

type JsonValue = Any

#: Maximum ledger rows any single read returns.
_MAX_LEDGER_ROWS = 500


def _dumps(value: object) -> str:
    """Serialize one ledger payload as compact JSON.

    Args:
        value: JSON-safe payload.

    Returns:
        Compact JSON text.

    Raises:
        ValidationError: If the payload is not JSON-serializable.
    """
    try:
        return json.dumps(value, separators=(",", ":"), default=str)
    except (TypeError, ValueError) as error:
        raise ValidationError(
            "RES_PERSISTENCE_FAILED", "LEDGER_PAYLOAD_NOT_SERIALIZABLE"
        ) from error


def _loads(value: object) -> JsonValue:
    """Parse one stored ledger payload, tolerating an empty column.

    Args:
        value: Stored JSON text, or an empty string when absent.

    Returns:
        Parsed payload, or ``None`` when the column is empty.
    """
    text = str(value or "")
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Discarding malformed Research ledger payload")
        return None


def persist_research_experiment(
    *,
    experiment_id: str,
    principal_id: str,
    name: str,
    hypothesis: str,
    notes: str | None,
    tags: Sequence[str],
    created_at: str,
    request_id: str,
) -> None:
    """Persist one experiment ledger entry.

    Args:
        experiment_id: Stable experiment identity.
        principal_id: Owning authenticated principal.
        name: Human-readable experiment name.
        hypothesis: Explicit hypothesis under test.
        notes: Optional free-form notes.
        tags: Bounded tag list.
        created_at: ISO-8601 creation instant.
        request_id: Request trace identifier.

    Raises:
        ValidationError: If the write cannot be confirmed.
    """
    logger.info("Persisting Research experiment %s", experiment_id)
    create_research_experiment_row(
        experiment_id=experiment_id,
        principal_id=principal_id,
        name=name,
        hypothesis=hypothesis,
        notes=notes or "",
        tags_json=_dumps(list(tags)),
        created_at=created_at,
        request_id=request_id,
    )


def load_research_experiments(
    *, principal_id: str, request_id: str
) -> tuple[Mapping[str, JsonValue], ...]:
    """Return every experiment owned by one principal, newest first.

    Args:
        principal_id: Owning authenticated principal.
        request_id: Request trace identifier.

    Returns:
        Normalized experiment records with parsed tags.
    """
    rows = read_research_experiment_rows(
        principal_id=principal_id, request_id=request_id, max_rows=_MAX_LEDGER_ROWS
    )
    return tuple(
        {
            "experiment_id": str(row["experiment_id"]),
            "principal_id": str(row["principal_id"]),
            "name": str(row["name"]),
            "hypothesis": str(row["hypothesis"]),
            "notes": str(row["notes"]) or None,
            "tags": _loads(row["tags_json"]) or [],
            "created_at": str(row["created_at"]),
        }
        for row in rows
    )


def persist_research_run(
    *,
    run_id: str,
    experiment_id: str,
    principal_id: str,
    batch_id: str | None,
    status: str,
    hypothesis: str,
    symbol: str,
    timeframe: str,
    preset: str,
    selected_stages: Sequence[str],
    reason: str | None,
    force_rerun: bool,
    request_material: Mapping[str, JsonValue],
    report: Mapping[str, JsonValue] | None,
    dataset: Mapping[str, JsonValue] | None,
    effective_configuration: Mapping[str, JsonValue] | None,
    artifacts: Sequence[Mapping[str, JsonValue]],
    error: Mapping[str, JsonValue] | None,
    created_at: str,
    started_at: str | None,
    completed_at: str | None,
    request_id: str,
) -> None:
    """Persist or advance one run ledger entry.

    Args:
        run_id: Stable run identity.
        experiment_id: Owning experiment identity.
        principal_id: Owning authenticated principal.
        batch_id: Owning automation batch, when the run came from one.
        status: Current lifecycle status.
        hypothesis: Explicit hypothesis recorded on the run.
        symbol: Instrument the run analyzed.
        timeframe: Canonical timeframe key.
        preset: Server-owned preset identifier.
        selected_stages: Dependency-complete stage selection.
        reason: Optional operator-supplied run reason.
        force_rerun: Whether the caller forced a fresh run.
        request_material: JSON-safe safe-request evidence.
        report: Projected registered report, or ``None``.
        dataset: Resolved dataset identity and preview, or ``None``.
        effective_configuration: Resolved configuration evidence.
        artifacts: Persisted artifact references.
        error: Terminal failure evidence, or ``None``.
        created_at: ISO-8601 queue instant.
        started_at: ISO-8601 start instant, when started.
        completed_at: ISO-8601 terminal instant, when terminal.
        request_id: Request trace identifier.

    Raises:
        ValidationError: If the write cannot be confirmed.
    """
    logger.info("Persisting Research run %s (%s)", run_id, status)
    upsert_research_run_row(
        run_id=run_id,
        experiment_id=experiment_id,
        principal_id=principal_id,
        batch_id=batch_id or "",
        status=status,
        hypothesis=hypothesis,
        symbol=symbol,
        timeframe=timeframe,
        preset=preset,
        selected_stages_json=_dumps(list(selected_stages)),
        reason=reason or "",
        force_rerun=force_rerun,
        request_json=_dumps(dict(request_material)),
        report_json=_dumps(dict(report)) if report is not None else "",
        dataset_json=_dumps(dict(dataset)) if dataset is not None else "",
        configuration_json=(
            _dumps(dict(effective_configuration))
            if effective_configuration is not None
            else ""
        ),
        artifacts_json=_dumps([dict(item) for item in artifacts]),
        error_json=_dumps(dict(error)) if error is not None else "",
        created_at=created_at,
        started_at=started_at or "",
        completed_at=completed_at or "",
        request_id=request_id,
    )


def load_research_runs(
    *, principal_id: str, request_id: str
) -> tuple[Mapping[str, JsonValue], ...]:
    """Return every retained run owned by one principal, newest first.

    Failed and cancelled runs are returned deliberately: a ledger that keeps
    only successes is not a ledger.

    Args:
        principal_id: Owning authenticated principal.
        request_id: Request trace identifier.

    Returns:
        Normalized run records with parsed evidence payloads.
    """
    rows = read_research_run_rows(
        principal_id=principal_id, request_id=request_id, max_rows=_MAX_LEDGER_ROWS
    )
    return tuple(
        {
            "run_id": str(row["run_id"]),
            "experiment_id": str(row["experiment_id"]),
            "principal_id": str(row["principal_id"]),
            "batch_id": str(row["batch_id"]) or None,
            "status": str(row["status"]),
            "hypothesis": str(row["hypothesis"]),
            "symbol": str(row["symbol"]),
            "timeframe": str(row["timeframe"]),
            "preset": str(row["preset"]),
            "selected_stages": _loads(row["selected_stages_json"]) or [],
            "reason": str(row["reason"]) or None,
            "force_rerun": bool(row["force_rerun"]),
            "request": _loads(row["request_json"]) or {},
            "report": _loads(row["report_json"]),
            "dataset": _loads(row["dataset_json"]),
            "effective_configuration": _loads(row["configuration_json"]),
            "artifacts": _loads(row["artifacts_json"]) or [],
            "error": _loads(row["error_json"]),
            "created_at": str(row["created_at"]),
            "started_at": str(row["started_at"]) or None,
            "completed_at": str(row["completed_at"]) or None,
        }
        for row in rows
    )


def persist_research_run_batch(
    *,
    batch_id: str,
    experiment_id: str,
    principal_id: str,
    symbols: Sequence[str],
    trigger: str,
    reason: str | None,
    request_material: Mapping[str, JsonValue],
    rejections: Sequence[Mapping[str, JsonValue]],
    created_at: str,
    request_id: str,
) -> None:
    """Persist one automation batch record.

    Args:
        batch_id: Stable batch identity.
        experiment_id: Owning experiment identity.
        principal_id: Owning authenticated principal.
        symbols: Requested symbol universe.
        trigger: Batch trigger kind.
        reason: Optional operator-supplied reason.
        request_material: JSON-safe request evidence.
        rejections: Symbols the gateway refused to queue.
        created_at: ISO-8601 creation instant.
        request_id: Request trace identifier.

    Raises:
        ValidationError: If the write cannot be confirmed.
    """
    logger.info("Persisting Research batch %s", batch_id)
    create_research_run_batch_row(
        batch_id=batch_id,
        experiment_id=experiment_id,
        principal_id=principal_id,
        symbols_json=_dumps(list(symbols)),
        trigger=trigger,
        reason=reason or "",
        request_json=_dumps(dict(request_material)),
        rejections_json=_dumps([dict(item) for item in rejections]),
        created_at=created_at,
        request_id=request_id,
    )


def load_research_run_batches(
    *, principal_id: str, request_id: str
) -> tuple[Mapping[str, JsonValue], ...]:
    """Return every automation batch owned by one principal, newest first.

    Args:
        principal_id: Owning authenticated principal.
        request_id: Request trace identifier.

    Returns:
        Normalized batch records with parsed payloads.
    """
    rows = read_research_run_batch_rows(
        principal_id=principal_id, request_id=request_id, max_rows=_MAX_LEDGER_ROWS
    )
    return tuple(
        {
            "batch_id": str(row["batch_id"]),
            "experiment_id": str(row["experiment_id"]),
            "principal_id": str(row["principal_id"]),
            "symbols": _loads(row["symbols_json"]) or [],
            "trigger": str(row["trigger"]),
            "reason": str(row["reason"]) or None,
            "request": _loads(row["request_json"]) or {},
            "rejections": _loads(row["rejections_json"]) or [],
            "created_at": str(row["created_at"]),
        }
        for row in rows
    )


__all__ = (
    "load_research_experiments",
    "load_research_run_batches",
    "load_research_runs",
    "persist_research_experiment",
    "persist_research_run",
    "persist_research_run_batch",
)
