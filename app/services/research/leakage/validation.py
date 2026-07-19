"""Evidence-based lookahead inspection for Research feature frames."""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast

import pandas as pd

from app.services.research.contracts import LeakageReport
from app.utils import logger
from app.utils.errors import ValidationError

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)

_FORWARD_TOKENS = ("forward", "future", "target", "label", "mfe", "mae")


def validate_no_lookahead_features(
    data: pd.DataFrame,
    *,
    feature_metadata: Mapping[str, JSONValue],
    target_column: str | None,
    allowed_forward_columns: tuple[str, ...] = (),
) -> LeakageReport:
    """Inspect declarations and names for suspected lookahead evidence.

    Args:
        data: Candidate feature frame.
        feature_metadata: Feature lineage and training-column declarations.
        target_column: Optional declared prediction target.
        allowed_forward_columns: Declared research labels that remain excluded from
            training features.

    Returns:
        Structured suspicion evidence without certifying absence of leakage.

    Raises:
        ValidationError: If frame or metadata is malformed.
    """
    logger.info("Inspecting Research features for lookahead risk")
    if not isinstance(data, pd.DataFrame) or data.empty:
        raise ValidationError("RES_INPUT_INVALID", "NONEMPTY_FEATURE_FRAME_REQUIRED")
    training = feature_metadata.get("training_feature_columns")
    if not isinstance(training, list) or any(
        not isinstance(item, str) for item in training
    ):
        raise ValidationError("RES_INPUT_INVALID", "TRAINING_COLUMNS_METADATA_REQUIRED")
    named = {
        column
        for column in data.columns
        if any(token in column.lower() for token in _FORWARD_TOKENS)
    }
    if target_column is not None:
        if target_column not in data:
            raise ValidationError("RES_INPUT_INVALID", "TARGET_COLUMN_MISSING")
        named.add(target_column)
    declared = set(allowed_forward_columns)
    training_set = set(training)
    unsafe = named & training_set
    severity = "high" if unsafe else ("medium" if named else "none")
    evidence: Mapping[str, JSONValue] = {
        "name_matches": cast("list[JSONValue]", sorted(named)),
        "unsafe_training_columns": cast("list[JSONValue]", sorted(unsafe)),
        "declared_forward_columns": cast("list[JSONValue]", sorted(declared)),
        "metadata_schema_version": feature_metadata.get("schema_version"),
    }
    recommendation = (
        "block publication and remove suspected training columns"
        if unsafe
        else "retain declared labels outside training features and review lineage"
    )
    sources = tuple(
        str(feature_metadata[key])
        for key in ("dataset_hash", "configuration_hash")
        if feature_metadata.get(key)
    )
    return LeakageReport(
        tuple(sorted(named)),
        severity,
        evidence,
        recommendation,
        tuple(sorted(declared)),
        target_column,
        sources,
    )


__all__ = ("validate_no_lookahead_features",)
