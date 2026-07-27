"""Unit tests for Research seasonality analysis (FR-RES-073 to 074)."""

from datetime import time

import pandas as pd
import pytest
from app.services.research import (
    DataQualityReport,
    PreparedDataset,
    ResearchResourceLimits,
    SessionConfig,
)
from app.services.research.seasonality import (
    SeasonalityFilters,
    run_seasonality,
)
from app.utils import ValidationError, logger

_HASH = "e" * 64


def _config() -> SessionConfig:
    """Build a session policy covering all 24 hours across two sessions."""
    return SessionConfig(
        "UTC",
        {
            "london": (time(0), time(12)),
            "asian": (time(12), time(0)),
        },
        ("london", "asian"),
    )


def _limits() -> ResearchResourceLimits:
    """Build approved resource ceilings."""
    return ResearchResourceLimits(500_000, 600.0, 52_428_800)


def _prepared(rows: int = 30) -> PreparedDataset:
    """Build a PreparedDataset spanning london and asian hours."""
    idx = pd.date_range("2026-01-01", periods=rows, freq="h", tz="UTC")
    close = pd.Series(
        [100.0 + i * 0.5 if i % 3 else 100.0 - i * 0.3 for i in range(rows)],
        index=idx,
        dtype="float64",
    )
    frame = pd.DataFrame({"close": close}, index=idx)
    return PreparedDataset(
        frame,
        "v1",
        DataQualityReport((), (), ("schema",), ()),
        _HASH,
        _HASH,
        ("fixture",),
    )


def test_filters_reject_invalid_month() -> None:
    """FR-RES-073: month 13 fails closed."""
    logger.debug("Testing Research filter validation")
    with pytest.raises(ValidationError, match="INVALID_MONTH_FILTER"):
        SeasonalityFilters(months=(13,))


def test_filters_accept_valid_ranges() -> None:
    """FR-RES-073: valid ranges construct successfully."""
    filters = SeasonalityFilters(
        years=(2026,), months=(1, 2), weekdays=(0, 1), hours=(8, 9)
    )
    assert filters.years == (2026,)


def _prepared_two_session() -> PreparedDataset:
    """Build a PreparedDataset with a rich london block and a sparse asian tail."""
    # 16 london hourly rows (hours 0-15 are all london 0-12... no, 12-23 asian).
    # Use hours 0-11 (london) x2 = 24 rows + 1 asian hour-12 row = 25 rows.
    day1 = pd.date_range("2026-01-01 00:00", periods=12, freq="h", tz="UTC")
    day2 = pd.date_range("2026-01-02 00:00", periods=12, freq="h", tz="UTC")
    extra = pd.DatetimeIndex(["2026-01-02T12:00:00Z"])
    idx = day1.append(day2).append(extra)
    close = pd.Series([100.0 + i * 0.5 for i in range(25)], index=idx, dtype="float64")
    frame = pd.DataFrame({"close": close}, index=idx)
    return PreparedDataset(
        frame,
        "v1",
        DataQualityReport((), (), ("schema",), ()),
        _HASH,
        _HASH,
        ("fixture",),
    )


def test_seasonality_warns_sparse_bucket() -> None:
    """FR-RES-074: sparse buckets produce SPARSE_BUCKET warnings."""
    logger.debug("Testing Research sparse-bucket warning")
    # 25 rows: 24 london (hours 0-11 twice) + 1 asian (hour 12). The asian
    # bucket has a single row -> 1 return, below the minimum sample count.
    result = run_seasonality(
        _prepared_two_session(),
        sessions=_config(),
        filters=SeasonalityFilters(),
        limits=_limits(),
    )
    warnings = result["warnings"]
    assert isinstance(warnings, list)
    codes = [warning["code"] for warning in warnings if isinstance(warning, dict)]
    assert "SPARSE_BUCKET" in codes


def test_seasonality_returns_versioned_evidence() -> None:
    """FR-RES-074: result is versioned and advisory."""
    result = run_seasonality(
        _prepared(rows=50),
        sessions=_config(),
        filters=SeasonalityFilters(),
        limits=_limits(),
    )
    assert result["schema_version"] == "v1"
    assert isinstance(result["sessions"], list)


def test_seasonality_rejects_oversized_input() -> None:
    """FR-RES-074: oversized input fails closed."""
    with pytest.raises(ValidationError, match="ROW_LIMIT_EXCEEDED"):
        run_seasonality(
            _prepared(),
            sessions=_config(),
            filters=SeasonalityFilters(),
            limits=ResearchResourceLimits(5, 10.0, 1024),
        )
