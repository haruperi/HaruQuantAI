"""Historical market data quality inspector, gap detector, and score engine.

Description:
    Provides automated quality inspection algorithms for OHLCV time-series
    data, detecting chronological gaps (`GAP_DETECTED`), weekend bars (`WEEKEND_BAR`),
    non-positive prices (`NON_POSITIVE_PRICE`), OHLC envelope violations
    (`OHLC_ENVELOPE_VIOLATION`), duplicate timestamps (`DUPLICATE_TIMESTAMP`), and
    abnormal price spikes (`PRICE_SPIKE`). Computes deterministic quality scores
    and persists inspection reports in the `datamgr_quality` database table.

Purpose:
    FEAT-DATAMGR-QUALITY: Market data quality inspection, gap detection,
    and scoring.

Key Capabilities:
    - FR-DATAMGR-QUALITY-INSPECTION: Scan OHLCV series for anomalies and
      envelope errors.
      Associated: `DataQualityInspector.inspect_dataframe()`
      Logging: Emits DEBUG on scanning bar chunks and identifying anomalies.
    - FR-DATAMGR-QUALITY-SCORE-AND-PERSISTENCE: Calculate scores and save
      quality reports.
      Associated: `DataQualityInspector.inspect_dataset()`
      Logging: Emits INFO on completing quality report and updating dataset
      score.
    - FR-DATAMGR-QUALITY-SUMMARY-AND-DETAILS: Provide summary metrics and
      paginated anomalies.
      Associated: `DataQualityInspector.get_quality_summary()`,
      `DataQualityInspector.get_quality_details()`
      Logging: Emits DEBUG when serving quality summary and anomaly slices.

Python API Usage:
    ```python
    from app.workspace.data_manager.actions.review.quality import DataQualityInspector

    inspector = DataQualityInspector()
    report = inspector.inspect_dataset("file:EURUSD")
    print(
        f"Quality score: {report.quality_score * 100:.1f}% "
        f"({len(report.anomalies)} anomalies)"
    )
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.actions.review.quality
    ```
"""

from __future__ import annotations

import json
import math
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
from app.host.logging import get_logger
from app.host.persistence.create import create_schema, insert_row
from app.host.persistence.delete import delete_rows
from app.host.persistence.read import read_rows, resolve_connection
from app.host.persistence.update import update_row_by_pk
from app.workspace.data_manager.data import DataManagerDataService

__all__ = [
    "DataQualityInspector",
    "QualityAnomaly",
    "QualityReport",
]

logger = get_logger(__name__)

INSPECTION_FR = "FR-DATAMGR-QUALITY-INSPECTION"
SCORE_PERSISTENCE_FR = "FR-DATAMGR-QUALITY-SCORE-AND-PERSISTENCE"
SUMMARY_DETAILS_FR = "FR-DATAMGR-QUALITY-SUMMARY-AND-DETAILS"

SECONDS_PER_MINUTE = 60.0
SECONDS_PER_HOUR = 3600.0
SECONDS_PER_DAY = 86400.0
SECONDS_PER_WEEK = 604800.0
MAX_WEEKEND_GAP_SECONDS = 259200.0
GAP_MULTIPLIER_THRESHOLD = 1.5
WEEKEND_DAY_FRIDAY = 4
WEEKEND_DAY_SATURDAY = 5
WEEKEND_DAY_SUNDAY = 6
WEEKEND_DAYS = (WEEKEND_DAY_SATURDAY, WEEKEND_DAY_SUNDAY)
ISO_MIN_STR_LENGTH = 10
WEIGHT_CRITICAL_PENALTY = 3
WEIGHT_MAJOR_PENALTY = 2
WEIGHT_MINOR_PENALTY = 1


def _parse_iso_timestamp(ts_str: str) -> datetime | None:
    """Parse timestamp string into timezone-aware datetime."""
    try:
        dt = datetime.fromisoformat(ts_str)
        return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
    except ValueError, TypeError:
        return None


def _timeframe_to_seconds(tf: str) -> float:
    """Convert timeframe code to duration in seconds."""
    clean = tf.strip().upper()
    if not clean or clean == "TICK":
        return 0.0
    unit = clean[0]
    val_str = clean[1:]
    try:
        val = int(val_str) if val_str else 1
    except ValueError:
        val = 1
    multiplier = SECONDS_PER_MINUTE
    if unit == "S":
        multiplier = 1.0
    elif unit == "M":
        multiplier = SECONDS_PER_MINUTE
    elif unit == "H":
        multiplier = SECONDS_PER_HOUR
    elif unit == "D":
        multiplier = SECONDS_PER_DAY
    elif unit == "W":
        multiplier = SECONDS_PER_WEEK
    return float(val) * multiplier


