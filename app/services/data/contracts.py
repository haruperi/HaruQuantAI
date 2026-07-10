"""Typed contracts for the market data service boundary.

This module defines lightweight protocols and aliases used to describe Data
service boundaries without importing broker SDKs or leaking provider-native
objects across module boundaries.
"""

from collections.abc import Callable
from datetime import datetime
from typing import Protocol, runtime_checkable

import pandas as pd

from app.utils.logger import logger

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]
type DataRecord = dict[str, JsonValue]
type DataRecords = list[DataRecord]
type SymbolMetadataRecord = dict[str, JsonValue]


@runtime_checkable
class BrokerMarketDataPort(Protocol):
    """Read-only broker market data client contract.

    Implementations are owned by ``app.services.brokers``. Data adapters may
    use this port only for connection-readiness checks and market-data reads.
    Broker account, order, position, or live-execution mutation methods are
    intentionally absent from this protocol.
    """

    def is_connected(self) -> bool:
        """Return whether the read-only broker data client is connected.

        Returns:
            True when the broker data client is connected, otherwise False.
        """
        logger.debug("BrokerMarketDataPort.is_connected contract invoked.")
        raise NotImplementedError

    def connect(self) -> bool | None:
        """Open the broker data connection when required.

        Returns:
            Optional provider connection result. Existing broker clients may
            return True/False, while some future clients may return None.

        Raises:
            Exception: Implementations may raise provider-specific connection
                errors, which data adapters must map to deterministic service
                errors.
        """
        logger.debug("BrokerMarketDataPort.connect contract invoked.")
        raise NotImplementedError

    def get_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        date_from: datetime,
        date_to: datetime,
    ) -> pd.DataFrame | None:
        """Read historical OHLCV bars from a broker data source.

        Args:
            symbol: Provider symbol identifier.
            timeframe: Provider timeframe identifier.
            date_from: Inclusive UTC start datetime.
            date_to: Inclusive UTC end datetime.

        Returns:
            A pandas DataFrame containing provider bar rows, or None when no
            rows are available.
        """
        logger.debug(
            "BrokerMarketDataPort.get_bars contract invoked for {} {} from {} to {}.",
            symbol,
            timeframe,
            date_from.isoformat(),
            date_to.isoformat(),
        )
        raise NotImplementedError

    def get_ticks(
        self,
        *,
        symbol: str,
        start: datetime,
        end: datetime,
        as_dataframe: bool = True,
    ) -> pd.DataFrame | None:
        """Read historical ticks from a broker data source.

        Args:
            symbol: Provider symbol identifier.
            start: Inclusive UTC start datetime.
            end: Inclusive UTC end datetime.
            as_dataframe: Whether the broker client should return a DataFrame.

        Returns:
            A pandas DataFrame containing provider tick rows, or None when no
            rows are available.
        """
        logger.debug(
            "BrokerMarketDataPort.get_ticks contract invoked for {} from {} to {} "
            "as_dataframe={}.",
            symbol,
            start.isoformat(),
            end.isoformat(),
            as_dataframe,
        )
        raise NotImplementedError


type BrokerMarketDataFactory = Callable[[], BrokerMarketDataPort]


@runtime_checkable
class SourceAdapterPort(Protocol):
    """Internal source adapter contract for normalized market data records."""

    def is_ready(self) -> bool:
        """Return whether the source adapter is configured for read calls.

        Returns:
            True when the source is ready, otherwise False.
        """
        logger.debug("SourceAdapterPort.is_ready contract invoked.")
        raise NotImplementedError

    def get_market_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,
    ) -> DataRecords:
        """Fetch normalized historical OHLCV records.

        Args:
            symbol: Canonical symbol identifier.
            timeframe: Canonical timeframe identifier.
            start_time: Inclusive UTC start datetime.
            end_time: Inclusive UTC end datetime.
            request_id: Optional trace identifier.

        Returns:
            Normalized JSON-safe market data records.
        """
        logger.debug(
            "SourceAdapterPort.get_market_data contract invoked for {} {} from {} "
            "to {}.",
            symbol,
            timeframe,
            start_time.isoformat(),
            end_time.isoformat(),
            extra={"request_id": request_id},
        )
        raise NotImplementedError

    def get_tick_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,
    ) -> DataRecords:
        """Fetch normalized historical tick records.

        Args:
            symbol: Canonical symbol identifier.
            start_time: Inclusive UTC start datetime.
            end_time: Inclusive UTC end datetime.
            request_id: Optional trace identifier.

        Returns:
            Normalized JSON-safe tick records.
        """
        logger.debug(
            "SourceAdapterPort.get_tick_data contract invoked for {} from {} to {}.",
            symbol,
            start_time.isoformat(),
            end_time.isoformat(),
            extra={"request_id": request_id},
        )
        raise NotImplementedError

    def list_symbols(self, *, request_id: str | None = None) -> list[str]:
        """List symbols discovered from the source.

        Args:
            request_id: Optional trace identifier.

        Returns:
            Sorted or provider-defined symbol identifiers.
        """
        logger.debug(
            "SourceAdapterPort.list_symbols contract invoked.",
            extra={"request_id": request_id},
        )
        raise NotImplementedError

    def get_symbol_metadata(
        self,
        symbol: str,
        *,
        request_id: str | None = None,
    ) -> SymbolMetadataRecord:
        """Return normalized metadata for a symbol.

        Args:
            symbol: Canonical symbol identifier.
            request_id: Optional trace identifier.

        Returns:
            JSON-safe symbol metadata.
        """
        logger.debug(
            "SourceAdapterPort.get_symbol_metadata contract invoked for {}.",
            symbol,
            extra={"request_id": request_id},
        )
        raise NotImplementedError
