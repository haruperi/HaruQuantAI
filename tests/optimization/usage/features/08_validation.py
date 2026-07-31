"""Executable Optimization validation usage example.

Demonstrates FEAT-OPT-08 walk-forward validation modes, time series fold generation, and walk-forward validation execution.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.optimization import (
    build_time_series_splits,
    run_walk_forward_validation,
)
from tests.optimization.usage._support import (
    genuine_execution_bundle,
    walk_forward_request,
)


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def fr_opt_029() -> None:
    """FR-OPT-029: Stage 1 — Time Series Split Modes.

    The system shall support rolling, anchored, and expanding split modes for walk-forward validation.
    """
    _header("Stage 1: Split Modes - Time Series Split Modes (FR-OPT-029)")
    modes = ("rolling", "anchored", "expanding")
    print(_format_result(modes))
    print(f"Data -> split_modes={modes}")


def fr_opt_031() -> None:
    """FR-OPT-031: Stage 1 — Walk-Forward Request Modeling.

    The system shall model walk-forward validation requests with window specifications and purge/embargo boundaries.
    """
    _header("Stage 1: WFA Request - Model Walk-Forward Request (FR-OPT-031)")
    dataset, _, _ = genuine_execution_bundle()
    req = walk_forward_request(dataset)
    print(_format_result(req))
    print(
        f"Data -> split_mode='{req.mode}', minimum_fold_count={req.minimum_fold_count}"
    )


def fr_opt_033() -> None:
    """FR-OPT-033: Stage 2 — Time Series Fold Split Assembly.

    The system shall construct deterministic UTC train/test folds enforcing purge and embargo logic.
    """
    _header("Stage 2: Fold Assembly - Build Time Series Splits (FR-OPT-033)")
    dataset, _, _ = genuine_execution_bundle()
    req = walk_forward_request(dataset)
    splits = build_time_series_splits(req)
    print(_format_result(splits))
    print(
        f"Data -> fold_count={len(splits)}, fold_0_leakage_prevented={splits[0].leakage_prevented if splits else None}"
    )


def fr_opt_034() -> None:
    """FR-OPT-034: Stage 3 — Walk-Forward Validation Execution.

    The system shall optimize each train fold, evaluate selected candidates OOS, and aggregate evidence without replacing failures with zero.
    """
    _header("Stage 3: Validation Execution - Run Walk-Forward Validation (FR-OPT-034)")
    dataset, _, adapter = genuine_execution_bundle()
    req = walk_forward_request(dataset)
    wf_res = run_walk_forward_validation(req, adapter)
    print(_format_result(wf_res))
    print(
        f"Data -> status='{wf_res.status}', pass_rate={wf_res.fold_pass_rate * 100:.1f}%, fold_count={len(wf_res.folds)}"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-OPT-08 — validation/ — Time-Series Validation\n\n"
        "Purpose: Build leakage-aware time-series splits (rolling, anchored, expanding), enforce purge/embargo boundaries, and execute walk-forward validation.\n\n"
        "Module flow:\n"
        "-> Stage 1: Split mode catalog and WFA request payload construction\n"
        "-> Stage 2: Time-series train/test fold split generation with purge/embargo evidence\n"
        "-> Stage 3: Walk-forward optimization execution across folds and aggregate evidence computation"
    )

    # Stage 1: Split Modes & Request Mapping
    fr_opt_029()
    fr_opt_031()

    # Stage 2: Fold Assembly
    fr_opt_033()

    # Stage 3: Validation Execution
    fr_opt_034()


if __name__ == "__main__":
    main()
