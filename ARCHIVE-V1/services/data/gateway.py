"""Market data gateway router and source adapters.

Orchestrates historical, real-time, local, synthetic, and broker data queries.
Consolidates source adapters (CSV, Parquet, MT5, cTrader, etc.), persistent circuit
breakers, and the single data query service API.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol, cast, runtime_checkable

import pandas as pd

from app.services.data.licensing import validate_license
from app.services.data.models import (
    DataAvailability,
    OHLCVRecord,
    SpreadRecord,
    SymbolMetadata,
    TickRecord,
)
from app.services.data.storage import (
    db_helper,
    generate_cache_key,
    get_cached_data,
    load_local_dataset,
    set_cached_data,
)
from app.services.data.transforms import (
    generate_synthetic_bars,
    generate_synthetic_ticks,
)
from app.services.data.validation import (
    DEFAULT_OHLCV_LIMIT,
    DEFAULT_SPREAD_LIMIT,
    DEFAULT_TICK_LIMIT,
    MAX_OHLCV_LIMIT,
    MAX_SPREAD_LIMIT,
    MAX_TICK_LIMIT,
    normalize_numeric,
    validate_limit,
    validate_timeframe,
)
from app.services.utils.errors import DataError, ExternalServiceError, ValidationError
from app.services.utils.logger import logger
from app.services.utils.normalization import _parse_datetime


# --- 1. Source Adapter Protocol ---
@runtime_checkable
class SourceAdapterProtocol(Protocol):
    """Common internal source adapter protocol for all data providers."""

    def is_ready(self) -> bool:
        """Description.
            Check if source adapter is ready/configured.
        
        Args:
            None.
        
        Returns:
            bool.
        """
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
        """Description.
            Fetch normalized historical OHLCV data.
        
        Args:
            symbol: str.
            timeframe: str.
            start_time: datetime.
            end_time: datetime.
            request_id: str | None.
        
        Returns:
            list[dict[str, Any]].
        """
        ...

    def get_tick_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Description.
            Fetch normalized historical tick data.
        
        Args:
            symbol: str.
            start_time: datetime.
            end_time: datetime.
            request_id: str | None.
        
        Returns:
            list[dict[str, Any]].
        """
        ...

    def list_symbols(self, *, request_id: str | None = None) -> list[str]:
        """Description.
            List symbols discovered from the source.
        
        Args:
            request_id: str | None.
        
        Returns:
            list[str].
        """
        ...

    def get_symbol_metadata(
        self, symbol: str, *, request_id: str | None = None
    ) -> dict[str, Any]:
        """Description.
            Retrieve symbol metadata.
        
        Args:
            symbol: str.
            request_id: str | None.
        
        Returns:
            dict[str, Any].
        """
        ...


