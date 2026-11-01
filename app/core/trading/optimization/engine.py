"""Parameter optimization engine.

Supports Grid Search and Walk-Forward matrix generation.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from app.core.data.contracts import MarketBar
from app.core.lib.errors import DomainError


class CancellationToken:
    """Cooperative cancellation token for interruptible search tasks."""

    def __init__(self) -> None:
        self._cancelled: bool = False

    def cancel(self) -> None:
        """Signal cancellation to running tasks."""
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        """Check whether cancellation has been requested."""
        return self._cancelled

    def check(self) -> None:
        """Raise DomainError if cancellation has been requested."""
        if self._cancelled:
            raise DomainError(
                code="OPTIMIZATION_CANCELLED",
                message="Optimization operation was cancelled",
            )


@dataclass(frozen=True, slots=True)
class ParameterRange:
    """Discrete stepped numeric parameter search dimension."""

    name: str
    start: float
    end: float
    step: float

    def get_values(self) -> tuple[float, ...]:
        """Generate sequence of discrete values from start to end inclusive."""
        if self.step <= 0.0 or self.start > self.end:
            return (self.start,)

        vals: list[float] = []
        curr = self.start
        while curr <= self.end + 1e-9:
            vals.append(round(curr, 6))
            curr += self.step
        return tuple(vals)


class OptimizationIndexes:
    """Bidirectional linear index permutation resolver for multi-parameter grids."""

    def __init__(self, ranges: Sequence[ParameterRange]) -> None:
        self.ranges = tuple(ranges)
        self._names = [r.name for r in self.ranges]
        self._values = [r.get_values() for r in self.ranges]
        self._sizes = [len(v) for v in self._values]

        total = 1
        for s in self._sizes:
            total *= max(1, s)
        self.total_permutations = total if self.ranges else 0

    def get_params(self, index: int) -> dict[str, float]:
        """Convert a linear permutation index into named parameter values."""
        if index < 0 or index >= self.total_permutations:
            msg = f"Index {index} out of bounds (total={self.total_permutations})"
            raise IndexError(msg)

        params: dict[str, float] = {}
        rem = index

        for i in reversed(range(len(self.ranges))):
            size = self._sizes[i]
            val_idx = rem % size
            rem //= size
            params[self._names[i]] = self._values[i][val_idx]

        return params

    def get_index(self, params: dict[str, float]) -> int:
        """Resolve named parameter values to their linear permutation index."""
        multiplier = 1
        index = 0

        for i in reversed(range(len(self.ranges))):
            name = self._names[i]
            target_val = params.get(name)
            if target_val is None:
                msg = f"Missing parameter '{name}' in query"
                raise KeyError(msg)

            vals = self._values[i]
            try:
                # Find closest matching discrete value
                val_idx = min(
                    range(len(vals)),
                    key=lambda idx: abs(vals[idx] - target_val),
                )
            except ValueError as err:
                msg = f"Unable to locate index for value {target_val}"
                raise ValueError(msg) from err

            index += val_idx * multiplier
            multiplier *= self._sizes[i]

        return index


@dataclass(frozen=True, slots=True)
class WalkForwardWindow:
    """Temporal In-Sample (training) and Out-of-Sample (testing) window partition."""

    index: int
    is_start_bar: int
    is_end_bar: int
    oos_start_bar: int
    oos_end_bar: int
    is_start_time: int = 0
    is_end_time: int = 0
    oos_start_time: int = 0
    oos_end_time: int = 0


@dataclass(frozen=True, slots=True)
class WalkForwardWindowResult:
    """Evaluation outcome for a single Walk-Forward window."""

    window: WalkForwardWindow
    selected_params: dict[str, float]
    is_score: float
    oos_score: float

    def to_dict(self) -> dict[str, Any]:
        """Convert window result to dictionary."""
        return {
            "window_index": self.window.index,
            "selected_params": dict(self.selected_params),
            "is_score": self.is_score,
            "oos_score": self.oos_score,
            "is_start_bar": self.window.is_start_bar,
            "is_end_bar": self.window.is_end_bar,
            "oos_start_bar": self.window.oos_start_bar,
            "oos_end_bar": self.window.oos_end_bar,
        }


@dataclass(frozen=True, slots=True)
class WalkForwardResult:
    """Aggregated multi-run Walk-Forward optimization outcome."""

    windows: tuple[WalkForwardWindow, ...]
    window_results: tuple[dict[str, Any], ...]
    wfe: float  # Walk-Forward Efficiency percentage
    detailed_windows: tuple[WalkForwardWindowResult, ...] = ()


class OptimizationEngine:
    """Strategy parameter optimization and Walk-Forward matrix engine."""

    def build_indexes(
        self, parameter_ranges: Sequence[ParameterRange]
    ) -> OptimizationIndexes:
        """Construct multi-parameter permutation index mapper."""
        return OptimizationIndexes(parameter_ranges)

    def generate_wf_windows(
        self,
        total_bars: int,
        num_windows: int,
        is_ratio: float = 0.7,
        bars: Sequence[MarketBar] | None = None,
    ) -> tuple[WalkForwardWindow, ...]:
        """Generate rolling In-Sample / Out-of-Sample Walk-Forward execution windows."""
        if total_bars <= 0 or num_windows <= 0:
            return ()

        # Ensure ratio is valid
        ratio = max(0.1, min(0.9, is_ratio))
        k_ratio = max(1, round(ratio / (1.0 - ratio)))

        # Each window has IS of length k_ratio * step_size and OOS of step_size
        step_size = max(2, total_bars // (num_windows + k_ratio))
        is_len = int(step_size * ratio / (1.0 - ratio))
        oos_len = step_size

        windows: list[WalkForwardWindow] = []

        for w in range(num_windows):
            is_start = w * step_size
            is_end = is_start + is_len
            oos_start = is_end
            oos_end = (
                total_bars
                if w == num_windows - 1
                else min(total_bars, oos_start + oos_len)
            )

            if oos_start >= total_bars or oos_end <= oos_start:
                break

            is_t_start = (
                int(bars[is_start].time) if bars and is_start < len(bars) else 0
            )
            is_t_end = int(bars[is_end - 1].time) if bars and is_end <= len(bars) else 0
            oos_t_start = (
                int(bars[oos_start].time) if bars and oos_start < len(bars) else 0
            )
            oos_t_end = (
                int(bars[oos_end - 1].time) if bars and oos_end <= len(bars) else 0
            )

            windows.append(
                WalkForwardWindow(
                    index=w,
                    is_start_bar=is_start,
                    is_end_bar=is_end,
                    oos_start_bar=oos_start,
                    oos_end_bar=oos_end,
                    is_start_time=is_t_start,
                    is_end_time=is_t_end,
                    oos_start_time=oos_t_start,
                    oos_end_time=oos_t_end,
                )
            )

        return tuple(windows)

    def calculate_wfe(self, is_metric: float, oos_metric: float) -> float:
        """Calculate Walk-Forward Efficiency (WFE) percentage.

        WFE = (OOS Metric / IS Metric) * 100%. Returns 0.0 when IS metric
        is non-positive.
        """
        if is_metric <= 0.0:
            return 0.0
        return (oos_metric / is_metric) * 100.0

    def run_grid(
        self,
        parameter_ranges: Sequence[ParameterRange],
        evaluate_fn: Callable[[dict[str, float]], float],
        token: CancellationToken | None = None,
        progress: Callable[[int, int], None] | None = None,
    ) -> list[tuple[dict[str, float], float]]:
        """Execute exhaustive grid search across parameter permutations."""
        indexes = self.build_indexes(parameter_ranges)
        total = indexes.total_permutations
        results: list[tuple[dict[str, float], float]] = []

        for step in range(total):
            if token is not None:
                token.check()

            params = indexes.get_params(step)
            score = float(evaluate_fn(params))
            results.append((params, score))

            if progress is not None:
                progress(step + 1, total)

        # Sort descending by evaluation score
        results.sort(key=lambda item: item[1], reverse=True)
        return results

    def _validate_wf_spec(
        self,
        bars: Sequence[MarketBar],
        num_windows: int,
        is_ratio: float,
    ) -> None:
        if num_windows <= 0:
            msg = f"num_windows must be positive, got {num_windows}"
            raise DomainError(code="INVALID_WALK_FORWARD_SPEC", message=msg)
        if not (0.0 < is_ratio < 1.0):
            msg = f"is_ratio must be between 0.0 and 1.0 exclusive, got {is_ratio}"
            raise DomainError(code="INVALID_WALK_FORWARD_SPEC", message=msg)
        if not bars:
            msg = "Cannot execute walk forward optimization with empty bar sequence"
            raise DomainError(code="INVALID_WALK_FORWARD_SPEC", message=msg)
        for i in range(1, len(bars)):
            if bars[i].time <= bars[i - 1].time:
                msg = (
                    f"Bar timestamps must be strictly increasing: "
                    f"bars[{i}].time ({bars[i].time}) <= "
                    f"bars[{i - 1}].time ({bars[i - 1].time})"
                )
                raise DomainError(code="INVALID_WALK_FORWARD_SPEC", message=msg)

    def _validate_wf_windows(
        self,
        windows: tuple[WalkForwardWindow, ...],
        num_windows: int,
        total_bars: int,
    ) -> None:
        if len(windows) < num_windows:
            msg = (
                f"Insufficient bars to generate {num_windows} windows "
                f"(generated {len(windows)})"
            )
            raise DomainError(code="INVALID_WALK_FORWARD_SPEC", message=msg)
        for w in windows:
            if w.is_end_bar <= w.is_start_bar or w.oos_end_bar <= w.oos_start_bar:
                msg = "Walk-forward window contains empty IS or OOS slice"
                raise DomainError(code="INVALID_WALK_FORWARD_SPEC", message=msg)
            if w.oos_end_bar > total_bars:
                msg = "Walk-forward window exceeds total bar sequence bounds"
                raise DomainError(code="INVALID_WALK_FORWARD_SPEC", message=msg)

    def _evaluate_single_window(
        self,
        window: WalkForwardWindow,
        bars: Sequence[MarketBar],
        indexes: OptimizationIndexes,
        evaluate_fn: Callable[[Sequence[MarketBar], Mapping[str, float]], float],
        *,
        token: CancellationToken | None = None,
        on_step: Callable[[], None] | None = None,
    ) -> WalkForwardWindowResult:
        is_slice = tuple(bars[window.is_start_bar : window.is_end_bar])
        oos_slice = tuple(bars[window.oos_start_bar : window.oos_end_bar])

        best_params: dict[str, float] | None = None
        best_is_score = float("-inf")

        for step in range(indexes.total_permutations):
            if token is not None:
                token.check()

            params = indexes.get_params(step)
            score = evaluate_fn(is_slice, params)
            if not math.isfinite(score):
                msg = f"Non-finite IS evaluation score encountered: {score}"
                raise DomainError(code="INVALID_OPTIMIZATION_SCORE", message=msg)

            if score > best_is_score:
                best_is_score = score
                best_params = params

            if on_step is not None:
                on_step()

        if best_params is None:
            msg = "Failed to select best parameter set for window"
            raise DomainError(code="INVALID_WALK_FORWARD_SPEC", message=msg)

        if token is not None:
            token.check()

        oos_score = evaluate_fn(oos_slice, best_params)
        if not math.isfinite(oos_score):
            msg = f"Non-finite OOS evaluation score encountered: {oos_score}"
            raise DomainError(code="INVALID_OPTIMIZATION_SCORE", message=msg)

        if on_step is not None:
            on_step()

        return WalkForwardWindowResult(
            window=window,
            selected_params=best_params,
            is_score=best_is_score,
            oos_score=oos_score,
        )

    def run_walk_forward(
        self,
        bars: Sequence[MarketBar],
        parameter_ranges: Sequence[ParameterRange],
        *,
        num_windows: int,
        is_ratio: float = 0.7,
        evaluate_fn: Callable[[Sequence[MarketBar], Mapping[str, float]], float],
        token: CancellationToken | None = None,
        progress: Callable[[int, int], None] | None = None,
    ) -> WalkForwardResult:
        """Execute rolling Walk-Forward optimization across sequential bar slices.

        For each rolling window:
        1. Evaluates all parameter candidates on In-Sample (IS) slice.
        2. Selects candidate with highest IS score (stable ties retain first order).
        3. Evaluates selected parameters once on Out-of-Sample (OOS) slice.
        4. Retains typed per-window details and computes aggregate WFE.

        Note:
            Callbacks must supply comparable, additive optimization scores.

        Args:
            bars: Chronologically increasing sequence of market bars.
            parameter_ranges: Parameter dimensions defining candidate search grid.
            num_windows: Number of rolling walk-forward windows (must be >= 1).
            is_ratio: Proportion of each window for In-Sample training (0 < ratio < 1).
            evaluate_fn: Callback accepting bar slice and parameter mapping.
            token: Optional cancellation token for task interruption.
            progress: Optional callback reporting (completed, total).

        Returns:
            WalkForwardResult containing windows, details, and aggregate WFE.
        """
        self._validate_wf_spec(bars, num_windows, is_ratio)
        indexes = self.build_indexes(parameter_ranges)
        if indexes.total_permutations <= 0:
            msg = "Parameter ranges produce no candidate permutations"
            raise DomainError(code="INVALID_WALK_FORWARD_SPEC", message=msg)

        windows = self.generate_wf_windows(
            total_bars=len(bars),
            num_windows=num_windows,
            is_ratio=is_ratio,
            bars=bars,
        )
        self._validate_wf_windows(windows, num_windows, len(bars))

        total_evals = len(windows) * (indexes.total_permutations + 1)
        completed = [0]

        def _on_step() -> None:
            completed[0] += 1
            if progress is not None:
                progress(completed[0], total_evals)

        detailed_windows = [
            self._evaluate_single_window(
                w,
                bars,
                indexes,
                evaluate_fn,
                token=token,
                on_step=_on_step,
            )
            for w in windows
        ]

        if token is not None:
            token.check()

        total_is = sum(item.is_score for item in detailed_windows)
        total_oos = sum(item.oos_score for item in detailed_windows)
        aggregate_wfe = self.calculate_wfe(total_is, total_oos)

        return WalkForwardResult(
            windows=windows,
            window_results=tuple(item.to_dict() for item in detailed_windows),
            wfe=aggregate_wfe,
            detailed_windows=tuple(detailed_windows),
        )


__all__ = [
    "CancellationToken",
    "OptimizationEngine",
    "OptimizationIndexes",
    "ParameterRange",
    "WalkForwardResult",
    "WalkForwardWindow",
    "WalkForwardWindowResult",
]
