"""Data source resolver and provider adapters for the market data service."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import pandas as pd

from app.services.data.normalization import (
    bars_dataframe_to_records,
    mt5_ticks_dataframe_to_records,
    normalize_file_records,
    ticks_dataframe_to_records,
)
from app.services.data.storage import db_helper, load_local_dataset
from app.services.data.transforms import (
    generate_synthetic_bars,
    generate_synthetic_ticks,
)
from app.utils.errors import ExternalServiceError, ValidationError
from app.utils.logger import logger

CIRCUIT_OPEN_FAILURE_THRESHOLD = 4


@runtime_checkable
class SourceAdapterProtocol(Protocol):
    """Common internal source adapter protocol for all data providers."""

    def is_ready(self) -> bool:
        """Check if source adapter is ready or configured."""
        ...

    def get_market_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch normalized historical OHLCV data."""
        ...

    def get_tick_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch normalized historical tick data."""
        ...

    def list_symbols(self, *, request_id: str | None = None) -> list[str]:
        """List symbols discovered from the source."""
        ...

    def get_symbol_metadata(
        self,
        symbol: str,
        *,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Retrieve symbol metadata."""
        ...


def get_circuit_breaker(source: str) -> dict[str, Any]:
    """Retrieve persisted circuit breaker state for a source.

    Args:
        source: Source identifier.

    Returns:
        dict[str, Any]: Persisted or default circuit breaker state.
    """
    try:
        with db_helper.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM circuit_breakers WHERE source = ?;", (source,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "source": row["source"],
                    "state": row["state"],
                    "last_state_change": row["last_state_change"],
                    "failures_count": int(row["failures_count"]),
                    "cooldown_expires": row["cooldown_expires"],
                }
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Failed to query circuit breaker for {source}: {e}")

    return {
        "source": source,
        "state": "closed",
        "last_state_change": datetime.now(UTC).isoformat(),
        "failures_count": 0,
        "cooldown_expires": None,
    }


