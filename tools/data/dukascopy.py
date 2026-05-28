"""Dukascopy market-data tools for HaruQuantAI.

Purpose:
    Provide safe, agent-callable tools for resolving Dukascopy instruments,
    listing supported instruments, and loading historical OHLCV bars from the
    Dukascopy web data endpoint.

Exported AI Tools:
    - dukascopy_data_load: Fetch historical OHLCV bars from Dukascopy.
    - dukascopy_data_list_symbols: List supported Dukascopy symbols.
    - dukascopy_data_resolve_instrument: Resolve a friendly symbol to the
      Dukascopy API instrument string.

Compatibility Aliases:
    - load_dukascopy: Backward-compatible alias for dukascopy_data_load.
    - get_instrument: Backward-compatible alias for
      dukascopy_data_resolve_instrument.
    - fetch: Backward-compatible alias for dukascopy_data_load.

Internal Helpers:
    - _fetch_jsonp: Fetch and decode a Dukascopy JSONP response.
    - _fetch_rows: Fetch rows from the Dukascopy endpoint with bounded paging.
    - _rows_to_frame: Convert raw rows to a normalized DataFrame.
    - _normalize_dukascopy_bars: Normalize raw OHLCV bars and attach freshness
      metadata.
    - validation and standard response helpers.

Classes:
    - DukascopyBarsSnapshot: Normalized OHLCV bars with freshness metadata.

Safety:
    These tools are read-only, require network access, do not write files, do
    not modify databases, and never place trades.
"""

from __future__ import annotations

import json
import random
import string
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional, cast
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pandas as pd
import requests

from tools.data.dukascopy_instruments import INSTRUMENT_MAP
from tools.utils import logger
from tools.utils.common import bars_to_records, get_cached_dataframe
from tools.utils.normalization import evaluate_freshness, format_timestamp_z, to_utc
from tools.utils.validators import prepare_ohlcv_data

UTC = timezone.utc

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "data"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = True

DEFAULT_REQUEST_TIMEOUT_SECONDS = 5
DEFAULT_MAX_RETRIES = 1
DEFAULT_MAX_PAGES = 100
DUKASCOPY_MAX_LIMIT = 30_000
DEFAULT_MAX_AGE_SECONDS = 86_400

TIME_UNIT_MONTH = "MONTH"
TIME_UNIT_WEEK = "WEEK"
TIME_UNIT_DAY = "DAY"
TIME_UNIT_HOUR = "HOUR"
TIME_UNIT_MIN = "MIN"
TIME_UNIT_SEC = "SEC"
TIME_UNIT_TICK = "TICK"

INTERVAL_MONTH_1 = f"1{TIME_UNIT_MONTH}"
INTERVAL_WEEK_1 = f"1{TIME_UNIT_WEEK}"
INTERVAL_DAY_1 = f"1{TIME_UNIT_DAY}"
INTERVAL_HOUR_4 = f"4{TIME_UNIT_HOUR}"
INTERVAL_HOUR_1 = f"1{TIME_UNIT_HOUR}"
INTERVAL_MIN_30 = f"30{TIME_UNIT_MIN}"
INTERVAL_MIN_15 = f"15{TIME_UNIT_MIN}"
INTERVAL_MIN_10 = f"10{TIME_UNIT_MIN}"
INTERVAL_MIN_5 = f"5{TIME_UNIT_MIN}"
INTERVAL_MIN_1 = f"1{TIME_UNIT_MIN}"
INTERVAL_SEC_30 = f"30{TIME_UNIT_SEC}"
INTERVAL_SEC_10 = f"10{TIME_UNIT_SEC}"
INTERVAL_SEC_1 = f"1{TIME_UNIT_SEC}"
INTERVAL_TICK = TIME_UNIT_TICK

OFFER_SIDE_BID = "B"
OFFER_SIDE_ASK = "A"
SUPPORTED_OFFER_SIDES = frozenset({OFFER_SIDE_BID, OFFER_SIDE_ASK})

TIMEFRAME_TO_INTERVAL = {
    "MN1": INTERVAL_MONTH_1,
    "W1": INTERVAL_WEEK_1,
    "D1": INTERVAL_DAY_1,
    "H4": INTERVAL_HOUR_4,
    "H1": INTERVAL_HOUR_1,
    "M30": INTERVAL_MIN_30,
    "M15": INTERVAL_MIN_15,
    "M10": INTERVAL_MIN_10,
    "M5": INTERVAL_MIN_5,
    "M1": INTERVAL_MIN_1,
    "S30": INTERVAL_SEC_30,
    "S10": INTERVAL_SEC_10,
    "S1": INTERVAL_SEC_1,
}
SUPPORTED_TIMEFRAMES = frozenset(TIMEFRAME_TO_INTERVAL)

