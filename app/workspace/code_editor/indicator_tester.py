"""Indicator tester editor contracts and workflows.

Description:
    Runs synchronous historical calculations and persists typed test configurations.
    Diagnostic variants preserve differences, non-finite gaps and execution failures.
Purpose:
    FEAT-CODE-EDITOR-CONTRACTS: Preserve typed editor behavior and host ownership.
Key Capabilities:
    - FR-code-editor-indicator-run: Observe the associated workflow; fixed-label logs
      are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-indicator-tester-edit-indy-params: Observe the associated workflow;
      fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-indicator-tester-indicator-tester: Observe the associated workflow;
      fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-indicator-tester-indicator-tester-error: Observe the associated
      workflow; fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-indicator-tester-init: Observe the associated workflow; fixed-label
      logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-indicator-tester-load-test-config: Observe the associated workflow;
      fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-indicator-tester-new-indy-test: Observe the associated workflow;
      fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-indicator-tester-save-test-config: Observe the associated workflow;
      fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
Python API Usage:
    import app.workspace.code_editor.indicator_tester
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor --no-cov
"""

from __future__ import annotations

import logging
import math
import time
from collections.abc import Callable, Mapping
from uuid import uuid4

from pydantic import TypeAdapter

from app.core.lib.errors import JSONValue
from app.core.lib.responses import ErrorCode
from app.include.blocks.indicators.base import BaseIndicator
from app.include.blocks.price import BarPrice
from app.workspace.code_editor._common import CodeEditorError
from app.workspace.code_editor._indicator_data import (
    calculate_indicator,
    historical_bars,
    indicator_defaults,
    output_series,
)
from app.workspace.code_editor._indicator_resolver import resolve_indicator
from app.workspace.code_editor._storage import StateStore
from app.workspace.code_editor.results import (
    Candle,
    IndicatorConfig,
    IndicatorDiagnostic,
    IndicatorResult,
    IndicatorRow,
    LoadedTest,
    PlotPoint,
    PlotSeries,
    SavedTest,
    validate_result,
)

logger = logging.getLogger(__name__)


