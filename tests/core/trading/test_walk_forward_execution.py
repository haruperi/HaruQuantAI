"""Unit and integration tests for end-to-end Walk-Forward execution workflow."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import pytest
from app.core.data.contracts import MarketBar
from app.core.lib.errors import DomainError
from app.core.trading.optimization import (
    CancellationToken,
    OptimizationEngine,
    ParameterRange,
    WalkForwardResult,
    WalkForwardWindowResult,
)


def _make_bar(time: int, close: float) -> MarketBar:
    return MarketBar(
        time=time,
        open=close - 0.0010,
        high=close + 0.0020,
        low=close - 0.0020,
        close=close,
        tick_volume=100,
    )


def test_walk_forward_execution_workflow_deterministic() -> None:
    """Walk-forward execution runs rolling windows, selects best IS param, and evaluates OOS."""
    engine = OptimizationEngine()
    bars = [_make_bar(1000 + i * 60, 1.1000 + (i % 10) * 0.0010) for i in range(100)]
    ranges = [
        ParameterRange(name="threshold", start=1.0, end=3.0, step=1.0),
    ]

    def mock_eval(
        slice_bars: Sequence[MarketBar], params: Mapping[str, float]
    ) -> float:
        assert len(slice_bars) > 0
        thresh = params["threshold"]
        # Score increases monotonically with threshold
        return thresh * 10.0

    result = engine.run_walk_forward(
        bars=bars,
        parameter_ranges=ranges,
        num_windows=3,
        is_ratio=0.7,
        evaluate_fn=mock_eval,
    )

    assert isinstance(result, WalkForwardResult)
    assert len(result.windows) == 3
    assert len(result.detailed_windows) == 3
    assert len(result.window_results) == 3
    for win_res in result.detailed_windows:
        assert isinstance(win_res, WalkForwardWindowResult)
        assert win_res.selected_params == {"threshold": 3.0}
        assert win_res.is_score == pytest.approx(30.0)
        assert win_res.oos_score == pytest.approx(30.0)
    # Aggregate WFE: 100 * sum(30 + 30 + 30) / sum(30 + 30 + 30) = 100.0%
    assert result.wfe == pytest.approx(100.0)


def test_walk_forward_stable_ties_retain_first_grid_order() -> None:
    """When multiple parameter sets have identical IS score, the earliest grid candidate is selected."""
    engine = OptimizationEngine()
    bars = [_make_bar(1000 + i * 60, 1.1000) for i in range(100)]
    # Candidates: p=1.0, p=2.0, p=3.0
    ranges = [ParameterRange(name="param", start=1.0, end=3.0, step=1.0)]

    # Constant score regardless of parameters
    def mock_eval(
        slice_bars: Sequence[MarketBar], params: Mapping[str, float]
    ) -> float:
        return 42.0

    result = engine.run_walk_forward(
        bars=bars,
        parameter_ranges=ranges,
        num_windows=2,
        is_ratio=0.7,
        evaluate_fn=mock_eval,
    )

    for win_res in result.detailed_windows:
        # First grid order candidate is param=1.0
        assert win_res.selected_params == {"param": 1.0}
        assert win_res.is_score == pytest.approx(42.0)
        assert win_res.oos_score == pytest.approx(42.0)
    assert result.wfe == pytest.approx(100.0)


def test_walk_forward_slice_isolation() -> None:
    """In-Sample evaluations receive strictly IS bars and Out-of-Sample receives strictly OOS bars."""
    engine = OptimizationEngine()
    bars = [_make_bar(1000 + i * 60, float(i)) for i in range(120)]
    ranges = [ParameterRange(name="p", start=1.0, end=1.0, step=1.0)]

    evaluated_slices: list[tuple[int, int, int]] = []

    def mock_eval(
        slice_bars: Sequence[MarketBar], params: Mapping[str, float]
    ) -> float:
        first_time = slice_bars[0].time
        last_time = slice_bars[-1].time
        evaluated_slices.append((len(slice_bars), first_time, last_time))
        return 10.0

    result = engine.run_walk_forward(
        bars=bars,
        parameter_ranges=ranges,
        num_windows=2,
        is_ratio=0.7,
        evaluate_fn=mock_eval,
    )

    # 2 windows * (1 candidate + 1 OOS) = 4 slice evaluations
    assert len(evaluated_slices) == 4
    for i, win in enumerate(result.windows):
        is_eval = evaluated_slices[i * 2]
        oos_eval = evaluated_slices[i * 2 + 1]

        # Slices must not overlap in bar time
        assert is_eval[2] < oos_eval[1]
        assert is_eval[0] == win.is_end_bar - win.is_start_bar
        assert oos_eval[0] == win.oos_end_bar - win.oos_start_bar


def test_walk_forward_invalid_specs_fail_closed() -> None:
    """Walk-forward execution rejects non-positive windows, invalid ratios, empty bars, and unsorted bars."""
    engine = OptimizationEngine()
    valid_bars = [_make_bar(1000 + i * 60, 1.1) for i in range(50)]
    ranges = [ParameterRange(name="p", start=1.0, end=2.0, step=1.0)]

    def dummy_eval(
        slice_bars: Sequence[MarketBar], params: Mapping[str, float]
    ) -> float:
        return 1.0

    # Non-positive windows
    with pytest.raises(DomainError) as exc:
        engine.run_walk_forward(
            bars=valid_bars,
            parameter_ranges=ranges,
            num_windows=0,
            evaluate_fn=dummy_eval,
        )
    assert exc.value.code == "INVALID_WALK_FORWARD_SPEC"

    # Invalid is_ratio <= 0.0 or >= 1.0
    with pytest.raises(DomainError) as exc:
        engine.run_walk_forward(
            bars=valid_bars,
            parameter_ranges=ranges,
            num_windows=2,
            is_ratio=0.0,
            evaluate_fn=dummy_eval,
        )
    assert exc.value.code == "INVALID_WALK_FORWARD_SPEC"

    with pytest.raises(DomainError) as exc:
        engine.run_walk_forward(
            bars=valid_bars,
            parameter_ranges=ranges,
            num_windows=2,
            is_ratio=1.0,
            evaluate_fn=dummy_eval,
        )
    assert exc.value.code == "INVALID_WALK_FORWARD_SPEC"

    # Empty bars
    with pytest.raises(DomainError) as exc:
        engine.run_walk_forward(
            bars=[],
            parameter_ranges=ranges,
            num_windows=2,
            evaluate_fn=dummy_eval,
        )
    assert exc.value.code == "INVALID_WALK_FORWARD_SPEC"

    # Non-increasing bar timestamps
    bad_time_bars = [
        _make_bar(1000, 1.1),
        _make_bar(1000, 1.2),  # identical timestamp
    ]
    with pytest.raises(DomainError) as exc:
        engine.run_walk_forward(
            bars=bad_time_bars,
            parameter_ranges=ranges,
            num_windows=1,
            evaluate_fn=dummy_eval,
        )
    assert exc.value.code == "INVALID_WALK_FORWARD_SPEC"


def test_walk_forward_non_finite_scores_fail_closed() -> None:
    """Walk-forward execution rejects NaN or Inf scores from evaluator."""
    engine = OptimizationEngine()
    bars = [_make_bar(1000 + i * 60, 1.1) for i in range(100)]
    ranges = [ParameterRange(name="p", start=1.0, end=2.0, step=1.0)]

    def nan_eval(slice_bars: Sequence[MarketBar], params: Mapping[str, float]) -> float:
        return float("nan")

    with pytest.raises(DomainError) as exc:
        engine.run_walk_forward(
            bars=bars,
            parameter_ranges=ranges,
            num_windows=2,
            evaluate_fn=nan_eval,
        )
    assert exc.value.code == "INVALID_OPTIMIZATION_SCORE"

    def inf_eval(slice_bars: Sequence[MarketBar], params: Mapping[str, float]) -> float:
        return float("inf")

    with pytest.raises(DomainError) as exc:
        engine.run_walk_forward(
            bars=bars,
            parameter_ranges=ranges,
            num_windows=2,
            evaluate_fn=inf_eval,
        )
    assert exc.value.code == "INVALID_OPTIMIZATION_SCORE"


def test_walk_forward_cancellation_and_progress() -> None:
    """Walk-forward reports progress and cancels cooperatively upon token request."""
    engine = OptimizationEngine()
    bars = [_make_bar(1000 + i * 60, 1.1) for i in range(100)]
    ranges = [
        ParameterRange(name="p1", start=1.0, end=2.0, step=1.0),  # 2 candidates
    ]

    progress_log: list[tuple[int, int]] = []

    def on_progress(completed: int, total: int) -> None:
        progress_log.append((completed, total))

    def eval_fn(slice_bars: Sequence[MarketBar], params: Mapping[str, float]) -> float:
        return 10.0

    # 3 windows * (2 candidates + 1 OOS) = 9 total evaluations
    res = engine.run_walk_forward(
        bars=bars,
        parameter_ranges=ranges,
        num_windows=3,
        evaluate_fn=eval_fn,
        progress=on_progress,
    )

    assert len(progress_log) == 9
    assert progress_log[-1] == (9, 9)
    assert res.wfe == pytest.approx(100.0)

    # Test pre-cancelled token
    cancelled_token = CancellationToken()
    cancelled_token.cancel()

    with pytest.raises(DomainError) as exc:
        engine.run_walk_forward(
            bars=bars,
            parameter_ranges=ranges,
            num_windows=2,
            evaluate_fn=eval_fn,
            token=cancelled_token,
        )
    assert exc.value.code == "OPTIMIZATION_CANCELLED"


def test_walk_forward_cancellation_during_execution() -> None:
    """Walk-forward execution aborts with OPTIMIZATION_CANCELLED when cancelled during evaluation."""
    engine = OptimizationEngine()
    bars = [_make_bar(1000 + i * 60, 1.1) for i in range(100)]
    ranges = [
        ParameterRange(name="p", start=1.0, end=5.0, step=1.0),
    ]
    token = CancellationToken()
    eval_count = 0

    def eval_fn(slice_bars: Sequence[MarketBar], params: Mapping[str, float]) -> float:
        nonlocal eval_count
        eval_count += 1
        if eval_count == 3:
            token.cancel()
        return 1.0

    with pytest.raises(DomainError) as exc:
        engine.run_walk_forward(
            bars=bars,
            parameter_ranges=ranges,
            num_windows=3,
            evaluate_fn=eval_fn,
            token=token,
        )
    assert exc.value.code == "OPTIMIZATION_CANCELLED"
    assert eval_count >= 3


def test_walk_forward_cancellation_immediately_before_return() -> None:
    """Walk-forward aborts with OPTIMIZATION_CANCELLED when cancelled on the final evaluation before return."""
    engine = OptimizationEngine()
    bars = [_make_bar(1000 + i * 60, 1.1) for i in range(100)]
    ranges = [
        ParameterRange(name="p", start=1.0, end=2.0, step=1.0),  # 2 candidates
    ]
    token = CancellationToken()
    # 2 windows * (2 candidates + 1 OOS) = 6 evaluations
    total_evals = 2 * (2 + 1)
    eval_count = 0

    def eval_fn(slice_bars: Sequence[MarketBar], params: Mapping[str, float]) -> float:
        nonlocal eval_count
        eval_count += 1
        if eval_count == total_evals:
            # Cancel on the very last evaluation, so loop completes but pre-return check trips
            token.cancel()
        return 10.0

    with pytest.raises(DomainError) as exc:
        engine.run_walk_forward(
            bars=bars,
            parameter_ranges=ranges,
            num_windows=2,
            evaluate_fn=eval_fn,
            token=token,
        )
    assert exc.value.code == "OPTIMIZATION_CANCELLED"
    assert eval_count == total_evals


def test_walk_forward_evaluator_exception_propagates() -> None:
    """User evaluator exceptions bubble directly without being swallowed or converted."""
    engine = OptimizationEngine()
    bars = [_make_bar(1000 + i * 60, 1.1) for i in range(100)]
    ranges = [ParameterRange(name="p", start=1.0, end=2.0, step=1.0)]

    def exploding_eval(
        slice_bars: Sequence[MarketBar], params: Mapping[str, float]
    ) -> float:
        raise ZeroDivisionError("custom_evaluator_division_error")

    with pytest.raises(ZeroDivisionError, match="custom_evaluator_division_error"):
        engine.run_walk_forward(
            bars=bars,
            parameter_ranges=ranges,
            num_windows=2,
            evaluate_fn=exploding_eval,
        )


def test_walk_forward_insufficient_bars_for_windows_fails_closed() -> None:
    """Walk-forward rejects when fewer windows than requested can be generated from the bar sequence."""
    engine = OptimizationEngine()
    # Only 10 bars, requesting 10 windows
    bars = [_make_bar(1000 + i * 60, 1.1) for i in range(10)]
    ranges = [ParameterRange(name="p", start=1.0, end=2.0, step=1.0)]

    def dummy_eval(
        slice_bars: Sequence[MarketBar], params: Mapping[str, float]
    ) -> float:
        return 1.0

    with pytest.raises(DomainError) as exc:
        engine.run_walk_forward(
            bars=bars,
            parameter_ranges=ranges,
            num_windows=10,
            evaluate_fn=dummy_eval,
        )
    assert exc.value.code == "INVALID_WALK_FORWARD_SPEC"
    assert "Insufficient bars to generate 10 windows" in exc.value.message
