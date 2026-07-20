"""Validation helpers for analysis-ready OHLCVS datasets.

Purpose:
    Validation helpers for analysis-ready OHLCVS datasets.

Classes:
    None.

Functions:
    _add_issue: Support internal add issue processing.
    _expected_frequency: Support internal expected frequency processing.
    validate_dataset: Run validate dataset processing.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.services.data.transforms import TimeframeManager
from app.services.utils.validators import (
    validate_duplicates,
    validate_gaps,
    validate_missing_timestamps,
    validate_price_sanity,
    validate_spread,
    validate_zero_volume,
)

from .models import CanonicalOHLCVSSchema, DataQualityReportModel, DatasetIssue


def _add_issue(
    report: DataQualityReportModel,
    *,
    code: str,
    severity: str,
    message: str,
    count: int = 0,
    **details,
) -> None:
    """Support internal add issue processing."""
    report.add_issue(
        DatasetIssue(
            code=code,
            severity=severity,
            message=message,
            count=count,
            details=details,
        )
    )


def _expected_frequency(timeframe: str | None) -> str | None:
    """Support internal expected frequency processing."""
    if not timeframe:
        return None
    return TimeframeManager.timeframe_to_frequency(timeframe)


def validate_dataset(
    df: pd.DataFrame,
    *,
    schema: CanonicalOHLCVSSchema | None = None,
    timeframe: str | None = None,
) -> DataQualityReportModel:
    """Validate schema, continuity, OHLC logic, duplicates, spread, and volume."""
    schema = schema or CanonicalOHLCVSSchema()
    report = DataQualityReportModel()

    report.add_check("schema")
    if not isinstance(df.index, pd.DatetimeIndex):
        _add_issue(
            report,
            code="missing_datetime_index",
            severity="fatal",
            message="Dataset must use a DatetimeIndex before analysis.",
        )
        return report

    for col in schema.price_columns:
        if col not in df.columns:
            _add_issue(
                report,
                code=f"missing_{col.lower()}",
                severity="fatal",
                message=f"Required price column '{col}' is missing.",
            )

    for col in (schema.volume, schema.spread):
        if col not in df.columns:
            _add_issue(
                report,
                code=f"missing_{col.lower()}",
                severity="warning",
                message=f"Optional input column '{col}' is missing and will be synthesized.",
            )

    report.add_check("ohlc_logic")
    if all(col in df.columns for col in (schema.high, schema.low)):
        invalid_high_low = int((df[schema.high] < df[schema.low]).sum())
        if invalid_high_low:
            _add_issue(
                report,
                code="invalid_high_low",
                severity="fatal",
                message="High must be greater than or equal to Low.",
                count=invalid_high_low,
            )

    all_valid, _, issues = validate_price_sanity(df, mark_invalid=False)
    if not all_valid:
        invalid_count = int(
            sum(
                int(issue.get("count", 0))
                for issue in issues
                if issue.get("type") == "price_sanity"
            )
        )
        _add_issue(
            report,
            code="invalid_ohlc",
            severity="warning",
            message="OHLC logical relationships are invalid.",
            count=invalid_count,
        )

    report.add_check("timestamp_continuity")
    expected_freq = _expected_frequency(timeframe)
    _, gaps = validate_gaps(df, expected_frequency=expected_freq)
    if gaps:
        total_missing = int(sum(max(0, int(g["expected_periods"]) - 1) for g in gaps))
        _add_issue(
            report,
            code="time_gaps_detected",
            severity="warning",
            message="Timestamp gaps were detected in the dataset.",
            count=len(gaps),
            missing_bars=total_missing,
        )

    missing_df, missing_info = validate_missing_timestamps(
        df,
        expected_frequency=expected_freq,
    )
    if missing_info:
        info = missing_info[0]
        _add_issue(
            report,
            code="missing_timestamps",
            severity="warning",
            message="Expected timestamps are missing from the dataset.",
            count=int(info.get("count", len(missing_df))),
            coverage=float(info.get("coverage", np.nan)),
        )

    report.add_check("duplicates")
    duplicates_df, duplicate_issues = validate_duplicates(df)
    if duplicate_issues:
        issue = duplicate_issues[0]
        _add_issue(
            report,
            code="duplicate_timestamps",
            severity="fatal",
            message="Duplicate timestamps were found.",
            count=int(issue.get("count", len(duplicates_df))),
        )

    report.add_check("spread")
    spread_stats, spread_issues = validate_spread(df)
    report.metadata["spread_stats"] = spread_stats
    for issue in spread_issues:
        _add_issue(
            report,
            code="spread_warning",
            severity="warning",
            message="Spread anomalies were detected.",
            count=int(issue.get("count", 0)),
            **{k: v for k, v in issue.items() if k not in {"type", "count"}},
        )

    report.add_check("volume")
    zero_volume_df, zero_volume_issues = validate_zero_volume(df)
    if zero_volume_issues:
        _add_issue(
            report,
            code="zero_volume",
            severity="warning",
            message="Zero-volume bars were detected.",
            count=len(zero_volume_df),
        )

    return report
