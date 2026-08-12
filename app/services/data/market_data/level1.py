"""Bounded Level-1 quote snapshot construction and retrieval.

Trading Cockpit Phase 0 reconciliation (`TC-IMP-DATA-02`): extends
`market_data/` with a bid/ask/last/spread/volume snapshot that discloses
source (event) time, receive time, and computed quote freshness instead of
returning raw tick evidence alone.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, cast

from pydantic import field_validator

from app.services.data.contracts._base import TracedOpenContract as _Contract
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
)
from app.services.data.market_data.pipeline import _fetch_market_dataset_raw
from app.services.data.market_data.requests import MarketDataRequest
from app.utils import generate_id, get_logger

if TYPE_CHECKING:
    from app.services.data.contracts.records import TickRecord

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


class Level1SnapshotRequest(_Contract):
    """Bounded request for one current Level-1 quote snapshot."""

    source_id: str
    symbol: str
    request_id: str

    @field_validator("source_id", "symbol", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one required Level-1 snapshot request field.

        Args:
            value: The ``value`` argument.

        Returns:
            Non-empty trimmed identifier.
        """
        return _text(value)


class Level1Snapshot(_Contract):
    """Bounded current bid/ask/last/spread/volume evidence with freshness."""

    symbol: str
    bid: Decimal | None
    ask: Decimal | None
    last: Decimal | None
    spread: Decimal | None
    volume: Decimal | None
    price_unit: str
    source_time: datetime
    receive_time: datetime
    quote_age_seconds: float
    request_id: str


def _level1_snapshot_request(
    request: Level1SnapshotRequest | None,
    *,
    source_id: str | None,
    symbol: str | None,
    request_id: str | None,
) -> Level1SnapshotRequest:
    """Return a typed Level-1 snapshot request from either call style.

    Args:
        request: The ``request`` argument.
        source_id: The ``source_id`` argument.
        symbol: The ``symbol`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        Validated Level-1 snapshot request.

    Raises:
        ValueError: If neither a request nor the required keywords are supplied.
    """
    if request is not None:
        return request
    trace_id = request_id if request_id is not None else generate_id("req")
    if source_id is None or symbol is None:
        raise ValueError("source_id and symbol are required without a typed request")
    return Level1SnapshotRequest(
        source_id=source_id, symbol=symbol, request_id=trace_id
    )


def _get_level1_snapshot_raw(request: Level1SnapshotRequest) -> Level1Snapshot:
    """Compose the latest tick evidence into one bounded Level-1 snapshot.

    Args:
        request: The ``request`` argument.

    Returns:
        Current bid/ask/last/spread/volume snapshot with disclosed freshness.
    """
    logger.info("Composing Level-1 snapshot for %s", request.symbol)
    tick_request = MarketDataRequest(
        source_id=request.source_id,
        symbol=request.symbol,
        data_kind="ticks",
        timeframe=None,
        start=None,
        end=None,
        limit=1,
        use_cache=False,
        cache_ttl_seconds=None,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        stale_cache_policy="refresh",
        fallback_sources=(),
        source_timezone="UTC",
        request_id=request.request_id,
    )
    from app.services.data.sources.composition import ensure_identity, ensure_storage

    ensure_storage(tick_request.request_id)
    ensure_identity(
        tick_request.source_id, tick_request.symbol, tick_request.request_id
    )
    dataset = _fetch_market_dataset_raw(tick_request)
    latest = cast("TickRecord", dataset.records[-1])
    bid = latest.bid
    ask = latest.ask
    spread = ask - bid if bid is not None and ask is not None else None
    receive_time = dataset.available_at
    now = datetime.now(UTC)
    return Level1Snapshot(
        symbol=request.symbol,
        bid=bid,
        ask=ask,
        last=latest.last,
        spread=spread,
        volume=latest.volume,
        price_unit=latest.price_unit,
        source_time=latest.timestamp,
        receive_time=receive_time,
        quote_age_seconds=max((now - receive_time).total_seconds(), 0.0),
        request_id=request.request_id,
    )


def get_level1_snapshot(
    request: Level1SnapshotRequest | None = None,
    *,
    source_id: str | None = None,
    symbol: str | None = None,
    request_id: str | None = None,
) -> StandardResponse[Level1Snapshot]:
    """Retrieve one current bounded Level-1 quote snapshot.

    Args:
        request: The ``request`` argument.
        source_id: The ``source_id`` argument.
        symbol: The ``symbol`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        Standard response carrying the Level-1 snapshot.
    """
    resolved_id = request.request_id if request is not None else request_id

    def _raw() -> Level1Snapshot:
        """Implement raw behavior.

        Returns:
            The result produced by the operation.
        """
        resolved = _level1_snapshot_request(
            request, source_id=source_id, symbol=symbol, request_id=request_id
        )
        return _get_level1_snapshot_raw(resolved)

    return run_data_operation(
        operation="data.market_data.get_level1_snapshot",
        request_id=resolved_id,
        start_time=data_start_time(),
        raw=_raw,
    )


__all__ = [
    "Level1Snapshot",
    "Level1SnapshotRequest",
    "get_level1_snapshot",
]
