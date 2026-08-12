"""Bounded current market snapshot composition (`TC-IMP-DATA-11`).

Composes the Level-1 quote snapshot (`TC-IMP-DATA-02`) with the latest
closed bar into one bounded read intended for cross-domain consumers
(Strategy, Risk, Simulator, Analytics, UI-API). No new retrieval path is
introduced; this reuses existing bounded Data reads read-only.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

from pydantic import field_validator

from app.services.data.contracts._base import TracedOpenContract as _Contract
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
)
from app.services.data.market_data.level1 import (
    Level1Snapshot,
    Level1SnapshotRequest,
    _get_level1_snapshot_raw,
)
from app.services.data.market_data.pipeline import _fetch_market_dataset_raw
from app.services.data.market_data.requests import MarketDataRequest
from app.utils import generate_id, get_logger

if TYPE_CHECKING:
    from app.services.data.contracts.records import OHLCVRecord

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


class MarketSnapshotRequest(_Contract):
    """Bounded request for one current composed market snapshot."""

    source_id: str
    symbol: str
    timeframe: str
    request_id: str

    @field_validator("source_id", "symbol", "timeframe", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one required market snapshot request field.

        Args:
            value: The ``value`` argument.

        Returns:
            Non-empty trimmed identifier.
        """
        return _text(value)


class MarketSnapshot(_Contract):
    """Bounded current Level-1 quote plus latest closed bar for one symbol."""

    symbol: str
    level1: Level1Snapshot
    latest_bar: object | None
    generated_at: datetime
    request_id: str


def _get_market_snapshot_raw(request: MarketSnapshotRequest) -> MarketSnapshot:
    """Compose the current Level-1 snapshot and latest closed bar.

    Args:
        request: The ``request`` argument.

    Returns:
        Bounded market snapshot for one symbol.
    """
    logger.info("Composing market snapshot for %s", request.symbol)
    level1 = _get_level1_snapshot_raw(
        Level1SnapshotRequest(
            source_id=request.source_id,
            symbol=request.symbol,
            request_id=request.request_id,
        )
    )

    bar_request = MarketDataRequest(
        source_id=request.source_id,
        symbol=request.symbol,
        data_kind="bars",
        timeframe=request.timeframe,
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

    ensure_storage(bar_request.request_id)
    ensure_identity(bar_request.source_id, bar_request.symbol, bar_request.request_id)
    latest_bar: OHLCVRecord | None = None
    try:
        bar_dataset = _fetch_market_dataset_raw(bar_request)
        latest_bar = cast("OHLCVRecord", bar_dataset.records[-1])
    except Exception:  # noqa: BLE001 - a missing bar leg degrades, never fails closed here
        logger.warning(
            "No latest bar evidence available for market snapshot of %s",
            request.symbol,
        )

    return MarketSnapshot(
        symbol=request.symbol,
        level1=level1,
        latest_bar=cast("object", latest_bar),
        generated_at=datetime.now(UTC),
        request_id=request.request_id,
    )


def get_market_snapshot(
    request: MarketSnapshotRequest | None = None,
    *,
    source_id: str | None = None,
    symbol: str | None = None,
    timeframe: str | None = None,
    request_id: str | None = None,
) -> StandardResponse[MarketSnapshot]:
    """Retrieve one bounded current market snapshot for a symbol.

    Args:
        request: Typed market snapshot request.
        source_id: Direct-call source identifier (mutually exclusive with `request`).
        symbol: Direct-call symbol (mutually exclusive with `request`).
        timeframe: Direct-call bar timeframe (mutually exclusive with `request`).
        request_id: Direct-call request identifier.

    Returns:
        Standard response carrying the composed market snapshot.

    Raises:
        DataError: If neither a typed request nor the required keywords are supplied.
    """
    resolved_id = request.request_id if request is not None else request_id

    def _raw() -> MarketSnapshot:
        """Resolve and execute the market-snapshot request.

        Returns:
            The requested point-in-time market snapshot.

        Raises:
            ValueError: If required keyword inputs are absent.
        """
        if request is not None:
            resolved = request
        else:
            if source_id is None or symbol is None or timeframe is None:
                raise ValueError(
                    "source_id, symbol, and timeframe are required without a "
                    "typed request"
                )
            resolved = MarketSnapshotRequest(
                source_id=source_id,
                symbol=symbol,
                timeframe=timeframe,
                request_id=request_id if request_id is not None else generate_id("req"),
            )
        return _get_market_snapshot_raw(resolved)

    return run_data_operation(
        operation="data.market_data.get_market_snapshot",
        request_id=resolved_id,
        start_time=data_start_time(),
        raw=_raw,
    )


__all__ = ["MarketSnapshot", "MarketSnapshotRequest", "get_market_snapshot"]
