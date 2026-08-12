"""Markets source, Data evidence, and Indicators orchestration."""

from __future__ import annotations

import threading
import time
from datetime import UTC, datetime, timedelta
from types import MappingProxyType
from typing import Final

from app.services.api.identity import get_system_settings
from app.services.api.workstation.markets.schemas import build_gateway_response
from app.services.data import (
    build_market_data_request,
    build_market_directory_request,
    build_symbol_metadata_request,
    build_symbols_quote_request,
    get_market_data,
    get_symbol_metadata,
    get_symbols_quotes,
    list_market_directory,
)
from app.services.indicators import project_market_overlay
from app.utils import generate_id, get_logger

logger = get_logger(__name__)

_HISTORY_DAYS: Final = 40
_CACHE_TTL_SECONDS: Final = 300.0
_cache_lock: Final = threading.Lock()
_cache: dict[tuple[str, str, float | None], tuple[float, dict[str, float | None]]] = {}

_BROKER_TO_SOURCE: Final = MappingProxyType(
    {
        "mt5": "mt5",
        "ctrader": "ctrader",
        "binance": "binance_spot",
        "dukascopy": "dukascopy",
        "yahoo": "yahoo",
    }
)


def resolve_runtime_source_id(
    override: str | None = None, *, request_id: str | None = None
) -> str:
    """Resolve the configured runtime broker to a Data source identifier.

    Args:
        override: Optional explicit source identifier from the request.
        request_id: Canonical request identifier for the settings read.

    Returns:
        Data source identifier for the active runtime broker.

    Raises:
        RuntimeError: If the configured runtime broker is unavailable.
    """
    if override is not None and override.strip():
        return override.strip()
    trace_id = request_id if request_id is not None else generate_id("req")
    record = get_system_settings(request_id=trace_id)
    broker = str(record.settings.get("RUNTIME_BROKER", "")).strip().lower()
    source_id = _BROKER_TO_SOURCE.get(broker)
    if source_id is None:
        logger.error("Runtime broker source is unavailable or unsupported")
        raise RuntimeError("RUNTIME_BROKER_UNAVAILABLE")
    logger.info("Resolved configured runtime broker to source %r", source_id)
    return source_id


def _reset_cache_for_tests() -> None:
    """Clear the bounded in-process projection cache."""
    with _cache_lock:
        _cache.clear()


def build_technical_evidence(
    source_id: str,
    symbol: str,
    *,
    last_price: float | None,
    request_id: str | None = None,
) -> dict[str, float | None]:
    """Fetch evidence and delegate calculations to Indicators.

    Args:
        source_id: Data provider identifier.
        symbol: Broker-native symbol.
        last_price: Current quote price, when available.
        request_id: Optional canonical request identifier.

    Returns:
        Nullable Indicators-owned market projection.
    """
    key = (source_id, symbol, last_price)
    now = time.monotonic()
    with _cache_lock:
        cached = _cache.get(key)
        if cached is not None and now - cached[0] < _CACHE_TTL_SECONDS:
            return cached[1]

    trace_id = request_id if request_id is not None else generate_id("req")
    end = datetime.now(UTC)
    try:
        metadata_response = get_symbol_metadata(
            build_symbol_metadata_request(
                source_id=source_id,
                symbol=symbol,
                request_id=trace_id,
            )
        )
        data_response = get_market_data(
            build_market_data_request(
                source_id=source_id,
                symbol=symbol,
                data_kind="bars",
                timeframe="D1",
                start=end - timedelta(days=_HISTORY_DAYS),
                end=end,
                limit=_HISTORY_DAYS,
                use_cache=True,
                quality_failure_behavior="warn",
                workflow_context="research",
                precision_policy="decimal_string",
                request_id=trace_id,
            )
        )
        metadata = metadata_response.data
        dataset = data_response.data
        if (
            metadata_response.status != "success"
            or data_response.status != "success"
            or metadata is None
            or dataset is None
        ):
            return {}
        digits = getattr(metadata, "digits", None)
        point = getattr(metadata, "point", None)
        if digits is None or point is None:
            return {}
        projection = project_market_overlay(
            dataset,
            digits=int(digits),
            point=float(point),
            last_price=last_price,
        )
    except Exception:  # noqa: BLE001 - optional evidence degrades to unavailable
        logger.debug("Technical evidence unavailable for symbol %s", symbol)
        return {}

    with _cache_lock:
        _cache[key] = (now, projection)
    return projection


def orchestrate_market_directory(
    *,
    source_id: str | None,
    query: str | None,
    cursor: str | None,
    limit: int,
    request_id: str,
) -> object:
    """Delegate one bounded categorized directory read to Data.

    Args:
        source_id: Optional explicit Data provider.
        query: Optional symbol search.
        cursor: Optional pagination cursor.
        limit: Bounded page size.
        request_id: Canonical request identifier.

    Returns:
        Normalized API market-directory response.
    """
    resolved_source_id = resolve_runtime_source_id(source_id, request_id=request_id)
    request = build_market_directory_request(
        source_id=resolved_source_id,
        query=query,
        cursor=cursor,
        limit=limit,
        request_id=request_id,
    )
    return build_gateway_response(
        list_market_directory(request),
        request_id=request_id,
        route="/api/v1/data/markets",
        operation="api.data.markets",
        success_message="Market directory retrieved",
        failure_message="Market directory unavailable",
        technical_builder=build_technical_evidence,
    )


def orchestrate_quotes(
    *,
    symbols: tuple[str, ...],
    source_id: str | None,
    include_technicals: bool,
    request_id: str,
) -> object:
    """Delegate one bounded explicit-symbol quote read to Data.

    Args:
        symbols: Broker-native symbols requested by the caller.
        source_id: Optional explicit Data provider.
        include_technicals: Whether to request optional Indicators evidence.
        request_id: Canonical request identifier.

    Returns:
        Normalized API quote response.
    """
    resolved_source_id = resolve_runtime_source_id(source_id, request_id=request_id)
    request = build_symbols_quote_request(
        source_id=resolved_source_id,
        symbols=symbols,
        request_id=request_id,
    )
    return build_gateway_response(
        get_symbols_quotes(request),
        request_id=request_id,
        route="/api/v1/data/quotes",
        operation="api.data.quotes",
        success_message="Quotes retrieved",
        failure_message="Quotes unavailable",
        source_id=resolved_source_id,
        include_technicals=include_technicals,
        technical_builder=build_technical_evidence,
    )


__all__ = (
    "build_technical_evidence",
    "orchestrate_market_directory",
    "orchestrate_quotes",
    "resolve_runtime_source_id",
)
