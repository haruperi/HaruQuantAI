"""WF-RES-003: build features, inspect leakage, and split chronologically."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.research import (
    build_research_feature_frame,
    create_research_value,
    enforce_time_split,
    validate_no_lookahead_features,
)
from tests.research.usage.workflows._support import limits, prepared_dataset

WORKFLOW_ID = "WF-RES-003"
STAGES = (
    "Receive prepared genuine MT5 data and explicit feature configuration.",
    "Build the Research feature frame and declared lineage.",
    "Validate that training inputs contain no forbidden forward fields.",
    "Enforce deterministic chronological train, validation, and test splits.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Execute the documented leakage-safe feature workflow."""
    print(f"{WORKFLOW_ID} — Build Leakage-Safe Feature Frame and Time Splits")
    print("INPUT BOUNDARY — PreparedDataset plus explicit FeatureConfig")

    # Stage 1 — Receive prepared genuine MT5 data and explicit feature configuration.
    _stage(1)
    prepared = prepared_dataset()
    config = create_research_value(
        "FeatureConfig", {"sma": 2}, (1,), ("forward_return_1",), "preserve"
    )

    # Stage 2 — Build the Research feature frame and declared lineage.
    _stage(2)
    frame, metadata = build_research_feature_frame(
        prepared,
        indicator_results={},
        config=config,
        limits=limits(),
    )

    # Stage 3 — Validate that training inputs contain no forbidden forward fields.
    _stage(3)
    leakage = validate_no_lookahead_features(
        frame,
        feature_metadata=metadata,
        target_column="forward_return_1",
        allowed_forward_columns=("forward_return_1",),
    )

    # Stage 4 — Enforce deterministic chronological train, validation, and test splits.
    _stage(4)
    split = enforce_time_split(frame, train_fraction=0.6, validation_fraction=0.2)
    print("Leakage severity:", leakage.severity)
    print(
        "OUTPUT BOUNDARY — feature frame, LeakageReport, TimeSplitResult:",
        split.split_hash,
    )


if __name__ == "__main__":
    main()
