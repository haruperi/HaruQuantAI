"""Executable Optimization validation usage example.

Demonstrates walk-forward validation modes, time series fold generation, and walk-forward validation execution.
"""

import sys
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.optimization.validation import (
    SplitMode,
    build_time_series_splits,
    run_walk_forward_validation,
)
from tests.optimization.unit.test_adapter import FakeAdapter
from tests.optimization.unit.test_validation_contracts import walk_forward_request


def example_validation() -> None:
    """Demonstrate walk-forward validation execution and fold splitting."""
    print("=" * 80)
    print("Optimization Example 8: Walk-Forward Validation and Time Series Folds")
    print("=" * 80)

    # 1. Split mode enum
    print(f"Split Mode: {SplitMode.ROLLING.value}")

    # 2. Walk forward request
    req = walk_forward_request()
    print(f"Minimum fold count: {req.minimum_fold_count}")

    # 3. Build time series splits
    splits = build_time_series_splits(req)
    print(f"Generated {len(splits)} time-series folds.")
    print(f"Fold 0 leakage prevented: {splits[0].leakage_prevented}")

    # 4. Run walk-forward validation
    adapter = FakeAdapter()
    wf_res = run_walk_forward_validation(req, adapter)
    print(
        f"Walk-forward validation status: {wf_res.status}, pass rate: {wf_res.fold_pass_rate * 100:.1f}%"
    )


def main() -> None:
    """Run Optimization validation usage example."""
    example_validation()


if __name__ == "__main__":
    main()