INTERVAL_UNITS = {
    INTERVAL_MONTH_1: TIME_UNIT_MONTH,
    INTERVAL_WEEK_1: TIME_UNIT_WEEK,
    INTERVAL_DAY_1: TIME_UNIT_DAY,
    INTERVAL_HOUR_4: TIME_UNIT_HOUR,
    INTERVAL_HOUR_1: TIME_UNIT_HOUR,
    INTERVAL_MIN_30: TIME_UNIT_MIN,
    INTERVAL_MIN_15: TIME_UNIT_MIN,
    INTERVAL_MIN_10: TIME_UNIT_MIN,
    INTERVAL_MIN_5: TIME_UNIT_MIN,
    INTERVAL_MIN_1: TIME_UNIT_MIN,
    INTERVAL_SEC_30: TIME_UNIT_SEC,
    INTERVAL_SEC_10: TIME_UNIT_SEC,
    INTERVAL_SEC_1: TIME_UNIT_SEC,
    INTERVAL_TICK: TIME_UNIT_TICK,
}

INTERVAL_MINUTES = {
    INTERVAL_MONTH_1: 43_200,
    INTERVAL_WEEK_1: 10_080,
    INTERVAL_DAY_1: 1_440,
    INTERVAL_HOUR_4: 240,
    INTERVAL_HOUR_1: 60,
    INTERVAL_MIN_30: 30,
    INTERVAL_MIN_15: 15,
    INTERVAL_MIN_10: 10,
    INTERVAL_MIN_5: 5,
    INTERVAL_MIN_1: 1,
    INTERVAL_SEC_30: 1,
    INTERVAL_SEC_10: 1,
    INTERVAL_SEC_1: 1,
}

BASE_URL = "https://freeserv.dukascopy.com/2.0/index.php"
DEFAULT_HEADERS = {
    "User-Agent": "HaruQuantAI/1.0 DukascopyDataTool",
    "Host": "freeserv.dukascopy.com",
    "Referer": "https://freeserv.dukascopy.com/2.0/?path=chart/index",
}


@dataclass(frozen=True)
class DukascopyBarsSnapshot:
    """Normalized Dukascopy bars with freshness metadata.

    Args:
        symbol: User-facing symbol requested by the caller.
        timeframe: Normalized HaruQuant timeframe.
        bars: Normalized OHLCV bars indexed by timestamp.
        observed_at: UTC timestamp when the bars were observed/fetched.
        max_age_seconds: Freshness threshold for this snapshot.
        source: Data source name. Defaults to ``dukascopy``.
    """

    symbol: str
    timeframe: str
    bars: pd.DataFrame
    observed_at: datetime
    max_age_seconds: int
    source: str = "dukascopy"

    @property
    def row_count(self) -> int:
        """Return the number of rows in the normalized bars."""
        return int(len(self.bars))

    @property
    def start_at(self) -> datetime | None:
        """Return the first bar timestamp in UTC, or None when empty."""
        if self.bars.empty:
            return None
        return to_utc(cast(datetime, self.bars.index[0].to_pydatetime()))

    @property
    def end_at(self) -> datetime | None:
        """Return the last bar timestamp in UTC, or None when empty."""
        if self.bars.empty:
            return None
        return to_utc(cast(datetime, self.bars.index[-1].to_pydatetime()))

    def freshness(self, *, clock: Any | None = None) -> Any:
        """Return freshness evaluation for the snapshot."""
        return evaluate_freshness(
            self.observed_at,
            max_age_seconds=self.max_age_seconds,
            clock=clock,
        )

    def to_payload(self, *, include_bars: bool = False) -> dict[str, Any]:
        """Return a JSON-safe payload for agent/workflow responses."""
        payload: dict[str, Any] = {
            "source": self.source,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "row_count": self.row_count,
            "observed_at": format_timestamp_z(self.observed_at),
            "max_age_seconds": self.max_age_seconds,
            "start_at": format_timestamp_z(self.start_at),
            "end_at": format_timestamp_z(self.end_at),
        }
        if include_bars:
            payload["bars"] = bars_to_records(self.bars)
        return payload


