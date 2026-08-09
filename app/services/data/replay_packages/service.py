"""Deterministic no-lookahead replay streaming (`TC-IMP-DATA-08`, `FEAT-DATA-19`)."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from datetime import datetime, timedelta
from typing import Any, cast

from app.services.data.market_data.pipeline import _fetch_market_dataset_raw
from app.services.data.market_data.requests import MarketDataRequest
from app.services.data.replay_packages.contracts import ReplayEvent, ReplayPackage
from app.utils import get_logger

logger = get_logger(__name__)

_REPLAY_MAX_RECORDS = 50_000


def build_replay_package(**values: object) -> ReplayPackage:
    """Build one validated replay package from direct keyword arguments.

    Returns:
        Immutable replay package accepted by :func:`stream_replay_events`.
    """
    return ReplayPackage.model_validate(values)


def parse_replay_package(mapping: Mapping[str, object]) -> ReplayPackage:
    """Parse one validated replay package from a JSON-safe mapping.

    Args:
        mapping: Previously serialized replay-package mapping (D-1 contract
            transport).

    Returns:
        Immutable replay package accepted by :func:`stream_replay_events`.
    """
    return ReplayPackage.model_validate(dict(mapping))


def _collect_records(package: ReplayPackage) -> list[tuple[datetime, str, object]]:
    """Retrieve every bounded record the package covers, unordered.

    Returns:
        Every ``(available_at, symbol, record)`` triple visible from any
        covered symbol, before deterministic ordering and `as_of` filtering.
    """
    from app.services.data.sources.composition import ensure_identity, ensure_storage

    collected: list[tuple[datetime, str, object]] = []
    for symbol in package.symbols:
        request = MarketDataRequest(
            source_id=package.source_id,
            symbol=symbol,
            data_kind=package.data_kind,
            timeframe=package.timeframe,
            start=package.start,
            end=package.end,
            limit=_REPLAY_MAX_RECORDS,
            use_cache=False,
            cache_ttl_seconds=None,
            quality_failure_behavior="warn",
            workflow_context="research",
            precision_policy="decimal_string",
            stale_cache_policy="refresh",
            fallback_sources=(),
            source_timezone="UTC",
            request_id=package.request_id,
        )
        ensure_storage(request.request_id)
        ensure_identity(request.source_id, request.symbol, request.request_id)
        dataset = _fetch_market_dataset_raw(request)
        collected.extend(
            (record.available_at, symbol, record) for record in dataset.records
        )
    return collected


def stream_replay_events(
    package: ReplayPackage,
    *,
    as_of: datetime,
) -> Iterator[ReplayEvent]:
    """Stream replay events in deterministic source order with no future visibility.

    Replay evidence is a bounded historical retrieval, not a live feed, so
    this is a synchronous generator: the underlying Data retrieval already
    manages its own thread/event-loop boundary for broker calls, and
    wrapping it in an `async def` here would nest event loops.

    `as_of` is required and never defaulted to a wall-clock "now" — it is the
    fail-closed consumer port standing in for Simulator's not-yet-built
    `SimulationClock` (`TC-IMP-SIM-01`). Only events whose evidence was
    already available at `as_of` are ever yielded.

    Args:
        package: Bounded declaration of what evidence to replay.
        as_of: Caller-supplied UTC boundary; no event beyond it is visible.

    Yields:
        Ordered `ReplayEvent` values, sorted by `(available_at, symbol)` for
        a deterministic source order across symbols.

    Raises:
        DataError: If `as_of` is not timezone-aware UTC or the package's
            declared source/symbols cannot be retrieved.
    """
    if as_of.tzinfo is None or as_of.utcoffset() != timedelta(0):
        raise ValueError("as_of must be timezone-aware UTC")
    logger.info(
        "Streaming replay package %s for %d symbol(s) as_of=%s",
        package.request_id,
        len(package.symbols),
        as_of.isoformat(),
    )
    records = _collect_records(package)
    visible = [item for item in records if item[0] <= as_of]
    visible.sort(key=lambda item: (item[0], item[1]))
    for sequence, (available_at, symbol, record) in enumerate(visible):
        yield ReplayEvent(
            sequence=sequence,
            symbol=symbol,
            available_at=available_at,
            record=cast("Any", record),
        )


__all__ = ["build_replay_package", "parse_replay_package", "stream_replay_events"]
