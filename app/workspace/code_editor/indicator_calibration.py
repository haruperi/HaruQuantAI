"""Indicator output range calibration across historical symbols and timeframes.

Description:
    Implements donor-faithful indicator calibration (WO-CE-CALIBRATION). Enforces
    engine gates (rejecting Stockpicker / Single-asset), loads historical bar series,
    evaluates parameter variation combinations, computes population mean and standard
    deviation across finite output values, and applies decade-based range rounding
    and step calculation.
Purpose:
    FEAT-CODE-EDITOR-CALIBRATION: Calibrate indicator min/max/step ranges from
    historical market data and persist results in host storage.
Key Capabilities:
    - FR-code-editor-calibration-parse: Parse CalibrationRanges configuration rules,
      parameter variations, disabled outputs, and rounding flags.
    - FR-code-editor-calibration-run: Evaluate indicator outputs across symbols,
      timeframes, and parameter grids and compute beautified population ranges.
Python API Usage:
    from app.workspace.code_editor.indicator_calibration import (
        IndicatorCalibrationService,
    )
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor/test_indicator_suite.py --no-cov
"""

from __future__ import annotations

import itertools
import logging
import math
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from app.core.lib.errors import JSONValue
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.price import BarPrice
from app.workspace.code_editor._common import CodeEditorError
from app.workspace.code_editor._indicator_data import (
    calculate_indicator,
    historical_bars,
    indicator_defaults,
    output_series,
)
from app.workspace.code_editor._indicator_resolver import resolve_indicator
from app.workspace.code_editor._storage import StateStore
from app.workspace.code_editor.catalogue import indicator_catalogue
from app.workspace.code_editor.command_models import (
    CalibratedRangeEntry,
    CalibrationRequest,
    CalibrationResult,
)
from app.workspace.code_editor.indicator_suite import _coerce_scalar

logger = logging.getLogger(__name__)

UNSUPPORTED_CALIBRATION_ENGINES = {
    "stockpicker",
    "single-asset",
    "single_asset",
    "sp",
    "sa",
    "algocloud stockpicker",
    "algocloud single-asset",
}
EXCLUDED_CALIBRATION_INDICATORS = {"DataLoggingIndy"}


@dataclass(slots=True)
class CalibrationRangesConfig:
    """Parsed parameter variation grid and output exclusions for calibration."""

    rounding_disabled: bool = False
    disabled_outputs: set[tuple[str, str]] = field(default_factory=set)
    parameter_variations: dict[tuple[str, str], list[str]] = field(default_factory=dict)


def parse_calibration_ranges_config(
    ranges_text: str | None,
) -> CalibrationRangesConfig:
    """Parse donor CalibrationRanges.txt key=value configuration lines."""
    logger.debug("FR-code-editor-calibration-parse: invoked")
    cfg = CalibrationRangesConfig()
    if not ranges_text:
        return cfg
    for raw_line in ranges_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        left, right = [part.strip() for part in line.split("=", 1)]
        if left.lower() == "rounding":
            cfg.rounding_disabled = right.lower() in {"disabled", "false", "0", "off"}
            continue
        if "." not in left:
            continue
        indy_name, member_name = [part.strip() for part in left.split(".", 1)]
        if right.lower() == "disabled":
            cfg.disabled_outputs.add((indy_name.lower(), member_name.lower()))
        else:
            values = [v.strip() for v in right.split(",") if v.strip()]
            if values:
                cfg.parameter_variations[(indy_name.lower(), member_name.lower())] = (
                    values
                )
    return cfg


