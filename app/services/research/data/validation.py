"""Validation of canonical Data-owned market datasets for Research."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, cast

import numpy as np
import pandas as pd

from app.services.data import (
    is_data_error,
    is_market_dataset,
    to_ohlcv_dataframe,
)
from app.services.research.contracts import (
    DataQualityReport,
    ResearchResourceLimits,
    ResearchWarning,
)
from app.utils import get_logger

logger = get_logger(__name__)

_MIN_CONTINUITY_ROWS = 3
_BYTES_PER_MEBIBYTE = 1024 * 1024


class _MarketDataset(Protocol):
    """Opaque subset of Data dataset evidence consumed by Research."""

    record_count: int
    data_kind: str
    source_metadata: Mapping[str, str]
    request_id: str

    def model_dump(self, *, mode: str) -> Mapping[str, object]:
        """Return the canonical serialized dataset payload."""
        ...


def _enforce_memory_budget(
    frame: pd.DataFrame,
    limits: ResearchResourceLimits,
    *,
    allocation_multiplier: int,
) -> None:
    """Fail before work whose deterministic allocation estimate exceeds policy.

    Pandas and NumPy allocate outside Python's object allocator, so admission is
    based on deep frame bytes and a documented per-stage copy multiplier rather
    than an unverifiable process-wide memory claim.

    Args:
        frame: Input frame whose deep allocation is measurable.
        limits: Approved Research resource ceilings.
        allocation_multiplier: Maximum simultaneous frame-sized allocations.

    Raises:
        ValueError: If the estimated peak exceeds the approved memory budget.
    """
    estimated_peak = int(frame.memory_usage(index=True, deep=True).sum()) * max(
        allocation_multiplier, 1
    )
    approved_bytes = limits.memory_budget_mb * _BYTES_PER_MEBIBYTE
    if estimated_peak > approved_bytes:
        raise ValueError("RES_RESOURCE_LIMIT_EXCEEDED", "MEMORY_BUDGET_EXCEEDED")


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
    dataset: object, *, limits: ResearchResourceLimits
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
        ValueError: If the input contract or resource bound is invalid.
    """
    logger.info("Validating canonical dataset for Research")
    if not is_market_dataset(dataset):
        raise ValueError("RES_INPUT_INVALID", "MARKET_DATASET_REQUIRED")
    market_dataset = cast("_MarketDataset", dataset)
    if market_dataset.record_count > limits.max_rows:
        raise ValueError("RES_RESOURCE_LIMIT_EXCEEDED", "ROW_LIMIT_EXCEEDED")
    if market_dataset.data_kind != "bars" or market_dataset.record_count == 0:
        raise ValueError("RES_INPUT_INVALID", "NONEMPTY_BAR_DATASET_REQUIRED")
    try:
        # Data contracts are intentionally opaque outside their package root.
        frame = to_ohlcv_dataframe(dataset)  # type: ignore[arg-type]
    except Exception as error:
        if not is_data_error(error):
            raise
        logger.exception("Data projection failed during Research validation")
        raise ValueError("RES_INPUT_INVALID", "DATA_PROJECTION_FAILED") from error
    # Validation materializes numeric arrays plus boolean masks alongside the frame.
    _enforce_memory_budget(frame, limits, allocation_multiplier=3)
    fatal = _frame_findings(frame)
    if not market_dataset.source_metadata:
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
