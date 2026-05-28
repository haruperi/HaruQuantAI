"""Synthetic and transformed market-data generation tools for HaruQuantAI.

Purpose:
    Provide deterministic, testable helpers for generating synthetic OHLCV
    candles and standardized tick streams used in research, backtesting, and
    agent workflows.

Exported AI Tools:
    - gbm_data_generate: Generate synthetic OHLCV candles using geometric
      Brownian motion.
    - data_generate_ticks: Generate standardized ticks from OHLCV bars using a
      selected tick model.

Support Classes:
    - TimeframeManager: Resample OHLCV data between supported timeframes.
    - BarAggregator: Incrementally aggregate ticks/bars into larger bars.
    - TicksGenerator: Internal tick-generation engine used by the public tool.

Side Effects:
    These tools are read-only, deterministic when a seed is supplied, do not
    require network access, do not write files, do not modify databases, and do
    not place trades.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union, cast

import numpy as np
import pandas as pd

from tools.utils import logger

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "data"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False

GBM_TOOL_NAME = "gbm_data_generate"
TICKS_TOOL_NAME = "data_generate_ticks"

VALID_SPREAD_MODELS = {"native_spread", "fixed_spread", "variable_spread"}
REQUIRED_OHLC_COLUMNS = ("open", "high", "low", "close")
DEFAULT_MAX_OUTPUT_ROWS = 1_000_000


class GeneratorValidationError(ValueError):
    """Raised when deterministic validation fails inside generator helpers."""


@dataclass(frozen=True)
class ToolSpec:
    """Metadata describing a HaruQuantAI tool response."""

    tool_name: str
    tool_version: str = TOOL_VERSION
    tool_category: str = TOOL_CATEGORY
    tool_risk_level: str = TOOL_RISK_LEVEL
    requires_approval: bool = REQUIRES_APPROVAL
    read_only: bool = READ_ONLY
    writes_file: bool = WRITES_FILE
    modifies_database: bool = MODIFIES_DATABASE
    places_trade: bool = PLACES_TRADE
    requires_network: bool = REQUIRES_NETWORK


def _execution_ms(started_at: float) -> float:
    """Return elapsed execution time in milliseconds."""
    return round((time.perf_counter() - started_at) * 1000, 3)


def _tool_response(
    *,
    spec: ToolSpec,
    started_at: float,
    request_id: Optional[str],
    status: str,
    message: str,
    data: Any = None,
    error_code: Optional[str] = None,
    error_details: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a standard HaruQuantAI tool response."""
    error = None
    if status == "error":
        error = {
            "code": error_code or "TOOL_EXECUTION_FAILED",
            "details": error_details or message,
        }

    return {
        "status": status,
        "message": message,
        "data": data,
        "error": error,
        "metadata": {
            "tool_name": spec.tool_name,
            "tool_version": spec.tool_version,
            "tool_category": spec.tool_category,
            "tool_risk_level": spec.tool_risk_level,
            "request_id": request_id,
            "execution_ms": _execution_ms(started_at),
            "read_only": spec.read_only,
            "writes_file": spec.writes_file,
            "modifies_database": spec.modifies_database,
            "places_trade": spec.places_trade,
            "requires_network": spec.requires_network,
            "requires_approval": spec.requires_approval,
        },
    }


def _success(
    *,
    tool_name: str,
    started_at: float,
    request_id: Optional[str],
    message: str,
    data: Any,
) -> Dict[str, Any]:
    """Build a standard success response."""
    return _tool_response(
        spec=ToolSpec(tool_name=tool_name),
        started_at=started_at,
        request_id=request_id,
        status="success",
        message=message,
        data=data,
    )


def _error(
    *,
    tool_name: str,
    started_at: float,
    request_id: Optional[str],
    code: str,
    message: str,
    details: str,
) -> Dict[str, Any]:
    """Build a standard error response."""
    return _tool_response(
        spec=ToolSpec(tool_name=tool_name),
        started_at=started_at,
        request_id=request_id,
        status="error",
        message=message,
        data=None,
        error_code=code,
        error_details=details,
    )


def _serialize_frame_records(frame: pd.DataFrame) -> List[Dict[str, Any]]:
    """Serialize a DataFrame into JSON-safe row dictionaries."""
    if frame is None or not isinstance(frame, pd.DataFrame):
        raise GeneratorValidationError("frame must be a pandas DataFrame.")

    out = frame.copy()
    if isinstance(out.index, pd.DatetimeIndex):
        out = out.reset_index()
        index_name = out.columns[0]
        if str(index_name).lower() not in {"timestamp", "datetime", "time", "index"}:
            out = out.rename(columns={index_name: "timestamp"})
        else:
            out = out.rename(columns={index_name: str(index_name).lower()})

    for column in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[column]):
            out[column] = pd.to_datetime(out[column]).dt.strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            )

    out = out.replace({np.nan: None, np.inf: None, -np.inf: None})
    return cast(List[Dict[str, Any]], out.to_dict(orient="records"))