class IndicatorTester:
    """Execute real historical tests without suppressing calculation anomalies."""

    def __init__(
        self,
        store: StateStore | None = None,
        history_loader: Callable[..., tuple[BarPrice, list[int]]] | None = None,
    ) -> None:
        logger.debug("FR-code-editor-indicator-tester-init: invoked")
        self._store = store or StateStore()
        self._history_loader = history_loader or (
            lambda symbol, timeframe, count: historical_bars(
                self._store.gateway, symbol, timeframe, count
            )
        )
        self._tests: dict[str, IndicatorConfig] = {}
        self._error_logs: dict[str, list[IndicatorDiagnostic]] = {}

    def new_indy_test(
        self, indicator_name: str, symbol: str = "EURUSD", timeframe: str = "H1"
    ) -> IndicatorConfig:
        """FR-CODEEDITOR-INDTEST-NEW: Derive defaults from the selected class."""
        logger.debug("FR-code-editor-indicator-tester-new-indy-test: invoked")
        cls = self._resolve_indicator_class(indicator_name)
        config: IndicatorConfig = {
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
        return config.copy()

    def _resolve_indicator_class(self, indicator_name: str) -> type[BaseIndicator]:
        """Resolve the current declared class in the unified indicator library."""
        return resolve_indicator(indicator_name)

    def indicator_tester(
        self,
        indicator_name: str,
        symbol: str = "EURUSD",
        timeframe: str = "H1",
        params: Mapping[str, JSONValue] | None = None,
        bars_to_reserve: int = 50,
        bar_count: int = 150,
        reference_values: list[float] | None = None,
        test_id: str | None = None,
    ) -> IndicatorResult:
        """FR-CODEEDITOR-INDTEST-RUN: Execute on Data Manager history and report gaps."""
        logger.debug("FR-code-editor-indicator-tester-indicator-tester: invoked")
        identifier = test_id or str(uuid4())
        errors: list[IndicatorDiagnostic] = []
        result: dict[str, object] = {
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
            config: IndicatorConfig = {
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
            candles: list[Candle] = [
                {
                    "time": stamp,
                    "open": float(ohlcv["open"][i]),
                    "high": float(ohlcv["high"][i]),
                    "low": float(ohlcv["low"][i]),
                    "close": float(ohlcv["close"][i]),
                    "volume": float(ohlcv["volume"][i]),
                }
                for i, stamp in enumerate(stamps)
            ]
            plots: list[PlotSeries] = []
            category = str(getattr(cls, "category", "")).lower()
            separate = any(
                word in category for word in ("momentum", "volume", "oscillator")
            ) or cls.__name__ in {"RSI", "MACD", "Stochastic", "ATR", "CCI", "ADX"}
            for name, values in outputs.items():
                points: list[PlotPoint] = []
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
            table: list[IndicatorRow] = []
            for index, candle in enumerate(candles):
                row_values = {
                    plot["name"]: plot["data"][index].get("value") for plot in plots
                }
                row: IndicatorRow = {
                    "time": candle["time"],
                    "open": candle["open"],
                    "high": candle["high"],
                    "low": candle["low"],
                    "close": candle["close"],
                    "volume": candle["volume"],
                    "indicator_val": primary[index].get("value"),
                    "outputs": row_values,
                }
                if reference_values is not None and index < len(reference_values):
                    reference = float(reference_values[index])
                    if not math.isfinite(reference):
                        raise CodeEditorError("Reference values must be finite")
                    actual = row["indicator_val"]
                    difference = abs(actual - reference) if actual is not None else None
                    row["reference_val"] = reference
                    row["diff"] = difference
                    if (
                        actual is not None
                        and difference is not None
                        and difference > 0.0001
                    ):
                        errors.append(
                            {
                                "bar": index,
                                "time": candle["time"],
                                "calc": actual,
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
            logger.warning(
                "FR-code-editor-indicator-run: failed category=%s", type(exc).__name__
            )
            message = (
                str(exc)
                if isinstance(exc, CodeEditorError)
                else "Indicator calculation failed"
            )
            errors.append({"bar": 0, "type": type(exc).__name__, "message": message})
            result.update(error=message, discrepancies=errors)
        self._error_logs[identifier] = errors
        logger.info("FR-code-editor-indicator-run: completed")
        return validate_result(TypeAdapter(IndicatorResult), result)

    def edit_indy_params(
        self, test_id: str, params: Mapping[str, JSONValue]
    ) -> IndicatorResult:
        """FR-CODEEDITOR-INDTEST-PARAMS: Reuse the session's history and identity."""
        logger.debug("FR-code-editor-indicator-tester-edit-indy-params: invoked")
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
    ) -> list[IndicatorDiagnostic]:
        """FR-CODEEDITOR-INDTEST-ERROR: Return non-finite values and exceptions."""
        logger.debug("FR-code-editor-indicator-tester-indicator-tester-error: invoked")
        return (
            self._error_logs.get(test_id, [])
            if test_id
            else [error for errors in self._error_logs.values() for error in errors]
        )

    def save_test_config(self, test_id: str, name: str) -> SavedTest:
        """FR-CODEEDITOR-INDTEST-SAVE: Persist the complete setup through SQLite."""
        logger.debug("FR-code-editor-indicator-tester-save-test-config: invoked")
        if test_id not in self._tests or not name.strip():
            raise CodeEditorError(
                "Choose an existing test and a nonempty configuration name"
            )
        config = self._tests[test_id].copy()
        config["saved_name"] = name
        self._store.write("indicator:" + test_id, config)
        return {"status": "saved", "config_id": test_id, "config": config}

    def load_test_config(self, config_id: str) -> LoadedTest:
        """FR-CODEEDITOR-INDTEST-LOAD: Restore a saved test after process restart."""
        logger.debug("FR-code-editor-indicator-tester-load-test-config: invoked")
        raw = self._store.read("indicator:" + config_id)
        if raw is None:
            raise CodeEditorError(f"Test config '{config_id}' not found")
        config = validate_result(TypeAdapter(IndicatorConfig), raw)
        if config["test_id"] != config_id:
            raise CodeEditorError(
                "Invalid editor stored state", code=ErrorCode.INTERNAL
            )
        self._tests[config_id] = config
        return {"status": "loaded", "config": config}