@dataclass(frozen=True)
class QualityAnomaly:
    """Represents a single detected time-series anomaly."""

    index: int
    timestamp: str
    code: str
    severity: str
    description: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert anomaly to dictionary representation."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "code": self.code,
            "severity": self.severity,
            "description": self.description,
            "details": self.details,
        }


@dataclass(frozen=True)
class QualityReport:
    """Represents the complete quality inspection report for a dataset."""

    report_id: str
    dataset_id: str
    quality_score: float
    total_records: int
    anomaly_counts: dict[str, int]
    anomalies: list[QualityAnomaly]
    evaluated_at_utc: str

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary representation."""
        return {
            "report_id": self.report_id,
            "dataset_id": self.dataset_id,
            "quality_score": self.quality_score,
            "total_records": self.total_records,
            "anomaly_counts": self.anomaly_counts,
            "anomalies": [a.to_dict() for a in self.anomalies],
            "evaluated_at_utc": self.evaluated_at_utc,
        }


def _inspect_bar(
    *,
    idx: int,
    ts_str: str,
    op: float,
    hi: float,
    lo: float,
    cl: float,
    prev_ts: str | None,
    prev_close: float | None,
    spike_threshold_pct: float,
    check_weekends: bool,
) -> list[QualityAnomaly]:
    """Inspect single bar values for non-positive, envelope, spike, and weekend."""
    bar_anomalies: list[QualityAnomaly] = []

    # 0. Check NaN / Inf price
    if any(math.isnan(p) or math.isinf(p) for p in (op, hi, lo, cl)):
        bar_anomalies.append(
            QualityAnomaly(
                index=idx,
                timestamp=ts_str,
                code="INVALID_NUMERIC",
                severity="ERROR",
                description=(
                    f"Bar contains non-finite price (O={op}, H={hi}, L={lo}, C={cl})"
                ),
                details={"open": op, "high": hi, "low": lo, "close": cl},
            )
        )
        return bar_anomalies

    # 1. Non-positive price
    if op <= 0.0 or hi <= 0.0 or lo <= 0.0 or cl <= 0.0:
        bar_anomalies.append(
            QualityAnomaly(
                index=idx,
                timestamp=ts_str,
                code="NON_POSITIVE_PRICE",
                severity="ERROR",
                description=(
                    f"Bar contains non-positive price (O={op}, H={hi}, L={lo}, C={cl})"
                ),
                details={"open": op, "high": hi, "low": lo, "close": cl},
            )
        )

    # 2. OHLC envelope violation
    if hi < lo or op > hi or op < lo or cl > hi or cl < lo:
        bar_anomalies.append(
            QualityAnomaly(
                index=idx,
                timestamp=ts_str,
                code="OHLC_ENVELOPE_VIOLATION",
                severity="ERROR",
                description=(
                    f"High/Low does not envelope Open/Close (O={op}, H={hi}, "
                    f"L={lo}, C={cl})"
                ),
                details={"open": op, "high": hi, "low": lo, "close": cl},
            )
        )

    # 3. Duplicate timestamp
    if prev_ts is not None and ts_str == prev_ts:
        bar_anomalies.append(
            QualityAnomaly(
                index=idx,
                timestamp=ts_str,
                code="DUPLICATE_TIMESTAMP",
                severity="WARNING",
                description=f"Duplicate bar timestamp: {ts_str}",
            )
        )

    # 4. Weekend bar
    if check_weekends:
        dt_val = _parse_iso_timestamp(ts_str)
        if dt_val is not None and dt_val.weekday() in WEEKEND_DAYS:
            bar_anomalies.append(
                QualityAnomaly(
                    index=idx,
                    timestamp=ts_str,
                    code="WEEKEND_BAR",
                    severity="INFO",
                    description=(
                        f"Bar occurs on weekend (day={dt_val.strftime('%A')})"
                    ),
                )
            )

    # 5. Price spike
    if prev_close is not None and prev_close > 0.0:
        pct_change = abs(cl - prev_close) / prev_close
        if pct_change >= spike_threshold_pct:
            bar_anomalies.append(
                QualityAnomaly(
                    index=idx,
                    timestamp=ts_str,
                    code="PRICE_SPIKE",
                    severity="WARNING",
                    description=(
                        f"Price spike of {pct_change * 100:.2f}% "
                        f"(from {prev_close} to {cl})"
                    ),
                    details={
                        "prev_close": prev_close,
                        "close": cl,
                        "change_pct": pct_change,
                    },
                )
            )

    return bar_anomalies


class DataQualityInspector:
    """Inspector executing quality validation checks on market data series."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        data_service: DataManagerDataService | None = None,
        spike_threshold_pct: float = 0.10,
    ) -> None:
        """Initialize inspector with database path and data service."""
        self.db_path = Path(db_path) if db_path is not None else None
        self.data_service = data_service
        self.spike_threshold_pct = spike_threshold_pct

    def inspect_dataframe(
        self,
        dataset_id: str,
        df: pd.DataFrame,
        timeframe: str = "M1",
        remove_weekends: bool = True,
    ) -> QualityReport:
        """Inspect an OHLCV DataFrame for anomalies and compute quality score."""
        logger.debug(
            "%s: Inspecting %s bars (timeframe=%s, remove_weekends=%s)",
            INSPECTION_FR,
            dataset_id,
            timeframe,
            remove_weekends,
            extra={"fr_id": INSPECTION_FR, "dataset_id": dataset_id},
        )
        anomalies: list[QualityAnomaly] = []
        anomaly_counts: dict[str, int] = {
            "INVALID_NUMERIC": 0,
            "NON_POSITIVE_PRICE": 0,
            "OHLC_ENVELOPE_VIOLATION": 0,
            "PRICE_SPIKE": 0,
            "DUPLICATE_TIMESTAMP": 0,
            "GAP_DETECTED": 0,
            "WEEKEND_BAR": 0,
        }

        total_records = len(df)
        if total_records == 0:
            return QualityReport(
                report_id=str(uuid.uuid4()),
                dataset_id=dataset_id,
                quality_score=1.0,
                total_records=0,
                anomaly_counts=anomaly_counts,
                anomalies=[],
                evaluated_at_utc=datetime.now(UTC).isoformat(),
            )

        expected_step = _timeframe_to_seconds(timeframe)
        prev_ts: str | None = None
        prev_dt: datetime | None = None
        prev_close: float | None = None

        for idx, (_, row) in enumerate(df.iterrows()):
            ts_str = str(row.get("timestamp", ""))
            curr_dt = _parse_iso_timestamp(ts_str)

            # Check time gap between consecutive bars
            if curr_dt is not None and prev_dt is not None and expected_step > 0:
                delta_sec = (curr_dt - prev_dt).total_seconds()
                is_normal_weekend = (
                    prev_dt.weekday() == WEEKEND_DAY_FRIDAY
                    and curr_dt.weekday() in (WEEKEND_DAY_SUNDAY, 0)
                    and delta_sec <= MAX_WEEKEND_GAP_SECONDS
                )
                if (
                    not is_normal_weekend
                    and delta_sec > expected_step * GAP_MULTIPLIER_THRESHOLD
                ):
                    gap_anomaly = QualityAnomaly(
                        index=idx,
                        timestamp=ts_str,
                        code="GAP_DETECTED",
                        severity="WARNING",
                        description=(
                            f"Time gap of {delta_sec:.0f}s detected between bars "
                            f"(expected ~{expected_step:.0f}s)"
                        ),
                        details={
                            "prev_timestamp": prev_ts,
                            "curr_timestamp": ts_str,
                            "gap_seconds": delta_sec,
                            "expected_step_seconds": expected_step,
                        },
                    )
                    anomalies.append(gap_anomaly)
                    anomaly_counts["GAP_DETECTED"] += 1

            try:
                op = float(row.get("open", 0.0))
                hi = float(row.get("high", 0.0))
                lo = float(row.get("low", 0.0))
                cl = float(row.get("close", 0.0))
            except ValueError, TypeError:
                num_anomaly = QualityAnomaly(
                    index=idx,
                    timestamp=ts_str,
                    code="INVALID_NUMERIC",
                    severity="ERROR",
                    description=(
                        f"Bar contains unparseable numeric values at index {idx}"
                    ),
                )
                anomalies.append(num_anomaly)
                anomaly_counts["INVALID_NUMERIC"] += 1
                prev_ts = ts_str
                prev_dt = curr_dt
                continue

            bar_anoms = _inspect_bar(
                idx=idx,
                ts_str=ts_str,
                op=op,
                hi=hi,
                lo=lo,
                cl=cl,
                prev_ts=prev_ts,
                prev_close=prev_close,
                spike_threshold_pct=self.spike_threshold_pct,
                check_weekends=remove_weekends,
            )
            for a in bar_anoms:
                anomaly_counts[a.code] = anomaly_counts.get(a.code, 0) + 1
            anomalies.extend(bar_anoms)

            prev_ts = ts_str
            prev_dt = curr_dt
            prev_close = cl

        # Deterministic scoring: each error subtracts proportionally
        error_count = (
            anomaly_counts["INVALID_NUMERIC"] * WEIGHT_CRITICAL_PENALTY
            + anomaly_counts["NON_POSITIVE_PRICE"] * WEIGHT_CRITICAL_PENALTY
            + anomaly_counts["OHLC_ENVELOPE_VIOLATION"] * WEIGHT_MAJOR_PENALTY
            + anomaly_counts["PRICE_SPIKE"] * WEIGHT_MINOR_PENALTY
            + anomaly_counts["DUPLICATE_TIMESTAMP"] * WEIGHT_MINOR_PENALTY
            + anomaly_counts["GAP_DETECTED"] * WEIGHT_MINOR_PENALTY
        )
        penalty = (error_count / max(1, total_records)) * 2.0
        score = max(0.0, round(1.0 - penalty, 4))

        report = QualityReport(
            report_id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            quality_score=score,
            total_records=total_records,
            anomaly_counts=anomaly_counts,
            anomalies=anomalies,
            evaluated_at_utc=datetime.now(UTC).isoformat(),
        )
        logger.debug(
            "%s: Completed quality inspection for %s (score=%.4f, anomalies=%d)",
            INSPECTION_FR,
            dataset_id,
            score,
            len(anomalies),
            extra={
                "fr_id": INSPECTION_FR,
                "dataset_id": dataset_id,
                "score": score,
                "anomalies": len(anomalies),
            },
        )
        return report

    def inspect_dataset(self, dataset_id: str) -> QualityReport:
        """Inspect dataset and persist report to datamgr_quality."""
        if self.data_service is None:
            raise RuntimeError("DataManagerDataService is required for inspection.")

        df = self.data_service.read_bars_dataframe(dataset_id)
        timeframe = "M1"
        meta = self.data_service.get_dataset(dataset_id)
        if meta is not None and meta.timeframe:
            timeframe = meta.timeframe
        report = self.inspect_dataframe(dataset_id, df, timeframe=timeframe)

        with resolve_connection(self.db_path) as conn:
            delete_rows(conn, "datamgr_quality", where={"dataset_id": dataset_id})
            insert_row(
                conn,
                "datamgr_quality",
                {
                    "report_id": report.report_id,
                    "dataset_id": report.dataset_id,
                    "quality_score": report.quality_score,
                    "total_records": report.total_records,
                    "anomalies_json": json.dumps(
                        [a.to_dict() for a in report.anomalies]
                    ),
                    "anomaly_counts_json": json.dumps(report.anomaly_counts),
                    "evaluated_at_utc": report.evaluated_at_utc,
                },
            )
            # Update quality score in datamgr_datasets
            update_row_by_pk(
                conn,
                "datamgr_datasets",
                {"id": dataset_id},
                {"quality_score": report.quality_score},
            )

        logger.info(
            "%s: Saved quality report for dataset %s (score=%.4f)",
            SCORE_PERSISTENCE_FR,
            dataset_id,
            report.quality_score,
            extra={
                "fr_id": SCORE_PERSISTENCE_FR,
                "dataset_id": dataset_id,
                "score": report.quality_score,
            },
        )
        return report

    def invalidate_report(self, dataset_id: str) -> None:
        """Invalidate cached quality report for a dataset and reset score."""
        with resolve_connection(self.db_path) as conn:
            delete_rows(conn, "datamgr_quality", where={"dataset_id": dataset_id})
            update_row_by_pk(
                conn,
                "datamgr_datasets",
                {"id": dataset_id},
                {"quality_score": 0.0},
            )
        logger.info(
            "%s: Invalidated quality report for %s",
            SCORE_PERSISTENCE_FR,
            dataset_id,
            extra={"fr_id": SCORE_PERSISTENCE_FR, "dataset_id": dataset_id},
        )

    def get_quality_summary(self, dataset_id: str) -> dict[str, Any]:
        """Retrieve quality summary metrics for a dataset."""
        with resolve_connection(self.db_path) as conn:
            rows = read_rows(
                conn,
                "datamgr_quality",
                where={"dataset_id": dataset_id},
                order_by="evaluated_at_utc DESC",
                limit=1,
            )

        if not rows:
            rep = self.inspect_dataset(dataset_id)
            return {
                "dataset_id": rep.dataset_id,
                "report_id": rep.report_id,
                "quality_score": rep.quality_score,
                "total_records": rep.total_records,
                "anomaly_counts": rep.anomaly_counts,
                "total_anomalies": len(rep.anomalies),
                "evaluated_at_utc": rep.evaluated_at_utc,
            }

        row = rows[0]
        raw_counts = row.get("anomaly_counts_json", "{}")
        counts: dict[str, int] = (
            json.loads(raw_counts) if isinstance(raw_counts, str) else {}
        )
        raw_anomalies = row.get("anomalies_json", "[]")
        anomalies_list: list[dict[str, Any]] = (
            json.loads(raw_anomalies) if isinstance(raw_anomalies, str) else []
        )

        res = {
            "dataset_id": dataset_id,
            "report_id": str(row.get("report_id", "")),
            "quality_score": float(row.get("quality_score", 1.0)),
            "total_records": int(row.get("total_records", 0)),
            "anomaly_counts": counts,
            "total_anomalies": len(anomalies_list),
            "evaluated_at_utc": str(row.get("evaluated_at_utc", "")),
        }
        logger.debug(
            "%s: Served quality summary for %s",
            SUMMARY_DETAILS_FR,
            dataset_id,
            extra={"fr_id": SUMMARY_DETAILS_FR, "dataset_id": dataset_id},
        )
        return res

    def get_quality_details(
        self,
        dataset_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Retrieve paginated anomaly records for a dataset."""
        with resolve_connection(self.db_path) as conn:
            rows = read_rows(
                conn,
                "datamgr_quality",
                where={"dataset_id": dataset_id},
                order_by="evaluated_at_utc DESC",
                limit=1,
            )

        anomalies: list[dict[str, Any]] = []
        if rows:
            raw_anom = rows[0].get("anomalies_json", "[]")
            if isinstance(raw_anom, str):
                try:
                    anomalies = json.loads(raw_anom)
                except json.JSONDecodeError, TypeError:
                    anomalies = []

        paginated = anomalies[offset : offset + limit]
        res = {
            "dataset_id": dataset_id,
            "total": len(anomalies),
            "limit": limit,
            "offset": offset,
            "anomalies": paginated,
        }
        logger.debug(
            "%s: Served %d anomalies for %s",
            SUMMARY_DETAILS_FR,
            len(paginated),
            dataset_id,
            extra={"fr_id": SUMMARY_DETAILS_FR, "count": len(paginated)},
        )
        return res


def main() -> None:
    """Execute real-usage demonstration of DataQualityInspector."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        temp_path = Path(temp_dir)
        db_file = temp_path / "test_quality.db"
        with resolve_connection(db_file) as conn:
            create_schema(conn)

        data_svc = DataManagerDataService(db_path=db_file, data_dir=temp_path / "data")
        sample_csv = "timestamp,open,high,low,close,volume,spread\n" + "\n".join(
            f"2026-01-01 {i // 60:02d}:{i % 60:02d}:00,"
            "1.1000,1.1005,1.0995,1.1002,150,1"
            for i in range(10)
        )
        rec = data_svc.import_dataset(
            {
                "symbol": "EURUSD",
                "timeframe": "M1",
                "source": "file",
                "csv_content": sample_csv,
            }
        )

        inspector = DataQualityInspector(db_path=db_file, data_service=data_svc)
        report = inspector.inspect_dataset(str(rec.id))
        print(
            f"Quality report: score={report.quality_score:.4f}, "
            f"records={report.total_records}"
        )
        print(f"Anomaly counts: {report.anomaly_counts}")

        summary = inspector.get_quality_summary(str(rec.id))
        print(f"Quality summary: {summary}")


if __name__ == "__main__":
    main()