def _normalize_ohlcv_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with standard lowercase OHLCV/timestamp columns."""
    if not isinstance(frame, pd.DataFrame):
        raise GeneratorValidationError("market data must be a pandas DataFrame.")

    renamed = frame.copy()
    column_map: Dict[str, str] = {}
    for column in renamed.columns:
        clean = str(column).strip().lower()
        if clean in {"datetime", "date", "time"}:
            column_map[column] = "timestamp"
        elif clean in {"open", "high", "low", "close", "volume", "spread"}:
            column_map[column] = clean
        elif clean in {
            "entry_signal",
            "exit_signal",
            "pending_signal",
            "cancel_pending_signal",
            "pending_signal_2",
            "cancel_pending_signal_2",
            "price",
            "price_2",
            "sl",
            "tp",
        }:
            column_map[column] = clean
    if column_map:
        renamed = renamed.rename(columns=column_map)

    return renamed


def _ensure_datetime_index(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of frame indexed by a DatetimeIndex."""
    if not isinstance(frame, pd.DataFrame):
        raise GeneratorValidationError("data must be a pandas DataFrame.")
    if isinstance(frame.index, pd.DatetimeIndex):
        return frame.copy()

    normalized = _normalize_ohlcv_columns(frame)
    if "timestamp" not in normalized.columns:
        raise GeneratorValidationError(
            "DataFrame must have a DatetimeIndex or a timestamp/datetime/time column."
        )
    normalized = normalized.copy()
    normalized["timestamp"] = pd.to_datetime(normalized["timestamp"], errors="raise")
    normalized = normalized.set_index("timestamp")
    normalized.index = pd.DatetimeIndex(normalized.index, name="timestamp")
    return normalized


def _validate_required_ohlc(frame: pd.DataFrame, *, context: str) -> None:
    """Validate that frame contains required OHLC columns."""
    normalized = _normalize_ohlcv_columns(frame)
    missing = [col for col in REQUIRED_OHLC_COLUMNS if col not in normalized.columns]
    if missing:
        raise GeneratorValidationError(
            f"{context} requires OHLC columns: open, high, low, close. "
            f"Missing: {', '.join(missing)}."
        )


def _validate_symbols(symbols: Union[str, Sequence[str]]) -> List[str]:
    """Validate and normalize one or more symbols."""
    if isinstance(symbols, str):
        cleaned = symbols.strip().upper()
        if not cleaned:
            raise GeneratorValidationError("symbols must contain at least one symbol.")
        return [cleaned]

    if not isinstance(symbols, Sequence):
        raise GeneratorValidationError(
            "symbols must be a string or a sequence of strings."
        )

    normalized: List[str] = []
    for symbol in symbols:
        if not isinstance(symbol, str) or not symbol.strip():
            raise GeneratorValidationError("all symbols must be non-empty strings.")
        normalized.append(symbol.strip().upper())

    if not normalized:
        raise GeneratorValidationError("symbols must contain at least one symbol.")
    return normalized


def _validate_numeric(value: Any, name: str) -> float:
    """Validate a finite numeric value and return it as float."""
    if isinstance(value, bool) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise GeneratorValidationError(f"{name} must be numeric.")
    result = float(value)
    if not np.isfinite(result):
        raise GeneratorValidationError(f"{name} must be finite.")
    return result


def _validate_optional_positive_int(value: Any, name: str) -> Optional[int]:
    """Validate an optional positive integer."""
    if value is None:
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, np.integer))
        or int(value) <= 0
    ):
        raise GeneratorValidationError(
            f"{name} must be a positive integer when provided."
        )
    return int(value)


def _parse_datetime(value: Union[str, datetime], name: str) -> pd.Timestamp:
    """Parse a date-like input into a pandas Timestamp."""
    try:
        parsed = pd.Timestamp(value)
    except Exception as exc:
        raise GeneratorValidationError(
            f"{name} must be a valid date or datetime."
        ) from exc
    if pd.isna(parsed):
        raise GeneratorValidationError(f"{name} must be a valid date or datetime.")
    return parsed


def _validate_date_range(
    start: Union[str, datetime],
    end: Optional[Union[str, datetime]],
    *,
    count: Optional[int],
) -> tuple[pd.Timestamp, Optional[pd.Timestamp]]:
    """Validate date inputs for generated time indexes."""
    start_ts = _parse_datetime(start, "start")
    end_ts: Optional[pd.Timestamp] = None
    if count is None:
        if end is None:
            raise GeneratorValidationError(
                "end is required when count is not provided."
            )
        end_ts = _parse_datetime(end, "end")
        if start_ts > end_ts:
            raise GeneratorValidationError(
                "start must be earlier than or equal to end."
            )
    return start_ts, end_ts


def _validate_timeframe_interval(interval: Any) -> str:
    """Validate and map a timeframe interval to a pandas frequency."""
    if not isinstance(interval, str) or not interval.strip():
        raise GeneratorValidationError("interval must be a non-empty string.")
    try:
        return TimeframeManager.timeframe_to_frequency(interval)
    except ValueError as exc:
        raise GeneratorValidationError(str(exc)) from exc


def _validate_dataframe_not_empty(value: Any, name: str) -> pd.DataFrame:
    """Validate a non-empty pandas DataFrame."""
    if value is None or not isinstance(value, pd.DataFrame):
        raise GeneratorValidationError(f"{name} must be a pandas DataFrame.")
    if value.empty:
        raise GeneratorValidationError(f"{name} must not be empty.")
    return value


def _validate_max_output_rows(value: Any) -> int:
    """Validate max_output_rows guardrail."""
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, np.integer))
        or int(value) <= 0
    ):
        raise GeneratorValidationError("max_output_rows must be a positive integer.")
    return int(value)


