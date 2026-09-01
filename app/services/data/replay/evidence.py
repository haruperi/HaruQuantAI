"""Bounded point-in-time replay evidence export (`TC-IMP-DATA-13`).

Reconstructs the exact bounded evidence a player decision or automated
action could have seen at a given instant, by composing the deterministic
no-lookahead replay stream (`TC-IMP-DATA-08`). No new retrieval path is
introduced and no evidence beyond `as_of` is ever included.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import field_validator

from app.composition.logging import get_logger
from app.services.data.contracts._base import TracedOpenContract as _Contract
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
)
from app.services.data.replay.contracts import ReplayEvent, ReplayPackage
from app.services.data.replay.packages import stream_replay_events

logger = get_logger(__name__)


def _text(value: str) -> str:
    """Execute one private DATA operation.

    Args:
        value: The ``value`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        ValueError: If the operation cannot be completed safely.
    """
    if not value or value != value.strip():
        raise ValueError("value must be a non-empty trimmed string")
    return value


class ReplayEvidenceRequest(_Contract):
    """Bounded request for one point-in-time replay evidence export."""

    source_id: str
    symbols: tuple[str, ...]
    data_kind: Literal["bars", "ticks", "spreads"]
    timeframe: str | None = None
    start: datetime
    end: datetime
    as_of: datetime
    request_id: str

    @field_validator("source_id", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one required export request field.

        Args:
            value: The ``value`` argument.

        Returns:
            Non-empty trimmed identifier.
        """
        return _text(value)


class ReplayEvidenceExport(_Contract):
    """The exact bounded evidence set visible at one `as_of` instant."""

    symbols: tuple[str, ...]
    as_of: datetime
    events: tuple[ReplayEvent, ...]
    event_count: int


def _export_replay_evidence_raw(
    request: ReplayEvidenceRequest,
) -> ReplayEvidenceExport:
    """Reconstruct the exact bounded evidence set visible at `as_of`.

    Args:
        request: The ``request`` argument.

    Returns:
        Ordered, no-lookahead evidence export for the requested symbols.
    """
    logger.info(
        "Exporting replay evidence for %d symbol(s) as_of=%s",
        len(request.symbols),
        request.as_of.isoformat(),
    )
    package = ReplayPackage(
        source_id=request.source_id,
        symbols=request.symbols,
        data_kind=request.data_kind,
        timeframe=request.timeframe,
        start=request.start,
        end=request.end,
        request_id=request.request_id,
    )
    events = tuple(stream_replay_events(package, as_of=request.as_of))
    return ReplayEvidenceExport(
        symbols=request.symbols,
        as_of=request.as_of,
        events=events,
        event_count=len(events),
    )


def export_replay_evidence(
    request: ReplayEvidenceRequest,
) -> StandardResponse[ReplayEvidenceExport]:
    """Retrieve the exact bounded evidence set visible at one instant.

    Args:
        request: Bounded replay-evidence export request.

    Returns:
        Standard response carrying the reconstructed evidence export.

    Raises:
        (in-band) ``VALIDATION_FAILED`` if `as_of` is not timezone-aware UTC
        or the declared source/symbols cannot be retrieved.
    """
    return run_data_operation(
        operation="data.market_data.export_replay_evidence",
        request_id=request.request_id,
        start_time=data_start_time(),
        raw=lambda: _export_replay_evidence_raw(request),
    )


__all__ = [
    "ReplayEvidenceExport",
    "ReplayEvidenceRequest",
    "export_replay_evidence",
]
