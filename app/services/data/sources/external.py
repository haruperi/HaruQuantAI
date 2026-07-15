"""Adapter for caller-owned canonical Brokers read capabilities."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from app.services.data.contracts.errors import DataError
from app.services.data.contracts.sources import (
    RawSourceBatch,
    SourceReadRequest,
    SymbolListRequest,
    SymbolMetadata,
    SymbolMetadataRequest,
    SymbolPage,
)
from app.services.data.sources.protocol import MarketDataSource
from app.utils import logger

if TYPE_CHECKING:
    from collections.abc import Coroutine

    from app.services.brokers import BrokerAdapter
    from app.services.brokers.contracts.models import BrokerResult


def _run[T](operation: Coroutine[Any, Any, T], request_id: str) -> T:
    """Run one bounded asynchronous broker read from the synchronous DATA API."""
    logger.debug("Running one injected broker read operation")
    try:
        return asyncio.run(operation)
    except DataError:
        raise
    except Exception as error:
        logger.error("Injected broker read failed")
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": "broker_read"},
            request_id=request_id,
        ) from error


def _require_result[T](
    result: BrokerResult[T],
    operation: str,
    request_id: str,
) -> T:
    """Return a canonical Brokers result value or map it to a DATA failure."""
    logger.debug("Validating canonical broker result for %s", operation)
    if result.error is not None or result.data is None:
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": operation},
            request_id=request_id,
        )
    return result.data


class ExternalMarketDataSource(MarketDataSource):
    """Read-only DATA source backed by an injected, caller-owned BrokerAdapter."""

    def __init__(self, source_id: str, adapter: BrokerAdapter) -> None:
        """Store a source identity and already configured adapter.

        Args:
            source_id: DATA-owned source identifier.
            adapter: Caller-owned canonical Brokers adapter. DATA does not connect,
                disconnect, select, configure, or otherwise own its lifecycle.
        """
        logger.info("Initializing injected external source %s", source_id)
        if not source_id or source_id != source_id.strip():
            raise ValueError("source_id must be a non-empty trimmed string")
        self._source_id = source_id
        self._adapter = adapter

    async def _fetch_async(self, request: SourceReadRequest) -> RawSourceBatch:
        """Fetch bounded raw records without mutating adapter lifecycle."""
        logger.info(
            "Fetching %s from injected source %s", request.data_kind, self._source_id
        )
        if request.source_id != self._source_id:
            raise DataError(
                "INVALID_INPUT",
                safe_details={"field": "source_id"},
                request_id=request.request_id,
            )

        records: tuple[Mapping[str, object], ...]
        if request.data_kind == "bars":
            bar_result = await self._adapter.get_historical_bars(
                symbol=request.provider_symbol,
                timeframe=request.timeframe or "M1",
                start=request.start,
                end=request.end,
                limit=request.limit,
            )
            bar_page = _require_result(
                bar_result, "historical_bars", request.request_id
            )
            normalized_bars: list[dict[str, object]] = []
            for bar in bar_page.items:
                volume = bar.trade_volume
                if volume is None:
                    volume = bar.tick_volume
                if volume is None:
                    raise DataError(
                        "DATA_QUALITY_FAILED",
                        safe_details={"field": "volume"},
                        request_id=request.request_id,
                    )
                normalized_bars.append(
                    {
                        "timestamp": bar.opening_timestamp,
                        "source": request.source_id,
                        "source_symbol": request.provider_symbol,
                        "source_revision": bar_result.adapter_version,
                        "available_at": bar_result.timestamp,
                        "open": bar.open,
                        "high": bar.high,
                        "low": bar.low,
                        "close": bar.close,
                        "volume": volume,
                        "price_unit": bar.price_unit,
                        "volume_unit": bar.quantity_unit,
                    }
                )
            records = tuple(normalized_bars)
            retrieved_at = bar_result.timestamp
            revision = bar_result.adapter_version
        elif request.data_kind == "ticks":
            tick_result = await self._adapter.get_ticks(
                symbol=request.provider_symbol,
                start=request.start,
                end=request.end,
                limit=request.limit,
            )
            tick_page = _require_result(tick_result, "ticks", request.request_id)
            records = tuple(
                {
                    "timestamp": tick.event_timestamp,
                    "source": request.source_id,
                    "source_symbol": request.provider_symbol,
                    "source_revision": tick_result.adapter_version,
                    "available_at": tick_result.timestamp,
                    "price_unit": tick.price_unit,
                    "bid": tick.bid,
                    "ask": tick.ask,
                    "last": tick.last_price,
                    "volume": None,
                    "volume_unit": None,
                }
                for tick in tick_page.items
            )
            retrieved_at = tick_result.timestamp
            revision = tick_result.adapter_version
        elif request.data_kind == "spreads":
            spread_result = await self._adapter.get_spread(
                symbol=request.provider_symbol
            )
            spread = _require_result(spread_result, "spread", request.request_id)
            metadata_result = await self._adapter.get_symbol_info(
                symbol=request.provider_symbol
            )
            metadata = _require_result(
                metadata_result,
                "symbol_info",
                request.request_id,
            )
            if metadata.price_precision is None:
                raise DataError(
                    "MISSING_ASSET_METADATA",
                    safe_details={"field": "price_precision"},
                    request_id=request.request_id,
                )
            records = (
                {
                    "timestamp": spread_result.timestamp,
                    "source": request.source_id,
                    "source_symbol": request.provider_symbol,
                    "source_revision": spread_result.adapter_version,
                    "available_at": spread_result.timestamp,
                    "spread": spread,
                    "unit": metadata.price_unit,
                    "scale": metadata.price_precision,
                },
            )
            retrieved_at = spread_result.timestamp
            revision = spread_result.adapter_version
        else:
            raise DataError(
                "UNSUPPORTED_OPERATION",
                safe_details={"data_kind": request.data_kind},
                request_id=request.request_id,
            )

        if not records:
            raise DataError("EMPTY_RESULT", request_id=request.request_id)
        return RawSourceBatch(
            source_id=request.source_id,
            provider_symbol=request.provider_symbol,
            data_kind=request.data_kind,
            records=records,
            retrieved_at=retrieved_at,
            revision=revision,
            request_id=request.request_id,
        )

    async def _list_symbols_async(self, request: SymbolListRequest) -> SymbolPage:
        """Read an exact bounded provider-native symbol page."""
        logger.info("Listing symbols from injected source %s", self._source_id)
        if request.source_id != self._source_id:
            raise DataError(
                "INVALID_INPUT",
                safe_details={"field": "source_id"},
                request_id=request.request_id,
            )
        result = await self._adapter.get_symbols(
            query=request.query,
            cursor=request.cursor,
            limit=request.limit,
        )
        page = _require_result(result, "symbols", request.request_id)
        items = tuple(sorted({symbol.provider_symbol for symbol in page.items}))
        return SymbolPage(
            source_id=request.source_id,
            items=items,
            limit=request.limit,
            next_cursor=page.next_cursor,
            revision=result.adapter_version,
            request_id=request.request_id,
        )

    async def _get_symbol_metadata_async(
        self,
        request: SymbolMetadataRequest,
    ) -> SymbolMetadata:
        """Read exact provider metadata without assigning guessed values."""
        logger.info("Reading metadata from injected source %s", self._source_id)
        if request.source_id != self._source_id:
            raise DataError(
                "INVALID_INPUT",
                safe_details={"field": "source_id"},
                request_id=request.request_id,
            )
        result = await self._adapter.get_symbol_info(symbol=request.symbol)
        info = _require_result(result, "symbol_info", request.request_id)
        timezone = info.provider_metadata.get("timezone")
        if timezone is not None and not isinstance(timezone, str):
            raise DataError(
                "MISSING_ASSET_METADATA",
                safe_details={"field": "timezone"},
                request_id=request.request_id,
            )
        return SymbolMetadata(
            canonical_symbol=request.symbol,
            provider_symbol=info.provider_symbol,
            asset_class=info.product_profile,
            base_currency=info.base_asset,
            quote_currency=info.quote_asset,
            digits=info.price_precision,
            price_step=info.price_step,
            quantity_step=info.quantity_step,
            timezone=timezone,
            source_id=request.source_id,
            revision=result.adapter_version,
            retrieved_at=result.timestamp,
            request_id=request.request_id,
        )

    def fetch(self, request: SourceReadRequest) -> RawSourceBatch:
        """Fetch raw records through the injected adapter."""
        logger.info("Executing external source fetch")
        return _run(self._fetch_async(request), request.request_id)

    def list_symbols(self, request: SymbolListRequest) -> SymbolPage:
        """List provider-native symbols through the injected adapter."""
        logger.info("Executing external source symbol listing")
        return _run(self._list_symbols_async(request), request.request_id)

    def get_symbol_metadata(self, request: SymbolMetadataRequest) -> SymbolMetadata:
        """Read provider-native symbol metadata through the injected adapter."""
        logger.info("Executing external source metadata read")
        return _run(self._get_symbol_metadata_async(request), request.request_id)


__all__ = ["ExternalMarketDataSource"]
