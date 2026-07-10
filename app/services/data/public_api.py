"""Official read-only AI-tool wrappers for the market data service boundary.

This module wraps existing native Data functions (`gateway.get_data`,
`gateway.list_symbols`, `validation.get_market_hours`, and
`scheduler.get_feed_status`) with the shared HaruQuant standard tool
envelope. Native functions are unchanged and keep returning their current
native values for existing internal callers; these wrappers are additive.
"""

import time
from typing import Any

from app.services.data.errors import to_data_error_payload
from app.services.data.gateway import get_data_with_metadata, list_symbols
from app.services.data.scheduler import get_feed_status
from app.services.data.validation import get_market_hours
from app.utils.logger import logger
from app.utils.standard import (
    StandardResponse,
    build_metadata,
    error_response,
    success_response,
)

TOOL_VERSION: str = "1.0.0"
TOOL_CATEGORY: str = "data"


def get_data_tool(
    symbol: str,
    start_time: str,
    end_time: str,
    data_kind: str = "ohlcv",
    timeframe: str | None = None,
    source: str = "csv",
    limit: int | None = None,
    stale_data_behavior: str = "refresh_and_return",
    workflow_context: str = "research",
    *,
    request_id: str | None = None,
) -> StandardResponse:
    """Retrieve normalized market data records as a standard tool envelope.

    Official read-only wrapper around `gateway.get_data`. No raw exception
    ever reaches this boundary; failures are mapped to a deterministic error
    envelope.

    Args:
        symbol: Financial symbol identifier.
        start_time: UTC start time string.
        end_time: UTC end time string.
        data_kind: Kind of data ('ohlcv', 'ticks', 'spreads', 'volume').
        timeframe: Bar timeframe (required for ohlcv/volume).
        source: Primary source adapter.
        limit: Max query limit parameter.
        stale_data_behavior: Expired cache lookup policy.
        workflow_context: Rounding/validation execution context.
        request_id: Optional trace identifier.

    Returns:
        StandardResponse: Success envelope with `records` and
        `result_metadata`, or a deterministic error envelope.
    """
    logger.info(
        f"get_data_tool invoked: symbol={symbol} source={source} kind={data_kind}",
        extra={"request_id": request_id},
    )
    start = time.perf_counter()
    meta = build_metadata(
        tool_name="get_data_tool",
        tool_category=TOOL_CATEGORY,
        tool_version=TOOL_VERSION,
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
        start_time=start,
    )
    try:
        records, result_metadata = get_data_with_metadata(
            symbol=symbol,
            start_time=start_time,
            end_time=end_time,
            data_kind=data_kind,
            timeframe=timeframe,
            source=source,
            limit=limit,
            stale_data_behavior=stale_data_behavior,
            workflow_context=workflow_context,
            request_id=request_id,
        )
        logger.info(
            f"get_data_tool succeeded: record_count={len(records)}",
            extra={"request_id": request_id},
        )
        return success_response(
            message=f"Retrieved {len(records)} {data_kind} record(s).",
            data={"records": records, "result_metadata": result_metadata},
            metadata=meta,
        )
    except Exception as exc:  # noqa: BLE001
        payload = to_data_error_payload(exc, request_id=request_id)
        logger.warning(
            f"get_data_tool failed: code={payload['code']}",
            extra={"request_id": request_id},
        )
        return error_response(
            message="get_data_tool failed.",
            code=payload["code"],
            details=payload["details"],
            metadata=meta,
        )


def list_symbols_tool(
    source: str = "csv",
    *,
    request_id: str | None = None,
) -> StandardResponse:
    """List symbols discovered from a source as a standard tool envelope.

    Official read-only wrapper around `gateway.list_symbols`.

    Args:
        source: Source adapter identifier.
        request_id: Optional trace identifier.

    Returns:
        StandardResponse: Success envelope with `symbols`, or a deterministic
        error envelope.
    """
    logger.info(
        f"list_symbols_tool invoked: source={source}",
        extra={"request_id": request_id},
    )
    start = time.perf_counter()
    meta = build_metadata(
        tool_name="list_symbols_tool",
        tool_category=TOOL_CATEGORY,
        tool_version=TOOL_VERSION,
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
        start_time=start,
    )
    try:
        symbols = list_symbols(source=source, request_id=request_id)
        logger.info(
            f"list_symbols_tool succeeded: symbol_count={len(symbols)}",
            extra={"request_id": request_id},
        )
        return success_response(
            message=f"Discovered {len(symbols)} symbol(s) for source '{source}'.",
            data={"source": source, "symbols": symbols},
            metadata=meta,
        )
    except Exception as exc:  # noqa: BLE001
        payload = to_data_error_payload(exc, request_id=request_id)
        logger.warning(
            f"list_symbols_tool failed: code={payload['code']}",
            extra={"request_id": request_id},
        )
        return error_response(
            message="list_symbols_tool failed.",
            code=payload["code"],
            details=payload["details"],
            metadata=meta,
        )


