"""Executable Research leakage usage example.

Demonstrates lookahead feature validation, chronological time splitting, and research artifact masking.
"""

import sys
from pathlib import Path

import pandas as pd

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.research.leakage import (
    enforce_time_split,
    mask_research_artifact,
    validate_no_lookahead_features,
)


def example_leakage() -> None:
    """Demonstrate research leakage controls."""
    print("=" * 80)
    print("Research Example 4: Leakage Controls and Artifact Masking")
    print("=" * 80)

    # 1. Validate lookahead features
    frame = pd.DataFrame({"feature": [1.0], "forward_1": [0.1]})
    report = validate_no_lookahead_features(
        frame,
        feature_metadata={
            "schema_version": "v1",
            "training_feature_columns": ["feature"],
        },
        target_column="forward_1",
        allowed_forward_columns=("forward_1",),
    )
    print(f"Lookahead validation severity: {report.severity}")

    # 2. Time-series splitting
    ts_frame = pd.DataFrame(
        {"value": range(20)},
        index=pd.date_range("2026-01-01", periods=20, freq="h", tz="UTC"),
    )
    split_result = enforce_time_split(
        ts_frame, train_fraction=0.5, validation_fraction=0.2
    )
    print(
        f"Train rows: {len(split_result.train)}, Val rows: {len(split_result.validation)}, Test rows: {len(split_result.test)}"
    )

    # 3. Artifact masking
    masked = mask_research_artifact({"password": "secret"})
    print(f"Masked secret value: {masked['password']}")


def main() -> None:
    """Run Research leakage usage example."""
    example_leakage()


if __name__ == "__main__":
    main()