def _execution_ms(started_at: float) -> float:
    """Return elapsed milliseconds rounded for stable tool metadata."""
    return round((time.perf_counter() - started_at) * 1000, 3)


def _metadata(
    tool_name: str, request_id: Optional[str], started_at: float
) -> dict[str, Any]:
    """Build standard HaruQuantAI tool metadata."""
    return {
        "tool_name": tool_name,
        "tool_version": TOOL_VERSION,
        "tool_category": TOOL_CATEGORY,
        "tool_risk_level": TOOL_RISK_LEVEL,
        "request_id": request_id,
        "execution_ms": _execution_ms(started_at),
        "read_only": READ_ONLY,
        "writes_file": WRITES_FILE,
        "modifies_database": MODIFIES_DATABASE,
        "places_trade": PLACES_TRADE,
        "requires_network": REQUIRES_NETWORK,
    }


def _tool_success(
    *,
    tool_name: str,
    request_id: Optional[str],
    started_at: float,
    message: str,
    data: Any,
) -> Dict[str, Any]:
    """Return a standard success response for an official tool."""
    return {
        "status": "success",
        "message": message,
        "data": data,
        "error": None,
        "metadata": _metadata(tool_name, request_id, started_at),
    }


def _tool_error(
    *,
    tool_name: str,
    request_id: Optional[str],
    started_at: float,
    code: str,
    message: str,
    details: str,
) -> Dict[str, Any]:
    """Return a standard error response for an official tool."""
    return {
        "status": "error",
        "message": message,
        "data": None,
        "error": {
            "code": code,
            "details": details,
        },
        "metadata": _metadata(tool_name, request_id, started_at),
    }


def _validate_symbol(symbol: Any) -> Optional[str]:
    """Return an error message if symbol is invalid."""
    if not isinstance(symbol, str) or not symbol.strip():
        return "symbol must be a non-empty string."
    return None


def _validate_pattern(pattern: Any) -> Optional[str]:
    """Return an error message if pattern is invalid."""
    if pattern is not None and not isinstance(pattern, str):
        return "pattern must be a string or None."
    return None


def _validate_timeframe(timeframe: Any) -> Optional[str]:
    """Return an error message if timeframe is unsupported."""
    if not isinstance(timeframe, str) or not timeframe.strip():
        return "timeframe must be a non-empty string."
    if timeframe.upper() not in SUPPORTED_TIMEFRAMES:
        return f"timeframe must be one of: {', '.join(sorted(SUPPORTED_TIMEFRAMES))}."
    return None


def _validate_optional_date(value: Any, name: str) -> Optional[str]:
    """Return an error message if a date value is invalid."""
    if value is None:
        return None
    if not isinstance(value, str):
        return f"{name} must be a YYYY-MM-DD string or None."
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return f"{name} must use YYYY-MM-DD format."
    return None


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    """Parse a YYYY-MM-DD date string as a UTC datetime."""
    if value is None:
        return None
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC)


def _validate_date_range(start_date: Any, end_date: Any) -> Optional[str]:
    """Return an error message if start/end dates are invalid."""
    start_error = _validate_optional_date(start_date, "start_date")
    if start_error:
        return start_error
    end_error = _validate_optional_date(end_date, "end_date")
    if end_error:
        return end_error
    parsed_start = _parse_date(start_date)
    parsed_end = _parse_date(end_date)
    if parsed_start and parsed_end and parsed_start > parsed_end:
        return "start_date must be earlier than or equal to end_date."
    return None


def _validate_optional_positive_int(value: Any, name: str) -> Optional[str]:
    """Return an error message when an optional positive integer is invalid."""
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        return f"{name} must be a positive integer when provided."
    return None


def _validate_non_negative_int(value: Any, name: str) -> Optional[str]:
    """Return an error message when a non-negative integer is invalid."""
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        return f"{name} must be a non-negative integer."
    return None


def _validate_positive_number(value: Any, name: str) -> Optional[str]:
    """Return an error message when a positive number is invalid."""
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        return f"{name} must be a positive number."
    return None


def _validate_bool(value: Any, name: str) -> Optional[str]:
    """Return an error message when a boolean value is invalid."""
    if not isinstance(value, bool):
        return f"{name} must be a boolean."
    return None


def _validate_offer_side(value: Any) -> Optional[str]:
    """Return an error message when offer_side is unsupported."""
    if not isinstance(value, str) or value.upper() not in SUPPORTED_OFFER_SIDES:
        return "offer_side must be 'B' for bid or 'A' for ask."
    return None


