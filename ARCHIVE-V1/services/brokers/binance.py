"""Binance broker client service.

This module provides the BinanceClient class responsible for managing the connection
to Binance via python-binance, fetching real klines, and aggregate trades as ticks.
"""

from datetime import UTC, datetime
from typing import Any

import pandas as pd
from app.services.utils.logger import logger
from binance.client import Client as BinanceAPIClient


class BinanceClient:
    """Client for interacting with the Binance API interface.

    Handles initialization, connection checking, and lifecycle connection gates.
    """

    _instance: "BinanceClient | None" = None

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
    ) -> None:
        """Description.
            Initialize the Binance client with API credentials.

        Args:
            api_key: str | None.
            api_secret: str | None.

        Returns:
            None.
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self._connected = False

        logger.info(
            "BinanceClient initialized",
            extra={
                "has_api_key": self.api_key is not None,
            },
        )

    def connect(self) -> bool:
        """Description.
            Initialize connection to Binance API.

        Args:
            None.

        Returns:
            bool.
        """
        self._connected = True
        logger.info("Binance client connected successfully.")
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
        logger.info("Binance client disconnected successfully.")

    def is_connected(self) -> bool:
        """Description.
            Check if client is currently connected.

        Args:
            None.

        Returns:
            bool.
        """
        logger.debug(
            f"Checking Binance client connection state (connected={self._connected})."
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
            Get OHLCVS bars from Binance.

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
        if not self.is_connected():
            self.connect()

        logger.debug(
            "Fetching Binance bars for {} (timeframe={}, count={}).",
            symbol,
            timeframe,
            count,
        )

        # Map timeframe to Binance interval
        tf_map = {
            "M1": BinanceAPIClient.KLINE_INTERVAL_1MINUTE,
            "M3": BinanceAPIClient.KLINE_INTERVAL_3MINUTE,
            "M5": BinanceAPIClient.KLINE_INTERVAL_5MINUTE,
            "M15": BinanceAPIClient.KLINE_INTERVAL_15MINUTE,
            "M30": BinanceAPIClient.KLINE_INTERVAL_30MINUTE,
            "H1": BinanceAPIClient.KLINE_INTERVAL_1HOUR,
            "H2": BinanceAPIClient.KLINE_INTERVAL_2HOUR,
            "H4": BinanceAPIClient.KLINE_INTERVAL_4HOUR,
            "H6": BinanceAPIClient.KLINE_INTERVAL_6HOUR,
            "H8": BinanceAPIClient.KLINE_INTERVAL_8HOUR,
            "H12": BinanceAPIClient.KLINE_INTERVAL_12HOUR,
            "D1": BinanceAPIClient.KLINE_INTERVAL_1DAY,
            "W1": BinanceAPIClient.KLINE_INTERVAL_1WEEK,
            "MN1": BinanceAPIClient.KLINE_INTERVAL_1MONTH,
        }

        tf_upper = timeframe.upper()
        interval = tf_map.get(tf_upper, BinanceAPIClient.KLINE_INTERVAL_1HOUR)

        client = BinanceAPIClient(self.api_key or "", self.api_secret or "")

        # Format symbol for Binance, e.g. "BTCUSD" -> "BTCUSDT"
        sym_upper = symbol.upper()
        suffixes = ("USDT", "BTC", "ETH", "BNB")
        if not any(sym_upper.endswith(suffix) for suffix in suffixes):
            sym_upper = sym_upper + "USDT"

        if date_from is not None:
            start_str = int(date_from.timestamp() * 1000)
            end_dt = date_to or datetime.now(UTC)
            end_str = int(end_dt.timestamp() * 1000)
            klines = client.get_historical_klines(
                sym_upper, interval, start_str, end_str
            )
        else:
            klines = client.get_klines(
                symbol=sym_upper, interval=interval, limit=count + start_pos
            )

        cols = ["Timestamp", "Open", "High", "Low", "Close", "Volume", "Spread"]
        if not klines:
            return pd.DataFrame(columns=cols)

        bars = []
        for k in klines:
            bars.append(
                {
                    "Timestamp": pd.to_datetime(k[0], unit="ms", utc=True),
                    "Open": float(k[1]),
                    "High": float(k[2]),
                    "Low": float(k[3]),
                    "Close": float(k[4]),
                    "Volume": float(k[5]),
                    "Spread": 0.0,
                }
            )

        df = pd.DataFrame(bars)
        if date_from is None:
            df = df.tail(count + start_pos).head(count)

        logger.info("Fetched {} Binance bars for {}.", len(df), symbol)
        return df[cols]

    def get_ticks(
        self,
        symbol: str,
        count: int = 100,
        start: datetime | None = None,
        end: datetime | None = None,
        as_dataframe: bool = True,
    ) -> pd.DataFrame | list[dict[str, Any]] | None:
        """Description.
            Get ticks from Binance (using aggregate trades).

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

        logger.debug("Fetching Binance ticks for {} (count={}).", symbol, count)

        client = BinanceAPIClient(self.api_key or "", self.api_secret or "")

        sym_upper = symbol.upper()
        suffixes = ("USDT", "BTC", "ETH", "BNB")
        if not any(sym_upper.endswith(suffix) for suffix in suffixes):
            sym_upper = sym_upper + "USDT"

        if start is not None:
            start_ms = int(start.timestamp() * 1000)
            end_dt = end or datetime.now(UTC)
            end_ms = int(end_dt.timestamp() * 1000)
            trades = client.get_aggregate_trades(
                symbol=sym_upper, startTime=start_ms, endTime=end_ms
            )
        else:
            trades = client.get_recent_trades(symbol=sym_upper, limit=count)

        if not trades:
            return pd.DataFrame() if as_dataframe else []

        ticks = []
        for t in trades:
            price = float(t.get("p") or t.get("price") or 0.0)
            qty = float(t.get("q") or t.get("qty") or 0.0)
            ts = int(t.get("T") or t.get("time") or 0)

            ticks.append(
                {
                    "Timestamp": pd.to_datetime(ts, unit="ms", utc=True),
                    "bid": price,
                    "ask": price,
                    "last": price,
                    "volume": qty,
                    "spread": 0.0,
                }
            )

        df = pd.DataFrame(ticks)
        if start is None:
            df = df.tail(count)

        res_df = df[["Timestamp", "bid", "ask", "last", "volume", "spread"]]

        logger.info("Fetched {} Binance ticks for {}.", len(res_df), symbol)
        if as_dataframe:
            return res_df
        return res_df.to_dict(orient="records")

    @classmethod
    def get_instance(cls) -> "BinanceClient":
        """Description.
            Get the shared singleton instance of BinanceClient.

        Args:
            None.

        Returns:
            'BinanceClient'.
        """
        if cls._instance is None:
            cls._instance = cls()
        logger.debug("Retrieving BinanceClient singleton instance.")
        return cls._instance


def get_binance_client() -> BinanceClient:
    """Description.
        Get the shared singleton instance of BinanceClient.

    Args:
        None.

    Returns:
        BinanceClient.
    """
    logger.debug("Retrieving active BinanceClient instance via public helper.")
    return BinanceClient.get_instance()


__all__ = [
    "BinanceClient",
    "get_binance_client",
]
