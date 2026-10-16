"""Foundational market data contracts, timeframe models, and bridge exceptions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, replace
from enum import StrEnum
from typing import Any

from app.services.brokers.base import BridgeError
from app.services.libs.contracts import SymbolInfo

__all__ = [
    "MAX_POSITION",
    "MAX_RECORDS",
    "MAX_UNDERLYING_DISPLAY_LEN",
    "READ_TIMEOUT",
    "TIMEFRAME_SECONDS",
    "TRUNCATE_LEN",
    "BridgeError",
    "ChartDef",
    "DataInfo",
    "InstrumentAliasRecord",
    "InstrumentInfo",
    "MarketBar",
    "MarketTick",
    "Timeframe",
    "format_dataset_table",
    "format_home_dashboard",
]

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
        """Parse timeframe from common string representations."""
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


@dataclass
class ChartDef:
    """Market data request specification and resample compatibility abstraction."""

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
        """Evaluate if this chart can be resampled/computed from another chart."""
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


@dataclass
class DataInfo:
    """Historical market dataset catalog metadata record."""

    id: str | int = 0
    symbol: str = ""
    timeframe: str | Timeframe = "M1"
    instrument: str = "Forex"
    connection: str = ""
    timezone: str = "UTC"
    decimals: int = 4
    date_from: str | int = 0
    date_from_str: str = ""
    date_to: str | int = 0
    date_to_str: str = ""
    rows: int = 0
    total_days: int = 0
    filename: str = ""
    file_hash: int = 0
    bar_time_type: int = 0
    remove_weekends: bool = True
    show: bool = True
    source: str | int = 0
    source_data_id: int = 0
    basket_id: int = 0
    broker_id: int = 0
    original_symbol: str = ""
    seconds_records: int = 0
    u_symbol: str = ""
    u_symbol_name: str = ""
    underlying: str = ""
    broker: str = "Default"
    broker_name: str = "Default"
    category: str = "Forex"
    bars: int = 0
    bar_type: str = "start"
    updated_at_utc: str = ""
    path: str = ""
    data_kind: str = "bars"
    quality_score: float = 1.0
    total_records: int = 0
    data_type: str = ""

    def __post_init__(self) -> None:
        """Harmonize aliases, default fields, and normalized types."""
        if isinstance(self.timeframe, Timeframe):
            self.timeframe = self.timeframe.value
        self._sync_paths_and_counts()
        self._sync_dates()
        self._sync_identifiers()

    def _sync_paths_and_counts(self) -> None:
        """Synchronize file paths and row counts."""
        if not self.path and self.filename:
            self.path = self.filename
        elif not self.filename and self.path:
            self.filename = self.path
        if not self.bars and self.rows:
            self.bars = self.rows
        elif not self.rows and self.bars:
            self.rows = self.bars
        if not self.total_records and (self.bars or self.rows):
            self.total_records = self.bars or self.rows
        elif not self.bars and self.total_records:
            self.bars = self.total_records
            self.rows = self.total_records

    def _sync_dates(self) -> None:
        """Synchronize start and end dates."""
        if not self.date_from_str and isinstance(self.date_from, str):
            self.date_from_str = self.date_from
        elif not self.date_from and self.date_from_str:
            self.date_from = self.date_from_str
        if not self.date_to_str and isinstance(self.date_to, str):
            self.date_to_str = self.date_to
        elif not self.date_to and self.date_to_str:
            self.date_to = self.date_to_str

    def _sync_identifiers(self) -> None:
        """Synchronize source, broker, and underlying symbol identifiers."""
        if not self.connection and isinstance(self.source, str) and self.source:
            self.connection = self.source
        elif (self.source == 0 or not self.source) and self.connection:
            self.source = self.connection
        if not self.underlying and self.symbol:
            self.underlying = self.symbol
        if not self.broker_name and self.broker:
            self.broker_name = self.broker
        elif not self.broker and self.broker_name:
            self.broker = self.broker_name
        if self.data_type and (not self.category or self.category == "Forex"):
            self.category = self.data_type
        elif self.category and not self.data_type:
            self.data_type = self.category

    def clone(self) -> DataInfo:
        """Clone this DataInfo record."""
        return replace(self)

    def to_chart_def(self) -> ChartDef:
        """Convert catalog metadata record into an operational ChartDef."""
        h_from = self.date_from if isinstance(self.date_from, int) else 0
        h_to = self.date_to if isinstance(self.date_to, int) else 0
        conn_name = str(self.connection or self.source or "")
        return ChartDef(
            symbol=self.symbol,
            timeframe=str(self.timeframe),
            instrument=self.instrument,
            connection_name=conn_name,
            history_from=h_from,
            history_to=h_to,
            bar_time_type=self.bar_time_type,
        )

    def to_data_info(self) -> DataInfo:
        """Self-identity adapter for backwards-compatible call sites."""
        return self

    def to_dict(self) -> dict[str, Any]:
        """Serialize DataInfo to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DataInfo:
        """Construct DataInfo from a dictionary."""
        valid_keys = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> DataInfo:
        """Construct DataInfo from database row or mapping."""
        d_from = str(row.get("date_from", ""))
        d_to = str(row.get("date_to", ""))
        bar_count = int(row.get("bars", 0))
        f_path = str(row.get("path", ""))
        src = str(row.get("source", "file"))
        cat = str(row.get("category", "Forex"))
        return cls(
            id=str(row.get("id", "")),
            source=src,
            symbol=str(row.get("symbol", "")),
            underlying=str(row.get("underlying", "")),
            instrument=str(row.get("instrument", "")),
            timeframe=str(row.get("timeframe", "M1")),
            broker=str(row.get("broker", "Default")),
            broker_name=str(row.get("broker_name", "Default")),
            timezone=str(row.get("timezone", "UTC")),
            category=cat,
            date_from=d_from,
            date_to=d_to,
            date_from_str=d_from,
            date_to_str=d_to,
            bars=bar_count,
            rows=bar_count,
            total_records=bar_count,
            data_type=cat,
            bar_type=str(row.get("bar_type", "start")),
            updated_at_utc=str(row.get("updated_at", row.get("updated_at_utc", ""))),
            path=f_path,
            filename=f_path,
            data_kind=str(row.get("data_kind", "bars")),
            quality_score=float(row.get("quality_score", 1.0)),
            connection=src,
        )