def update_circuit_breaker(
    source: str,
    state: str,
    failures_count: int,
    cooldown_expires: str | None = None,
) -> None:
    """Update and persist circuit breaker state.

    Args:
        source: Source identifier.
        state: New circuit breaker state.
        failures_count: Current failure count.
        cooldown_expires: Optional cooldown expiration timestamp.
    """
    logger.info(
        f"Updating circuit breaker: source={source}, state={state}, "
        f"failures={failures_count}"
    )
    try:
        with db_helper.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO circuit_breakers (
                    source, state, last_state_change, failures_count, cooldown_expires
                ) VALUES (?, ?, ?, ?, ?);
                """,
                (
                    source,
                    state,
                    datetime.now(UTC).isoformat(),
                    failures_count,
                    cooldown_expires,
                ),
            )
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to save circuit breaker state for {source}: {e}")


def check_circuit_breaker_barrier(source: str) -> None:
    """Block execution when a source circuit breaker is open.

    Args:
        source: Source identifier.

    Raises:
        ExternalServiceError: If the circuit breaker is open.
    """
    cb = get_circuit_breaker(source)
    if cb["state"] != "open":
        return

    expires = cb["cooldown_expires"]
    if expires and datetime.now(UTC) > datetime.fromisoformat(expires):
        logger.info(
            f"Circuit breaker cooldown expired for {source}. "
            "Transitioning to half-open."
        )
        update_circuit_breaker(source, "half-open", cb["failures_count"])
        return

    msg = f"Circuit breaker is open for source: {source} (blocked)."
    raise ExternalServiceError(msg, code="CIRCUIT_OPEN")


class LocalFileAdapter:
    """Base adapter for local file-backed OHLCV and tick sources."""

    def __init__(self, source: str, extension: str, paths: tuple[str, ...]) -> None:
        """Initialize local file adapter.

        Args:
            source: Source identifier.
            extension: File extension without leading dot.
            paths: Candidate local data directories.
        """
        self.source = source
        self.extension = extension
        self.paths = paths

    def is_ready(self) -> bool:
        """Check if local source adapter is ready."""
        return True

    def get_market_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch market data from local files."""
        filename = f"{symbol}_{timeframe}.{self.extension}"
        for path in self.paths:
            target_path = Path(path) / filename
            if not target_path.exists():
                continue
            raw_records = load_local_dataset(str(target_path), request_id=request_id)
            records = normalize_file_records(
                raw_records,
                symbol,
                timeframe,
                self.source,
            )
            return self._filter_by_time(records, start_time, end_time)
        return []

    def get_tick_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch tick data from local files."""
        filename = f"{symbol}_ticks.{self.extension}"
        for path in self.paths:
            target_path = Path(path) / filename
            if not target_path.exists():
                continue
            records = load_local_dataset(str(target_path), request_id=request_id)
            return self._filter_by_time(records, start_time, end_time)
        return []

    def list_symbols(self, *, request_id: str | None = None) -> list[str]:
        """List symbols from local files."""
        _ = request_id
        symbols = set()
        for path in self.paths:
            path_obj = Path(path)
            if not path_obj.exists():
                continue
            for file_path in path_obj.glob(f"*.{self.extension}"):
                symbols.add(file_path.name.split("_")[0])
        return sorted(symbols)

    def get_symbol_metadata(
        self,
        symbol: str,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Get local file source metadata."""
        return {
            "symbol": symbol,
            "source": self.source,
            "ready": True,
            "license": "Open",
            "attribution": f"Local {self.extension.upper()} Files",
        }

    @staticmethod
    def _filter_by_time(
        records: list[dict[str, Any]],
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict[str, Any]]:
        """Filter records inclusively between start and end times."""
        start_comp = (
            start_time.replace(tzinfo=UTC) if start_time.tzinfo is None else start_time
        )
        end_comp = end_time.replace(tzinfo=UTC) if end_time.tzinfo is None else end_time

        filtered = []
        for record in records:
            ts = pd.to_datetime(record["timestamp"])
            ts_utc = ts.tz_convert(UTC) if ts.tzinfo else ts.replace(tzinfo=UTC)
            if start_comp <= ts_utc <= end_comp:
                filtered.append(record)
        return filtered


class CSVAdapter(LocalFileAdapter):
    """CSV file data source adapter."""

    def __init__(self) -> None:
        """Initialize CSV adapter."""
        super().__init__(
            "csv",
            "csv",
            ("data/processed", "data/raw", "data/processed/csv", "data/raw/csv"),
        )


class ParquetAdapter(LocalFileAdapter):
    """Parquet file data source adapter."""

    def __init__(self) -> None:
        """Initialize Parquet adapter."""
        super().__init__(
            "parquet",
            "parquet",
            (
                "data/processed",
                "data/raw",
                "data/processed/parquet",
                "data/raw/parquet",
            ),
        )


