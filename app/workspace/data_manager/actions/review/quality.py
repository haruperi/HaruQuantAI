"""Data quality evaluation, gap detection, and health metric auditing.

Description:
    Diagnostic auditing service for historical market data series within the
    Data Manager workspace, mirroring SQX DataManagerActions review quality.
    Analyzes OHLCV bar sequences for price envelope geometry anomalies, zero or
    negative prices, duplicate timestamps, and unexpected chronological gap
    intervals. Calculates a normalized health quality score [0.0, 1.0] and produces
    structured data quality reports for dataset cataloging.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Audit, diagnose, and score historical market data
    quality in the Data Manager workspace.

Key Capabilities:
    - FR-DATA-QUALITY-METRICS: Calculate bar health, gaps, duplicates, and
      quality score.
      Associated: `[DataQualityInspector.inspect_series()]`
      Logging: Emits INFO on quality analysis completion.

Python API Usage:
    ```python
    from app.workspace.data_manager.actions.review.quality import DataQualityInspector
    from app.workspace.data_manager.data import BarRecord

    inspector = DataQualityInspector()
    report = inspector.inspect_series(bars, expected_interval_seconds=60)
    print(f"Quality score: {report.quality_score:.2f} (Gaps: {report.gap_bars})")
    ```

CLI Usage:
    ```bash
    python -m app.workspace.data_manager.actions.review.quality \
        --file dataset.csv --step 60
    ```
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from app.host.logging import get_logger
from app.workspace.data_manager.data import BarRecord

logger = get_logger(__name__)

DEFAULT_INTERVAL_SECONDS = 60
MAX_REPORTED_ISSUES = 5
MAX_GAP_INFLATION = 100
GAP_TOLERANCE_MULTIPLIER = 1.5


class DataQualityReport(BaseModel):
    """Authoritative quality audit report for a market data series."""

    model_config = ConfigDict(frozen=True)

    total_bars: int = Field(ge=0, description="Total bars analyzed")
    valid_bars: int = Field(ge=0, description="Bars satisfying all criteria")
    bad_bars: int = Field(ge=0, description="Bars with invalid geometry or prices")
    duplicate_bars: int = Field(ge=0, description="Bars with duplicate timestamps")
    gap_bars: int = Field(ge=0, description="Estimated missing bars across gaps")
    quality_score: float = Field(
        ge=0.0, le=1.0, description="Normalized quality metric [0.0 - 1.0]"
    )
    issues: list[str] = Field(
        default_factory=list, description="Diagnostic issue messages"
    )


class DataQualityInspector:
    """Audits market data series quality metrics and flags anomalies."""

    def inspect_series(
        self,
        bars: list[BarRecord],
        expected_interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
    ) -> DataQualityReport:
        """Analyze a list of bars and compute authoritative quality metrics.

        Fires FR-DATA-QUALITY-METRICS.
        """
        if not bars:
            logger.info(
                "FR-DATA-QUALITY-METRICS: Inspected empty series (score=0.0)",
                extra={"total_bars": 0, "fr_id": "FR-DATA-QUALITY-METRICS"},
            )
            return DataQualityReport(
                total_bars=0,
                valid_bars=0,
                bad_bars=0,
                duplicate_bars=0,
                gap_bars=0,
                quality_score=0.0,
                issues=["Series is empty."],
            )

        total_bars = len(bars)
        bad_bars = 0
        duplicate_bars = 0
        gap_bars = 0
        issues: list[str] = []

        seen_timestamps: set[str] = set()
        prev_dt: datetime | None = None

        for idx, bar in enumerate(bars):
            if bar.timestamp_utc in seen_timestamps:
                duplicate_bars += 1
            else:
                seen_timestamps.add(bar.timestamp_utc)

            if not bar.is_valid_geometry() or any(
                p <= 0.0 for p in (bar.open, bar.high, bar.low, bar.close)
            ):
                bad_bars += 1
                if len(issues) < MAX_REPORTED_ISSUES:
                    issues.append(
                        f"Bad bar geometry at {bar.timestamp_utc} (idx {idx})"
                    )

            try:
                dt = datetime.fromisoformat(bar.timestamp_utc)
                gap_count = self._evaluate_gap(
                    prev_dt, dt, expected_interval_seconds, issues
                )
                gap_bars += gap_count
                prev_dt = dt
            except ValueError:
                bad_bars += 1

        valid_bars = max(0, total_bars - bad_bars - duplicate_bars)
        quality_score = self._compute_score(
            total_bars, bad_bars, duplicate_bars, gap_bars
        )

        logger.info(
            "FR-DATA-QUALITY-METRICS: Inspected %d bars (score=%.4f, bad=%d)",
            total_bars,
            quality_score,
            bad_bars,
            extra={
                "total_bars": total_bars,
                "score": quality_score,
                "bad_bars": bad_bars,
                "duplicate_bars": duplicate_bars,
                "gap_bars": gap_bars,
                "fr_id": "FR-DATA-QUALITY-METRICS",
            },
        )

        return DataQualityReport(
            total_bars=total_bars,
            valid_bars=valid_bars,
            bad_bars=bad_bars,
            duplicate_bars=duplicate_bars,
            gap_bars=gap_bars,
            quality_score=round(quality_score, 4),
            issues=issues,
        )

    @staticmethod
    def _evaluate_gap(
        prev_dt: datetime | None,
        dt: datetime,
        expected_interval_seconds: int,
        issues: list[str],
    ) -> int:
        """Estimate missing gap bars between consecutive timestamps."""
        if prev_dt is None:
            return 0
        delta_sec = (dt - prev_dt).total_seconds()
        if delta_sec < 0:
            if len(issues) < MAX_REPORTED_ISSUES:
                issues.append(f"Chronological inversion at {dt.isoformat()}")
            return 0
        threshold = expected_interval_seconds * GAP_TOLERANCE_MULTIPLIER
        if delta_sec > threshold:
            missing = int(
                (delta_sec - expected_interval_seconds) / expected_interval_seconds
            )
            return min(missing, MAX_GAP_INFLATION)
        return 0

    @staticmethod
    def _compute_score(
        total_bars: int, bad_bars: int, duplicate_bars: int, gap_bars: int
    ) -> float:
        """Calculate bounded quality metric in range [0.0, 1.0]."""
        denominator = total_bars + gap_bars
        if denominator <= 0:
            return 1.0
        penalty = (bad_bars * 2.0 + duplicate_bars + gap_bars * 0.1) / denominator
        return max(0.0, min(1.0, 1.0 - penalty))


def main() -> int:
    """CLI tool for auditing data quality of CSV market files."""
    parser = argparse.ArgumentParser(description="Audit market data file quality")
    parser.add_argument("--file", required=True, help="Path to CSV data file")
    parser.add_argument(
        "--step", type=int, default=60, help="Expected bar interval in seconds"
    )
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: file not found: {file_path}")
        return 1

    bars: list[BarRecord] = []
    with file_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                bars.append(
                    BarRecord(
                        timestamp_utc=r["timestamp"],
                        open=float(r["open"]),
                        high=float(r["high"]),
                        low=float(r["low"]),
                        close=float(r["close"]),
                        volume=float(r.get("volume", 0.0)),
                    )
                )
            except KeyError, ValueError:
                continue

    inspector = DataQualityInspector()
    report = inspector.inspect_series(bars, expected_interval_seconds=args.step)
    print(f"Audited {report.total_bars} bars:")
    print(f"  Quality Score:  {report.quality_score:.2%}")
    print(f"  Valid Bars:     {report.valid_bars}")
    print(f"  Bad Bars:       {report.bad_bars}")
    print(f"  Duplicate Bars: {report.duplicate_bars}")
    print(f"  Gap Bars:       {report.gap_bars}")
    if report.issues:
        print("  Issues noted:")
        for iss in report.issues:
            print(f"    - {iss}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
