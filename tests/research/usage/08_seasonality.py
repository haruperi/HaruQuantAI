"""Executable Research seasonality usage example.

Demonstrates session resolution, payload, tagging, filters, and seasonality
analysis.
"""

import sys
from datetime import time
from pathlib import Path

import pandas as pd

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.research import (
    DataQualityReport,
    PreparedDataset,
    ResearchResourceLimits,
    SessionConfig,
)
from app.services.research.seasonality import (
    SeasonalityFilters,
    active_sessions_for_hour,
    run_seasonality,
    session_hours_payload,
    session_label_for_hour,
    tag_sessions,
)

_HASH = "e" * 64


def _config() -> SessionConfig:
    """Build a two-session policy with a documented overlap."""
    return SessionConfig(
        "UTC",
        {
            "london": (time(8), time(17)),
            "new_york": (time(13), time(22)),
        },
        ("london", "new_york"),
    )


def _prepared() -> PreparedDataset:
    """Build a PreparedDataset spanning multiple sessions."""
    idx = pd.date_range("2026-01-05", periods=48, freq="h", tz="UTC")
    close = pd.Series([100.0 + i * 0.3 for i in range(48)], index=idx, dtype="float64")
    frame = pd.DataFrame({"close": close}, index=idx)
    return PreparedDataset(
        frame,
        "v1",
        DataQualityReport((), (), ("schema",), ()),
        _HASH,
        _HASH,
        ("fixture",),
    )


def fr_res_069() -> None:
    """FR-RES-069: Return every configured session active for a timezone-aware
    hour using canonical overlap precedence."""
    print("=" * 80)
    print("Research Example 8: Sessions and Seasonality")
    print("=" * 80)
    active = active_sessions_for_hour(14, config=_config())
    print(f"FR-RES-069 active_sessions_at_14={active}")


def fr_res_070() -> None:
    """FR-RES-070: Return the deterministic primary session label for an hour
    while preserving overlap evidence."""
    label = session_label_for_hour(14, config=_config())
    print(f"FR-RES-070 primary_label_at_14={label}")


def fr_res_071() -> None:
    """FR-RES-071: Return a machine-readable payload of timezone, windows,
    order, overlaps, and schema version."""
    payload = session_hours_payload(config=_config())
    print(f"FR-RES-071 schema_version={payload['schema_version']}")


def fr_res_072() -> None:
    """FR-RES-072: Add session labels to a copied timezone-aware frame and
    record DST/unmatched warnings without changing row order."""
    idx = pd.date_range("2026-01-05", periods=24, freq="h", tz="UTC")
    data = pd.DataFrame({"close": range(24)}, index=idx)
    tagged, warnings = tag_sessions(data, config=_config())
    print(f"FR-RES-072 tagged_rows={len(tagged)} warnings={len(warnings)}")


def fr_res_073() -> None:
    """FR-RES-073: Define immutable optional calendar, session, symbol, and hour
    filters without embedding session definitions."""
    filters = SeasonalityFilters(years=(2026,), months=(1,), hours=(8, 9, 14))
    print(f"FR-RES-073 filter_hours={filters.hours}")


def fr_res_074() -> None:
    """FR-RES-074: Compute calendar/session/hour summaries, sparse-bucket
    warnings, opportunity windows, and extremes."""
    result = run_seasonality(
        _prepared(),
        sessions=_config(),
        filters=SeasonalityFilters(),
        limits=ResearchResourceLimits(500_000, 600.0, 52_428_800),
    )
    print(f"FR-RES-074 row_count={result['row_count']}")


def main() -> None:
    """Run Research seasonality usage example."""
    fr_res_069()
    fr_res_070()
    fr_res_071()
    fr_res_072()
    fr_res_073()
    fr_res_074()


if __name__ == "__main__":
    main()
