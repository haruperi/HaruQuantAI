"""Data preparation pipeline for simulation backtests.

Purpose:
    Data preparation pipeline for simulation backtests.

Classes:
    SimulationDataPreparationError: Public class defined by this module.
    PreparedSimulationData: Public class defined by this module.
    SimulationDataPreparer: Public class defined by this module.

Functions:
    _dukascopy_tick_fetcher: Internal helper function defined by this module.
    _resolve_engine_type: Internal helper function defined by this module.
    _normalize_position_sizing_method: Internal helper function defined by this module.
    _resolve_modelling: Internal helper function defined by this module.
    _resolve_tick_generator_config: Internal helper function defined by this module.
    _ensure_engine_symbol: Internal helper function defined by this module.
    _generate_ticks_for_backtest: Internal helper function defined by this module.

Notes:
    External-facing exports are collected in app/services/simulation/__init__.py;
    private underscore helpers remain implementation details unless preserved for API compatibility.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
from app.services.brokers.dukascopy import load_dukascopy
from app.services.data.generators import (
    TICK_MODEL_GENERATED,
    TICK_MODEL_OHLC_M1,
    TICK_MODEL_REAL,
    TICK_MODEL_TRADING_BAR,
    TicksGenerator,
)
from app.services.data.parquet import load_parquet
from app.services.execution import core
from app.services.risk.calculations.position_sizing import PositionSizer
from app.services.strategy.registry import get_strategy_class
from app.services.utils.logger import logger

from .config import (
    SimulationConfig,
    SimulationConfigError,
    SimulationPositionSizingError,
    SimulationSymbolInfo,
    _position_sizer_config,
)

INTERVAL_TICK = None
OFFER_SIDE_BID = None
fetch = None


def _dukascopy_tick_fetcher():
    """Internal function for data_preparation._dukascopy_tick_fetcher."""
    global INTERVAL_TICK, OFFER_SIDE_BID, fetch
    if fetch is None:
        from app.services.brokers.dukascopy import (
            INTERVAL_TICK as resolved_interval_tick,
        )
        from app.services.brokers.dukascopy import (
            OFFER_SIDE_BID as resolved_offer_side_bid,
        )
        from app.services.brokers.dukascopy import (
            fetch as resolved_fetch,
        )

        INTERVAL_TICK = resolved_interval_tick
        OFFER_SIDE_BID = resolved_offer_side_bid
        fetch = resolved_fetch
    return fetch, INTERVAL_TICK, OFFER_SIDE_BID


def _resolve_engine_type(value: str | None) -> str:
    """Internal function for data_preparation._resolve_engine_type."""
    raw = str(value or "event_driven").strip().lower()
    if raw == "simulator":
        raw = "event_driven"
    raw = raw.replace("-", "_")
    if raw == "vectorized":
        raw = "vectorised"
    if raw not in {"event_driven", "vectorised"}:
        raise ValueError(f"Unsupported engine_type: {value}")
    return raw


def _normalize_position_sizing_method(value: str | None) -> str:
    """Internal function for data_preparation._normalize_position_sizing_method."""
    raw = str(value or "fixed_lot").strip().lower().replace("-", "_")
    # We now enforce standard names directly from the Risk Engine
    return raw if raw in PositionSizer.VALID_METHODS else "fixed_lot"


def _resolve_modelling(mode: str | None) -> str:
    """Internal function for data_preparation._resolve_modelling."""
    resolved = str(mode or "trading_timeframe").strip().lower()
    allowed = {
        "trading_timeframe",
        "m1_ohlc",
        "generated",
        "real",
    }
    if resolved not in allowed:
        raise ValueError(f"Unsupported data_resolution: {mode}")
    return resolved


def _resolve_tick_generator_config(request: Any, data_mode: str) -> tuple[str, str]:
    """Internal function for data_preparation._resolve_tick_generator_config."""
    model_map = {
        "trading_timeframe": TICK_MODEL_TRADING_BAR,
        "m1_ohlc": TICK_MODEL_OHLC_M1,
        "generated": TICK_MODEL_GENERATED,
        "real": TICK_MODEL_REAL,
    }
    spread_map = {
        "use-broker": "native_spread",
        "broker": "native_spread",
        "fixed": "fixed_spread",
        "fixed_spread": "fixed_spread",
        "variable": "variable_spread",
        "variable_spread": "variable_spread",
    }
    tick_model = model_map.get(str(data_mode), TICK_MODEL_TRADING_BAR)
    spread_model = spread_map.get(
        str(getattr(request, "spread_type", "use-broker") or "use-broker")
        .strip()
        .lower(),
        "native_spread",
    )
    return tick_model, spread_model


def _ensure_engine_symbol(engine: Any, symbol_name: str) -> Any:
    """Register symbol info in engine state if not already present."""
    state = getattr(engine, "state", None)
    if state is None:
        return None

    for row in state.trading_symbols:
        if str(getattr(row, "name", "") or "") == str(symbol_name):
            return row

    client = getattr(engine, "client", None)
    symbol_info_fn = getattr(client, "symbol_info", None)
    if symbol_info_fn:
        info = symbol_info_fn(symbol_name)
        if info:
            # Wrap in core.SymbolInfo if available, otherwise use raw
            try:
                info = core.SymbolInfo(info)
            except Exception:
                pass
            state.trading_symbols.append(info)
            return info
    return None


def _generate_ticks_for_backtest(
    engine: Any,
    symbol_name: str,
    timeframe: str,
    request: Any,
    data_mode: str,
    bars_data,
    step_data=None,
):
    """Internal function for data_preparation._generate_ticks_for_backtest."""
    symbol_info = _ensure_engine_symbol(engine, symbol_name)
    tick_model, spread_model = _resolve_tick_generator_config(request, data_mode)
    point_value = float(getattr(symbol_info, "point", 0.00001) or 0.00001)

    generator_kwargs = {
        "model": tick_model,
        "trading_timeframe": timeframe,
        "point_value": point_value,
        "spread_model": spread_model,
    }
    if spread_model == "fixed_spread":
        generator_kwargs["fixed_spread_points"] = float(
            getattr(request, "spread", 0) or 0
        )
    elif spread_model == "variable_spread":
        generator_kwargs["min_spread_points"] = float(
            getattr(request, "spread_min", 0) or 0
        )
        generator_kwargs["max_spread_points"] = float(
            getattr(request, "spread_max", getattr(request, "spread_min", 0)) or 0
        )

    if tick_model == TICK_MODEL_OHLC_M1:
        generator_kwargs["m1_bars"] = step_data
    elif tick_model == TICK_MODEL_REAL:
        generator_kwargs["real_ticks"] = step_data

    ticks_generator = TicksGenerator(**generator_kwargs)
    ticks_data = ticks_generator.generate(bars_data.copy())
    if ticks_data is None or ticks_data.empty:
        raise ValueError(f"No ticks generated for {symbol_name}")
    return ticks_data, tick_model


def _resolve_position_size_impl(
    config: SimulationConfig,
    prepared: PreparedSimulationData,
) -> float:
    """Resolve configured money management into one primitive lot size."""
    position_config = config.execution.position_size
    sizing_input = _position_sizing_input(config, prepared)

    # PositionSizer now handles name aliasing and common config remapping internally
    sizer = PositionSizer(
        method=position_config.type,
        config=_position_sizer_config(config, position_config),
        mt5_client=None,
    )

    size = sizer.calculate_size(
        account_balance=float(config.account.initial_balance),
        entry_price=sizing_input["entry_price"],
        stop_loss=sizing_input["stop_loss"],
        symbol_info=SimulationSymbolInfo(
            contract_size=float(config.execution.contract_size),
        ),
        context=sizing_input["context"],
        symbol=sizing_input["symbol"],
        signal_type=sizing_input["signal_type"],
    )
    size = float(size)
    if size <= 0.0:
        raise SimulationPositionSizingError(
            f"position sizing resolved non-positive lot size: {size}"
        )
    return size


def _position_sizing_input(
    config: SimulationConfig,
    prepared: PreparedSimulationData,
) -> dict[str, Any]:
    """Internal function for data_preparation._position_sizing_input."""
    ticks = prepared.ticks
    if ticks is None or ticks.empty:
        raise SimulationPositionSizingError("position sizing requires prepared ticks")

    row = _first_trade_context_row(ticks)
    bid = _prep_safe_float(row.get("bid"), 0.0)
    ask = _prep_safe_float(row.get("ask"), bid)
    entry_signal = _prep_safe_float(row.get("entry_signal"), 0.0)
    signal_type = "sell" if entry_signal < 0 else "buy"
    entry_price = ask if signal_type == "buy" else bid
    if entry_price <= 0.0:
        entry_price = max(bid, ask, 1.0)

    stop_loss = _prep_safe_float(row.get("sl"), 0.0)
    context = dict(config.execution.position_size.params)
    if "atr" not in context:
        atr = _estimate_atr_from_ticks(ticks)
        if atr is not None:
            context["atr"] = atr

    return {
        "entry_price": float(entry_price),
        "stop_loss": None if stop_loss <= 0.0 else float(stop_loss),
        "context": context,
        "symbol": str(row.get("symbol") or config.data.symbols[0]),
        "signal_type": signal_type,
    }


def _first_trade_context_row(ticks: pd.DataFrame) -> Mapping[str, Any]:
    """Internal function for data_preparation._first_trade_context_row."""
    if "entry_signal" in ticks.columns:
        entries = ticks[ticks["entry_signal"].fillna(0.0).astype(float) != 0.0]
        if not entries.empty:
            return entries.iloc[0]
    return ticks.iloc[0]


def _estimate_atr_from_ticks(ticks: pd.DataFrame) -> float | None:
    """Internal function for data_preparation._estimate_atr_from_ticks."""
    if not {"bid", "ask"}.issubset(set(ticks.columns)):
        return None
    mid = (ticks["bid"].astype(float) + ticks["ask"].astype(float)) / 2.0
    if mid.empty:
        return None
    high = float(mid.max())
    low = float(mid.min())
    atr = high - low
    return atr if atr > 0.0 else None


def _prep_safe_float(value: Any, default: float = 0.0) -> float:
    """Internal function for data_preparation._prep_safe_float."""
    try:
        if value is None:
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def resolve_position_size(
    config: SimulationConfig,
    prepared: PreparedSimulationData,
) -> dict[str, Any]:
    """AI Tool wrapper for _resolve_position_size_impl."""
    try:
        import pandas as pd
        from app.services.utils.logger import logger

        kwargs = {}
        kwargs["config"] = config
        kwargs["prepared"] = prepared

        res = _resolve_position_size_impl(**kwargs)
        logger.info("Executed resolve_position_size tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]

        return {"status": "success", "data": data_payload}
    except Exception as error:
        from app.services.utils.logger import logger

        logger.error(f"Error in resolve_position_size: {error!s}")
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


class SimulationDataPreparationError(RuntimeError):
    """Raised when simulation data preparation cannot produce ticks."""


@dataclass(frozen=True)
class PreparedSimulationData:
    """Prepared tick stream and metadata for a simulation run."""

    ticks: pd.DataFrame
    signal_bars_by_symbol: Mapping[str, pd.DataFrame] = field(default_factory=dict)
    tick_counts_by_symbol: Mapping[str, int] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)


class SimulationDataPreparer:
    """Prepare strategy signals and ticks for the simulation engine."""

    def __init__(self, engine: Any):
        """Internal function for data_preparation.__init__."""
        self.engine = engine

    def prepare(self, config: SimulationConfig) -> PreparedSimulationData:
        """Prepare and merge all configured symbols into one tick stream."""
        merged_ticks: list[pd.DataFrame] = []
        signal_bars_by_symbol: dict[str, pd.DataFrame] = {}
        tick_counts_by_symbol: dict[str, int] = {}

        for symbol in config.data.symbols:
            prepared = self.prepare_symbol(config, symbol)
            merged_ticks.append(prepared.ticks)
            signal_bars_by_symbol[symbol] = prepared.signal_bars_by_symbol[symbol]
            tick_counts_by_symbol[symbol] = len(prepared.ticks)

        if not merged_ticks:
            raise SimulationDataPreparationError("no ticks generated for simulation")

        ticks = pd.concat(merged_ticks, axis=0).sort_index(kind="mergesort")
        metadata = {
            "symbols": tuple(config.data.symbols),
            "timeframe": config.data.timeframe,
            "tick_model": config.execution.tick_model,
            "spread_model": config.execution.spread_model,
            "start": config.data.start,
            "end": config.data.end,
            "warmup_start": config.data.warmup_start,
            "tick_count": len(ticks),
            "tick_counts_by_symbol": dict(tick_counts_by_symbol),
        }
        return PreparedSimulationData(
            ticks=ticks,
            signal_bars_by_symbol=signal_bars_by_symbol,
            tick_counts_by_symbol=tick_counts_by_symbol,
            metadata=metadata,
        )

    def prepare_symbol(
        self,
        config: SimulationConfig,
        symbol: str,
    ) -> PreparedSimulationData:
        """Prepare signal bars and ticks for one symbol."""
        bars = self._load_bars(config, symbol, config.data.timeframe)
        if bars is None or bars.empty:
            raise SimulationDataPreparationError(f"no bars retrieved for {symbol}")

        signal_bars = self._run_strategy(config, symbol, bars)
        signal_bars = signal_bars[signal_bars.index >= config.data.start]
        if signal_bars is None or signal_bars.empty:
            raise SimulationDataPreparationError(
                f"no signal-ready bars available for {symbol} after start filter"
            )

        point_value = self._point_value(symbol)
        _ensure_engine_symbol(self.engine, symbol)
        m1_data = self._load_m1_data_if_required(config, symbol)
        real_ticks = self._load_real_ticks_if_required(config, symbol)

        ticks_generator = TicksGenerator(
            model=config.execution.tick_model,
            trading_timeframe=config.data.timeframe,
            m1_bars=m1_data,
            real_ticks=real_ticks,
            point_value=point_value,
            spread_model=config.execution.spread_model,
            fixed_spread_points=config.execution.spread_points,
            min_spread_points=config.execution.spread_min,
            max_spread_points=config.execution.spread_max,
        )
        ticks = ticks_generator.generate(signal_bars.copy())
        if ticks is None or ticks.empty:
            raise SimulationDataPreparationError(f"no ticks generated for {symbol}")

        ticks = ticks.copy()
        ticks["symbol"] = symbol
        ticks["signal_timeframe"] = config.data.timeframe

        logger.info(
            f"Prepared {len(ticks)} ticks for {symbol} using "
            f"{config.execution.tick_model}/{config.execution.spread_model}"
        )
        return PreparedSimulationData(
            ticks=ticks,
            signal_bars_by_symbol={symbol: signal_bars.copy()},
            tick_counts_by_symbol={symbol: len(ticks)},
            metadata={
                "symbol": symbol,
                "timeframe": config.data.timeframe,
                "tick_model": config.execution.tick_model,
                "spread_model": config.execution.spread_model,
                "point_value": point_value,
            },
        )

    def _run_strategy(
        self,
        config: SimulationConfig,
        symbol: str,
        bars: pd.DataFrame,
    ) -> pd.DataFrame:
        """Internal function for data_preparation._run_strategy."""
        strategy_cls = get_strategy_class(config.strategy.name)
        params = dict(config.strategy.params)
        params["symbol"] = symbol
        strategy = strategy_cls(params=params)
        strategy.on_init()
        signal_bars = strategy.on_bar(bars.copy())
        if signal_bars is None or signal_bars.empty:
            raise SimulationDataPreparationError(
                f"strategy {config.strategy.name} produced no bars for {symbol}"
            )
        return signal_bars

    def _point_value(self, symbol: str) -> float:
        """Internal function for data_preparation._point_value."""
        client = getattr(self.engine, "client", None)
        symbol_info_fn = getattr(client, "symbol_info", None)
        if symbol_info_fn is None:
            return 0.00001
        symbol_info = symbol_info_fn(symbol)
        return float(getattr(symbol_info, "point", 0.00001) or 0.00001)

    def _load_bars(
        self,
        config: SimulationConfig,
        symbol: str,
        timeframe: str,
    ) -> pd.DataFrame:
        """Internal function for data_preparation._load_bars."""
        if config.preloaded_data is not None:
            return config.preloaded_data

        if config.data.source == "metatrader":
            client = self._required_client()
            return client.get_bars(
                symbol=symbol,
                timeframe=timeframe,
                date_from=config.data.warmup_start,
                date_to=config.data.end,
            )
        if config.data.source == "dukascopy":
            return load_dukascopy(
                symbol=symbol,
                timeframe=timeframe,
                start_date=config.data.warmup_start.strftime("%Y-%m-%d"),
                end_date=config.data.end.strftime("%Y-%m-%d"),
            )
        if config.data.source == "local":
            return self._load_local_frame(config, symbol, "bars")
        raise SimulationConfigError(
            f"unsupported data.source for simulation preparation: {config.data.source}"
        )

    def _load_m1_data_if_required(
        self,
        config: SimulationConfig,
        symbol: str,
    ) -> pd.DataFrame | None:
        """Internal function for data_preparation._load_m1_data_if_required."""
        if config.execution.tick_model != TICK_MODEL_OHLC_M1:
            return None
        if config.data.source == "local":
            m1_data = self._load_local_frame(config, symbol, "m1")
        else:
            m1_data = self._load_bars(config, symbol, "M1")
        if m1_data is None or m1_data.empty:
            raise SimulationDataPreparationError(
                f"no M1 bars retrieved for {symbol}; "
                f"{config.execution.tick_model} requires M1 data"
            )
        return m1_data

    def _load_real_ticks_if_required(
        self,
        config: SimulationConfig,
        symbol: str,
    ) -> pd.DataFrame | None:
        """Internal function for data_preparation._load_real_ticks_if_required."""
        if config.execution.tick_model != TICK_MODEL_REAL:
            return None
        if config.data.source == "metatrader":
            client = self._required_client()
            ticks = client.get_ticks(
                symbol=symbol,
                start=config.data.warmup_start,
                end=config.data.end,
            )
        elif config.data.source == "local":
            ticks = self._load_local_frame(config, symbol, "ticks")
        elif config.data.source == "dukascopy":
            ticks = self._load_dukascopy_real_ticks(config, symbol)
        else:
            raise SimulationConfigError(
                "unsupported data.source for real tick generation: "
                f"{config.data.source}"
            )

        if ticks is None or ticks.empty:
            raise SimulationDataPreparationError(
                f"no real ticks retrieved for {symbol}"
            )
        missing = {"bid", "ask"} - {str(col).lower() for col in ticks.columns}
        if missing:
            raise SimulationDataPreparationError(
                f"real tick data for {symbol} must contain bid and ask columns"
            )
        return ticks

    def _load_dukascopy_real_ticks(
        self,
        config: SimulationConfig,
        symbol: str,
    ) -> pd.DataFrame:
        """Internal function for data_preparation._load_dukascopy_real_ticks."""
        fetch_ticks, interval_tick, offer_side_bid = _dukascopy_tick_fetcher()

        dukas_symbol = f"{symbol[:3]}/{symbol[3:]}" if len(symbol) == 6 else symbol
        ticks = fetch_ticks(
            instrument=dukas_symbol,
            interval=interval_tick,
            offer_side=offer_side_bid,
            start=config.data.warmup_start,
            end=config.data.end,
        )
        if ticks is None or ticks.empty:
            return pd.DataFrame()

        out = ticks.copy()
        out.columns = [str(col).strip().lower() for col in out.columns]
        out = out.rename(
            columns={
                "bidprice": "bid",
                "askprice": "ask",
                "bidvolume": "bid_volume",
                "askvolume": "ask_volume",
            }
        )
        if "volume" not in out.columns and "bid_volume" in out.columns:
            out["volume"] = out["bid_volume"]
        if isinstance(out.index, pd.DatetimeIndex) and out.index.tz is not None:
            out.index = out.index.tz_convert("Europe/Athens").tz_localize(None)
        return self._slice_by_date(
            out.sort_index(), config.data.warmup_start, config.data.end
        )

    def _required_client(self) -> Any:
        """Internal function for data_preparation._required_client."""
        client = getattr(self.engine, "client", None)
        if client is None:
            raise SimulationDataPreparationError("engine.client is required")
        return client

    def _load_local_frame(
        self,
        config: SimulationConfig,
        symbol: str,
        kind: str,
    ) -> pd.DataFrame:
        """Internal function for data_preparation._load_local_frame."""
        path = self._resolve_local_file(config, symbol, kind)
        frame = self._read_local_frame(path)
        frame = self._slice_by_date(frame, config.data.warmup_start, config.data.end)
        if frame.empty:
            raise SimulationDataPreparationError(
                f"local {kind} file for {symbol} has no rows in requested range: {path}"
            )
        return frame

    def _resolve_local_file(
        self,
        config: SimulationConfig,
        symbol: str,
        kind: str,
    ) -> Path:
        """Internal function for data_preparation._resolve_local_file."""
        local_files = config.data.local_files
        aliases = {
            "bars": ("bars", "ohlcv", "data", "file", "path"),
            "m1": ("m1", "m1_bars", "minute_bars"),
            "ticks": ("ticks", "real_ticks", "tick_file"),
        }[kind]

        symbol_entry = self._lookup_mapping_key(local_files, symbol)
        if isinstance(symbol_entry, Mapping):
            path_value = self._first_mapping_value(symbol_entry, aliases)
        elif symbol_entry is not None and kind == "bars":
            path_value = symbol_entry
        else:
            path_value = self._first_mapping_value(local_files, aliases)

        if path_value is None:
            raise SimulationDataPreparationError(
                f"data.local_files must define {kind} file for {symbol}"
            )
        path = Path(str(path_value)).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists():
            raise SimulationDataPreparationError(f"local data file not found: {path}")
        return path

    @staticmethod
    def _lookup_mapping_key(mapping: Mapping[str, Any], key: str) -> Any:
        """Internal function for data_preparation._lookup_mapping_key."""
        if key in mapping:
            return mapping[key]
        lower_key = key.lower()
        for candidate, value in mapping.items():
            if str(candidate).lower() == lower_key:
                return value
        return None

    @staticmethod
    def _first_mapping_value(mapping: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
        """Internal function for data_preparation._first_mapping_value."""
        for key in keys:
            if key in mapping:
                return mapping[key]
        lower = {str(key).lower(): value for key, value in mapping.items()}
        for key in keys:
            if key.lower() in lower:
                return lower[key.lower()]
        return None

    @staticmethod
    def _read_local_frame(path: Path) -> pd.DataFrame:
        """Internal function for data_preparation._read_local_frame."""
        suffix = path.suffix.lower()
        if suffix == ".csv":
            frame = pd.read_csv(path)
        elif suffix in {".parquet", ".pq"}:
            frame = load_parquet(path)
        else:
            raise SimulationDataPreparationError(
                f"unsupported local data file type for {path}; expected csv or parquet"
            )
        if frame is None or frame.empty:
            raise SimulationDataPreparationError(f"local data file is empty: {path}")
        return SimulationDataPreparer._normalize_local_frame(frame, path)

    @staticmethod
    def _normalize_local_frame(frame: pd.DataFrame, path: Path) -> pd.DataFrame:
        """Internal function for data_preparation._normalize_local_frame."""
        data = frame.copy()
        data.columns = [str(col).strip().lower() for col in data.columns]

        if not isinstance(data.index, pd.DatetimeIndex):
            date_col = SimulationDataPreparer._detect_datetime_column(data)
            if date_col is None:
                raise SimulationDataPreparationError(
                    f"no datetime column detected in local data file: {path}"
                )
            data[date_col] = pd.to_datetime(data[date_col], errors="coerce")
            data = data.dropna(subset=[date_col]).set_index(date_col)
        else:
            data.index = pd.to_datetime(data.index, errors="coerce")
            data = data[~data.index.isna()]

        rename_map = {
            "tick_volume": "volume",
            "tickvolume": "volume",
            "vol": "volume",
            "datetime": "timestamp",
            "date": "timestamp",
            "time": "timestamp",
        }
        data = data.rename(
            columns={k: v for k, v in rename_map.items() if k in data.columns}
        )
        numeric_columns = {
            "open",
            "high",
            "low",
            "close",
            "volume",
            "spread",
            "bid",
            "ask",
            "last",
        }
        for col in numeric_columns & set(data.columns):
            data[col] = pd.to_numeric(data[col], errors="coerce")

        data.index = pd.DatetimeIndex(data.index, name="Datetime")
        return data.sort_index()

    @staticmethod
    def _detect_datetime_column(frame: pd.DataFrame) -> str | None:
        """Internal function for data_preparation._detect_datetime_column."""
        hints = ("timestamp", "datetime", "date", "time", "ts")
        for hint in hints:
            if hint in frame.columns:
                return hint
        for col in frame.columns:
            lowered = str(col).lower()
            if any(hint in lowered for hint in hints):
                return str(col)
        return None

    @staticmethod
    def _slice_by_date(
        frame: pd.DataFrame,
        start: pd.Timestamp,
        end: pd.Timestamp,
    ) -> pd.DataFrame:
        """Internal function for data_preparation._slice_by_date."""
        index = pd.DatetimeIndex(frame.index)
        mask = (index >= pd.Timestamp(start)) & (index <= pd.Timestamp(end))
        return frame.loc[mask].copy()