def _validate_timezone(timezone_name: Any) -> Optional[str]:
    """Return an error message when timezone_name is invalid."""
    if not isinstance(timezone_name, str) or not timezone_name.strip():
        return "timezone_name must be a non-empty IANA timezone string."
    try:
        ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return f"timezone_name is not recognized: {timezone_name}."
    return None


def _validate_load_inputs(
    *,
    symbol: Any,
    timeframe: Any,
    start_date: Any,
    end_date: Any,
    count: Any,
    cache: Any,
    timeout: Any,
    max_retries: Any,
    offer_side: Any,
    timezone_name: Any,
) -> Optional[str]:
    """Validate inputs for dukascopy_data_load."""
    count_error = _validate_optional_positive_int(count, "count")
    if count_error:
        return count_error
    if isinstance(count, int) and count > DUKASCOPY_MAX_LIMIT:
        return f"count cannot exceed {DUKASCOPY_MAX_LIMIT}."
    return (
        _validate_symbol(symbol)
        or _validate_timeframe(timeframe)
        or _validate_date_range(start_date, end_date)
        or _validate_bool(cache, "cache")
        or _validate_positive_number(timeout, "timeout")
        or _validate_non_negative_int(max_retries, "max_retries")
        or _validate_offer_side(offer_side)
        or _validate_timezone(timezone_name)
    )


def _normalize_key(symbol: str) -> str:
    """Normalize a symbol key for INSTRUMENT_MAP lookup."""
    return (
        symbol.upper()
        .replace(" ", "")
        .replace("-", "")
        .replace(".", "")
        .replace("/", "")
    )


def _resolve_dukascopy_instrument(symbol: str) -> str:
    """Resolve a friendly symbol to a Dukascopy API instrument string."""
    clean_symbol = _normalize_key(symbol)
    if clean_symbol in INSTRUMENT_MAP:
        return INSTRUMENT_MAP[clean_symbol]
    if "/" in symbol:
        return symbol.upper()
    if len(clean_symbol) == 6 and clean_symbol.isalpha():
        return f"{clean_symbol[:3]}/{clean_symbol[3:]}"
    return symbol.upper()


def _interval_for_timeframe(timeframe: str) -> str:
    """Return the Dukascopy interval for a HaruQuant timeframe."""
    return TIMEFRAME_TO_INTERVAL[timeframe.upper()]


def _columns_for_interval(interval: str) -> list[str]:
    """Return raw row columns for a Dukascopy interval."""
    time_unit = INTERVAL_UNITS[interval]
    if time_unit == TIME_UNIT_TICK:
        return ["timestamp", "bidprice", "askprice", "bidvolume", "askvolume"]
    return ["timestamp", "open", "high", "low", "close", "volume"]


def _build_date_window(
    *,
    interval: str,
    start_date: Optional[str],
    end_date: Optional[str],
    count: Optional[int],
) -> tuple[datetime, datetime, int]:
    """Build a bounded fetch window and limit from dates/count."""
    if count is not None:
        end = datetime.now(UTC)
        interval_minutes = INTERVAL_MINUTES[interval]
        limit = min(max(count + 5, count), DUKASCOPY_MAX_LIMIT)
        minutes_needed = max(limit * interval_minutes, interval_minutes)
        days_needed = max(2, int(minutes_needed / 1_440) + 5)
        start = end - timedelta(days=days_needed)
        return start, end, limit

    start = _parse_date(start_date) or (datetime.now(UTC) - timedelta(days=365))
    end = _parse_date(end_date) or datetime.now(UTC)
    return start, end, DUKASCOPY_MAX_LIMIT


def _fetch_jsonp(
    *,
    instrument: str,
    interval: str,
    offer_side: str,
    last_update: int,
    limit: Optional[int],
    timeout: float,
    request_get: Callable[..., requests.Response] | None = None,
) -> list[list[Any]]:
    """Fetch and decode one Dukascopy JSONP batch."""
    characters = string.ascii_letters + string.digits
    jsonp = f"_callbacks____{''.join(random.choices(characters, k=9))}"
    query_params = {
        "path": "chart/json3",
        "splits": "true",
        "stocks": "true",
        "time_direction": "N",
        "jsonp": jsonp,
        "last_update": str(int(last_update)),
        "offer_side": offer_side,
        "instrument": instrument,
        "interval": interval,
    }
    if limit is not None:
        query_params["limit"] = str(int(limit))

    request_get = request_get or requests.get
    response = request_get(
        BASE_URL,
        headers=DEFAULT_HEADERS,
        params=query_params,
        timeout=timeout,
    )
    response.raise_for_status()
    text = str(response.text)
    prefix = f"{jsonp}("
    suffix = ");"
    if not text.startswith(prefix) or not text.endswith(suffix):
        raise ValueError("Dukascopy response was not valid JSONP.")
    parsed = json.loads(text.removeprefix(prefix).removesuffix(suffix))
    if not isinstance(parsed, list):
        raise ValueError("Dukascopy response JSON must be a list of rows.")
    return parsed


