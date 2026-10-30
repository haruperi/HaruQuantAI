"""Parameter optimization engine.

Supports Grid Search and Walk-Forward matrix generation.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
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

        for i in range(len(self.ranges)):
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
class WalkForwardResult:
    """Aggregated multi-run Walk-Forward optimization outcome."""

    windows: tuple[WalkForwardWindow, ...]
    window_results: tuple[dict[str, Any], ...]
    wfe: float  # Walk-Forward Efficiency percentage


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


__all__ = [
    "CancellationToken",
    "OptimizationEngine",
    "OptimizationIndexes",
    "ParameterRange",
    "WalkForwardResult",
    "WalkForwardWindow",
]
