"""Executable Research seasonality usage example.

Demonstrates session resolution, payload, tagging, filters, and seasonality
analysis.
"""

import sys
from datetime import time
from pathlib import Path
from typing import Any

import pandas as pd

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.research import (
    active_sessions_for_hour,
    create_research_value,
    run_seasonality,
    session_hours_payload,
    session_label_for_hour,
    tag_sessions,
)

_HASH = "e" * 64


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"SUCCESS: {title}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"SUCCESS: {title}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def _config() -> object:
    """Build a two-session policy with a documented overlap."""
    return create_research_value(
        "SessionConfig",
        "UTC",
        {
            "london": (time(8), time(17)),
            "new_york": (time(13), time(22)),
        },
        ("london", "new_york"),
    )


def _prepared() -> object:
    """Build a PreparedDataset spanning multiple sessions."""
    idx = pd.date_range("2026-01-05", periods=48, freq="h", tz="UTC")
    close = pd.Series([100.0 + i * 0.3 for i in range(48)], index=idx, dtype="float64")
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


def fr_res_069() -> None:
    """FR-RES-069: Return every configured session active for a timezone-aware
    hour using canonical overlap precedence."""
    _header(
        "FR-RES-069: Return every configured session active for a timezone-aware hour using canonical overlap precedence."
    )
    active = active_sessions_for_hour(14, config=_config())
    print(f"FR-RES-069 active_sessions_at_14={active}")


def fr_res_070() -> None:
    """FR-RES-070: Return the deterministic primary session label for an hour
    while preserving overlap evidence."""
    _header(
        "FR-RES-070: Return the deterministic primary session label for an hour while preserving overlap evidence."
    )
    label = session_label_for_hour(14, config=_config())
    print(f"FR-RES-070 primary_label_at_14={label}")


def fr_res_071() -> None:
    """FR-RES-071: Return a machine-readable payload of timezone, windows,
    order, overlaps, and schema version."""
    _header(
        "FR-RES-071: Return a machine-readable payload of timezone, windows, order, overlaps, and schema version."
    )
    payload = session_hours_payload(config=_config())
    print(f"FR-RES-071 schema_version={payload['schema_version']}")


def fr_res_072() -> None:
    """FR-RES-072: Add session labels to a copied timezone-aware frame and
    record DST/unmatched warnings without changing row order."""
    _header(
        "FR-RES-072: Add session labels to a copied timezone-aware frame and record DST/unmatched warnings without changing row order."
    )
    idx = pd.date_range("2026-01-05", periods=24, freq="h", tz="UTC")
    data = pd.DataFrame({"close": range(24)}, index=idx)
    tagged, warnings = tag_sessions(data, config=_config())
    print(f"FR-RES-072 tagged_rows={len(tagged)} warnings={len(warnings)}")


def fr_res_073() -> None:
    """FR-RES-073: Define immutable optional calendar, session, symbol, and hour
    filters without embedding session definitions."""
    _header(
        "FR-RES-073: Define immutable optional calendar, session, symbol, and hour filters without embedding session definitions."
    )
    filters = create_research_value(
        "SeasonalityFilters", years=(2026,), months=(1,), hours=(8, 9, 14)
    )
    print(f"FR-RES-073 filter_hours={filters.hours}")


def fr_res_074() -> None:
    """FR-RES-074: Compute calendar/session/hour summaries, sparse-bucket
    warnings, opportunity windows, and extremes."""
    _header(
        "FR-RES-074: Compute calendar/session/hour summaries, sparse-bucket warnings, opportunity windows, and extremes."
    )
    result = run_seasonality(
        _prepared(),
        sessions=_config(),
        filters=create_research_value("SeasonalityFilters"),
        limits=create_research_value(
            "ResearchResourceLimits", 500_000, 600.0, 52_428_800
        ),
    )
    print(f"FR-RES-074 row_count={result['row_count']}")


def main() -> None:
    """Run Research seasonality usage example."""
    _feature_header(
        "FEATURE: FEAT-RES-08 — seasonality/ — Sessions and Seasonality\n\n"
        "Purpose: Tag timezone-aware market session boundaries and analyze seasonal opportunity patterns.\n\n"
        "Module flow:\n"
        "-> Stage 1: UTC session timestamp tagging\n-> Stage 2: Day-of-week and hour-of-day return distribution profiling\n-> Stage 3: Seasonality opportunity report rendering"
    )

    fr_res_069()
    fr_res_070()
    fr_res_071()
    fr_res_072()
    fr_res_073()
    fr_res_074()


if __name__ == "__main__":
    main()
