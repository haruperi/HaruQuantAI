"""Chart specifications and catalog metadata records.

Description:
    Provides market data request specification and resample compatibility
    abstractions (ChartDef) matching SQX `com.strategyquant.datalib.ChartDef`,
    and dataset boundary/storage catalog records (DataInfo) matching
    `com.strategyquant.datalib.DataInfo`.

Purpose:
    FEAT-DATA-CATALOG: Chart specifications and catalog metadata records.

Key Capabilities:
    - FR-DATA-CHART-DEF-AND-CATALOG: Chart specifications and catalog metadata records.
      Associated: `ChartDef`, `DataInfo`.
      Logging: Pure in-memory metadata records with zero logging overhead.

Python API Usage:
    ```python
    from app.services.data.catalog import ChartDef, DataInfo

    chart = ChartDef("EURUSD", "M1")
    info = DataInfo(symbol="EURUSD", timeframe="M1")
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.data.catalog
    ```
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, replace
from typing import Any

from app.host.logging import get_logger

from .primitives import Timeframe

__all__ = [
    "ChartDef",
    "DataInfo",
]

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Stage 2A: ChartDef & DataInfo Market Data Abstractions
# ---------------------------------------------------------------------------


@dataclass
class ChartDef:
    """Market data request specification and resample compatibility abstraction.

    Corresponds to `com.strategyquant.datalib.ChartDef`. Defines chart properties,
    symbol identifiers, sessions, spread settings, and resample predicates.
    """

    symbol: str
    timeframe: str | Timeframe = "M1"
    instrument: str = "Forex"
    session: str = "Default"
    connection_name: str = ""
    connection_hash: int = 0
    symbol_hash: int = 0
    history_from: int = 0
    history_to: int = 0
    loaded_history_from: int = 0
    spread: float = 0.0
    real_spread: bool = False
    bar_time_type: int = 0
    min_distance: float = 0.0
    is_backtest_data_def: bool = False
    backload_type: int = 0
    backload_number: int = 0
    registered: bool = False

    def __post_init__(self) -> None:
        """Normalize timeframe string and initialize deterministic hashes."""
        if isinstance(self.timeframe, Timeframe):
            self.timeframe = self.timeframe.value
        if not self.connection_hash and self.connection_name:
            self.connection_hash = abs(hash(self.connection_name))
        if not self.symbol_hash and self.symbol:
            self.symbol_hash = abs(hash(self.symbol))

    @property
    def timeframe_str(self) -> str:
        """String representation of timeframe."""
        return str(self.timeframe)

    @property
    def timeframe_seconds(self) -> int:
        """Timeframe duration in seconds."""
        if isinstance(self.timeframe, Timeframe):
            return self.timeframe.to_seconds()
        tf_str = self.timeframe.strip().upper()
        if tf_str in ("TICK", "TICKS"):
            return 0
        try:
            return Timeframe.from_string(tf_str).to_seconds()
        except ValueError:
            pass
        if tf_str.startswith("S") and tf_str[1:].isdigit():
            return int(tf_str[1:])
        return 0

    def is_registered(self) -> bool:
        """Check if chart definition is registered."""
        return self.registered

    def set_registered(self, registered: bool = True) -> None:
        """Set registration flag."""
        self.registered = registered

    def get_symbol(self) -> str:
        """Get chart symbol."""
        return self.symbol

    def set_symbol(self, symbol: str) -> None:
        """Set chart symbol and recompute symbol hash."""
        self.symbol = symbol
        self.symbol_hash = abs(hash(symbol))

    def get_instrument(self) -> str:
        """Get instrument class."""
        return self.instrument

    def get_instrument_info(self) -> str:
        """Get instrument class info."""
        return self.instrument

    def get_symbol_info(self) -> str:
        """Get symbol instrument info."""
        return self.instrument

    def get_timeframe(self) -> str:
        """Get timeframe string."""
        return str(self.timeframe)

    def get_session(self) -> str:
        """Get chart session identifier."""
        return self.session

    def set_session(self, session: str) -> None:
        """Set chart session identifier."""
        self.session = session

    def get_connection_name(self) -> str:
        """Get connection provider name."""
        return self.connection_name

    def get_connection_hash(self) -> int:
        """Get connection hash."""
        return self.connection_hash

    def get_symbol_hash(self) -> int:
        """Get symbol hash."""
        return self.symbol_hash

    def get_history_from(self) -> int:
        """Get history start timestamp."""
        return self.history_from

    def set_history_from(self, history_from: int) -> None:
        """Set history start timestamp."""
        self.history_from = history_from

    def get_history_to(self) -> int:
        """Get history end timestamp."""
        return self.history_to

    def set_history_to(self, history_to: int) -> None:
        """Set history end timestamp."""
        self.history_to = history_to

    def get_loaded_history_from(self) -> int:
        """Get loaded history start timestamp."""
        return self.loaded_history_from

    def set_loaded_history_from(self, loaded_history_from: int) -> None:
        """Set loaded history start timestamp."""
        self.loaded_history_from = loaded_history_from

    def get_spread(self) -> float:
        """Get fixed spread points/price units."""
        return self.spread

    def set_spread(self, spread: float) -> None:
        """Set fixed spread."""
        self.spread = spread

    def modify_spread(self, spread: float) -> None:
        """Modify fixed spread."""
        self.spread = spread

    def set_real_spread(self, real_spread: bool) -> None:
        """Set whether real variable spread is active."""
        self.real_spread = real_spread

    def get_min_distance(self) -> float:
        """Get minimum distance in points."""
        return self.min_distance

    def set_min_distance(self, min_distance: float) -> None:
        """Set minimum distance in points."""
        self.min_distance = min_distance

    def get_bar_time_type(self) -> int:
        """Get bar timestamp anchor type (0=Open, 1=Close)."""
        return self.bar_time_type

    def get_effective_bar_time_type(self) -> int:
        """Get effective bar timestamp anchor type."""
        return self.bar_time_type

    def get_backload_type(self) -> int:
        """Get backload type."""
        return self.backload_type

    def get_backload_number(self) -> int:
        """Get backload count / number."""
        return self.backload_number

    def get_is_backtest_data_def(self) -> bool:
        """Check if this chart definition is designated for backtesting."""
        return self.is_backtest_data_def

    def is_symbol_recognized(self) -> bool:
        """Check if symbol is valid/recognized."""
        return bool(self.symbol and len(self.symbol.strip()) > 0)

    def is_smaller_than(self, other: ChartDef) -> bool:
        """Evaluate if this chart's timeframe is strictly smaller than other's."""
        return self.timeframe_seconds < other.timeframe_seconds

    def can_be_computed_from(self, other: ChartDef) -> bool:
        """Evaluate if this chart can be resampled/computed from another chart.

        Conditions:
        - Symbols match (case-insensitive).
        - Sessions match (or either is 'Default').
        - other's timeframe is smaller than or equal to this timeframe.
        - other's timeframe evenly divides this timeframe (or other is tick data).
        - other's historical range covers this chart's range (if specified).
        """
        if self.symbol.strip().upper() != other.symbol.strip().upper():
            return False

        if (
            self.session
            and other.session
            and self.session != "Default"
            and other.session not in ("Default", self.session)
        ):
            return False

        other_sec = other.timeframe_seconds
        self_sec = self.timeframe_seconds

        if other_sec > self_sec:
            return False

        if other_sec > 0 and self_sec % other_sec != 0:
            return False

        has_from_mismatch = (
            self.history_from > 0
            and other.history_from > 0
            and other.history_from > self.history_from
        )
        has_to_mismatch = (
            self.history_to > 0
            and other.history_to > 0
            and other.history_to < self.history_to
        )
        return not (has_from_mismatch or has_to_mismatch)

    def is_same_connection_symbol(self, other: ChartDef) -> bool:
        """Check if both charts share identical connection name and symbol."""
        return (
            self.symbol.strip().upper() == other.symbol.strip().upper()
            and self.connection_name.strip().upper()
            == other.connection_name.strip().upper()
        )

    def get_charts_hash(self) -> str:
        """Compute unique identifier hash string for chart."""
        return f"{self.connection_name}_{self.symbol}_{self.timeframe}_{self.session}"

    def clone(
        self,
        symbol: str | None = None,
        history_from: int | None = None,
        history_to: int | None = None,
    ) -> ChartDef:
        """Clone this ChartDef, optionally overriding symbol or date ranges."""
        overrides: dict[str, Any] = {}
        if symbol is not None:
            overrides["symbol"] = symbol
            overrides["symbol_hash"] = abs(hash(symbol))
        if history_from is not None:
            overrides["history_from"] = history_from
        if history_to is not None:
            overrides["history_to"] = history_to
        return replace(self, **overrides)

    def get_clone(
        self,
        symbol: str | None = None,
        history_from: int | None = None,
        history_to: int | None = None,
    ) -> ChartDef:
        """SQX donor alias for clone()."""
        return self.clone(
            symbol=symbol, history_from=history_from, history_to=history_to
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize ChartDef to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChartDef:
        """Construct ChartDef from a dictionary."""
        valid_keys = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class DataInfo:
    """Market data catalog metadata record.

    Corresponds to `com.strategyquant.datalib.DataInfo`. Encapsulates dataset
    identity, symbol, timeframe, boundaries, row counts, and storage file metadata.
    """

    id: int = 0
    symbol: str = ""
    timeframe: str = "M1"
    instrument: str = "Forex"
    connection: str = ""
    timezone: str = "UTC"
    decimals: int = 4
    date_from: int = 0
    date_from_str: str = ""
    date_to: int = 0
    date_to_str: str = ""
    rows: int = 0
    total_days: int = 0
    filename: str = ""
    file_hash: int = 0
    bar_time_type: int = 0
    remove_weekends: bool = True
    show: bool = True
    source: int = 0
    source_data_id: int = 0
    basket_id: int = 0
    broker_id: int = 0
    original_symbol: str = ""
    seconds_records: int = 0
    u_symbol: str = ""
    u_symbol_name: str = ""

    def clone(self) -> DataInfo:
        """Clone this DataInfo record."""
        return replace(self)

    def to_chart_def(self) -> ChartDef:
        """Convert catalog metadata record into an operational ChartDef."""
        return ChartDef(
            symbol=self.symbol,
            timeframe=self.timeframe,
            instrument=self.instrument,
            connection_name=self.connection,
            history_from=self.date_from,
            history_to=self.date_to,
            bar_time_type=self.bar_time_type,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize DataInfo to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DataInfo:
        """Construct DataInfo from a dictionary."""
        valid_keys = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


def main() -> None:
    """Demonstrate ChartDef and DataInfo catalog metadata."""
    chart = ChartDef(symbol="EURUSD", timeframe="M1")
    print(f"ChartDef created: symbol={chart.symbol}, timeframe={chart.timeframe}")
    info = DataInfo(symbol="EURUSD", timeframe="M1", decimals=5)
    print(f"DataInfo created: symbol={info.symbol}")


if __name__ == "__main__":
    main()