# --- 2. Rate Limiters ---
class TokenBucketLimiter:
    """A thread-safe simple Token Bucket rate limiter."""

    def __init__(self, rate: float, capacity: float) -> None:
        """Description.
            Initialize with a token replenishment rate (tokens/sec) and capacity.
        
        Args:
            rate: float.
            capacity: float.
        
        Returns:
            None.
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = datetime.now(UTC).timestamp()
        logger.debug(
            f"Initialized TokenBucketLimiter with rate={rate} and capacity={capacity}."
        )

    def consume(self) -> bool:
        """Description.
            Consume 1 token from the bucket. Returns True if successful.
        
        Args:
            None.
        
        Returns:
            bool.
        """
        now = datetime.now(UTC).timestamp()
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


RATE_LIMITERS: dict[str, TokenBucketLimiter] = {
    "mt5": TokenBucketLimiter(10.0, 20.0),
    "ctrader": TokenBucketLimiter(10.0, 20.0),
    "dukascopy": TokenBucketLimiter(5.0, 10.0),
    "binance": TokenBucketLimiter(5.0, 10.0),
    "ccxt": TokenBucketLimiter(5.0, 10.0),
    "yahoo": TokenBucketLimiter(5.0, 10.0),
    "csv": TokenBucketLimiter(100.0, 500.0),
    "parquet": TokenBucketLimiter(100.0, 500.0),
    "synthetic": TokenBucketLimiter(100.0, 500.0),
}


def check_rate_limit(source: str) -> None:
    """Description.
        Consume rate limit token or raise a BACKPRESSURE_EXCEEDED error.
    
    Args:
        source: str.
    
    Returns:
        None.
    """
    src_lower = source.lower()
    if src_lower in RATE_LIMITERS:
        limiter = RATE_LIMITERS[src_lower]
        if not limiter.consume():
            msg = f"Rate limit exceeded for source: {source}."
            raise ExternalServiceError(msg, code="BACKPRESSURE_EXCEEDED")


# --- 3. Circuit Breaker Handlers ---
def get_circuit_breaker(source: str) -> dict[str, Any]:
    """Description.
        Retrieve persisted circuit breaker state for a source.
    
    Args:
        source: str.
    
    Returns:
        dict[str, Any].
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
    """Description.
        Update and persist circuit breaker state.
    
    Args:
        source: str.
        state: str.
        failures_count: int.
        cooldown_expires: str | None.
    
    Returns:
        None.
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
    """Description.
        Check if the source's circuit breaker blocks execution.
    
    Args:
        source: str.
    
    Returns:
        None.
    """
    cb = get_circuit_breaker(source)
    if cb["state"] == "open":
        expires = cb["cooldown_expires"]
        if expires and datetime.now(UTC) > datetime.fromisoformat(expires):
            logger.info(
                f"Circuit breaker cooldown expired for {source}. "
                "Transitioning to half-open."
            )
            update_circuit_breaker(source, "half-open", cb["failures_count"])
        else:
            msg = f"Circuit breaker is open for source: {source} (blocked)."
            raise ExternalServiceError(msg, code="CIRCUIT_OPEN")


def _normalize_mt5_record(
    r: dict[str, Any], symbol: str, timeframe: str, source: str
) -> dict[str, Any]:
    """Description.
        Normalize a single MT5-style raw record.
    
    Args:
        r: dict[str, Any].
        symbol: str.
        timeframe: str.
        source: str.
    
    Returns:
        dict[str, Any].
    """
    logger.debug(
        f"Normalizing a single MT5-style raw record for symbol={symbol}, "
        f"timeframe={timeframe}, source={source}."
    )
    date_val = r.get("<DATE>") or r.get("DATE") or ""
    time_val = r.get("<TIME>") or r.get("TIME") or "00:00:00"
    date_val = str(date_val).replace(".", "-")
    dt_str = f"{date_val} {time_val}"
    try:
        dt = pd.to_datetime(dt_str)
        dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.tz_convert(UTC)
        ts_str = dt.isoformat()
    except (ValueError, TypeError):
        ts_str = dt_str

    def get_float(key: str) -> float:
        """Description.
            Return ``r[key]`` coerced to float, or ``0.0`` when missing/invalid.
        
        Args:
            key: str.
        
        Returns:
            float.
        """
        logger.debug(f"Coercing MT5 field '{key}' to float.")
        val = r.get(key)
        if val is None:
            return 0.0
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    op = get_float("<OPEN>")
    hi = get_float("<HIGH>")
    lo = get_float("<LOW>")
    cl = get_float("<CLOSE>")
    tick_vol = get_float("<TICKVOL>")
    real_vol = get_float("<VOL>")
    spread_val = get_float("<SPREAD>")

    return {
        "timestamp": ts_str,
        "open": op,
        "high": hi,
        "low": lo,
        "close": cl,
        "volume": tick_vol,
        "tick_volume": tick_vol,
        "real_volume": real_vol,
        "spread": spread_val,
        "source": source,
        "symbol": symbol,
        "timeframe": timeframe,
    }


def _normalize_std_record(
    r: dict[str, Any], symbol: str, timeframe: str, source: str
) -> dict[str, Any]:
    """Description.
        Normalize a single standard-style record.
    
    Args:
        r: dict[str, Any].
        symbol: str.
        timeframe: str.
        source: str.
    
    Returns:
        dict[str, Any].
    """
    norm_r = dict(r)
    if "timestamp" in norm_r:
        try:
            dt = pd.to_datetime(norm_r["timestamp"])
            dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.tz_convert(UTC)
            norm_r["timestamp"] = dt.isoformat()
        except (ValueError, TypeError) as ex:
            logger.warning(f"Failed to parse timestamp {norm_r.get('timestamp')}: {ex}")
    norm_r.setdefault("source", source)
    norm_r.setdefault("symbol", symbol)
    norm_r.setdefault("timeframe", timeframe)
    norm_r.setdefault("tick_volume", norm_r.get("volume", 0.0))
    norm_r.setdefault("real_volume", 0.0)
    norm_r.setdefault("spread", 0.0)
    if "volume" not in norm_r:
        norm_r["volume"] = norm_r.get("tick_volume", 0.0)
    return norm_r


def normalize_file_records(
    records: list[dict[str, Any]],
    symbol: str,
    timeframe: str,
    source: str,
) -> list[dict[str, Any]]:
    """Description.
        Normalize raw or MT5 file records to standard OHLCV schema.
    
    Args:
        records: list[dict[str, Any]].
        symbol: str.
        timeframe: str.
        source: str.
    
    Returns:
        list[dict[str, Any]].
    """
    logger.debug(
        f"Normalizing {len(records)} raw file records for symbol={symbol}, "
        f"timeframe={timeframe}, source={source} to standard schema."
    )
    if not records:
        return []

    first = records[0]
    is_mt5_style = any(str(k).startswith("<") and str(k).endswith(">") for k in first)

    normalized = []
    for r in records:
        if is_mt5_style:
            norm_r = _normalize_mt5_record(r, symbol, timeframe, source)
        else:
            norm_r = _normalize_std_record(r, symbol, timeframe, source)
        normalized.append(norm_r)
    return normalized


class CSVAdapter:
    """CSV File Data Source Adapter."""

    def is_ready(self) -> bool:
        """Description.
            Check if ready.
        
        Args:
            None.
        
        Returns:
            bool.
        """
        logger.debug("Checking if CSVAdapter is ready (always returns True).")
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
        """Description.
            Fetch market data.
        
        Args:
            symbol: str.
            timeframe: str.
            start_time: datetime.
            end_time: datetime.
            request_id: str | None.
        
        Returns:
            list[dict[str, Any]].
        """
        logger.debug(
            f"CSVAdapter: Fetching market data for symbol={symbol}, "
            f"timeframe={timeframe} from {start_time} to {end_time}."
        )
        filename = f"{symbol}_{timeframe}.csv"
        paths = [
            "data/processed",
            "data/raw",
            "data/processed/csv",
            "data/raw/csv",
        ]
        for p in paths:
            target_path = Path(p) / filename
            if target_path.exists():
                raw_records = load_local_dataset(
                    str(target_path), request_id=request_id
                )
                records = normalize_file_records(raw_records, symbol, timeframe, "csv")
                filtered = []
                for r in records:
                    ts = pd.to_datetime(r["timestamp"])
                    if start_time.tzinfo is None:
                        start_comp = start_time.replace(tzinfo=UTC)
                    else:
                        start_comp = start_time
                    if end_time.tzinfo is None:
                        end_comp = end_time.replace(tzinfo=UTC)
                    else:
                        end_comp = end_time

                    ts_utc = ts.tz_convert(UTC) if ts.tzinfo else ts.replace(tzinfo=UTC)
                    if start_comp <= ts_utc <= end_comp:
                        filtered.append(r)
                return filtered
        return []

    def get_tick_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Description.
            Fetch tick data.
        
        Args:
            symbol: str.
            start_time: datetime.
            end_time: datetime.
            request_id: str | None.
        
        Returns:
            list[dict[str, Any]].
        """
        logger.debug(
            f"CSVAdapter: Fetching tick data for symbol={symbol} "
            f"from {start_time} to {end_time}."
        )
        filename = f"{symbol}_ticks.csv"
        paths = [
            "data/processed",
            "data/raw",
            "data/processed/csv",
            "data/raw/csv",
        ]
        for p in paths:
            target_path = Path(p) / filename
            if target_path.exists():
                records = load_local_dataset(str(target_path), request_id=request_id)
                filtered = []
                for r in records:
                    ts = pd.to_datetime(r["timestamp"])
                    ts_utc = ts.tz_convert(UTC) if ts.tzinfo else ts.replace(tzinfo=UTC)
                    start_comp = (
                        start_time.replace(tzinfo=UTC)
                        if start_time.tzinfo is None
                        else start_time
                    )
                    end_comp = (
                        end_time.replace(tzinfo=UTC)
                        if end_time.tzinfo is None
                        else end_time
                    )
                    if start_comp <= ts_utc <= end_comp:
                        filtered.append(r)
                return filtered
        return []

    def list_symbols(self, *, request_id: str | None = None) -> list[str]:
        """Description.
            List symbols.
        
        Args:
            request_id: str | None.
        
        Returns:
            list[str].
        """
        logger.debug("CSVAdapter: Scanning directories to list available symbols.")
        _ = request_id
        symbols = set()
        paths = [
            "data/processed",
            "data/raw",
            "data/processed/csv",
            "data/raw/csv",
        ]
        for p in paths:
            path_obj = Path(p)
            if path_obj.exists():
                for f in path_obj.glob("*.csv"):
                    symbol = f.name.split("_")[0]
                    symbols.add(symbol)
        return sorted(symbols)

    def get_symbol_metadata(
        self,
        symbol: str,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Description.
            Get symbol metadata.
        
        Args:
            symbol: str.
            request_id: str | None.
        
        Returns:
            dict[str, Any].
        """
        logger.debug(
            f"CSVAdapter: Retrieving symbol metadata for symbol={symbol}."
        )
        return {
            "symbol": symbol,
            "source": "csv",
            "ready": True,
            "license": "Open",
            "attribution": "Local CSV Files",
        }


class ParquetAdapter:
    """Parquet File Data Source Adapter."""

    def is_ready(self) -> bool:
        """Description.
            Check if ready.
        
        Args:
            None.
        
        Returns:
            bool.
        """
        logger.debug("Checking if ParquetAdapter is ready (always returns True).")
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
        """Description.
            Fetch market data.
        
        Args:
            symbol: str.
            timeframe: str.
            start_time: datetime.
            end_time: datetime.
            request_id: str | None.
        
        Returns:
            list[dict[str, Any]].
        """
        logger.debug(
            f"ParquetAdapter: Fetching market data for symbol={symbol}, "
            f"timeframe={timeframe} from {start_time} to {end_time}."
        )
        filename = f"{symbol}_{timeframe}.parquet"
        paths = [
            "data/processed",
            "data/raw",
            "data/processed/parquet",
            "data/raw/parquet",
        ]
        for p in paths:
            target_path = Path(p) / filename
            if target_path.exists():
                raw_records = load_local_dataset(
                    str(target_path), request_id=request_id
                )
                records = normalize_file_records(
                    raw_records, symbol, timeframe, "parquet"
                )
                filtered = []
                for r in records:
                    ts = pd.to_datetime(r["timestamp"])
                    ts_utc = ts.tz_convert(UTC) if ts.tzinfo else ts.replace(tzinfo=UTC)
                    start_comp = (
                        start_time.replace(tzinfo=UTC)
                        if start_time.tzinfo is None
                        else start_time
                    )
                    end_comp = (
                        end_time.replace(tzinfo=UTC)
                        if end_time.tzinfo is None
                        else end_time
                    )
                    if start_comp <= ts_utc <= end_comp:
                        filtered.append(r)
                return filtered
        return []

    def get_tick_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Description.
            Fetch tick data.
        
        Args:
            symbol: str.
            start_time: datetime.
            end_time: datetime.
            request_id: str | None.
        
        Returns:
            list[dict[str, Any]].
        """
        logger.debug(
            f"ParquetAdapter: Fetching tick data for symbol={symbol} "
            f"from {start_time} to {end_time}."
        )
        filename = f"{symbol}_ticks.parquet"
        paths = [
            "data/processed",
            "data/raw",
            "data/processed/parquet",
            "data/raw/parquet",
        ]
        for p in paths:
            target_path = Path(p) / filename
            if target_path.exists():
                records = load_local_dataset(str(target_path), request_id=request_id)
                filtered = []
                for r in records:
                    ts = pd.to_datetime(r["timestamp"])
                    ts_utc = ts.tz_convert(UTC) if ts.tzinfo else ts.replace(tzinfo=UTC)
                    start_comp = (
                        start_time.replace(tzinfo=UTC)
                        if start_time.tzinfo is None
                        else start_time
                    )
                    end_comp = (
                        end_time.replace(tzinfo=UTC)
                        if end_time.tzinfo is None
                        else end_time
                    )
                    if start_comp <= ts_utc <= end_comp:
                        filtered.append(r)
                return filtered
        return []

    def list_symbols(self, *, request_id: str | None = None) -> list[str]:
        """Description.
            List symbols.
        
        Args:
            request_id: str | None.
        
        Returns:
            list[str].
        """
        logger.debug("ParquetAdapter: Scanning directories to list available symbols.")
        _ = request_id
        symbols = set()
        paths = [
            "data/processed",
            "data/raw",
            "data/processed/parquet",
            "data/raw/parquet",
        ]
        for p in paths:
            path_obj = Path(p)
            if path_obj.exists():
                for f in path_obj.glob("*.parquet"):
                    symbol = f.name.split("_")[0]
                    symbols.add(symbol)
        return sorted(symbols)

    def get_symbol_metadata(
        self,
        symbol: str,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Description.
            Get symbol metadata.
        
        Args:
            symbol: str.
            request_id: str | None.
        
        Returns:
            dict[str, Any].
        """
        logger.debug(
            f"ParquetAdapter: Retrieving symbol metadata for symbol={symbol}."
        )
        return {
            "symbol": symbol,
            "source": "parquet",
            "ready": True,
            "license": "Open",
            "attribution": "Local Parquet Files",
        }


class SyntheticAdapter:
    """Synthetic Data Source Adapter."""

    def is_ready(self) -> bool:
        """Description.
            Check if ready.
        
        Args:
            None.
        
        Returns:
            bool.
        """
        logger.debug("Checking if SyntheticAdapter is ready (always returns True).")
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
        """Description.
            Fetch market data.
        
        Args:
            symbol: str.
            timeframe: str.
            start_time: datetime.
            end_time: datetime.
            request_id: str | None.
        
        Returns:
            list[dict[str, Any]].
        """
        logger.debug(
            f"SyntheticAdapter: Generating synthetic bars for symbol={symbol}, "
            f"timeframe={timeframe}."
        )
        start_str = start_time.isoformat()
        return generate_synthetic_bars(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_str,
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
        """Description.
            Fetch tick data.
        
        Args:
            symbol: str.
            start_time: datetime.
            end_time: datetime.
            request_id: str | None.
        
        Returns:
            list[dict[str, Any]].
        """
        logger.debug(
            f"SyntheticAdapter: Generating synthetic ticks for symbol={symbol}."
        )
        start_str = start_time.isoformat()
        return generate_synthetic_ticks(
            symbol=symbol,
            start_time=start_str,
            num_ticks=250,
            start_price=1.10,
            average_spread=0.0002,
            volatility=0.0001,
            seed=42,
            request_id=request_id,
        )

    def list_symbols(self, *, request_id: str | None = None) -> list[str]:
        """Description.
            List symbols.
        
        Args:
            request_id: str | None.
        
        Returns:
            list[str].
        """
        logger.debug("SyntheticAdapter: Listing static EURUSD, GBPUSD, USDJPY, SPX500, XAUUSD symbols.")
        _ = request_id
        return ["EURUSD", "GBPUSD", "USDJPY", "SPX500", "XAUUSD"]

    def get_symbol_metadata(
        self,
        symbol: str,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Description.
            Get symbol metadata.
        
        Args:
            symbol: str.
            request_id: str | None.
        
        Returns:
            dict[str, Any].
        """
        logger.debug(
            f"SyntheticAdapter: Retrieving symbol metadata for symbol={symbol}."
        )
        asset_class = "forex"
        if symbol == "SPX500":
            asset_class = "indices"
        elif symbol == "XAUUSD":
            asset_class = "metals"
        return {
            "symbol": symbol,
            "source": "synthetic",
            "ready": True,
            "license": "Permissive",
            "attribution": "Synthetic Bar Generator",
            "asset_class": asset_class,
        }


class CCXTAdapter:
    """CCXT exchange OHLCV data source adapter."""

    _TIMEFRAME_MAP: dict[str, str] = {
        "M1": "1m",
        "M5": "5m",
        "M15": "15m",
        "M30": "30m",
        "H1": "1h",
        "H4": "4h",
        "D1": "1d",
        "W1": "1w",
    }
    _QUOTE_SUFFIXES: tuple[str, ...] = (
        "USDT",
        "USD",
        "USDC",
        "BTC",
        "ETH",
        "EUR",
    )

    def __init__(self, exchange_id: str = "binance") -> None:
        """Initialize the adapter with a default CCXT exchange.

        Args:
            exchange_id: CCXT exchange identifier.

        Returns:
            None.
        """
        self.exchange_id = exchange_id

    def is_ready(self) -> bool:
        """Check whether the CCXT dependency can be imported.

        Args:
            None.

        Returns:
            bool.
        """
        try:
            import ccxt  # noqa: F401
        except ImportError:
            return False
        return True

    def get_market_dataframe(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> pd.DataFrame:
        """Fetch CCXT OHLCV data as a provider DataFrame.

        Args:
            symbol: Instrument symbol.
            timeframe: Bar timeframe.
            start_time: Inclusive UTC start time.
            end_time: Inclusive UTC end time.
            request_id: Optional request correlation identifier.

        Returns:
            Provider OHLCV frame, or an empty frame when no rows are available.
        """
        try:
            import ccxt
        except ImportError as exc:
            msg = "ccxt is required for source='ccxt'."
            raise ExternalServiceError(msg, code="SERVICE_UNAVAILABLE") from exc

        ccxt_timeframe = self._TIMEFRAME_MAP.get(timeframe)
        if ccxt_timeframe is None:
            raise ValidationError(f"Unsupported CCXT timeframe: {timeframe}")

        exchange_class = getattr(ccxt, self.exchange_id, None)
        if exchange_class is None:
            raise ValidationError(f"Unknown CCXT exchange: {self.exchange_id}")

        exchange = exchange_class({"enableRateLimit": True})
        market_symbol = self._to_ccxt_symbol(symbol)
        since = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)
        rows: list[list[Any]] = []

        while since <= end_ms:
            batch = exchange.fetch_ohlcv(
                market_symbol,
                timeframe=ccxt_timeframe,
                since=since,
                limit=1000,
            )
            if not batch:
                break

            in_range = [row for row in batch if int(row[0]) <= end_ms]
            rows.extend(in_range)
            last_ts = int(batch[-1][0])
            if last_ts <= since or last_ts >= end_ms:
                break
            since = last_ts + 1

        if not rows:
            return pd.DataFrame()

        frame = pd.DataFrame(
            rows,
            columns=["Timestamp", "Open", "High", "Low", "Close", "Volume"],
        )
        frame["Timestamp"] = pd.to_datetime(
            frame["Timestamp"],
            unit="ms",
            utc=True,
        )
        frame["Spread"] = 0.0
        logger.debug(
            f"CCXTAdapter ({self.exchange_id}): Retrieved {len(frame)} "
            f"bar rows for symbol={symbol}, timeframe={timeframe}."
        )
        return frame

    def get_market_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch normalized historical OHLCV records.

        Args:
            symbol: Instrument symbol.
            timeframe: Bar timeframe.
            start_time: Inclusive UTC start time.
            end_time: Inclusive UTC end time.
            request_id: Optional request correlation identifier.

        Returns:
            OHLCV records.
        """
        frame = self.get_market_dataframe(
            symbol,
            timeframe,
            start_time,
            end_time,
            request_id=request_id,
        )
        records: list[dict[str, Any]] = []
        for _, row in frame.iterrows():
            records.append(
                {
                    "timestamp": row["Timestamp"].isoformat(),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": float(row["Volume"]),
                    "tick_volume": float(row["Volume"]),
                    "real_volume": 0.0,
                    "spread": float(row["Spread"]),
                    "source": "ccxt",
                    "symbol": symbol,
                    "timeframe": timeframe,
                }
            )
        return records

    def get_tick_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return no tick data; CCXT gateway support is OHLCV-only.

        Args:
            symbol: Instrument symbol.
            start_time: Inclusive UTC start time.
            end_time: Inclusive UTC end time.
            request_id: Optional request correlation identifier.

        Returns:
            Empty tick record list.
        """
        _ = symbol, start_time, end_time, request_id
        return []

    def list_symbols(self, *, request_id: str | None = None) -> list[str]:
        """List the common symbols supported by this usage adapter.

        Args:
            request_id: Optional request correlation identifier.

        Returns:
            Symbol list.
        """
        _ = request_id
        return ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

    def get_symbol_metadata(
        self,
        symbol: str,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Retrieve CCXT symbol metadata.

        Args:
            symbol: Instrument symbol.
            request_id: Optional request correlation identifier.

        Returns:
            Symbol metadata.
        """
        return {
            "symbol": symbol,
            "source": "ccxt",
            "ready": self.is_ready(),
            "license": "Restricted",
            "attribution": "CCXT Exchange API Data",
            "asset_class": "crypto",
        }

    def _to_ccxt_symbol(self, symbol: str) -> str:
        """Convert compact symbols like BTCUSDT to CCXT market symbols.

        Args:
            symbol: Compact or CCXT-formatted symbol.

        Returns:
            CCXT market symbol.
        """
        if "/" in symbol:
            return symbol
        upper = symbol.upper()
        for quote in self._QUOTE_SUFFIXES:
            if upper.endswith(quote) and len(upper) > len(quote):
                return f"{upper[:-len(quote)]}/{quote}"
        return upper


# --- 5. Broker-backed Source Adapters ---
def _mt5_client() -> Any:  # noqa: ANN401
    """Description.
        Lazily resolve the MT5 broker client.
    
    Args:
        None.
    
    Returns:
        Any.
    """
    logger.debug("Lazily resolving MT5 broker client dependency.")
    from app.services.brokers.mt5 import get_mt5_client

    return get_mt5_client()


def _ctrader_client() -> Any:  # noqa: ANN401
    """Description.
        Lazily resolve the cTrader broker client.
    
    Args:
        None.
    
    Returns:
        Any.
    """
    logger.debug("Lazily resolving cTrader broker client dependency.")
    from app.services.brokers.ctrader import get_ctrader_client

    return get_ctrader_client()


def _dukascopy_client() -> Any:  # noqa: ANN401
    """Description.
        Lazily resolve the Dukascopy broker client.
    
    Args:
        None.
    
    Returns:
        Any.
    """
    logger.debug("Lazily resolving Dukascopy broker client dependency.")
    from app.services.brokers.dukascopy import get_dukascopy_client

    return get_dukascopy_client()


def _binance_client() -> Any:  # noqa: ANN401
    """Description.
        Lazily resolve the Binance broker client.
    
    Args:
        None.
    
    Returns:
        Any.
    """
    logger.debug("Lazily resolving Binance broker client dependency.")
    from app.services.brokers.binance import get_binance_client

    return get_binance_client()


def _yahoo_client() -> Any:  # noqa: ANN401
    """Description.
        Lazily resolve the Yahoo Finance broker client.
    
    Args:
        None.
    
    Returns:
        Any.
    """
    logger.debug("Lazily resolving Yahoo Finance broker client dependency.")
    from app.services.brokers.yahoo import get_yahoo_client

    return get_yahoo_client()


def _mt5_asset_class(symbol: str) -> str:
    """Description.
        Resolve the asset class for an MT5 symbol.
    
    Args:
        symbol: str.
    
    Returns:
        str.
    """
    logger.debug(f"Resolving MT5 asset class for symbol: {symbol}")
    sym_upper = symbol.upper()
    if sym_upper == "SPX500":
        return "indices"
    if sym_upper == "XAUUSD":
        return "metals"
    return "forex"


@dataclass(frozen=True)
class _BrokerSpec:
    """Per-source configuration for the generic broker adapter."""

    source: str
    client_factory: Callable[[], Any]
    unavailable_code: str
    init_fail_log_prefix: str
    unavailable_msg_prefix: str
    post_connect_fail_msg: str
    license_type: str
    attribution: str
    symbols: tuple[str, ...]
    tick_mode: str = "standard"
    asset_class_resolver: Callable[[str], str] | None = None


class BrokerAdapter:
    """Generic active source adapter delegating to a configured broker client.

    All broker-backed sources share identical orchestration (circuit breaker
    barrier, lazy connect, OHLCV/tick normalization). Per-source differences are
    expressed through a ``_BrokerSpec`` rather than bespoke adapter classes.
    """

    def __init__(self, spec: _BrokerSpec) -> None:
        """Description.
            Initialize the adapter with its source specification.
        
        Args:
            spec: _BrokerSpec.
        
        Returns:
            None.
        """
        self._spec = spec
        logger.debug("Initialized broker adapter for %s.", spec.source)

    def is_ready(self) -> bool:
        """Description.
            Check if source adapter is ready/configured.
        
        Args:
            None.
        
        Returns:
            bool.
        """
        logger.debug(
            f"BrokerAdapter ({self._spec.source}): Checking if adapter is ready "
            f"(always returns True)."
        )
        return True

    def _connect(self, *, with_breaker: bool) -> Any:  # noqa: ANN401
        """Description.
            Resolve and connect the broker client, applying failure policy.
        
        Args:
            with_breaker: bool.
        
        Returns:
            Any.
        """
        spec = self._spec
        try:
            client = spec.client_factory()
            if not client.is_connected():
                client.connect()
        except Exception as e:
            logger.warning(f"{spec.init_fail_log_prefix}: {e}")
            if with_breaker:
                cb = get_circuit_breaker(spec.source)
                update_circuit_breaker(
                    spec.source,
                    "open" if cb["failures_count"] >= 4 else "closed",  # noqa: PLR2004
                    cb["failures_count"] + 1,
                    (datetime.now(UTC) + timedelta(seconds=60)).isoformat(),
                )
            msg = f"{spec.unavailable_msg_prefix}: {e}"
            raise ExternalServiceError(msg, code=spec.unavailable_code) from e
        return client

    def get_market_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Description.
            Fetch normalized historical OHLCV data.
        
        Args:
            symbol: str.
            timeframe: str.
            start_time: datetime.
            end_time: datetime.
            request_id: str | None.
        
        Returns:
            list[dict[str, Any]].
        """
        df = self.get_market_dataframe(
            symbol,
            timeframe,
            start_time,
            end_time,
            request_id=request_id,
        )
        if df.empty:
            return []

        logger.debug(
            f"BrokerAdapter ({self._spec.source}): Serializing {len(df)} "
            f"bar rows for symbol={symbol}, timeframe={timeframe}."
        )
        return [self._bar_record(row, symbol, timeframe) for _, row in df.iterrows()]

    def get_market_dataframe(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> pd.DataFrame:
        """Fetch broker OHLCV data as the provider DataFrame.

        Args:
            symbol: Instrument symbol.
            timeframe: Bar timeframe.
            start_time: Inclusive UTC start time.
            end_time: Inclusive UTC end time.
            request_id: Optional request correlation identifier.

        Returns:
            Provider OHLCV frame, or an empty frame when no rows are available.
        """
        logger.debug(
            f"BrokerAdapter ({self._spec.source}): Fetching market data for "
            f"symbol={symbol}, timeframe={timeframe} from {start_time} to {end_time}."
        )
        spec = self._spec
        check_circuit_breaker_barrier(spec.source)
        client = self._connect(with_breaker=True)

        if not client.is_connected():
            raise ExternalServiceError(
                spec.post_connect_fail_msg, code=spec.unavailable_code
            )

        df = client.get_bars(
            symbol=symbol,
            timeframe=timeframe,
            date_from=start_time,
            date_to=end_time,
        )
        if df is None or df.empty:
            return pd.DataFrame()

        logger.debug(
            f"BrokerAdapter ({self._spec.source}): Retrieved {len(df)} "
            f"bar rows for symbol={symbol}, timeframe={timeframe}."
        )
        return df.copy()

    def get_tick_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Description.
            Fetch normalized historical tick data.
        
        Args:
            symbol: str.
            start_time: datetime.
            end_time: datetime.
            request_id: str | None.
        
        Returns:
            list[dict[str, Any]].
        """
        df = self.get_tick_dataframe(
            symbol,
            start_time,
            end_time,
            request_id=request_id,
        )
        if df.empty:
            return []

        logger.debug(
            f"BrokerAdapter ({self._spec.source}): Serializing {len(df)} "
            f"tick rows for symbol={symbol}."
        )
        if self._spec.tick_mode == "mt5":
            return [self._tick_record_mt5(row, symbol) for _, row in df.iterrows()]
        return [self._tick_record_standard(row, symbol) for _, row in df.iterrows()]

    def get_tick_dataframe(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> pd.DataFrame:
        """Fetch broker tick data as the provider DataFrame.

        Args:
            symbol: Instrument symbol.
            start_time: Inclusive UTC start time.
            end_time: Inclusive UTC end time.
            request_id: Optional request correlation identifier.

        Returns:
            Provider tick frame, or an empty frame when no rows are available.
        """
        logger.debug(
            f"BrokerAdapter ({self._spec.source}): Fetching tick data for "
            f"symbol={symbol} from {start_time} to {end_time}."
        )
        spec = self._spec
        check_circuit_breaker_barrier(spec.source)
        client = self._connect(with_breaker=False)

        df = client.get_ticks(
            symbol=symbol,
            start=start_time,
            end=end_time,
            as_dataframe=True,
        )
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return pd.DataFrame()

        logger.debug(
            f"BrokerAdapter ({self._spec.source}): Retrieved {len(df)} "
            f"tick rows for symbol={symbol}."
        )
        return df.copy()

    def list_symbols(self, *, request_id: str | None = None) -> list[str]:
        """Description.
            List symbols discovered from the source.
        
        Args:
            request_id: str | None.
        
        Returns:
            list[str].
        """
        logger.debug(
            f"BrokerAdapter ({self._spec.source}): Listing allowed symbols: "
            f"{self._spec.symbols}"
        )
        _ = request_id
        return list(self._spec.symbols)

    def get_symbol_metadata(
        self,
        symbol: str,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Description.
            Retrieve symbol metadata.
        
        Args:
            symbol: str.
            request_id: str | None.
        
        Returns:
            dict[str, Any].
        """
        logger.debug(
            f"BrokerAdapter ({self._spec.source}): Retrieving symbol metadata "
            f"for symbol={symbol}."
        )
        spec = self._spec
        meta: dict[str, Any] = {
            "symbol": symbol,
            "source": spec.source,
            "ready": True,
            "license": spec.license_type,
            "attribution": spec.attribution,
        }
        if spec.asset_class_resolver is not None:
            meta["asset_class"] = spec.asset_class_resolver(symbol)
        return meta

    def _bar_record(
        self,
        row: Any,  # noqa: ANN401
        symbol: str,
        timeframe: str,
    ) -> dict[str, Any]:
        """Description.
            Normalize a single broker OHLCV row to the standard schema.
        
        Args:
            row: Any.
            symbol: str.
            timeframe: str.
        
        Returns:
            dict[str, Any].
        """
        ts = row["Timestamp"]
        ts_str = (
            ts.isoformat()
            if hasattr(ts, "isoformat")
            else pd.to_datetime(ts).isoformat()
        )
        return {
            "timestamp": ts_str,
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": float(row["Volume"]),
            "tick_volume": float(row["Volume"]),
            "real_volume": 0.0,
            "spread": float(row["Spread"]),
            "source": self._spec.source,
            "symbol": symbol,
            "timeframe": timeframe,
        }

    def _tick_record_standard(
        self,
        row: Any,  # noqa: ANN401
        symbol: str,
    ) -> dict[str, Any]:
        """Description.
            Normalize a single standard broker tick row.
        
        Args:
            row: Any.
            symbol: str.
        
        Returns:
            dict[str, Any].
        """
        ts = row["Timestamp"]
        ts_str = (
            ts.isoformat()
            if hasattr(ts, "isoformat")
            else pd.to_datetime(ts).isoformat()
        )
        return {
            "timestamp": ts_str,
            "bid": float(row["bid"]),
            "ask": float(row["ask"]),
            "last": float(row["last"]),
            "volume": float(row["volume"]),
            "spread": float(row["spread"]),
            "source": self._spec.source,
            "symbol": symbol,
        }

    def _tick_record_mt5(
        self,
        row: Any,  # noqa: ANN401
        symbol: str,
    ) -> dict[str, Any]:
        """Description.
            Normalize a single MT5-native tick row.
        
        Args:
            row: Any.
            symbol: str.
        
        Returns:
            dict[str, Any].
        """
        time_msc = int(row.get("time_msc", 0))
        if time_msc > 0:
            dt = pd.to_datetime(time_msc, unit="ms", utc=True)
        else:
            dt = pd.to_datetime(int(row.get("time", 0)), unit="s", utc=True)

        bid = float(row.get("bid", 0.0))
        ask = float(row.get("ask", 0.0))
        spread = ask - bid

        return {
            "timestamp": dt.isoformat(),
            "bid": bid,
            "ask": ask,
            "last": float(row.get("last", 0.0)),
            "volume": float(row.get("volume", 0.0)),
            "spread": spread,
            "source": self._spec.source,
            "symbol": symbol,
        }


_BROKER_SPECS: dict[str, _BrokerSpec] = {
    "mt5": _BrokerSpec(
        source="mt5",
        client_factory=_mt5_client,
        unavailable_code="BROKER_UNAVAILABLE",
        init_fail_log_prefix="MT5 initialization failed",
        unavailable_msg_prefix="MetaTrader 5 terminal is not available",
        post_connect_fail_msg="MT5 Client failed to connect to live broker.",
        license_type="Proprietary",
        attribution="MetaTrader 5 Terminal Gateway Data",
        symbols=("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "SPX500"),
        tick_mode="mt5",
        asset_class_resolver=_mt5_asset_class,
    ),
    "ctrader": _BrokerSpec(
        source="ctrader",
        client_factory=_ctrader_client,
        unavailable_code="BROKER_UNAVAILABLE",
        init_fail_log_prefix="cTrader initialization failed",
        unavailable_msg_prefix="cTrader OpenAPI client is not available",
        post_connect_fail_msg="cTrader Client failed to connect to live broker.",
        license_type="Proprietary",
        attribution="cTrader OpenAPI Client Feed",
        symbols=("EURUSD", "GBPUSD"),
    ),
    "dukascopy": _BrokerSpec(
        source="dukascopy",
        client_factory=_dukascopy_client,
        unavailable_code="SERVICE_UNAVAILABLE",
        init_fail_log_prefix="Dukascopy client initialization failed",
        unavailable_msg_prefix="Dukascopy service is not available",
        post_connect_fail_msg="Dukascopy Client failed to connect.",
        license_type="Restricted",
        attribution="Dukascopy Community Feed",
        symbols=("EURUSD", "GBPUSD", "USDJPY"),
    ),
    "binance": _BrokerSpec(
        source="binance",
        client_factory=_binance_client,
        unavailable_code="SERVICE_UNAVAILABLE",
        init_fail_log_prefix="Binance client initialization failed",
        unavailable_msg_prefix="Binance service is not available",
        post_connect_fail_msg="Binance Client failed to connect.",
        license_type="Restricted",
        attribution="Binance Discovery Feed",
        symbols=("BTCUSDT", "ETHUSDT", "SOLUSDT"),
    ),
    "yahoo": _BrokerSpec(
        source="yahoo",
        client_factory=_yahoo_client,
        unavailable_code="SERVICE_UNAVAILABLE",
        init_fail_log_prefix="Yahoo Finance client initialization failed",
        unavailable_msg_prefix="Yahoo Finance service is not available",
        post_connect_fail_msg="Yahoo Finance Client failed to connect.",
        license_type="Restricted",
        attribution="Yahoo Finance Public Feed",
        symbols=("AAPL", "MSFT", "SPY"),
    ),
}


# Adapter registry
ADAPTER_REGISTRY: dict[str, SourceAdapterProtocol] = {
    "csv": CSVAdapter(),
    "parquet": ParquetAdapter(),
    "synthetic": SyntheticAdapter(),
    "ccxt": CCXTAdapter(),
    "mt5": BrokerAdapter(_BROKER_SPECS["mt5"]),
    "ctrader": BrokerAdapter(_BROKER_SPECS["ctrader"]),
    "dukascopy": BrokerAdapter(_BROKER_SPECS["dukascopy"]),
    "binance": BrokerAdapter(_BROKER_SPECS["binance"]),
    "yahoo": BrokerAdapter(_BROKER_SPECS["yahoo"]),
}


def get_source_adapter(source: str) -> SourceAdapterProtocol:
    """Description.
        Retrieve the registered adapter for a source.
    
    Args:
        source: str.
    
    Returns:
        SourceAdapterProtocol.
    """
    source_lower = source.lower()
    if source_lower not in ADAPTER_REGISTRY:
        msg = f"Unknown or unregistered source: {source}"
        raise ValidationError(msg)
    return ADAPTER_REGISTRY[source_lower]


def _normalize_and_validate_records(
    records: list[dict[str, Any]],
    data_kind: str,
    symbol: str,
    source: str,
    workflow_context: str,
) -> list[dict[str, Any]]:
    """Description.
        Validate, normalize, and dump records based on data_kind.
    
    Args:
        records: list[dict[str, Any]].
        data_kind: str.
        symbol: str.
        source: str.
        workflow_context: str.
    
    Returns:
        list[dict[str, Any]].
    """
    validated = []
    for r in records:
        if data_kind == "ohlcv":
            bar = OHLCVRecord(**r)
            bar.open = normalize_numeric(bar.open, 5, workflow_context)
            bar.high = normalize_numeric(bar.high, 5, workflow_context)
            bar.low = normalize_numeric(bar.low, 5, workflow_context)
            bar.close = normalize_numeric(bar.close, 5, workflow_context)
            bar.spread = normalize_numeric(bar.spread, 1, workflow_context)
            validated.append(bar.model_dump())
        elif data_kind == "ticks":
            tick = TickRecord(**r)
            tick.bid = normalize_numeric(tick.bid, 5, workflow_context)
            tick.ask = normalize_numeric(tick.ask, 5, workflow_context)
            tick.last = normalize_numeric(tick.last, 5, workflow_context)
            tick.spread = normalize_numeric(tick.spread, 1, workflow_context)
            validated.append(tick.model_dump())
        elif data_kind == "spreads":
            bid_val = float(r.get("bid", 0.0))
            ask_val = float(r.get("ask", 0.0))
            spread_pts = float(r.get("spread", 0.0))
            if spread_pts <= 0.0 and ask_val >= bid_val:
                spread_pts = round((ask_val - bid_val) / 0.00001, 1)

            sp_rec = SpreadRecord(
                timestamp=r["timestamp"],
                symbol=symbol,
                bid=bid_val,
                ask=ask_val,
                spread_points=spread_pts,
                spread_pips=round(spread_pts / 10.0, 2),
                source=source,
            )
            sp_rec.bid = normalize_numeric(sp_rec.bid, 5, workflow_context)
            sp_rec.ask = normalize_numeric(sp_rec.ask, 5, workflow_context)
            sp_rec.spread_points = normalize_numeric(
                sp_rec.spread_points, 1, workflow_context
            )
            sp_rec.spread_pips = normalize_numeric(
                sp_rec.spread_pips, 2, workflow_context
            )
            validated.append(sp_rec.model_dump())
    return validated


def _check_gateway_cache(
    source: str,
    symbol: str,
    timeframe: str | None,
    start_time: datetime,
    end_time: datetime,
    stale_data_behavior: str,
    request_id: str | None = None,
) -> tuple[str, str, list[dict[str, Any]] | None]:
    """Description.
        Generate cache keys and check cache availability.
    
    Args:
        source: str.
        symbol: str.
        timeframe: str | None.
        start_time: datetime.
        end_time: datetime.
        stale_data_behavior: str.
        request_id: str | None.
    
    Returns:
        tuple[str, str, list[dict[str, Any]] | None].
    """
    cache_tf = timeframe or "ticks"
    cache_key = generate_cache_key(
        source,
        symbol,
        cache_tf,
        start_time.isoformat(),
        end_time.isoformat(),
    )
    cached = get_cached_data(cache_key, stale_data_behavior, request_id=request_id)
    return cache_key, cache_tf, cached["records"] if cached else None


def _download_from_adapter(
    source: str,
    symbol: str,
    timeframe: str | None,
    start_time: datetime,
    end_time: datetime,
    data_kind: str,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Description.
        Retrieve raw records from the registered source adapter.
    
    Args:
        source: str.
        symbol: str.
        timeframe: str | None.
        start_time: datetime.
        end_time: datetime.
        data_kind: str.
        request_id: str | None.
    
    Returns:
        list[dict[str, Any]].
    """
    adapter = get_source_adapter(source)
    if data_kind == "ohlcv":
        return adapter.get_market_data(
            symbol,
            timeframe or "M1",
            start_time,
            end_time,
            request_id=request_id,
        )
    if data_kind in ("ticks", "spreads"):
        return adapter.get_tick_data(
            symbol, start_time, end_time, request_id=request_id
        )
    return []


# --- 5. Unified Gateway Core Execution ---
def execute_gateway_request(  # noqa: C901
    source: str,
    symbol: str,
    timeframe: str | None,
    start_time: datetime,
    end_time: datetime,
    data_kind: str,
    stale_data_behavior: str = "refresh_and_return",
    workflow_context: str = "research",
    fallback_sources: list[str] | None = None,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Description.
        Internal gateway request execution, routing through adapters with cache.
    
    Args:
        source: str.
        symbol: str.
        timeframe: str | None.
        start_time: datetime.
        end_time: datetime.
        data_kind: str.
        stale_data_behavior: str.
        workflow_context: str.
        fallback_sources: list[str] | None.
        request_id: str | None.
    
    Returns:
        list[dict[str, Any]].
    """
    sources_to_try = [source]
    if fallback_sources:
        for f in fallback_sources:
            if f not in sources_to_try:
                sources_to_try.append(f)

    last_exception = None

    for current_source in sources_to_try:
        try:
            logger.debug(
                "get_data flow: cache lookup | "
                f"source={current_source}, symbol={symbol}, "
                f"kind={data_kind}, timeframe={timeframe or 'ticks'}",
                extra={"request_id": request_id},
            )

            # 1. Enforce licensing validation (fail closed)
            validate_license(
                current_source, symbol, workflow_context, request_id=request_id
            )

            # 2. Consume rate limits
            check_rate_limit(current_source)

            # 3. Cache checks (only for historical queries)
            cache_key, cache_tf, cached_records = _check_gateway_cache(
                current_source,
                symbol,
                timeframe,
                start_time,
                end_time,
                stale_data_behavior,
                request_id=request_id,
            )
            if cached_records is not None:
                logger.debug(
                    "get_data flow: cache hit -> return canonical records | "
                    f"kind={data_kind}, rows={len(cached_records)}",
                    extra={"request_id": request_id},
                )
                return cached_records

            # 4. Resolve adapter and download
            logger.debug(
                "get_data flow: cache miss -> source adapter records | "
                f"source={current_source}, symbol={symbol}, kind={data_kind}",
                extra={"request_id": request_id},
            )
            records = _download_from_adapter(
                current_source,
                symbol,
                timeframe,
                start_time,
                end_time,
                data_kind,
                request_id=request_id,
            )
            logger.debug(
                "get_data flow: source adapter returned records | "
                f"kind={data_kind}, rows={len(records)}",
                extra={"request_id": request_id},
            )

            if not records:
                logger.debug(
                    "get_data flow: cache canonical records | "
                    f"kind={data_kind}, rows=0",
                    extra={"request_id": request_id},
                )
                set_cached_data(
                    cache_key,
                    current_source,
                    symbol,
                    cache_tf,
                    start_time.isoformat(),
                    end_time.isoformat(),
                    [],
                    ttl_seconds=60,
                    request_id=request_id,
                )
                return []

            # 5. Validate schemas and normalize
            logger.debug(
                "get_data flow: record validation/normalization | "
                f"kind={data_kind}, rows={len(records)}",
                extra={"request_id": request_id},
            )
            validated = _normalize_and_validate_records(
                records=records,
                data_kind=data_kind,
                symbol=symbol,
                source=current_source,
                workflow_context=workflow_context,
            )

            # 6. Cache validated records
            ttl = 900
            if data_kind == "ohlcv":
                ttl = 3600 if timeframe != "D1" else 86400

            logger.debug(
                "get_data flow: cache canonical records | "
                f"kind={data_kind}, rows={len(validated)}",
                extra={"request_id": request_id},
            )
            set_cached_data(
                cache_key,
                current_source,
                symbol,
                cache_tf,
                start_time.isoformat(),
                end_time.isoformat(),
                validated,
                ttl_seconds=ttl,
                request_id=request_id,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(
                f"Request failed on source {current_source}: {e}. Trying fallback."
            )
            last_exception = e
        else:
            return validated

    if last_exception:
        if isinstance(last_exception, ValidationError | ExternalServiceError):
            raise last_exception
        err_msg = f"Gateway request failed: {last_exception}"
        raise DataError(err_msg) from last_exception

    return []


def _download_ohlcv_dataframe_from_adapter(
    source: str,
    symbol: str,
    timeframe: str,
    start_time: datetime,
    end_time: datetime,
    request_id: str | None = None,
) -> pd.DataFrame:
    """Retrieve OHLCV data from an adapter as a DataFrame.

    Broker adapters can return their provider DataFrame directly. File and
    synthetic adapters still expose records, so they are converted once at the
    gateway boundary before vectorized canonicalization.

    Args:
        source: Source adapter name.
        symbol: Instrument symbol.
        timeframe: Bar timeframe.
        start_time: Inclusive UTC start time.
        end_time: Inclusive UTC end time.
        request_id: Optional request correlation identifier.

    Returns:
        Provider or record-derived OHLCV DataFrame.
    """
    adapter = get_source_adapter(source)
    if isinstance(adapter, BrokerAdapter | CCXTAdapter):
        return adapter.get_market_dataframe(
            symbol,
            timeframe,
            start_time,
            end_time,
            request_id=request_id,
        )

    records = adapter.get_market_data(
        symbol,
        timeframe,
        start_time,
        end_time,
        request_id=request_id,
    )
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)


def _download_tick_dataframe_from_adapter(
    source: str,
    symbol: str,
    start_time: datetime,
    end_time: datetime,
    request_id: str | None = None,
) -> pd.DataFrame:
    """Retrieve tick data from an adapter as a DataFrame.

    Args:
        source: Source adapter name.
        symbol: Instrument symbol.
        start_time: Inclusive UTC start time.
        end_time: Inclusive UTC end time.
        request_id: Optional request correlation identifier.

    Returns:
        Provider or record-derived tick DataFrame.
    """
    adapter = get_source_adapter(source)
    if isinstance(adapter, BrokerAdapter):
        return adapter.get_tick_dataframe(
            symbol,
            start_time,
            end_time,
            request_id=request_id,
        )

    records = adapter.get_tick_data(
        symbol,
        start_time,
        end_time,
        request_id=request_id,
    )
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)


# --- 6. Standardized DataFrame schema ---
# The canonical OHLCV frame used across the codebase: a non-null UTC ``datetime``
# index plus ``open``/``high``/``low``/``close`` (required, non-null) and
# ``volume``/``spread`` (present, but may be null when a platform omits them).
OHLCV_REQUIRED_COLUMNS: tuple[str, ...] = ("open", "high", "low", "close")
OHLCV_OPTIONAL_COLUMNS: tuple[str, ...] = ("volume", "spread")
OHLCV_COLUMNS: tuple[str, ...] = (*OHLCV_REQUIRED_COLUMNS, *OHLCV_OPTIONAL_COLUMNS)


def _empty_datetime_index() -> pd.DatetimeIndex:
    """Description.
        Build an empty UTC DatetimeIndex named ``datetime``.

    Args:
        None.

    Returns:
        pd.DatetimeIndex.
    """
    return pd.DatetimeIndex([], tz="UTC", name="datetime")


def _records_to_dataframe(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Description.
        Build a DataFrame indexed by a UTC ``datetime`` index from records.

        The ``timestamp`` field of each record becomes the index; every other
        field is preserved as a column. Used for tick, spread, and volume rows
        whose natural columns differ from the OHLCV bar schema.

    Args:
        records: list[dict[str, Any]].

    Returns:
        pd.DataFrame.
    """
    if not records:
        return pd.DataFrame(index=_empty_datetime_index())
    df = pd.DataFrame(records)
    if "timestamp" in df.columns:
        index = pd.DatetimeIndex(
            pd.to_datetime(df["timestamp"], utc=True, format="mixed"),
            name="datetime",
        )
        df = df.drop(columns=["timestamp"])
        df.index = index
        df = df.sort_index()
    return df


def _ohlcv_records_to_dataframe(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Description.
        Build the standardized OHLCV DataFrame from validated bar records.

        Returns a frame indexed by a non-null UTC ``datetime`` index with
        columns ``open``, ``high``, ``low``, ``close`` (required, non-null) plus
        ``volume`` and ``spread`` (present, but null when a platform does not
        supply them). This is the canonical shape used across the codebase,
        independent of the originating source/platform.

    Args:
        records: list[dict[str, Any]].

    Returns:
        pd.DataFrame.
    """
    if not records:
        return pd.DataFrame(
            {col: pd.Series(dtype="float64") for col in OHLCV_COLUMNS},
            index=_empty_datetime_index(),
        )

    df = pd.DataFrame(records)
    index = pd.DatetimeIndex(
        pd.to_datetime(df["timestamp"], utc=True, format="mixed"),
        name="datetime",
    )
    out = pd.DataFrame(index=index)
    for col in OHLCV_REQUIRED_COLUMNS:
        out[col] = pd.to_numeric(df[col], errors="coerce").to_numpy()
    for col in OHLCV_OPTIONAL_COLUMNS:
        if col in df.columns:
            out[col] = pd.to_numeric(df[col], errors="coerce").to_numpy()
        else:
            out[col] = float("nan")
    return out.sort_index()


def _resolve_ohlcv_column(
    columns_by_key: dict[str, str],
    candidates: tuple[str, ...],
    label: str,
    required: bool,
) -> str | None:
    """Resolve a source OHLCV column from normalized candidate names.

    Args:
        columns_by_key: Mapping of normalized column names to original names.
        candidates: Accepted normalized names for the target field.
        label: Reader-facing field label for validation errors.
        required: Whether the field must be present.

    Returns:
        The original column name, or ``None`` for missing optional fields.
    """
    for candidate in candidates:
        if candidate in columns_by_key:
            return columns_by_key[candidate]
    if required:
        raise ValidationError(f"Missing required OHLCV column: {label}.")
    return None


def _canonicalize_ohlcv_dataframe(
    frame: pd.DataFrame,
    source: str,
    symbol: str,
    timeframe: str,
    workflow_context: str,  # noqa: ARG001
) -> pd.DataFrame:
    """Validate and normalize an OHLCV frame with vectorized operations.

    Args:
        frame: Provider or record-derived OHLCV frame.
        source: Source adapter name.
        symbol: Instrument symbol.
        timeframe: Bar timeframe.
        workflow_context: Workflow context retained for API symmetry.

    Returns:
        Canonical OHLCV frame indexed by UTC ``datetime``.
    """
    if frame.empty:
        return pd.DataFrame(
            {col: pd.Series(dtype="float64") for col in OHLCV_COLUMNS},
            index=_empty_datetime_index(),
        )

    columns_by_key = {
        str(column).strip().lower(): str(column) for column in frame.columns
    }
    timestamp_column = _resolve_ohlcv_column(
        columns_by_key,
        ("timestamp", "datetime", "date", "time", "open_time"),
        "timestamp",
        required=not isinstance(frame.index, pd.DatetimeIndex),
    )
    if timestamp_column is None:
        timestamp_values = frame.index
    else:
        timestamp_values = frame[timestamp_column]

    index = pd.DatetimeIndex(
        pd.to_datetime(timestamp_values, utc=True, errors="coerce"),
        name="datetime",
    )
    valid_index = pd.Series(index.notna(), index=frame.index)
    if not bool(valid_index.all()):
        logger.warning(
            f"Dropping {int((~valid_index).sum())} OHLCV rows with invalid "
            f"timestamps for source={source}, symbol={symbol}, timeframe={timeframe}."
        )

    source_frame = frame.loc[valid_index].copy()
    index = pd.DatetimeIndex(index[valid_index.to_numpy()], name="datetime")
    out = pd.DataFrame(index=index)

    field_candidates = {
        "open": ("open", "open_price"),
        "high": ("high", "high_price"),
        "low": ("low", "low_price"),
        "close": ("close", "close_price", "last"),
        "volume": ("volume", "tick_volume", "real_volume"),
        "spread": ("spread",),
    }
    for column in OHLCV_REQUIRED_COLUMNS:
        source_column = _resolve_ohlcv_column(
            columns_by_key,
            field_candidates[column],
            column,
            required=True,
        )
        out[column] = pd.to_numeric(
            source_frame[source_column],
            errors="coerce",
        ).round(5).to_numpy()

    for column in OHLCV_OPTIONAL_COLUMNS:
        source_column = _resolve_ohlcv_column(
            columns_by_key,
            field_candidates[column],
            column,
            required=False,
        )
        if source_column is None:
            out[column] = float("nan")
        else:
            values = pd.to_numeric(source_frame[source_column], errors="coerce")
            if column == "spread":
                out[column] = values.round(1).to_numpy()
            else:
                out[column] = values.to_numpy()

    if out[list(OHLCV_REQUIRED_COLUMNS)].isna().any().any():
        raise ValidationError(
            f"OHLCV data contains null required prices for "
            f"source={source}, symbol={symbol}, timeframe={timeframe}."
        )

    invalid_ohlc = (
        (out["high"] < out[["open", "close"]].max(axis=1))
        | (out["low"] > out[["open", "close"]].min(axis=1))
        | (out["high"] < out["low"])
    )
    if bool(invalid_ohlc.any()):
        raise ValidationError(
            f"OHLCV data contains {int(invalid_ohlc.sum())} invalid bars "
            f"for source={source}, symbol={symbol}, timeframe={timeframe}."
        )

    return out.sort_index()


def _ohlcv_dataframe_to_cache_records(
    frame: pd.DataFrame,
    source: str,
    symbol: str,
    timeframe: str,
) -> list[dict[str, Any]]:
    """Serialize a canonical OHLCV frame to cache-compatible records.

    Args:
        frame: Canonical OHLCV DataFrame.
        source: Source adapter name.
        symbol: Instrument symbol.
        timeframe: Bar timeframe.

    Returns:
        Records compatible with the existing JSON cache schema.
    """
    records: list[dict[str, Any]] = []
    for timestamp, row in frame.iterrows():
        volume = row.get("volume")
        records.append(
            {
                "timestamp": timestamp.isoformat(),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": None if pd.isna(volume) else float(volume),
                "tick_volume": None if pd.isna(volume) else float(volume),
                "real_volume": 0.0,
                "spread": (
                    None
                    if pd.isna(row.get("spread"))
                    else float(row.get("spread"))
                ),
                "source": source,
                "symbol": symbol,
                "timeframe": timeframe,
            }
        )
    return records


def _resolve_column(
    columns_by_key: dict[str, str],
    candidates: tuple[str, ...],
) -> str | None:
    """Resolve a source column from normalized candidate names.

    Args:
        columns_by_key: Mapping of normalized column names to original names.
        candidates: Accepted normalized names.

    Returns:
        The original column name, or ``None`` when no candidate is present.
    """
    for candidate in candidates:
        if candidate in columns_by_key:
            return columns_by_key[candidate]
    return None


def _canonicalize_tick_dataframe(
    frame: pd.DataFrame,
    source: str,
    symbol: str,
) -> pd.DataFrame:
    """Validate and normalize a tick frame with vectorized operations.

    Args:
        frame: Provider or record-derived tick frame.
        source: Source adapter name.
        symbol: Instrument symbol.

    Returns:
        Canonical tick DataFrame indexed by UTC ``datetime``.
    """
    if frame.empty:
        return pd.DataFrame(index=_empty_datetime_index())

    columns_by_key = {
        str(column).strip().lower(): str(column) for column in frame.columns
    }
    timestamp_column = _resolve_column(
        columns_by_key,
        ("timestamp", "datetime", "time", "time_msc", "date"),
    )
    if timestamp_column is None:
        timestamp_values = frame.index
        timestamp_unit = None
    else:
        timestamp_values = frame[timestamp_column]
        timestamp_key = timestamp_column.lower()
        if timestamp_key == "time_msc":
            timestamp_unit = "ms"
        elif timestamp_key == "time" and pd.api.types.is_numeric_dtype(timestamp_values):
            timestamp_unit = "s"
        else:
            timestamp_unit = None

    if timestamp_unit is None:
        index_values = pd.to_datetime(
            timestamp_values,
            utc=True,
            errors="coerce",
            format="mixed",
        )
    else:
        index_values = pd.to_datetime(
            timestamp_values,
            unit=timestamp_unit,
            utc=True,
            errors="coerce",
        )
    index = pd.DatetimeIndex(index_values, name="datetime")
    valid_index = pd.Series(index.notna(), index=frame.index)
    if not bool(valid_index.all()):
        logger.warning(
            f"Dropping {int((~valid_index).sum())} tick rows with invalid "
            f"timestamps for source={source}, symbol={symbol}."
        )

    source_frame = frame.loc[valid_index].copy()
    index = pd.DatetimeIndex(index[valid_index.to_numpy()], name="datetime")
    out = pd.DataFrame(index=index)

    for column, candidates in {
        "bid": ("bid", "Bid"),
        "ask": ("ask", "Ask"),
        "last": ("last", "Last", "price"),
        "volume": ("volume", "Volume", "tick_volume"),
        "spread": ("spread", "Spread"),
    }.items():
        source_column = _resolve_column(
            columns_by_key,
            tuple(candidate.lower() for candidate in candidates),
        )
        if source_column is None:
            out[column] = float("nan")
        else:
            out[column] = pd.to_numeric(
                source_frame[source_column],
                errors="coerce",
            ).to_numpy()

    missing_last = out["last"].isna()
    if bool(missing_last.any()):
        out.loc[missing_last, "last"] = (
            out.loc[missing_last, ["bid", "ask"]].mean(axis=1)
        )

    missing_spread = out["spread"].isna()
    if bool(missing_spread.any()):
        out.loc[missing_spread, "spread"] = (
            out.loc[missing_spread, "ask"] - out.loc[missing_spread, "bid"]
        )

    invalid_quotes = out["bid"].notna() & out["ask"].notna() & (out["ask"] < out["bid"])
    if bool(invalid_quotes.any()):
        raise ValidationError(
            f"Tick data contains {int(invalid_quotes.sum())} rows where ask < bid "
            f"for source={source}, symbol={symbol}."
        )

    out["source"] = source
    out["symbol"] = symbol
    return out.sort_index()


def _tick_dataframe_to_cache_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Serialize a canonical tick frame to cache-compatible records.

    Args:
        frame: Canonical tick DataFrame.

    Returns:
        Records compatible with the existing JSON cache schema.
    """
    records: list[dict[str, Any]] = []
    for timestamp, row in frame.iterrows():
        records.append(
            {
                "timestamp": timestamp.isoformat(),
                "bid": None if pd.isna(row.get("bid")) else float(row.get("bid")),
                "ask": None if pd.isna(row.get("ask")) else float(row.get("ask")),
                "last": (
                    None if pd.isna(row.get("last")) else float(row.get("last"))
                ),
                "volume": (
                    None
                    if pd.isna(row.get("volume"))
                    else float(row.get("volume"))
                ),
                "spread": (
                    None
                    if pd.isna(row.get("spread"))
                    else float(row.get("spread"))
                ),
                "source": str(row.get("source", "")),
                "symbol": str(row.get("symbol", "")),
            }
        )
    return records


def _spread_dataframe_from_ticks(frame: pd.DataFrame) -> pd.DataFrame:
    """Build the public spread DataFrame from canonical ticks.

    Args:
        frame: Canonical tick DataFrame.

    Returns:
        Spread DataFrame indexed by UTC ``datetime``.
    """
    columns = ["bid", "ask", "spread", "source", "symbol"]
    if frame.empty:
        return pd.DataFrame(columns=columns, index=_empty_datetime_index())
    available = [column for column in columns if column in frame.columns]
    return frame[available].copy()


def execute_gateway_dataframe_request(  # noqa: C901
    source: str,
    symbol: str,
    timeframe: str,
    start_time: datetime,
    end_time: datetime,
    stale_data_behavior: str = "refresh_and_return",
    workflow_context: str = "research",
    fallback_sources: list[str] | None = None,
    request_id: str | None = None,
) -> pd.DataFrame:
    """Execute an OHLCV gateway request using a DataFrame-first flow.

    Args:
        source: Preferred source adapter name.
        symbol: Instrument symbol.
        timeframe: Bar timeframe.
        start_time: Inclusive UTC start time.
        end_time: Inclusive UTC end time.
        stale_data_behavior: Cache stale-data policy.
        workflow_context: Licensing and numeric normalization context.
        fallback_sources: Ordered fallback source names.
        request_id: Optional request correlation identifier.

    Returns:
        Canonical OHLCV DataFrame.
    """
    sources_to_try = [source]
    if fallback_sources:
        for fallback_source in fallback_sources:
            if fallback_source not in sources_to_try:
                sources_to_try.append(fallback_source)

    last_exception: Exception | None = None

    for current_source in sources_to_try:
        try:
            logger.debug(
                "get_data flow: cache lookup | "
                f"source={current_source}, symbol={symbol}, timeframe={timeframe}",
                extra={"request_id": request_id},
            )
            validate_license(
                current_source, symbol, workflow_context, request_id=request_id
            )
            check_rate_limit(current_source)

            cache_key, cache_tf, cached_records = _check_gateway_cache(
                current_source,
                symbol,
                timeframe,
                start_time,
                end_time,
                stale_data_behavior,
                request_id=request_id,
            )
            if cached_records is not None:
                frame = _ohlcv_records_to_dataframe(cached_records)
                logger.debug(
                    "get_data flow: cache hit -> return canonical OHLCV "
                    f"DataFrame | rows={len(frame)}",
                    extra={"request_id": request_id},
                )
                return frame

            logger.debug(
                "get_data flow: cache miss -> source adapter OHLCV DataFrame | "
                f"source={current_source}, symbol={symbol}, timeframe={timeframe}",
                extra={"request_id": request_id},
            )

            raw_frame = _download_ohlcv_dataframe_from_adapter(
                current_source,
                symbol,
                timeframe,
                start_time,
                end_time,
                request_id=request_id,
            )
            logger.debug(
                "get_data flow: source adapter returned OHLCV DataFrame | "
                f"rows={len(raw_frame)}",
                extra={"request_id": request_id},
            )
            logger.debug(
                "get_data flow: vectorized DataFrame validation/normalization",
                extra={"request_id": request_id},
            )
            canonical = _canonicalize_ohlcv_dataframe(
                raw_frame,
                current_source,
                symbol,
                timeframe,
                workflow_context,
            )
            logger.debug(
                "get_data flow: cache canonical data | "
                f"rows={len(canonical)}",
                extra={"request_id": request_id},
            )
            cache_records = _ohlcv_dataframe_to_cache_records(
                canonical,
                current_source,
                symbol,
                timeframe,
            )
            ttl = 3600 if timeframe != "D1" else 86400
            if canonical.empty:
                ttl = 60
            set_cached_data(
                cache_key,
                current_source,
                symbol,
                cache_tf,
                start_time.isoformat(),
                end_time.isoformat(),
                cache_records,
                ttl_seconds=ttl,
                request_id=request_id,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(
                f"OHLCV frame request failed on source {current_source}: {e}. "
                f"Trying fallback."
            )
            last_exception = e
        else:
            return canonical

    if last_exception:
        if isinstance(last_exception, ValidationError | ExternalServiceError):
            raise last_exception
        err_msg = f"Gateway OHLCV frame request failed: {last_exception}"
        raise DataError(err_msg) from last_exception

    return pd.DataFrame(
        {col: pd.Series(dtype="float64") for col in OHLCV_COLUMNS},
        index=_empty_datetime_index(),
    )


def execute_gateway_tick_dataframe_request(  # noqa: C901
    source: str,
    symbol: str,
    start_time: datetime,
    end_time: datetime,
    data_kind: str,
    limit: int,
    stale_data_behavior: str = "refresh_and_return",
    workflow_context: str = "research",
    fallback_sources: list[str] | None = None,
    request_id: str | None = None,
) -> pd.DataFrame:
    """Execute a tick/spread request using a DataFrame-first flow.

    Args:
        source: Preferred source adapter name.
        symbol: Instrument symbol.
        start_time: Inclusive UTC start time.
        end_time: Inclusive UTC end time.
        data_kind: ``ticks`` or ``spreads``.
        limit: Maximum rows returned by the public request.
        stale_data_behavior: Cache stale-data policy.
        workflow_context: Licensing and numeric normalization context.
        fallback_sources: Ordered fallback source names.
        request_id: Optional request correlation identifier.

    Returns:
        Canonical tick or spread DataFrame.
    """
    sources_to_try = [source]
    if fallback_sources:
        for fallback_source in fallback_sources:
            if fallback_source not in sources_to_try:
                sources_to_try.append(fallback_source)

    last_exception: Exception | None = None

    for current_source in sources_to_try:
        try:
            logger.debug(
                "get_data flow: cache lookup | "
                f"source={current_source}, symbol={symbol}, kind={data_kind}",
                extra={"request_id": request_id},
            )
            validate_license(
                current_source, symbol, workflow_context, request_id=request_id
            )
            check_rate_limit(current_source)

            cache_key, cache_tf, cached_records = _check_gateway_cache(
                current_source,
                symbol,
                data_kind,
                start_time,
                end_time,
                stale_data_behavior,
                request_id=request_id,
            )
            if cached_records is not None:
                frame = _records_to_dataframe(cached_records).iloc[:limit]
                if data_kind == "spreads":
                    frame = _spread_dataframe_from_ticks(frame)
                logger.debug(
                    "get_data flow: cache hit -> return DataFrame | "
                    f"kind={data_kind}, rows={len(frame)}",
                    extra={"request_id": request_id},
                )
                return frame

            logger.debug(
                "get_data flow: cache miss -> source adapter tick DataFrame | "
                f"source={current_source}, symbol={symbol}, kind={data_kind}",
                extra={"request_id": request_id},
            )
            raw_frame = _download_tick_dataframe_from_adapter(
                current_source,
                symbol,
                start_time,
                end_time,
                request_id=request_id,
            )
            logger.debug(
                "get_data flow: source adapter returned tick DataFrame | "
                f"rows={len(raw_frame)}",
                extra={"request_id": request_id},
            )
            logger.debug(
                "get_data flow: vectorized DataFrame validation/normalization | "
                f"kind={data_kind}",
                extra={"request_id": request_id},
            )
            canonical_ticks = _canonicalize_tick_dataframe(
                raw_frame,
                current_source,
                symbol,
            )
            result = canonical_ticks.iloc[:limit]
            if data_kind == "spreads":
                result = _spread_dataframe_from_ticks(result)

            if len(canonical_ticks) <= limit:
                logger.debug(
                    "get_data flow: cache canonical records | "
                    f"kind={data_kind}, rows={len(canonical_ticks)}",
                    extra={"request_id": request_id},
                )
                set_cached_data(
                    cache_key,
                    current_source,
                    symbol,
                    cache_tf,
                    start_time.isoformat(),
                    end_time.isoformat(),
                    _tick_dataframe_to_cache_records(canonical_ticks),
                    ttl_seconds=900,
                    request_id=request_id,
                )
            else:
                logger.debug(
                    "get_data flow: skip cache for truncated tick result | "
                    f"kind={data_kind}, source_rows={len(canonical_ticks)}, "
                    f"return_rows={len(result)}",
                    extra={"request_id": request_id},
                )
        except Exception as e:  # noqa: BLE001
            logger.warning(
                f"Tick frame request failed on source {current_source}: {e}. "
                f"Trying fallback."
            )
            last_exception = e
        else:
            return result

    if last_exception:
        if isinstance(last_exception, ValidationError | ExternalServiceError):
            raise last_exception
        err_msg = f"Gateway tick frame request failed: {last_exception}"
        raise DataError(err_msg) from last_exception

    return pd.DataFrame(index=_empty_datetime_index())


# --- 7. Clean Service APIs ---
def get_data(
    symbol: str,
    start_time: str,
    end_time: str,
    data_kind: str = "ohlcv",
    timeframe: str | None = None,
    source: str = "csv",
    limit: int | None = None,
    stale_data_behavior: str = "refresh_and_return",
    workflow_context: str = "research",
    fallback_sources: list[str] | None = None,
    request_id: str | None = None,
) -> pd.DataFrame:
    """Description.
        Retrieve normalized market data (ohlcv, ticks, spreads, or volume).

        Always returns a ``pandas.DataFrame`` indexed by a UTC ``datetime``
        index, regardless of the originating platform. For ``ohlcv`` the frame
        carries the standardized columns ``open``/``high``/``low``/``close``
        (non-null) plus ``volume``/``spread`` (nullable). Tick/spread/volume
        kinds retain their natural columns.

    Args:
        symbol: str.
        start_time: str.
        end_time: str.
        data_kind: str.
        timeframe: str | None.
        source: str.
        limit: int | None.
        stale_data_behavior: str.
        workflow_context: str.
        fallback_sources: list[str] | None.
        request_id: str | None.

    Returns:
        pd.DataFrame.
    """
    logger.debug(
        "get_data flow: validate request once | "
        f"symbol={symbol}, kind={data_kind}, timeframe={timeframe}, "
        f"source={source}, range={start_time} to {end_time}, limit={limit}",
        extra={"request_id": request_id},
    )
    # Lightweight UTC parse: the service layer only needs a datetime, not the
    # tool-response envelope/DatetimeResponse machinery that normalize_timestamp
    # (a tools-layer helper) builds and logs for every call.
    try:
        t_start = _parse_datetime(start_time).astimezone(UTC)
        t_end = _parse_datetime(end_time).astimezone(UTC)
    except (ValueError, TypeError) as exc:
        raise ValidationError(str(exc)) from exc

    kind = data_kind.lower()
    if kind not in ("ohlcv", "ticks", "spreads", "volume"):
        err_msg = f"Unsupported data_kind: {data_kind}"
        raise ValidationError(err_msg)

    if kind == "ohlcv":
        if not timeframe:
            raise ValidationError("timeframe is required for ohlcv data.")
        tf = validate_timeframe(timeframe)
        valid_limit = validate_limit(limit, MAX_OHLCV_LIMIT, DEFAULT_OHLCV_LIMIT)
        logger.debug(
            "get_data flow: request validated | "
            f"symbol={symbol}, kind=ohlcv, timeframe={tf}, limit={valid_limit}",
            extra={"request_id": request_id},
        )
        frame = execute_gateway_dataframe_request(
            source,
            symbol,
            tf,
            t_start,
            t_end,
            stale_data_behavior,
            workflow_context,
            fallback_sources,
            request_id,
        )
        result = frame.iloc[:valid_limit]
        logger.debug(
            "get_data flow: return DataFrame | "
            f"rows={len(result)}, columns={list(result.columns)}",
            extra={"request_id": request_id},
        )
        return result

    if kind == "ticks":
        valid_limit = validate_limit(limit, MAX_TICK_LIMIT, DEFAULT_TICK_LIMIT)
        logger.debug(
            "get_data flow: request validated | "
            f"symbol={symbol}, kind=ticks, limit={valid_limit}",
            extra={"request_id": request_id},
        )
        result = execute_gateway_tick_dataframe_request(
            source,
            symbol,
            t_start,
            t_end,
            "ticks",
            valid_limit,
            stale_data_behavior,
            workflow_context,
            fallback_sources,
            request_id,
        )
        logger.debug(
            "get_data flow: return DataFrame | "
            f"kind=ticks, rows={len(result)}, columns={list(result.columns)}",
            extra={"request_id": request_id},
        )
        return result

    if kind == "spreads":
        valid_limit = validate_limit(limit, MAX_SPREAD_LIMIT, DEFAULT_SPREAD_LIMIT)
        logger.debug(
            "get_data flow: request validated | "
            f"symbol={symbol}, kind=spreads, limit={valid_limit}",
            extra={"request_id": request_id},
        )
        result = execute_gateway_tick_dataframe_request(
            source,
            symbol,
            t_start,
            t_end,
            "spreads",
            valid_limit,
            stale_data_behavior,
            workflow_context,
            fallback_sources,
            request_id,
        )
        logger.debug(
            "get_data flow: return DataFrame | "
            f"kind=spreads, rows={len(result)}, columns={list(result.columns)}",
            extra={"request_id": request_id},
        )
        return result

    if kind == "volume":
        if not timeframe:
            raise ValidationError("timeframe is required for volume data.")
        tf = validate_timeframe(timeframe)
        valid_limit = validate_limit(limit, MAX_OHLCV_LIMIT, DEFAULT_OHLCV_LIMIT)
        logger.debug(
            "get_data flow: request validated | "
            f"symbol={symbol}, kind=volume, timeframe={tf}, limit={valid_limit}",
            extra={"request_id": request_id},
        )
        logger.debug(
            "get_data flow: delegate volume request to OHLCV flow | "
            f"symbol={symbol}, timeframe={tf}",
            extra={"request_id": request_id},
        )
        bars = get_data(
            symbol=symbol,
            start_time=start_time,
            end_time=end_time,
            data_kind="ohlcv",
            timeframe=tf,
            source=source,
            limit=valid_limit,
            stale_data_behavior=stale_data_behavior,
            workflow_context=workflow_context,
            fallback_sources=fallback_sources,
            request_id=request_id,
        )
        volume_df = pd.DataFrame(index=bars.index)
        volume_df["volume"] = (
            bars["volume"] if "volume" in bars.columns else float("nan")
        )
        logger.debug(
            "get_data flow: return DataFrame | "
            f"kind=volume, rows={len(volume_df)}, columns={list(volume_df.columns)}",
            extra={"request_id": request_id},
        )
        return volume_df

    return pd.DataFrame(index=_empty_datetime_index())


def get_symbol_metadata(
    symbol: str,
    source: str = "csv",
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Description.
        Retrieve normalized symbol and asset metadata.
    
    Args:
        symbol: str.
        source: str.
        request_id: str | None.
    
    Returns:
        dict[str, Any].
    """
    logger.info(
        f"Retrieving symbol metadata: symbol={symbol}, source={source}",
        extra={"request_id": request_id},
    )
    adapter = get_source_adapter(source)
    raw_meta = adapter.get_symbol_metadata(symbol, request_id=request_id)

    meta_obj = SymbolMetadata(
        symbol=symbol,
        asset_class=raw_meta.get("asset_class", "forex"),
        base_currency=raw_meta.get("base_currency", "EUR"),
        quote_currency=raw_meta.get("quote_currency", "USD"),
        contract_size=raw_meta.get("contract_size", 100000.0),
        tick_size=raw_meta.get("tick_size", 0.00001),
        tick_value=raw_meta.get("tick_value", 1.0),
        point=raw_meta.get("point", 0.00001),
        digits=raw_meta.get("digits", 5),
        lot_min=raw_meta.get("lot_min", 0.01),
        lot_max=raw_meta.get("lot_max", 100.0),
        lot_step=raw_meta.get("lot_step", 0.01),
        margin_currency=raw_meta.get("margin_currency", "EUR"),
        profit_currency=raw_meta.get("profit_currency", "USD"),
        trading_hours=raw_meta.get("trading_hours", {}),
        source_metadata=raw_meta,
    )

    return cast(dict[str, Any], meta_obj.model_dump())


def list_symbols(
    source: str = "csv",
    *,
    request_id: str | None = None,
) -> list[str]:
    """Description.
        List symbols discovered from the source.
    
    Args:
        source: str.
        request_id: str | None.
    
    Returns:
        list[str].
    """
    logger.debug(f"list_symbols API called for source={source}")
    adapter = get_source_adapter(source)
    return adapter.list_symbols(request_id=request_id)


def get_data_availability(
    symbol: str,
    timeframe: str,
    source: str = "csv",
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Description.
        Inspect committed ranges, gaps, and record counts.
    
    Args:
        symbol: str.
        timeframe: str.
        source: str.
        request_id: str | None.
    
    Returns:
        dict[str, Any].
    """
    logger.info(
        f"Checking data availability: symbol={symbol}, source={source}",
        extra={"request_id": request_id},
    )

    count = 0
    start_str = None
    end_str = None
    try:
        with db_helper.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT key, start_time, end_time, records_json FROM data_cache
                WHERE source = ? AND symbol = ? AND timeframe = ?;
                """,
                (source, symbol, timeframe),
            )
            rows = cursor.fetchall()
            for row in rows:
                start_str = row["start_time"]
                end_str = row["end_time"]
                records = json.loads(row["records_json"])
                count += len(records)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Failed to query data availability from database cache: {e}")

    availability = DataAvailability(
        symbol=symbol,
        timeframe=timeframe,
        source=source,
        start_time=start_str,
        end_time=end_str,
        gap_count=0,
        gap_windows=[],
        is_ready=True,
        record_count=count,
        metadata={"cache_queried": True},
    )

    return cast(dict[str, Any], availability.model_dump())


__all__ = [
    "BrokerAdapter",
    "CSVAdapter",
    "ParquetAdapter",
    "SourceAdapterProtocol",
    "SyntheticAdapter",
    "TokenBucketLimiter",
    "check_circuit_breaker_barrier",
    "check_rate_limit",
    "execute_gateway_request",
    "get_circuit_breaker",
    "get_data",
    "get_data_availability",
    "get_source_adapter",
    "get_symbol_metadata",
    "list_symbols",
    "normalize_file_records",
    "update_circuit_breaker",
]
