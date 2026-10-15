"""Foundational market data contracts, timeframe models, and bridge exceptions.

Description:
    Provides broker-neutral immutable contracts and primitives for financial
    market data within the Data Manager workspace, including discrete
    candlestick bars (MarketBar), millisecond ticks (MarketTick), standardized
    timeframe enumerations (Timeframe), duration mappings, boundary limits,
    and shared bridge error types.

Purpose:
    FEAT-DATAMGR-CONTRACTS: Foundational market data contracts, timeframe models,
    and primitives.

Key Capabilities:
    - FR-DATAMGR-CONTRACTS-TIMEFRAME: Standard timeframe enums, duration
      calculations, and string parsing.
      Associated: `Timeframe`.
      Logging: Pure numerical data structures with zero logging overhead.
    - FR-DATAMGR-CONTRACTS-TIMEFRAME-SECONDS: Timeframe duration lookup mapping
      for interval arithmetic.
      Associated: `TIMEFRAME_SECONDS`.
      Logging: Constant lookup dictionary with zero logging overhead.
    - FR-DATAMGR-CONTRACTS-MARKET-BAR: Immutable historical OHLC candlestick
      bar record and candle metrics.
      Associated: `MarketBar`.
      Logging: Pure numerical data structures with zero logging overhead.
    - FR-DATAMGR-CONTRACTS-MARKET-TICK: Immutable millisecond tick record with
      instantaneous spread and midpoint.
      Associated: `MarketTick`.
      Logging: Pure numerical data structures with zero logging overhead.
    - FR-DATAMGR-CONTRACTS-BRIDGE-ERROR: Shared base exception for data broker
      bridge communication failures.
      Associated: `BridgeError`.
      Logging: Exception definition with zero logging overhead.
    - FR-DATAMGR-CONTRACTS-PAGINATION-LIMIT: Default and maximum batch pagination
      record limit.
      Associated: `MAX_RECORDS`.
      Logging: Constant boundary definition with zero logging overhead.
    - FR-DATAMGR-CONTRACTS-POSITION-BOUND: Maximum position index boundary
      limit for historical windowing.
      Associated: `MAX_POSITION`.
      Logging: Constant boundary definition with zero logging overhead.
    - FR-DATAMGR-CONTRACTS-TIMEOUT-BOUND: Global default network read timeout limit.
      Associated: `READ_TIMEOUT`.
      Logging: Constant boundary definition with zero logging overhead.

Python API Usage:
    ```python
    from app.workspace.data_manager.contracts import (
        BridgeError,
        MarketBar,
        MarketTick,
        Timeframe,
    )

    tf = Timeframe.from_string("M1")
    bar = MarketBar(time=1700000000, open=1.0, high=1.2, low=0.9, close=1.1)
    tick = MarketTick(time_msc=1700000000000, bid=1.0999, ask=1.1001)
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.contracts
    ```
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.host.logging import get_logger
from app.services.brokers.base import BridgeError

__all__ = [
    "MAX_POSITION",
    "MAX_RECORDS",
    "READ_TIMEOUT",
    "TIMEFRAME_SECONDS",
    "BridgeError",
    "MarketBar",
    "MarketTick",
    "Timeframe",
]

logger = get_logger(__name__)

MAX_RECORDS = 1000
MAX_POSITION = 2**31 - 1
READ_TIMEOUT = 60.0


class Timeframe(StrEnum):
    """Chart and series timeframe enumeration."""

    PERIOD_CURRENT = "CURRENT"
    PERIOD_M1 = "M1"
    PERIOD_M2 = "M2"
    PERIOD_M3 = "M3"
    PERIOD_M4 = "M4"
    PERIOD_M5 = "M5"
    PERIOD_M6 = "M6"
    PERIOD_M10 = "M10"
    PERIOD_M12 = "M12"
    PERIOD_M15 = "M15"
    PERIOD_M20 = "M20"
    PERIOD_M30 = "M30"
    PERIOD_H1 = "H1"
    PERIOD_H2 = "H2"
    PERIOD_H3 = "H3"
    PERIOD_H4 = "H4"
    PERIOD_H6 = "H6"
    PERIOD_H8 = "H8"
    PERIOD_H12 = "H12"
    PERIOD_D1 = "D1"
    PERIOD_W1 = "W1"
    PERIOD_MN1 = "MN1"

    # Shorthand aliases
    M1 = "M1"
    M2 = "M2"
    M3 = "M3"
    M4 = "M4"
    M5 = "M5"
    M6 = "M6"
    M10 = "M10"
    M12 = "M12"
    M15 = "M15"
    M20 = "M20"
    M30 = "M30"
    H1 = "H1"
    H2 = "H2"
    H3 = "H3"
    H4 = "H4"
    H6 = "H6"
    H8 = "H8"
    H12 = "H12"
    D1 = "D1"
    W1 = "W1"
    MN1 = "MN1"

    def to_seconds(self) -> int:
        """Convert timeframe duration to whole seconds."""
        val = self.value
        if val.startswith("M") and self != Timeframe.PERIOD_MN1:
            return int(val[1:]) * 60
        if val.startswith("H"):
            return int(val[1:]) * 3600
        fixed = {
            Timeframe.PERIOD_D1: 86400,
            Timeframe.PERIOD_W1: 604800,
            Timeframe.PERIOD_MN1: 2419200,
        }
        return fixed.get(self, 0)

    def to_minutes(self) -> int:
        """Convert timeframe duration to whole minutes."""
        return self.to_seconds() // 60

    @classmethod
    def from_string(cls, name: str) -> Timeframe:
        """Parse timeframe from common string representations.

        Args:
            name: String such as 'M1', '1m', 'H1', '1h', 'D1', '1d', etc.

        Returns:
            Matching Timeframe member.

        Raises:
            ValueError: If string format cannot be mapped to a standard timeframe.
        """
        cleaned = name.strip().upper()
        mapping: dict[str, Timeframe] = {
            "M1": cls.PERIOD_M1,
            "1M": cls.PERIOD_M1,
            "1MIN": cls.PERIOD_M1,
            "M2": cls.PERIOD_M2,
            "2M": cls.PERIOD_M2,
            "M3": cls.PERIOD_M3,
            "3M": cls.PERIOD_M3,
            "M4": cls.PERIOD_M4,
            "4M": cls.PERIOD_M4,
            "M5": cls.PERIOD_M5,
            "5M": cls.PERIOD_M5,
            "5MIN": cls.PERIOD_M5,
            "M6": cls.PERIOD_M6,
            "6M": cls.PERIOD_M6,
            "M10": cls.PERIOD_M10,
            "10M": cls.PERIOD_M10,
            "M12": cls.PERIOD_M12,
            "12M": cls.PERIOD_M12,
            "M15": cls.PERIOD_M15,
            "15M": cls.PERIOD_M15,
            "15MIN": cls.PERIOD_M15,
            "M20": cls.PERIOD_M20,
            "20M": cls.PERIOD_M20,
            "M30": cls.PERIOD_M30,
            "30M": cls.PERIOD_M30,
            "30MIN": cls.PERIOD_M30,
            "H1": cls.PERIOD_H1,
            "1H": cls.PERIOD_H1,
            "60M": cls.PERIOD_H1,
            "H2": cls.PERIOD_H2,
            "2H": cls.PERIOD_H2,
            "H3": cls.PERIOD_H3,
            "3H": cls.PERIOD_H3,
            "H4": cls.PERIOD_H4,
            "4H": cls.PERIOD_H4,
            "240M": cls.PERIOD_H4,
            "H6": cls.PERIOD_H6,
            "6H": cls.PERIOD_H6,
            "H8": cls.PERIOD_H8,
            "8H": cls.PERIOD_H8,
            "H12": cls.PERIOD_H12,
            "12H": cls.PERIOD_H12,
            "D1": cls.PERIOD_D1,
            "1D": cls.PERIOD_D1,
            "DAY": cls.PERIOD_D1,
            "W1": cls.PERIOD_W1,
            "1W": cls.PERIOD_W1,
            "WEEK": cls.PERIOD_W1,
            "MN1": cls.PERIOD_MN1,
            "1MN": cls.PERIOD_MN1,
            "MONTH": cls.PERIOD_MN1,
        }
        if cleaned in mapping:
            return mapping[cleaned]
        raise ValueError(f"Unknown timeframe identifier: {name!r}")


TIMEFRAME_SECONDS: dict[Timeframe, int] = {
    frame: frame.to_seconds()
    for frame in Timeframe
    if frame != Timeframe.PERIOD_CURRENT
}


@dataclass(frozen=True, slots=True)
class MarketBar:
    """Historical OHLC bar with its UTC opening time in epoch seconds."""

    time: int
    open: float
    high: float
    low: float
    close: float
    tick_volume: int = 0
    spread: int = 0
    real_volume: int = 0

    @property
    def is_bullish(self) -> bool:
        """Check if candle closed higher than open."""
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        """Check if candle closed lower than open."""
        return self.close < self.open

    @property
    def is_doji(self) -> bool:
        """Check if candle closed at open."""
        return self.close == self.open

    @property
    def range(self) -> float:
        """Calculate total bar price range (High - Low)."""
        return self.high - self.low

    @property
    def body(self) -> float:
        """Calculate candle body size abs(Close - Open)."""
        return abs(self.close - self.open)

    @property
    def volume(self) -> float:
        """Calculate primary volume (real_volume if present, else tick_volume)."""
        return float(self.real_volume or self.tick_volume)


@dataclass(frozen=True, slots=True)
class MarketTick:
    """Historical tick retaining UTC epoch milliseconds and native flags."""

    time_msc: int
    bid: float
    ask: float
    last: float = 0.0
    volume: int = 0
    flags: int = 0
    volume_real: float = 0.0

    @property
    def spread(self) -> float:
        """Calculate instantaneous spread (Ask - Bid)."""
        return self.ask - self.bid

    @property
    def mid(self) -> float:
        """Calculate midpoint price."""
        return (self.ask + self.bid) / 2.0

    @property
    def time(self) -> int:
        """UTC epoch milliseconds alias for time_msc."""
        return self.time_msc


def main() -> None:
    """Demonstrate MarketBar, MarketTick, and Timeframe primitives."""
    tf = Timeframe.PERIOD_M1
    print(f"Timeframe: {tf.value}, seconds: {tf.to_seconds()}")
    bar = MarketBar(
        time=1700000000,
        open=1.0850,
        high=1.0860,
        low=1.0845,
        close=1.0855,
        tick_volume=120,
    )
    print(f"Bar: bullish={bar.is_bullish}, range={bar.range:.4f}, body={bar.body:.4f}")
    tick = MarketTick(time_msc=1700000000123, bid=1.0854, ask=1.0856)
    print(f"Tick: mid={tick.mid:.4f}, spread={tick.spread:.4f}")


if __name__ == "__main__":
    main()
