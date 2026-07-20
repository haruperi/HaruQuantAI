"""Yahoo Finance broker client service.

This module provides the YahooClient class responsible for managing the connection
to Yahoo Finance via yfinance, fetching real historical bars, and generating
synthetic tick data based on price constraints.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import pandas as pd
import yfinance as yf
from app.services.utils.logger import logger


class YahooClient:
    """Client for interacting with the Yahoo Finance interface.

    Handles initialization, connection checking, and lifecycle connection gates.
    """

    _instance: "YahooClient | None" = None

    def __init__(self, api_key: str | None = None) -> None:
        """Description.
            Initialize the Yahoo Finance client.

        Args:
            api_key: str | None.

        Returns:
            None.
        """
        self.api_key = api_key
        self._connected = False

        logger.info(
            "YahooClient initialized",
            extra={
                "has_api_key": self.api_key is not None,
            },
        )

    def connect(self) -> bool:
        """Description.
            Initialize connection to Yahoo Finance feed.

        Args:
            None.

        Returns:
            bool.
        """
        self._connected = True
        logger.info("Yahoo Finance client connected successfully.")
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
        logger.info("Yahoo Finance client disconnected successfully.")

    def is_connected(self) -> bool:
        """Description.
            Check if client is currently connected.

        Args:
            None.

        Returns:
            bool.
        """
        logger.debug(
            f"Checking Yahoo Finance client connection state "
            f"(connected={self._connected})."
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
            Get OHLCVS bars from Yahoo Finance.

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
            "Fetching Yahoo bars for {} (timeframe={}, count={}).",
            symbol,
            timeframe,
            count,
        )

        # map timeframe to yfinance interval
        tf_map = {
            "M1": "1m",
            "M2": "2m",
            "M5": "5m",
            "M15": "15m",
            "M30": "30m",
            "H1": "1h",
            "D1": "1d",
            "W1": "1wk",
            "MN1": "1mo",
        }
        tf_upper = timeframe.upper()
        interval = tf_map.get(tf_upper, "1h")

        if date_from is None:
            # Download by period
            period_map = {
                "1m": "1d",
                "2m": "1d",
                "5m": "5d",
                "15m": "5d",
                "30m": "5d",
                "1h": "1mo",
                "1d": "1y",
                "1wk": "5y",
                "1mo": "max",
            }
            period = period_map.get(interval, "1mo")
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
        else:
            ticker = yf.Ticker(symbol)
            start_str = date_from.strftime("%Y-%m-%d")
            end_dt = date_to or datetime.now(UTC)
            end_str = end_dt.strftime("%Y-%m-%d")
            df = ticker.history(start=start_str, end=end_str, interval=interval)

        cols = ["Timestamp", "Open", "High", "Low", "Close", "Volume", "Spread"]
        if df.empty:
            return pd.DataFrame(columns=cols)

        df = df.reset_index()
        date_col = (
            "Datetime"
            if "Datetime" in df.columns
            else ("Date" if "Date" in df.columns else df.columns[0])
        )
        df = df.rename(
            columns={
                date_col: "Timestamp",
                "Open": "Open",
                "High": "High",
                "Low": "Low",
                "Close": "Close",
                "Volume": "Volume",
            }
        )
        df["Spread"] = 0.0

        df["Timestamp"] = pd.to_datetime(df["Timestamp"], utc=True)

        if date_from is None:
            df = df.tail(count + start_pos).head(count)

        logger.info("Fetched {} Yahoo bars for {}.", len(df), symbol)
        return df[cols]

    def get_ticks(
        self,
        symbol: str,
        count: int = 100,
        start: datetime | None = None,
        end: datetime | None = None,  # noqa: ARG002
        as_dataframe: bool = True,
    ) -> pd.DataFrame | list[dict[str, Any]] | None:
        """Description.
            Get ticks from Yahoo Finance (mocked/generated from daily bounds).

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

        logger.debug(
            "Generating Yahoo synthetic ticks for {} (count={}).", symbol, count
        )

        ticker = yf.Ticker(symbol)
        history = ticker.history(period="1d")
        last_price = 100.0
        if not history.empty:
            last_price = float(history["Close"].iloc[-1])

        # Generate synthetic tick updates
        from app.services.data.transforms import (
            generate_synthetic_ticks,
        )

        start_str = (start or datetime.now(UTC) - timedelta(minutes=10)).isoformat()
        ticks = generate_synthetic_ticks(
            symbol=symbol,
            start_time=start_str,
            num_ticks=count,
            start_price=last_price,
            average_spread=0.01,
            volatility=0.001,
        )

        df = pd.DataFrame(ticks)
        if df.empty:
            return pd.DataFrame() if as_dataframe else []

        df["Timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.rename(
            columns={"bid": "bid", "ask": "ask", "last": "last", "volume": "volume"}
        )
        df["spread"] = df["ask"] - df["bid"]

        res_df = df[["Timestamp", "bid", "ask", "last", "volume", "spread"]]

        logger.info("Generated {} Yahoo synthetic ticks for {}.", len(res_df), symbol)
        if as_dataframe:
            return res_df
        return res_df.to_dict(orient="records")

    @classmethod
    def get_instance(cls) -> "YahooClient":
        """Description.
            Get the shared singleton instance of YahooClient.

        Args:
            None.

        Returns:
            'YahooClient'.
        """
        if cls._instance is None:
            cls._instance = cls()
        logger.debug("Retrieving YahooClient singleton instance.")
        return cls._instance


def get_yahoo_client() -> YahooClient:
    """Description.
        Get the shared singleton instance of YahooClient.

    Args:
        None.

    Returns:
        YahooClient.
    """
    logger.debug("Retrieving shared YahooClient instance via public helper.")
    return YahooClient.get_instance()


__all__ = [
    "YahooClient",
    "get_yahoo_client",
]
