"""Adapter for caller-owned canonical Brokers read capabilities."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import datetime
from typing import TYPE_CHECKING, Any, Protocol, override

from app.services.data.contracts import DataError
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
)
from app.services.data.market_data.symbol_metadata import (
    SymbolListRequest,
    SymbolMetadata,
    SymbolMetadataRequest,
    SymbolPage,
)
from app.services.data.sources.contracts import (
    RawSourceBatch,
    SourceReadRequest,
)
from app.services.data.sources.protocol import MarketDataSource
from app.utils import get_logger, parse_utc_timestamp

logger = get_logger(__name__)

if TYPE_CHECKING:
    from collections.abc import Coroutine

    from app.services.brokers.contracts import BrokerAdapter


class _AsyncRunner(Protocol):
    """Execute one broker coroutine behind Data's synchronous facade."""

    def __call__[T](
        self,
        operation: Coroutine[Any, Any, T],
        request_id: str,
    ) -> T:
        """Return the completed coroutine result."""
        ...


def _run[T](operation: Coroutine[Any, Any, T], request_id: str) -> T:
    """Run one bounded asynchronous broker read from the synchronous DATA API.

    Returns:
        Completed broker read result.

    Raises:
        DataError: If the asynchronous provider operation fails.
    """
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
    result: StandardResponse[T],
    operation: str,
    request_id: str,
) -> T:
    """Return a canonical Brokers result value or map it to a DATA failure.

    Returns:
        Successful result payload.

    Raises:
        DataError: If the broker result contains an error or no payload.
    """
    logger.debug("Validating canonical broker result for %s", operation)
    if result.error is not None or result.data is None:
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": operation},
            request_id=request_id,
        )
    return result.data


def _require_broker_extension[T](
    result: StandardResponse[T],
    key: str,
    operation: str,
    request_id: str,
) -> str:
    """Return one required Brokers metadata extension.

    Args:
        result: Standard Brokers response.
        key: Required extension key.
        operation: Data-owned operation label.
        request_id: Data request identity.

    Returns:
        Required string extension value.

    Raises:
        DataError: If the required Brokers evidence is absent or malformed.
    """
    value = result.metadata.extensions.get(key)
    if not isinstance(value, str):
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": operation, "field": key},
            request_id=request_id,
        )
    return value


def _require_broker_timestamp[T](
    result: StandardResponse[T],
    operation: str,
    request_id: str,
) -> datetime:
    """Return the required Brokers completion timestamp.

    Raises:
        DataError: If the timestamp extension is absent or malformed.
    """
    value = _require_broker_extension(result, "timestamp", operation, request_id)
    try:
        return parse_utc_timestamp(value)
    except ValueError as error:
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": operation, "field": "timestamp"},
            request_id=request_id,
        ) from error


