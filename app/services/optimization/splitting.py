"""Optimization walk-forward and chronological time-series splitting.

Provides rolling, anchored, and expanding time-series split generators,
with support for purging overlapping trades and embargo windows expressed
in bars (``bar_duration * bars``), not raw minutes.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.services.optimization.models import (
    OptimizationSummary,
    ParameterSpace,
    SplitterResult,
    WalkForwardWindow,
)

_DEFAULT_BAR_DURATION: timedelta = timedelta(days=1)


class WalkForwardSplit:
    """Configures and runs walk-forward split generation.

    Args:
        start_date: Start date boundary.
        end_date: End date boundary.
        folds: Number of time-series folds.
        train_fraction: Training allocation fraction (0-1).
        fold_mode: Split mode (``"rolling"``, ``"anchored"``,
            ``"expanding"``).
        purging_bars: Overlap purge window expressed in number of bars.
        embargo_bars: Embargo window expressed in number of bars.
        bar_duration: Duration of a single bar used to convert bar counts
            to time deltas. Defaults to 1 calendar day.
    """

    def __init__(
        self,
        start_date: datetime | str,
        end_date: datetime | str,
        folds: int = 5,
        train_fraction: float = 0.7,
        fold_mode: str = "rolling",
        purging_bars: int = 0,
        embargo_bars: int = 0,
        bar_duration: timedelta = _DEFAULT_BAR_DURATION,
    ) -> None:
        """Initialize split configuration."""
        self.start_date = (
            datetime.fromisoformat(start_date)
            if isinstance(start_date, str)
            else start_date
        )
        self.end_date = (
            datetime.fromisoformat(end_date) if isinstance(end_date, str) else end_date
        )
        self.folds = folds
        self.train_fraction = train_fraction
        self.fold_mode = fold_mode.strip().lower()
        self.purging_bars = purging_bars
        self.embargo_bars = embargo_bars
        self.bar_duration = bar_duration

    def split(self) -> SplitterResult:
        """Generate time-series split windows.

        Returns:
            SplitterResult: Generated train/test windows.
        """
        if self.fold_mode in {"expanding", "anchored"}:
            folds_list = expanding_window_split(
                self.start_date,
                self.end_date,
                self.folds,
                self.train_fraction,
                self.purging_bars,
                self.embargo_bars,
                self.bar_duration,
            )
        else:
            folds_list = rolling_window_split(
                self.start_date,
                self.end_date,
                self.folds,
                self.train_fraction,
                self.purging_bars,
                self.embargo_bars,
                self.bar_duration,
            )
        return SplitterResult(folds=folds_list)


def chronological_split(
    start: datetime | str,
    end: datetime | str,
    train_fraction: float = 0.7,
) -> tuple[WalkForwardWindow, ...]:
    """Create a single train-test split window.

    Args:
        start: Start date.
        end: End date.
        train_fraction: Fraction allocated to training (0-1).

    Returns:
        tuple[WalkForwardWindow, ...]: Single-element tuple containing
            the split window.
    """
    dt_start = datetime.fromisoformat(start) if isinstance(start, str) else start
    dt_end = datetime.fromisoformat(end) if isinstance(end, str) else end
    total_sec = (dt_end - dt_start).total_seconds()
    train_end = dt_start + timedelta(seconds=total_sec * train_fraction)
    return (
        WalkForwardWindow(
            train_start=dt_start.isoformat(),
            train_end=train_end.isoformat(),
            test_start=train_end.isoformat(),
            test_end=dt_end.isoformat(),
        ),
    )


def rolling_window_split(
    start: datetime,
    end: datetime,
    folds: int = 5,
    train_fraction: float = 0.7,
    purging_bars: int = 0,
    embargo_bars: int = 0,
    bar_duration: timedelta = _DEFAULT_BAR_DURATION,
) -> list[WalkForwardWindow]:
    """Create deterministic rolling time-series train/test windows.

    Purging and embargo periods are computed as
    ``bar_duration * bar_count`` rather than raw minutes, so the same
    bar count produces the correct time offset regardless of timeframe.

    Args:
        start: Start date boundary.
        end: End date boundary.
        folds: Number of folds.
        train_fraction: Training allocation fraction (0-1).
        purging_bars: Bars to purge at the end of each train window.
        embargo_bars: Bars to embargo at the start of each test window.
        bar_duration: Duration of one bar (e.g. ``timedelta(hours=1)``
            for hourly data).

    Returns:
        list[WalkForwardWindow]: Generated rolling split windows.
    """
    total_seconds = (end - start).total_seconds()
    step_seconds = total_seconds / (folds + 1)
    purge_delta = bar_duration * purging_bars
    embargo_delta = bar_duration * embargo_bars
    windows: list[WalkForwardWindow] = []
    for i in range(folds):
        fold_start = start + timedelta(seconds=i * step_seconds)
        fold_end = start + timedelta(seconds=(i + 2) * step_seconds)

        train_duration = (fold_end - fold_start).total_seconds() * train_fraction
        train_end = fold_start + timedelta(seconds=train_duration)

        purged_train_end = train_end - purge_delta
        if purged_train_end <= fold_start:
            purged_train_end = train_end

        test_start = train_end + embargo_delta
        if test_start >= fold_end:
            test_start = train_end

        windows.append(
            WalkForwardWindow(
                train_start=fold_start.isoformat(),
                train_end=purged_train_end.isoformat(),
                test_start=test_start.isoformat(),
                test_end=fold_end.isoformat(),
            )
        )
    return windows


def expanding_window_split(
    start: datetime,
    end: datetime,
    folds: int = 5,
    train_fraction: float = 0.7,
    purging_bars: int = 0,
    embargo_bars: int = 0,
    bar_duration: timedelta = _DEFAULT_BAR_DURATION,
) -> list[WalkForwardWindow]:
    """Create deterministic expanding time-series train/test windows.

    Each fold's training window always begins at ``start`` and grows
    with each successive fold. Purging and embargo are applied in bars
    via ``bar_duration * bar_count``.

    Args:
        start: Start date boundary.
        end: End date boundary.
        folds: Number of folds.
        train_fraction: Training allocation fraction (0-1).
        purging_bars: Bars to purge at the end of each train window.
        embargo_bars: Bars to embargo at the start of each test window.
        bar_duration: Duration of one bar.

    Returns:
        list[WalkForwardWindow]: Generated expanding split windows.
    """
    total_seconds = (end - start).total_seconds()
    step_seconds = total_seconds / (folds + 1)
    purge_delta = bar_duration * purging_bars
    embargo_delta = bar_duration * embargo_bars
    windows: list[WalkForwardWindow] = []
    for i in range(folds):
        fold_start = start
        fold_end = start + timedelta(seconds=(i + 2) * step_seconds)

        train_duration = (fold_end - fold_start).total_seconds() * train_fraction
        train_end = fold_start + timedelta(seconds=train_duration)

        purged_train_end = train_end - purge_delta
        if purged_train_end <= fold_start:
            purged_train_end = train_end

        test_start = train_end + embargo_delta
        if test_start >= fold_end:
            test_start = train_end

        windows.append(
            WalkForwardWindow(
                train_start=fold_start.isoformat(),
                train_end=purged_train_end.isoformat(),
                test_start=test_start.isoformat(),
                test_end=fold_end.isoformat(),
            )
        )
    return windows


def splitter_from_rolling(
    start: str,
    end: str,
    folds: int = 5,
    train_fraction: float = 0.7,
    purging_bars: int = 0,
    embargo_bars: int = 0,
    bar_duration: timedelta = _DEFAULT_BAR_DURATION,
) -> SplitterResult:
    """Create rolling split windows from ISO date strings.

    Args:
        start: ISO start date.
        end: ISO end date.
        folds: Number of folds.
        train_fraction: Training allocation fraction (0-1).
        purging_bars: Bars to purge at the end of each train window.
        embargo_bars: Bars to embargo at the start of each test window.
        bar_duration: Duration of one bar.

    Returns:
        SplitterResult: Generated windows envelope.
    """
    dt_start = datetime.fromisoformat(start)
    dt_end = datetime.fromisoformat(end)
    folds_list = rolling_window_split(
        dt_start,
        dt_end,
        folds,
        train_fraction,
        purging_bars,
        embargo_bars,
        bar_duration,
    )
    return SplitterResult(folds=folds_list)


def splitter_from_expanding(
    start: str,
    end: str,
    folds: int = 5,
    train_fraction: float = 0.7,
    purging_bars: int = 0,
    embargo_bars: int = 0,
    bar_duration: timedelta = _DEFAULT_BAR_DURATION,
) -> SplitterResult:
    """Create expanding split windows from ISO date strings.

    Args:
        start: ISO start date.
        end: ISO end date.
        folds: Number of folds.
        train_fraction: Training allocation fraction (0-1).
        purging_bars: Bars to purge at the end of each train window.
        embargo_bars: Bars to embargo at the start of each test window.
        bar_duration: Duration of one bar.

    Returns:
        SplitterResult: Generated expanding windows.
    """
    dt_start = datetime.fromisoformat(start)
    dt_end = datetime.fromisoformat(end)
    folds_list = expanding_window_split(
        dt_start,
        dt_end,
        folds,
        train_fraction,
        purging_bars,
        embargo_bars,
        bar_duration,
    )
    return SplitterResult(folds=folds_list)


def splitter_rolling_split(
    data: Any,  # noqa: ANN401
    train_fraction: float = 0.7,
) -> tuple[Any, Any]:
    """Split tabular data into rolling train/test slices.

    Args:
        data: Tabular list or pandas DataFrame.
        train_fraction: Training fraction allocation (0-1).

    Returns:
        tuple[Any, Any]: ``(train, test)`` slices.
    """
    if hasattr(data, "iloc"):
        split_idx = int(len(data) * train_fraction)
        return data.iloc[:split_idx], data.iloc[split_idx:]
    split_idx = int(len(data) * train_fraction)
    return data[:split_idx], data[split_idx:]


def run_walk_forward_optimization(
    strategy_ref: str,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    parameter_space: ParameterSpace,
    objective: str = "sharpe",
    initial_balance: float = 10000.0,
    folds: int = 5,
    train_fraction: float = 0.7,
    fold_mode: str = "rolling",
    purging_bars: int = 0,
    embargo_bars: int = 0,
    bar_duration: timedelta = _DEFAULT_BAR_DURATION,
    max_candidates: int = 20,
    seed: int | None = None,
    **kwargs: Any,  # noqa: ANN401
) -> dict[str, Any]:
    """Run walk-forward optimization: optimize on train folds, evaluate on test folds.

    For each time-series fold the training window is optimized via random
    search; the best candidate from that fold is then applied to the test
    window and the out-of-sample result is recorded.

    Args:
        strategy_ref: Target strategy registration name.
        symbols: Symbol ticker list.
        timeframe: Bar resolution timeframe string.
        start: ISO start date.
        end: ISO end date.
        parameter_space: Parameter space boundaries.
        objective: Target optimization metric name.
        initial_balance: Starting account balance.
        folds: Number of time-series folds.
        train_fraction: Training allocation fraction (0-1).
        fold_mode: Split mode (``"rolling"``, ``"anchored"``,
            ``"expanding"``).
        purging_bars: Bars to purge at the end of each train window.
        embargo_bars: Bars to embargo at the start of each test window.
        bar_duration: Duration of one bar for bar-count conversion.
        max_candidates: Maximum optimization candidates per fold.
        seed: Random seed for deterministic reproducibility.
        **kwargs: Additional adapter options (e.g. ``dry_run``).

    Returns:
        dict[str, Any]: Standard response dictionary with keys
            ``"status"``, ``"message"``, and ``"data"`` containing a
            list of per-fold results with in-sample and out-of-sample
            summaries.
    """
    from app.services.optimization.algorithms.random import random_search
    from app.services.optimization.helpers import run_strategy_backtest
    from app.services.optimization.scoring import evaluate_candidate_score

    dry_run = kwargs.get("dry_run", True)

    splitter = WalkForwardSplit(
        start_date=start,
        end_date=end,
        folds=folds,
        train_fraction=train_fraction,
        fold_mode=fold_mode,
        purging_bars=purging_bars,
        embargo_bars=embargo_bars,
        bar_duration=bar_duration,
    )
    split_result = splitter.split()

    fold_results: list[dict[str, Any]] = []
    for fold_idx, window in enumerate(split_result.folds):
        # In-sample optimization
        try:
            is_summary: OptimizationSummary = random_search(
                strategy_ref=strategy_ref,
                symbols=symbols,
                timeframe=timeframe,
                start=window.train_start,
                end=window.train_end,
                parameter_space=parameter_space,
                objective=objective,
                initial_balance=initial_balance,
                max_candidates=max_candidates,
                seed=seed,
                **kwargs,
            )
        except Exception as exc:  # noqa: BLE001
            fold_results.append(
                {
                    "fold": fold_idx,
                    "window": window.model_dump(),
                    "error": str(exc),
                }
            )
            continue

        best_params = is_summary.best_candidate.parameters

        # Out-of-sample evaluation
        oos_score: float | None = None
        oos_metrics: dict[str, Any] = {}
        if not dry_run:
            try:
                bt_res = run_strategy_backtest(
                    strategy_ref=strategy_ref,
                    symbols=symbols,
                    timeframe=timeframe,
                    start=window.test_start,
                    end=window.test_end,
                    parameters=best_params,
                    initial_balance=initial_balance,
                    **kwargs,
                )
                oos_eval = evaluate_candidate_score(
                    bt_res.trades,
                    initial_balance,
                    objective,
                )
                oos_score = oos_eval["score"]
                oos_metrics = oos_eval
            except Exception as exc:  # noqa: BLE001
                oos_metrics = {"error": str(exc)}

        fold_results.append(
            {
                "fold": fold_idx,
                "window": window.model_dump(),
                "best_parameters": best_params,
                "in_sample_score": is_summary.best_score,
                "out_of_sample_score": oos_score,
                "out_of_sample_metrics": oos_metrics,
            }
        )

    return {
        "status": "success",
        "message": "Walk-forward optimization completed.",
        "data": {
            "folds": fold_results,
            "total_folds": len(fold_results),
            "objective": objective,
        },
    }


def run_walk_forward_matrix(
    strategy_refs: list[str],
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    parameter_spaces: list[ParameterSpace],
    objective: str = "sharpe",
    initial_balance: float = 10000.0,
    folds: int = 5,
    train_fraction: float = 0.7,
    fold_mode: str = "rolling",
    purging_bars: int = 0,
    embargo_bars: int = 0,
    bar_duration: timedelta = _DEFAULT_BAR_DURATION,
    max_candidates: int = 20,
    seed: int | None = None,
    **kwargs: Any,  # noqa: ANN401
) -> dict[str, Any]:
    """Run walk-forward optimization across multiple strategy configurations.

    Executes :func:`run_walk_forward_optimization` for each
    ``(strategy_ref, parameter_space)`` pair and assembles the results
    into a comparison matrix keyed by strategy reference.

    Args:
        strategy_refs: Strategy registration names to compare.
        symbols: Symbol ticker list.
        timeframe: Bar resolution timeframe string.
        start: ISO start date.
        end: ISO end date.
        parameter_spaces: Parameter space boundaries per strategy.
            Must have the same length as ``strategy_refs``.
        objective: Target optimization metric name.
        initial_balance: Starting account balance.
        folds: Number of time-series folds.
        train_fraction: Training allocation fraction (0-1).
        fold_mode: Split mode (``"rolling"``, ``"anchored"``,
            ``"expanding"``).
        purging_bars: Bars to purge at the end of each train window.
        embargo_bars: Bars to embargo at the start of each test window.
        bar_duration: Duration of one bar for bar-count conversion.
        max_candidates: Maximum optimization candidates per fold.
        seed: Random seed for deterministic reproducibility.
        **kwargs: Additional adapter options (e.g. ``dry_run``).

    Returns:
        dict[str, Any]: Standard response dictionary with keys
            ``"status"``, ``"message"``, and ``"data"`` containing a
            matrix of per-strategy walk-forward results.

    Raises:
        ValueError: When ``strategy_refs`` and ``parameter_spaces``
            have different lengths.
    """
    if len(strategy_refs) != len(parameter_spaces):
        msg = (
            "strategy_refs and parameter_spaces must have the same length. "
            f"Got {len(strategy_refs)} strategies and "
            f"{len(parameter_spaces)} spaces."
        )
        raise ValueError(msg)

    matrix: dict[str, Any] = {}
    for strategy_ref, space in zip(strategy_refs, parameter_spaces, strict=True):
        result = run_walk_forward_optimization(
            strategy_ref=strategy_ref,
            symbols=symbols,
            timeframe=timeframe,
            start=start,
            end=end,
            parameter_space=space,
            objective=objective,
            initial_balance=initial_balance,
            folds=folds,
            train_fraction=train_fraction,
            fold_mode=fold_mode,
            purging_bars=purging_bars,
            embargo_bars=embargo_bars,
            bar_duration=bar_duration,
            max_candidates=max_candidates,
            seed=seed,
            **kwargs,
        )
        matrix[strategy_ref] = result.get("data", {})

    return {
        "status": "success",
        "message": "Walk-forward matrix completed.",
        "data": {
            "matrix": matrix,
            "strategies": strategy_refs,
            "objective": objective,
            "folds": folds,
        },
    }