def beautify_calibration_range(
    min_value: float,
    max_value: float,
    *,
    max_steps: int = -1,
    rounding_disabled: bool = False,
) -> tuple[float, float, float]:
    """Round min/max/step values across decade thresholds matching donor fixValues."""
    diff = abs(max_value - min_value)
    if diff == 0.0:
        fixed_min = round(min_value, 4)
        fixed_max = round(max_value, 4)
        return fixed_min, fixed_max, 0.1
    if rounding_disabled:
        fixed_min = round(min_value, 4)
        fixed_max = round(max_value, 4)
        span = abs(fixed_max - fixed_min)
        raw_step = (span / max_steps) if max_steps > 0 else (diff / 100.0)
        return fixed_min, fixed_max, max(round(raw_step, 4), 0.0001)

    decade_table: tuple[tuple[float, float, float], ...] = (
        (100000.0, 10000.0, 5000.0),
        (10000.0, 1000.0, 500.0),
        (1000.0, 100.0, 50.0),
        (100.0, 10.0, 5.0),
        (10.0, 1.0, 0.5),
        (1.0, 0.1, 0.05),
        (0.1, 0.01, 0.005),
        (0.01, 0.001, 0.0005),
        (0.001, 0.0001, 0.0001),
    )
    quantum = 0.0001
    default_step = 0.0001
    for threshold, q_val, step_val in decade_table:
        if diff > threshold:
            quantum = q_val
            default_step = step_val
            break

    fixed_min = round(math.floor(min_value / quantum) * quantum, 6)
    fixed_max = round(math.ceil(max_value / quantum) * quantum, 6)
    if max_steps > 0:
        span = abs(fixed_max - fixed_min)
        step = max(round(span / max_steps, 4), 0.0001)
    else:
        step = default_step
    return fixed_min, fixed_max, step


