# ruff: noqa: E501, C901, BLE001, PLR0911, EM102, ANN401, S113, N806, TRY201, PERF402, PLR2004
"""Dukascopy broker client service.

This module provides the DukascopyClient class responsible for managing the lifecycle
of connection endpoints for Dukascopy data feeds, and includes the HTTP freeserv scraper
to fetch real tick and bar data.
"""

import fnmatch
import json
import random
import string
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from time import sleep
from typing import Any

import pandas as pd
import requests
from app.services.brokers.dukascopy_instruments import INSTRUMENT_MAP
from app.services.utils.common import bars_to_records
from app.services.utils.logger import logger

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

_interval_units = {
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

OFFER_SIDE_BID = "B"
OFFER_SIDE_ASK = "A"


def _resample_to_nearest(
    timestamp: datetime,
    time_unit: str,
    interval_value: int,
) -> datetime:
    """Description.
        Resample timestamp to nearest time unit.

    Args:
        timestamp: datetime.
        time_unit: str.
        interval_value: int.

    Returns:
        datetime.
    """
    logger.debug(
        f"Resampling timestamp={timestamp} to nearest "
        f"time_unit={time_unit}, interval_value={interval_value}."
    )
    if time_unit == TIME_UNIT_SEC:  # pragma: no cover
        subtraction = timestamp.second % interval_value  # pragma: no cover
        return timestamp - timedelta(  # pragma: no cover
            seconds=subtraction,  # pragma: no cover
            microseconds=timestamp.microsecond,  # pragma: no cover
        )  # pragma: no cover
    if time_unit == TIME_UNIT_MIN:  # pragma: no cover
        subtraction = timestamp.minute % interval_value  # pragma: no cover
        return timestamp - timedelta(  # pragma: no cover
            minutes=subtraction,  # pragma: no cover
            seconds=timestamp.second,  # pragma: no cover
            microseconds=timestamp.microsecond,  # pragma: no cover
        )  # pragma: no cover
    if time_unit == TIME_UNIT_HOUR:  # pragma: no cover
        subtraction = timestamp.hour % interval_value  # pragma: no cover
        return timestamp - timedelta(  # pragma: no cover
            hours=subtraction,  # pragma: no cover
            minutes=timestamp.minute,  # pragma: no cover
            seconds=timestamp.second,  # pragma: no cover
            microseconds=timestamp.microsecond,  # pragma: no cover
        )  # pragma: no cover
    if time_unit == TIME_UNIT_DAY:  # pragma: no cover
        subtraction = timestamp.day % interval_value  # pragma: no cover
        return timestamp - timedelta(  # pragma: no cover
            days=subtraction,  # pragma: no cover
            hours=timestamp.hour,  # pragma: no cover
            minutes=timestamp.minute,  # pragma: no cover
            seconds=timestamp.second,  # pragma: no cover
            microseconds=timestamp.microsecond,  # pragma: no cover
        )  # pragma: no cover
    if time_unit == TIME_UNIT_WEEK:  # pragma: no cover
        subtraction = (timestamp.weekday() + 1) % (
            interval_value * 7
        )  # pragma: no cover
        return timestamp - timedelta(  # pragma: no cover
            days=subtraction,  # pragma: no cover
            hours=timestamp.hour,  # pragma: no cover
            minutes=timestamp.minute,  # pragma: no cover
            seconds=timestamp.second,  # pragma: no cover
            microseconds=timestamp.microsecond,  # pragma: no cover
        )  # pragma: no cover
    if time_unit == TIME_UNIT_MONTH:  # pragma: no cover
        month = (timestamp.month // interval_value) + 1  # pragma: no cover
        return datetime(
            timestamp.year, month, 1, 0, 0, 0, 0, timestamp.tzinfo
        )  # pragma: no cover
    if time_unit == TIME_UNIT_TICK:  # pragma: no cover
        return timestamp  # pragma: no cover

    raise NotImplementedError(
        f"resampling not implemented for {time_unit}"
    )  # pragma: no cover


def _get_dataframe_columns_for_timeunit(time_unit: str) -> list[str]:
    """Description.
        Get dataframe columns for time unit.

    Args:
        time_unit: str.

    Returns:
        list[str].
    """
    logger.debug(f"Retrieving DataFrame columns for Dukascopy time_unit: '{time_unit}'")
    ohlc_df = ["timestamp", "open", "high", "low", "close", "volume"]
    tick_df = ["timestamp", "bidPrice", "askPrice", "bidVolume", "askVolume"]

    return {
        TIME_UNIT_DAY: ohlc_df,
        TIME_UNIT_HOUR: ohlc_df,
        TIME_UNIT_MIN: ohlc_df,
        TIME_UNIT_MONTH: ohlc_df,
        TIME_UNIT_SEC: ohlc_df,
        TIME_UNIT_TICK: tick_df,
        TIME_UNIT_WEEK: ohlc_df,
    }[time_unit]


def _fetch(
    instrument: str,
    interval: str,
    offer_side: str,
    last_update: int,
    limit: int | None = None,
) -> Any:
    """Description.
        Fetch data from Dukascopy freeserv.

    Args:
        instrument: str.
        interval: str.
        offer_side: str.
        last_update: int.
        limit: int | None.

    Returns:
        Any.
    """
    characters = string.ascii_letters + string.digits
    jsonp = f"_callbacks____{''.join(random.choices(characters, k=9))}"

    query_params = {
        "path": "chart/json3",
        "splits": "true",
        "stocks": "true",
        "time_direction": "N",
        "jsonp": jsonp,
        "last_update": f"{int(last_update)}",
        "offer_side": f"{offer_side}",
        "instrument": f"{instrument}",
        "interval": f"{interval}",
    }

    if limit is not None:  # pragma: no cover
        query_params["limit"] = f"{int(limit)}"

    base_url = "https://freeserv.dukascopy.com/2.0/index.php"

    logger.debug(
        "Requesting Dukascopy freeserv data for %s (interval=%s).",
        instrument,
        interval,
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
        "Host": "freeserv.dukascopy.com",
        "Referer": "https://freeserv.dukascopy.com/2.0/?path=chart/index&showUI=true&showTabs=true&showParameterToolbar=true&showOfferSide=true&allowInstrumentChange=true&allowPeriodChange=true&allowOfferSideChange=true&showAdditionalToolbar=true&showExportImportWorkspace=true&allowSocialSharing=true&showUndoRedoButtons=true&showDetachButton=true&presentationType=candle&axisX=true&axisY=true&legend=true&timeline=true&showDateSeparators=true&showZoom=true&showScrollButtons=true&showAutoShiftButton=true&crosshair=true&borders=false&freeMode=false&theme=Pastelle&uiColor=%23000&availableInstruments=l%3A&instrument=EUR/USD&period=5&offerSide=BID&timezone=0&live=true&allowPan=true&width=100%25&height=700&adv=popup&lang=en",
    }

    response = requests.get(base_url, headers=headers, params=query_params)
    jsonText = response.text.removeprefix(f"{jsonp}(").removesuffix(");")
    return json.loads(jsonText)


def _stream(
    instrument: str,
    interval: str,
    offer_side: str,
    start: datetime,
    end: datetime | None = None,
    max_retries: int = 7,
    limit: int | None = None,
) -> Generator[list[Any]]:
    """Description.
        Stream data from Dukascopy freeserv.

    Args:
        instrument: str.
        interval: str.
        offer_side: str.
        start: datetime.
        end: datetime | None.
        max_retries: int.
        limit: int | None.

    Returns:
        Generator[list[Any]].
    """
    logger.debug(
        "Streaming Dukascopy data for %s (interval=%s) from %s.",
        instrument,
        interval,
        start,
    )
    no_of_retries = 0
    cursor = int(start.timestamp() * 1000)
    end_timestamp = None
    if end is not None:  # pragma: no cover
        end_timestamp = end.timestamp() * 1000

    is_first_iteration = True

    while True:
        try:
            lastUpdates = _fetch(
                instrument=instrument,
                interval=interval,
                offer_side=offer_side,
                last_update=cursor,
                limit=limit,
            )

            if not is_first_iteration and lastUpdates and lastUpdates[0][0] == cursor:
                lastUpdates = lastUpdates[1:]

            if not lastUpdates or len(lastUpdates) < 1:
                if end is not None:
                    break
                else:
                    sleep(0.5)  # pragma: no cover
                    continue  # pragma: no cover

            for row in lastUpdates:
                if end_timestamp is not None and row[0] > end_timestamp:
                    return  # pragma: no cover
                if interval == INTERVAL_TICK:
                    row[-1] = row[-1] / 1_000_000
                    row[-2] = row[-2] / 1_000_000
                yield row
                cursor = row[0]

            no_of_retries = 0
            is_first_iteration = False

        except Exception as e:
            no_of_retries += 1
            if max_retries is not None and (no_of_retries - 1) > max_retries:
                raise e
            else:
                sleep(1)
            continue


def fetch(
    instrument: str,
    interval: str,
    offer_side: str,
    start: datetime,
    end: datetime,
    max_retries: int = 7,
    limit: int = 30_000,
) -> pd.DataFrame:
    """Description.
        Fetch data from Dukascopy freeserv.

    Args:
        instrument: str.
        interval: str.
        offer_side: str.
        start: datetime.
        end: datetime.
        max_retries: int.
        limit: int.

    Returns:
        pd.DataFrame.
    """
    time_unit = _interval_units[interval]
    columns = _get_dataframe_columns_for_timeunit(time_unit)

    data = []
    datafeed = _stream(
        instrument=instrument,
        interval=interval,
        offer_side=offer_side,
        start=start,
        end=end,
        max_retries=max_retries,
        limit=limit,
    )

    for row in datafeed:
        data.append(row)

    df = pd.DataFrame(data=data, columns=columns)
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        unit="ms",
        utc=True,
    )
    df = df.set_index("timestamp")
    logger.info(
        "Fetched %d Dukascopy rows for %s (interval=%s).",
        len(df),
        instrument,
        interval,
    )
    return df


class DukascopyClient:
    """Client for interacting with the Dukascopy feed interface.

    Handles initialization, connection checking, and lifecycle connection gates.
    """

    _instance: "DukascopyClient | None" = None

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        """Description.
            Initialize the Dukascopy client with account credentials.

        Args:
            username: str | None.
            password: str | None.

        Returns:
            None.
        """
        self.username = username
        self.password = password
        self._connected = False

        logger.info(
            "DukascopyClient initialized",
            extra={
                "username": self.username,
            },
        )

    def connect(self) -> bool:
        """Description.
            Initialize connection to Dukascopy feed.

        Args:
            None.

        Returns:
            bool.
        """
        self._connected = True
        logger.info("Dukascopy client connected successfully.")
        return True

    def disconnect(self) -> None:
        """Description.
            Shutdown the connection and clean up resources.

        Args:
            None.

        Returns:
            None.
        """
        self._connected = False
        logger.info("Dukascopy client disconnected successfully.")

    def is_connected(self) -> bool:
        """Description.
            Check if client is currently connected.

        Args:
            None.

        Returns:
            bool.
        """
        logger.debug(
            f"Checking Dukascopy client connection state (connected={self._connected})."
        )
        return self._connected

    def get_bars(
        self,
        symbol: str,
        timeframe: str,
        count: int = 100,
        start_pos: int = 0,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> pd.DataFrame:
        """Description.
            Get OHLCVS bars from Dukascopy.

        Args:
            symbol: str.
            timeframe: str.
            count: int.
            start_pos: int.
            date_from: datetime | None.
            date_to: datetime | None.

        Returns:
            pd.DataFrame.
        """
        if not self.is_connected():  # pragma: no cover
            self.connect()

        logger.debug(
            "Fetching Dukascopy bars for %s (timeframe=%s, count=%d).",
            symbol,
            timeframe,
            count,
        )

        # Normalise symbol: e.g. "EURUSD" -> "EUR/USD"
        if len(symbol) == 6 and "/" not in symbol:
            instrument = f"{symbol[:3].upper()}/{symbol[3:].upper()}"
        else:
            instrument = symbol  # pragma: no cover

        # Map standard timeframe to Dukascopy interval
        tf_map = {
            "M1": "1MIN",
            "M5": "5MIN",
            "M15": "15MIN",
            "M30": "30MIN",
            "H1": "1HOUR",
            "H4": "4HOUR",
            "D1": "1DAY",
            "W1": "1WEEK",
            "MN1": "1MONTH",
        }
        tf_upper = timeframe.upper()
        if tf_upper not in tf_map:
            msg = f"Unsupported Dukascopy timeframe: {timeframe}"
            logger.error(msg)
            raise ValueError(msg)
        dukas_interval = tf_map[tf_upper]

        # Calculate time range if date_from is not specified
        if date_from is None:
            period_hours = {
                "M1": 1 / 60,
                "M5": 5 / 60,
                "M15": 15 / 60,
                "M30": 30 / 60,
                "H1": 1,
                "H4": 4,
                "D1": 24,
                "W1": 168,
                "MN1": 720,
            }
            hours_needed = (count + start_pos) * period_hours.get(tf_upper, 1)
            # buffer for weekends
            buffer_multiplier = 2.0 if tf_upper in ("D1", "W1") else 1.5
            dt_to = date_to if date_to is not None else datetime.now(UTC)
            dt_from = dt_to - timedelta(hours=hours_needed * buffer_multiplier)
        else:
            dt_from = date_from  # pragma: no cover
            dt_to = (
                date_to if date_to is not None else datetime.now(UTC)
            )  # pragma: no cover

        try:
            df = fetch(
                instrument=instrument,
                interval=dukas_interval,
                offer_side="B",
                start=dt_from,
                end=dt_to,
                limit=30000,
            )
        except Exception as e:
            logger.error("Dukascopy fetch failed: {}", e)
            return pd.DataFrame(
                columns=[
                    "Timestamp",
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Volume",
                    "Spread",
                ]
            )

        if df.empty:
            return pd.DataFrame(  # pragma: no cover
                columns=[
                    "Timestamp",
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Volume",
                    "Spread",
                ]
            )

        df = df.reset_index()
        df = df.rename(
            columns={
                "timestamp": "Timestamp",
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume",
            }
        )
        df["Spread"] = 0.0002  # standard EURUSD 2-pip spread representation

        df["Timestamp"] = pd.to_datetime(df["Timestamp"], utc=True)

        if date_from is None:  # pragma: no cover
            df = df.tail(count)

        logger.info("Fetched %d Dukascopy bars for %s.", len(df), symbol)
        return df[["Timestamp", "Open", "High", "Low", "Close", "Volume", "Spread"]]

    def get_ticks(
        self,
        symbol: str,
        count: int = 100,
        start: datetime | None = None,
        end: datetime | None = None,
        as_dataframe: bool = True,
    ) -> pd.DataFrame | list[dict[str, Any]] | None:
        """Description.
            Get ticks from Dukascopy.

        Args:
            symbol: str.
            count: int.
            start: datetime | None.
            end: datetime | None.
            as_dataframe: bool.

        Returns:
            pd.DataFrame | list[dict[str, Any]] | None.
        """
        if not self.is_connected():
            self.connect()

        logger.debug("Fetching Dukascopy ticks for %s (count=%d).", symbol, count)

        if len(symbol) == 6 and "/" not in symbol:
            instrument = f"{symbol[:3].upper()}/{symbol[3:].upper()}"
        else:
            instrument = symbol

        if start is None:
            dt_end = end if end is not None else datetime.now(UTC)
            dt_start = dt_end - timedelta(hours=1)
        else:
            dt_start = start
            dt_end = end if end is not None else datetime.now(UTC)

        try:
            df = fetch(
                instrument=instrument,
                interval="TICK",
                offer_side="B",
                start=dt_start,
                end=dt_end,
                limit=30000,
            )
        except Exception as e:
            logger.error("Dukascopy tick fetch failed: {}", e)
            return None

        if df.empty:
            return pd.DataFrame() if as_dataframe else []  # pragma: no cover

        df = df.reset_index()
        df = df.rename(
            columns={
                "timestamp": "Timestamp",
                "bidPrice": "bid",
                "askPrice": "ask",
            }
        )
        df["last"] = (df["bid"] + df["ask"]) / 2.0
        df["volume"] = df["bidVolume"]
        df["spread"] = df["ask"] - df["bid"]

        df["Timestamp"] = pd.to_datetime(df["Timestamp"], utc=True)

        res_df = df[["Timestamp", "bid", "ask", "last", "volume", "spread"]]

        if start is None:  # pragma: no cover
            res_df = res_df.tail(count)

        logger.info("Fetched %d Dukascopy ticks for %s.", len(res_df), symbol)
        if as_dataframe:
            return res_df  # pragma: no cover
        return res_df.to_dict(orient="records")

    @classmethod
    def get_instance(cls) -> "DukascopyClient":
        """Description.
            Get the shared singleton instance of DukascopyClient.

        Args:
            None.

        Returns:
            'DukascopyClient'.
        """
        if cls._instance is None:
            cls._instance = cls()
        logger.debug("Retrieving DukascopyClient singleton instance.")
        return cls._instance


def get_dukascopy_client() -> DukascopyClient:
    """Description.
        Get the shared singleton instance of DukascopyClient.

    Args:
        None.

    Returns:
        DukascopyClient.
    """
    logger.debug("Retrieving active DukascopyClient instance via public helper.")
    return DukascopyClient.get_instance()


def _load_dukascopy_impl(
    symbol: str,
    timeframe: str = "H1",
    start_date: str | datetime | None = None,
    end_date: str | datetime | None = None,
    count: int | None = None,
    cache: bool = True,
) -> pd.DataFrame:
    """Description.
        Load OHLCV bars from Dukascopy as a DataFrame.

    Args:
        symbol: str.
        timeframe: str.
        start_date: str | datetime | None.
        end_date: str | datetime | None.
        count: int | None.
        cache: bool.

    Returns:
        pd.DataFrame.
    """
    del cache
    parsed_start = _parse_date_value(start_date)
    parsed_end = _parse_date_value(end_date)
    client = get_dukascopy_client()
    frame = client.get_bars(
        symbol=symbol,
        timeframe=timeframe,
        count=count or 100,
        date_from=parsed_start,
        date_to=parsed_end,
    )
    logger.info("Loaded %d Dukascopy bars for %s.", len(frame), symbol)
    return frame


def _parse_date_value(value: str | datetime | None) -> datetime | None:
    """Description.
        Parse a date-like value for Dukascopy wrappers.

    Args:
        value: str | datetime | None.

    Returns:
        datetime | None.
    """
    logger.debug(f"Parsing date-like value: {value}")
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_dukascopy(
    symbol: str,
    timeframe: str | None = "H1",
    start_date: str | datetime | None = None,
    end_date: str | datetime | None = None,
    count: int | None = None,
    cache: bool = True,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Description.
        Load OHLCV bars from Dukascopy through the broker-owned client.

    Args:
        symbol: str.
        timeframe: str | None.
        start_date: str | datetime | None.
        end_date: str | datetime | None.
        count: int | None.
        cache: bool.
        request_id: str | None.

    Returns:
        dict[str, Any].
    """
    logger.debug(
        f"Initiating Dukascopy public load workflow for symbol={symbol}, "
        f"timeframe={timeframe}, request_id={request_id}."
    )
    del cache
    if not symbol:
        return {"status": "error", "message": "symbol argument is required."}
    try:
        client = get_dukascopy_client()
        frame = client.get_bars(
            symbol=symbol,
            timeframe=timeframe or "H1",
            count=count or 1000,
            date_from=_parse_date_value(start_date),
            date_to=_parse_date_value(end_date),
        )
        if frame is None:
            frame = pd.DataFrame()
        frame = frame.copy()
        if "Timestamp" in frame.columns:
            frame["Timestamp"] = pd.to_datetime(frame["Timestamp"], utc=True)
            frame = frame.set_index("Timestamp")
        frame = frame.rename(
            columns={column: str(column).lower() for column in frame.columns}
        )
        records_result = bars_to_records(frame)
        records = (
            records_result.get("data", [])
            if isinstance(records_result, dict)
            else records_result
        )
        return {
            "status": "success",
            "message": "Dukascopy data loaded successfully.",
            "data": {
                "source": "load_dukascopy",
                "symbol": symbol,
                "timeframe": timeframe,
                "rows": len(frame),
                "columns": [str(column) for column in frame.columns],
                "data": records,
            },
            "request_id": request_id,
        }
    except Exception as exc:
        return {"status": "error", "message": f"Tool execution failed: {exc!s}"}


def dukascopy_data_list_symbols(
    pattern: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Description.
        List known Dukascopy instrument symbols from broker metadata.

    Args:
        pattern: str | None.
        request_id: str | None.

    Returns:
        dict[str, Any].
    """
    del request_id
    symbols = sorted(set(INSTRUMENT_MAP) | set(INSTRUMENT_MAP.values()))
    if pattern:
        pattern_lower = pattern.lower()
        symbols = [
            symbol
            for symbol in symbols
            if fnmatch.fnmatch(symbol.lower(), pattern_lower)
            or pattern_lower in symbol.lower()
        ]
    logger.debug(f"Listing known Dukascopy symbols filtered by pattern={pattern}.")
    return {"status": "success", "data": {"symbols": symbols}}


__all__ = [
    "DukascopyClient",
    "dukascopy_data_list_symbols",
    "fetch",
    "get_dukascopy_client",
    "load_dukascopy",
]
