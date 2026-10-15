"""In-memory streaming intra-bar tick simulator and event cursors.

Description:
    Provides zero-allocation streaming tick simulators (DefaultTickSimulator,
    TSTickSimulator) reproducing intra-bar tick dynamics (Open -> High -> Low ->
    Close or Open -> Low -> High -> Close) into a mutable TickEvent cursor.

Purpose:
    FEAT-DATA-SIMULATION: In-memory streaming tick simulator cursors.

Key Capabilities:
    - FR-DATA-STREAMING-TICK-SIMULATOR: In-memory streaming intra-bar tick cursors.
      Associated: `TickEvent`, `SpreadsMap`, `ITickSimulator`,
        `DefaultTickSimulator`, `TSTickSimulator`.
      Logging: Pure in-memory streaming tick cursors with zero allocation overhead.

Python API Usage:
    ```python
    from app.services.data.simulation import DefaultTickSimulator, TickEvent

    sim = DefaultTickSimulator()
    sim.init(bars)
    event = TickEvent()
    while sim.get_next_tick(event):
        pass
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.data.simulation
    ```
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, override

import numpy as np
from app.host.logging import get_logger

from .primitives import MarketTick

__all__ = [
    "DefaultTickSimulator",
    "ITickSimulator",
    "SpreadsMap",
    "TSTickSimulator",
    "TickEvent",
]

logger = get_logger(__name__)

# ============================================================================
# Component 1: In-Memory Streaming Tick Cursor (SQX ITickSimulator / Default)
# ============================================================================


_TICKS_PER_BAR = 4
_CLOSE_TICK_INDEX = 3
_S_TO_MS_THRESHOLD = 100_000_000_000


@dataclass
class TickEvent:
    """Mutable market tick event buffer for zero-allocation simulation cursors.

    Matches com.strategyquant.datalib.TickEvent specification. Reused across
    billions of simulator ticks in Stage 4B backtesting without object allocation.
    """

    time: int = 0
    bid: float = 0.0
    ask: float = 0.0
    volume: float = 0.0
    symbol: str = ""
    symbol_hash: int = 0
    connection_hash: int = 0
    is_bar_open: bool = False
    is_bar_close: bool = False
    session_start_time: int = 0
    session_end_time: int = 0
    is_set: bool = False

    def set(
        self,
        time: int,
        bid: float,
        ask: float,
        *,
        volume: float = 1.0,
        symbol_hash: int = 0,
        connection_hash: int = 0,
        session_start_time: int = 0,
        session_end_time: int = 0,
        is_bar_open: bool = False,
        is_bar_close: bool = False,
    ) -> None:
        """Mutate all fields in-place on this event buffer."""
        self.time = time
        self.symbol_hash = symbol_hash
        self.connection_hash = connection_hash
        self.bid = bid
        self.ask = ask
        self.volume = volume
        self.session_start_time = session_start_time
        self.session_end_time = session_end_time
        self.is_bar_open = is_bar_open
        self.is_bar_close = is_bar_close
        self.is_set = True

    def copy_from(self, other: TickEvent) -> None:
        """Copy all field values from another TickEvent."""
        self.time = other.time
        self.bid = other.bid
        self.ask = other.ask
        self.volume = other.volume
        self.symbol = other.symbol
        self.symbol_hash = other.symbol_hash
        self.connection_hash = other.connection_hash
        self.is_bar_open = other.is_bar_open
        self.is_bar_close = other.is_bar_close
        self.session_start_time = other.session_start_time
        self.session_end_time = other.session_end_time
        self.is_set = other.is_set

    def reset(self) -> None:
        """Reset event buffer to uninitialized state."""
        self.time = 0
        self.bid = 0.0
        self.ask = 0.0
        self.volume = 0.0
        self.symbol = ""
        self.symbol_hash = 0
        self.connection_hash = 0
        self.is_bar_open = False
        self.is_bar_close = False
        self.session_start_time = 0
        self.session_end_time = 0
        self.is_set = False

    def to_market_tick(self) -> MarketTick:
        """Convert current state to an immutable MarketTick instance."""
        return MarketTick(
            time_msc=self.time,
            bid=self.bid,
            ask=self.ask,
            last=self.bid,
            volume=int(self.volume),
            volume_real=self.volume,
        )


class SpreadsMap:
    """Lookup container mapping instrument/connection keys to spread points.

    Matches com.strategyquant.datalib.ticksimulator.SpreadsMap specification.
    """

    def __init__(self, initial_spreads: dict[int | str, float] | None = None) -> None:
        """Initialize map with optional key-to-spread dictionary."""
        self._spreads: dict[int | str, float] = {}
        if initial_spreads:
            for k, v in initial_spreads.items():
                self._spreads[k] = max(0.0, float(v))

    def contains_key(self, key: int | str) -> bool:
        """Return True if the key has a configured spread."""
        return key in self._spreads

    def get_spread(self, key: int | str, default: float = 0.0) -> float:
        """Retrieve spread points for key, or fallback to default."""
        return self._spreads.get(key, default)

    def set_spread(self, key: int | str, spread: float) -> None:
        """Configure spread points for key."""
        self._spreads[key] = max(0.0, float(spread))


class ITickSimulator(Protocol):
    """Protocol defining the streaming tick simulator cursor contract.

    Matches com.strategyquant.datalib.ticksimulator.ITickSimulator.
    """

    def init(self, bars: Sequence[Any]) -> None:
        """Initialize simulator with historical bars."""
        ...

    def get_next_tick(self, target: TickEvent) -> bool:
        """Mutate target with next intra-bar tick, returning True until exhausted."""
        ...

    def set_symbols_spread(self, spreads: SpreadsMap | dict[int | str, float]) -> None:
        """Configure spread lookup table."""
        ...


class DefaultTickSimulator:
    """Clean-room intra-bar 4-tick simulator cursor for backtesting.

    Emulates com.strategyquant.datalib.ticksimulator.DefaultTickSimulator.
    Generates 4 ticks per bar in O(1) memory:
      - Bullish bar (close >= open): Open -> Low -> High -> Close
      - Bearish bar (close < open): Open -> High -> Low -> Close
    """

    def __init__(
        self,
        point_value: float = 0.00001,
        symbol: str = "",
        symbol_hash: int = 0,
        bar_duration_seconds: int = 60,
    ) -> None:
        """Initialize simulator cursor parameters."""
        self._point_value = max(1e-10, float(point_value))
        self._symbol = symbol
        self._symbol_hash = symbol_hash
        self._bar_duration_ms = max(1000, int(bar_duration_seconds * 1000))
        self._spreads_map = SpreadsMap()
        self._bars: list[Any] = []
        self._bar_index = 0
        self._tick_in_bar = 0

    def init(self, bars: Sequence[Any]) -> None:
        """Initialize simulator with a chronological sequence of bars."""
        self._bars = list(bars)
        self._bar_index = 0
        self._tick_in_bar = 0
        logger.debug(
            "FR-DATA-STREAMING-TICK-SIMULATOR: initialized cursor with %d bars",
            len(self._bars),
        )

    def set_symbols_spread(self, spreads: SpreadsMap | dict[int | str, float]) -> None:
        """Configure symbol spread lookup table."""
        if isinstance(spreads, SpreadsMap):
            self._spreads_map = spreads
        else:
            self._spreads_map = SpreadsMap(spreads)

    def get_next_tick(self, target: TickEvent) -> bool:
        """Advance cursor by one intra-bar tick, mutating target in place.

        Returns True while ticks are available, or False when all bars are exhausted.
        """
        while self._bar_index < len(self._bars):
            bar = self._bars[self._bar_index]
            open_val, high_val, low_val, close_val, vol_val, bar_time = (
                self._extract_bar_ohlcv(bar)
            )

            offsets = self._four_tick_offsets_ms(self._bar_duration_ms)
            bullish = close_val >= open_val

            if bullish:
                prices = (open_val, low_val, high_val, close_val)
            else:
                prices = (open_val, high_val, low_val, close_val)

            tick_idx = self._tick_in_bar
            price = prices[tick_idx]
            tick_time = bar_time + offsets[tick_idx]

            spread_pts = self._spreads_map.get_spread(
                self._symbol_hash or self._symbol,
                default=getattr(bar, "spread", 0.0) or 0.0,
            )
            spread_cash = spread_pts * self._point_value
            bid = price
            ask = price + spread_cash

            is_open = tick_idx == 0
            is_close = tick_idx == _CLOSE_TICK_INDEX

            target.set(
                time=tick_time,
                bid=bid,
                ask=ask,
                volume=max(1.0, vol_val / _TICKS_PER_BAR),
                symbol_hash=self._symbol_hash,
                is_bar_open=is_open,
                is_bar_close=is_close,
            )

            self._tick_in_bar += 1
            if self._tick_in_bar >= _TICKS_PER_BAR:
                self._bar_index += 1
                self._tick_in_bar = 0

            return True

        return False

    def stream_ticks(
        self,
        bars: Sequence[Any] | None = None,
    ) -> Iterator[MarketTick]:
        """Convenience generator yielding immutable MarketTick instances."""
        if bars is not None:
            self.init(bars)
        event = TickEvent()
        while self.get_next_tick(event):
            yield event.to_market_tick()

    @staticmethod
    def _extract_bar_ohlcv(
        bar: Any,
    ) -> tuple[float, float, float, float, float, int]:
        """Extract OHLCV and millisecond timestamp from bar object or dict."""
        if isinstance(bar, dict):
            o_raw = bar.get("open")
            o = float(o_raw if o_raw is not None else bar.get("Open", 0.0))
            h_raw = bar.get("high")
            h = float(h_raw if h_raw is not None else bar.get("High", 0.0))
            low_raw = bar.get("low")
            low_price = float(low_raw if low_raw is not None else bar.get("Low", 0.0))
            c_raw = bar.get("close")
            c = float(c_raw if c_raw is not None else bar.get("Close", 0.0))
            v_raw = bar.get("volume")
            v = float(v_raw if v_raw is not None else bar.get("Volume", 1.0))
            t_val = bar.get("time") or bar.get("Time", 0)
        else:
            o = float(getattr(bar, "open", 0.0))
            h = float(getattr(bar, "high", 0.0))
            low_price = float(getattr(bar, "low", 0.0))
            c = float(getattr(bar, "close", 0.0))
            v = float(getattr(bar, "volume", 1.0))
            t_val = getattr(bar, "time", 0)

        if isinstance(t_val, datetime):
            bar_ms = int(t_val.timestamp() * 1000)
        elif isinstance(t_val, (int, float)):
            bar_ms = int(t_val * 1000) if t_val < _S_TO_MS_THRESHOLD else int(t_val)
        else:
            bar_ms = 0

        return o, h, low_price, c, v, bar_ms

    @staticmethod
    def _four_tick_offsets_ms(bar_ms: int) -> tuple[int, int, int, int]:
        """Return 4 within-bar millisecond offsets."""
        close_offset = max(0, bar_ms - 1)
        first_inner = max(1, bar_ms // 3)
        second_inner = max(first_inner + 1, (2 * bar_ms) // 3)
        second_inner = min(second_inner, max(first_inner + 1, close_offset - 1))
        return (0, first_inner, second_inner, close_offset)


class TSTickSimulator(DefaultTickSimulator):
    """TradeStation-compatible intra-bar tick simulator cursor.

    Emulates com.strategyquant.datalib.ticksimulator.TSTickSimulator.
    Determines turn direction by evaluating proximity of Open to Low vs High:
      - If abs(open - low) < abs(open - high): price moves to Low first.
      - Flat or single-price bars emit reduced ticks.
    """

    @override
    def get_next_tick(self, target: TickEvent) -> bool:
        """Advance cursor using TradeStation intra-bar tick logic."""
        while self._bar_index < len(self._bars):
            bar = self._bars[self._bar_index]
            open_val, high_val, low_val, close_val, vol_val, bar_time = (
                self._extract_bar_ohlcv(bar)
            )

            # Determine TradeStation tick sequence
            prices: tuple[float, ...]
            if open_val == high_val == low_val == close_val:
                prices = (open_val,)
            elif open_val == high_val:
                prices = (open_val, low_val, close_val)
            elif open_val == low_val:
                prices = (open_val, high_val, close_val)
            else:
                dist_to_low = abs(open_val - low_val)
                dist_to_high = abs(open_val - high_val)
                if dist_to_low < dist_to_high:
                    prices = (open_val, low_val, high_val, close_val)
                else:
                    prices = (open_val, high_val, low_val, close_val)

            total_ticks = len(prices)
            offsets = np.linspace(0, self._bar_duration_ms - 1, total_ticks, dtype=int)

            tick_idx = self._tick_in_bar
            price = prices[tick_idx]
            tick_time = bar_time + int(offsets[tick_idx])

            spread_pts = self._spreads_map.get_spread(
                self._symbol_hash or self._symbol,
                default=getattr(bar, "spread", 0.0) or 0.0,
            )
            spread_cash = spread_pts * self._point_value
            bid = price
            ask = price + spread_cash

            is_open = tick_idx == 0
            is_close = tick_idx == total_ticks - 1

            target.set(
                time=tick_time,
                bid=bid,
                ask=ask,
                volume=max(1.0, vol_val / total_ticks),
                symbol_hash=self._symbol_hash,
                is_bar_open=is_open,
                is_bar_close=is_close,
            )

            self._tick_in_bar += 1
            if self._tick_in_bar >= total_ticks:
                self._bar_index += 1
                self._tick_in_bar = 0

            return True

        return False


def main() -> None:
    """Demonstrate streaming tick simulation across synthetic bars."""
    bars = [
        {"open": 1.1, "high": 1.105, "low": 1.095, "close": 1.102, "time": 1700000000},
    ]
    sim = DefaultTickSimulator()
    sim.init(bars)
    event = TickEvent()
    tick_count = 0
    while sim.get_next_tick(event):
        tick_count += 1
    print(f"Generated {tick_count} simulation ticks from bar.")


if __name__ == "__main__":
    main()
