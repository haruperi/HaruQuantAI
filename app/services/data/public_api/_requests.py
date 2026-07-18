"""Private request construction for the Data package-root facade."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Literal

from app.services.data.contracts import (
    AvailabilityRequest,
    MarketDataRequest,
    ScheduleRequest,
    SymbolListRequest,
    SymbolMetadataRequest,
    VolumeRequest,
)
from app.services.data.contracts.errors import DataError
from app.utils import generate_id

if TYPE_CHECKING:
    from app.services.data.contracts.market import PrecisionPolicy
    from app.services.data.contracts.sources import WorkflowContext


def _request_id(value: str | None) -> str:
    """Return an explicit request ID or generate one for a direct call."""
    return value if value is not None else generate_id("req")


def _required(value: str | None, field: str, request_id: str) -> str:
    """Return a required direct-call value.

    Raises:
        DataError: If the required value is absent.
    """
    if value is None:
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"field": field},
            request_id=request_id,
        )
    return value


def _reject_mixed(
    request: object | None,
    values: tuple[object | None, ...],
    request_id: str,
) -> None:
    """Reject combining a typed request with direct keyword arguments.

    Raises:
        DataError: If both call styles are mixed.
    """
    if request is not None and any(value is not None for value in values):
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"message": "request objects cannot be mixed with keywords"},
            request_id=request_id,
        )


def market_request(
    request: MarketDataRequest | None,
    *,
    data_kind: Literal["bars", "ticks", "spreads"] | None,
    source_id: str | None,
    symbol: str | None,
    timeframe: str | None,
    start: datetime | None,
    end: datetime | None,
    limit: int | None,
    use_cache: bool | None,
    cache_ttl_seconds: int | None,
    quality_failure_behavior: Literal["fail", "warn"] | None,
    workflow_context: WorkflowContext | None,
    precision_policy: PrecisionPolicy | None,
    fallback_sources: tuple[str, ...] | None,
    source_timezone: str | None,
    request_id: str | None,
) -> MarketDataRequest:
    """Return a typed market request from either supported call style.

    Raises:
        DataError: If call styles are mixed or the requested kind is invalid.
    """
    trace_id = request.request_id if request is not None else _request_id(request_id)
    _reject_mixed(
        request,
        (
            source_id,
            symbol,
            timeframe,
            start,
            end,
            limit,
            use_cache,
            cache_ttl_seconds,
            quality_failure_behavior,
            workflow_context,
            precision_policy,
            fallback_sources,
            source_timezone,
            request_id,
        ),
        trace_id,
    )
    if request is not None:
        if data_kind is not None and request.data_kind != data_kind:
            operation = {
                "ticks": "get_tick_data",
                "spreads": "get_spread_data",
            }[data_kind]
            required_kind = data_kind.removesuffix("s")
            raise DataError(
                "VALIDATION_FAILED",
                safe_details={
                    "message": (
                        f"{operation} requires {required_kind} data_kind, "
                        f"got '{request.data_kind}'"
                    )
                },
                request_id=request.request_id,
            )
        return request
    return MarketDataRequest(
        source_id=_required(source_id, "source_id", trace_id),
        symbol=_required(symbol, "symbol", trace_id),
        data_kind=data_kind or "bars",
        timeframe=timeframe,
        start=start,
        end=end,
        limit=10 if limit is None else limit,
        use_cache=False if use_cache is None else use_cache,
        cache_ttl_seconds=cache_ttl_seconds,
        quality_failure_behavior=quality_failure_behavior or "fail",
        workflow_context=workflow_context or "research",
        precision_policy=precision_policy or "decimal_string",
        fallback_sources=fallback_sources or (),
        source_timezone=source_timezone,
        request_id=trace_id,
    )


def symbol_metadata_request(
    request: SymbolMetadataRequest | None,
    *,
    source_id: str | None,
    symbol: str | None,
    request_id: str | None,
) -> SymbolMetadataRequest:
    """Return a typed symbol-metadata request."""
    trace_id = request.request_id if request is not None else _request_id(request_id)
    _reject_mixed(request, (source_id, symbol, request_id), trace_id)
    if request is not None:
        return request
    return SymbolMetadataRequest(
        source_id=_required(source_id, "source_id", trace_id),
        symbol=_required(symbol, "symbol", trace_id),
        request_id=trace_id,
    )


def symbol_list_request(
    request: SymbolListRequest | None,
    *,
    source_id: str | None,
    query: str | None,
    cursor: str | None,
    limit: int | None,
    request_id: str | None,
) -> SymbolListRequest:
    """Return a typed symbol-list request."""
    trace_id = request.request_id if request is not None else _request_id(request_id)
    _reject_mixed(
        request,
        (source_id, query, cursor, limit, request_id),
        trace_id,
    )
    if request is not None:
        return request
    return SymbolListRequest(
        source_id=_required(source_id, "source_id", trace_id),
        query=query,
        cursor=cursor,
        limit=100 if limit is None else limit,
        request_id=trace_id,
    )


def availability_request(
    request: AvailabilityRequest | None,
    *,
    source_id: str | None,
    symbol: str | None,
    data_kind: Literal["ohlcv", "tick", "spread"] | None,
    timeframe: str | None,
    start: datetime | None,
    end: datetime | None,
    max_probe_records: int | None,
    request_id: str | None,
) -> AvailabilityRequest:
    """Return a typed availability request."""
    trace_id = request.request_id if request is not None else _request_id(request_id)
    _reject_mixed(
        request,
        (
            source_id,
            symbol,
            data_kind,
            timeframe,
            start,
            end,
            max_probe_records,
            request_id,
        ),
        trace_id,
    )
    if request is not None:
        return request
    return AvailabilityRequest(
        source_id=_required(source_id, "source_id", trace_id),
        symbol=_required(symbol, "symbol", trace_id),
        data_kind=data_kind or "ohlcv",
        timeframe=timeframe,
        start=start,
        end=end,
        max_probe_records=(1_000 if max_probe_records is None else max_probe_records),
        request_id=trace_id,
    )


def schedule_request(
    request: ScheduleRequest | None,
    *,
    view: Literal["hours", "sessions"],
    source_id: str | None,
    symbol: str | None,
    timezone: str | None,
    request_id: str | None,
) -> ScheduleRequest:
    """Return a typed schedule request for one facade operation.

    Raises:
        DataError: If call styles are mixed or the request view is invalid.
    """
    trace_id = request.request_id if request is not None else _request_id(request_id)
    _reject_mixed(
        request,
        (source_id, symbol, timezone, request_id),
        trace_id,
    )
    if request is not None:
        if request.view != view:
            operation = (
                "get_market_hours" if view == "hours" else "get_trading_sessions"
            )
            raise DataError(
                "VALIDATION_FAILED",
                safe_details={
                    "message": (
                        f"{operation} requires {view} view, got '{request.view}'"
                    )
                },
                request_id=request.request_id,
            )
        return request
    return ScheduleRequest(
        source_id=_required(source_id, "source_id", trace_id),
        symbol=_required(symbol, "symbol", trace_id),
        view=view,
        timezone=timezone or "UTC",
        request_id=trace_id,
    )


def volume_request(
    request: VolumeRequest | None,
    *,
    source_id: str | None,
    symbol: str | None,
    start: datetime | None,
    end: datetime | None,
    mode: Literal["records", "buckets", "summary"] | None,
    bucket_seconds: int | None,
    limit: int | None,
    request_id: str | None,
) -> VolumeRequest:
    """Return a typed historical-volume request.

    Raises:
        DataError: If call styles are mixed or the required range is absent.
    """
    trace_id = request.request_id if request is not None else _request_id(request_id)
    _reject_mixed(
        request,
        (
            source_id,
            symbol,
            start,
            end,
            mode,
            bucket_seconds,
            limit,
            request_id,
        ),
        trace_id,
    )
    if request is not None:
        return request
    if start is None or end is None:
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"field": "start/end"},
            request_id=trace_id,
        )
    return VolumeRequest(
        source_id=_required(source_id, "source_id", trace_id),
        symbol=_required(symbol, "symbol", trace_id),
        start=start,
        end=end,
        mode=mode or "summary",
        bucket_seconds=bucket_seconds,
        limit=10 if limit is None else limit,
        request_id=trace_id,
    )


__all__ = [
    "availability_request",
    "market_request",
    "schedule_request",
    "symbol_list_request",
    "symbol_metadata_request",
    "volume_request",
]
