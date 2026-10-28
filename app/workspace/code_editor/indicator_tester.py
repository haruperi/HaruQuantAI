"""Historical indicator test sessions, chart series and durable configurations."""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Mapping
from typing import Any
from uuid import uuid4

from app.host.logging import get_logger
from app.include.price import BarPrice
from app.workspace.code_editor._common import CodeEditorError
from app.workspace.code_editor._indicator_data import (
    calculate_indicator,
    historical_bars,
    indicator_defaults,
    output_series,
)
from app.workspace.code_editor._indicator_resolver import resolve_indicator
from app.workspace.code_editor._storage import StateStore

logger = get_logger(__name__)


class IndicatorTester:
    """Execute real historical tests without suppressing calculation anomalies."""

    def __init__(
        self,
        store: StateStore | None = None,
        history_loader: Callable[..., tuple[BarPrice, list[int]]] | None = None,
    ) -> None:
        self._store = store or StateStore()
        self._history_loader = history_loader or (
            lambda symbol, timeframe, count: historical_bars(
                self._store.gateway, symbol, timeframe, count
            )
        )
        self._tests: dict[str, dict[str, Any]] = {}
        self._error_logs: dict[str, list[dict[str, Any]]] = {}

    def new_indy_test(
        self, indicator_name: str, symbol: str = "EURUSD", timeframe: str = "H1"
    ) -> dict[str, Any]:
        """FR-CODEEDITOR-INDTEST-NEW: Derive defaults from the selected class."""
        cls = self._resolve_indicator_class(indicator_name)
        config: dict[str, Any] = {
            "test_id": str(uuid4()),
            "indicator_name": indicator_name,
            "symbol": symbol,
            "timeframe": timeframe,
            "params": indicator_defaults(cls),
            "bars_to_reserve": 50,
            "bar_count": 150,
            "created_at": time.time(),
        }
        self._tests[config["test_id"]] = config
        return dict(config)

    def _resolve_indicator_class(self, indicator_name: str) -> Any:
        """Resolve the current declared class in the unified indicator library."""
        return resolve_indicator(indicator_name)

    def indicator_tester(
        self,
        indicator_name: str,
        symbol: str = "EURUSD",
        timeframe: str = "H1",
        params: Mapping[str, Any] | None = None,
        bars_to_reserve: int = 50,
        bar_count: int = 150,
        reference_values: list[float] | None = None,
        test_id: str | None = None,
    ) -> dict[str, Any]:
        """FR-CODEEDITOR-INDTEST-RUN: Execute on Data Manager history and report gaps."""
        identifier = test_id or str(uuid4())
        errors: list[dict[str, Any]] = []
        result: dict[str, Any] = {
            "test_id": identifier,
            "status": "failed",
            "symbol": symbol,
            "timeframe": timeframe,
            "bars_calculated": 0,
            "candlesticks": [],
            "indicator_plots": [],
            "plot_series": [],
            "table_rows": [],
            "discrepancies": [],
        }
        try:
            if not 0 <= bars_to_reserve <= 10000 or not 1 <= bar_count <= 10000:
                raise CodeEditorError("Reserve and display bar counts are out of range")
            cls = self._resolve_indicator_class(indicator_name)
            effective = indicator_defaults(cls) if params is None else dict(params)
            config = {
                "test_id": identifier,
                "indicator_name": indicator_name,
                "symbol": symbol,
                "timeframe": timeframe,
                "params": effective,
                "bars_to_reserve": bars_to_reserve,
                "bar_count": bar_count,
                "reference_values": reference_values,
            }
            self._tests[identifier] = config
            bars, timestamps = self._history_loader(
                symbol, timeframe, bars_to_reserve + bar_count
            )
            outputs = output_series(
                calculate_indicator(cls, bars, effective, timestamps), len(timestamps)
            )
            start = bars_to_reserve
            stamps = timestamps[start:]
            ohlcv = {
                name: getattr(bars, name + "_series")().values[start:]
                for name in ("open", "high", "low", "close", "volume")
            }
            candles = [
                {
                    "time": stamp,
                    **{name: float(values[i]) for name, values in ohlcv.items()},
                }
                for i, stamp in enumerate(stamps)
            ]
            plots: list[dict[str, Any]] = []
            category = str(getattr(cls, "category", "")).lower()
            separate = any(
                word in category for word in ("momentum", "volume", "oscillator")
            ) or cls.__name__ in {"RSI", "MACD", "Stochastic", "ATR", "CCI", "ADX"}
            for name, values in outputs.items():
                points: list[dict[str, Any]] = []
                for index, value in enumerate(values[start:]):
                    if not math.isfinite(float(value)):
                        errors.append(
                            {
                                "bar": index + start,
                                "time": stamps[index],
                                "series": name,
                                "type": "NonFiniteValue",
                                "message": "Indicator returned NaN or infinity",
                            }
                        )
                        points.append({"time": stamps[index]})
                    else:
                        points.append({"time": stamps[index], "value": float(value)})
                pane = (
                    "oscillator"
                    if separate or name in {"bandwidth", "percent_b"}
                    else "main"
                )
                plots.append({"name": name, "pane": pane, "data": points})
            primary = plots[0]["data"]
            table = []
            for index, candle in enumerate(candles):
                row_values = {
                    plot["name"]: plot["data"][index].get("value") for plot in plots
                }
                row = {
                    **candle,
                    "indicator_val": primary[index].get("value"),
                    "outputs": row_values,
                }
                if reference_values is not None and index < len(reference_values):
                    reference = float(reference_values[index])
                    if not math.isfinite(reference):
                        raise CodeEditorError("Reference values must be finite")
                    difference = (
                        abs(row["indicator_val"] - reference)
                        if row["indicator_val"] is not None
                        else None
                    )
                    row.update(reference_val=reference, diff=difference)
                    if difference is not None and difference > 0.0001:
                        errors.append(
                            {
                                "bar": index,
                                "time": candle["time"],
                                "calc": row["indicator_val"],
                                "ref": reference,
                                "diff": difference,
                            }
                        )
                table.append(row)
            result.update(
                status="success",
                bars_calculated=len(table),
                candlesticks=candles,
                indicator_plots=primary,
                plot_series=plots,
                table_rows=table,
                discrepancies=errors,
                data_source="historical",
            )
        except Exception as exc:
            logger.exception("Indicator test failed: %s", indicator_name)
            errors.append({"bar": 0, "type": type(exc).__name__, "message": str(exc)})
            result.update(error=str(exc), discrepancies=errors)
        self._error_logs[identifier] = errors
        return result

    def edit_indy_params(
        self, test_id: str, params: Mapping[str, Any]
    ) -> dict[str, Any]:
        """FR-CODEEDITOR-INDTEST-PARAMS: Reuse the session's history and identity."""
        if test_id not in self._tests:
            raise CodeEditorError(f"Unknown indicator test: {test_id}")
        cfg = self._tests[test_id]
        return self.indicator_tester(
            cfg["indicator_name"],
            cfg["symbol"],
            cfg["timeframe"],
            params,
            cfg["bars_to_reserve"],
            cfg.get("bar_count", 150),
            cfg.get("reference_values"),
            test_id,
        )

    def indicator_tester_error(
        self, test_id: str | None = None
    ) -> list[dict[str, Any]]:
        """FR-CODEEDITOR-INDTEST-ERROR: Return non-finite values and exceptions."""
        return (
            self._error_logs.get(test_id, [])
            if test_id
            else [error for errors in self._error_logs.values() for error in errors]
        )

    def save_test_config(self, test_id: str, name: str) -> dict[str, Any]:
        """FR-CODEEDITOR-INDTEST-SAVE: Persist the complete setup through SQLite."""
        if test_id not in self._tests or not name.strip():
            raise CodeEditorError(
                "Choose an existing test and a nonempty configuration name"
            )
        config = {**self._tests[test_id], "saved_name": name}
        self._store.write("indicator:" + test_id, config)
        return {"status": "saved", "config_id": test_id, "config": config}

    def load_test_config(self, config_id: str) -> dict[str, Any]:
        """FR-CODEEDITOR-INDTEST-LOAD: Restore a saved test after process restart."""
        config = self._store.read("indicator:" + config_id)
        if config is None:
            raise CodeEditorError(f"Test config '{config_id}' not found")
        self._tests[config_id] = config
        return {"status": "loaded", "config": config}
