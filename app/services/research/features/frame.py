"""Assembly of canonical Research feature frames."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, cast

import pandas as pd

from app.composition.logging import get_logger
from app.services.indicators import (
    get_indicator_result_metadata,
    get_indicator_result_values,
)
from app.services.research.data.validation import _enforce_memory_budget
from app.services.research.features.calculations import (
    forward_returns,
    log_returns,
    rolling_hurst,
    simple_returns,
)

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.research.contracts import (
        FeatureConfig,
        PreparedDataset,
        ResearchResourceLimits,
    )

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)


def _attach_indicator(
    frame: pd.DataFrame, name: str, result: object
) -> tuple[pd.DataFrame, Mapping[str, JSONValue]]:
    """Attach one public IndicatorResult by timestamp.

    Args:
        frame: Detached Research feature frame.
        name: Caller-owned indicator input name.
        result: Public IndicatorResult v1.

    Returns:
        Updated frame and lineage evidence.

    Raises:
        ValueError: If the contract, index, or columns are incompatible.
    """
    logger.debug("Attaching public IndicatorResult to Research frame")
    metadata = get_indicator_result_metadata(result)
    if (
        metadata["contract_version"] != "v1"
        or metadata["schema_id"] != "indicators.indicator_series.v1"
    ):
        raise ValueError("RES_VERSION_INCOMPATIBLE", "INDICATOR_VERSION_INVALID")
    values = get_indicator_result_values(result)
    if not values.index.equals(frame.index):
        raise ValueError("RES_INPUT_INVALID", "INDICATOR_INDEX_MISMATCH")
    columns_value = metadata["output_columns"]
    if not isinstance(columns_value, tuple) or not all(
        isinstance(column, str) for column in columns_value
    ):
        raise ValueError("RES_INPUT_INVALID", "INDICATOR_COLUMNS_INVALID")
    columns = cast("tuple[str, ...]", columns_value)
    if set(columns) & set(frame.columns):
        raise ValueError("RES_INPUT_INVALID", "INDICATOR_COLUMN_COLLISION")
    output = frame.copy(deep=True)
    for column in columns:
        output[column] = values[column].to_numpy(copy=True)
    lineage: Mapping[str, JSONValue] = {
        "name": name,
        "indicator_id": str(metadata["indicator_id"]),
        "parameter_hash": str(metadata["parameter_hash"]),
        "input_checksum": str(
            cast("Mapping[str, object]", metadata["manifest"])["input_checksum"]
        ),
        "output_columns": list(columns),
    }
    return output, lineage


def build_research_feature_frame(
    prepared: PreparedDataset,
    *,
    indicator_results: Mapping[str, object],
    config: FeatureConfig,
    limits: ResearchResourceLimits,
) -> tuple[pd.DataFrame, Mapping[str, JSONValue]]:
    """Build a detached feature frame with lineage and leakage metadata.

        The output retains the prepared UTC index. Warm-up values remain NaN unless
        `
    an_policy='drop_warmup'``. Forward columns are recorded as research-only
        labels and are never included in ``training_feature_columns``.

    Args:
            prepared: Prepared Research dataset.
            indicator_results: Caller-supplied public IndicatorResult v1 values.
            config: Explicit feature windows and NaN policy.
            limits: Approved resource ceilings.

    Returns:
            Detached feature frame and JSON-compatible lineage metadata.

    Raises:
            ValueError: If inputs, dependencies, or resource bounds are invalid.
    """
    logger.info("Building canonical Research feature frame")
    if len(prepared.data) > limits.max_rows:
        raise ValueError("RES_RESOURCE_LIMIT_EXCEEDED", "ROW_LIMIT_EXCEEDED")
    # Feature assembly retains input, output, indicator, and forward-label frames.
    _enforce_memory_budget(prepared.data, limits, allocation_multiplier=4)
    if "close" not in prepared.data:
        raise ValueError("RES_INPUT_INVALID", "CLOSE_COLUMN_REQUIRED")
    frame = pd.DataFrame(index=prepared.data.index.copy())
    close = prepared.data["close"]
    frame["log_return"] = log_returns(close)
    frame["simple_return"] = simple_returns(close)
    if "hurst" in config.windows:
        window = config.windows["hurst"]
        frame[f"hurst_{window}"] = rolling_hurst(
            close, window=window, minimum_samples=min(window, 20)
        )
    indicator_lineage: list[Mapping[str, JSONValue]] = []
    for name, result in indicator_results.items():
        frame, lineage = _attach_indicator(frame, name, result)
        indicator_lineage.append(lineage)
    forward_columns: list[str] = []
    for horizon in config.forward_horizons:
        column = f"forward_return_{horizon}"
        frame[column] = forward_returns(
            close, horizon=horizon, mode="log", output_label=column
        )
        forward_columns.append(column)
    declared = set(config.allowed_forward_columns)
    if declared - set(forward_columns):
        raise ValueError("RES_INPUT_INVALID", "UNRESOLVED_FORWARD_DECLARATION")
    training_columns = tuple(
        column for column in frame.columns if column not in set(forward_columns)
    )
    if config.nan_policy == "drop_warmup":
        frame = frame.dropna(subset=list(training_columns))
    frame.attrs["research_only_columns"] = tuple(forward_columns)
    metadata: Mapping[str, JSONValue] = {
        "schema_version": "v1",
        "dataset_hash": prepared.dataset_hash,
        "configuration_hash": prepared.configuration_hash,
        "indicator_lineage": cast("list[JSONValue]", indicator_lineage),
        "research_only_forward_columns": cast("list[JSONValue]", forward_columns),
        "training_feature_columns": cast("list[JSONValue]", list(training_columns)),
        "nan_policy": config.nan_policy,
        "input_mutated": False,
    }
    return frame, metadata


__all__ = ("build_research_feature_frame",)