def get_market_hours_tool(
    symbol: str,
    *,
    request_id: str | None = None,
) -> StandardResponse:
    """Retrieve current-hours market schedule as a standard tool envelope.

    Official read-only wrapper around `validation.get_market_hours`. Only
    current configured hours are supported; historical market-hour
    reconstruction is disclosed as unsupported via
    `historical_hours_supported=False` in the underlying payload.

    Args:
        symbol: Financial symbol identifier.
        request_id: Optional trace identifier.

    Returns:
        StandardResponse: Success envelope with market hours, or a
        deterministic error envelope.
    """
    logger.info(
        f"get_market_hours_tool invoked: symbol={symbol}",
        extra={"request_id": request_id},
    )
    start = time.perf_counter()
    meta = build_metadata(
        tool_name="get_market_hours_tool",
        tool_category=TOOL_CATEGORY,
        tool_version=TOOL_VERSION,
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
        start_time=start,
    )
    try:
        hours = get_market_hours(symbol, request_id=request_id)
        logger.info(
            "get_market_hours_tool succeeded.",
            extra={"request_id": request_id},
        )
        return success_response(
            message=f"Retrieved market hours for {symbol}.",
            data=hours,
            metadata=meta,
        )
    except Exception as exc:  # noqa: BLE001
        payload = to_data_error_payload(exc, request_id=request_id)
        logger.warning(
            f"get_market_hours_tool failed: code={payload['code']}",
            extra={"request_id": request_id},
        )
        return error_response(
            message="get_market_hours_tool failed.",
            code=payload["code"],
            details=payload["details"],
            metadata=meta,
        )


def get_feed_status_tool(
    feed_id: str | None = None,
    source: str | None = None,
    symbol: str | None = None,
    data_kind: str | None = None,
    *,
    request_id: str | None = None,
) -> StandardResponse:
    """Retrieve read-only real-time feed observability as a standard envelope.

    Official read-only wrapper around `scheduler.get_feed_status`. Never
    returns raw sockets, SDK objects, clients, or credential-bearing
    connection strings.

    Args:
        feed_id: Optional specific feed identifier.
        source: Optional source filter.
        symbol: Optional symbol filter.
        data_kind: Optional data-kind filter.
        request_id: Optional trace identifier.

    Returns:
        StandardResponse: Success envelope with `feeds`, or a deterministic
        error envelope.
    """
    logger.info(
        f"get_feed_status_tool invoked: feed_id={feed_id} source={source}",
        extra={"request_id": request_id},
    )
    start = time.perf_counter()
    meta = build_metadata(
        tool_name="get_feed_status_tool",
        tool_category=TOOL_CATEGORY,
        tool_version=TOOL_VERSION,
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
        start_time=start,
    )
    try:
        result = get_feed_status(
            feed_id=feed_id,
            source=source,
            symbol=symbol,
            data_kind=data_kind,
            request_id=request_id,
        )
        feeds: list[dict[str, Any]] = result if isinstance(result, list) else [result]
        logger.info(
            f"get_feed_status_tool succeeded: feed_count={len(feeds)}",
            extra={"request_id": request_id},
        )
        return success_response(
            message=f"Retrieved status for {len(feeds)} feed(s).",
            data={"feeds": feeds},
            metadata=meta,
        )
    except Exception as exc:  # noqa: BLE001
        payload = to_data_error_payload(exc, request_id=request_id)
        logger.warning(
            f"get_feed_status_tool failed: code={payload['code']}",
            extra={"request_id": request_id},
        )
        return error_response(
            message="get_feed_status_tool failed.",
            code=payload["code"],
            details=payload["details"],
            metadata=meta,
        )