def _fetch_rows(
    *,
    instrument: str,
    interval: str,
    offer_side: str,
    start: datetime,
    end: datetime,
    limit: int,
    timeout: float,
    max_retries: int,
    max_pages: int = DEFAULT_MAX_PAGES,
    request_get: Callable[..., requests.Response] | None = None,
) -> list[list[Any]]:
    """Fetch rows from Dukascopy with bounded retries and paging."""
    rows: list[list[Any]] = []
    cursor = int(start.timestamp() * 1000)
    end_timestamp = int(end.timestamp() * 1000)
    first_page = True

    for _page in range(max_pages):
        remaining = max(0, limit - len(rows))
        if remaining <= 0:
            break

        batch: list[list[Any]] = []
        for attempt in range(max_retries + 1):
            try:
                batch = _fetch_jsonp(
                    instrument=instrument,
                    interval=interval,
                    offer_side=offer_side,
                    last_update=cursor,
                    limit=remaining,
                    timeout=timeout,
                    request_get=request_get,
                )
                break
            except requests.Timeout:
                if attempt >= max_retries:
                    raise
                time.sleep(min(1.0, 0.1 * (attempt + 1)))
            except requests.RequestException:
                if attempt >= max_retries:
                    raise
                time.sleep(min(1.0, 0.1 * (attempt + 1)))

        if not batch:
            break
        if not first_page and batch and batch[0][0] == cursor:
            batch = batch[1:]

        added = 0
        for row in batch:
            if not isinstance(row, list) or not row:
                continue
            timestamp_ms = int(row[0])
            if timestamp_ms > end_timestamp:
                return rows
            rows.append(row)
            cursor = timestamp_ms
            added += 1
            if len(rows) >= limit:
                break

        if added == 0:
            break
        first_page = False

    return rows


def _rows_to_frame(rows: list[list[Any]], interval: str) -> pd.DataFrame:
    """Convert raw Dukascopy rows to a DataFrame."""
    columns = _columns_for_interval(interval)
    if not rows:
        return pd.DataFrame(columns=columns).set_index(
            pd.DatetimeIndex([], name="timestamp")
        )
    frame = pd.DataFrame(data=rows, columns=columns)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
    frame = frame.set_index("timestamp").sort_index()
    return frame


def _apply_timezone(frame: pd.DataFrame, timezone_name: str) -> pd.DataFrame:
    """Convert timestamps to timezone_name while preserving UTC by default."""
    if frame.empty:
        return frame
    result = frame.copy()
    index = cast(pd.DatetimeIndex, result.index)
    if index.tz is None:
        index = index.tz_localize("UTC")
    if timezone_name.upper() == "UTC":
        result.index = index.tz_convert("UTC")
    else:
        result.index = index.tz_convert(timezone_name)
    return result


def _normalize_dukascopy_bars(
    bars: pd.DataFrame,
    *,
    symbol: str,
    timeframe: str,
    observed_at: datetime | None = None,
    max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS,
) -> DukascopyBarsSnapshot:
    """Normalize raw Dukascopy OHLCV bars to HaruQuant market-data shape."""
    if max_age_seconds < 0:
        raise ValueError("max_age_seconds must be non-negative.")
    if not isinstance(bars, pd.DataFrame):
        raise TypeError("bars must be a pandas DataFrame.")
    if bars.empty:
        raise ValueError("Dukascopy returned no bars.")
    normalized = prepare_ohlcv_data(bars)
    if not isinstance(normalized, pd.DataFrame):
        raise TypeError("prepare_ohlcv_data must return a pandas DataFrame.")
    required = {"open", "high", "low", "close"}
    missing = required.difference(
        {str(column).lower() for column in normalized.columns}
    )
    if missing:
        raise ValueError(
            f"Normalized bars are missing required columns: {sorted(missing)}."
        )

    observed = observed_at or datetime.now(UTC)
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=UTC)

    return DukascopyBarsSnapshot(
        symbol=symbol.upper(),
        timeframe=timeframe.upper(),
        bars=normalized,
        observed_at=observed.astimezone(UTC),
        max_age_seconds=int(max_age_seconds),
    )


