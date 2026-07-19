"""Validation of canonical Data-owned market datasets for Research."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

from app.services.data import to_ohlcv_dataframe
from app.services.data.contracts import MarketDataset
from app.services.data.contracts.errors import DataError
from app.services.research.contracts import (
    DataQualityReport,
    ResearchResourceLimits,
    ResearchWarning,
)
from app.utils import logger
from app.utils.errors import ValidationError

_MIN_CONTINUITY_ROWS = 3


def _fatal(code: str, field: str) -> Mapping[str, str]:
    """Build one bounded fatal quality issue.

    Args:
        code: Machine-readable issue code.
        field: Affected field.

    Returns:
        Fatal issue mapping.
    """
    logger.debug("Building Research fatal quality issue")
    return {"code": code, "field": field}


def _frame_findings(frame: pd.DataFrame) -> list[Mapping[str, str]]:
    """Collect structural and numeric frame findings.

    Args:
        frame: Detached Data-owned analytical projection.

    Returns:
        Fatal issue mappings.
    """
    logger.debug("Checking Research frame quality")
    fatal: list[Mapping[str, str]] = []
    checks = (
        (
            not isinstance(frame.index, pd.DatetimeIndex) or frame.index.tz is None,
            "INVALID_TIMESTAMP_INDEX",
            "timestamp",
        ),
        (not frame.index.is_monotonic_increasing, "UNSORTED_TIMESTAMPS", "timestamp"),
        (frame.index.has_duplicates, "DUPLICATE_TIMESTAMPS", "timestamp"),
    )
    fatal.extend(_fatal(code, field) for failed, code, field in checks if failed)
    numeric = frame[["open", "high", "low", "close", "volume", "spread"]]
    if not np.isfinite(numeric.to_numpy(dtype="float64")).all():
        fatal.append(_fatal("NONFINITE_VALUE", "ohlcvs"))
    invalid_ohlc = (
        (frame["high"] < frame[["open", "close", "low"]].max(axis=1))
        | (frame["low"] > frame[["open", "close", "high"]].min(axis=1))
        | (frame["high"] < frame["low"])
    )
    numeric_checks = (
        (bool(invalid_ohlc.any()), "INVALID_OHLC", "ohlc"),
        (bool((frame["spread"] < 0).any()), "NEGATIVE_SPREAD", "spread"),
        (bool((frame["volume"] < 0).any()), "NEGATIVE_VOLUME", "volume"),
    )
    fatal.extend(
        _fatal(code, field) for failed, code, field in numeric_checks if failed
    )
    return fatal


def _continuity_warnings(frame: pd.DataFrame) -> tuple[ResearchWarning, ...]:
    """Return interval-continuity warnings.

    Args:
        frame: Detached Data-owned analytical projection.

    Returns:
        Zero or one continuity warning.
    """
    logger.debug("Checking Research timestamp continuity")
    if len(frame.index) < _MIN_CONTINUITY_ROWS:
        return ()
    differences = frame.index.to_series().diff().dropna()
    if bool(differences.eq(differences.iloc[0]).all()):
        return ()
    return (
        ResearchWarning(
            "IRREGULAR_INTERVALS",
            "Timestamp intervals are not uniform",
            "warning",
            "timestamp",
            {"distinct_intervals": int(differences.nunique())},
        ),
    )


def validate_dataset(
    dataset: MarketDataset, *, limits: ResearchResourceLimits
) -> DataQualityReport:
    """Validate one canonical bar dataset without mutating it.

    The Data-owned projection supplies a new UTC-indexed frame with float64
    ``open``, ``high``, ``low``, ``close``, ``volume``, and ``spread`` columns.
    Research checks ordering, continuity, OHLC relationships, finite values,
    spread, volume, and provenance. No rows are filled or removed.

    Args:
        dataset: Canonical Data-owned market dataset version 1.
        limits: Approved Research resource ceilings.

    Returns:
        Machine-readable quality evidence.

    Raises:
        ValidationError: If the input contract or resource bound is invalid.
    """
    logger.info("Validating canonical dataset for Research")
    if not isinstance(dataset, MarketDataset):
        raise ValidationError("RES_INPUT_INVALID", "MARKET_DATASET_REQUIRED")
    if dataset.record_count > limits.max_rows:
        raise ValidationError("RES_RESOURCE_LIMIT_EXCEEDED", "ROW_LIMIT_EXCEEDED")
    if dataset.data_kind != "bars" or dataset.record_count == 0:
        raise ValidationError("RES_INPUT_INVALID", "NONEMPTY_BAR_DATASET_REQUIRED")
    try:
        frame = to_ohlcv_dataframe(dataset)
    except DataError as error:
        logger.error("Data projection failed during Research validation")
        raise ValidationError("RES_INPUT_INVALID", "DATA_PROJECTION_FAILED") from error
    fatal = _frame_findings(frame)
    if not dataset.source_metadata:
        fatal.append(_fatal("MISSING_SOURCE_METADATA", "source_metadata"))
    checks = (
        "contract",
        "timestamps",
        "duplicates",
        "continuity",
        "ohlc",
        "spread",
        "volume",
        "finite",
        "provenance",
    )
    return DataQualityReport(tuple(fatal), _continuity_warnings(frame), checks, ())


__all__ = ("validate_dataset",)
