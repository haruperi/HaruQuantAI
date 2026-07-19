"""Unit tests for Research leakage evidence."""

import pandas as pd
from app.services.research.leakage import validate_no_lookahead_features
from app.utils import logger


def test_leakage_report_detects_forward_target() -> None:
    """Verify a forward label in training features blocks publication."""
    logger.debug("Testing Research forward-target detection")
    frame = pd.DataFrame({"feature": [1.0], "forward_return_5": [0.1]})
    report = validate_no_lookahead_features(
        frame,
        feature_metadata={
            "schema_version": "v1",
            "training_feature_columns": ["feature", "forward_return_5"],
        },
        target_column="forward_return_5",
        allowed_forward_columns=("forward_return_5",),
    )
    assert report.severity == "high"
