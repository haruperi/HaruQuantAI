"""Markets source, Data evidence, and Indicators orchestration."""

from __future__ import annotations

import threading
import time
from types import MappingProxyType
from typing import Any, Final, Protocol, cast

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

_HISTORY_BAR_COUNT: Final = 40
_MINIMUM_OVERLAY_BARS: Final = 12
_CACHE_TTL_SECONDS: Final = 300.0
_cache_lock: Final = threading.Lock()
type _TechnicalCacheKey = tuple[str, str]
type _TechnicalCacheEntry = tuple[float, object, int, float]
_cache: dict[_TechnicalCacheKey, _TechnicalCacheEntry] = {}


class _QuoteMetadata(Protocol):
    """Private symbol-precision contract consumed from Data."""

    digits: Any
    point: Any


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


def _quote_precision(metadata: object) -> tuple[int, float]:
    """Return validated broker quote precision.

    Args:
        metadata: Data-owned symbol metadata.

    Returns:
        Broker digits and positive point size.

    Raises:
        AttributeError: If required metadata fields are absent.
        TypeError: If a metadata field cannot be converted.
        ValueError: If precision is outside its valid domain.
    """
    quote_metadata = cast("_QuoteMetadata", metadata)
    digits = int(quote_metadata.digits)
    point = float(quote_metadata.point)
    if digits < 0 or point <= 0:
        raise ValueError("invalid broker quote precision")
    return digits, point


def _history_is_sufficient(dataset: object) -> bool:
    """Return whether a dataset can warm up the Markets indicators.

    Args:
        dataset: Data-owned market dataset.

    Returns:
        Whether the dataset contains the minimum required bar count.
    """
    records = getattr(dataset, "records", ())
    return len(records) >= _MINIMUM_OVERLAY_BARS


def build_technical_evidence(
    source_id: str,
    symbol: str,
    *,
    last_price: float | None,
    request_id: str | None = None,
) -> dict[str, float | None]:
    """Fetch symbol evidence and delegate calculations to Indicators.

    Args:
        source_id: Data provider identifier.
        symbol: Broker-native symbol.
        last_price: Current quote price, when available.
        request_id: Optional canonical request identifier.

    Returns:
        Nullable Indicators-owned market projection.
    """
    key = (source_id, symbol)
    now = time.monotonic()
    dataset: object | None = None
    digits: int | None = None
    point: float | None = None

    with _cache_lock:
        cached = _cache.get(key)
        if cached is not None and now - cached[0] < _CACHE_TTL_SECONDS:
            _, dataset, digits, point = cached

    if dataset is None or digits is None or point is None:
        trace_id = request_id if request_id is not None else generate_id("req")
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
                    limit=_HISTORY_BAR_COUNT,
                    use_cache=False,
                    quality_failure_behavior="warn",
                    workflow_context="research",
                    precision_policy="decimal_string",
                    request_id=trace_id,
                )
            )
            if (
                data_response.status == "success"
                and data_response.data is not None
                and not _history_is_sufficient(data_response.data)
            ):
                # MT5 can return only its current bar while it synchronizes a
                # symbol's history. One uncached retry reads the synchronized
                # bars without allowing that transient response into our cache.
                data_response = get_market_data(
                    build_market_data_request(
                        source_id=source_id,
                        symbol=symbol,
                        data_kind="bars",
                        timeframe="D1",
                        limit=_HISTORY_BAR_COUNT,
                        use_cache=False,
                        quality_failure_behavior="warn",
                        workflow_context="research",
                        precision_policy="decimal_string",
                        request_id=trace_id,
                    )
                )
            if (
                data_response.status == "success"
                and data_response.data is not None
                and _history_is_sufficient(data_response.data)
                and metadata_response.status == "success"
                and metadata_response.data is not None
            ):
                dataset = data_response.data
                metadata = metadata_response.data
                digits, point = _quote_precision(metadata)

                with _cache_lock:
                    _cache[key] = (now, dataset, digits, point)
        except Exception:  # noqa: BLE001 - optional evidence degrades to unavailable
            logger.warning("Markets technical evidence fetch was unavailable")

    if dataset is None or digits is None or point is None:
        return {}

    try:
        return project_market_overlay(
            dataset,
            digits=digits,
            point=point,
            last_price=last_price,
        )
    except Exception:  # noqa: BLE001 - optional evidence degrades to unavailable
        logger.warning("Markets technical evidence projection was unavailable")
        return {}


def orchestrate_market_directory(
    *,
    source_id: str | None,
    query: str | None,
    cursor: str | None,
    limit: int,
    include_technicals: bool = True,
    request_id: str,
) -> object:
    """Delegate one bounded categorized directory read to Data.

    Args:
        source_id: Optional explicit Data provider.
        query: Optional symbol search.
        cursor: Optional pagination cursor.
        limit: Bounded page size.
        include_technicals: Whether to request Indicators evidence.
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
        source_id=resolved_source_id,
        include_technicals=include_technicals,
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