class TimeframeManager:
    """Manager for OHLCV resampling and timeframe conversions."""

    TIMEFRAME_MAP: Dict[str, str] = {
        "M1": "1min",
        "M5": "5min",
        "M15": "15min",
        "M30": "30min",
        "H1": "1h",
        "H4": "4h",
        "D1": "1D",
        "W1": "1W",
        "MN1": "1ME",
        "1M": "1min",
        "1MIN": "1min",
        "5MIN": "5min",
        "15MIN": "15min",
        "30MIN": "30min",
        "1H": "1h",
        "4H": "4h",
        "1D": "1D",
    }

    VALID_TIMEFRAMES: List[str] = [
        "M1",
        "M5",
        "M15",
        "M30",
        "H1",
        "H4",
        "D1",
        "W1",
        "MN1",
    ]

    def __init__(self) -> None:
        """Initialize the timeframe manager."""
        logger.debug("TimeframeManager initialized")

    @classmethod
    def timeframe_to_frequency(cls, timeframe: str) -> str:
        """Convert a HaruQuant timeframe string to a pandas frequency string."""
        if not isinstance(timeframe, str) or not timeframe.strip():
            raise ValueError("timeframe must be a non-empty string.")
        key = timeframe.strip().upper()
        if key not in cls.TIMEFRAME_MAP:
            supported = ", ".join(cls.VALID_TIMEFRAMES)
            raise ValueError(
                f"Unsupported timeframe: {timeframe}. Supported: {supported}."
            )
        return cls.TIMEFRAME_MAP[key]

    @classmethod
    def validate_timeframe(cls, timeframe: str) -> bool:
        """Return True when the timeframe is supported."""
        return (
            isinstance(timeframe, str)
            and timeframe.strip().upper() in cls.TIMEFRAME_MAP
        )

    @classmethod
    def can_resample(cls, from_timeframe: str, to_timeframe: str) -> bool:
        """Return whether source timeframe can be resampled to target timeframe."""
        try:
            from_idx = cls.VALID_TIMEFRAMES.index(from_timeframe.strip().upper())
            to_idx = cls.VALID_TIMEFRAMES.index(to_timeframe.strip().upper())
        except (AttributeError, ValueError):
            return False
        return to_idx > from_idx

    @staticmethod
    def _find_ohlcv_columns(frame: pd.DataFrame) -> Dict[str, str]:
        """Find OHLCV columns case-insensitively."""
        lower = {str(col).strip().lower(): str(col) for col in frame.columns}
        mapping: Dict[str, str] = {}
        for standard in ("open", "high", "low", "close", "volume", "spread"):
            if standard in lower:
                mapping[standard] = lower[standard]
        return mapping

    def resample(
        self,
        data: pd.DataFrame,
        target_timeframe: str,
        source_timeframe: Optional[str] = None,
    ) -> pd.DataFrame:
        """Resample OHLCV data to a larger target timeframe.

        Args:
            data: Source OHLCV data with a DatetimeIndex or timestamp column.
            target_timeframe: Target timeframe, for example ``M5`` or ``H1``.
            source_timeframe: Optional source timeframe used to prevent invalid
                downsampling direction.

        Returns:
            DataFrame with lowercase OHLCV columns and DatetimeIndex.

        Raises:
            ValueError: If timeframe or OHLCV schema is invalid.
        """
        if not isinstance(data, pd.DataFrame):
            raise ValueError("data must be a pandas DataFrame.")
        if data.empty:
            logger.warning("Cannot resample empty DataFrame")
            return data.copy()
        if source_timeframe and not self.can_resample(
            source_timeframe, target_timeframe
        ):
            raise ValueError(
                f"Cannot resample from {source_timeframe} to {target_timeframe}; "
                "target timeframe must be less granular."
            )

        frequency = self.timeframe_to_frequency(target_timeframe)
        frame = _normalize_ohlcv_columns(_ensure_datetime_index(data))
        mapping = self._find_ohlcv_columns(frame)
        missing = [column for column in REQUIRED_OHLC_COLUMNS if column not in mapping]
        if missing:
            raise ValueError(
                f"No complete OHLC columns found. Missing: {', '.join(missing)}."
            )

        aggregation: Dict[str, Any] = {
            mapping["open"]: "first",
            mapping["high"]: "max",
            mapping["low"]: "min",
            mapping["close"]: "last",
        }
        if "volume" in mapping:
            aggregation[mapping["volume"]] = "sum"
        if "spread" in mapping:
            aggregation[mapping["spread"]] = "last"

        other_columns = [
            column
            for column in frame.columns
            if column not in set(aggregation.keys())
            and str(column).lower() != "timestamp"
        ]
        for column in other_columns:
            aggregation[column] = "last"

        resampled = frame.resample(frequency).agg(aggregation)
        resampled = _normalize_ohlcv_columns(resampled)
        resampled = resampled.dropna(subset=list(REQUIRED_OHLC_COLUMNS), how="all")
        resampled.index = pd.DatetimeIndex(resampled.index, name="timestamp")

        logger.info(
            (
                "Resampled OHLCV data | source_rows=%s | "
                "target_timeframe=%s | output_rows=%s"
            ),
            len(frame),
            target_timeframe,
            len(resampled),
        )
        return resampled

    def resample_multi_timeframe(
        self,
        data: pd.DataFrame,
        source_timeframe: str,
        target_timeframes: Sequence[str],
    ) -> Dict[str, pd.DataFrame]:
        """Resample data into multiple target timeframes."""
        results: Dict[str, pd.DataFrame] = {}
        for target_timeframe in target_timeframes:
            try:
                results[str(target_timeframe).upper()] = self.resample(
                    data, str(target_timeframe), source_timeframe
                )
            except ValueError as exc:
                logger.warning(
                    "Failed to resample to %s | error=%s", target_timeframe, exc
                )
        return results


