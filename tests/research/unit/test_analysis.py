"""Unit tests for Research seasonality analysis (FR-RES-073 to 074)."""

from datetime import time

import pandas as pd
import pytest
from app.services.research import (
    create_research_value,
    run_seasonality,
)
from app.utils import get_logger

logger = get_logger(__name__)

_HASH = "e" * 64


def _config() -> object:
    """Build a session policy covering all 24 hours across two sessions."""
    return create_research_value(
        "SessionConfig",
        "UTC",
        {
            "london": (time(0), time(12)),
            "asian": (time(12), time(0)),
        },
        ("london", "asian"),
    )


def _limits() -> object:
    """Build approved resource ceilings."""
    return create_research_value("ResearchResourceLimits", 500_000, 600.0, 52_428_800)


def _prepared(rows: int = 30) -> object:
    """Build a PreparedDataset spanning london and asian hours."""
    idx = pd.date_range("2026-01-01", periods=rows, freq="h", tz="UTC")
    close = pd.Series(
        [100.0 + i * 0.5 if i % 3 else 100.0 - i * 0.3 for i in range(rows)],
        index=idx,
        dtype="float64",
    )
    frame = pd.DataFrame({"close": close}, index=idx)
    return create_research_value(
        "PreparedDataset",
        frame,
        "v1",
        create_research_value("DataQualityReport", (), (), ("schema",), ()),
        _HASH,
        _HASH,
        ("fixture",),
    )


def test_filters_reject_invalid_month() -> None:
    """FR-RES-073: month 13 fails closed."""
    logger.debug("Testing Research filter validation")
    with pytest.raises(ValueError, match="INVALID_MONTH_FILTER"):
        create_research_value("SeasonalityFilters", months=(13,))


def test_filters_accept_valid_ranges() -> None:
    """FR-RES-073: valid ranges construct successfully."""
    filters = create_research_value(
        "SeasonalityFilters",
        years=(2026,),
        months=(1, 2),
        weekdays=(0, 1),
        hours=(8, 9),
    )
    assert filters.years == (2026,)


def _prepared_two_session() -> object:
    """Build a PreparedDataset with a rich london block and a sparse asian tail."""
    # 16 london hourly rows (hours 0-15 are all london 0-12... no, 12-23 asian).
    # Use hours 0-11 (london) x2 = 24 rows + 1 asian hour-12 row = 25 rows.
    day1 = pd.date_range("2026-01-01 00:00", periods=12, freq="h", tz="UTC")
    day2 = pd.date_range("2026-01-02 00:00", periods=12, freq="h", tz="UTC")
    extra = pd.DatetimeIndex(["2026-01-02T12:00:00Z"])
    idx = day1.append(day2).append(extra)
    close = pd.Series([100.0 + i * 0.5 for i in range(25)], index=idx, dtype="float64")
    frame = pd.DataFrame({"close": close}, index=idx)
    return create_research_value(
        "PreparedDataset",
        frame,
        "v1",
        create_research_value("DataQualityReport", (), (), ("schema",), ()),
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
        filters=create_research_value("SeasonalityFilters"),
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
        filters=create_research_value("SeasonalityFilters"),
        limits=_limits(),
    )
    assert result["schema_version"] == "v1"
    assert isinstance(result["sessions"], list)


def test_seasonality_rejects_oversized_input() -> None:
    """FR-RES-074: oversized input fails closed."""
    with pytest.raises(ValueError, match="ROW_LIMIT_EXCEEDED"):
        run_seasonality(
            _prepared(),
            sessions=_config(),
            filters=create_research_value("SeasonalityFilters"),
            limits=create_research_value("ResearchResourceLimits", 5, 10.0, 1024),
        )


@pytest.mark.parametrize(
    ("values", "message"),
    [
        ({"years": (1969,)}, "INVALID_YEAR_FILTER"),
        ({"weekdays": (7,)}, "INVALID_WEEKDAY_FILTER"),
        ({"hours": (24,)}, "INVALID_HOUR_FILTER"),
        ({"sessions": (" london",)}, "INVALID_SESSION_FILTER"),
    ],
)
def test_filters_reject_every_invalid_range(
    values: dict[str, tuple[object, ...]],
    message: str,
) -> None:
    """Cover every closed filter vocabulary."""
    with pytest.raises(ValueError, match=message):
        create_research_value("SeasonalityFilters", **values)


def test_seasonality_applies_all_filters_and_reports_insufficiency() -> None:
    """Cover calendar/session filters and the declared ADR insufficiency output."""
    result = run_seasonality(
        _prepared(rows=50),
        sessions=_config(),
        filters=create_research_value(
            "SeasonalityFilters",
            years=(2026,),
            months=(1,),
            weekdays=(3,),
            hours=(0, 1),
            sessions=("london",),
        ),
        limits=_limits(),
    )
    assert result["sessions"] == []
    assert result["warnings"][0]["code"] == "INSUFFICIENT_SAMPLES"