class ExternalMarketDataSource(MarketDataSource):
    """Read-only DATA source backed by an injected, caller-owned BrokerAdapter."""

    def __init__(
        self,
        source_id: str,
        adapter: BrokerAdapter,
        runner: _AsyncRunner = _run,
    ) -> None:
        """Store a source identity and already configured adapter.

        Args:
            source_id: DATA-owned source identifier.
            adapter: Caller-owned canonical Brokers adapter. DATA does not connect,
                disconnect, select, configure, or otherwise own its lifecycle.
            runner: Composition-owned synchronous coroutine runner. The default
                creates one event loop per operation for already-connected adapters.

        Raises:
            ValueError: If the source identifier is blank or padded.
        """
        logger.info("Initializing injected external source %s", source_id)
        if not source_id or source_id != source_id.strip():
            raise ValueError("source_id must be a non-empty trimmed string")
        self._source_id = source_id
        self._adapter = adapter
        self._runner = runner

    async def _fetch_async(self, request: SourceReadRequest) -> RawSourceBatch:
        """Fetch bounded raw records without mutating adapter lifecycle.

        Returns:
            Provider-neutral raw source batch.

        Raises:
            DataError: If source identity, capability, or evidence is invalid.
        """
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
            bar_revision = _require_broker_extension(
                bar_result,
                "adapter_version",
                "historical_bars",
                request.request_id,
            )
            bar_timestamp = _require_broker_timestamp(
                bar_result,
                "historical_bars",
                request.request_id,
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
                        "source_revision": bar_revision,
                        "available_at": bar.closing_timestamp,
                        "open": bar.open,
                        "high": bar.high,
                        "low": bar.low,
                        "close": bar.close,
                        "volume": volume,
                        "price_unit": bar.price_unit,
                        "volume_unit": bar.quantity_unit,
                        "spread": bar.spread,
                        "spread_unit": bar.spread_unit,
                    }
                )
            records = tuple(normalized_bars)
            retrieved_at = max(
                (
                    *(bar.closing_timestamp for bar in bar_page.items),
                    bar_timestamp,
                )
            )
            revision = bar_revision
        elif request.data_kind == "ticks":
            tick_result = await self._adapter.get_ticks(
                symbol=request.provider_symbol,
                start=request.start,
                end=request.end,
                limit=request.limit,
            )
            tick_page = _require_result(tick_result, "ticks", request.request_id)
            tick_revision = _require_broker_extension(
                tick_result, "adapter_version", "ticks", request.request_id
            )
            tick_timestamp = _require_broker_timestamp(
                tick_result, "ticks", request.request_id
            )
            available_times = [
                max(
                    tick.event_timestamp,
                    tick.provider_receipt_timestamp,
                    tick_timestamp,
                )
                for tick in tick_page.items
            ]
            records = tuple(
                {
                    "timestamp": tick.event_timestamp,
                    "source": request.source_id,
                    "source_symbol": request.provider_symbol,
                    "source_revision": tick_revision,
                    "available_at": available_at,
                    "price_unit": tick.price_unit,
                    "bid": tick.bid,
                    "ask": tick.ask,
                    "last": tick.last_price,
                    "volume": None,
                    "volume_unit": None,
                }
                for tick, available_at in zip(
                    tick_page.items,
                    available_times,
                    strict=True,
                )
            )
            retrieved_at = max(available_times, default=tick_timestamp)
            revision = tick_revision
        elif request.data_kind == "spreads":
            spread_result = await self._adapter.get_spread(
                symbol=request.provider_symbol
            )
            spread = _require_result(spread_result, "spread", request.request_id)
            spread_revision = _require_broker_extension(
                spread_result, "adapter_version", "spread", request.request_id
            )
            spread_timestamp = _require_broker_timestamp(
                spread_result, "spread", request.request_id
            )
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
                    "timestamp": spread_timestamp,
                    "source": request.source_id,
                    "source_symbol": request.provider_symbol,
                    "source_revision": spread_revision,
                    "available_at": spread_timestamp,
                    "spread": spread,
                    "unit": metadata.price_unit,
                    "scale": metadata.price_precision,
                },
            )
            retrieved_at = spread_timestamp
            revision = spread_revision
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
        """Read an exact bounded provider-native symbol page.

        Returns:
            Bounded normalized symbol page.

        Raises:
            DataError: If source identity or provider evidence is invalid.
        """
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
        revision = _require_broker_extension(
            result, "adapter_version", "symbols", request.request_id
        )
        items = tuple(sorted({symbol.provider_symbol for symbol in page.items}))
        return SymbolPage(
            source_id=request.source_id,
            items=items,
            limit=request.limit,
            next_cursor=page.next_cursor,
            revision=revision,
            request_id=request.request_id,
        )

    async def _get_symbol_metadata_async(
        self,
        request: SymbolMetadataRequest,
    ) -> SymbolMetadata:
        """Read exact provider metadata without assigning guessed values.

        Returns:
            Normalized symbol metadata.

        Raises:
            DataError: If source identity or provider evidence is invalid.
        """
        logger.info("Reading metadata from injected source %s", self._source_id)
        if request.source_id != self._source_id:
            raise DataError(
                "INVALID_INPUT",
                safe_details={"field": "source_id"},
                request_id=request.request_id,
            )
        result = await self._adapter.get_symbol_info(symbol=request.symbol)
        info = _require_result(result, "symbol_info", request.request_id)
        revision = _require_broker_extension(
            result, "adapter_version", "symbol_info", request.request_id
        )
        retrieved_at = _require_broker_timestamp(
            result, "symbol_info", request.request_id
        )
        timezone = info.provider_metadata.get("timezone")
        if timezone is not None and not isinstance(timezone, str):
            raise DataError(
                "MISSING_ASSET_METADATA",
                safe_details={"field": "timezone"},
                request_id=request.request_id,
            )
        metadata_dict: dict[str, Any] = {
            "canonical_symbol": request.symbol,
            "provider_symbol": info.provider_symbol,
            "asset_class": info.product_profile,
            "base_currency": info.base_asset,
            "quote_currency": info.quote_asset,
            "digits": info.price_precision,
            "price_step": info.price_step,
            "quantity_step": info.quantity_step,
            "timezone": timezone,
            "source_id": request.source_id,
            "revision": revision,
            "retrieved_at": retrieved_at,
            "request_id": request.request_id,
        }
        metadata_dict.update(info.provider_metadata)
        if "trade_contract_size" in info.provider_metadata:
            metadata_dict["lot_size"] = info.provider_metadata["trade_contract_size"]

        return SymbolMetadata(**metadata_dict)

    @override
    def fetch(self, request: SourceReadRequest) -> StandardResponse[RawSourceBatch]:
        """Fetch raw records through the injected adapter.

        Returns:
            Standard response carrying the provider-neutral raw source batch.
        """
        logger.info("Executing external source fetch")
        return run_data_operation(
            operation="data.sources.market_data_source.fetch",
            request_id=request.request_id,
            start_time=data_start_time(),
            raw=lambda: self._runner(self._fetch_async(request), request.request_id),
        )

    @override
    def list_symbols(self, request: SymbolListRequest) -> StandardResponse[SymbolPage]:
        """List provider-native symbols through the injected adapter.

        Returns:
            Standard response carrying the bounded normalized symbol page.
        """
        logger.info("Executing external source symbol listing")
        return run_data_operation(
            operation="data.sources.market_data_source.list_symbols",
            request_id=request.request_id,
            start_time=data_start_time(),
            raw=lambda: self._runner(
                self._list_symbols_async(request), request.request_id
            ),
        )

    @override
    def get_symbol_metadata(
        self, request: SymbolMetadataRequest
    ) -> StandardResponse[SymbolMetadata]:
        """Read provider-native symbol metadata through the injected adapter.

        Returns:
            Standard response carrying the normalized symbol metadata.
        """
        logger.info("Executing external source metadata read")
        return run_data_operation(
            operation="data.sources.market_data_source.get_symbol_metadata",
            request_id=request.request_id,
            start_time=data_start_time(),
            raw=lambda: self._runner(
                self._get_symbol_metadata_async(request), request.request_id
            ),
        )


__all__ = ["ExternalMarketDataSource"]
