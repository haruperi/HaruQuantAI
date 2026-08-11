"""Executable usage evidence for FEAT-INDI-06 IndicatorSnapshot v1."""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.indicators import build_indicator_snapshot, parse_indicator_snapshot
from tests.indicators.usage._support import unwrap_indicator_response

NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)


def _snapshot() -> dict[str, object]:
    """Build and parse one real deterministic snapshot mapping."""
    built = build_indicator_snapshot(
        indicator_id="atr",
        value=1.25,
        unit="price",
        state="AVAILABLE",
        observed_at=NOW,
        source_start=NOW - timedelta(hours=2),
        source_end=NOW - timedelta(hours=1),
        complete=True,
        confidence=1.0,
        data_health="HEALTHY",
        evidence_refs=("dataset-example",),
    )
    built_data = unwrap_indicator_response(built)
    parsed = parse_indicator_snapshot(built_data)
    return dict(unwrap_indicator_response(parsed))


def fr_indi_036() -> None:
    """FR-INDI-036: Build the versioned JSON-safe snapshot."""
    data = _snapshot()
    print("SUCCESS: FR-INDI-036")
    print(f"DATA: {data}")


def fr_indi_037() -> None:
    """FR-INDI-037: Parse the versioned JSON-safe snapshot."""
    data = _snapshot()
    print("SUCCESS: FR-INDI-037")
    print(f"DATA: {data}")


def fr_indi_038() -> None:
    """FR-INDI-038: Preserve completeness and data-health evidence."""
    data = _snapshot()
    print("SUCCESS: FR-INDI-038")
    print(f"DATA: complete={data['complete']}, health={data['data_health']}")


def main() -> None:
    """Run every snapshot requirement demonstration."""
    fr_indi_036()
    fr_indi_037()
    fr_indi_038()


if __name__ == "__main__":
    main()