def _fetch_historical_frame(
    *,
    symbol: str,
    timeframe: str,
    start_date: Optional[str],
    end_date: Optional[str],
    count: Optional[int],
    cache: bool,
    timezone_name: str,
    offer_side: str,
    timeout: float,
    max_retries: int,
    request_get: Callable[..., requests.Response] | None = None,
) -> pd.DataFrame:
    """Fetch and normalize a historical Dukascopy DataFrame."""
    interval = _interval_for_timeframe(timeframe)
    instrument = _resolve_dukascopy_instrument(symbol)
    start, end, limit = _build_date_window(
        interval=interval,
        start_date=start_date,
        end_date=end_date,
        count=count,
    )

    def _load() -> pd.DataFrame:
        rows = _fetch_rows(
            instrument=instrument,
            interval=interval,
            offer_side=offer_side.upper(),
            start=start,
            end=end,
            limit=limit,
            timeout=timeout,
            max_retries=max_retries,
            request_get=request_get,
        )
        frame = _rows_to_frame(rows, interval)
        if count is not None and not frame.empty:
            frame = frame.tail(count)
        return _apply_timezone(frame, timezone_name)

    if not cache:
        return _load()

    cache_key = (
        f"dukascopy:{instrument}:{timeframe.upper()}:{start.isoformat()}:"
        f"{end.isoformat()}:{count}:{timezone_name}:{offer_side.upper()}"
    )
    cached = get_cached_dataframe(cache_key, _load)
    if isinstance(cached, dict) and cached.get("status") == "success":
        cached = cached.get("data")
    if not isinstance(cached, pd.DataFrame):
        raise TypeError("Cached Dukascopy data must be a pandas DataFrame.")
    return cached.copy()