class IndicatorCalibrationService:
    """Calibrate indicator output ranges across historical market datasets."""

    def __init__(
        self,
        store: StateStore | None = None,
        history_loader: Callable[[str, str, int], tuple[BarPrice, list[int]]]
        | None = None,
    ) -> None:
        logger.debug("FR-code-editor-calibration-run: service initialized")
        self.store = store or StateStore()
        self._history_loader = history_loader or (
            lambda symbol, timeframe, count: historical_bars(
                self.store.gateway, symbol, timeframe, count
            )
        )

    def calibrate(self, req: CalibrationRequest) -> CalibrationResult:
        """Execute indicator calibration and persist resulting parameter ranges."""
        logger.debug("FR-code-editor-calibration-run: invoked")
        engine_norm = req.engine.strip().lower()
        if engine_norm in UNSUPPORTED_CALIBRATION_ENGINES:
            raise CodeEditorError(
                "Indicator calibration is not supported for AlgoCloud "
                "Stockpicker / Single-asset engine."
            )

        datasets: list[tuple[BarPrice, list[int]]] = []
        for symbol in req.symbols:
            for timeframe in req.timeframes:
                bars, timestamps = self._history_loader(
                    symbol, timeframe, req.bars_count
                )
                datasets.append((bars, timestamps))

        ranges_cfg = parse_calibration_ranges_config(req.ranges_config_text)
        target_classes = self._resolve_target_classes(req.indicators)

        entries: list[CalibratedRangeEntry] = []
        skipped: list[str] = []
        for cls in target_classes:
            if cls.__name__ in EXCLUDED_CALIBRATION_INDICATORS:
                skipped.append(cls.__name__)
                continue
            param_grids = self._expand_parameter_grid(cls, ranges_cfg)
            collected_by_output: dict[str, list[float]] = {}
            calculation_succeeded = False
            for bars, timestamps in datasets:
                for params in param_grids:
                    try:
                        raw_out = calculate_indicator(cls, bars, params, timestamps)
                        series_map = output_series(raw_out, len(timestamps))
                        calculation_succeeded = True
                    except Exception:
                        logger.debug(
                            "FR-code-editor-calibration-run: calc failed, skipping parameter set"
                        )
                        continue
                    for out_name, arr in series_map.items():
                        if (
                            cls.__name__.lower(),
                            out_name.lower(),
                        ) in ranges_cfg.disabled_outputs:
                            continue
                        finite_mask = np.isfinite(arr)
                        if np.any(finite_mask):
                            bucket = collected_by_output.setdefault(out_name, [])
                            bucket.extend(float(v) for v in arr[finite_mask])

            if not calculation_succeeded or not collected_by_output:
                skipped.append(cls.__name__)
                continue

            total_outputs = len(collected_by_output)
            for out_idx, (out_name, samples) in enumerate(collected_by_output.items()):
                if not samples:
                    continue
                arr_vals = np.asarray(samples, dtype=np.float64)
                mean_val = float(np.mean(arr_vals))
                std_val = float(np.std(arr_vals, ddof=0))
                raw_min = mean_val - std_val
                raw_max = mean_val + std_val
                fixed_min, fixed_max, step = beautify_calibration_range(
                    raw_min,
                    raw_max,
                    max_steps=req.max_steps,
                    rounding_disabled=ranges_cfg.rounding_disabled,
                )
                is_primary = out_idx == 0 and (
                    total_outputs == 1 or out_name.lower() in {"value", "main"}
                )
                key = cls.__name__ if is_primary else f"{cls.__name__}.{out_name}"
                entries.append(
                    CalibratedRangeEntry(
                        key=key,
                        indicator=cls.__name__,
                        output=out_name,
                        min_value=fixed_min,
                        max_value=fixed_max,
                        step=step,
                        mean=round(mean_val, 6),
                        std_dev=round(std_val, 6),
                        samples=len(samples),
                    )
                )

        result = CalibrationResult(
            project_name=req.project_name,
            task_name=req.task_name,
            engine=req.engine,
            calibrated_count=len(entries),
            skipped_indicators=skipped,
            ranges=entries,
        )
        scope_key = (
            f"indicator_calibration:{req.project_name}:{req.task_name or 'project'}"
        )
        payload = result.model_dump(mode="json")
        self.store.write(scope_key, payload)
        self.store.write("indicator_calibration:latest", payload)
        logger.info(
            "FR-code-editor-calibration-run: calibrated=%d skipped=%d",
            len(entries),
            len(skipped),
        )
        return result

    def _resolve_target_classes(
        self, requested: list[str]
    ) -> list[type[BaseIndicator]]:
        if requested:
            classes: list[type[BaseIndicator]] = []
            seen: set[str] = set()
            for ref in requested:
                base_ref = ref.split(".")[0] if "::" not in ref else ref
                if base_ref in EXCLUDED_CALIBRATION_INDICATORS:
                    continue
                cls = resolve_indicator(base_ref)
                if cls.__name__ not in seen:
                    seen.add(cls.__name__)
                    classes.append(cls)
            return classes
        resolved_all: list[type[BaseIndicator]] = []
        for info in indicator_catalogue():
            if info.name in EXCLUDED_CALIBRATION_INDICATORS:
                continue
            try:
                resolved_all.append(resolve_indicator(info.identity))
            except Exception:
                logger.debug(
                    "FR-code-editor-calibration-run: resolve indicator failed, skipping"
                )
                continue
        return resolved_all

    def _expand_parameter_grid(
        self,
        cls: type[BaseIndicator],
        ranges_cfg: CalibrationRangesConfig,
    ) -> list[dict[str, JSONValue]]:
        defaults = indicator_defaults(cls)
        if not defaults:
            return [{}]
        keys = list(defaults.keys())
        value_lists: list[list[JSONValue]] = []
        for param_name in keys:
            default_val = defaults[param_name]
            custom_tokens = ranges_cfg.parameter_variations.get(
                (cls.__name__.lower(), param_name.lower())
            )
            if custom_tokens:
                coerced: list[JSONValue] = []
                for token in custom_tokens:
                    try:
                        coerced.append(_coerce_scalar(token, default_val))
                    except CodeEditorError:
                        continue
                value_lists.append(coerced or [default_val])
            else:
                value_lists.append([default_val])
        combinations: list[dict[str, JSONValue]] = []
        for combo in itertools.product(*value_lists):
            combinations.append(dict(zip(keys, combo, strict=True)))
            if len(combinations) >= 64:
                break
        return combinations