class BarAggregator:
    """Incrementally aggregate ticks or smaller bars into larger OHLCV bars."""

    def __init__(self, target_timeframe: str) -> None:
        """Initialize the aggregator for a supported target timeframe."""
        self.target_timeframe = target_timeframe.upper()
        self.target_frequency = TimeframeManager.timeframe_to_frequency(
            target_timeframe
        )
        self.current_bar: Optional[Dict[str, float]] = None
        self.current_bar_start: Optional[datetime] = None
        self.completed_bars: List[Dict[str, Any]] = []
        logger.debug(
            "BarAggregator initialized | target_timeframe=%s", target_timeframe
        )

    def add_tick(
        self,
        timestamp: datetime,
        price: float,
        volume: float = 0.0,
        bid: Optional[float] = None,
        ask: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """Add one tick and return a completed bar when the period changes."""
        if not isinstance(timestamp, datetime):
            raise ValueError("timestamp must be a datetime instance.")
        if bid is not None and ask is not None:
            price = (float(bid) + float(ask)) / 2.0
        price = _validate_numeric(price, "price")
        volume = _validate_numeric(volume, "volume")

        bar_start = self._get_bar_start_time(timestamp)
        completed_bar = None
        if self.current_bar_start is not None and bar_start != self.current_bar_start:
            completed_bar = self._finalize_current_bar()
            self.completed_bars.append(completed_bar)

        if bar_start != self.current_bar_start:
            self.current_bar_start = bar_start
            self.current_bar = {
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": volume,
            }
        elif self.current_bar is not None:
            self.current_bar["high"] = max(self.current_bar["high"], price)
            self.current_bar["low"] = min(self.current_bar["low"], price)
            self.current_bar["close"] = price
            self.current_bar["volume"] += volume

        return completed_bar

    def add_bar(
        self,
        timestamp: datetime,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: float = 0.0,
    ) -> Optional[Dict[str, Any]]:
        """Add one smaller bar and return a completed bar when the period changes."""
        if not isinstance(timestamp, datetime):
            raise ValueError("timestamp must be a datetime instance.")
        open_price = _validate_numeric(open_price, "open_price")
        high_price = _validate_numeric(high_price, "high_price")
        low_price = _validate_numeric(low_price, "low_price")
        close_price = _validate_numeric(close_price, "close_price")
        volume = _validate_numeric(volume, "volume")

        bar_start = self._get_bar_start_time(timestamp)
        completed_bar = None
        if self.current_bar_start is not None and bar_start != self.current_bar_start:
            completed_bar = self._finalize_current_bar()
            self.completed_bars.append(completed_bar)

        if bar_start != self.current_bar_start:
            self.current_bar_start = bar_start
            self.current_bar = {
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume,
            }
        elif self.current_bar is not None:
            self.current_bar["high"] = max(self.current_bar["high"], high_price)
            self.current_bar["low"] = min(self.current_bar["low"], low_price)
            self.current_bar["close"] = close_price
            self.current_bar["volume"] += volume

        return completed_bar

    def _get_bar_start_time(self, timestamp: datetime) -> datetime:
        """Return the normalized period start for a timestamp."""
        period = pd.Period(pd.Timestamp(timestamp), freq=self.target_frequency)
        return cast(datetime, period.start_time.to_pydatetime())

    def _finalize_current_bar(self) -> Dict[str, Any]:
        """Return the current bar with timestamp included."""
        if self.current_bar is None or self.current_bar_start is None:
            raise ValueError("No current bar to finalize.")
        bar: Dict[str, Any] = dict(self.current_bar)
        bar["timestamp"] = self.current_bar_start
        return bar

    def get_current_bar(self) -> Optional[Dict[str, Any]]:
        """Return the current incomplete bar, if one exists."""
        if self.current_bar is None or self.current_bar_start is None:
            return None
        bar: Dict[str, Any] = dict(self.current_bar)
        bar["timestamp"] = self.current_bar_start
        return bar

    def get_completed_bars(self) -> List[Dict[str, Any]]:
        """Return completed bars without exposing internal list state."""
        return list(self.completed_bars)

    def flush(self) -> Optional[Dict[str, Any]]:
        """Finalize and clear the current incomplete bar."""
        if self.current_bar is None or self.current_bar_start is None:
            return None
        completed_bar = self._finalize_current_bar()
        self.completed_bars.append(completed_bar)
        self.current_bar = None
        self.current_bar_start = None
        return completed_bar


class TicksGenerator:
    """Generate standardized tick DataFrames from OHLCV bars or tick sources."""

    SUPPORTED_MODELS = {"timeframe_ticks", "m1_ticks", "real_ticks", "synthetic_ticks"}
    SIGNAL_COLUMNS = (
        "entry_signal",
        "exit_signal",
        "pending_signal",
        "cancel_pending_signal",
        "pending_signal_2",
        "cancel_pending_signal_2",
        "price",
        "price_2",
        "sl",
        "tp",
    )

    def __init__(
        self,
        model: str,
        trading_timeframe: str,
        m1_data: Optional[pd.DataFrame] = None,
        real_ticks: Optional[pd.DataFrame] = None,
        point_value: float = 0.00001,
        spread_model: str = "native_spread",
        fixed_spread_points: Optional[float] = None,
        min_spread_points: Optional[float] = None,
        max_spread_points: Optional[float] = None,
        random_seed: Optional[int] = None,
    ) -> None:
        """Initialize the tick generator configuration."""
        if not isinstance(model, str) or model.lower() not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported ticks model: {model}. "
                f"Supported: {sorted(self.SUPPORTED_MODELS)}."
            )
        if not TimeframeManager.validate_timeframe(trading_timeframe):
            raise ValueError(f"Unsupported trading_timeframe: {trading_timeframe}.")
        if (
            not isinstance(spread_model, str)
            or spread_model.lower() not in VALID_SPREAD_MODELS
        ):
            raise ValueError(
                f"Unsupported spread_model: {spread_model}. "
                f"Supported: {sorted(VALID_SPREAD_MODELS)}."
            )

        point = _validate_numeric(point_value, "point_value")
        if point <= 0:
            raise ValueError("point_value must be > 0.")

        self.model = model.lower()
        self.trading_timeframe = trading_timeframe.upper()
        self.m1_data = m1_data
        self.real_ticks = real_ticks
        self.point_value = point
        self.spread_model = spread_model.lower()
        self.fixed_spread_points = fixed_spread_points
        self.min_spread_points = min_spread_points
        self.max_spread_points = max_spread_points
        self._rng = np.random.default_rng(random_seed)

        self._validate_spread_settings()

    def _validate_spread_settings(self) -> None:
        """Validate spread model-specific settings."""
        if self.spread_model == "fixed_spread":
            if self.fixed_spread_points is None:
                raise ValueError("fixed_spread_points is required for fixed_spread.")
            if _validate_numeric(self.fixed_spread_points, "fixed_spread_points") < 0:
                raise ValueError("fixed_spread_points must be >= 0.")
        if self.spread_model == "variable_spread":
            if self.min_spread_points is None or self.max_spread_points is None:
                raise ValueError(
                    "min_spread_points and max_spread_points are required "
                    "for variable_spread."
                )
            low = _validate_numeric(self.min_spread_points, "min_spread_points")
            high = _validate_numeric(self.max_spread_points, "max_spread_points")
            if low < 0 or high < 0:
                raise ValueError("variable spread bounds must be >= 0.")
            if low > high:
                raise ValueError(
                    "min_spread_points cannot be greater than max_spread_points."
                )

    def generate(self, trading_tf_data: pd.DataFrame) -> pd.DataFrame:
        """Generate standardized ticks from the configured model."""
        trading_tf_data = _validate_dataframe_not_empty(
            trading_tf_data, "trading_tf_data"
        )
        if self.model == "timeframe_ticks":
            return self._generate_timeframe_ticks(trading_tf_data)
        if self.model == "m1_ticks":
            return self._generate_m1_ticks(trading_tf_data)
        if self.model == "real_ticks":
            return self._generate_real_ticks(trading_tf_data)
        if self.model == "synthetic_ticks":
            return self._generate_synthetic_ticks(trading_tf_data)
        raise ValueError(f"Unsupported model: {self.model}.")

    @staticmethod
    def _find_col(frame: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
        """Find the first matching column name case-insensitively."""
        lower = {str(column).lower(): str(column) for column in frame.columns}
        for candidate in candidates:
            if candidate.lower() in lower:
                return lower[candidate.lower()]
        return None

    @staticmethod
    def _infer_bar_seconds(index: pd.DatetimeIndex, fallback: int = 60) -> int:
        """Infer median bar duration in seconds from a DatetimeIndex."""
        if len(index) > 1:
            deltas = index.to_series().diff().dropna()
            if not deltas.empty:
                return int(max(1, deltas.median().total_seconds()))
        return fallback

    @staticmethod
    def _ensure_signal_columns(frame: pd.DataFrame) -> pd.DataFrame:
        """Return a copy containing all supported signal columns."""
        out = frame.copy()
        for column in TicksGenerator.SIGNAL_COLUMNS:
            if column not in out.columns:
                out[column] = 0.0
        return out

    def _resolve_spread_points(self, native_spread_points: float) -> float:
        """Resolve spread points according to the configured spread model."""
        native = max(0.0, float(native_spread_points or 0.0))
        if self.spread_model == "native_spread":
            return native
        if self.spread_model == "fixed_spread":
            return max(0.0, float(self.fixed_spread_points or 0.0))
        low = float(self.min_spread_points or 0.0)
        high = float(self.max_spread_points or 0.0)
        return float(max(0.0, self._rng.uniform(low, high)))

    @staticmethod
    def _empty_ticks() -> pd.DataFrame:
        """Return an empty tick frame with the standard schema."""
        return pd.DataFrame(
            columns=[
                "bid",
                "ask",
                "last",
                "spread",
                "entry_signal",
                "exit_signal",
                "pending_signal",
                "cancel_pending_signal",
                "pending_signal_2",
                "cancel_pending_signal_2",
                "price",
                "price_2",
                "sl",
                "tp",
                "source_bar_time",
                "tick_index_in_bar",
                "is_bar_close",
            ]
        )

    def _generate_timeframe_ticks(self, bars: pd.DataFrame) -> pd.DataFrame:
        """Generate four synthetic ticks per OHLCV bar."""
        if bars.empty:
            return self._empty_ticks()
        frame = _normalize_ohlcv_columns(_ensure_datetime_index(bars))
        _validate_required_ohlc(frame, context="timeframe_ticks")
        frame = self._ensure_signal_columns(frame)

        rows: List[Dict[str, Any]] = []
        fallback_seconds = _timeframe_seconds(self.trading_timeframe)
        bar_seconds = self._infer_bar_seconds(
            cast(pd.DatetimeIndex, frame.index), fallback_seconds
        )
        offsets = [
            0,
            max(1, bar_seconds // 3),
            max(2, (2 * bar_seconds) // 3),
            max(3, bar_seconds) - 0.001,
        ]

        for timestamp, bar in frame.iterrows():
            open_px = float(bar["open"])
            high_px = float(bar["high"])
            low_px = float(bar["low"])
            close_px = float(bar["close"])
            native_spread = float(bar.get("spread", 0.0) or 0.0)
            path = (
                [open_px, low_px, high_px, close_px]
                if close_px >= open_px
                else [open_px, high_px, low_px, close_px]
            )
            phases = [
                "open",
                "low" if close_px >= open_px else "high",
                "high" if close_px >= open_px else "low",
                "close",
            ]
            for idx, price in enumerate(path):
                spread_points = self._resolve_spread_points(native_spread)
                rows.append(
                    self._tick_row(
                        timestamp=pd.Timestamp(timestamp)
                        + pd.to_timedelta(offsets[idx], unit="s"),
                        bid=float(price),
                        spread_points=spread_points,
                        source_bar_time=pd.Timestamp(timestamp),
                        tick_index=idx,
                        phase=phases[idx],
                        signal_bar=bar if idx == 0 else None,
                    )
                )
        return self._rows_to_ticks(rows)

    def _prepare_m1_with_signals(self, trading_tf_data: pd.DataFrame) -> pd.DataFrame:
        """Merge trading-timeframe signals onto M1 bars."""
        if self.m1_data is None or self.m1_data.empty:
            raise ValueError("m1_ticks/synthetic_ticks requires non-empty m1_data.")

        trading_tf = self._ensure_signal_columns(
            _normalize_ohlcv_columns(_ensure_datetime_index(trading_tf_data))
        )
        m1 = _normalize_ohlcv_columns(_ensure_datetime_index(self.m1_data))
        _validate_required_ohlc(m1, context="m1_data")

        tf_seconds = self._infer_bar_seconds(
            cast(pd.DatetimeIndex, trading_tf.index),
            _timeframe_seconds(self.trading_timeframe),
        )
        bucket_index = cast(pd.DatetimeIndex, m1.index).floor(f"{max(1, tf_seconds)}s")
        signals = trading_tf[list(self.SIGNAL_COLUMNS)].copy()
        signals.index = cast(pd.DatetimeIndex, signals.index).floor(
            f"{max(1, tf_seconds)}s"
        )
        mapped = signals.reindex(bucket_index).fillna(0.0)
        mapped.index = m1.index
        for column in self.SIGNAL_COLUMNS:
            m1[column] = mapped[column]
        logger.info("Mapped trading timeframe signals to M1 bars | rows=%s", len(m1))
        return m1

    def _generate_m1_ticks(self, trading_tf_data: pd.DataFrame) -> pd.DataFrame:
        """Generate four ticks per M1 bar after signal mapping."""
        return self._generate_timeframe_ticks(
            self._prepare_m1_with_signals(trading_tf_data)
        )

    def _generate_real_ticks(self, trading_tf_data: pd.DataFrame) -> pd.DataFrame:
        """Merge trading-timeframe signals into real tick data."""
        if self.real_ticks is None or self.real_ticks.empty:
            raise ValueError(
                "real_ticks model requires non-empty real_ticks DataFrame."
            )

        ticks = _ensure_datetime_index(self.real_ticks)
        tf = self._ensure_signal_columns(
            _normalize_ohlcv_columns(_ensure_datetime_index(trading_tf_data))
        )
        bid_col = self._find_col(ticks, ["bid"])
        ask_col = self._find_col(ticks, ["ask"])
        if bid_col is None or ask_col is None:
            raise ValueError("real_ticks DataFrame must contain bid and ask columns.")

        last_col = self._find_col(ticks, ["last"])
        spread_col = self._find_col(ticks, ["spread"])
        tf_seconds = self._infer_bar_seconds(
            cast(pd.DatetimeIndex, tf.index), _timeframe_seconds(self.trading_timeframe)
        )
        buckets = cast(pd.DatetimeIndex, ticks.index).floor(f"{max(1, tf_seconds)}s")
        first_in_bucket = ~pd.Index(buckets).duplicated()

        signals = tf[list(self.SIGNAL_COLUMNS)].copy()
        signals.index = cast(pd.DatetimeIndex, signals.index).floor(
            f"{max(1, tf_seconds)}s"
        )
        mapped = signals.reindex(buckets).fillna(0.0).reset_index(drop=True)

        out = pd.DataFrame(index=ticks.index)
        out["bid"] = pd.to_numeric(ticks[bid_col], errors="raise")
        out["ask"] = pd.to_numeric(ticks[ask_col], errors="raise")
        out["last"] = (
            pd.to_numeric(ticks[last_col], errors="raise") if last_col else out["bid"]
        )
        out["spread"] = (
            pd.to_numeric(ticks[spread_col], errors="raise")
            if spread_col
            else ((out["ask"] - out["bid"]) / self.point_value).round().clip(lower=0)
        )
        for column in self.SIGNAL_COLUMNS:
            values = mapped[column].to_numpy()
            out[column] = values
            out.loc[~first_in_bucket, column] = 0.0
        out["source_bar_time"] = buckets
        out["tick_index_in_bar"] = (
            pd.Series(buckets, index=out.index).groupby(buckets).cumcount()
        )
        out["is_bar_close"] = ""
        out.index = pd.DatetimeIndex(out.index, name="timestamp")
        return out.sort_index()

    def _generate_synthetic_ticks(self, trading_tf_data: pd.DataFrame) -> pd.DataFrame:
        """Generate volume-based synthetic tick paths from M1 bars."""
        m1 = self._prepare_m1_with_signals(trading_tf_data)
        _validate_required_ohlc(m1, context="synthetic_ticks")
        if "volume" not in m1.columns:
            raise ValueError("synthetic_ticks requires M1 volume column.")

        rows: List[Dict[str, Any]] = []
        for timestamp, bar in m1.iterrows():
            open_px = float(bar["open"])
            high_px = float(bar["high"])
            low_px = float(bar["low"])
            close_px = float(bar["close"])
            volume = int(max(4, round(float(bar["volume"]))))
            native_spread = float(bar.get("spread", 0.0) or 0.0)
            path = (
                [open_px, low_px, high_px, close_px]
                if close_px >= open_px
                else [open_px, high_px, low_px, close_px]
            )
            prices = _interpolate_path(path, volume)
            high_idx = int(np.argmax(prices))
            low_idx = int(np.argmin(prices))
            for idx, price in enumerate(prices):
                phase_parts: List[str] = []
                if idx == 0:
                    phase_parts.append("open")
                if idx == high_idx:
                    phase_parts.append("high")
                if idx == low_idx:
                    phase_parts.append("low")
                if idx == volume - 1:
                    phase_parts.append("close")
                offset_ms = int((60_000 * idx) / max(1, volume))
                rows.append(
                    self._tick_row(
                        timestamp=pd.Timestamp(timestamp)
                        + pd.to_timedelta(offset_ms, unit="ms"),
                        bid=float(price),
                        spread_points=self._resolve_spread_points(native_spread),
                        source_bar_time=pd.Timestamp(timestamp),
                        tick_index=idx,
                        phase="|".join(phase_parts),
                        signal_bar=bar if idx == 0 else None,
                    )
                )
        return self._rows_to_ticks(rows)

    def _tick_row(
        self,
        *,
        timestamp: pd.Timestamp,
        bid: float,
        spread_points: float,
        source_bar_time: pd.Timestamp,
        tick_index: int,
        phase: str,
        signal_bar: Optional[pd.Series],
    ) -> Dict[str, Any]:
        """Build one standardized tick row."""
        ask = bid + (max(0.0, spread_points) * self.point_value)
        row: Dict[str, Any] = {
            "timestamp": timestamp,
            "bid": bid,
            "ask": ask,
            "last": bid,
            "spread": int(round(max(0.0, spread_points))),
            "source_bar_time": source_bar_time,
            "tick_index_in_bar": tick_index,
            "is_bar_close": phase,
        }
        for column in self.SIGNAL_COLUMNS:
            row[column] = (
                float(signal_bar.get(column, 0.0) or 0.0)
                if signal_bar is not None
                else 0.0
            )
        return row

    @staticmethod
    def _rows_to_ticks(rows: List[Dict[str, Any]]) -> pd.DataFrame:
        """Convert tick rows into a sorted DataFrame."""
        if not rows:
            return TicksGenerator._empty_ticks()
        ticks = pd.DataFrame(rows).set_index("timestamp")
        ticks.index = pd.DatetimeIndex(ticks.index, name="timestamp")
        return ticks.sort_index()


def _interpolate_path(path: Sequence[float], n: int) -> List[float]:
    """Interpolate a price path into exactly n points."""
    if n <= 1:
        return [float(path[0])]
    if len(path) < 2:
        return [float(path[0])] * n
    x = np.linspace(0, len(path) - 1, num=n)
    xp = np.arange(len(path))
    return [
        float(value) for value in np.interp(x, xp, np.array(path, dtype=np.float64))
    ]


def _timeframe_seconds(timeframe: str) -> int:
    """Return approximate timeframe duration in seconds."""
    mapping = {
        "M1": 60,
        "M5": 300,
        "M15": 900,
        "M30": 1800,
        "H1": 3600,
        "H4": 14400,
        "D1": 86400,
        "W1": 604800,
        "MN1": 2_592_000,
    }
    return mapping.get(str(timeframe).upper(), 60)


def _validate_tick_output(frame: pd.DataFrame, max_output_rows: int) -> None:
    """Validate generated tick output before returning success."""
    if not isinstance(frame, pd.DataFrame):
        raise GeneratorValidationError("generated ticks must be a pandas DataFrame.")
    if len(frame) > max_output_rows:
        raise GeneratorValidationError(
            f"Generated tick rows ({len(frame)}) exceed "
            f"max_output_rows ({max_output_rows})."
        )
    required = {"bid", "ask", "last", "spread"}
    missing = required - set(str(column) for column in frame.columns)
    if missing:
        raise GeneratorValidationError(
            f"Generated ticks missing required columns: {sorted(missing)}."
        )


def gbm_data_generate(
    symbols: Union[str, List[str]],
    start: Union[str, datetime] = "2020-01-01",
    end: Optional[Union[str, datetime]] = "2021-01-01",
    interval: str = "1d",
    count: Optional[int] = None,
    mu: float = 0.0,
    sigma: float = 0.01,
    start_value: float = 100.0,
    seed: Optional[int] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate synthetic OHLCV candles with geometric Brownian motion.

    Use this read-only tool when an agent or workflow needs deterministic
    synthetic candles for tests, research experiments, examples, or pipeline
    validation without touching a broker or external data source.
    """
    tool_name = GBM_TOOL_NAME
    started_at = time.perf_counter()
    logger.info(
        "%s called | request_id=%s | symbols=%s", tool_name, request_id, symbols
    )

    try:
        normalized_symbols = _validate_symbols(symbols)
        count_value = _validate_optional_positive_int(count, "count")
        sigma_value = _validate_numeric(sigma, "sigma")
        mu_value = _validate_numeric(mu, "mu")
        start_price = _validate_numeric(start_value, "start_value")
        if sigma_value < 0:
            raise GeneratorValidationError("sigma must be non-negative.")
        if start_price <= 0:
            raise GeneratorValidationError("start_value must be positive.")
        if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)):
            raise GeneratorValidationError("seed must be an integer or None.")
        frequency = _validate_timeframe_interval(interval)
        start_ts, end_ts = _validate_date_range(start, end, count=count_value)

        date_index = (
            pd.date_range(start=start_ts, periods=count_value, freq=frequency)
            if count_value is not None
            else pd.date_range(start=start_ts, end=end_ts, freq=frequency)
        )
        if date_index.empty:
            raise GeneratorValidationError("date range produced no rows.")

        rng = np.random.default_rng(seed)
        frame = pd.DataFrame(index=pd.DatetimeIndex(date_index, name="timestamp"))

        if len(normalized_symbols) == 1:
            returns = rng.normal(mu_value, sigma_value, len(date_index))
            close = start_price * np.exp(np.cumsum(returns))
            open_values = np.roll(close, 1)
            open_values[0] = start_price
            high_noise = np.abs(rng.normal(0.0, 0.001, len(date_index)))
            low_noise = np.abs(rng.normal(0.0, 0.001, len(date_index)))
            frame["open"] = open_values
            frame["close"] = close
            frame["high"] = np.maximum(frame["open"], frame["close"]) * (1 + high_noise)
            frame["low"] = np.minimum(frame["open"], frame["close"]) * (1 - low_noise)
            frame["volume"] = rng.uniform(100.0, 1000.0, len(date_index))
            frame = frame[["open", "high", "low", "close", "volume"]]
        else:
            for symbol in normalized_symbols:
                returns = rng.normal(mu_value, sigma_value, len(date_index))
                frame[symbol] = start_price * np.exp(np.cumsum(returns))

        payload = {
            "source": tool_name,
            "request": {
                "symbols": normalized_symbols,
                "start": str(start),
                "end": None if end is None else str(end),
                "interval": interval,
                "count": count_value,
                "mu": mu_value,
                "sigma": sigma_value,
                "start_value": start_price,
                "seed": seed,
            },
            "rows": int(len(frame)),
            "columns": [str(column) for column in frame.columns],
            "data": _serialize_frame_records(frame),
        }
        logger.info(
            "%s completed successfully | request_id=%s | rows=%s",
            tool_name,
            request_id,
            len(frame),
        )
        return _success(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Synthetic GBM data generated successfully.",
            data=payload,
        )
    except GeneratorValidationError as exc:
        logger.warning(
            "%s validation failed | request_id=%s | error=%s",
            tool_name,
            request_id,
            exc,
        )
        return _error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            code="INVALID_INPUT",
            message="Invalid input.",
            details=str(exc),
        )
    except Exception as exc:
        logger.exception("%s failed | request_id=%s", tool_name, request_id)
        return _error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            code="TOOL_EXECUTION_FAILED",
            message="Tool execution failed.",
            details=str(exc),
        )


def data_generate_ticks(
    trading_tf_data: pd.DataFrame,
    *,
    model: str,
    trading_timeframe: str,
    m1_data: Optional[pd.DataFrame] = None,
    real_ticks: Optional[pd.DataFrame] = None,
    point_value: float = 0.00001,
    spread_model: str = "native_spread",
    fixed_spread_points: Optional[float] = None,
    min_spread_points: Optional[float] = None,
    max_spread_points: Optional[float] = None,
    random_seed: Optional[int] = None,
    max_output_rows: int = DEFAULT_MAX_OUTPUT_ROWS,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate standardized tick data from bars or existing tick data.

    Use this read-only tool for backtesting and simulation workflows that need
    a tick stream derived from OHLCV bars, M1 bars, real tick data, or a
    synthetic intrabar path.
    """
    tool_name = TICKS_TOOL_NAME
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s | model=%s", tool_name, request_id, model)

    try:
        base_frame = _validate_dataframe_not_empty(trading_tf_data, "trading_tf_data")
        max_rows = _validate_max_output_rows(max_output_rows)
        _validate_required_ohlc(base_frame, context="trading_tf_data")
        if model == "m1_ticks" or model == "synthetic_ticks":
            _validate_dataframe_not_empty(m1_data, "m1_data")
        if model == "real_ticks":
            _validate_dataframe_not_empty(real_ticks, "real_ticks")
        if random_seed is not None and (
            isinstance(random_seed, bool) or not isinstance(random_seed, int)
        ):
            raise GeneratorValidationError("random_seed must be an integer or None.")

        generator = TicksGenerator(
            model=model,
            trading_timeframe=trading_timeframe,
            m1_data=m1_data,
            real_ticks=real_ticks,
            point_value=point_value,
            spread_model=spread_model,
            fixed_spread_points=fixed_spread_points,
            min_spread_points=min_spread_points,
            max_spread_points=max_spread_points,
            random_seed=random_seed,
        )
        ticks = generator.generate(base_frame)
        _validate_tick_output(ticks, max_rows)

        payload = {
            "source": tool_name,
            "model": str(model).lower(),
            "trading_timeframe": str(trading_timeframe).upper(),
            "rows": int(len(ticks)),
            "columns": [str(column) for column in ticks.columns],
            "data": _serialize_frame_records(ticks),
        }
        logger.info(
            "%s completed successfully | request_id=%s | rows=%s",
            tool_name,
            request_id,
            len(ticks),
        )
        return _success(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Tick data generated successfully.",
            data=payload,
        )
    except (GeneratorValidationError, ValueError) as exc:
        logger.warning(
            "%s validation failed | request_id=%s | error=%s",
            tool_name,
            request_id,
            exc,
        )
        return _error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            code="INVALID_INPUT",
            message="Invalid input.",
            details=str(exc),
        )
    except Exception as exc:
        logger.exception("%s failed | request_id=%s", tool_name, request_id)
        return _error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            code="TOOL_EXECUTION_FAILED",
            message="Tool execution failed.",
            details=str(exc),
        )


__all__ = [
    "gbm_data_generate",
    "data_generate_ticks",
]

_TOOL_MARKER = "_haruquant_standardized_tool"

for _tool_name in __all__:
    setattr(globals()[_tool_name], _TOOL_MARKER, True)
