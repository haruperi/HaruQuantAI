"""Executable Research leakage usage example.

Demonstrates lookahead validation, chronological splitting, and artifact
masking.
"""

import sys
from pathlib import Path

import pandas as pd

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.research import (
    enforce_time_split,
    mask_research_artifact,
    validate_no_lookahead_features,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def fr_res_039() -> None:
    """FR-RES-039.

    Inspect feature metadata, names, targets, horizons, and declarations and
    return evidence/severity/recommendation without claiming proof of no
    leakage.
    """
    _header(
        "FR-RES-039. Inspect feature metadata, names, targets, horizons, and declarations and return evidence/severity/recommendation without claiming proof of no leakage."
    )
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
    print(f"FR-RES-039 severity={report.severity}")


def fr_res_040() -> None:
    """FR-RES-040.

    Split chronologically into non-overlapping train/validation/test frames
    with deterministic boundaries and split hash.
    """
    _header(
        "FR-RES-040. Split chronologically into non-overlapping train/validation/test frames with deterministic boundaries and split hash."
    )
    ts_frame = pd.DataFrame(
        {"value": range(20)},
        index=pd.date_range("2026-01-01", periods=20, freq="h", tz="UTC"),
    )
    split = enforce_time_split(ts_frame, train_fraction=0.5, validation_fraction=0.2)
    print(
        f"FR-RES-040 train={len(split.train)} "
        f"val={len(split.validation)} test={len(split.test)}"
    )


def fr_res_041() -> None:
    """FR-RES-041.

    Recursively mask sensitive, broker/account, and forbidden forward fields
    before sharing or serialization without mutating input.
    """
    _header(
        "FR-RES-041. Recursively mask sensitive, broker/account, and forbidden forward fields before sharing or serialization without mutating input."
    )
    masked = mask_research_artifact({"password": "secret", "data": {"api_key": "abc"}})
    print(f"FR-RES-041 masked_password={masked['password']}")


def main() -> None:
    """Run every Research leakage requirement demonstration in order."""
    print("Research Example 4: Leakage Controls and Artifact Masking")
    fr_res_039()
    fr_res_040()
    fr_res_041()


if __name__ == "__main__":
    main()