class SyntheticAdapter:
    """Synthetic data source adapter."""

    def is_ready(self) -> bool:
        """Check if synthetic source adapter is ready."""
        return True

    def get_market_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,  # noqa: ARG002
        *,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch synthetic bar data."""
        return generate_synthetic_bars(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_time.isoformat(),
            num_bars=100,
            start_price=1.10,
            drift=0.0,
            volatility=0.01,
            seed=42,
            request_id=request_id,
        )

    def get_tick_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,  # noqa: ARG002
        *,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch synthetic tick data."""
        return generate_synthetic_ticks(
            symbol=symbol,
            start_time=start_time.isoformat(),
            num_ticks=250,
            start_price=1.10,
            average_spread=0.0002,
            volatility=0.0001,
            seed=42,
            request_id=request_id,
        )

    def list_symbols(self, *, request_id: str | None = None) -> list[str]:
        """List synthetic symbols."""
        _ = request_id
        return ["EURUSD", "GBPUSD", "USDJPY", "SPX500", "XAUUSD"]

    def get_symbol_metadata(
        self,
        symbol: str,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Get synthetic symbol metadata."""
        return {
            "symbol": symbol,
            "source": "synthetic",
            "ready": True,
            "license": "Generated",
            "attribution": "Synthetic deterministic generator",
        }


class BrokerBackedAdapter:
    """Base adapter for broker-backed data sources."""

    def __init__(
        self,
        source: str,
        client_factory: Callable[[], Any],
        unavailable_message: str,
        error_code: str,
        symbols: list[str],
        metadata: dict[str, Any],
        *,
        mt5_tick_schema: bool = False,
    ) -> None:
        """Initialize broker-backed data source adapter."""
        self.source = source
        self._client_factory = client_factory
        self._unavailable_message = unavailable_message
        self._error_code = error_code
        self._symbols = symbols
        self._metadata = metadata
        self._mt5_tick_schema = mt5_tick_schema

    def is_ready(self) -> bool:
        """Check if broker-backed adapter is ready."""
        return True

    def get_market_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Fetch broker-backed market data."""
        client = self._connected_client()
        df = client.get_bars(
            symbol=symbol,
            timeframe=timeframe,
            date_from=start_time,
            date_to=end_time,
        )
        if df is None or df.empty:
            return []
        return bars_dataframe_to_records(df, symbol, timeframe, self.source)

    def get_tick_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Fetch broker-backed tick data."""
        client = self._connected_client()
        df = client.get_ticks(
            symbol=symbol,
            start=start_time,
            end=end_time,
            as_dataframe=True,
        )
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return []
        if self._mt5_tick_schema:
            return mt5_ticks_dataframe_to_records(df, symbol, self.source)
        return ticks_dataframe_to_records(df, symbol, self.source)

    def list_symbols(self, *, request_id: str | None = None) -> list[str]:
        """List representative symbols for the source."""
        _ = request_id
        return self._symbols

    def get_symbol_metadata(
        self,
        symbol: str,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Get broker-backed symbol metadata."""
        metadata = dict(self._metadata)
        metadata["symbol"] = symbol
        metadata["source"] = self.source
        return metadata

    def _connected_client(self) -> Any:  # noqa: ANN401
        """Return a connected broker data client."""
        check_circuit_breaker_barrier(self.source)
        try:
            client = self._client_factory()
            if not client.is_connected():
                client.connect()
        except Exception as e:
            self._record_connection_failure()
            msg = f"{self._unavailable_message}: {e}"
            raise ExternalServiceError(msg, code=self._error_code) from e

        if not client.is_connected():
            msg = f"{self._unavailable_message}."
            raise ExternalServiceError(msg, code=self._error_code)
        return client

    def _record_connection_failure(self) -> None:
        """Record a connection failure in the source circuit breaker."""
        cb = get_circuit_breaker(self.source)
        failure_count = cb["failures_count"] + 1
        update_circuit_breaker(
            self.source,
            "open"
            if cb["failures_count"] >= CIRCUIT_OPEN_FAILURE_THRESHOLD
            else "closed",
            failure_count,
            (datetime.now(UTC) + timedelta(seconds=60)).isoformat(),
        )


def _get_mt5_client() -> Any:  # noqa: ANN401
    """Return the MT5 broker client."""
    from app.services.brokers.mt5 import get_mt5_client

    return get_mt5_client()


def _get_ctrader_client() -> Any:  # noqa: ANN401
    """Return the cTrader broker client."""
    from app.services.brokers.ctrader import get_ctrader_client

    return get_ctrader_client()


def _get_dukascopy_client() -> Any:  # noqa: ANN401
    """Return the Dukascopy broker client."""
    from app.services.brokers.dukascopy import get_dukascopy_client

    return get_dukascopy_client()


def _get_binance_client() -> Any:  # noqa: ANN401
    """Return the Binance broker client."""
    from app.services.brokers.binance import get_binance_client

    return get_binance_client()


def _get_yahoo_client() -> Any:  # noqa: ANN401
    """Return the Yahoo Finance broker client."""
    from app.services.brokers.yahoo import get_yahoo_client

    return get_yahoo_client()


class MT5Adapter(BrokerBackedAdapter):
    """MetaTrader 5 source adapter."""

    def __init__(self) -> None:
        """Initialize MT5 adapter."""
        super().__init__(
            "mt5",
            _get_mt5_client,
            "MetaTrader 5 terminal is not available",
            "BROKER_UNAVAILABLE",
            ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "SPX500"],
            {
                "ready": True,
                "license": "Proprietary",
                "attribution": "MetaTrader 5 Terminal Gateway Data",
            },
            mt5_tick_schema=True,
        )

    def get_symbol_metadata(
        self,
        symbol: str,
        *,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Get MT5 symbol metadata."""
        metadata = super().get_symbol_metadata(symbol, request_id=request_id)
        sym_upper = symbol.upper()
        if sym_upper == "SPX500":
            metadata["asset_class"] = "indices"
        elif sym_upper == "XAUUSD":
            metadata["asset_class"] = "metals"
        else:
            metadata["asset_class"] = "forex"
        return metadata


class CTraderAdapter(BrokerBackedAdapter):
    """cTrader source adapter."""

    def __init__(self) -> None:
        """Initialize cTrader adapter."""
        super().__init__(
            "ctrader",
            _get_ctrader_client,
            "cTrader OpenAPI client is not available",
            "BROKER_UNAVAILABLE",
            ["EURUSD", "GBPUSD"],
            {
                "ready": True,
                "license": "Proprietary",
                "attribution": "cTrader OpenAPI Client Feed",
            },
        )


class DukascopyAdapter(BrokerBackedAdapter):
    """Dukascopy source adapter."""

    def __init__(self) -> None:
        """Initialize Dukascopy adapter."""
        super().__init__(
            "dukascopy",
            _get_dukascopy_client,
            "Dukascopy service is not available",
            "SERVICE_UNAVAILABLE",
            ["EURUSD", "GBPUSD", "USDJPY"],
            {
                "ready": True,
                "license": "Restricted",
                "attribution": "Dukascopy Community Feed",
            },
        )


class BinanceAdapter(BrokerBackedAdapter):
    """Binance source adapter."""

    def __init__(self) -> None:
        """Initialize Binance adapter."""
        super().__init__(
            "binance",
            _get_binance_client,
            "Binance service is not available",
            "SERVICE_UNAVAILABLE",
            ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
            {
                "ready": True,
                "license": "Restricted",
                "attribution": "Binance Discovery Feed",
            },
        )


class YahooAdapter(BrokerBackedAdapter):
    """Yahoo Finance source adapter."""

    def __init__(self) -> None:
        """Initialize Yahoo Finance adapter."""
        super().__init__(
            "yahoo",
            _get_yahoo_client,
            "Yahoo Finance service is not available",
            "SERVICE_UNAVAILABLE",
            ["AAPL", "MSFT", "SPY"],
            {
                "ready": True,
                "license": "Restricted",
                "attribution": "Yahoo Finance Public Feed",
            },
        )


ADAPTER_REGISTRY: dict[str, SourceAdapterProtocol] = {
    "csv": CSVAdapter(),
    "parquet": ParquetAdapter(),
    "synthetic": SyntheticAdapter(),
    "mt5": MT5Adapter(),
    "ctrader": CTraderAdapter(),
    "dukascopy": DukascopyAdapter(),
    "binance": BinanceAdapter(),
    "yahoo": YahooAdapter(),
}


def get_data_source(source: str) -> SourceAdapterProtocol:
    """Resolve a data source adapter by name.

    Args:
        source: Source identifier.

    Returns:
        SourceAdapterProtocol: Registered data source adapter.

    Raises:
        ValidationError: If the source is unknown.
    """
    source_lower = source.lower()
    if source_lower not in ADAPTER_REGISTRY:
        msg = f"Unknown or unregistered source: {source}"
        raise ValidationError(msg)
    return ADAPTER_REGISTRY[source_lower]


def get_source_adapter(source: str) -> SourceAdapterProtocol:
    """Backward-compatible alias for resolving a data source adapter."""
    return get_data_source(source)
