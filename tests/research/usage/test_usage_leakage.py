"""Runnable usage examples for Research leakage controls."""

import pandas as pd
from app.services.research.leakage import (
    enforce_time_split,
    mask_research_artifact,
    validate_no_lookahead_features,
)
from app.utils import logger


def test_usage_validation_validate_no_lookahead() -> None:
    """Inspect a safe declared feature set."""
    logger.debug("Running Research leakage-validation usage")
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
    assert report.severity == "medium"


def test_usage_splitting_enforce_time_split() -> None:
    """Create a chronological train/validation/test split."""
    logger.debug("Running Research split usage")
    frame = pd.DataFrame(
        {"value": range(20)},
        index=pd.date_range("2026-01-01", periods=20, freq="h", tz="UTC"),
    )
    assert (
        len(enforce_time_split(frame, train_fraction=0.5, validation_fraction=0.2).test)
        == 6
    )


def test_usage_masking_mask_research_artifact() -> None:
    """Mask a nested artifact before sharing."""
    logger.debug("Running Research masking usage")
    assert (
        mask_research_artifact(
            {"password": "secret"},  # pragma: allowlist secret
        )["password"]
        == "[REDACTED]"
    )