def dukascopy_data_resolve_instrument(
    symbol: str,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Resolve a friendly symbol to a Dukascopy API instrument string.

    Use this tool when an agent needs to confirm how a user-facing symbol such
    as ``EURUSD`` or ``XAUUSD`` maps to the Dukascopy data API.
    """
    tool_name = "dukascopy_data_resolve_instrument"
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s | symbol=%s", tool_name, request_id, symbol)
    validation_error = _validate_symbol(symbol)
    if validation_error:
        logger.warning(
            "%s validation failed | request_id=%s | reason=%s",
            tool_name,
            request_id,
            validation_error,
        )
        return _tool_error(
            tool_name=tool_name,
            request_id=request_id,
            started_at=started_at,
            code="INVALID_INPUT",
            message="Invalid input.",
            details=validation_error,
        )
    instrument = _resolve_dukascopy_instrument(symbol.strip())
    return _tool_success(
        tool_name=tool_name,
        request_id=request_id,
        started_at=started_at,
        message="Dukascopy instrument resolved successfully.",
        data={"symbol": symbol.strip().upper(), "instrument": instrument},
    )


def dukascopy_data_list_symbols(
    pattern: Optional[str] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """List supported Dukascopy symbols known to HaruQuantAI.

    Use this tool when an agent needs to discover available Dukascopy symbols or
    verify whether a symbol can be resolved before fetching data.
    """
    tool_name = "dukascopy_data_list_symbols"
    started_at = time.perf_counter()
    logger.info(
        "%s called | request_id=%s | pattern=%s", tool_name, request_id, pattern
    )
    validation_error = _validate_pattern(pattern)
    if validation_error:
        logger.warning(
            "%s validation failed | request_id=%s | reason=%s",
            tool_name,
            request_id,
            validation_error,
        )
        return _tool_error(
            tool_name=tool_name,
            request_id=request_id,
            started_at=started_at,
            code="INVALID_INPUT",
            message="Invalid input.",
            details=validation_error,
        )

    symbols = sorted(set(INSTRUMENT_MAP.keys()) | set(INSTRUMENT_MAP.values()))
    if pattern:
        import fnmatch

        normalized_pattern = pattern.upper()
        symbols = [
            symbol
            for symbol in symbols
            if fnmatch.fnmatch(symbol.upper(), normalized_pattern)
        ]

    return _tool_success(
        tool_name=tool_name,
        request_id=request_id,
        started_at=started_at,
        message="Dukascopy symbols listed successfully.",
        data={"symbols": symbols, "count": len(symbols)},
    )


def dukascopy_data_load(
    symbol: str,
    timeframe: str = "M1",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    count: Optional[int] = None,
    cache: bool = True,
    timezone_name: str = "UTC",
    offer_side: str = OFFER_SIDE_BID,
    timeout: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
    max_retries: int = DEFAULT_MAX_RETRIES,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetch historical OHLCV bars from Dukascopy.

    Use this tool when an agent needs read-only historical market data from
    Dukascopy for analysis, validation, or backtesting preparation.

    Args:
        symbol: Friendly symbol such as ``EURUSD`` or ``XAUUSD``.
        timeframe: Supported timeframe such as ``M1``, ``M5``, ``H1``, or ``D1``.
        start_date: Optional start date in ``YYYY-MM-DD`` format.
        end_date: Optional end date in ``YYYY-MM-DD`` format.
        count: Optional number of most recent bars to return.
        cache: Whether to use the process-local DataFrame cache.
        timezone_name: IANA timezone for returned index. Defaults to UTC.
        offer_side: Dukascopy offer side, ``B`` for bid or ``A`` for ask.
        timeout: HTTP timeout in seconds.
        max_retries: Number of retries for timeout/network failures.
        request_id: Optional workflow trace ID.

    Returns:
        Dict[str, Any]: Standard HaruQuantAI tool response containing metadata,
        normalized bar records, and source provenance.
    """
    tool_name = "dukascopy_data_load"
    started_at = time.perf_counter()
    logger.info(
        "%s called | request_id=%s | symbol=%s | timeframe=%s | count=%s",
        tool_name,
        request_id,
        symbol,
        timeframe,
        count,
    )

    validation_error = _validate_load_inputs(
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        count=count,
        cache=cache,
        timeout=timeout,
        max_retries=max_retries,
        offer_side=offer_side,
        timezone_name=timezone_name,
    )
    if validation_error:
        logger.warning(
            "%s validation failed | request_id=%s | reason=%s",
            tool_name,
            request_id,
            validation_error,
        )
        return _tool_error(
            tool_name=tool_name,
            request_id=request_id,
            started_at=started_at,
            code="INVALID_INPUT",
            message="Invalid input.",
            details=validation_error,
        )

    try:
        normalized_symbol = symbol.strip().upper()
        normalized_timeframe = timeframe.strip().upper()
        frame = _fetch_historical_frame(
            symbol=normalized_symbol,
            timeframe=normalized_timeframe,
            start_date=start_date,
            end_date=end_date,
            count=count,
            cache=cache,
            timezone_name=timezone_name,
            offer_side=offer_side.upper(),
            timeout=float(timeout),
            max_retries=max_retries,
        )
        if frame.empty:
            logger.warning(
                "%s empty result | request_id=%s | symbol=%s",
                tool_name,
                request_id,
                normalized_symbol,
            )
            return _tool_error(
                tool_name=tool_name,
                request_id=request_id,
                started_at=started_at,
                code="DATA_NOT_FOUND",
                message="No Dukascopy data found.",
                details=(
                    f"No bars were returned for {normalized_symbol} "
                    f"{normalized_timeframe}."
                ),
            )

        snapshot = _normalize_dukascopy_bars(
            frame,
            symbol=normalized_symbol,
            timeframe=normalized_timeframe,
        )
        payload = snapshot.to_payload(include_bars=True)
        payload.update(
            {
                "instrument": _resolve_dukascopy_instrument(normalized_symbol),
                "timezone": timezone_name,
                "offer_side": offer_side.upper(),
                "fallback_used": False,
            }
        )
        logger.info(
            "%s completed successfully | request_id=%s | rows=%s",
            tool_name,
            request_id,
            snapshot.row_count,
        )
        return _tool_success(
            tool_name=tool_name,
            request_id=request_id,
            started_at=started_at,
            message="Dukascopy data loaded successfully.",
            data=payload,
        )
    except requests.Timeout as error:
        logger.exception("%s timeout | request_id=%s", tool_name, request_id)
        return _tool_error(
            tool_name=tool_name,
            request_id=request_id,
            started_at=started_at,
            code="TIMEOUT",
            message="Dukascopy request timed out.",
            details=str(error),
        )
    except requests.RequestException as error:
        logger.exception("%s network failure | request_id=%s", tool_name, request_id)
        return _tool_error(
            tool_name=tool_name,
            request_id=request_id,
            started_at=started_at,
            code="NETWORK_ERROR",
            message="Dukascopy network request failed.",
            details=str(error),
        )
    except ValueError as error:
        logger.warning(
            "%s data validation failed | request_id=%s | error=%s",
            tool_name,
            request_id,
            error,
        )
        code = (
            "DATA_NOT_FOUND"
            if "no bars" in str(error).lower() or "no data" in str(error).lower()
            else "VALIDATION_FAILED"
        )
        return _tool_error(
            tool_name=tool_name,
            request_id=request_id,
            started_at=started_at,
            code=code,
            message="Dukascopy data validation failed.",
            details=str(error),
        )
    except Exception as error:
        logger.exception("%s failed | request_id=%s", tool_name, request_id)
        return _tool_error(
            tool_name=tool_name,
            request_id=request_id,
            started_at=started_at,
            code="TOOL_EXECUTION_FAILED",
            message="Tool execution failed.",
            details=str(error),
        )


def load_dukascopy(
    symbol: str,
    timeframe: str = "M1",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    count: Optional[int] = None,
    cache: bool = True,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Backward-compatible alias for dukascopy_data_load."""
    return dukascopy_data_load(
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        count=count,
        cache=cache,
        request_id=request_id,
    )


def get_instrument(symbol: str, request_id: Optional[str] = None) -> Dict[str, Any]:
    """Backward-compatible alias for dukascopy_data_resolve_instrument."""
    return dukascopy_data_resolve_instrument(symbol=symbol, request_id=request_id)


def fetch(
    symbol: str,
    timeframe: str = "M1",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    count: Optional[int] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Backward-compatible historical fetch alias for dukascopy_data_load."""
    return dukascopy_data_load(
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        count=count,
        request_id=request_id,
    )


def live_fetch(*_: Any, request_id: Optional[str] = None, **__: Any) -> Dict[str, Any]:
    """Return a structured error because streaming is not an official AI Tool.

    Streaming should be implemented in a dedicated streaming module with a
    lifecycle-aware runtime, not exposed through this historical data tool file.
    """
    tool_name = "live_fetch"
    started_at = time.perf_counter()
    return _tool_error(
        tool_name=tool_name,
        request_id=request_id,
        started_at=started_at,
        code="SERVICE_UNAVAILABLE",
        message="Dukascopy streaming is not exposed by this tool module.",
        details=(
            "Use dukascopy_data_load for historical data or implement streaming "
            "in a dedicated module."
        ),
    )


def normalize_dukascopy_bars(
    bars: pd.DataFrame,
    *,
    symbol: str,
    timeframe: str,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Normalize a DataFrame of Dukascopy bars and return a standard response."""
    tool_name = "normalize_dukascopy_bars"
    started_at = time.perf_counter()
    validation_error = _validate_symbol(symbol) or _validate_timeframe(timeframe)
    if validation_error:
        return _tool_error(
            tool_name=tool_name,
            request_id=request_id,
            started_at=started_at,
            code="INVALID_INPUT",
            message="Invalid input.",
            details=validation_error,
        )
    try:
        snapshot = _normalize_dukascopy_bars(bars, symbol=symbol, timeframe=timeframe)
        return _tool_success(
            tool_name=tool_name,
            request_id=request_id,
            started_at=started_at,
            message="Dukascopy bars normalized successfully.",
            data=snapshot.to_payload(include_bars=True),
        )
    except Exception as error:
        return _tool_error(
            tool_name=tool_name,
            request_id=request_id,
            started_at=started_at,
            code="VALIDATION_FAILED",
            message="Dukascopy bar normalization failed.",
            details=str(error),
        )


_TOOL_MARKER = "_haruquant_standardized_tool"
setattr(dukascopy_data_load, _TOOL_MARKER, True)
setattr(dukascopy_data_list_symbols, _TOOL_MARKER, True)
setattr(dukascopy_data_resolve_instrument, _TOOL_MARKER, True)


__all__ = [
    "DukascopyBarsSnapshot",
    "dukascopy_data_load",
    "dukascopy_data_list_symbols",
    "dukascopy_data_resolve_instrument",
    "fetch",
    "get_instrument",
    "live_fetch",
    "load_dukascopy",
    "normalize_dukascopy_bars",
]