@dataclass
class InstrumentInfo:
    """Represents a financial instrument's specification and trading costs."""

    id: int | None = None
    symbol: str = ""
    connection: str = ""
    broker_id: int = 0
    description: str = ""
    tick_size: float = 0.00001
    tick_step: float = 0.00001
    tick_value_in_money: float = 10.0
    point_value: float = 100000.0
    decimals: int = 5
    default_spread: float = 0.0001
    default_slippage: float = 0.0
    min_volume: float = 0.01
    max_volume: float = 100.0
    lot_step: float = 0.01
    margin_rate: float = 0.05
    swap_long: float = 0.0
    swap_short: float = 0.0
    swap_3day_day: int = 3
    commissions: str = "0.0"
    data_type: str = "Forex"
    alias: str = ""
    exchange: str = ""
    country: str = ""
    sector: str = ""
    min_distance: float = 0.0
    order_size_multiplier: float = 1.0
    order_size_step: float = 0.0
    cot: str | None = None
    created_at_utc: str = ""
    updated_at_utc: str = ""

    def round_to_tick_size(self, price: float) -> float:
        """Round a price to the instrument's minimum tick size."""
        step = self.tick_size if self.tick_size > 0.0 else 0.0001
        return round(round(price / step) * step, self.decimals)

    def to_symbol_info(self) -> SymbolInfo:
        """Convert specification to the Tier 2 SymbolInfo domain model."""
        return SymbolInfo(
            name=self.symbol,
            digits=self.decimals,
            point=self.tick_size,
            trade_tick_size=self.tick_size,
            trade_tick_value=self.tick_value_in_money,
            trade_contract_size=self.point_value,
            volume_min=self.min_volume,
            volume_max=self.max_volume,
            volume_step=self.lot_step,
            margin_initial=self.margin_rate,
            swap_long=self.swap_long,
            swap_short=self.swap_short,
            swap_rollover3days=self.swap_3day_day,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert specification to dictionary representation."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "connection": self.connection,
            "broker_id": self.broker_id,
            "description": self.description,
            "tick_size": self.tick_size,
            "tick_step": self.tick_step,
            "tick_value_in_money": self.tick_value_in_money,
            "point_value": self.point_value,
            "decimals": self.decimals,
            "default_spread": self.default_spread,
            "default_slippage": self.default_slippage,
            "min_volume": self.min_volume,
            "max_volume": self.max_volume,
            "lot_step": self.lot_step,
            "margin_rate": self.margin_rate,
            "swap_long": self.swap_long,
            "swap_short": self.swap_short,
            "swap_3day_day": self.swap_3day_day,
            "commissions": self.commissions,
            "data_type": self.data_type,
            "alias": self.alias,
            "exchange": self.exchange,
            "country": self.country,
            "sector": self.sector,
            "min_distance": self.min_distance,
            "order_size_multiplier": self.order_size_multiplier,
            "order_size_step": self.order_size_step,
            "cot": self.cot,
            "created_at_utc": self.created_at_utc,
            "updated_at_utc": self.updated_at_utc,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> InstrumentInfo:
        """Construct InstrumentInfo from row or dictionary data."""
        return cls(
            id=data.get("id"),
            symbol=str(data.get("symbol", "")),
            connection=str(data.get("connection", "")),
            broker_id=int(data.get("broker_id", -1)),
            description=str(data.get("description", "")),
            tick_size=float(data.get("tick_size", 0.0001)),
            tick_step=float(data.get("tick_step", 0.00001)),
            tick_value_in_money=float(data.get("tick_value_in_money", 10.0)),
            point_value=float(data.get("point_value", 100000.0)),
            decimals=int(data.get("decimals", 5)),
            default_spread=float(data.get("default_spread", 1.0)),
            default_slippage=float(data.get("default_slippage", 0.0)),
            min_volume=float(data.get("min_volume", 0.01)),
            max_volume=float(data.get("max_volume", 100.0)),
            lot_step=float(data.get("lot_step", 0.01)),
            margin_rate=float(data.get("margin_rate", 0.05)),
            swap_long=float(data.get("swap_long", 0.0)),
            swap_short=float(data.get("swap_short", 0.0)),
            swap_3day_day=int(data.get("swap_3day_day", 3)),
            commissions=str(data.get("commissions", "0.0")),
            data_type=str(data.get("data_type", "Forex")),
            alias=str(data.get("alias", "")),
            exchange=str(data.get("exchange", "")),
            country=str(data.get("country", "")),
            sector=str(data.get("sector", "")),
            min_distance=float(data.get("min_distance", 0.0)),
            order_size_multiplier=float(data.get("order_size_multiplier", 1.0)),
            order_size_step=float(data.get("order_size_step", 0.01)),
            cot=str(data["cot"]) if data.get("cot") is not None else None,
            created_at_utc=str(data.get("created_at_utc", "")),
            updated_at_utc=str(data.get("updated_at_utc", "")),
        )


@dataclass(frozen=True)
class InstrumentAliasRecord:
    """Represents a symbol alias mapping."""

    alias: str
    instrument: str
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert alias record to dictionary representation."""
        return {
            "alias": self.alias,
            "instrument": self.instrument,
            "description": self.description,
        }


MAX_UNDERLYING_DISPLAY_LEN: int = 32
TRUNCATE_LEN: int = 30


def format_dataset_table(saved_datasets: Sequence[DataInfo]) -> str:
    """Format ASCII table of saved dataset catalog entries."""
    count = len(saved_datasets)
    lines: list[str] = [f"=== Saved Datasets Catalog ({count} items) ==="]
    header_fmt = (
        "| {sym:<14} | {inst:<15} | {brk:<12} | {und:<32} | {tf:<4} "
        "| {tz:<8} | {d_from:<10} | {d_to:<10} | {days:>6} | {recs:>10} "
        "| {src:<16} | {cat:<8} |"
    )
    divider = (
        "|-"
        + "-|-".join(
            [
                "-" * 14,
                "-" * 15,
                "-" * 12,
                "-" * 32,
                "-" * 4,
                "-" * 8,
                "-" * 10,
                "-" * 10,
                "-" * 6,
                "-" * 10,
                "-" * 16,
                "-" * 8,
            ]
        )
        + "-|"
    )
    lines.append(
        header_fmt.format(
            sym="Symbol Name",
            inst="Instrument",
            brk="Broker profile",
            und="Underlying Symbol",
            tf="TF",
            tz="Timezone",
            d_from="Date from",
            d_to="Date to",
            days="Days",
            recs="Records",
            src="Source",
            cat="Data type",
        )
    )
    lines.append(divider)
    for ds in saved_datasets:
        if len(ds.underlying) > MAX_UNDERLYING_DISPLAY_LEN:
            und_preview = ds.underlying[:TRUNCATE_LEN] + ".."
        else:
            und_preview = ds.underlying
        lines.append(
            header_fmt.format(
                sym=ds.symbol,
                inst=ds.instrument,
                brk=ds.broker,
                und=und_preview,
                tf=str(ds.timeframe),
                tz=ds.timezone,
                d_from=str(ds.date_from) or "-",
                d_to=str(ds.date_to) or "-",
                days=ds.total_days,
                recs=f"{ds.total_records:,}",
                src=str(ds.source),
                cat=ds.data_type,
            )
        )
    return "\n".join(lines)


def format_home_dashboard(
    overview: Mapping[str, Any] | Any,
    saved_datasets: Sequence[DataInfo],
) -> str:
    """Format complete human-readable dashboard output."""
    if isinstance(overview, Mapping):
        ds_count = overview.get("datasets_count", 0)
        total_bars = int(overview.get("total_bars", 0))
        inst_count = overview.get("instruments_count", 0)
        sess_count = overview.get("sessions_count", 0)
        bask_count = overview.get("baskets_count", 0)
        act_prov = overview.get("active_providers_count", 0)
    else:
        ds_count = getattr(overview, "datasets_count", 0)
        total_bars = int(getattr(overview, "total_bars", 0))
        inst_count = getattr(overview, "instruments_count", 0)
        sess_count = getattr(overview, "sessions_count", 0)
        bask_count = getattr(overview, "baskets_count", 0)
        act_prov = getattr(overview, "active_providers_count", 0)

    lines = [
        "=== Data Manager Home: Live Database Overview ===",
        f"Total Datasets:       {ds_count}",
        f"Historical Bars:      {total_bars:,}",
        f"Instruments Catalog:  {inst_count}",
        f"Trading Sessions:     {sess_count}",
        f"Custom Baskets:       {bask_count}",
        f"Active Providers:     {act_prov}",
        "",
        format_dataset_table(saved_datasets),
    ]
    return "\n".join(lines)
